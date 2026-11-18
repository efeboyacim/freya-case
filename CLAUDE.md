# CLAUDE.md

Freya FDE case: kuryenin ulaşamadığı müşterileri arayıp kart teslimatını yeniden planlayan sesli asistan.

- **Spec:** Kapsam, kurallar (R1–R12), endpoint'ler, tool'lar, senaryolar ve bitti tanımı [docs/spec.md](docs/spec.md) dosyasında. Kod yazmadan önce oku. Spec'ten sapacaksan önce sor. Case metni: [docs/Freya-FDE-On-Test.pdf](docs/Freya-FDE-On-Test.pdf).
- **Gerçek bilgi servisten gelir:** İş kuralları `bank_service` içinde (FastAPI + SQLite) zorlanır, sadece prompt'a yazılmaz. Asistan müşteri, yer, kapasite ve randevu bilgisini yalnız tool call ile servisten alır. Bu bilgileri prompt'a gömme ya da uydurma. Doğum tarihi LLM'e verilmez.
- **Önce dokümantasyon:** Claude Agent SDK (Python) ya da OpenAI API (STT/TTS) kodu yazmadan önce, kullanacağın API'yi, model adını ve parametreleri güncel resmi dokümantasyondan doğrula. Hafızaya güvenme.
- **Gizli anahtarlar:** `.env` dosyasında tutulur ve commit edilmez.
- **Plan ve durum:** [docs/plan.md](docs/plan.md). Aşama 1 (banka servisi), Aşama 2 (yazılı modda asistan) ve Aşama 3 (ses, bas-konuş) ve Aşama 4 (eval, kısaltılmış koşu; bulgular `eval/findings.md`) bitti. Sıradaki yalnız Aşama 3b (opsiyonel, streaming ses); açık iş: R7'yi güvenilir kapatmak ve tam 36 aramalık koşu. Her aşama kabul kriterleri geçince commit edilir.

## Komutlar (Windows, `.venv`)
- Kurulum: `python -m venv .venv` ardından `.\.venv\Scripts\python -m pip install -r requirements.txt`
- Testler: `.\.venv\Scripts\python -m pytest -q`
- Servis: `.\.venv\Scripts\python -m uvicorn bank_service.app:app --port 8000`. DB yolu `BANK_DB` ortam değişkeninden okunur, varsayılan `bank.db`.
- Yazılı arama (servis açıkken): `.\.venv\Scripts\python -m assistant.cli --customer 1 --reset --debug`. `/fill <slot_id>` yeri doldurur, `/kapat` müşterinin kapattığını bildirir. `.env` içinde `ANTHROPIC_API_KEY` gerekir; `BANK_URL`, `ASSISTANT_MODEL` (varsayılan `claude-sonnet-5-5`), `ASSISTANT_EFFORT` (varsayılan `low`) isteğe bağlı.
- Sesli arama (servis açıkken): `.\.venv\Scripts\python -m voice.main --customer 1 --reset --debug`. Enter kaydı başlatır ve bitirir; metin yazmak STT'yi atlar. `.env` içinde `OPENAI_API_KEY` gerekir. Mikrofon listesi: `python -m sounddevice`, seçim `--input-device N`.
- Eval (servis açıkken, aramalar sıralı): `.\.venv\Scripts\python -m eval.run [--only 1,6] [--reps 3] [--personas a,b] [--tag ad] [--variant broken_r5]`. Sonuç `eval/runs/<tarih>[-tag]/` (`summary.md`, `results.jsonl`, `transcripts/`). Paralel koşular için her parçaya ayrı servis (`BANK_DB`, port) ve `BANK_URL` verilir, sonra `--merge klasör1,klasör2 --tag ad` ile birleştirilir. `.env` içinde `ANTHROPIC_API_KEY` gerekir.
- Mikrofonsuz ses testi: `python -m voice.selftest stt` (tarih/isim STT'si) ve `python -m voice.selftest call [--play]` (senaryo 1, sentezlenmiş müşteri sesiyle).

## Kod yapısı
- `bank_service/seed.py`: PDF tablolarındaki veri. `db.py`: şema ve reset. `app.py`: endpoint'ler ve iş kuralı korumaları.
- `assistant/tools.py`: 5 tool, `call_id` closure'da, servis hataları `is_error` + `"HATA <kod>: ..."`. `prompt.py`: R1–R12, yalnız müşteri adı eklenir. `session.py`: `CallSession` (`start`, `send`, `hangup`, `done`), ses ve eval de bunu kullanır; ajan ayarları `build_options` içinde (`tools=[]`, `dontAsk`, `setting_sources=[]`, `strict_mcp_config`, tool search kapalı). `cli.py`: yazılı mod.
- `voice/audio.py`: kayıt ve pcm çalma (24 kHz mono int16). `speech.py`: STT `gpt-transcribe` (`languages=["tr"]`, `prompt`, `keywords`; doğum tarihi verilmez), TTS `gpt-4o-mini-tts` pcm streaming (6 Ocak 2027'de kapanacak). `main.py`: `VoiceCall` (`opening`, `hear`, `respond`, `say`) ve tur başı gecikme. `selftest.py`: mikrofonsuz test.
- `eval/`: `scenarios.py` (12 senaryo, ne olacağı), `personas.py` (6 persona, nasıl konuşulacağı; tekrar *k* için `(senaryo + k) mod 6`), `simulator.py` (müşteri rolündeki Claude, tool'suz), `checks.py` (17 kontrol, sabit zarar puanı; deterministik olanlar DB'den, R1/R2/R5/R6/R7/R8/R9 ve uydurma Claude hakemle), `run.py`, `findings.md`.
- `tests/test_service.py`: servis testleri. `tests/test_assistant.py`: LLM'siz tool/ayar/prompt testleri (servis ASGI üzerinden). `tests/test_voice.py`: ağsız ses testleri. Her test kendi geçici DB'sini kullanır.
