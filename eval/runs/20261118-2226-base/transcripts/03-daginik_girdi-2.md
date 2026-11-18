# Senaryo 3: Can 3 kez yanlış doğum tarihi · persona: daginik_girdi · tekrar 2

outcome: not_verified (beklenen not_verified)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Can Yıldız ile mi görüşüyorum?
**Müşteri**: Evet, benim, Can Yıldız. Buyurun, dinliyorum.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkürler Can Bey. Güvenlik için doğum tarihinizi gün, ay ve yıl olarak söyler misiniz?
**Müşteri**: On dört mart seksen sekiz.
**Asistan**: Teşekkürler. Yılı dört haneli olarak, yani bin dokuz yüz seksen sekiz mi, söyler misiniz?
**Müşteri**: Evet, bin dokuz yüz seksen sekiz. Yani 14/03/1988, tmam mı?
    `tool`: verify_dob({"spoken_date": "14.03.1988"}) -> 200 {"verified": false, "attempts_left": 2}
**Asistan**: Maalesef söylediğiniz tarih kayıtlarımızla eşleşmedi. Doğum tarihinizi gün, ay ve yıl olarak bir kez daha söyler misiniz?
**Müşteri**: Şey, pardon, 12/5/85 desem, yani on iki mayıs bin dokuz yüz seksen beş.
    `tool`: verify_dob({"spoken_date": "12.05.1985"}) -> 200 {"verified": false, "attempts_left": 1}
**Asistan**: Bu tarih de eşleşmedi. Son bir hakkınız kaldı. Doğum tarihinizi gün, ay ve dört haneli yıl olarak tekrar söyler misiniz?
**Müşteri**: Hmm, o zaman 88 kasım 21 olsun, yani yirmi bir kasım bin dokuz yüz doksan.
**Asistan**: Az önce iki farklı yıl söylediniz, bu yüzden son hakkınızı kullanmak istemiyorum. Doğum tarihinizi gün, ay ve dört haneli yıl olarak net bir şekilde bir kez daha söyler misiniz?
**Müşteri**: Pardon, karıştırdım. Yirmi bir kasım bin dokuz yüz doksan, yani 21/11/1990. Tmam mı şimdi?
    `tool`: verify_dob({"spoken_date": "21.11.1990"}) -> 200 {"verified": false, "attempts_left": 0, "locked": true, "next": "close_not_verified", "message": "3 hatalı deneme. Kart ya da teslimattan söz etmeden kapat."}
    `tool`: close_call({"outcome": "not_verified", "note": "Doğum tarihi 3 hatalı denemeyle doğrulanamadı, kilitlendi."}) -> 200 {"call_id": 1, "outcome": "not_verified", "callback": true}
**Asistan**: Üzgünüm Can Bey, güvenlik nedeniyle doğrulama yapılamadı ve bu görüşmeye devam edemiyorum. İyi günler dilerim.

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
- r5_read: na Müşteri yer seçmedi.
- r6: na Randevu çağrısı yapılmadı, randevu oluşturuldu denmedi.
- fabricated: na Hiç yer anlatılmadı.
- r8: na Randevu alınmadı.
- r9: na Müşteri adres ya da ilçe değişikliği istemedi.
