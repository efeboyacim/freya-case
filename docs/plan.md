# Uygulama planı

Kaynak: [spec.md](spec.md). Aşamalar sırayla yapılır. Bir aşamanın kabul kriterlerinin hepsi geçince `main`'e commit atılır. 2 saat dolarsa o ana kadar yapılan iş yarım hâliyle commit edilir ve eksikler not edilir.

**Repo yapısı:** `bank_service/` · `assistant/` · `voice/` · `eval/` · `tests/` · `requirements.txt`

**Spec'e eklenenler (1. aşamada yapıldı):**
- `POST /calls/{id}/transcript {role, text}`: konuşmanın DB'ye yazılması için.
- `POST /admin/fill {slot_id}`: senaryo 6'da yeri arama sürerken doldurmak için.
- `tool_log`'u servis kendisi yazar: tool'lara karşılık gelen her istek (confirm_name, verify_dob, list_slots, book_appointment, close_call, no_answer) kaydedilir. Transkript yazımı kaydedilmez.

**Durum:** Aşama 1 ✅ bitti · Aşama 2 ✅ bitti · Aşama 3 ⏳ · Aşama 4 ⏳

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

## Aşama 2: Yazılı modda asistan (Claude Agent SDK, Python) — ✅ BİTTİ

**Dokümandan doğrulananlar (2026-11-18, code.claude.com/docs/en/agent-sdk):**
- Paket `claude-agent-sdk`. Python 3.10+ ister (bizde 3.10.11). Claude Code binary'si wheel içinde gelir, ayrı kurulum gerekmez.
- Kimlik bilgisi `ANTHROPIC_API_KEY`. SDK `.env` okumaz, `python-dotenv` ile biz yükleriz.
- Tool: `@tool(name, description, input_schema)` ve `async def handler(args)`. Handler `{"content": [{"type": "text", "text": ...}], "is_error": bool}` döner. Enum ve opsiyonel alan için tam JSON Schema dict verilir.
- Sunucu: `create_sdk_mcp_server(name, version, tools=[...])` ve `ClaudeAgentOptions(mcp_servers={"bank": server})`. Tool adları `mcp__bank__<ad>` olur.
- `tools=[]` tüm yerleşik tool'ları bağlamdan çıkarır. `allowed_tools` yalnız ön onay verir, kısıtlamaz.
- Tool search varsayılan olarak açık ve MCP tool'larını erteliyor (`ToolSearch` çağrısı ve fazladan bir tur). `env={"ENABLE_TOOL_SEARCH": "false"}` ile kapatılır.
- `setting_sources=[]` dosya sistemindeki ayarları (bu repodaki CLAUDE.md dahil) yüklemez.
- Çok turlu konuşma: `async with ClaudeSDKClient(options) as c`, ardından `await c.query(text)` ve `async for m in c.receive_response()`. Akış `ResultMessage` ile biter. Döngüden `break` ile çıkılmaz.
- Mesajlar: `AssistantMessage.content` içinde `TextBlock.text` ve `ToolUseBlock(id, name, input)` bulunur. `ResultMessage` alanları: `subtype`, `is_error`, `num_turns`, `total_cost_usd`.
- Model `claude-sonnet-5-5` (dokümanda "Fast", ses gecikmesi için seçildi). `ASSISTANT_MODEL` ortam değişkeniyle değiştirilebilir.

**Dosyalar**
```
assistant/
  __init__.py
  config.py    # .env yükler; BANK_URL (varsayılan http://127.0.0.1:8000), ASSISTANT_MODEL
  tools.py     # build_bank_server(state, http, on_tool=None) -> server; state.call_id closure'da
  prompt.py    # build_system_prompt(customer_name) -> str
  session.py   # CallSession: girdi ve çıktıdan bağımsız arama döngüsü
  cli.py       # python -m assistant.cli --customer N
tests/test_assistant.py   # LLM'siz testler
```
`requirements.txt` dosyasına `claude-agent-sdk` ve `python-dotenv` eklenir. `.env.example` dosyası `ANTHROPIC_API_KEY=`, `BANK_URL=` ve `ASSISTANT_MODEL=` satırlarını içerir.

**2.1 `tools.py`:** 5 tool'un hepsi `build_bank_server` içinde closure olarak tanımlanır. `call_id` ve `httpx.AsyncClient` dışarıdan gelir, LLM bunları göremez.

| Tool | Şema | Servis |
|---|---|---|
| `confirm_identity_name` | `{is_customer: bool}` | `POST /calls/{id}/confirm-name` |
| `verify_dob` | `{spoken_date: str}`: müşterinin söylediği tarih, GG.AA.YYYY biçimine çevrilmiş | `POST /calls/{id}/verify` |
| `list_slots` | `{}` | `GET /calls/{id}/slots` |
| `book_appointment` | `{slot_id: int}` | `POST /calls/{id}/appointments` |
| `close_call` | `{outcome: enum[booked, no_slot, declined, not_verified], note?: str}` | `POST /calls/{id}/close` |

