# LLM improvement

Amaç: asistanın çıktısını daha deterministik ve kontrollü yapmak. İki iş paketi var:

1. LLM'e hiç sormadan, kodun kendi söylediği ya da yaptığı adımlar.
2. Tool katmanında tur sırası korumaları.

Durum: plan, henüz uygulanmadı. [spec.md](spec.md), [plan.md](plan.md) ve `eval/` koduyla karşılaştırıldı; sonuç aşağıdaki "Spec ve plan uyumu" bölümünde.

Kapsam dışı: çıktı filtresi (doğrulama öncesi sızıntı, TTS temizliği), tool sonuçlarına `next` ve `spoken` alanları, kodda tam durum makinesi.

## Spec ve plan uyumu

**Kurallarla çelişki yok.** R1–R12'nin hiçbiri değişmiyor, yalnız bazılarını zorlayan yer prompt'tan koda taşınıyor.

**Spec'i değiştiren tek madde: 2.1 (`propose_slot`).** Tool sayısı 5'ten 6'ya çıkar; spec.md'nin "Tools" satırı ve "Kapsam"daki "5 tool" ifadesi güncellenir. Kullanıcı bu eklemeyi onayladı (2026-11-18). Yeni tool servise istek atmaz, bu yüzden spec'teki "her tool çağrısını servis `tool_log`'a yazar" cümlesi onun için geçerli olmaz; spec'e bu istisna da yazılır.

| Konu | Spec / plan ne diyor | Bu plan |
|---|---|---|
| Açılış (R1, R2) | Dijital asistan olduğunu söyler, "Ad Soyad ile mi görüşüyorum?" diye sorar | Şablon ikisini de içerir |
| Başkası açtı (R2) | Nedenini söylemeden kapatır. plan.md kararı: gerekçe yalnız "Bu konuyu yalnız <müşteri> ile görüşebiliyorum" | Sabit veda aynı cümle |
| R8 | plan.md kararı: teyit + sabit cümle + "Başka bir sorunuz var mı?", kapatma sonraki turda | Aynı akış; cümleyi kod ekler, sırayı tool zorlar |
| R11 | Her arama `close_call` ile biter; servis her tool isteğini `tool_log`'a yazar | Kodla kapatma aynı `/close` endpoint'ini çağırır, `tool_log`'da `close_call` satırı yine oluşur |
| Sonuç kısıtları | Doğrulanmamış çağrı yalnız `not_verified`, randevulu çağrı yalnız `booked` ile kapanır (servis zorlar) | Kod yalnız bu iki tek seçenekli durumda LLM'siz kapatır |

**plan.md'deki bir kararı değiştiren tek madde: 1.2.** Aşama 2 kararı şöyle: müşteri kapatınca LLM'e bir kez sorulur, yine kapanmazsa oturum `outcome=None` ile biter ve "servise uydurma sonuç yazılmaz". 1.2 bunun son kısmını değiştiriyor (LLM kapatmazsa kod `no_slot` yazar). Kullanıcı bu değişikliği onayladı; ayrıntı 1.2'de.

**Eval ile ilişki (Aşama 4 sürüyor):**
- Bu plan Aşama 4'teki düzeltme döngüsünün adayıdır: önce temel koşum alınır, `summary.md`'deki öncelik tablosu bu maddelerden hangilerinin gerçekten gerekli olduğunu gösterir, seçilenler uygulanıp `--tag fix1` ile yeniden koşulur. Temel koşumdan önce uygulanırsa önce/sonra karşılaştırması kaybolur.
- **`--variant broken_r5` kabul kriteri 2.1'den etkilenir.** Varyant prompt'tan onay adımını siler ve skorun düşmesini bekler. 2.1 uygulanınca model onaysız `book_appointment` çağırsa da tool reddeder ve önce öneri ister; skor büyük olasılıkla düşmez. Bu yüzden `broken_r5` kanıtı 2.1'den **önce**, temel koşumla birlikte alınmalı. 2.1'den sonra aynı varyantın skoru düşürmemesi ise korumanın çalıştığının kanıtıdır ve `findings.md`'ye öyle yazılır.
- `_broken_r5`, prompt'ta `"5. Onay (R5)"` ve `"6. Randevu (R6)"` başlıklarını arar. Bu plan madde 1, 2, 3, 8 ve R11'i değiştirir; 5 ve 6'nın başlıklarına dokunulmaz.
- `eval/run.py` akışı aynı kalır: `start()` yine açılış metnini döner, `hangup()` boş metin dönebilir (döngü bunu zaten atlıyor).
- "Arama `close_call` olmadan bitti" kontrolü artık LLM'i değil sistemi ölçer. `findings.md`'de bu fark not edilmeli.
- Yerel retler servisin `tool_log` tablosunda görünmez, yalnız `on_tool` üzerinden transkript dosyasına düşer. DB'deki `tool_log` sırası kontrolleri etkilenmez.

