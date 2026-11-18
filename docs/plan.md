# Uygulama planı

Kaynak: [spec.md](spec.md). Aşamalar sırayla yapılır. Bir aşamanın kabul kriterlerinin hepsi geçince `main`'e commit atılır. 2 saat dolarsa o ana kadar yapılan iş yarım hâliyle commit edilir ve eksikler not edilir.

**Repo yapısı:** `bank_service/` · `assistant/` · `voice/` · `eval/` · `tests/` · `requirements.txt`

**Spec'e eklenenler (1. aşamada yapıldı):**
- `POST /calls/{id}/transcript {role, text}`: konuşmanın DB'ye yazılması için.
- `POST /admin/fill {slot_id}`: senaryo 6'da yeri arama sürerken doldurmak için.
- `tool_log`'u servis kendisi yazar: tool'lara karşılık gelen her istek (confirm_name, verify_dob, list_slots, book_appointment, close_call, no_answer) kaydedilir. Transkript yazımı kaydedilmez.

**Durum:** Aşama 1 ✅ bitti · Aşama 2 ✅ bitti · Aşama 3 ✅ bitti · Aşama 3b (opsiyonel) ⏳ · Aşama 4 ✅ bitti (kısaltılmış koşu)

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
- **R2 kapanışı.** Asistan kendini yalnız açılışta tanıtıyor; "kim arıyor?" sorulsa bile tanıtımı tekrarlamıyor. Telefonu başkası açtıysa gerekçe olarak yalnız "Bu konuyu yalnız <müşteri> ile görüşebiliyorum" diyor. Kart ya da teslimat geçmediği için R1 ve R2 korunuyor. Senaryo 2 üç kez koşuldu, üçünde de tutarlı.

## Aşama 3: Ses (OpenAI) — bas-konuş — ✅ BİTTİ

**Dokümandan doğrulananlar (2026-11-18, developers.openai.com/api/docs):**
- STT: `gpt-transcribe`, `/v1/audio/transcriptions` üzerinden. `gpt-4o-transcribe` ve `gpt-4o-mini-transcribe` deprecated.
- TTS: `gpt-4o-mini-tts`, `/v1/audio/speech` üzerinden. Bu model deprecated ve **6 Ocak 2027'de kapanıyor**. OpenAI'nin önerdiği yerine geçecek model `gpt-realtime-2.1-mini`, ama o bir LLM: `/v1/audio/speech`'i desteklemiyor ve metni birebir okuma garantisi yok. Banka senaryosunda tarih ve saatin yanlış okunması riski olduğu için case'de `gpt-4o-mini-tts` kullanılır, kapanış tarihi README'de not edilir.
- Ses `marin` ya da `cedar` (dokümanın kalite önerisi). `instructions` ile ton verilir. Düşük gecikme için `response_format="pcm"` ve chunked streaming kullanılır, çalma ilk parçayla başlar.
- *Kod yazarken doğrulanacak:* dosya API'sinde dil alanının adı (`language="tr"`) ve `prompt` parametresi.

**Tasarım**
- `voice/main.py`: `sounddevice` ile kayıt, Enter'a basınca başlar ve basınca durur. Endpointing'i kullanıcının tuşa basması yapar, VAD gerekmez. Akış: wav → STT → `session` → TTS → çalma. Ajan tarafı Aşama 2'deki kodla aynı.
- STT `prompt`'una bağlam verilir: telefonda kart teslimatı, müşteri adı, "doğum tarihi" ifadesi. Doğum tarihinin kendisi ipucu olarak **verilmez**.
- `requirements.txt` dosyasına `openai` ve `sounddevice` eklenir. `.env.example` dosyasına `OPENAI_API_KEY=` satırı eklenir.

**Dosyalar**
```
voice/
  audio.py     # Recorder (bas-konuş, 24 kHz mono int16 → WAV), Player (pcm parçalarını sırayla çalar)
  speech.py    # transcribe(): gpt-transcribe; speak(): gpt-4o-mini-tts pcm streaming, ilk bayt ölçümü
  main.py      # python -m voice.main --customer N [--reset] [--debug] [--voice] [--input-device]
  selftest.py  # mikrofonsuz test: müşteri sözü başka TTS sesiyle sentezlenir, STT'ye verilir
tests/test_voice.py   # WAV başlığı, tepe seviye, STT bağlamında DOB/ilçe olmaması, gecikme toplamı
```