- 2xx yanıtında servisin JSON'u `ensure_ascii=False` ile metin olarak döner. 4xx yanıtında `is_error: True` döner, metin `"HATA <kod>: <servisin Türkçe message'ı>"` olur. Ağ hatasında da `is_error: True` döner, metin "Banka servisine ulaşılamadı, müşteriye teknik sorun olduğunu söyle." olur.
- `close_call` 200 dönünce `state.closed = True` ve `state.outcome` atanır. Hata dönerse çağrı kapanmış sayılmaz.
- `on_tool(name, args, status, body)` geri çağrısı CLI'da debug çıktısı için kullanılır. Aşama 4'te senaryo 6'nın tetikleyicisi de bu olur (`list_slots` sonrası `/admin/fill`).
- Tool açıklamaları Türkçe ve kısadır, ne zaman çağrılacağını söyler. Örnek, `book_appointment` için: "Yalnız müşteri tekrar okunan yeri açıkça onayladıktan sonra çağır."

**2.2 `prompt.py`:** Sabit metne yalnız `{customer_name}` eklenir. İlçe, yer, kapasite ve doğum tarihi prompt'ta yer almaz.
- Rol: bankanın dijital asistanı, Türkçe ve telefonda konuşuyor. Kısa cümle kurar, madde işareti ve markdown kullanmaz, her turda tek soru sorar. Böylece ses moduna hazır olur.
- Akış ve R1–R12 kuralları tool adlarıyla eşlenir: açılış ve isim sorusu → `confirm_identity_name` → doğum tarihi → `verify_dob` → `list_slots` → yeri tekrar okuma ve onay → `book_appointment` → R8 hatırlatması → `close_call`.
- Tool sonucuna bağlılık: "Yer, gün, saat ve adres tipini yalnız `list_slots` ve `book_appointment` sonucundan söyle. Tool 'HATA' dönerse 'ayarlandı' deme."
- Bağlam olarak yalnız "Bugün Çarşamba" bilgisi verilir. Yerlerin günü yine tool'dan gelir.
- Kapanış: asistan vedayı söyler ve aynı turda `close_call` çağırır. Sistem notları `[SİSTEM]` önekiyle gelir ve müşteri sözü sayılmaz.

**2.3 `session.py`:** `CallSession` bir async context manager'dır.
```python
async with CallSession(customer_id, http=None, on_tool=None) as s:
    greeting = await s.start()          # POST /calls ve asistanın açılış cümlesi
    while not s.closed:
        reply = await s.send(customer_text)
    s.call_id, s.outcome, s.turn_stats  # tur başına LLM süresi (Aşama 3 için)
```
- `start()`: `POST /calls` ile `customer_name` alınır. Prompt, server ve options kurulur, `ClaudeSDKClient` bağlanır. Ardından `[SİSTEM] Arama bağlandı, müşteri telefonu açtı.` notu gönderilir. Bu not transkripte yazılmaz.
- `send(text)`: müşteri satırı `/transcript`'e yazılır. `query` gönderilir ve `receive_response` sonuna kadar okunur. `TextBlock`'lar birleştirilip asistan satırı olarak yazılır ve döndürülür.
- Options:
  - `system_prompt=<str>` ve `model`
  - `tools=[]`, `mcp_servers={"bank": server}`, `allowed_tools=<5 tam ad>`
  - `permission_mode="dontAsk"`: listede olmayan her tool reddedilir.
  - `setting_sources=[]` ve `env={"ENABLE_TOOL_SEARCH": "false"}`
  - `max_turns=10`: tek müşteri turundaki ajan döngüsünün sınırı.
- Bekçiler:
  - İlk `SystemMessage(init)` içindeki tool listesi 5 tool'un dışına çıkarsa hata verilir. Bu, deterministik kanıt olur. *Alan adı uygularken doğrulanacak.*
  - 5 tool dışında bir `ToolUseBlock` görülürse `violations` listesine yazılır.
  - `closed` olunca yanıt biter bitmez oturum kapanır, `send` artık çağrılamaz.
  - Müşteri kapatırsa (`hangup()`) ya da 20 müşteri turu aşılırsa bir kez şu not gönderilir: `[SİSTEM] Müşteri hattan düştü / süre doldu. Uygun sonuçla close_call çağır.` Yine kapanmazsa oturum `outcome=None` ile biter ve uyarı verir. Servise uydurma sonuç yazılmaz.

