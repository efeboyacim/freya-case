"""Mikrofonsuz ses testi. Müşteri sözleri başka bir TTS sesiyle sentezlenir ve STT'ye verilir.

    python -m voice.selftest stt                 # tarih ve isim cümlelerinin STT sonucu
    python -m voice.selftest call [--play]       # senaryo 1: sentezlenmiş müşteriyle tam arama

Mikrofon, hoparlör ve gerçek insan sesi bu testin dışındadır; onlar için voice.main kullanılır.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import httpx
from openai import AsyncOpenAI

from assistant import config
from assistant.cli import print_summary, print_tool
from assistant.session import CallSession

from .audio import TTS_RATE, to_wav
from .main import VoiceCall
from .speech import speak, transcribe

CUSTOMER_VOICE = "cedar"   # asistan marin, müşteri farklı ses

STT_PHRASES = [
    ("Ayşe Kaya", "Evet, Ayşe Kaya benim."),
    ("Ayşe Kaya", "On dört Mart bin dokuz yüz seksen sekiz."),
    ("Ayşe Kaya", "Doğum tarihim 14 Mart 1988."),
    ("Mehmet Demir", "İki Kasım yetmiş beş."),
    ("Elif Şahin", "Otuz Ağustos doksan."),
    ("Burak Çelik", "Perşembe olmaz, Cuma öğleden sonra olur mu?"),
]

# Senaryo 1 (Ayşe Perşembe'yi seçer): asistanın beklenen sorularına sırayla cevaplar.
SCENARIO_1 = [
    "Evet, benim.",
    "On dört Mart bin dokuz yüz seksen sekiz.",
    "Perşembe olsun.",
    "Evet, onaylıyorum.",
    "Hayır, teşekkür ederim.",
]


async def synth(oai: AsyncOpenAI, text: str) -> bytes:
    pcm = bytearray()

    async def collect(chunk: bytes) -> None:
        pcm.extend(chunk)
    await speak(oai, text, collect, voice=CUSTOMER_VOICE)
    return to_wav(bytes(pcm), TTS_RATE)


async def stt_check() -> None:
    oai = AsyncOpenAI()
    for name, phrase in STT_PHRASES:
        text = await transcribe(oai, await synth(oai, phrase), name)
        print(f"söylenen: {phrase!r}\n  STT   : {text!r}")


async def call_check(play: bool, debug: bool) -> None:
    oai = AsyncOpenAI()
    async with httpx.AsyncClient(base_url=config.BANK_URL, timeout=15) as http:
        (await http.post("/admin/reset")).raise_for_status()
        session = CallSession(1, http=http, on_tool=print_tool if debug else None)
        async with session:
            call = VoiceCall(session, oai, play=play)
            await call.opening()
            for phrase in SCENARIO_1:
                if session.done:
                    break
                text, stt_s = await call.hear(await synth(oai, phrase))
                print(f"\nMüşteri (söylenen: {phrase!r}) STT: {text}")
                await call.respond(text, stt_s)
            if not session.done:
                print("\nUYARI: senaryo cümleleri bitti, arama kapanmadı.")
            await print_summary(http, session.call_id, session)
            call.print_latency_summary()


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=["stt", "call"])
    parser.add_argument("--play", action="store_true", help="Asistanın sesini hoparlörden çal")
    parser.add_argument("--debug", action="store_true", help="Tool çağrılarını göster")
    args = parser.parse_args()
    asyncio.run(stt_check() if args.mode == "stt" else call_check(args.play, args.debug))


if __name__ == "__main__":
    main()
