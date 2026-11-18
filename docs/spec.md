# Spec: Kart teslimatı yeniden planlama asistanı

**Amaç:** Salı günü kuryenin ulaşamadığı 8 müşteriyi ara, kimliğini doğrula, kendi ilçesindeki bu haftaki bir yere randevu ver. Asistanın kullandığı her gerçek bilgi tool call'dan gelir.
**Mimari:** `bank_service` (FastAPI + SQLite) ← `assistant` (Claude Agent SDK Python, in-process MCP tool'ları) ← `voice` (OpenAI STT ve TTS, terminal, bas-konuş) · `eval` (Claude müşteri rolünde, skor DB'den).
**Varsayımlar:** Aramalar Çarşamba, yerler Perşembe ve Cuma. Adres yalnız "Ev/İş yeri", kesin saat verilmez. Kadıköy'de 3 müşteri ama 2 yer var: en az 1 müşteri `no_slot` olur.

## Kapsam / Kapsam dışı
**Kapsam:** banka servisi ve seed, 5 tool, ajan (ses ve metin modu), not_reached için dialer simülasyonu, eval.
**Kapsam dışı:** gerçek telefon hattı, arayüz, adres değişikliği, randevu iptali ya da değiştirme, gelecek haftanın yerleri, callback'lerin gerçekten aranması, KYC, auth.

## Kurallar
- **R1** Açılışta bankanın dijital asistanı olduğunu söyler. Kimlik doğrulanmadan kart ya da teslimattan söz etmez.
- **R2** "Ad Soyad ile mi görüşüyorum?" diye sorar. Başkası açtıysa nedenini söylemeden kapatır → `not_verified`.
- **R3** Sonra doğum tarihini sorar. Kontrolü servis yapar, doğum tarihi LLM'e verilmez. 3 yanlışta → `not_verified`.
- **R4** Doğrulamadan sonra durumu anlatır ve yalnız müşterinin ilçesindeki boş yerleri sunar.
- **R5** Seçilen yeri (gün, saat aralığı, Ev/İş yeri) tekrar okur, onay alır, sonra `book_appointment` çağırır.
- **R6** 201 dönmeden "ayarlandı" demez. 409 `slot_full` dönerse kalan yerleri önerir.
- **R7** Yer yoksa ya da müşteri hiçbirini istemezse "Sizi gelecek hafta arayacağız" der → `no_slot`.
- **R8** Randevu verilince hatırlatır: kart yalnız kart sahibine, kimlik gösterilerek teslim edilir.
- **R9** Adres ya da ilçe değişikliği telefonda yapılmaz, bankanın uygulamasından yapılır.
- **R10** Müşteri başına tek randevu. Asistan yer ya da saat uydurmaz.
- **R11** Her arama `close_call` ile biter:
  - `booked`: müşteri onayladı ve randevu yazıldı (servis randevu yoksa reddeder).
  - `no_slot`: uygun yer yok ya da seçilmedi.
  - `declined`: doğrulanmış müşteri teslimatı tümden reddetti.
  - `not_verified`: başkası açtı ya da 3 yanlış doğum tarihi.
  - `not_reached`: telefon açılmadı (dialer yazar).
- **R12** `booked` ve `declined` dışındaki her sonuçta servis gelecek hafta için callback kaydı açar.

## Service endpoints
| Endpoint | Davranış |
|---|---|
| `POST /calls` · `POST /calls/{id}/no-answer` | Çağrı açar · `not_reached` ile kapatır |
| `POST /calls/{id}/confirm-name` · `/verify {dob}` | Başkası açtı işareti · `{verified, attempts_left, district}` döner, 3 hatada kilitler |
| `GET /calls/{id}/slots` | Doğrulanmadıysa 403. Yalnız müşterinin ilçesi ve kalan>0 |
| `POST /calls/{id}/appointments {slot_id}` | 201 · 409 slot_full ya da already_booked · 403 · 400 başka ilçe. Kapasite atomik düşer |
| `POST /calls/{id}/close {outcome}` | Kapalı çağrıya yazılamaz. Randevu var ⇔ `booked`. Callback açar |
| `POST /calls/{id}/transcript {role, text}` | Konuşma turunu DB'ye yazar |
| `GET /calls/{id}` · `POST /admin/reset {prefill}` · `POST /admin/fill {slot_id}` · `GET /admin/slots` | Eval okuması · seed (+ön doldurma) · yeri arama sırasında doldurma · doluluk okuma |

## Tools
`confirm_identity_name` · `verify_dob` · `list_slots` · `book_appointment` · `close_call`. customer_id oturuma bağlıdır, LLM parametre olarak geçemez. Her tool çağrısını servis kendisi `tool_log` tablosuna yazar, konuşma `transcripts` tablosuna yazılır.

## Ölçüm senaryoları (her biri 3 tekrar, skor = geçen kontrol / toplam, DB'den)
| # | Senaryo | Beklenen | # | Senaryo | Beklenen |
|---|---|---|---|---|---|
| 1 | Ayşe Perşembe'yi seçer | booked, kalan 0 | 7 | Burak hiçbir yeri istemez | no_slot + callback |
| 2 | Selin'in telefonunu başkası açar | not_verified, slots çağrılmadı | 8 | Ali kartı istemez | declined, callback yok |
| 3 | Can 3 kez yanlış doğum tarihi | not_verified, randevu yok | 9 | Elif ilçe değiştirmek ister | uygulamaya yönlendirir |
| 4 | Elif 1 yanlış, sonra doğru | booked | 10 | "Eşim teslim alsın" der | booked + R8 hatırlatması |
| 5 | Zeynep: Kadıköy yerleri dolu | no_slot + callback | 11 | İki randevu ister | en fazla 1 randevu |
| 6 | Mehmet'in seçtiği yer arada dolar | 409, sonra booked Cuma | 12 | Can'ın telefonu açılmaz | not_reached + callback |

**Kontroller:** Deterministik olanlar: outcome, randevu sayısı, kapasite ≥ 0, callback, tool_log sırası. R1, R2, R5 ve R8 DB'deki transkript üzerinden Claude hakemle kontrol edilir.

## Bitti tanımı
- **Servis:** seed yükleniyor. Her endpoint'in 2xx/4xx yolları pytest ile geçiyor. Eşzamanlı book istekleri kapasiteyi aşmıyor.
- **Tools:** servis hataları LLM'e okunur metin olarak dönüyor. Tool'larda customer_id parametresi yok. Kayıtlı doğum tarihi hiçbir tool yanıtında ya da prompt'ta yok; `verify_dob` yalnız müşterinin söylediği tarihi (`spoken_date`) alır.
- **Ajan:** metin modunda senaryo 1, 2 ve 6 elle oynanınca DB'deki sonuç doğru.
- **Ses:** mikrofonla Türkçe 1 tam arama (senaryo 1) yapılabiliyor.
- **Eval:** `python -m eval.run` 12 senaryo × 3 tekrarı çalıştırıyor ve skor tablosunu basıyor.
