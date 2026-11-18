# CLAUDE.md

Freya FDE case: kuryenin ulaşamadığı müşterileri arayıp kart teslimatını yeniden planlayan sesli asistan.

- **Spec:** Kapsam, kurallar (R1–R12), endpoint'ler, tool'lar, senaryolar ve bitti tanımı [docs/spec.md](docs/spec.md) dosyasında. Kod yazmadan önce oku. Spec'ten sapacaksan önce sor. Case metni: [docs/Freya-FDE-On-Test.pdf](docs/Freya-FDE-On-Test.pdf).
- **Gerçek bilgi servisten gelir:** İş kuralları `bank_service` içinde (FastAPI + SQLite) zorlanır, sadece prompt'a yazılmaz. Asistan müşteri, yer, kapasite ve randevu bilgisini yalnız tool call ile servisten alır. Bu bilgileri prompt'a gömme ya da uydurma. Doğum tarihi LLM'e verilmez.
- **Önce dokümantasyon:** Claude Agent SDK (Python) ya da OpenAI API (STT/TTS) kodu yazmadan önce, kullanacağın API'yi, model adını ve parametreleri güncel resmi dokümantasyondan doğrula. Hafızaya güvenme.
- **Gizli anahtarlar:** `.env` dosyasında tutulur ve commit edilmez.
- **Plan ve durum:** [docs/plan.md](docs/plan.md). Aşama 1 (banka servisi) bitti, sıradaki Aşama 2 (yazılı modda asistan). Her aşama kabul kriterleri geçince commit edilir.

## Komutlar (Windows, `.venv`)
- Kurulum: `python -m venv .venv` ardından `.\.venv\Scripts\python -m pip install -r requirements.txt`
- Testler: `.\.venv\Scripts\python -m pytest -q`
- Servis: `.\.venv\Scripts\python -m uvicorn bank_service.app:app --port 8000`. DB yolu `BANK_DB` ortam değişkeninden okunur, varsayılan `bank.db`.

## Kod yapısı
- `bank_service/seed.py`: PDF tablolarındaki veri. `db.py`: şema ve reset. `app.py`: endpoint'ler ve iş kuralı korumaları.
- `tests/test_service.py`: servis testleri. Her test kendi geçici DB'sini kullanır.
