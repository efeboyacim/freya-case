# Eval özeti: 20261118-2237-fix3

Varyant `base` · model `claude-sonnet-5-5` · 2 arama · **skor 24/25 (96.0%)** · maliyet $0.06

## Senaryo × persona (geçen/toplam kontrol)

| # | Senaryo | daginik_girdi | tek_kelime | Toplam |
|---|---|---|---|---|
| 5 | Zeynep: Kadıköy yerleri dolu | 11/12 | · | 11/12 |
| 7 | Burak hiçbir yeri istemez | · | 13/13 | 13/13 |

## Hata öncelik tablosu (öncelik = sıklık × zarar)

Sıklık: hatanın görüldüğü arama / toplam arama.

| Öncelik | Sıklık | Açıklama |
|---|---|---|
| 0.50 | 1/2 | Aynı turda birden fazla soru (zarar 1). Örnek: [05-daginik_girdi-0.md](transcripts/05-daginik_girdi-0.md) |

## Hakemin 'diğer sorunlar' listesi (zarar sırasıyla)

| Zarar | Sorun | Örnek |
|---|---|---|
| 1 | Asistan doğum tarihini zaten net söylenmişken gereksiz yere dört haneli yılla tekrar teyit ettirdi; hafif üslup/verimlilik sorunu. | [05-daginik_girdi-0.md](transcripts/05-daginik_girdi-0.md) |

## Persona başına skor

| Persona | Skor |
|---|---|
| daginik_girdi | 11/12 (92%) |
| tek_kelime | 13/13 (100%) |