**Kabul kriterleri**
- [x] `python -m voice.main --customer 1` ile senaryo 1 mikrofonla baştan sona konuşuluyor ve DB'de `booked` yazılıyor. Kullanıcı mikrofonla denedi, çalıştı. Ayrıca mikrofonsuz eşdeğeri de geçti: `python -m voice.selftest call` sentezlenmiş müşteri sesiyle senaryo 1'i STT → ajan → TTS üzerinden konuştu, DB'de `booked`, Perşembe kalan 0, tool_log `confirm_name → verify_dob → list_slots → book_appointment:201 → close_call`. Mikrofon 24 kHz'de açılıyor, hoparlörden çalma çalışıyor (duman testi).
- [x] Türkçe isimler ve tarihler doğru yazıya dökülüyor (`python -m voice.selftest stt`). "On dört Mart bin dokuz yüz seksen sekiz" → `verify_dob("14.03.1988")` → 200. "Otuz Ağustos doksan" ilk denemede "Otuz As" çıktı; ay adları `keywords`'e eklenince düzeldi.
- [x] Her turun gecikmesi basılıyor: `[gecikme] STT · LLM · TTS ilk bayt · söz bitti→ilk ses`, arama sonunda ortalama/medyan/en çok. Senaryo 1 ölçümü (5 müşteri turu): STT ort 0.57 sn, LLM ort 2.47 sn (en çok 3.98, `list_slots` turu), TTS ilk bayt ort 0.63 sn, söz bitti→ilk ses ort 3.67 sn. Darboğaz LLM; Aşama 3b bunu hedefler.
- [x] Commit: `stage 3: voice`

**Uygulamada verilen ek kararlar:**
- **Dil alanı.** `gpt-transcribe` için `language` değil `languages=["tr"]` gönderiliyor (doküman ve openai 3.55.1 imzası). `prompt` ve `keywords` da SDK'de doğrudan parametre.
- **STT bağlamı.** `prompt`: konu (kart teslimatı), müşteri adı, "doğum tarihi gün/ay/yıl söylenebilir". `keywords`: müşteri adı, Perşembe, Cuma, 12 ay adı. Doğum tarihi ve ilçe verilmez; `tests/test_voice.py` bunu kontrol ediyor.
- **Ses.** Asistan `marin`, selftest'teki müşteri `cedar`. `TTS_VOICE`, `STT_MODEL`, `TTS_MODEL` ortam değişkenleriyle değiştirilebilir.
- **Sessiz kayıt.** 0.3 sn'den kısa ya da tepe seviyesi 0.01'in altındaki kayıt STT'ye gönderilmez; boş STT sonucu ajana gönderilmez.
- **Metinle deneme.** İstemde Enter yerine metin yazılırsa STT atlanır, cevap yine seslendirilir. `/fill` ve `/kapat` CLI'daki gibi.
- **Kapanan hat.** `/kapat` sonrası asistanın ürettiği metin seslendirilmez, yalnız "(hat kapalı, okunmadı)" diye basılır. İlk denemede bu metin hoparlörden okunuyordu.

## Aşama 3b (opsiyonel, süre kalırsa): Streaming STT, semantic endpointing, streaming TTS
Spec'teki bas-konuş tasarımının üstüne eklenir, onun yerine geçmez (`--stream` bayrağı). Yapılırsa spec.md'deki `voice` satırına eklenir.

**Dokümandan doğrulananlar (2026-11-18):**
- Streaming STT: `gpt-live-transcribe`, `wss://api.openai.com/v1/realtime?intent=transcription` üzerinden. `session.update` ile `type: "transcription"`, `audio.input.format` pcm 24 kHz, `transcription: {model, languages: ["tr"], prompt, keywords, delay}` verilir. Kısmi metin `conversation.item.input_audio_transcription.delta` ile, son metin `...completed` ile gelir. Olaylar `item_id` ile eşlenir.
- `gpt-live-transcribe` sunucu VAD'ını desteklemiyor (`turn_detection: null`). Turu istemci kendisi `input_audio_buffer.commit` ile bitirir. `semantic_vad` speech-to-speech modellerinde var, ama bu modeller Claude'un yerine geçeceği için kullanılmaz.

