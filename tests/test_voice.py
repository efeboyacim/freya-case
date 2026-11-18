"""Ses katmanı testleri. Ağ, mikrofon ve hoparlör kullanılmaz."""

import io
import wave

from bank_service.seed import CUSTOMERS
from voice.audio import peak_level, to_wav
from voice.main import TurnLatency
from voice.speech import stt_keywords, stt_prompt


def test_to_wav_header():
    pcm = b"\x00\x01" * 2400
    with wave.open(io.BytesIO(to_wav(pcm, 24_000))) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, 24_000)
        assert w.getnframes() == 2400


def test_peak_level():
    assert peak_level(b"") == 0.0
    assert peak_level(b"\x00\x00" * 10) == 0.0
    assert peak_level((16384).to_bytes(2, "little", signed=True)) == 0.5


def test_stt_context_has_name_but_no_dob():
    for _, name, _, dob, district, _ in CUSTOMERS:
        y, m, d = dob.split("-")
        texts = [stt_prompt(name), " ".join(stt_keywords(name))]
        for text in texts:
            assert name in text
            for leak in (dob, y, f"{d}.{m}", district):
                assert leak not in text


def test_latency_sum():
    lat = TurnLatency(stt_s=0.5, llm_s=2.0, tts_first_s=0.6)
    assert abs(lat.to_first_audio_s - 3.1) < 1e-9
    assert "STT 0.50 sn" in lat.line()
    assert "STT -" in TurnLatency(None, 1.0, None).line()
