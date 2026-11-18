"""Sesli arama, bas-konuş: python -m voice.main --customer 1 [--reset] [--debug]

Enter'a basınca kayıt başlar, tekrar Enter'a basınca biter. Kayıt → STT → CallSession → TTS → çalma.
İstemde Enter yerine metin yazılırsa STT atlanır (mikrofonsuz deneme). Komutlar: /fill <slot_id>, /kapat.
Her turun gecikmesi STT, LLM ve TTS ilk bayt olarak ayrı ayrı basılır.
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
from dataclasses import dataclass

import httpx
from openai import AsyncOpenAI

from assistant import config
from assistant.cli import print_summary, print_tool
from assistant.session import CallSession

from .audio import Player, Recorder
from .speech import TTS_VOICE, TTSStat, speak, transcribe

MIN_SECONDS = 0.3     # bundan kısa kayıt gönderilmez
MIN_PEAK = 0.01       # tepe seviye bunun altındaysa kayıt sessiz sayılır


@dataclass
class TurnLatency:
    stt_s: float | None   # yazılı girdide None
    llm_s: float
    tts_first_s: float | None   # asistan bir şey söylemediyse None

    @property
    def to_first_audio_s(self) -> float:
        """Müşterinin sözü bitti → asistanın ilk ses baytı."""
        return (self.stt_s or 0) + self.llm_s + (self.tts_first_s or 0)

    def line(self) -> str:
        stt = f"{self.stt_s:.2f} sn" if self.stt_s is not None else "-"
        tts = f"{self.tts_first_s:.2f} sn" if self.tts_first_s is not None else "-"
        return (f"    [gecikme] STT {stt} · LLM {self.llm_s:.2f} sn · TTS ilk bayt {tts} · "
                f"söz bitti→ilk ses {self.to_first_audio_s:.2f} sn")


class VoiceCall:
    """Bir aramanın ses tarafı. `play=False` ile ses çalınmaz, yalnız TTS akışı ölçülür."""

    def __init__(self, session: CallSession, oai: AsyncOpenAI, *, voice: str = TTS_VOICE,
                 play: bool = True):
        self.session = session
        self.oai = oai
        self.voice = voice
        self.play = play
        self.latencies: list[TurnLatency] = []

    async def say(self, text: str) -> TTSStat | None:
        if not text:
            return None
        if not self.play:
            async def discard(_: bytes) -> None:
                return None
            return await speak(self.oai, text, discard, voice=self.voice)
        player = Player()
        try:
            return await speak(self.oai, text, player.write, voice=self.voice)
        finally:
            await asyncio.to_thread(player.close)   # tampondaki ses bitene kadar bekler

    async def hear(self, wav: bytes) -> tuple[str, float]:
        started = time.perf_counter()
        text = await transcribe(self.oai, wav, self.session.customer_name)
        return text, time.perf_counter() - started

    async def respond(self, customer_text: str, stt_s: float | None) -> str:
        started = time.perf_counter()
        reply = await self.session.send(customer_text)
        llm_s = time.perf_counter() - started
        print(f"Asistan: {reply}")
        tts = await self.say(reply)
        lat = TurnLatency(stt_s, llm_s, tts.first_byte_s if tts else None)
        self.latencies.append(lat)
        print(lat.line())
        return reply

    async def opening(self) -> str:
        started = time.perf_counter()
        greeting = await self.session.start()
        llm_s = time.perf_counter() - started
        print(f"Asistan: {greeting}")
        tts = await self.say(greeting)
        print(TurnLatency(None, llm_s, tts.first_byte_s if tts else None).line())
        return greeting

    def print_latency_summary(self) -> None:
        rows = [("STT", [l.stt_s for l in self.latencies if l.stt_s is not None]),
                ("LLM", [l.llm_s for l in self.latencies]),
                ("TTS ilk bayt", [l.tts_first_s for l in self.latencies if l.tts_first_s is not None]),
                ("söz bitti→ilk ses", [l.to_first_audio_s for l in self.latencies])]
        print("--- Gecikme (müşteri turları, sn) ---")
        for name, vals in rows:
            if vals:
                print(f"{name:>18}: ort {statistics.mean(vals):.2f} · medyan "
                      f"{statistics.median(vals):.2f} · en çok {max(vals):.2f} (n={len(vals)})")


async def ask(prompt: str) -> str:
    try:
        return (await asyncio.to_thread(input, prompt)).strip()
    except EOFError:
        return "/kapat"


async def run(customer_id: int, reset: bool, debug: bool, voice: str, device: int | None) -> None:
    oai = AsyncOpenAI()   # OPENAI_API_KEY .env'den (assistant.config yükler)
    recorder = Recorder(device=device)
    async with httpx.AsyncClient(base_url=config.BANK_URL, timeout=15) as http:
        if reset:
            (await http.post("/admin/reset")).raise_for_status()
        session = CallSession(customer_id, http=http, on_tool=print_tool if debug else None)
        async with session:
            call = VoiceCall(session, oai, voice=voice)
            await call.opening()
            while not session.done:
                line = await ask("\n[Enter: konuş · metin yaz · /fill N · /kapat] > ")
                if line.startswith("/fill"):
                    slot_id = int(line.split()[1])
                    r = await http.post("/admin/fill", json={"slot_id": slot_id})
                    print(f"    [admin] slot {slot_id} dolduruldu -> {r.status_code}")
                    continue
                if line == "/kapat":
                    reply = await session.hangup()
                    if reply:   # hat kapandı: seslendirilmez
                        print(f"    (asistan, hat kapalı, okunmadı) {reply}")
                    continue
                if line:
                    await call.respond(line, stt_s=None)
                    continue
                recorder.start()
                await ask("● Kayıt sürüyor... bitirmek için Enter ")
                wav, seconds, peak = recorder.stop()
                if seconds < MIN_SECONDS or peak < MIN_PEAK:
                    print(f"    Ses alınamadı ({seconds:.1f} sn, seviye {peak:.3f}). Tekrar deneyin.")
                    continue
                text, stt_s = await call.hear(wav)
                if not text:
                    print("    Konuşma anlaşılamadı. Tekrar deneyin.")
                    continue
                print(f"Müşteri (STT, {seconds:.1f} sn ses): {text}")
                await call.respond(text, stt_s)
            await print_summary(http, session.call_id, session)
            call.print_latency_summary()


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Kart teslimatı asistanı, sesli mod (bas-konuş)")
    parser.add_argument("--customer", type=int, required=True, help="Müşteri id (1-8)")
    parser.add_argument("--reset", action="store_true", help="Önce DB'yi seed durumuna döndür")
    parser.add_argument("--debug", action="store_true", help="Tool çağrılarını göster")
    parser.add_argument("--voice", default=TTS_VOICE, help="TTS sesi (varsayılan marin)")
    parser.add_argument("--input-device", type=int, default=None,
                        help="Mikrofon cihaz no (python -m sounddevice ile listelenir)")
    args = parser.parse_args()
    asyncio.run(run(args.customer, args.reset, args.debug, args.voice, args.input_device))


if __name__ == "__main__":
    main()
