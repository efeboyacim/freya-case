"""Banka servisi: müşteri, kurye yeri ve arama kayıtları. İş kuralları burada zorlanır."""

import json
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import db

MAX_DOB_ATTEMPTS = 3
CALLBACK_OUTCOMES = {"no_slot", "not_verified", "not_reached"}
DOB_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    with db.connection() as conn:
        db.init_db(conn)
    yield


app = FastAPI(title="Bank service", lifespan=lifespan)


# ---------- request bodies ----------

class StartCall(BaseModel):
    customer_id: int


class ConfirmName(BaseModel):
    is_customer: bool


class VerifyDob(BaseModel):
    dob: str


class Book(BaseModel):
    slot_id: int


class Close(BaseModel):
    outcome: Literal["booked", "no_slot", "declined", "not_verified"]
    note: str = ""


class TranscriptLine(BaseModel):
    role: Literal["assistant", "customer"]
    text: str


class Reset(BaseModel):
    prefill: dict[int, int] = {}


class Fill(BaseModel):
    slot_id: int


# ---------- helpers ----------

def error(status: int, code: str, message: str) -> tuple[int, dict]:
    return status, {"error": code, "message": message}


def respond(conn, call_id: int, action: str, req: dict | None, status: int, body: dict):
    """Return a JSON response and record it in tool_log."""
    conn.execute(
        "INSERT INTO tool_log (call_id, action, request, status_code, response) VALUES (?,?,?,?,?)",
        (call_id, action, json.dumps(req, ensure_ascii=False) if req is not None else None,
         status, json.dumps(body, ensure_ascii=False)),
    )
    return JSONResponse(status_code=status, content=body)


def get_call(conn, call_id: int):
    return conn.execute(
        "SELECT c.*, cu.name, cu.dob, cu.district, cu.address_type "
        "FROM calls c JOIN customers cu ON cu.id = c.customer_id WHERE c.id = ?",
        (call_id,),
    ).fetchone()


def not_found(call_id: int):
    return JSONResponse(status_code=404, content={"error": "call_not_found",
                                                  "message": f"Çağrı {call_id} bulunamadı."})


def parse_dob(value: str) -> str | None:
    value = value.strip()
    for fmt in DOB_FORMATS:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def slot_dict(row) -> dict:
    return {"slot_id": row["id"], "district": row["district"], "day": row["day"],
            "time_range": row["time_range"], "remaining": row["capacity"] - row["booked"]}


CLOSED = error(409, "call_closed", "Bu çağrı kapatılmış, işlem yapılamaz.")


# ---------- call flow ----------

@app.post("/calls", status_code=201)
def start_call(body: StartCall):
    with db.connection() as conn:
        cust = conn.execute("SELECT id, name FROM customers WHERE id = ?",
                            (body.customer_id,)).fetchone()
        if cust is None:
            return JSONResponse(status_code=404, content={"error": "customer_not_found",
                                                          "message": "Müşteri bulunamadı."})
        cur = conn.execute("INSERT INTO calls (customer_id) VALUES (?)", (cust["id"],))
        return {"call_id": cur.lastrowid, "customer_id": cust["id"], "customer_name": cust["name"]}


@app.post("/calls/{call_id}/no-answer")
def no_answer(call_id: int):
    with db.connection() as conn:
        call = get_call(conn, call_id)
        if call is None:
            return not_found(call_id)
        if call["status"] == "closed":
            status, body = CLOSED
        elif call["name_confirmed"] is not None:
            status, body = error(409, "call_answered", "Çağrı cevaplanmış, not_reached yazılamaz.")
        else:
            close_call_row(conn, call, "not_reached", "telefon açılmadı")
            status, body = 200, {"call_id": call_id, "outcome": "not_reached", "callback": True}
        return respond(conn, call_id, "no_answer", None, status, body)


@app.post("/calls/{call_id}/confirm-name")
def confirm_name(call_id: int, body: ConfirmName):
    with db.connection() as conn:
        call = get_call(conn, call_id)
        if call is None:
            return not_found(call_id)
        req = body.model_dump()
        if call["status"] == "closed":
            status, resp = CLOSED
        elif call["verified"]:
            status, resp = 200, {"name_confirmed": True, "next": "already_verified"}
        else:
            conn.execute("UPDATE calls SET name_confirmed = ? WHERE id = ?",
                         (int(body.is_customer), call_id))
            if body.is_customer:
                status, resp = 200, {"name_confirmed": True, "next": "ask_date_of_birth"}
            else:
                status, resp = 200, {
                    "name_confirmed": False, "next": "close_not_verified",
                    "message": "Telefonu müşteri dışında biri açtı. Arama nedenini söyleme, "
                               "nazikçe kapat: close_call(not_verified).",
                }
        return respond(conn, call_id, "confirm_name", req, status, resp)


