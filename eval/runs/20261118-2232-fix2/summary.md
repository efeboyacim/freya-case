# Eval özeti: 20261118-2232-fix2

Varyant `base` · model `claude-sonnet-5-5` · 8 arama · **skor 95/96 (99.0%)** · maliyet $0.29

## Senaryo × persona (geçen/toplam kontrol)

| # | Senaryo | daginik_girdi | isbirlikci | konuskan | supheci | tek_kelime | Toplam |
|---|---|---|---|---|---|---|---|
| 5 | Zeynep: Kadıköy yerleri dolu | 23/23 | 11/12 | · | · | · | 34/35 |
| 7 | Burak hiçbir yeri istemez | · | · | 12/12 | · | 26/26 | 38/38 |
| 8 | Ali kartı istemez | · | · | 12/12 | 11/11 | · | 23/23 |

## Hata öncelik tablosu (öncelik = sıklık × zarar)

Sıklık: hatanın görüldüğü arama / toplam arama.

| Öncelik | Sıklık | Açıklama |
|---|---|---|
| 0.25 | 1/8 | R7: yer yokken/seçilmeyince "gelecek hafta arayacağız" denmedi (zarar 2). Örnek: [05-isbirlikci-1.md](transcripts/05-isbirlikci-1.md) |

## Hakemin 'diğer sorunlar' listesi (zarar sırasıyla)

| Zarar | Sorun | Örnek |
|---|---|---|
| 2 | Asistan müşteriye arama nedenini ve boş yer olmadığını hiç açıklamadı; görüşme açıklamasız bitti. | [05-isbirlikci-1.md](transcripts/05-isbirlikci-1.md) |
| 2 | Müşteri 'kartı istemedim, bankayı bıraktım' dedi; asistan 'Doğru mu?' diye teyit sorup yanıt beklemeden görüşmeyi kapattı. close_call da tey | [08-konuskan-0.md](transcripts/08-konuskan-0.md) |
| 1 | Müşteri müsait olmama nedenini ya da başka seçenek ihtiyacını sormadan hemen close_call yapıldı; ayrıca close_call müşterinin yanıtından son | [07-tek_kelime-0.md](transcripts/07-tek_kelime-0.md) |
| 1 | "Hesabınızda bir sorun yok" ifadesi araç sonuçlarında dayanağı olmayan bir güvence. | [07-konuskan-1.md](transcripts/07-konuskan-1.md) |
| 1 | Asistan close_call'ı müşteri "doğru mu?" sorusuna cevap vermeden çağırdı. Reddi teyit etmeden görüşmeyi kapattı. | [08-supheci-1.md](transcripts/08-supheci-1.md) |
| 1 | Asistan close_call'ı müşteriye bilgi vermeden çağırdı; ardından "tekrar belirtmek isterim" dedi, oysa daha önce yer olmadığını söylememişti. | [05-daginik_girdi-0.md](transcripts/05-daginik_girdi-0.md) |

## Persona başına skor

| Persona | Skor |
|---|---|
| daginik_girdi | 23/23 (100%) |
| isbirlikci | 11/12 (92%) |
| konuskan | 24/24 (100%) |
| supheci | 11/11 (100%) |
| tek_kelime | 26/26 (100%) |