**2.4 `cli.py`:** `python -m assistant.cli --customer 1 [--reset] [--debug]`
- `--reset` önce `/admin/reset` çağırır. Müşteri girdisi `Müşteri: ` istemiyle okunur.
- Komutlar: `/fill <slot_id>` `/admin/fill` çağırır (senaryo 6). `/kapat` `hangup()` çağırır.
- `--debug` tool çağrılarını basar, örneğin `[tool] list_slots() → 200 {...}`.
- Arama bitince `GET /calls/{id}` özeti basılır: outcome, randevu, callback ve tool_log sırası.

**2.5 `tests/test_assistant.py`:** LLM ve ağ kullanılmaz, servis `httpx.ASGITransport` ile aynı süreçte çalışır.
- Sunucuda tam 5 tool var. Hiçbir şemada `customer_id`, `call_id` ya da `dob` adlı alan yok.
- Doğrulama öncesi `list_slots` çağrısı `is_error` ve "HATA 403" metni döner. `book_appointment` 409 `slot_full` aldığında `is_error` ve okunur metin döner.
- Başarılı `close_call` `state.closed` değerini açar. Hatalı `close_call` çağrıyı kapanmış saymaz.
- `build_options()` sonucunda `tools == []`, `allowed_tools` tam 5 ad, `setting_sources == []` ve tool search kapalı.
- Prompt'ta müşteri adı var. Seed'deki doğum tarihleri, ilçeler ve saat aralıkları yok.

**Sıra (yaklaşık 40 dk):**
1. Bağımlılıklar ve config (5 dk)
2. Tools ve testleri (10 dk)
3. Prompt (5 dk)
4. Session (10 dk)
5. CLI (5 dk)
6. Senaryo 1, 2 ve 6'yı elle oynama (5 dk)
7. plan.md ve CLAUDE.md güncelleme, commit

**Kabul kriterleri**
- [x] `pytest -q` yeşil: 42 test (31 servis, 11 asistan).
- [x] Senaryo 1, 2 ve 6 CLI ile oynandı. Senaryo 6'daki ara doldurma `/fill 1` komutuyla yapıldı. Üçünde de DB'deki outcome beklenenle aynı:
  - 1: `booked`, Perşembe yerinde kalan 0.
  - 2: `not_verified` ve callback açıldı. `list_slots` hiç çağrılmadı.
  - 6: 409 `slot_full` → `list_slots` → `booked` Cuma.
- [x] Asistan bu 5 tool dışında hiçbir tool çağıramıyor. init mesajındaki tool listesi tam olarak 5 `mcp__bank__*` tool'u. `violations` boş.
- [x] Tool'larda `customer_id` parametresi yok. Kayıtlı doğum tarihi hiçbir tool yanıtında ve prompt'ta yer almıyor. `verify_dob` yalnız müşterinin söylediği tarihi alıyor.
- [x] Doğrulamadan önce kart ya da teslimat sözü geçmiyor. Üç transkriptte de elle kontrol edildi.
- [x] Arama `close_call` gelmeden bitmiyor, geldikten sonra hemen bitiyor (`session.done`).
- [x] Commit: `stage 2: text-mode assistant`

**Uygulamada verilen ek kararlar:**
- **R8 iki turda yapılıyor.** İlk denemelerde model `book_appointment` ile `close_call`'u art arda çağırdı ve teyit ile R8 hatırlatmasını atladı. Çözüm:
  - 201 sonrası `book_appointment` sonucuna `next` alanı eklendi.
  - Prompt'a şu akış yazıldı: teyit + sabit R8 cümlesi + "Başka bir sorunuz var mı?" Müşteri cevap verince `close_call(booked)` çağrılır.
- **Tek veda.** `close_call`'dan sonra gelen metin, aynı turda daha önce bir şey söylendiyse atılır. Böylece tek veda kalır.
- **Model ayarları.** `effort="low"` kullanılıyor; bir LLM turu yaklaşık 1–7 sn sürüyor. `ASSISTANT_EFFORT` ile değiştirilebilir. Yalnız MCP sunucumuzun yüklenmesi için `strict_mcp_config=True` eklendi.
- **Aşama 1 hatası düzeltildi.** `GET /calls/{id}` yanıtında `appointment.slot_id` alanı randevu id'sini gösteriyordu (`a.id` ile `s.id` çakışıyordu). Bunu yakalayan bir test eklendi.
- **`CallSession` alanları.** Aşama 3 ve 4 için şu alanları tutuyor: `turn_stats` (LLM süresi), `events` (blok sırası), `init_tools`, `violations`. Senaryo tetikleyicileri için `on_tool` geri çağrısı var.
- **Git Bash notu.** `/fill 1` komut satırı argümanı olarak verilirse Git Bash onu dosya yoluna çeviriyor. CLI'da stdin üzerinden sorun yok.

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