@app.post("/calls/{call_id}/verify")
def verify(call_id: int, body: VerifyDob):
    with db.connection() as conn:
        call = get_call(conn, call_id)
        if call is None:
            return not_found(call_id)
        req = body.model_dump()
        status, resp = _verify(conn, call, body.dob)
        return respond(conn, call_id, "verify_dob", req, status, resp)


def _verify(conn, call, raw_dob: str) -> tuple[int, dict]:
    if call["status"] == "closed":
        return CLOSED
    if call["name_confirmed"] is None:
        return error(409, "name_not_confirmed", "Önce isim teyidi alınmalı (confirm_identity_name).")
    if call["name_confirmed"] == 0:
        return error(403, "wrong_person", "Telefonu müşteri açmadı; doğrulama yapılamaz.")
    if call["verified"]:
        return 200, {"verified": True, "attempts_left": MAX_DOB_ATTEMPTS - call["dob_attempts"],
                     "district": call["district"], "address_type": call["address_type"]}
    if call["dob_attempts"] >= MAX_DOB_ATTEMPTS:
        return error(403, "locked", "3 hatalı deneme yapıldı. close_call(not_verified) ile kapat.")
    dob = parse_dob(raw_dob)
    if dob is None:
        return error(400, "invalid_format",
                     "Tarih anlaşılamadı, hak düşülmedi. GG.AA.YYYY ya da YYYY-AA-GG gönder.")

    if dob == call["dob"]:
        conn.execute("UPDATE calls SET verified = 1 WHERE id = ?", (call["id"],))
        return 200, {"verified": True, "attempts_left": MAX_DOB_ATTEMPTS - call["dob_attempts"],
                     "district": call["district"], "address_type": call["address_type"]}

    conn.execute("UPDATE calls SET dob_attempts = dob_attempts + 1 WHERE id = ?", (call["id"],))
    left = MAX_DOB_ATTEMPTS - call["dob_attempts"] - 1
    resp = {"verified": False, "attempts_left": left}
    if left == 0:
        resp.update(locked=True, next="close_not_verified",
                    message="3 hatalı deneme. Kart ya da teslimattan söz etmeden kapat.")
    return 200, resp


@app.get("/calls/{call_id}/slots")
def list_slots(call_id: int):
    with db.connection() as conn:
        call = get_call(conn, call_id)
        if call is None:
            return not_found(call_id)
        if call["status"] == "closed":
            status, resp = CLOSED
        elif not call["verified"]:
            status, resp = error(403, "not_verified", "Kimlik doğrulanmadan yer listelenemez.")
        else:
            rows = conn.execute(
                "SELECT * FROM slots WHERE district = ? AND booked < capacity ORDER BY id",
                (call["district"],),
            ).fetchall()
            status, resp = 200, {"district": call["district"], "address_type": call["address_type"],
                                 "slots": [slot_dict(r) for r in rows]}
        return respond(conn, call_id, "list_slots", None, status, resp)


@app.post("/calls/{call_id}/appointments")
def book(call_id: int, body: Book):
    with db.connection() as conn:
        call = get_call(conn, call_id)
        if call is None:
            return not_found(call_id)
        req = body.model_dump()
        status, resp = _book(conn, call, body.slot_id)
        return respond(conn, call_id, "book_appointment", req, status, resp)


def _book(conn, call, slot_id: int) -> tuple[int, dict]:
    if call["status"] == "closed":
        return CLOSED
    if not call["verified"]:
        return error(403, "not_verified", "Kimlik doğrulanmadan randevu yazılamaz.")
    slot = conn.execute("SELECT * FROM slots WHERE id = ?", (slot_id,)).fetchone()
    if slot is None:
        return error(404, "slot_not_found", "Böyle bir yer yok.")
    if slot["district"] != call["district"]:
        return error(400, "wrong_district",
                     "Bu yer müşterinin ilçesinde değil. İlçe değişikliği telefonda yapılamaz.")

    conn.execute("BEGIN IMMEDIATE")
    try:
        if conn.execute("SELECT 1 FROM appointments WHERE customer_id = ?",
                        (call["customer_id"],)).fetchone():
            conn.execute("ROLLBACK")
            return error(409, "already_booked", "Müşterinin zaten bir randevusu var.")
        cur = conn.execute(
            "UPDATE slots SET booked = booked + 1 WHERE id = ? AND booked < capacity", (slot_id,))
        if cur.rowcount == 0:
            conn.execute("ROLLBACK")
            return error(409, "slot_full", "Bu yer dolmuş. list_slots ile kalan yerleri öner.")
        cur = conn.execute(
            "INSERT INTO appointments (customer_id, slot_id, call_id) VALUES (?,?,?)",
            (call["customer_id"], slot_id, call["id"]))
        conn.execute("COMMIT")
    except sqlite3.IntegrityError:
        conn.execute("ROLLBACK")
        return error(409, "already_booked", "Müşterinin zaten bir randevusu var.")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    slot = conn.execute("SELECT * FROM slots WHERE id = ?", (slot_id,)).fetchone()
    return 201, {"appointment_id": cur.lastrowid, "slot": slot_dict(slot),
                 "address_type": call["address_type"]}


