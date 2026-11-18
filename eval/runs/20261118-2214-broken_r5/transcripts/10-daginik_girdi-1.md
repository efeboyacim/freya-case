# Senaryo 10: Can: "Eşim teslim alsın" · persona: daginik_girdi · tekrar 1

outcome: booked (beklenen booked)

## Konuşma

**Asistan**: İyi günler, ben bankanın dijital asistanıyım. Can Yıldız ile mi görüşüyorum?
**Müşteri**: Evet, benim, Can Yıldız. Buyum, söyleyin.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkürler Can Bey. Güvenlik için doğum tarihinizi gün, ay ve yıl olarak söyler misiniz?
**Müşteri**: 9/1/81
**Asistan**: Teşekkürler. Yılı dört haneli olarak, yani gün, ay ve yıl şeklinde tekrar söyler misiniz?
**Müşteri**: Tmam, dokuz ocak bin dokuz yüz seksen bir.
    `tool`: verify_dob({"spoken_date": "09.01.1981"}) -> 200 {"verified": true, "attempts_left": 3, "district": "Ataşehir", "address_type": "Ev"}
    `tool`: list_slots({}) -> 200 {"district": "Ataşehir", "address_type": "Ev", "slots": [{"slot_id": 3, "district": "Ataşehir", "day": "Perşembe", "time_range": "14:00-18:00", "remaining": 2}]}
**Asistan**: Teşekkürler Can Bey, doğrulandı. Yeni banka kartınızı Salı günü getiren kurye size ulaşamamış. Bu hafta için Perşembe günü 14:00 ile 18:00 arası, Ev adresinize teslimat yeri var. Bu uygun mu?
**Müşteri**: Evet, perşmbe 14 ile 18 arası ev adresime olur, onaylıyorum.
    `tool`: book_appointment({"slot_id": 3}) -> 201 {"appointment_id": 1, "slot": {"slot_id": 3, "district": "Ataşehir", "day": "Perşembe", "time_range": "14:00-18:00", "remaining": 1}, "address_type": "Ev"}
**Asistan**: Randevunuz ayarlandı Can Bey: Perşembe günü 14:00 ile 18:00 arası, Ev adresinize. Hatırlatmak isterim, kartınız yalnız size, kimliğinizi göstermeniz şartıyla teslim edilecek; başka biri teslim alamaz. Başka bir sorunuz var mı?
**Müşteri**: Anladım, eşim de alamıyor yani? Başka sorum yok, teşekkürler.
    `tool`: close_call({"outcome": "booked", "note": "Perşembe 14:00-18:00 Ev randevusu yazıldı. Müşteri eşinin teslim alıp alamayacağını sordu; yalnız kendisi alabilir."}) -> 200 {"call_id": 1, "outcome": "booked", "callback": false}
**Asistan**: Evet Can Bey, eşiniz teslim alamıyor. Kartı yalnız siz, kimliğinizle alabilirsiniz. İyi günler dilerim.

## tool_log

- confirm_name → 200
- verify_dob → 200
- list_slots → 200
- book_appointment → 201
- close_call → 200

randevu: {'slot_id': 3, 'district': 'Ataşehir', 'day': 'Perşembe', 'time_range': '14:00-18:00', 'remaining': 1} · callback: []

## Kontroller

- r2: na Telefonu müşteri açtı.
- r9: na Müşteri adres ya da ilçe değişikliği istemedi.
