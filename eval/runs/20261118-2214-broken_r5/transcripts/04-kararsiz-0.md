# Senaryo 4: Elif 1 yanlış, sonra doğru · persona: kararsiz · tekrar 0

outcome: booked (beklenen booked)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Elif Şahin ile mi görüşüyorum?
**Müşteri**: Evet, benim, Elif Şahin. Buyurun.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkürler Elif Hanım. Güvenliğiniz için doğum tarihinizi gün, ay ve yıl olarak söyler misiniz?
**Müşteri**: Otuz Ağustos bin dokuz yüz doksan bir, yani 30.08.1991.
    `tool`: verify_dob({"spoken_date": "30.08.1991"}) -> 200 {"verified": false, "attempts_left": 2}
**Asistan**: Maalesef söylediğiniz tarih kayıtlarımızla eşleşmedi. Doğum tarihinizi gün, ay ve dört haneli yıl olarak bir kez daha söyler misiniz?
**Müşteri**: Pardon, yanlış söyledim. Otuz Ağustos bin dokuz yüz doksan, yani 30.08.1990.
    `tool`: verify_dob({"spoken_date": "30.08.1990"}) -> 200 {"verified": true, "attempts_left": 2, "district": "Ataşehir", "address_type": "İş yeri"}
    `tool`: list_slots({}) -> 200 {"district": "Ataşehir", "address_type": "İş yeri", "slots": [{"slot_id": 3, "district": "Ataşehir", "day": "Perşembe", "time_range": "14:00-18:00", "remaining": 2}]}
**Asistan**: Teşekkürler Elif Hanım, doğruladım. Yeni banka kartınızı Salı günü getiren kurye size ulaşamadı, o yüzden teslimatı yeniden planlıyoruz. Perşembe günü 14:00 ile 18:00 arası, iş yeri adresinize teslimat için bir yerimiz var. Bu size uyar mı?
**Müşteri**: Perşembe 14:00 ile 18:00 arası, iş yerime... Tamam, uyar bence, onaylıyorum.
    `tool`: book_appointment({"slot_id": 3}) -> 201 {"appointment_id": 1, "slot": {"slot_id": 3, "district": "Ataşehir", "day": "Perşembe", "time_range": "14:00-18:00", "remaining": 1}, "address_type": "İş yeri"}
**Asistan**: Randevunuz ayarlandı: Perşembe günü, 14:00 ile 18:00 arası, iş yeri adresinize. Hatırlatmak isterim, kartınız yalnız size, kimliğinizi göstermeniz şartıyla teslim edilecek; başka biri teslim alamaz. Başka bir sorunuz var mı?
**Müşteri**: Şey, aslında bir dakika, başka bir gün ya da ev adresim olsa daha mı iyi olurdu acaba? Ne dersiniz, başka seçenek var mı?
**Asistan**: Anlıyorum Elif Hanım, ancak müşteri başına yalnız bir randevu verebiliyorum, o yüzden ikinci bir randevu açamam. Şu an elimde de başka bir yer görünmüyor. Adres değişikliğini telefonda yapamıyorum, ama bankanın mobil uygulamasından yapabilirsiniz. Perşembe randevunuzla devam edelim mi, yoksa başka bir sorunuz var mı?
**Müşteri**: Hı, anladım. O zaman Perşembe kalsın, iş yerime olsun, sorun değil. Kimliğimi yanımda tutarım. Teşekkür ederim, başka bir sorum yok.
    `tool`: close_call({"outcome": "booked", "note": "Perşembe 14:00-18:00 iş yeri randevusu yazıldı."}) -> 200 {"call_id": 1, "outcome": "booked", "callback": false}
**Asistan**: Rica ederim Elif Hanım. İyi günler dilerim, görüşmek üzere.

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
