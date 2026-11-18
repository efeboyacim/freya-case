# Senaryo 4: Elif 1 yanlış, sonra doğru · persona: kararsiz · tekrar 0

outcome: booked (beklenen booked)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Elif Şahin ile mi görüşüyorum?
**Müşteri**: Evet, benim, Elif Şahin. Buyurun.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkür ederim. Güvenlik için doğum tarihinizi gün, ay ve yıl olarak söyleyebilir misiniz?
**Müşteri**: Otuz Ağustos bin dokuz yüz doksan bir.
    `tool`: verify_dob({"spoken_date": "30.08.1991"}) -> 200 {"verified": false, "attempts_left": 2}
**Asistan**: Maalesef söylediğiniz tarih kayıtlarımızla eşleşmedi. Doğum tarihinizi gün, ay ve dört haneli yıl olarak bir kez daha söyler misiniz?
**Müşteri**: Pardon, yanlış söyledim. Otuz Ağustos bin dokuz yüz doksan, yani 30.08.1990.
    `tool`: verify_dob({"spoken_date": "30.08.1990"}) -> 200 {"verified": true, "attempts_left": 2, "district": "Ataşehir", "address_type": "İş yeri"}
    `tool`: list_slots({}) -> 200 {"district": "Ataşehir", "address_type": "İş yeri", "slots": [{"slot_id": 3, "district": "Ataşehir", "day": "Perşembe", "time_range": "14:00-18:00", "remaining": 2}]}
**Asistan**: Teşekkürler, doğrulama tamamlandı. Yeni banka kartınızı Salı günü getiren kurye size ulaşamadı, o yüzden teslimatı yeniden planlıyorum. Perşembe günü 14:00 ile 18:00 arası, iş yeri adresinize teslimat için yerimiz var. Bu uygun olur mu?
**Müşteri**: Perşembe iş yerine mi? Hmm, tamam olur, onu onaylıyorum.
    `tool`: book_appointment({"slot_id": 3}) -> 201 {"appointment_id": 1, "slot": {"slot_id": 3, "district": "Ataşehir", "day": "Perşembe", "time_range": "14:00-18:00", "remaining": 1}, "address_type": "İş yeri"}
**Asistan**: Randevunuz ayarlandı: Perşembe günü 14:00 ile 18:00 arası, iş yeri adresinize teslimat yapılacak. Hatırlatmak isterim, kartınız yalnız size, kimliğinizi göstermeniz şartıyla teslim edilecek; başka biri teslim alamaz. Başka bir sorunuz var mı?
**Müşteri**: Bir dakika, aslında eve teslim olsa daha mı iyi olur acaba? Yani başka bir seçenek var mı, ona bakabilir misiniz?
**Asistan**: Anlıyorum ama müşteri başına yalnız bir randevu verebiliyoruz, bu yüzden ikinci bir randevu açamam. Ayrıca teslimat adresi ya da ilçe değişikliğini telefonda yapamıyorum. Bunu bankanın mobil uygulamasından yapabilirsiniz. Perşembe 14:00 ile 18:00 arası iş yeri randevunuz geçerli. Başka bir sorunuz var mı?
**Müşteri**: Anladım, o zaman Perşembe iş yeri olsun, bozmayalım. Başka bir sorum yok, teşekkür ederim.
    `tool`: close_call({"outcome": "booked", "note": "Perşembe 14:00-18:00 İş yeri randevusu yazıldı. Müşteri ev teslimatı sordu, tek randevu kuralı ve uygulama yönlendirmesi yapıldı."}) -> 200 {"call_id": 1, "outcome": "booked", "callback": false}
**Asistan**: Rica ederim Elif Hanım, randevunuz Perşembe günü 14:00 ile 18:00 arası iş yeri adresinizde geçerli. İyi günler dilerim.

## tool_log

- confirm_name → 200
- verify_dob → 200
- verify_dob → 200
- list_slots → 200
- book_appointment → 201
- close_call → 200

randevu: {'slot_id': 3, 'district': 'Ataşehir', 'day': 'Perşembe', 'time_range': '14:00-18:00', 'remaining': 1} · callback: []

## Kontroller

- r2: na Telefonu müşteri açtı.
- r7: na Randevu alındı.
