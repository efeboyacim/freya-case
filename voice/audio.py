"""Mikrofon kaydı (bas-konuş) ve hoparlörden PCM çalma. sounddevice kullanır.

TTS çıktısı 24 kHz, 16 bit, mono, little-endian ham PCM'dir; çalma da bu biçimdedir.
"""

from __future__ import annotations

import asyncio
import io
import threading
import wave

import numpy as np
import sounddevice as sd

TTS_RATE = 24_000      # gpt-4o-mini-tts response_format="pcm"
REC_RATE = 24_000      # MME/DirectSound örnekleme hızını kendisi dönüştürür


def to_wav(pcm: bytes, rate: int) -> bytes:
    """Ham 16 bit mono PCM'i WAV dosyası baytlarına çevirir (STT dosya ister)."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


class Recorder:
    """start() ile kayıt başlar, stop() kaydı WAV baytı ve süresiyle döner."""

    def __init__(self, rate: int = REC_RATE, device: int | None = None):
        self.rate = rate
        self.device = device
        self._chunks: list[bytes] = []
        self._lock = threading.Lock()
        self._stream: sd.RawInputStream | None = None

    def _callback(self, indata, frames, time_info, status) -> None:
        with self._lock:
            self._chunks.append(bytes(indata))

    def start(self) -> None:
        self._chunks = []
        try:
            self._stream = sd.RawInputStream(samplerate=self.rate, channels=1, dtype="int16",
                                             device=self.device, callback=self._callback)
        except sd.PortAudioError:
            # Cihaz 24 kHz desteklemiyorsa kendi varsayılan hızına düşülür.
            self.rate = int(sd.query_devices(self.device, "input")["default_samplerate"])
            self._stream = sd.RawInputStream(samplerate=self.rate, channels=1, dtype="int16",
                                             device=self.device, callback=self._callback)
        self._stream.start()

    def stop(self) -> tuple[bytes, float, float]:
        """(wav baytları, süre sn, tepe seviye 0–1) döner."""
        assert self._stream is not None
        self._stream.stop()
        self._stream.close()
        self._stream = None
        with self._lock:
            pcm = b"".join(self._chunks)
        return to_wav(pcm, self.rate), len(pcm) / 2 / self.rate, peak_level(pcm)


def peak_level(pcm: bytes) -> float:
    """0–1 arası tepe seviye; boş ya da sessiz kaydı yakalamak için."""
    if not pcm:
        return 0.0
    return float(np.abs(np.frombuffer(pcm, dtype=np.int16)).max()) / 32768


class Player:
    """Gelen PCM parçalarını sırayla çalar. Tek bayt artığı bir sonraki parçaya taşınır."""

    def __init__(self, rate: int = TTS_RATE, device: int | None = None):
        self._stream = sd.RawOutputStream(samplerate=rate, channels=1, dtype="int16",
                                          device=device)
        self._stream.start()
        self._rest = b""

    async def write(self, chunk: bytes) -> None:
        data = self._rest + chunk
        cut = len(data) - len(data) % 2
        self._rest = data[cut:]
        if cut:
            await asyncio.to_thread(self._stream.write, data[:cut])

    def close(self) -> None:
        self._stream.stop()      # stop() tampondaki sesin çalınmasını bekler
        self._stream.close()
