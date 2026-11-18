"""Asistan katmanı testleri. LLM çağrılmaz; servis aynı süreçte ASGI üzerinden çalışır."""

import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from assistant.prompt import build_system_prompt
from assistant.session import build_options
from assistant.tools import ALLOWED_TOOLS, TOOL_NAMES, CallState, build_bank_server, build_tools
from bank_service.app import app
from bank_service.seed import CUSTOMERS, SLOTS

AYSE, MEHMET = 1, 2
KADIKOY_THU = 1


@pytest.fixture
def svc(tmp_path, monkeypatch):
    monkeypatch.setenv("BANK_DB", str(tmp_path / "test.db"))
    with TestClient(app) as c:  # lifespan şemayı ve seed'i kurar
        yield c


def new_call(svc, customer_id):
    return svc.post("/calls", json={"customer_id": customer_id}).json()["call_id"]


def run_tools(call_id, steps, on_tool=None):
    """steps: [(tool_name, args)] sırayla çalışır; (state, [result]) döner."""
    async def go():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
            state = CallState(call_id=call_id)
            tools = {t.name: t for t in build_tools(state, http, on_tool)}
            results = [await tools[name].handler(args) for name, args in steps]
            return state, results
    return asyncio.run(go())


def text(result):
    return result["content"][0]["text"]


# ---------- tool tanımları ----------

def test_exactly_five_tools_without_identity_params():
    tools = build_tools(CallState(call_id=1), httpx.AsyncClient())
    assert [t.name for t in tools] == list(TOOL_NAMES)
    assert ALLOWED_TOOLS == [f"mcp__bank__{n}" for n in TOOL_NAMES]
    for t in tools:
        props = set(t.input_schema.get("properties", {}))
        assert not props & {"customer_id", "call_id", "dob", "birth_date", "phone"}, t.name


def test_server_builds():
    server = build_bank_server(CallState(call_id=1), httpx.AsyncClient())
    assert server["type"] == "sdk" and server["name"] == "bank"


# ---------- tool davranışı ----------

def test_verify_flow_and_no_dob_leak(svc):
    cid = new_call(svc, AYSE)
    _, (name, wrong, ok) = run_tools(cid, [
        ("confirm_identity_name", {"is_customer": True}),
        ("verify_dob", {"spoken_date": "15.03.1988"}),
        ("verify_dob", {"spoken_date": "14.03.1988"}),
    ])
    assert "is_error" not in name
    assert json.loads(text(wrong)) == {"verified": False, "attempts_left": 2}
    assert json.loads(text(ok))["verified"] is True
    for r in (name, wrong, ok):
        assert "1988-03-14" not in text(r)


def test_service_errors_become_readable_tool_errors(svc):
    cid = new_call(svc, AYSE)
    _, (slots,) = run_tools(cid, [("list_slots", {})])
    assert slots["is_error"] is True
    assert text(slots).startswith("HATA 403 not_verified:")
    assert "Kimlik doğrulanmadan" in text(slots)


def test_slot_full_is_error(svc):
    cid = new_call(svc, MEHMET)
    svc.post("/admin/fill", json={"slot_id": KADIKOY_THU})
    _, results = run_tools(cid, [
        ("confirm_identity_name", {"is_customer": True}),
        ("verify_dob", {"spoken_date": "02.11.1975"}),
        ("book_appointment", {"slot_id": KADIKOY_THU}),
    ])
    assert results[-1]["is_error"] is True
    assert "HATA 409 slot_full" in text(results[-1])


def test_close_call_sets_state_only_on_success(svc):
    cid = new_call(svc, AYSE)
    state, (bad, good) = run_tools(cid, [
        ("close_call", {"outcome": "booked"}),        # randevu yok -> 409
        ("close_call", {"outcome": "not_verified"}),
    ])
    assert bad["is_error"] is True and "no_appointment" in text(bad)
    assert "is_error" not in good
    assert state.closed is True and state.outcome == "not_verified"


def test_close_call_failure_keeps_call_open(svc):
    cid = new_call(svc, AYSE)
    state, _ = run_tools(cid, [("close_call", {"outcome": "booked"})])
    assert state.closed is False and state.outcome is None


def test_on_tool_callback_receives_each_call(svc):
    cid = new_call(svc, AYSE)
    seen = []
    run_tools(cid, [("confirm_identity_name", {"is_customer": False}),
                    ("close_call", {"outcome": "not_verified"})],
              on_tool=lambda n, a, s, b: seen.append((n, s)))
    assert seen == [("confirm_identity_name", 200), ("close_call", 200)]


def test_unreachable_service_is_error():
    async def go():
        async with httpx.AsyncClient(base_url="http://127.0.0.1:1") as http:
            tools = {t.name: t for t in build_tools(CallState(call_id=1), http)}
            return await tools["list_slots"].handler({})
    result = asyncio.run(go())
    assert result["is_error"] is True and "ulaşılamadı" in text(result)


# ---------- ajan ayarları ve prompt ----------

def test_options_lock_down_tools(tmp_path):
    server = build_bank_server(CallState(call_id=1), httpx.AsyncClient())
    opts = build_options("Ayşe Kaya", server, cwd=str(tmp_path))
    assert opts.tools == []
    assert opts.allowed_tools == ALLOWED_TOOLS
    assert opts.permission_mode == "dontAsk"
    assert opts.setting_sources == []
    assert opts.strict_mcp_config is True
    assert opts.env["ENABLE_TOOL_SEARCH"] == "false"
    assert list(opts.mcp_servers) == ["bank"]


def test_prompt_has_name_but_no_service_data():
    prompt = build_system_prompt("Ayşe Kaya")
    assert "Ayşe Kaya" in prompt
    for _id, _name, phone, dob, district, _addr in CUSTOMERS:
        assert dob not in prompt and phone not in prompt and district not in prompt
    for _id, _district, _day, time_range, _cap in SLOTS:
        assert time_range not in prompt


def test_ensure_r7_adds_next_week_line_only_for_no_slot():
    from assistant.session import R7_LINE, ensure_r7
    assert ensure_r7("Hoşça kalın.", "no_slot") == f"{R7_LINE} Hoşça kalın."
    assert ensure_r7("", "no_slot") == R7_LINE
    said = "Anladım. Sizi gelecek hafta arayacağız, iyi günler."
    assert ensure_r7(said, "no_slot") == said
    assert ensure_r7("İyi günler.", "booked") == "İyi günler."
    assert ensure_r7("İyi günler.", None) == "İyi günler."