@app.post("/calls/{call_id}/close")
def close(call_id: int, body: Close):
    with db.connection() as conn:
        call = get_call(conn, call_id)
        if call is None:
            return not_found(call_id)
        req = body.model_dump()
        status, resp = _close(conn, call, body.outcome, body.note)
        return respond(conn, call_id, "close_call", req, status, resp)


def _close(conn, call, outcome: str, note: str) -> tuple[int, dict]:
    if call["status"] == "closed":
        return CLOSED
    has_appt = conn.execute("SELECT 1 FROM appointments WHERE call_id = ?",
                            (call["id"],)).fetchone() is not None
    if outcome == "booked" and not has_appt:
        return error(409, "no_appointment", "Randevu yazılmadan booked ile kapatılamaz.")
    if has_appt and outcome != "booked":
        return error(409, "appointment_exists", "Bu çağrıda randevu var; sonuç booked olmalı.")
    if outcome in ("no_slot", "declined") and not call["verified"]:
        return error(409, "not_verified",
                     "Kimliği doğrulanmamış çağrı yalnız not_verified ile kapanabilir.")
    if outcome == "not_verified" and call["verified"]:
        return error(409, "already_verified", "Kimlik doğrulandı; not_verified kullanılamaz.")
    callback = close_call_row(conn, call, outcome, note)
    return 200, {"call_id": call["id"], "outcome": outcome, "callback": callback}


def close_call_row(conn, call, outcome: str, note: str) -> bool:
    callback = outcome in CALLBACK_OUTCOMES
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            "UPDATE calls SET status='closed', outcome=?, note=?, closed_at=CURRENT_TIMESTAMP "
            "WHERE id=?", (outcome, note, call["id"]))
        if callback:
            conn.execute("INSERT INTO callbacks (customer_id, call_id, reason) VALUES (?,?,?)",
                         (call["customer_id"], call["id"], outcome))
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return callback


@app.post("/calls/{call_id}/transcript", status_code=201)
def add_transcript(call_id: int, body: TranscriptLine):
    with db.connection() as conn:
        if get_call(conn, call_id) is None:
            return not_found(call_id)
        conn.execute("INSERT INTO transcripts (call_id, role, text) VALUES (?,?,?)",
                     (call_id, body.role, body.text))
        return {"ok": True}


# ---------- read / admin ----------

@app.get("/calls/{call_id}")
def get_call_detail(call_id: int):
    with db.connection() as conn:
        call = get_call(conn, call_id)
        if call is None:
            return not_found(call_id)
        appt = conn.execute(
            "SELECT a.id, s.* FROM appointments a JOIN slots s ON s.id = a.slot_id "
            "WHERE a.call_id = ?", (call_id,)).fetchone()
        rows = lambda sql: [dict(r) for r in conn.execute(sql, (call_id,)).fetchall()]
        return {
            "call_id": call["id"], "customer_id": call["customer_id"], "customer_name": call["name"],
            "status": call["status"], "outcome": call["outcome"], "note": call["note"],
            "name_confirmed": None if call["name_confirmed"] is None else bool(call["name_confirmed"]),
            "verified": bool(call["verified"]), "dob_attempts": call["dob_attempts"],
            "appointment": slot_dict(appt) if appt else None,
            "callbacks": rows("SELECT reason, due FROM callbacks WHERE call_id = ?"),
            "tool_log": rows("SELECT action, request, status_code, response FROM tool_log "
                             "WHERE call_id = ? ORDER BY id"),
            "transcript": rows("SELECT role, text FROM transcripts WHERE call_id = ? ORDER BY id"),
        }


@app.post("/admin/reset")
def admin_reset(body: Reset | None = None):
    with db.connection() as conn:
        db.reset(conn, (body.prefill if body else {}))
        return {"ok": True}


@app.post("/admin/fill")
def admin_fill(body: Fill):
    with db.connection() as conn:
        cur = conn.execute("UPDATE slots SET booked = capacity WHERE id = ?", (body.slot_id,))
        if cur.rowcount == 0:
            return JSONResponse(status_code=404, content={"error": "slot_not_found"})
        return {"ok": True, "slot_id": body.slot_id}
