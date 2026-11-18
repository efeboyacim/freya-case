# Kart teslimatı yeniden planlama asistanı

Kuryenin Salı günü ulaşamadığı müşterileri arayan, kimliğini doğrulayan ve kendi ilçesindeki bu haftaki bir yere teslimat randevusu veren sesli asistan (Freya FDE case). Ayrıntılı kapsam: [docs/spec.md](docs/spec.md), plan ve kararlar: [docs/plan.md](docs/plan.md).

**Mimari:** `bank_service` (FastAPI + SQLite, iş kuralları burada zorlanır) ← `assistant` (Claude Agent SDK, 5 tool) ← `voice` (OpenAI STT/TTS, bas-konuş) · `eval` (simüle müşteriler, skor DB'den). Asistan müşteri, yer ve randevu bilgisini yalnız tool çağrısıyla servisten alır. Doğum tarihi modele verilmez, kontrolü servis yapar.

## Çalıştırma (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env   # ANTHROPIC_API_KEY (ses için ayrıca OPENAI_API_KEY) yaz
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m uvicorn bank_service.app:app --port 8000
```

Servis açıkken, ayrı terminalde:

| Ne | Komut |
|---|---|
| Yazılı arama | `.\.venv\Scripts\python -m assistant.cli --customer 1 --reset --debug` (`/fill <slot_id>` yeri doldurur, `/kapat` hattı kapatır) |
| Sesli arama | `.\.venv\Scripts\python -m voice.main --customer 1 --reset --debug` (Enter kaydı başlatır ve bitirir) |
| Mikrofonsuz ses testi | `.\.venv\Scripts\python -m voice.selftest call` |
| Eval | `.\.venv\Scripts\python -m eval.run [--only 1,6] [--reps 3] [--variant broken_r5] [--tag ad]` |

Eval sonuçları `eval/runs/<tarih>[-tag]/` altına yazılır (`summary.md`, `results.jsonl`, `transcripts/`). Paralel koşuları `--merge klasör1,klasör2 --tag ad` birleştirir.

## Kurallar (özet)

- **R1–R2:** Açılışta bankanın dijital asistanı olduğunu söyler, "Ad Soyad ile mi görüşüyorum?" diye sorar. Kimlik doğrulanmadan kart ya da teslimattan söz etmez. Telefonu başkası açtıysa nedenini söylemeden kapatır (`not_verified`).
- **R3:** Doğum tarihini sorar, kontrolü servis yapar, 3 yanlışta kilitlenir (`not_verified`).
- **R4–R5:** Yalnız müşterinin ilçesindeki boş yerleri sunar. Seçilen yeri (gün, saat aralığı, Ev/İş yeri) tekrar okur, onay alır, sonra randevu yazar.
- **R6–R7:** 201 dönmeden "ayarlandı" demez. `slot_full` dönerse kalan yerleri önerir. Yer yoksa ya da seçilmezse "Sizi gelecek hafta arayacağız" (`no_slot`). Bu cümle `session.ensure_r7` ile kodda garanti edilir.
- **R8–R10:** Randevuda kartın yalnız sahibine, kimlikle teslim edileceğini hatırlatır. Adres/ilçe değişikliği telefonda yapılmaz, uygulamadan yapılır. Müşteri başına tek randevu, yer ya da saat uydurulmaz.
- **R11–R12:** Her arama `close_call` ile biter (`booked`, `no_slot`, `declined`, `not_verified`; `not_reached`'i dialer yazar). `booked` ve `declined` dışındaki sonuçlarda servis gelecek hafta için callback açar.

Sunucu tarafı korumalar: doğrulanmamış çağrıda yerler ve randevu 403, kapasite tek SQL ile atomik düşer (eşzamanlı isteklerde aşılmaz), müşteri başına tek randevu, kapalı çağrıya yazılamaz.

## Ölçüm sonuçları

Metin modunda, Claude'un müşteriyi oynadığı 12 senaryo × 6 persona (ayrıntı: [eval/findings.md](eval/findings.md)). Skor = geçen kontrol / uygulanabilir kontrol.

| Koşu | Arama | Skor |
|---|---|---|
| Taban | 19 | 244/245 (%99,6) |
| `broken_r5` (R5 onay adımı silinmiş prompt), aynı senaryolarda | 6 | 87/92 (%94,6), taban %98,9 |
| R7 düzeltmesi (kodda) | 2 | 24/25 |

- **Kontroller bir şey ölçüyor:** R5 onay adımı silinince "onaysız randevu" (3/6) ve "tekrar okuma yok" (2/6) hataları öncelik tablosunun başına çıktı. Tabanda 0/19.
- **Bulunan gerçek hata:** Yer yokken asistan metinsiz `close_call` çağırıp R7 cümlesini söylemiyordu. Prompt düzeltmesi yetmedi, kodla zorlandı.
- **Ses (bas-konuş), senaryo 1:** STT ort. 0,57 sn, LLM ort. 2,47 sn, TTS ilk bayt ort. 0,63 sn, söz bitti → ilk ses ort. 3,67 sn. Darboğaz LLM.
- **Güvenilirlik sınırı:** Örneklem küçük (persona başına 1–3 arama), hakem aynı model ve bazen kendi notuyla çelişiyor. Rakamlar yön gösterir, kesin oran değildir.

## Dışarıda bırakılanlar

- **Tam eval koşusu:** 12 senaryo × 3 tekrar (36 arama) süre nedeniyle koşulmadı; taban 19 arama, düzeltme turları 2–8 arama.
- **Aşama 3b:** streaming STT, semantic endpointing ve streaming TTS yapılmadı. Ses yalnız bas-konuş.
- **Spec kapsamı dışı:** gerçek telefon hattı, arayüz, adres değişikliği, randevu iptali/değiştirme, gelecek haftanın yerleri, callback'lerin gerçekten aranması, KYC ve auth.
- **TTS modeli:** `gpt-4o-mini-tts` 6 Ocak 2027'de kapanacak. Yerine önerilen model `/v1/audio/speech`'i desteklemiyor ve metni birebir okuma garantisi vermiyor; tarih ve saat okumada risk olduğu için bu model kullanıldı.
- **Modelin çıktısını kodla kontrol (planlandı, uygulanmadı):** [docs/llm-improvement.md](docs/llm-improvement.md). Bugün yalnız R7 cümlesi kodla garanti. Plan, geri alınamayan veya riskli adımları prompt'tan koda taşıyor:
  - **LLM'siz sabit cümleler:** açılış, R8 hatırlatması, yanlış kişi ve kilitlenme vedası şablondan gelir, modelin üretmesi gerekmez (arama nedeninin sızma riski kapanır).
  - **Kodla kapatma:** müşteri hattı kapatınca doğrulanmamış çağrı `not_verified`, randevulu çağrı `booked` ile LLM'siz kapanır; LLM kapatamazsa kod `no_slot` yazar.
  - **Tur sırası korumaları (tool katmanında):** yeni `propose_slot` tool'u müşteriye okunan yer ile yazılan `slot_id`'yi aynı kaynağa bağlar. Önerilmemiş ya da onaysız `book_appointment` ile randevu turunda `close_call` reddedilir.
  - **Neden yapılmadı:** süre yetmedi ve temel eval koşumu önce alınmalıydı; `--variant broken_r5` kanıtı `propose_slot` eklenince geçersizleşir. Plan, eval öncelik tablosuna göre seçilerek uygulanacak şekilde yazıldı.
- **R7 nedeni:** Yer yokken eklenen sabit cümle "neden" açıklamasının yerini tutmaz; model nedeni söylemeyebilir.
