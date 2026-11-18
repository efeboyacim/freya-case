"""Yazılı modda arama: python -m assistant.cli --customer 1 [--reset] [--debug]

Komutlar: /fill <slot_id> yeri doldurur (senaryo 6), /kapat müşterinin kapattığını bildirir.
"""

import argparse
import asyncio
import json
import sys

import httpx

from . import config
from .session import CallSession


def print_tool(name: str, args: dict, status, body: dict) -> None:
    short = json.dumps(body, ensure_ascii=False)
    if len(short) > 200:
        short = short[:200] + "..."
    print(f"    [tool] {name}({json.dumps(args, ensure_ascii=False)}) -> {status} {short}")


async def print_summary(http: httpx.AsyncClient, call_id: int, session: CallSession) -> None:
    d = (await http.get(f"/calls/{call_id}")).json()
    print("\n--- Arama özeti (DB) ---")
    print(f"call_id={d['call_id']} müşteri={d['customer_name']} status={d['status']} "
          f"outcome={d['outcome']}")
    print(f"randevu: {d['appointment']}")
    print(f"callback: {d['callbacks']}")
    print("tool_log: " + " → ".join(f"{t['action']}:{t['status_code']}" for t in d["tool_log"]))
    llm = [round(s.llm_s, 1) for s in session.turn_stats]
    print(f"LLM süreleri (sn): {llm}")
    if session.violations:
        print(f"UYARI: {session.violations}")


async def run(customer_id: int, reset: bool, debug: bool) -> None:
    async with httpx.AsyncClient(base_url=config.BANK_URL, timeout=15) as http:
        if reset:
            (await http.post("/admin/reset")).raise_for_status()
        session = CallSession(customer_id, http=http, on_tool=print_tool if debug else None)
        async with session:
            print(f"Asistan: {await session.start()}")
            while not session.done:
                try:
                    line = (await asyncio.to_thread(input, "Müşteri: ")).strip()
                except EOFError:
                    line = "/kapat"
                if not line:
                    continue
                if line.startswith("/fill"):
                    slot_id = int(line.split()[1])
                    r = await http.post("/admin/fill", json={"slot_id": slot_id})
                    print(f"    [admin] slot {slot_id} dolduruldu -> {r.status_code}")
                    continue
                reply = await (session.hangup() if line == "/kapat" else session.send(line))
                if reply:
                    print(f"Asistan: {reply}")
            await print_summary(http, session.call_id, session)


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Kart teslimatı asistanı, yazılı mod")
    parser.add_argument("--customer", type=int, required=True, help="Müşteri id (1-8)")
    parser.add_argument("--reset", action="store_true", help="Önce DB'yi seed durumuna döndür")
    parser.add_argument("--debug", action="store_true", help="Tool çağrılarını göster")
    args = parser.parse_args()
    asyncio.run(run(args.customer, args.reset, args.debug))


if __name__ == "__main__":
    main()
