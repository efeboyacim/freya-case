# Eval bulguları (Aşama 4)

Model `claude-sonnet-5-5` (effort `low`), müşteri simülatörü ve hakem aynı model. Süre kısıtı nedeniyle koşular **kısaltıldı**: 12 senaryo × 3 tekrarın tamamı yerine tabanda 19 arama (senaryo 1–12, çoğu 1 tekrar) koşuldu. Rakamlar küçük örneklemdir, kesin oran değil yönü gösterir. Skor = geçen kontrol / uygulanabilir kontrol.

| Koşu | Klasör | Arama | Skor |
|---|---|---|---|
| Taban (ilk hakem) | `runs/20261118-2226-base` | 19 | 244/245 (%99,6) |
| `broken_r5` (R5 onay adımı silinmiş prompt) | `runs/20261118-2214-broken_r5` | 6 (s1, s4, s10) | 87/92 (%94,6) |
| Taban, R7 kontrolü eklenmiş hakemle | `runs/20261118-2229-base_r7` | 3 (s5, s7, s8) | 36/36 |
| fix1 (prompt düzeltmesi) | `runs/20261118-2229-fix1` | 5 (s1, s4, s5, s7, s8) | 65/68 (%95,6) |
| fix2 (+ `close_call` sonucuna `next`) | `runs/20261118-2232-fix2` | 8 (s5, s7, s8) | 95/96 (%99,0) |
| fix3 (R7 kodda: `ensure_r7`) | `runs/20261118-2237-fix3` | 2 (s5, s7, 1 tekrar) | 24/25 (%96,0) |

## 1. Kontroller bir şey ölçüyor mu? (`broken_r5`)
Aynı senaryolarda (1, 4, 10) tabanda 6 aramanın 91/92'si geçti (%98,9). R5 onay adımı silinince skor %94,6'ya düştü ve öncelik tablosunun ilk iki satırı R5 oldu:

| Öncelik | Sıklık | Açıklama |
|---|---|---|
| 1,50 | 3/6 | R5: müşteri onaylamadan book_appointment çağrıldı (zarar 3) |
| 0,67 | 2/6 | R5: yer (gün, saat, adres) tekrar okunup onay istenmedi (zarar 2) |

Tabanda (19 arama) bu iki hata hiç görülmedi. Düşüş küçük görünüyor çünkü R5 yalnız randevu alınan aramalarda uygulanır.

## 2. Taban öncelik tablosu (`20261118-2226-base`, 19 arama)

| Öncelik | Sıklık | Açıklama |
|---|---|---|
| 0,16 | 1/19 | R6: "201 gelmeden ayarlandı denildi" (zarar 3). **Hakem hatası**: transkriptte "ayarlandı" 201'den sonra söyleniyor, hakemin kendi notu "aslında uygun" diyor. |

Hakemin "diğer sorunlar" listesinden çıkan gerçek hata: **yer yokken asistan `close_call`'u metinsiz çağırıp yalnız "Aramayı sonlandırdım" dedi** (s5, `05-daginik_girdi-0`), R7'nin "Sizi gelecek hafta arayacağız" cümlesi geçmedi (zarar 2). Bu hatayı ölçen kontrol yoktu. Diğer gözlemler: reddedilen teslimatta sonuç açıklanmıyor, "müşteri başına tek randevu" (R10) cümlesi hakemce yanlışlıkla "dayanaksız" sayıldı.

## 3. Yapılan düzeltmeler
1. **Hakem:** `r7` kontrolü eklendi. R6 yanlış alarmı için "not ile karar çelişmesin" ve bilinen kurallar (tek randevu, adres değişikliği uygulamadan) notu eklendi.
2. **Prompt (fix1):** Sonuç ve vedayı `close_call`'dan önce yaz; yer yoksa nedeni söyle ve aynen "Sizi gelecek hafta arayacağız" de; reddedilirse kararı not aldığını söyle.
3. **R7 kodda (fix3):** `session.ensure_r7`, `no_slot` ile kapanan turda yanıtta "gelecek hafta" yoksa "Sizi gelecek hafta arayacağız." cümlesini başa ekler. Model unutsa bile kural çalışır; `send()` üzerinden geçtiği için ses modu da kapsanır. Birim testi: `tests/test_assistant.py::test_ensure_r7_adds_next_week_line_only_for_no_slot`.
4. **`close_call` sonucuna `next` (fix2):** `no_slot` ve `declined` sonucunda tool, modele son sözü ne söyleyeceğini yazar (Aşama 2'de R8 için işe yarayan yöntem). Model aynı turda zaten bir şey söylediyse metin atılır.

## 4. Önce / sonra (R7, yani `no_slot` aramaları)

| Koşu | R7 hatası | Not |
|---|---|---|
| Taban, ilk koşu | 1/? | Kontrol yoktu; ihlal transkriptte elle görüldü (s5) |
| Taban + R7 hakemi | 0/2 | Bu iki aramada model kapanıştan sonra "gelecek hafta ulaşılacak" dedi |
| fix1 | 1/2 | s5'te model hâlâ metinsiz `close_call` çağırıp "Hoşça kalın" dedi |
| fix2 | 1/6 | s5 `isbirlikci`: `next` talimatına rağmen "hoşça kalın" |
| fix3 (kodda) | 0/2 | Zaman kısıtı nedeniyle yalnız 1 tekrar; asıl kanıt birim testi |

**Sonuç (fix1–fix2):** Prompt ve `next` düzeltmesi R7'yi kesin olarak kapatmadı. Örneklem (2–6 arama) iyileşmeyi ya da kötüleşmeyi ayırt etmek için çok küçük. R6 yanlış alarmı ise düzeldi (sonraki koşularda görülmedi). `fix1`'deki 2/5 "birden fazla soru" üslup hatası örnekleme gürültüsü gibi duruyor, taban ve `fix2`'de görülmedi.

## 5. Açık kalanlar
- R7 artık kodla garanti (fix3), ama eval kanıtı yalnız 2 arama (zaman kısıtı, tek tur). Eklenen cümle `list_slots` boşken "neden" açıklamasının yerini tutmaz; model nedeni söylemeyebilir.
- 12 senaryo × 3 tekrar tam koşusu yapılmadı. Persona başına örnek sayısı 1–3.
- Hakem aynı modelle çalışıyor ve zaman zaman kendi notuyla çelişen karar veriyor. Önemli bulgular transkriptten elle doğrulanmalı.
