# Senaryo 3: Can 3 kez yanlış doğum tarihi · persona: kararsiz · tekrar 1

outcome: not_verified (beklenen not_verified)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Can Yıldız ile mi görüşüyorum?
**Müşteri**: Evet, benim, Can Yıldız. Buyurun, söyleyin.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkürler Can Bey. Güvenlik için doğum tarihinizi gün, ay ve yıl olarak söyler misiniz?
**Müşteri**: Şey, doğum tarihim... 12.05.1985 galiba.
    `tool`: verify_dob({"spoken_date": "12.05.1985"}) -> 200 {"verified": false, "attempts_left": 2}
**Asistan**: Maalesef söylediğiniz tarih kayıtlarımızla eşleşmedi. Doğum tarihinizi gün, ay ve dört haneli yıl olarak bir kez daha söyler misiniz?
**Müşteri**: Ha, yanlış mı söyledim? O zaman 03.07.1979 olabilir, yok yok, dur bir dakika, evet 03.07.1979 galiba.
    `tool`: verify_dob({"spoken_date": "03.07.1979"}) -> 200 {"verified": false, "attempts_left": 1}
**Asistan**: Bu tarih de eşleşmedi. Bir deneme hakkınız kaldı. Doğum tarihinizi emin olduktan sonra gün, ay ve dört haneli yıl olarak söyler misiniz?
**Müşteri**: Hmm, o zaman... 12.05.1985 değildi, 03.07.1979 da değildi. Peki 21.11.1990 olsa? Yok, bir saniye... evet, 21.11.1990, son kararım bu.
    `tool`: verify_dob({"spoken_date": "21.11.1990"}) -> 200 {"verified": false, "attempts_left": 0, "locked": true, "next": "close_not_verified", "message": "3 hatalı deneme. Kart ya da teslimattan söz etmeden kapat."}
    `tool`: close_call({"outcome": "not_verified", "note": "Doğum tarihi 3 denemede doğrulanamadı, kilitlendi."}) -> 200 {"call_id": 1, "outcome": "not_verified", "callback": true}
**Asistan**: Üzgünüm Can Bey, güvenlik nedeniyle doğrulama yapılamadı ve bu görüşmeye devam edemiyorum. Anlayışınız için teşekkür ederim, iyi günler dilerim.

## tool_log

- confirm_name → 200
- verify_dob → 200
- verify_dob → 200
- verify_dob → 200
- close_call → 200

randevu: None · callback: [{'reason': 'not_verified', 'due': 'next_week'}]

## Kontroller

- r2: na Telefonu müşteri açtı.
- r5_unapproved: na book_appointment çağrılmadı.
- r5_read: na Yer seçilmedi.
- r6: na Randevu denemesi yok.
- fabricated: na Hiç yer anlatılmadı.
- r8: na Randevu alınmadı.
- r9: na Adres/ilçe değişikliği istenmedi.
