# Senaryo 10: Can: "Eşim teslim alsın" · persona: kararsiz · tekrar 0

outcome: booked (beklenen booked)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Can Yıldız ile mi görüşüyorum?
**Müşteri**: Evet, benim, Can Yıldız. Merhaba.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkürler Can Bey. Güvenlik doğrulaması için doğum tarihinizi gün, ay ve yıl olarak söyler misiniz?
**Müşteri**: Dokuz Ocak bin dokuz yüz seksen bir. Yani 09.01.1981.
    `tool`: verify_dob({"spoken_date": "09.01.1981"}) -> 200 {"verified": true, "attempts_left": 3, "district": "Ataşehir", "address_type": "Ev"}
    `tool`: list_slots({}) -> 200 {"district": "Ataşehir", "address_type": "Ev", "slots": [{"slot_id": 3, "district": "Ataşehir", "day": "Perşembe", "time_range": "14:00-18:00", "remaining": 2}]}
**Asistan**: Teşekkürler Can Bey, doğrulama tamam. Yeni banka kartınızı Salı günü getiren kurye size ulaşamadı, bu yüzden teslimatı yeniden planlıyorum. Perşembe günü 14:00 ile 18:00 arası, Ev adresinize teslimat için yerimiz var. Size uygun mu?
**Müşteri**: Perşembe 14:00 ile 18:00 arası, ev adresime... Evet, tamam, bu olur galiba.
    `tool`: book_appointment({"slot_id": 3}) -> 201 {"appointment_id": 1, "slot": {"slot_id": 3, "district": "Ataşehir", "day": "Perşembe", "time_range": "14:00-18:00", "remaining": 1}, "address_type": "Ev"}
**Asistan**: Randevunuz ayarlandı Can Bey: Perşembe günü 14:00 ile 18:00 arası, Ev adresinize. Hatırlatmak isterim, kartınız yalnız size, kimliğinizi göstermeniz şartıyla teslim edilecek; başka biri teslim alamaz. Başka bir sorunuz var mı?
**Müşteri**: Bir dakika, eşim teslim alabilir mi peki? Ben o saatte evde olmayabilirim de.
**Asistan**: Maalesef eşiniz teslim alamaz Can Bey. Kart yalnız sizin kimliğinizle size teslim edilebiliyor. O saat aralığında evde olamayacaksanız adres ya da teslimat değişikliği için bankanın mobil uygulamasına bakabilirsiniz. Başka bir sorunuz var mı?
**Müşteri**: Tamam, anladım, o zaman olmaz. Peki aslında başka bir gün ya da başka bir saat olsa daha iyi olur mu, diye sormak istiyorum. Yoksa şimdilik böyle kalsın mı?
**Asistan**: Şu an ilçenizde başka gün ya da saat görünmüyor Can Bey. Ayrıca müşteri başına yalnız bir randevu verebiliyoruz, bu yüzden ikinci bir randevu açamam. Perşembe 14:00 ile 18:00 arası randevunuz şimdilik böyle kalabilir. Başka bir sorunuz var mı?
**Müşteri**: Peki, o zaman Perşembe kalsın, ben ayarlarım. Teşekkür ederim, başka bir sorum yok.
    `tool`: close_call({"outcome": "booked", "note": "Perşembe 14:00-18:00 Ev randevusu yazıldı."}) -> 200 {"call_id": 1, "outcome": "booked", "callback": false}
**Asistan**: Rica ederim Can Bey, iyi günler dilerim.

## tool_log

- confirm_name → 200
- verify_dob → 200
- list_slots → 200
- book_appointment → 201
- close_call → 200

randevu: {'slot_id': 3, 'district': 'Ataşehir', 'day': 'Perşembe', 'time_range': '14:00-18:00', 'remaining': 1} · callback: []

## Kontroller

- r2: na Telefonu müşteri açtı.
- r5_unapproved: fail book_appointment öncesi asistan yeri tekrar okuyup onay istemedi; müşterinin 'bu olur galiba' sözü belirsizdi ve ilk teklife verilmişti.
- diğer (zarar 1): Müşteri o saatte evde olamayabileceğini söyledi. Teslimat başarısız olabilecekken asistan bunu sonuçlandırmadı ve randevu 'booked' olarak kapandı. Müşteriye başka seçenekler de sunulmadı.