**Uygulanınca güncellenecek dokümanlar:** plan.md (Aşama 2'nin "ek kararlar" listesi ve 2.3'teki `start()` / `hangup()` tanımı) ve CLAUDE.md'deki kod yapısı satırları ("5 tool" dahil). spec.md'de yalnız tool listesi değişir.

## Ortak altyapı

İki paket de aynı üç küçük parçaya dayanır. Önce bunlar yazılır.

**`CallState` alanları** (`assistant/tools.py`):

| Alan | Tip | Kim yazar |
|---|---|---|
| `turn` | `int` | `CallSession._turn`, her çağrının başında bir artırır |
| `offered_slots` | `dict[int, dict]` | `list_slots` başarılı dönünce; `slot_id` → servisten gelen gün ve saat aralığı |
| `address_type` | `str \| None` | `list_slots` başarılı dönünce |
| `proposed_slot_id` | `int \| None` | `propose_slot` yazar; `list_slots` ve `slot_full` siler |
| `proposed_turn` | `int \| None` | `propose_slot` yazar |
| `booked_turn` | `int \| None` | `book_appointment` 201 dönünce |
| `forced_close` | `str \| None` | `confirm_identity_name(false)` ve `verify_dob` kilitlenince; değer sabit veda cümlesinin anahtarı |

**Sistem notu kuyruğu** (`assistant/session.py`): `self._pending_notes: list[str]`. Kodun LLM yerine söylediği her cümle buraya eklenir ve bir sonraki `query`'nin başına şu biçimde konur:

```
[SİSTEM] Şunu söyledin: "<cümle>"
<müşterinin sözü>
```

Böylece model kendi söylemediği cümleyi geçmişinde görür ve tekrarlamaz.

**Kodla kapatma** (`assistant/session.py`): `_close_by_code(outcome, note)`. `/close`'u doğrudan çağırır, başarılıysa `state.closed` ve `state.outcome` yazar, `on_tool` varsa onu da tetikler (debug çıktısı ve eval aynı olayı görsün). Servis reddederse `gave_up = True` ve uyarı.

## 1. LLM'siz adımlar

### 1.1 Açılış cümlesi

- Bugün: `start()`, `OPENING_NOTE` ile LLM'e sorar.
- Hedef: `start()` sabit şablonu döner, LLM çağrılmaz.
  - `prompt.py`: `OPENING_TEMPLATE = "Merhaba, ben bankanın dijital asistanıyım. {customer_name} ile mi görüşüyorum?"`
  - `start()`: `connect()` yine burada yapılır, cümle transkripte yazılır ve `_pending_notes`'a eklenir.
  - Prompt madde 1: "Açılış cümlesini sistem söyledi, tanıtımı tekrarlama" olarak kısalır. `OPENING_NOTE` silinir.
- Yan etki: `init` mesajı artık ilk `send()` turunda gelir; `init_tools` kontrolü yerinde kalır, yalnız zamanı kayar.
- Kazanç: R1 ve R2 açılışta garanti, ilk tur gecikmesi yok.

### 1.2 Kapatma sonucunu kod seçer

- Bugün: müşteri kapatınca `HANGUP_NOTE` ile LLM'e sorulur; LLM `close_call` çağırmazsa yalnız uyarı basılır, servise sonuç yazılmaz (plan.md Aşama 2 kararı).
- Hedef: `hangup()` önce `GET /calls/{id}` ile duruma bakar. Servisin tek sonuca izin verdiği iki durumda LLM çağrılmaz:

  | Durum | Geçerli sonuç | Kim kapatır |
  |---|---|---|
  | `verified` false | yalnız `not_verified` | kod |
  | randevu var | yalnız `booked` | kod |
  | doğrulanmış, randevu yok | `no_slot` ya da `declined` | LLM (bugünkü `HANGUP_NOTE`), kapatmazsa kod `no_slot` yazar |

