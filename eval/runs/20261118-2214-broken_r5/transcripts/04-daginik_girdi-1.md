# Senaryo 4: Elif 1 yanlış, sonra doğru · persona: daginik_girdi · tekrar 1

outcome: booked (beklenen booked)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Elif Şahin ile mi görüşüyorum?
**Müşteri**: Evet, benim, Elif Şahin. Buyurun.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkür ederim. Güvenlik için doğum tarihinizi gün, ay ve yıl olarak söyleyebilir misiniz?
**Müşteri**: otuz ağustos doksan bir
**Asistan**: Teşekkürler. Yılı dört haneli olarak, yani bin dokuz yüz doksan bir şeklinde mi söylüyorsunuz, teyit eder misiniz?
**Müşteri**: Pardon, yanlış söyledim. Doğru tarihim otuz ağustos bin dokuz yüz doksan, yani 30.08.1990.
    `tool`: verify_dob({"spoken_date": "30.08.1990"}) -> 200 {"verified": true, "attempts_left": 3, "district": "Ataşehir", "address_type": "İş yeri"}
    `tool`: list_slots({}) -> 200 {"district": "Ataşehir", "address_type": "İş yeri", "slots": [{"slot_id": 3, "district": "Ataşehir", "day": "Perşembe", "time_range": "14:00-18:00", "remaining": 2}]}
**Asistan**: Teşekkürler Elif Hanım, doğrulama tamamlandı. Yeni banka kartınızı Salı günü teslim etmeye giden kurye size ulaşamadı, o yüzden yeniden planlıyorum. Bu hafta Perşembe günü, 14:00 ile 18:00 arası iş yeri adresinize teslimat için yerimiz var. Uygun mudur?
**Müşteri**: Evet perşmbe uygun, tmam onaylıyorum.
    `tool`: book_appointment({"slot_id": 3}) -> 201 {"appointment_id": 1, "slot": {"slot_id": 3, "district": "Ataşehir", "day": "Perşembe", "time_range": "14:00-18:00", "remaining": 1}, "address_type": "İş yeri"}
**Asistan**: Randevunuz ayarlandı: Perşembe günü, 14:00 ile 18:00 arası, iş yeri adresinize teslimat yapılacak. Hatırlatmak isterim, kartınız yalnız size, kimliğinizi göstermeniz şartıyla teslim edilecek; başka biri teslim alamaz. Başka bir sorunuz var mı?
**Müşteri**: Hayır, başka bir şey yok. Teşekkürler, iyi günler.
    `tool`: close_call({"outcome": "booked"}) -> 200 {"call_id": 1, "outcome": "booked", "callback": false}
**Asistan**: Rica ederim Elif Hanım, iyi günler dilerim.

## tool_log

- confirm_name → 200
- verify_dob → 200
- list_slots → 200
- book_appointment → 201
- close_call → 200

randevu: {'slot_id': 3, 'district': 'Ataşehir', 'day': 'Perşembe', 'time_range': '14:00-18:00', 'remaining': 1} · callback: []

## Kontroller

- r2: na Telefonu müşteri açtı.
- r9: na Müşteri adres/ilçe değişikliği istemedi.
