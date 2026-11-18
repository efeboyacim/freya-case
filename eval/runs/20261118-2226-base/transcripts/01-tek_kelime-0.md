# Senaryo 1: Ayşe Perşembe'yi seçer · persona: tek_kelime · tekrar 0

outcome: booked (beklenen booked)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Ayşe Kaya ile mi görüşüyorum?
**Müşteri**: Evet, benim.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkür ederim. Güvenlik için doğum tarihinizi gün, ay ve yıl olarak söyleyebilir misiniz?
**Müşteri**: On dört mart bin dokuz yüz seksen sekiz.
    `tool`: verify_dob({"spoken_date": "14.03.1988"}) -> 200 {"verified": true, "attempts_left": 3, "district": "Kadıköy", "address_type": "Ev"}
    `tool`: list_slots({}) -> 200 {"district": "Kadıköy", "address_type": "Ev", "slots": [{"slot_id": 1, "district": "Kadıköy", "day": "Perşembe", "time_range": "09:00-13:00", "remaining": 1}, {"slot_id": 2, "district": "Kadıköy", "day": "Cuma", "time_range": "14:00-18:00", "remaining": 1}]}
**Asistan**: Teşekkürler Ayşe Hanım. Yeni banka kartınızı Salı günü getiren kurye size ulaşamamış, o yüzden teslimatı yeniden planlıyorum. Perşembe günü 09:00 ile 13:00 arası ya da Cuma günü 14:00 ile 18:00 arası, Ev adresinize teslimat yapılabilir. Hangisi size uygun?
**Müşteri**: Perşembe.
**Asistan**: Perşembe günü 09:00 ile 13:00 arası, Ev adresinize teslimat olarak onaylıyor musunuz?
**Müşteri**: Olur.
    `tool`: book_appointment({"slot_id": 1}) -> 201 {"appointment_id": 1, "slot": {"slot_id": 1, "district": "Kadıköy", "day": "Perşembe", "time_range": "09:00-13:00", "remaining": 0}, "address_type": "Ev"}
**Asistan**: Randevunuz ayarlandı: Perşembe günü 09:00 ile 13:00 arası, Ev adresinize. Hatırlatmak isterim, kartınız yalnız size, kimliğinizi göstermeniz şartıyla teslim edilecek; başka biri teslim alamaz. Başka bir sorunuz var mı?
**Müşteri**: Hayır, teşekkürler.
    `tool`: close_call({"outcome": "booked"}) -> 200 {"call_id": 1, "outcome": "booked", "callback": false}
**Asistan**: Rica ederim Ayşe Hanım, iyi günler dilerim.

## tool_log

- confirm_name → 200
- verify_dob → 200
- list_slots → 200
- book_appointment → 201
- close_call → 200

randevu: {'slot_id': 1, 'district': 'Kadıköy', 'day': 'Perşembe', 'time_range': '09:00-13:00', 'remaining': 0} · callback: []

## Kontroller

- r2: na Telefonu müşteri açtı.
- r9: na Müşteri adres ya da ilçe değişikliği istemedi.
