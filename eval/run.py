"""Eval: python -m eval.run [--only 1,6] [--reps 3] [--personas a,b] [--tag ad] [--variant broken_r5]

Her arama sırasıyla: reset, simüle müşteriyle arama, DB'den kontroller. Aramalar sıralı çalışır
(reset globaldir). Sonuç: eval/runs/<YYYYMMDD-HHMM>[-tag]/
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import httpx

from assistant import config
from assistant.prompt import SYSTEM_PROMPT
from assistant.session import MAX_CUSTOMER_TURNS, CallSession

from . import checks
from .personas import PERSONAS
from .scenarios import SCENARIOS, Scenario
from .simulator import HANGUP, Customer

RUNS = Path(__file__).parent / "runs"


# ---------- bozuk prompt varyantları (kontrollerin gerçekten ölçtüğünü göstermek için) ----------

def _broken_r5(prompt: str) -> str:
    start = prompt.index("5. Onay (R5)")
    end = prompt.index("6. Randevu (R6)")
    new = ("5. Seçim: Müşteri bir yer seçince hemen book_appointment çağır; tekrar okuma ya da onay "
           "isteme.\n")
    return prompt[:start] + new + prompt[end:]


VARIANTS = {"base": None, "broken_r5": _broken_r5}


def pick_persona(sc_no: int, rep: int, names: list[str]) -> str:
    return names[(sc_no + rep) % len(names)]


# ---------- tek arama ----------

async def play(sc: Scenario, persona: str, http: httpx.AsyncClient, variant: str) -> dict:
    """Aramayı oynar; (log, session bilgileri) döner."""
    log: list[tuple[str, str]] = []
    assistant_turns: list[str] = []
    filled = False

    async def on_tool(name, args, status, body):
        nonlocal filled
        short = json.dumps(body, ensure_ascii=False)
        log.append(("tool", f"{name}({json.dumps(args, ensure_ascii=False)}) -> {status} {short[:300]}"))
        if sc.fill_after_list and name == "list_slots" and not filled:
            filled = True
            await http.post("/admin/fill", json={"slot_id": sc.fill_after_list})
            log.append(("tool", f"[harness] slot {sc.fill_after_list} arada doldu (asistan görmez)"))

    s = CallSession(sc.customer_id, http=http, on_tool=on_tool,
                    prompt_transform=VARIANTS[variant])
    sim_cost = 0.0
    async with s, Customer(sc, persona) as cust:
        text = await s.start()
        for _ in range(MAX_CUSTOMER_TURNS + 2):
            if text:
                log.append(("assistant", text))
                assistant_turns.append(text)
            if s.done:
                break
            said = await cust.reply(text or "(sessizlik)")
            if said == HANGUP:
                log.append(("customer", "(müşteri hattı kapattı)"))
                text = await s.hangup()
            else:
                log.append(("customer", said))
                text = await s.send(said)
        sim_cost = cust.cost
    llm_cost = s.turn_stats[-1].cost_usd or 0.0 if s.turn_stats else 0.0
    return {"call_id": s.call_id, "log": log, "assistant_turns": assistant_turns, "closed": s.closed,
            "violations": s.violations, "cost": llm_cost + sim_cost}


async def run_call(sc: Scenario, persona: str, rep: int, http: httpx.AsyncClient, variant: str,
                   out: Path) -> dict:
    started = time.perf_counter()
    (await http.post("/admin/reset", json={"prefill": sc.prefill})).raise_for_status()
    row = {"scenario": sc.no, "title": sc.title, "persona": persona if sc.goal else "-", "rep": rep,
           "checks": {}, "other": [], "error": None}
    try:
        if sc.goal is None:      # senaryo 12: dialer no-answer yazar, LLM yok
            cid = (await http.post("/calls", json={"customer_id": sc.customer_id})).json()["call_id"]
            await http.post(f"/calls/{cid}/no-answer")
            played = {"call_id": cid, "log": [("tool", "[harness] no-answer (dialer)")], "assistant_turns": [],
                      "closed": True, "violations": [], "cost": 0.0}
        else:
            played = await play(sc, persona, http, variant)
        d = (await http.get(f"/calls/{played['call_id']}")).json()
        slots = (await http.get("/admin/slots")).json()["slots"]
        row["outcome"] = d["outcome"]
        row["checks"] = checks.deterministic(sc, d, slots, closed=played["closed"],
                                             violations=played["violations"],
                                             assistant_turns=played["assistant_turns"])
        judged, other, jcost = (await checks.judge(played["log"]) if sc.goal else
                                ({k: (checks.NA, "") for k in checks.JUDGED}, [], 0.0))
        row["checks"].update(judged)
        row["other"] = other
        row["cost"] = round(played["cost"] + jcost, 4)
        write_transcript(out, sc, persona, rep, row, played["log"], d)
    except Exception as exc:        # tek aramanın çökmesi koşumu durdurmasın
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["checks"]["clean_end"] = (checks.FAIL, row["error"])
        row["outcome"] = row.get("outcome")
        write_transcript(out, sc, persona, rep, row, [], None)
    row["secs"] = round(time.perf_counter() - started, 1)
    row["file"] = f"transcripts/{sc.no:02d}-{row['persona']}-{rep}.md"
    return row


def write_transcript(out: Path, sc: Scenario, persona: str, rep: int, row: dict, log, d) -> None:
    lines = [f"# Senaryo {sc.no}: {sc.title} · persona: {row['persona']} · tekrar {rep}", ""]
    lines.append(f"outcome: {row.get('outcome')} (beklenen {sc.outcome})")
    if row["error"]:
        lines.append(f"HATA: {row['error']}")
    lines += ["", "## Konuşma", ""]
    names = {"customer": "**Müşteri**", "assistant": "**Asistan**", "tool": "    `tool`"}
    lines += [f"{names[k]}: {t}" for k, t in log]
    if d:
        lines += ["", "## tool_log", ""]
        lines += [f"- {t['action']} → {t['status_code']}" for t in d["tool_log"]]
        lines += ["", f"randevu: {d['appointment']} · callback: {d['callbacks']}"]
    lines += ["", "## Kontroller", ""]
    for k, (v, note) in row["checks"].items():
        if v != checks.PASS:
            lines.append(f"- {k}: {v} {note}")
    for o in row["other"]:
        lines.append(f"- diğer (zarar {o['harm']}): {o['issue']}")
    (out / "transcripts" / f"{sc.no:02d}-{row['persona']}-{rep}.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")


# ---------- özet ----------

def score(row: dict) -> tuple[int, int]:
    vals = [v for v, _ in row["checks"].values() if v != checks.NA]
    return sum(v == checks.PASS for v in vals), len(vals)


def summarize(rows: list[dict], meta: dict) -> str:
    n = len(rows)
    ok = sum(score(r)[0] for r in rows)
    tot = sum(score(r)[1] for r in rows)
    out = [f"# Eval özeti: {meta['name']}", "",
           f"Varyant `{meta['variant']}` · model `{meta['model']}` · {n} arama · "
           f"**skor {ok}/{tot} ({100 * ok / max(tot, 1):.1f}%)** · maliyet ${sum(r.get('cost', 0) for r in rows):.2f}",
           ""]
    personas = sorted({r["persona"] for r in rows})
    out += ["## Senaryo × persona (geçen/toplam kontrol)", "",
            "| # | Senaryo | " + " | ".join(personas) + " | Toplam |",
            "|---|---|" + "---|" * (len(personas) + 1)]
    for sc_no in sorted({r["scenario"] for r in rows}):
        rs = [r for r in rows if r["scenario"] == sc_no]
        cells = []
        for p in personas:
            ps = [score(r) for r in rs if r["persona"] == p]
            cells.append(f"{sum(a for a, _ in ps)}/{sum(b for _, b in ps)}" if ps else "·")
        a, b = sum(score(r)[0] for r in rs), sum(score(r)[1] for r in rs)
        out.append(f"| {sc_no} | {rs[0]['title']} | " + " | ".join(cells) + f" | {a}/{b} |")
    out += ["", "## Hata öncelik tablosu (öncelik = sıklık × zarar)", "",
            "Sıklık: hatanın görüldüğü arama / toplam arama.", "",
            "| Öncelik | Sıklık | Açıklama |", "|---|---|---|"]
    fails: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        for k, (v, _) in r["checks"].items():
            if v == checks.FAIL:
                fails[k].append(r)
    table = [(len(rs) / n * checks.CHECKS[k][0], k, rs) for k, rs in fails.items()]
    for pri, k, rs in sorted(table, key=lambda t: -t[0]):
        harm, label = checks.CHECKS[k]
        out.append(f"| {pri:.2f} | {len(rs)}/{n} | {label} (zarar {harm}). "
                   f"Örnek: [{rs[0]['file'].split('/')[1]}]({rs[0]['file']}) |")
    if not table:
        out.append("| - | 0 | hata yok |")
    others = [(o, r) for r in rows for o in r["other"]]
    if others:
        out += ["", "## Hakemin 'diğer sorunlar' listesi (zarar sırasıyla)", "",
                "| Zarar | Sorun | Örnek |", "|---|---|---|"]
        for o, r in sorted(others, key=lambda t: -t[0]["harm"])[:15]:
            out.append(f"| {o['harm']} | {o['issue'].replace('|', '/')[:140]} | [{r['file'].split('/')[1]}]({r['file']}) |")
    out += ["", "## Persona başına skor", "", "| Persona | Skor |", "|---|---|"]
    for p in personas:
        ps = [score(r) for r in rows if r["persona"] == p]
        a, b = sum(x for x, _ in ps), sum(y for _, y in ps)
        out.append(f"| {p} | {a}/{b} ({100 * a / max(b, 1):.0f}%) |")
    return "\n".join(out) + "\n"


# ---------- ana ----------

async def main_async(args) -> None:
    scs = [s for s in SCENARIOS if not args.only or s.no in args.only]
    names = args.personas or list(PERSONAS)
    stamp = datetime.now().strftime("%Y%m%d-%H%M") + (f"-{args.tag}" if args.tag else "")
    out = RUNS / stamp
    (out / "transcripts").mkdir(parents=True, exist_ok=True)
    prompt = SYSTEM_PROMPT if not VARIANTS[args.variant] else VARIANTS[args.variant](SYSTEM_PROMPT)
    meta = {"name": stamp, "model": config.MODEL, "effort": config.EFFORT, "variant": args.variant,
            "prompt_sha1": hashlib.sha1(prompt.encode()).hexdigest()[:10],
            "scenarios": [s.no for s in scs], "personas": names, "reps": args.reps}
    (out / "config.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    rows: list[dict] = []
    async with httpx.AsyncClient(base_url=config.BANK_URL, timeout=30) as http:
        for sc in scs:
            for rep in range(args.reps):
                persona = pick_persona(sc.no, rep, names)
                row = await run_call(sc, persona, rep, http, args.variant, out)
                rows.append(row)
                a, b = score(row)
                bad = [k for k, (v, _) in row["checks"].items() if v == checks.FAIL]
                print(f"[{len(rows)}] s{sc.no:>2} {row['persona']:<13} #{rep} "
                      f"{row.get('outcome')!s:<12} {a}/{b} {row['secs']:>5}s  {','.join(bad)}", flush=True)
                with (out / "results.jsonl").open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = summarize(rows, meta)
    (out / "summary.md").write_text(summary, encoding="utf-8")
    print("\n" + summary)
    print(f"Sonuç klasörü: {out}")


def merge(dirs: list[str], tag: str) -> None:
    """Birden çok koşunun results.jsonl dosyalarını birleştirip tek summary.md üretir."""
    rows = []
    out = RUNS / (datetime.now().strftime("%Y%m%d-%H%M") + f"-{tag}")
    (out / "transcripts").mkdir(parents=True, exist_ok=True)
    for d in dirs:
        src = RUNS / d
        for line in (src / "results.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            r["checks"] = {k: tuple(v) for k, v in r["checks"].items()}
            name = r["file"].split("/")[1]
            shutil.copy(src / r["file"], out / "transcripts" / name)
            rows.append(r)
    meta = {"name": out.name, "model": config.MODEL, "variant": "base", "merged_from": dirs}
    (out / "config.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out / "results.jsonl").open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    (out / "summary.md").write_text(summarize(rows, meta), encoding="utf-8")
    print(f"{len(rows)} arama birleştirildi: {out}")


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Simüle müşterilerle eval")
    ap.add_argument("--only", type=lambda s: [int(x) for x in s.split(",")], help="Senaryolar: 1,6")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--personas", type=lambda s: s.split(","), help="Persona listesi")
    ap.add_argument("--tag", default="")
    ap.add_argument("--variant", default="base", choices=list(VARIANTS))
    ap.add_argument("--merge", type=lambda s: s.split(","), help="Koşu klasörlerini birleştir: a,b,c")
    args = ap.parse_args()
    if args.merge:
        merge(args.merge, args.tag or "merged")
    else:
        asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
