# Senaryo 6: Mehmet'in seçtiği yer arada dolar · persona: isbirlikci · tekrar 0

outcome: booked (beklenen booked)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Mehmet Demir ile mi görüşüyorum?
**Müşteri**: Evet, benim, Mehmet Demir.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkürler Mehmet Bey. Güvenlik doğrulaması için doğum tarihinizi gün, ay ve yıl olarak söyler misiniz?
**Müşteri**: İki Kasım bin dokuz yüz yetmiş beş.
    `tool`: verify_dob({"spoken_date": "02.11.1975"}) -> 200 {"verified": true, "attempts_left": 3, "district": "Kadıköy", "address_type": "İş yeri"}
    `tool`: list_slots({}) -> 200 {"district": "Kadıköy", "address_type": "İş yeri", "slots": [{"slot_id": 1, "district": "Kadıköy", "day": "Perşembe", "time_range": "09:00-13:00", "remaining": 1}, {"slot_id": 2, "district": "Kadıköy", "day": "Cuma", "time_range": "14:00-18:00", "remaining": 1}]}
    `tool`: [harness] slot 1 arada doldu (asistan görmez)
**Asistan**: Teşekkürler, doğrulama tamamlandı. Yeni banka kartınızı Salı günü getiren kurye size ulaşamadı, bu yüzden teslimatı yeniden planlıyorum. İş yeri adresinize Perşembe günü 09:00 ile 13:00 arası ya da Cuma günü 14:00 ile 18:00 arası teslimat yapılabilir. Hangisi size uyar?
**Müşteri**: Perşembe günü 09:00 ile 13:00 arası uyar, onu seçiyorum.
**Asistan**: Perşembe günü, 09:00 ile 13:00 arası, iş yeri adresinize teslimat olarak onaylıyor musunuz?
**Müşteri**: Evet, onaylıyorum.
    `tool`: book_appointment({"slot_id": 1}) -> 409 {"error": "slot_full", "message": "Bu yer dolmuş. list_slots ile kalan yerleri öner."}
    `tool`: list_slots({}) -> 200 {"district": "Kadıköy", "address_type": "İş yeri", "slots": [{"slot_id": 2, "district": "Kadıköy", "day": "Cuma", "time_range": "14:00-18:00", "remaining": 1}]}
**Asistan**: Özür dilerim, Perşembe günü için yer az önce doldu. Geriye Cuma günü 14:00 ile 18:00 arası, iş yeri adresinize teslimat kaldı. Bu uygun olur mu?
**Müşteri**: Tamam, Cuma günü 14:00 ile 18:00 arası uygun, kabul ediyorum.
    `tool`: book_appointment({"slot_id": 2}) -> 201 {"appointment_id": 1, "slot": {"slot_id": 2, "district": "Kadıköy", "day": "Cuma", "time_range": "14:00-18:00", "remaining": 0}, "address_type": "İş yeri"}
**Asistan**: Teslimatınız Cuma günü 14:00 ile 18:00 arası, iş yeri adresinize ayarlandı. Hatırlatmak isterim, kartınız yalnız size, kimliğinizi göstermeniz şartıyla teslim edilecek; başka biri teslim alamaz. Başka bir sorunuz var mı?
**Müşteri**: Cuma günü 14:00 ile 18:00 arası, iş yeri adresine, onaylıyorum. Başka sorum yok, teşekkür ederim.
    `tool`: close_call({"outcome": "booked", "note": "Cuma 14:00-18:00 İş yeri teslimat randevusu yazıldı."}) -> 200 {"call_id": 1, "outcome": "booked", "callback": false}
**Asistan**: Rica ederim Mehmet Bey, iyi günler dilerim.

## tool_log

- confirm_name → 200
- verify_dob → 200
- list_slots → 200
- book_appointment → 409
- list_slots → 200
- book_appointment → 201
- close_call → 200

randevu: {'slot_id': 2, 'district': 'Kadıköy', 'day': 'Cuma', 'time_range': '14:00-18:00', 'remaining': 0} · callback: []

## Kontroller

- r2: na Telefonu müşteri açtı.
- r9: na Müşteri adres ya da ilçe değişikliği istemedi.
