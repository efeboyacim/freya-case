from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient

from bank_service.app import app

AYSE, MEHMET, ZEYNEP, CAN, ELIF, ALI = 1, 2, 3, 4, 5, 8
DOB = {AYSE: "14.03.1988", MEHMET: "02.11.1975", ZEYNEP: "1993-06-27", CAN: "09.01.1981",
       ELIF: "30.08.1990", ALI: "21.07.1984"}
KADIKOY_THU, KADIKOY_FRI, ATASEHIR_THU, SISLI_FRI = 1, 2, 3, 4


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("BANK_DB", str(tmp_path / "test.db"))
    with TestClient(app) as c:
        yield c


def start(client, customer_id):
    r = client.post("/calls", json={"customer_id": customer_id})
    assert r.status_code == 201
    return r.json()["call_id"]


def verified_call(client, customer_id):
    cid = start(client, customer_id)
    assert client.post(f"/calls/{cid}/confirm-name", json={"is_customer": True}).status_code == 200
    r = client.post(f"/calls/{cid}/verify", json={"dob": DOB[customer_id]})
    assert r.json()["verified"] is True
    return cid


def detail(client, cid):
    return client.get(f"/calls/{cid}").json()


# ---------- seed / start ----------

def test_start_call_returns_name_but_not_dob(client):
    r = client.post("/calls", json={"customer_id": AYSE})
    assert r.json()["customer_name"] == "Ayşe Kaya"
    assert "dob" not in r.json()


def test_unknown_customer_404(client):
    assert client.post("/calls", json={"customer_id": 99}).status_code == 404


# ---------- identity ----------

def test_verify_requires_name_confirmation_first(client):
    cid = start(client, AYSE)
    r = client.post(f"/calls/{cid}/verify", json={"dob": DOB[AYSE]})
    assert r.status_code == 409 and r.json()["error"] == "name_not_confirmed"


def test_wrong_person_cannot_verify_and_closes_not_verified_with_callback(client):
    cid = start(client, AYSE)
    r = client.post(f"/calls/{cid}/confirm-name", json={"is_customer": False})
    assert r.json()["next"] == "close_not_verified"
    assert client.post(f"/calls/{cid}/verify", json={"dob": DOB[AYSE]}).status_code == 403
    assert client.get(f"/calls/{cid}/slots").status_code == 403
    r = client.post(f"/calls/{cid}/close", json={"outcome": "not_verified"})
    assert r.status_code == 200 and r.json()["callback"] is True


def test_verify_accepts_iso_and_dotted_dates(client):
    cid = start(client, AYSE)
    client.post(f"/calls/{cid}/confirm-name", json={"is_customer": True})
    r = client.post(f"/calls/{cid}/verify", json={"dob": "1988-03-14"})
    assert r.json() == {"verified": True, "attempts_left": 3, "district": "Kadıköy",
                        "address_type": "Ev"}


def test_invalid_date_format_does_not_consume_attempt(client):
    cid = start(client, AYSE)
    client.post(f"/calls/{cid}/confirm-name", json={"is_customer": True})
    assert client.post(f"/calls/{cid}/verify", json={"dob": "mart ayı"}).status_code == 400
    assert detail(client, cid)["dob_attempts"] == 0


def test_one_wrong_then_right_verifies(client):
    cid = start(client, ELIF)
    client.post(f"/calls/{cid}/confirm-name", json={"is_customer": True})
    r = client.post(f"/calls/{cid}/verify", json={"dob": "01.01.1990"})
    assert r.json() == {"verified": False, "attempts_left": 2}
    r = client.post(f"/calls/{cid}/verify", json={"dob": DOB[ELIF]})
    assert r.json()["verified"] is True


def test_three_wrong_dob_locks_call(client):
    cid = start(client, CAN)
    client.post(f"/calls/{cid}/confirm-name", json={"is_customer": True})
    for left in (2, 1, 0):
        r = client.post(f"/calls/{cid}/verify", json={"dob": "01.01.2000"})
        assert r.json()["attempts_left"] == left
    assert r.json()["locked"] is True
    # Doğru tarih bile artık kabul edilmez.
    r = client.post(f"/calls/{cid}/verify", json={"dob": DOB[CAN]})
    assert r.status_code == 403 and r.json()["error"] == "locked"
    assert client.get(f"/calls/{cid}/slots").status_code == 403
    r = client.post(f"/calls/{cid}/close", json={"outcome": "not_verified"})
    assert r.json()["callback"] is True
    d = detail(client, cid)
    assert d["dob_attempts"] == 3 and d["appointment"] is None