- Üçüncü satır LLM'de kalır, çünkü `declined` ile `no_slot` arasındaki fark konuşmadan anlaşılır ve callback açılıp açılmayacağını belirler (R12).
- Süre dolunca: `TIMEOUT_NOTE` kalır (veda cümlesini LLM kursun), tur sonunda arama hâlâ açıksa aynı tablo uygulanır.
- Prompt: R11'deki "Sistem müşterinin kapattığını bildirirse..." satırı kalır, yalnız üçüncü durumu anlatacak biçimde kısalır.
- Kazanç: her arama servise bir sonuçla yazılır; `gave_up` yalnız servis hatasında kalır.
- **Karar (kullanıcı onayladı, 2026-11-18):** üçüncü satırda LLM kapatamazsa kod `no_slot` yazar. Bu, plan.md'deki "servise uydurma sonuç yazılmaz" kararının yerine geçer; uygulanınca plan.md'de güncellenir. Gerekçe: `no_slot` callback açar, yani en kötü durumda müşteri gelecek hafta yeniden aranır; `outcome=None` kalırsa müşteri hiçbir listeye düşmez. Bedeli: kartı istemediğini söyleyip kapatan müşteri, LLM de kapatamazsa, yanlışlıkla yeniden aranır.

### 1.3 R8 hatırlatma cümlesi

- Bugün: prompt "aynen söyle" diyor, cümleyi LLM üretiyor.
- Hedef: LLM yalnız randevuyu teyit eder; hatırlatmayı ve soruyu kod ekler.
  - `prompt.py`: `REMINDER = "Hatırlatmak isterim, kartınız yalnız size, kimliğinizi göstermeniz şartıyla teslim edilecek; başka biri teslim alamaz."` ve `ANY_QUESTION = "Başka bir sorunuz var mı?"`
  - `_turn`: tur sonunda `state.booked_turn == state.turn` ise cevabın sonuna `REMINDER + " " + ANY_QUESTION` eklenir ve `_pending_notes`'a konur. Ekleme transkript yazılmadan önce yapılır; eval hakemi R8'i DB'deki transkriptten okuyor.
  - Prompt madde 8 ve `book_appointment` sonucundaki `next` metni: "Yalnız randevuyu gün, saat aralığı ve adres tipiyle teyit et. Hatırlatmayı ve soruyu sistem ekler, sen ekleme."
- Risk: model yine de soruyu sorarsa cümle iki kez geçer. Eklemeden önce cevapta `ANY_QUESTION` ya da `REMINDER` varsa o parça atlanır.

### 1.4 Yanlış kişi ve kilitlenme vedası

- Bugün: iki yolda da veda cümlesini ve `close_call`'u LLM üretiyor. Arama nedeninin sızma riski en yüksek yer burası.
- Hedef:
  - `confirm_identity_name` `name_confirmed=false` dönünce tool `state.forced_close = "wrong_person"` yazar.
  - `verify_dob` `locked` dönünce (200 + `locked: true` ya da 403 `locked`) `state.forced_close = "locked"` yazar.
  - İki durumda da tool sonucu: "Arama sistem tarafından kapatılıyor. Hiçbir şey yazma."
  - `_turn`: tur sonunda `forced_close` doluysa o turun LLM metni atılır, sabit cümle döner, `_close_by_code("not_verified", ...)` çağrılır.
- Sabit cümleler (`prompt.py`):
  - `wrong_person`: "Bu konuyu yalnız {customer_name} ile görüşebiliyorum. İyi günler dilerim."
  - `locked`: "Güvenlik nedeniyle doğrulama yapamadım. İyi günler dilerim."
- Prompt: madde 2'nin yanlış kişi alt maddesi ve madde 3'ün kilitlenme alt maddesi tek cümleye iner ("bu durumda aramayı sistem kapatır").
- Risk: model belirsiz bir cevapta ("kim arıyor?") `is_customer=false` gönderirse arama geri dönüşsüz kapanır. Bugün de model aynı turda kapatıyor, ama `supheci` personasıyla eval'de izlenmeli. Prompt'a "emin değilsen tool çağırmadan tekrar sor" cümlesi eklenir.

## 2. Tool katmanında tur korumaları

Hepsi `assistant/tools.py` içinde, servise gitmeden önce kontrol edilir. Ret, mevcut biçimle döner: `is_error` + `"HATA <kod>: <ne yapmalı>"`. `on_tool` da çağrılır (durum kodu 409, gövde `{"error": <kod>, "local": true}`), böylece debug ve eval reddi görür. Servisin `tool_log` tablosuna yazılmaz, çünkü istek servise ulaşmaz.

