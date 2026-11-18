# Eval özeti: 20261118-2229-fix1

Varyant `base` · model `claude-sonnet-5-5` · 5 arama · **skor 65/68 (95.6%)** · maliyet $0.22

## Senaryo × persona (geçen/toplam kontrol)

| # | Senaryo | daginik_girdi | kararsiz | konuskan | tek_kelime | Toplam |
|---|---|---|---|---|---|---|
| 1 | Ayşe Perşembe'yi seçer | · | · | · | 14/15 | 14/15 |
| 4 | Elif 1 yanlış, sonra doğru | · | 16/16 | · | · | 16/16 |
| 5 | Zeynep: Kadıköy yerleri dolu | 10/12 | · | · | · | 10/12 |
| 7 | Burak hiçbir yeri istemez | · | · | · | 13/13 | 13/13 |
| 8 | Ali kartı istemez | · | · | 12/12 | · | 12/12 |

## Hata öncelik tablosu (öncelik = sıklık × zarar)

Sıklık: hatanın görüldüğü arama / toplam arama.

| Öncelik | Sıklık | Açıklama |
|---|---|---|
| 0.40 | 2/5 | Aynı turda birden fazla soru (zarar 1). Örnek: [01-tek_kelime-0.md](transcripts/01-tek_kelime-0.md) |
| 0.40 | 1/5 | R7: yer yokken/seçilmeyince "gelecek hafta arayacağız" denmedi (zarar 2). Örnek: [05-daginik_girdi-0.md](transcripts/05-daginik_girdi-0.md) |

## Hakemin 'diğer sorunlar' listesi (zarar sırasıyla)

| Zarar | Sorun | Örnek |
|---|---|---|
| 2 | Doğrulamadan sonra müşteriye hiçbir bilgi verilmedi: kurye Salı günü ulaşamadı, bu hafta yer yok açıklaması yapılmadı; görüşme habersiz ve a | [05-daginik_girdi-0.md](transcripts/05-daginik_girdi-0.md) |
| 1 | close_call ikinci kez çağrıldı (409 call_closed); gereksiz tekrar çağrı. Ayrıca kapanıştan sonra konuşmaya devam edildi, ancak müşteriye zar | [07-tek_kelime-0.md](transcripts/07-tek_kelime-0.md) |

## Persona başına skor

| Persona | Skor |
|---|---|
| daginik_girdi | 10/12 (83%) |
| kararsiz | 16/16 (100%) |
| konuskan | 12/12 (100%) |
| tek_kelime | 27/28 (96%) |