# ---------- slots ----------

def test_unverified_call_cannot_list_or_book(client):
    cid = start(client, AYSE)
    assert client.get(f"/calls/{cid}/slots").status_code == 403
    r = client.post(f"/calls/{cid}/appointments", json={"slot_id": KADIKOY_THU})
    assert r.status_code == 403 and r.json()["error"] == "not_verified"


def test_slots_only_customer_district_with_capacity(client):
    cid = verified_call(client, AYSE)
    slots = client.get(f"/calls/{cid}/slots").json()["slots"]
    assert [s["slot_id"] for s in slots] == [KADIKOY_THU, KADIKOY_FRI]
    assert all(s["district"] == "Kadıköy" and s["remaining"] == 1 for s in slots)


def test_full_slots_are_hidden(client):
    client.post("/admin/reset", json={"prefill": {KADIKOY_THU: 1, KADIKOY_FRI: 1}})
    cid = verified_call(client, ZEYNEP)
    assert client.get(f"/calls/{cid}/slots").json()["slots"] == []


# ---------- booking ----------

def test_happy_path_booked(client):
    cid = verified_call(client, AYSE)
    r = client.post(f"/calls/{cid}/appointments", json={"slot_id": KADIKOY_THU})
    assert r.status_code == 201 and r.json()["slot"]["remaining"] == 0
    r = client.post(f"/calls/{cid}/close", json={"outcome": "booked"})
    assert r.json() == {"call_id": cid, "outcome": "booked", "callback": False}
    d = detail(client, cid)
    assert d["appointment"]["slot_id"] == KADIKOY_THU and d["callbacks"] == []
    actions = [t["action"] for t in d["tool_log"]]
    assert actions == ["confirm_name", "verify_dob", "book_appointment", "close_call"]


def test_slot_full_409_then_other_slot(client):
    cid = verified_call(client, MEHMET)
    client.post("/admin/fill", json={"slot_id": KADIKOY_THU})
    r = client.post(f"/calls/{cid}/appointments", json={"slot_id": KADIKOY_THU})
    assert r.status_code == 409 and r.json()["error"] == "slot_full"
    r = client.post(f"/calls/{cid}/appointments", json={"slot_id": KADIKOY_FRI})
    assert r.status_code == 201


def test_one_appointment_per_customer(client):
    cid = verified_call(client, CAN)
    assert client.post(f"/calls/{cid}/appointments", json={"slot_id": ATASEHIR_THU}).status_code == 201
    r = client.post(f"/calls/{cid}/appointments", json={"slot_id": ATASEHIR_THU})
    assert r.status_code == 409 and r.json()["error"] == "already_booked"


def test_other_district_400(client):
    cid = verified_call(client, ELIF)
    r = client.post(f"/calls/{cid}/appointments", json={"slot_id": KADIKOY_THU})
    assert r.status_code == 400 and r.json()["error"] == "wrong_district"


def test_unknown_slot_404(client):
    cid = verified_call(client, AYSE)
    assert client.post(f"/calls/{cid}/appointments", json={"slot_id": 42}).status_code == 404


def test_concurrent_bookings_do_not_exceed_capacity(client):
    """3 Kadıköy müşterisi aynı anda 1 kapasiteli yere: yalnız 1'i başarılı."""
    calls = [verified_call(client, c) for c in (AYSE, MEHMET, ZEYNEP)]
    barrier = Barrier(len(calls))

    def book(cid):
        barrier.wait()
        return client.post(f"/calls/{cid}/appointments", json={"slot_id": KADIKOY_THU}).status_code

    with ThreadPoolExecutor(len(calls)) as pool:
        codes = sorted(pool.map(book, calls))
    assert codes == [201, 409, 409]
    assert sum(detail(client, c)["appointment"] is not None for c in calls) == 1


def test_concurrent_same_customer_books_once(client):
    cid = verified_call(client, ELIF)
    barrier = Barrier(5)

    def book(_):
        barrier.wait()
        return client.post(f"/calls/{cid}/appointments", json={"slot_id": ATASEHIR_THU}).status_code

    with ThreadPoolExecutor(5) as pool:
        codes = sorted(pool.map(book, range(5)))
    assert codes == [201, 409, 409, 409, 409]


