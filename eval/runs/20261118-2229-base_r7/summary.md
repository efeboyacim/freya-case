# Eval özeti: 20261118-2229-base_r7

Varyant `base` · model `claude-sonnet-5-5` · 3 arama · **skor 36/36 (100.0%)** · maliyet $0.11

## Senaryo × persona (geçen/toplam kontrol)

| # | Senaryo | daginik_girdi | konuskan | tek_kelime | Toplam |
|---|---|---|---|---|---|
| 5 | Zeynep: Kadıköy yerleri dolu | 11/11 | · | · | 11/11 |
| 7 | Burak hiçbir yeri istemez | · | · | 13/13 | 13/13 |
| 8 | Ali kartı istemez | · | 12/12 | · | 12/12 |

## Hata öncelik tablosu (öncelik = sıklık × zarar)

Sıklık: hatanın görüldüğü arama / toplam arama.

| Öncelik | Sıklık | Açıklama |
|---|---|---|
| - | 0 | hata yok |

## Hakemin 'diğer sorunlar' listesi (zarar sırasıyla)

| Zarar | Sorun | Örnek |
|---|---|---|
| 2 | Asistan, müşteriye uygun yer olmadığını söylemeden close_call ile aramayı kapattı; müşteri sonucu ancak kapanıştan sonra, gerekçe verilmeden | [05-daginik_girdi-0.md](transcripts/05-daginik_girdi-0.md) |
| 1 | Asistan, müşteri reddini onaylatmadan önce close_call çağırıp kapattı; 'doğru anladıysam' dedi ama müşterinin yanıtını beklemedi. | [08-konuskan-0.md](transcripts/08-konuskan-0.md) |

## Persona başına skor

| Persona | Skor |
|---|---|
| daginik_girdi | 11/11 (100%) |
| konuskan | 12/12 (100%) |
| tek_kelime | 13/13 (100%) |
