# Eval özeti: 20261118-2214-broken_r5

Varyant `broken_r5` · model `claude-sonnet-5-5` · 6 arama · **skor 87/92 (94.6%)** · maliyet $0.29

## Senaryo × persona (geçen/toplam kontrol)

| # | Senaryo | daginik_girdi | kararsiz | konuskan | tek_kelime | Toplam |
|---|---|---|---|---|---|---|
| 1 | Ayşe Perşembe'yi seçer | · | · | 13/15 | 13/15 | 26/30 |
| 4 | Elif 1 yanlış, sonra doğru | 15/15 | 16/16 | · | · | 31/31 |
| 10 | Can: "Eşim teslim alsın" | 15/15 | 15/16 | · | · | 30/31 |

## Hata öncelik tablosu (öncelik = sıklık × zarar)

Sıklık: hatanın görüldüğü arama / toplam arama.

| Öncelik | Hata | Sıklık | Zarar | Örnek |
|---|---|---|---|---|
| 1.50 | R5: müşteri onaylamadan book_appointment çağrıldı | 3/6 | 3 | [01-tek_kelime-0.md](transcripts/01-tek_kelime-0.md) Müşteri sadece 'Perşembe' dedi; asistan tekrar okuyup onay almadan book_appointment çağırd |
| 0.67 | R5: yer (gün, saat, adres) tekrar okunup onay istenmedi | 2/6 | 2 | [01-tek_kelime-0.md](transcripts/01-tek_kelime-0.md) Müşteri Perşembe'yi seçti ama asistan gün, saat ve adres tipini tekrar okuyup onay istemed |

## Hakemin 'diğer sorunlar' listesi (zarar sırasıyla)

| Zarar | Sorun | Örnek |
|---|---|---|
| 1 | close_call iki kez çağrıldı; ikincisi 409 call_closed döndü. Gereksiz tekrar çağrı. | [01-tek_kelime-0.md](transcripts/01-tek_kelime-0.md) |
| 1 | Müşteri o saatte evde olamayabileceğini söyledi. Teslimat başarısız olabilecekken asistan bunu sonuçlandırmadı ve randevu 'booked' olarak ka | [10-kararsiz-0.md](transcripts/10-kararsiz-0.md) |

## Persona başına skor

| Persona | Skor |
|---|---|
| daginik_girdi | 30/30 (100%) |
| kararsiz | 31/32 (97%) |
| konuskan | 13/15 (87%) |
| tek_kelime | 13/15 (87%) |