# ---------- close ----------

def test_booked_without_appointment_rejected(client):
    cid = verified_call(client, AYSE)
    r = client.post(f"/calls/{cid}/close", json={"outcome": "booked"})
    assert r.status_code == 409 and r.json()["error"] == "no_appointment"


def test_appointment_forces_booked(client):
    cid = verified_call(client, AYSE)
    client.post(f"/calls/{cid}/appointments", json={"slot_id": KADIKOY_THU})
    r = client.post(f"/calls/{cid}/close", json={"outcome": "no_slot"})
    assert r.status_code == 409 and r.json()["error"] == "appointment_exists"


def test_no_slot_creates_callback(client):
    cid = verified_call(client, ZEYNEP)
    r = client.post(f"/calls/{cid}/close", json={"outcome": "no_slot", "note": "hiçbiri uymadı"})
    assert r.json()["callback"] is True
    assert detail(client, cid)["callbacks"] == [{"reason": "no_slot", "due": "next_week"}]


def test_declined_has_no_callback(client):
    cid = verified_call(client, ALI)
    r = client.post(f"/calls/{cid}/close", json={"outcome": "declined"})
    assert r.json()["callback"] is False
    assert detail(client, cid)["callbacks"] == []


def test_unverified_can_only_close_not_verified(client):
    cid = start(client, AYSE)
    for outcome in ("no_slot", "declined"):
        r = client.post(f"/calls/{cid}/close", json={"outcome": outcome})
        assert r.status_code == 409 and r.json()["error"] == "not_verified"


def test_verified_cannot_close_not_verified(client):
    cid = verified_call(client, AYSE)
    r = client.post(f"/calls/{cid}/close", json={"outcome": "not_verified"})
    assert r.status_code == 409


def test_llm_cannot_close_not_reached(client):
    cid = start(client, AYSE)
    assert client.post(f"/calls/{cid}/close", json={"outcome": "not_reached"}).status_code == 422


def test_closed_call_rejects_writes(client):
    cid = verified_call(client, ZEYNEP)
    client.post(f"/calls/{cid}/close", json={"outcome": "no_slot"})
    for method, path, body in [
        ("post", "close", {"outcome": "declined"}),
        ("post", "appointments", {"slot_id": KADIKOY_THU}),
        ("post", "verify", {"dob": DOB[ZEYNEP]}),
        ("post", "confirm-name", {"is_customer": True}),
        ("get", "slots", None),
    ]:
        kwargs = {"json": body} if body else {}
        r = getattr(client, method)(f"/calls/{cid}/{path}", **kwargs)
        assert r.status_code == 409 and r.json()["error"] == "call_closed", path


# ---------- dialer / transcript / admin ----------

def test_no_answer_closes_not_reached_with_callback(client):
    cid = start(client, CAN)
    r = client.post(f"/calls/{cid}/no-answer")
    assert r.json() == {"call_id": cid, "outcome": "not_reached", "callback": True}
    d = detail(client, cid)
    assert d["outcome"] == "not_reached" and d["callbacks"][0]["reason"] == "not_reached"


def test_no_answer_rejected_after_answer(client):
    cid = start(client, CAN)
    client.post(f"/calls/{cid}/confirm-name", json={"is_customer": True})
    assert client.post(f"/calls/{cid}/no-answer").status_code == 409


def test_transcript_is_stored_in_order(client):
    cid = start(client, AYSE)
    client.post(f"/calls/{cid}/transcript", json={"role": "assistant", "text": "Merhaba"})
    client.post(f"/calls/{cid}/transcript", json={"role": "customer", "text": "Buyrun"})
    assert detail(client, cid)["transcript"] == [
        {"role": "assistant", "text": "Merhaba"}, {"role": "customer", "text": "Buyrun"}]
    assert detail(client, cid)["tool_log"] == []  # transkript tool_log'a yazılmaz


def test_reset_restores_seed(client):
    cid = verified_call(client, AYSE)
    client.post(f"/calls/{cid}/appointments", json={"slot_id": KADIKOY_THU})
    client.post("/admin/reset")
    assert client.get(f"/calls/{cid}").status_code == 404
    cid = verified_call(client, MEHMET)
    assert len(client.get(f"/calls/{cid}/slots").json()["slots"]) == 2
