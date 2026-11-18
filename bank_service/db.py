import os
import sqlite3
from contextlib import contextmanager

from .seed import CUSTOMERS, SLOTS

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    dob TEXT NOT NULL,
    district TEXT NOT NULL,
    address_type TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS slots (
    id INTEGER PRIMARY KEY,
    district TEXT NOT NULL,
    day TEXT NOT NULL,
    time_range TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    booked INTEGER NOT NULL DEFAULT 0,
    CHECK (booked >= 0 AND booked <= capacity)
);
CREATE TABLE IF NOT EXISTS calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    status TEXT NOT NULL DEFAULT 'open',
    name_confirmed INTEGER,
    verified INTEGER NOT NULL DEFAULT 0,
    dob_attempts INTEGER NOT NULL DEFAULT 0,
    outcome TEXT,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TEXT
);
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL UNIQUE REFERENCES customers(id),
    slot_id INTEGER NOT NULL REFERENCES slots(id),
    call_id INTEGER NOT NULL REFERENCES calls(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS callbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    call_id INTEGER NOT NULL REFERENCES calls(id),
    reason TEXT NOT NULL,
    due TEXT NOT NULL DEFAULT 'next_week',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tool_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    request TEXT,
    status_code INTEGER NOT NULL,
    response TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id INTEGER NOT NULL REFERENCES calls(id),
    role TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

TABLES = ["transcripts", "tool_log", "callbacks", "appointments", "calls", "slots", "customers"]


def db_path() -> str:
    return os.environ.get("BANK_DB", "bank.db")


def connect() -> sqlite3.Connection:
    # isolation_level=None: transactions are explicit (BEGIN IMMEDIATE) where needed.
    conn = sqlite3.connect(db_path(), timeout=10, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    if conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
        reset(conn)


def reset(conn: sqlite3.Connection, prefill: dict[int, int] | None = None) -> None:
    """Wipe everything and load the seed. prefill = {slot_id: booked_count}."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        for t in TABLES:
            conn.execute(f"DELETE FROM {t}")
        conn.execute("DELETE FROM sqlite_sequence")
        conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?)", CUSTOMERS)
        conn.executemany(
            "INSERT INTO slots (id, district, day, time_range, capacity) VALUES (?,?,?,?,?)", SLOTS
        )
        for slot_id, booked in (prefill or {}).items():
            conn.execute(
                "UPDATE slots SET booked = MIN(capacity, ?) WHERE id = ?", (booked, slot_id)
            )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
