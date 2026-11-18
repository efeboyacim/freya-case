"""OpenAI STT (gpt-transcribe) ve TTS (gpt-4o-mini-tts, pcm streaming).

Doküman (2026-11-18): gpt-transcribe için tek dil alanı `language` değil `languages` listesi;
`prompt` ve `keywords` destekleniyor. gpt-4o-mini-tts 6 Ocak 2027'de kapanacak (bkz. plan.md).
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Awaitable, Callable

from openai import AsyncOpenAI

from assistant import config  # noqa: F401  .env burada yüklenir

STT_MODEL = os.getenv("STT_MODEL") or "gpt-transcribe"
TTS_MODEL = os.getenv("TTS_MODEL") or "gpt-4o-mini-tts"
TTS_VOICE = os.getenv("TTS_VOICE") or "marin"

TTS_INSTRUCTIONS = (
    "Türkçe konuşan, bir bankanın telefon asistanısın. Sıcak, sakin ve profesyonel bir tonla, "
    "orta hızda konuş. Gün, saat ve tarihleri tane tane ve net oku."
)


def stt_prompt(customer_name: str | None) -> str:
    """STT bağlamı. Yalnız konuyu ve müşteri adını içerir; kayıtlı doğum tarihi verilmez."""
    parts = ["Türkçe telefon görüşmesi. Banka, müşterinin kredi kartı teslimatını yeniden "
             "planlamak için arıyor. Müşteri adını onaylayabilir, doğum tarihini gün, ay ve yıl "
             "olarak söyleyebilir, Perşembe ya da Cuma gibi bir gün seçebilir."]
    if customer_name:
        parts.append(f"Aranan kişi: {customer_name}.")
    return " ".join(parts)


MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül",
          "Ekim", "Kasım", "Aralık"]


def stt_keywords(customer_name: str | None) -> list[str]:
    """Genel ifadeler ve müşteri adı. Kayıtlı doğum tarihi ya da ilçe bilgisi eklenmez."""
    words = ["Perşembe", "Cuma", *MONTHS]
    if customer_name:
        words.insert(0, customer_name)
    return words


async def transcribe(client: AsyncOpenAI, wav: bytes, customer_name: str | None) -> str:
    result = await client.audio.transcriptions.create(
        model=STT_MODEL,
        file=("turn.wav", wav, "audio/wav"),
        languages=["tr"],
        prompt=stt_prompt(customer_name),
        keywords=stt_keywords(customer_name),
    )
    return result.text.strip()


@dataclass
class TTSStat:
    first_byte_s: float      # istekten ilk ses baytına
    total_s: float           # istekten son baytın çalınmasına
    audio_bytes: int


async def speak(client: AsyncOpenAI, text: str,
                sink: Callable[[bytes], Awaitable[None]], *, voice: str = TTS_VOICE) -> TTSStat:
    """Metni pcm olarak akıtır; her parça geldiği anda `sink`e verilir (çalma ilk parçayla başlar)."""
    started = time.perf_counter()
    first: float | None = None
    total = 0
    async with client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=voice,
        input=text,
        instructions=TTS_INSTRUCTIONS,
        response_format="pcm",
    ) as response:
        async for chunk in response.iter_bytes(4096):
            if first is None:
                first = time.perf_counter() - started
            total += len(chunk)
            await sink(chunk)
    end = time.perf_counter() - started
    return TTSStat(first_byte_s=first if first is not None else end, total_s=end, audio_bytes=total)