**Tasarım**
- Endpointing istemcide yapılır: Silero VAD (`onnxruntime` ile, torch'suz) sessizliği yakalar (~400 ms). Ardından kısmi metne bakılıp cümlenin bitip bitmediğine karar verilir (soru eki, yarım kalan tarih ya da sayı, "şey…" gibi dolgu sözcükleri için kural tabanlı kontrol). Bitmişse `commit` gönderilir, bitmemişse daha uzun bir sessizlik eşiği beklenir.
- Streaming TTS: Claude'un çıktısı cümle sınırlarından bölünür ve her cümle ayrı bir `gpt-4o-mini-tts` pcm isteğine gider. Çalma sırası korunur.
- `CallSession`'a cümle cümle yield eden bir `send_stream(text)` eklenir. *Agent SDK'nin kısmi mesaj desteği (`include_partial_messages`) uygularken doğrulanacak.* `send()` aynı kalır, böylece eval etkilenmez.
- `requirements.txt` dosyasına `websockets` ve `silero-vad` eklenir.

**Kabul kriterleri**
- [ ] `python -m voice.main --customer 1 --stream` ile senaryo 1 tuşa basmadan konuşuluyor ve DB'de `booked` yazılıyor.
- [ ] "14 Mart… 1988" gibi araya duraklama giren bir tarih ortadan bölünmüyor.
- [ ] Gecikme basılıyor: konuşma bitişinden `commit`'e, LLM'in ilk cümlesine ve TTS'in ilk ses baytına kadar. Bas-konuş moduyla karşılaştırma `eval/findings.md` dosyasına not ediliyor.
- [ ] Commit: `stage 3b: streaming voice`

## Aşama 4: Eval (simüle müşteriler + DB skoru) ve persona deneyleri — ✅ BİTTİ (kısaltılmış koşu)

**Amaç:** Asistanı yazılı modda (`CallSession`, ses yok) farklı personalarla konuşturmak, çıkan hataları toplamak ve **sıklık × zarar** puanına göre sıralamak. Düzeltmeler bu sıraya göre yapılır. Süre kısıtlı olduğu için yeni senaryo eklenmez: spec'teki 12 senaryo × 3 tekrar korunur, persona ekseni tekrarların içine yerleştirilir.

**Senaryo ve persona ayrımı**
- **Senaryo** (`scenarios.py`): *ne olacağını* belirler. customer_id, ön doldurma, müşterinin hedefi (ör. "Perşembe'yi seç", "kartı istemiyorsun"), tetikleyici ve beklenen DB durumu. Senaryo 6'nın tetikleyicisi: `list_slots` sonrası `/admin/fill`.
- **Persona** (`personas.py`): *nasıl konuşulacağını* belirler. Hedefi değiştirmez, yalnız üslubu değiştirir. 6 persona:
  1. `isbirlikci`: net ve kısa cevaplar (temel çizgi)
  2. `tek_kelime`: "evet", "hı hı", "olur"
  3. `konuskan`: konudan sapar, soruya soruyla cevap verir
  4. `supheci`: dolandırıcılıktan korkar, "neden doğum tarihimi soruyorsunuz?" der
  5. `kararsiz`: seçimini değiştirir, onaydan sonra başka yer ister
  6. `daginik_girdi`: tarihi farklı biçimlerde söyler ("14/3/88", "on dört mart seksen sekiz"), yazım hatası yapar
- Tekrarlarda persona döner: tekrar *k*, `(senaryo_no + k) mod 6` personasını alır. 36 aramanın her personası 6 kez görünür ve ek arama maliyeti olmaz.

**Dosyalar**
- `simulator.py`: müşteriyi oynayan Claude, tool'u yok. Prompt'a senaryo hedefi, persona ve müşterinin kendi bilgileri (ad, doğum tarihi) eklenir. Doğum tarihi yalnız müşteri rolüne verilir, asistana verilmez. Müşteri `[KAPAT]` yazarsa `hangup()` çağrılır. Tur sınırı 20. *API ve model adı uygularken dokümandan doğrulanacak.*
- `checks.py`: her kontrolün sabit bir **zarar** puanı vardır.
  - 3 (iş ya da güvenlik): yanlış outcome; onaysız ya da fazla randevu; kapasite < 0; doğrulamadan önce kart veya teslimat sözü (R1); başkasına neden söylemek (R2); uydurulan yer veya saat; 201 gelmeden "ayarlandı" demek; aramanın `close_call` olmadan bitmesi ya da hata vermesi.
  - 2 (kural): eksik R8 hatırlatması; R5 tekrar okumanın eksik olması; callback beklentisine uyulmaması; `tool_log` sırasında sapma.
  - 1 (üslup): aynı turda birden fazla soru, markdown ya da madde işareti, uzun cevap.
  - Deterministik kontroller DB'den okunur. R1, R2, R5 ve R8 Claude hakemle transkriptten evet/hayır olarak kontrol edilir. Hakem ayrıca serbest metin olarak "diğer sorunlar" listesi döner (en fazla 3 madde, her birine 1–3 zarar). Beklenmedik hatalar bu listeden çıkar.
- `run.py`: her arama için sırasıyla reset, arama ve kontroller çalışır. Senaryo 12'de LLM çağrılmaz, dialer `no-answer` gönderir. Aramalar sıralı çalışır, çünkü reset globaldir ve yerler senaryolar arasında paylaşılır. Bayraklar: `--only 1,6`, `--reps N`, `--personas a,b`, `--tag ad`, `--variant broken_r5`.

**Sonuç klasörü:** `eval/runs/<YYYYMMDD-HHMM>[-tag]/`
- `config.json`: model, effort, prompt'un sha1'i, variant, senaryo ve persona listesi.
- `results.jsonl`: arama başına bir satır (senaryo, persona, tekrar, outcome, her kontrolün geç/kal sonucu, hakem notları, süre, maliyet).
- `transcripts/<senaryo>-<persona>-<tekrar>.md`: transkript ve `tool_log`. DB her reset'te silindiği için tek kalıcı kayıt budur.
- `summary.md`:
  - senaryo × persona geçme tablosu ve toplam skor;
  - **hata öncelik tablosu**: hata, sıklık (kaç aramada görüldü / toplam), zarar, öncelik = sıklık × zarar. Tablo büyükten küçüğe sıralanır ve her satır örnek bir transkripte bağlanır.

**Düzeltme döngüsü:** temel çalıştırma → `summary.md`'deki ilk 2–3 hata düzeltilir → aynı ayarla `--tag fix1` ile yeniden çalıştırılır → iki `summary.md` dosyasındaki öncelik tabloları `eval/findings.md` dosyasında karşılaştırılır.

**Süre (yaklaşık 60 dk + koşum):** personalar ve senaryolar (10 dk), simülatör (10 dk), kontroller ve hakem (15 dk), run ve klasör çıktısı (15 dk), küçük deneme `--only 1,2,6 --reps 1` (5 dk), tam koşum (36 arama, tahminen 30–40 dk; arka planda çalışırken düzeltmeler incelenir).

**Kabul kriterleri**
- [x] `python -m eval.run` tek komutla çalışıyor, skor tablosunu basıyor ve sonuç klasörünü oluşturuyor. Tam koşu (36 arama) süre nedeniyle **yarıda kesildi**: taban 19 arama (senaryo 1–3 için 3'er, senaryo 4 için 2, geri kalan senaryolar için 1 tekrar). Senaryo 12 LLM'siz.
- [x] Her aramanın transkripti `transcripts/` altında. `summary.md` içinde `Öncelik | Sıklık | Açıklama` sütunlu, sıklık × zarar ile sıralı hata tablosu var.
- [x] `--variant broken_r5`: skor %98,9'dan %94,6'ya düştü, R5 hataları tablonun ilk iki satırı oldu (3/6 ve 2/6). Tabanda 0/19.
- [x] Düzeltme turu yapıldı (fix1, fix2). Önce/sonra tabloları `eval/findings.md` içinde. **R7 düzeltmesi örneklem küçük olduğu için kanıtlanamadı** (taban 0/2, fix1 1/2, fix2 1/6); bulgular ve açık kalanlar orada.
- [x] Commit: `stage 4: eval`

**Uygulamada verilen ek kararlar:**
- **Eklenenler:** `GET /admin/slots` (doluluk okuma, kapasite kontrolü için). `run.py --merge a,b,c` paralel koşuların klasörlerini tek `summary.md`'de birleştirir. `CallSession(prompt_transform=...)` yalnız eval varyantları içindir.
- **Paralel koşu:** Reset global olduğu için her paralel parça kendi servis örneğini (`BANK_DB`, farklı port) ve `BANK_URL`'i kullanır.
- **R7 kontrolü sonradan eklendi** (hakemin "diğer sorunlar" listesinden çıktı): `close_call`'dan önce söylenmeyen "Sizi gelecek hafta arayacağız".
- **`close_call` `next` talimatı:** `no_slot` ve `declined` sonucunda tool son sözü modele yazdırır. R7'yi tam kapatmadı.
- **Hakem** aynı model; zaman zaman kendi notuyla çelişiyor (R6 yanlış alarmı). Önemli bulgular transkriptten elle doğrulandı.
- **Kapsam:** Yalnız metin; Aşama 3b yapılmadı.