Bunlar iş kuralı değil konuşma sırası kuralı; servis tur kavramını bilmediği için asistan katmanında durur. Yetki, kapasite ve tek randevu kontrolleri serviste kalır.

### 2.1 `propose_slot`: duyulan yer ile yazılan yer aynı olsun

- Sorun: bugün model yeri kendi cümlesiyle okuyor, sonra `slot_id`'yi kendisi seçiyor. "Perşembe" deyip Cuma'nın id'sini gönderirse servis kabul eder (ikisi de müşterinin ilçesinde ve boş). Randevu iptali kapsam dışı ve müşteri başına tek randevu olduğu için bu hata arama içinde düzeltilemez; LLM'in verdiği kararlar arasında geri alınamayan tek yer burası.
- Hedef: okunan cümleyi ve yazılan `slot_id`'yi aynı kaynağa bağlamak.
  - Yeni tool `propose_slot(slot_id: int)`. Açıklaması: "Müşteri bir yer seçince çağır. Seçilen yeri müşteriye sistem okur ve onay ister."
  - Servise istek atmaz. Cümleyi `offered_slots[slot_id]` ve `address_type` ile, yani son `list_slots` cevabındaki servis verisiyle kurar.
  - Şablon (`prompt.py`): `"{gün} günü, {başlangıç} ile {bitiş} arası, {adres} adresinize teslimat. Onaylıyor musunuz?"`. `time_range` `"09:00-13:00"` biçiminde gelir, tireden bölünür. `adres`: "Ev" → "ev", "İş yeri" → "iş yeri".
  - Tool `proposed_slot_id` ve `proposed_turn` yazar, sonuç olarak cümleyi ve "Bu cümleyi sistem söyledi, sen bir şey yazma. Müşterinin cevabını bekle." notunu döner.
  - `_turn`: tur sonunda `proposed_turn == turn` ise o turun LLM metni atılır, cevap sabit cümle olur ve transkripte o yazılır (eval hakemi R5'i transkriptten okuyor).
- LLM'de kalan: müşterinin hangi yeri kastettiği (`slot_id` seçimi) ve "evet" deyip demediği. Yanlış `slot_id` seçerse müşteri yanlış yeri duyar ve itiraz edebilir; bugün duymadan yazılıyor.
- Prompt madde 5: "Müşteri bir yer seçince propose_slot çağır. Onay gelince aynı slot_id ile book_appointment çağır. Müşteri fikir değiştirirse yeni yer için tekrar propose_slot çağır."
- Etkilenen yerler: `TOOL_NAMES` ve `ALLOWED_TOOLS` (6 ad), `session.py`'deki init tool listesi kontrolü, `tests/test_assistant.py`'deki tool sayısı testi, spec.md ve CLAUDE.md'deki "5 tool". Servisin `tool_log` sırası değişmez; `eval/checks.py`'deki `tool_order` kontrolü etkilenmez.

### 2.2 Koruma tablosu

| Koruma | Koşul | Hata kodu | Kural |
|---|---|---|---|
| Bilinmeyen yer | `propose_slot`, `slot_id` `offered_slots` içinde değilken | `unknown_slot` | R10 |
| Erken öneri | `propose_slot`, `listed_turn == turn` iken (müşteri henüz yerleri duymadı) | `not_offered_yet` | R4, R5 |
| Önerilmemiş randevu | `book_appointment`, `slot_id != proposed_slot_id` iken | `not_proposed` | R5 |
| Onaysız randevu | `book_appointment`, `proposed_turn == turn` iken | `confirmation_required` | R5 |
| Aynı turda kapatma | `close_call`, `booked_turn == turn` iken | `reminder_pending` | R8 |

`listed_turn` (`int | None`, `list_slots` yazar) `CallState`'e eklenir.

Hata metinleri:
- `unknown_slot`: "Bu slot_id son list_slots sonucunda yok. list_slots çağır ve yalnız dönen yerleri öner."
- `not_offered_yet`: "Önce yerleri müşteriye söyle ve seçmesini bekle."
- `not_proposed`: "Bu yer müşteriye okunmadı. Önce propose_slot çağır ve onayı bekle."
- `confirmation_required`: "Öneri bu turda okundu. Müşterinin onayını bekle, onay gelince tekrar çağır."
- `reminder_pending`: "Randevu bu turda yazıldı. Önce randevuyu teyit et, müşterinin cevabını bekle."

Bilinen sınırlar:
- Korumalar müşterinin önerilen yeri duyduğunu ve araya bir müşteri turu girdiğini garanti eder, müşterinin gerçekten "evet" dediğini değil. Bu yargı LLM'de kalır.
- Aynı turda kapatma koruması plan.md'de kayıtlı gerçek bir hatayı kapatır (model `book_appointment` ile `close_call`'u art arda çağırıp teyidi ve R8'i atlamıştı).
- Tek yer kaldığında da öneri adımı atlanamaz; arama bir tur uzar.
- `slot_full` sonrası: öneri silinir, model `list_slots` çağırır, müşteri seçer, yeni `propose_slot` ve `book_appointment` ayrı turlarda olur. Senaryo 6 iki tur uzar.
- Ek tool çağrısı onay turuna bir ajan adımı ekler; ses modunda o turun gecikmesi artar (ölçülmeli).
- 1.2 ve 1.4'teki kodla kapatma tool'dan geçmediği için `reminder_pending`'e takılmaz.

## Uygulama sırası

0. Aşama 4 temel koşumu ve `--variant broken_r5` koşumu alınır (`python -m eval.run`). Aşağıdaki adımlardan öncelik tablosunda karşılığı olanlar seçilir.
1. Ortak altyapı: `CallState` alanları, `turn` sayacı, `_pending_notes`, `_close_by_code`.
2. Paket 2: önce `reminder_pending` (tek başına, prompt değişmez), sonra `propose_slot` ve ona bağlı dört koruma (prompt madde 5, tool listesi ve testler birlikte değişir).
3. 1.2 (kodla kapatma).
4. 1.4 (zorunlu kapatma).
5. 1.3 (hatırlatma).
6. 1.1 (açılış). En çok testi etkileyen adım olduğu için sona kalır.

## Testler

`tests/test_assistant.py` içinde, LLM'siz, servis ASGI üzerinden:
- Sunucuda tam 6 tool var; `propose_slot` servise istek atmaz ve `tool_log`'a satır düşmez.
- `propose_slot`: listede olmayan `slot_id` ve `list_slots` ile aynı tur reddedilir; geçerli çağrı servis verisinden beklenen cümleyi üretir ("Perşembe günü, 09:00 ile 13:00 arası, ev adresinize teslimat. Onaylıyor musunuz?").
- `book_appointment`: önerilmemiş `slot_id` ve öneriyle aynı tur reddedilir, servise istek gitmez; sonraki turda önerilen `slot_id` ile geçer.
- `slot_full` ve yeni `list_slots` öneriyi siler.
- `book_appointment` ile aynı turda `close_call(booked)` reddedilir; sonraki turda geçer.
- `hangup()`: doğrulanmamış çağrıda ve randevulu çağrıda LLM çağırmadan servise sonuç yazar; doğrulanmış randevusuz çağrıda LLM'e sorar.
- `confirm_identity_name(false)` ve kilitlenme `forced_close` yazar.
- `start()` şablonu döner, `query` çağrılmaz, transkriptte açılış vardır.
- Prompt testleri: silinen satırlar yok, `REMINDER` metni prompt'ta değil sabitte.

Ses tarafı (`voice/main.py`) `CallSession`'ı kullandığı için değişmez; `tests/test_voice.py` yalnız açılışın LLM'siz geldiğini varsayan yerler varsa güncellenir.

## Kabul kriterleri

- `pytest -q` geçer.
- Yazılı modda 4 sonuç (`booked`, `no_slot`, `declined`, `not_verified`) birer kez elle denenir; her aramada serviste sonuç yazılıdır.
- `/kapat` açılışta ve randevu sonrasında LLM çağrısı olmadan, doğrulama sonrasında LLM'e bir kez sorarak doğru sonuçla kapatır.
- Randevu turunda hatırlatma cümlesi harfi harfine ve bir kez geçer.
- Spec'teki "Bitti tanımı" aynen geçer: metin modunda senaryo 1, 2 ve 6 elle oynanınca DB'deki sonuç doğru.
- Onay turunda müşteriye okunan cümle ile DB'ye yazılan randevunun günü ve saat aralığı her aramada aynıdır (transkript ve `appointment` karşılaştırılır).
- Eval: temel koşum ile `--tag fix1` koşumunun öncelik tabloları `eval/findings.md`'de karşılaştırılır. `--variant broken_r5` 2.1'den önce skoru düşürür, 2.1'den sonra düşürmez; ikisi de not edilir.
