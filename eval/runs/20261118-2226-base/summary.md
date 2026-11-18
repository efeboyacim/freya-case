# Eval özeti: 20261118-2226-base

Varyant `base` · model `claude-sonnet-5-5` · 19 arama · **skor 244/245 (99.6%)** · maliyet $0.79

## Senaryo × persona (geçen/toplam kontrol)

| # | Senaryo | - | daginik_girdi | isbirlikci | kararsiz | konuskan | supheci | tek_kelime | Toplam |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Ayşe Perşembe'yi seçer | · | · | · | · | 15/15 | 15/15 | 15/15 | 45/45 |
| 2 | Selin'in telefonunu başkası açar | · | · | · | 11/11 | 11/11 | 11/11 | · | 33/33 |
| 3 | Can 3 kez yanlış doğum tarihi | · | 10/10 | · | 10/10 | · | 10/10 | · | 30/30 |
| 4 | Elif 1 yanlış, sonra doğru | · | · | · | 31/32 | · | · | · | 31/32 |
| 5 | Zeynep: Kadıköy yerleri dolu | · | 11/11 | · | · | · | · | · | 11/11 |
| 6 | Mehmet'in seçtiği yer arada dolar | · | · | 15/15 | · | · | · | · | 15/15 |
| 7 | Burak hiçbir yeri istemez | · | · | · | · | · | · | 12/12 | 12/12 |
| 8 | Ali kartı istemez | · | · | · | · | 12/12 | · | · | 12/12 |
| 9 | Elif ilçe değiştirmek ister | · | · | · | · | · | 16/16 | · | 16/16 |
| 10 | Can: "Eşim teslim alsın" | · | · | · | 15/15 | · | · | · | 15/15 |
| 11 | Selin iki randevu ister | · | 15/15 | · | · | · | · | · | 15/15 |
| 12 | Can'ın telefonu açılmaz | 9/9 | · | · | · | · | · | · | 9/9 |

## Hata öncelik tablosu (öncelik = sıklık × zarar)

Sıklık: hatanın görüldüğü arama / toplam arama.

| Öncelik | Sıklık | Açıklama |
|---|---|---|
| 0.16 | 1/19 | R6: 201 gelmeden "ayarlandı" denildi (zarar 3). Örnek: [04-kararsiz-0.md](transcripts/04-kararsiz-0.md) |

## Hakemin 'diğer sorunlar' listesi (zarar sırasıyla)

| Zarar | Sorun | Örnek |
|---|---|---|
| 2 | Müşteri teslimatın tamamen iptalini istedi; asistan iptalin yapılıp yapılmadığını ve kartın akıbetini açıklamadı. Sadece 'not alıyorum' dedi | [08-konuskan-0.md](transcripts/08-konuskan-0.md) |
| 2 | Asistan müşteriye boş slot olmadığını, gelecek hafta aranacağını açıklamadan sadece 'Aramayı sonlandırdım' dedi; müşteri bilgilendirilmedi,  | [05-daginik_girdi-0.md](transcripts/05-daginik_girdi-0.md) |
| 2 | Asistan 'Müşteri başına da yalnızca bir randevu verilebiliyor' dedi. Bu bilgi [tool] sonuçlarında ve görev tanımında yok. Kayda göre dayanak | [10-kararsiz-0.md](transcripts/10-kararsiz-0.md) |
| 1 | 'kurye bu aralık içinde size ulaşacak' kesin bir söz. Kaydın gösterdiği tek şey randevu aralığı. Kuryenin gecikmeyeceğini garanti edecek bir | [01-konuskan-1.md](transcripts/01-konuskan-1.md) |
| 1 | Asistan kimlik doğrulanmadan önce 'size özel bir konuyu paylaşmadan önce' diyerek hafifçe arama konusuna işaret etti; ayrıca müşterinin 'ban | [01-supheci-2.md](transcripts/01-supheci-2.md) |
| 1 | Asistan müşteriye Cuma dışında başka gün/seçenek ya da gelecek haftaya ilişkin alternatif sormadan görüşmeyi hemen kapattı; ayrıca 'gelecek  | [07-tek_kelime-0.md](transcripts/07-tek_kelime-0.md) |

## Persona başına skor

| Persona | Skor |
|---|---|
| - | 9/9 (100%) |
| daginik_girdi | 36/36 (100%) |
| isbirlikci | 15/15 (100%) |
| kararsiz | 67/68 (99%) |
| konuskan | 38/38 (100%) |
| supheci | 52/52 (100%) |
| tek_kelime | 27/27 (100%) |
