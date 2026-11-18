"""Ortam ayarları. `.env` dosyası burada yüklenir (SDK kendisi okumaz)."""

import os

from dotenv import load_dotenv

load_dotenv()

BANK_URL = os.getenv("BANK_URL") or "http://127.0.0.1:8000"
MODEL = os.getenv("ASSISTANT_MODEL") or "claude-sonnet-5-5"
EFFORT = os.getenv("ASSISTANT_EFFORT") or "low"
