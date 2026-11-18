# Uygulama planı

Kaynak: [spec.md](spec.md). Aşamalar sırayla yapılır. Bir aşamanın kabul kriterlerinin hepsi geçince `main`'e commit atılır. 2 saat dolarsa o ana kadar yapılan iş yarım hâliyle commit edilir ve eksikler not edilir.

**Repo yapısı:** `bank_service/` · `assistant/` · `voice/` · `eval/` · `tests/` · `requirements.txt`

**Spec'e eklenenler (1. aşamada yapıldı):**
- `POST /calls/{id}/transcript {role, text}`: konuşmanın DB'ye yazılması için.
- `POST /admin/fill {slot_id}`: senaryo 6'da yeri arama sürerken doldurmak için.
- `tool_log`'u servis kendisi yazar: tool'lara karşılık gelen her istek (confirm_name, verify_dob, list_slots, book_appointment, close_call, no_answer) kaydedilir. Transkript yazımı kaydedilmez.

**Durum:** Aşama 1 ✅ bitti · Aşama 2 ⏳ · Aşama 3 ⏳ · Aşama 4 ⏳

---

## Aşama 1: Banka servisi (FastAPI + SQLite) — ✅ BİTTİ
- `db.py`: Tablolar customers, slots, calls, appointments (`UNIQUE customer_id`), callbacks, tool_log, transcripts.
- `seed.py`: PDF'teki 8 müşteri ve 5 yer.
- `app.py`: spec'teki endpoint'ler ve yukarıdaki iki ek.
  - Kapasite tek sorguyla atomik düşer: `UPDATE slots SET booked=booked+1 WHERE id=? AND booked<capacity`.
  - `close` endpoint'i outcome'a göre callback açar.
- `tests/test_service.py`: pytest.

**Kabul kriterleri**
- [x] `uvicorn bank_service.app:app` açılıyor. `/admin/reset` seed durumuna dönüyor.
- [x] pytest yeşil (30 test). Kapsadığı durumlar:
  - doğrulama 3. hatada kilitleniyor;
  - doğrulanmamış çağrıda `slots` 403 ve `appointments` 403 dönüyor;
  - 409 `slot_full`, 409 `already_booked` ve başka ilçe için 400 dönüyor;
  - randevu yokken `booked` reddediliyor, kapalı çağrıya yazma reddediliyor;
  - callback yalnız no_slot, not_verified ve not_reached sonuçlarında açılıyor.
- [x] Eşzamanlılık testi: 3 Kadıköy müşterisi aynı anda 1 kapasiteli yere istek atıyor, yalnız 1'i başarılı. Aynı müşteri 5 paralel istek atıyor, yalnız 1 randevu yazılıyor. (Kadıköy'de 3 müşteri olduğu için "5 farklı müşteri" yerine 3 kullanıldı.)
- [x] Commit: `stage 1: bank service`

**Uygulamada verilen ek kararlar:**
- `confirm-name` gelmeden `verify` 409 döner.
- Tarih formatı anlaşılamazsa 400 döner ve hak düşmez.
- Doğrulanmamış çağrı yalnız `not_verified` ile, doğrulanmış çağrı yalnız `booked`, `no_slot` ya da `declined` ile kapanır.
- `close` endpoint'i `not_reached` kabul etmez (422). Bu sonucu yalnız dialer `no-answer` ile yazar.

## Aşama 2: Yazılı modda asistan (Claude Agent SDK, Python)
- Kod yazmadan önce güncel dokümandan doğrula: `ClaudeSDKClient`, `@tool`, `create_sdk_mcp_server`, `allowed_tools`, yerleşik tool'ların kapatılması.
- `tools.py`: 5 tool. `call_id` closure ile bağlanır. httpx ile servisi çağırır. Hatalar Türkçe okunur metin olarak döner.
- `prompt.py`: R1–R12 kuralları. Prompt'ta yalnız müşterinin adı bulunur.
- `session.py`: girdi ve çıktıdan bağımsız arama döngüsü. Akış: `POST /calls` → asistan selamlar → sırayla konuşma, her tur transkripte yazılır → `close_call` gelince biter. Ses ve eval aynı sınıfı kullanır.
- `cli.py`: `python -m assistant.cli --customer 1`.

**Kabul kriterleri**
- [ ] Senaryo 1, 2 ve 6 elle oynanıyor. Senaryo 6'daki ara doldurma `/admin/fill` ile yapılıyor. Üçünde de DB'deki outcome beklenenle aynı.
- [ ] Asistan bu 5 tool dışında hiçbir tool çağıramıyor. Tool'larda customer_id ya da doğum tarihi parametresi yok.
- [ ] Doğrulamadan önce kart ya da teslimat sözü geçmiyor. Bu, transkriptte elle kontrol edilir.
- [ ] Arama `close_call` gelmeden bitmiyor, geldikten sonra hemen bitiyor.
- [ ] Commit: `stage 2: text-mode assistant`

## Aşama 3: Ses (OpenAI)
- Kod yazmadan önce güncel dokümandan doğrula: STT modeli (`gpt-4o-transcribe`, `language="tr"`), TTS modeli ve ses seçimi (`gpt-4o-mini-tts`).
- `voice/main.py`: `sounddevice` ile kayıt, Enter'a basınca başlar ve basınca durur. Akış: wav → STT → `session` → TTS → çalma. Ajan tarafı Aşama 2'deki kodla aynı.

**Kabul kriterleri**
- [ ] `python -m voice.main --customer 1` ile senaryo 1 mikrofonla baştan sona konuşuluyor ve DB'de `booked` yazılıyor.
- [ ] Türkçe isimler ve tarihler doğru yazıya dökülüyor. Örnek: "14 Mart 1988" doğrulamayı geçiyor.
- [ ] Her turun gecikmesi (STT, LLM, TTS ayrı ayrı) terminale basılıyor.
- [ ] Commit: `stage 3: voice`

## Aşama 4: Eval (simüle müşteriler + DB skoru)
- `scenarios.py`: 12 senaryo. Her senaryoda customer_id, ön doldurma, persona metni, tetikleyici ve beklenen DB durumu var. Senaryo 6'daki tetikleyici: `list_slots` sonrası `/admin/fill`.
- `simulator.py`: müşteriyi oynayan Claude. Tool'u yok, persona ile cevap veriyor. Tur sınırı 20.
- `checks.py`: deterministik kontroller DB'den okunur (outcome, randevu sayısı, kapasite ≥ 0, callback, tool_log sırası). R1, R2, R5 ve R8, DB'deki transkript üzerinden Claude hakemle evet/hayır olarak kontrol edilir.
- `run.py`: her senaryo için reset → arama → kontroller. 12 senaryo × 3 tekrar. Senaryo 12'de LLM çağrılmaz, dialer `no-answer` gönderir.

**Kabul kriterleri**
- [ ] `python -m eval.run` tek komutla çalışıyor. Senaryo bazında geçme oranını ve toplam skoru tablo hâlinde basıyor, sonuçları `eval/results.json` dosyasına yazıyor.
- [ ] Kasıtlı bozulmuş bir prompt ile skor düşüyor. Bu, kontrollerin gerçekten bir şey ölçtüğünü gösteriyor. Örnek bozulma: R5 onay adımını silmek.
- [ ] Başarısız kontroller ve bulunan hatalar video için `eval/findings.md` dosyasına not ediliyor.
- [ ] Commit: `stage 4: eval`
