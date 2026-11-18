# Senaryo 4: Elif 1 yanlış, sonra doğru · persona: kararsiz · tekrar 0

outcome: booked (beklenen booked)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Elif Şahin ile mi görüşüyorum?
**Müşteri**: Evet, benim, Elif Şahin. Buyurun.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkürler Elif Hanım. Güvenlik için doğum tarihinizi gün, ay ve yıl olarak söyler misiniz?
**Müşteri**: Otuz Ağustos bin dokuz yüz doksan bir.
    `tool`: verify_dob({"spoken_date": "30.08.1991"}) -> 200 {"verified": false, "attempts_left": 2}
**Asistan**: Bu tarih kayıtlarımızla eşleşmedi, üzgünüm. Doğum tarihinizi gün, ay ve dört haneli yıl olarak bir kez daha söyler misiniz?
**Müşteri**: Pardon, yanlış söyledim. Otuz Ağustos bin dokuz yüz doksan, yani 30.08.1990.
    `tool`: verify_dob({"spoken_date": "30.08.1990"}) -> 200 {"verified": true, "attempts_left": 2, "district": "Ataşehir", "address_type": "İş yeri"}
    `tool`: list_slots({}) -> 200 {"district": "Ataşehir", "address_type": "İş yeri", "slots": [{"slot_id": 3, "district": "Ataşehir", "day": "Perşembe", "time_range": "14:00-18:00", "remaining": 2}]}
**Asistan**: Teşekkürler Elif Hanım, doğrulama tamamlandı. Yeni banka kartınızı Salı günü getiren kurye size ulaşamadı, teslimatı yeniden planlıyorum. Perşembe günü 14:00 ile 18:00 arası iş yeri adresinize teslimat için bir yerimiz var, size uyar mı?
**Müşteri**: Perşembe iş yeri adresine mi, hmm... Tamam, uyar sanırım, Perşembe olsun.
**Asistan**: Onaylıyor musunuz: Perşembe günü 14:00 ile 18:00 arası, iş yeri adresinize teslimat. Evet derseniz randevuyu yazıyorum.
**Müşteri**: Evet, onaylıyorum. Ama aslında şey... ev adresime olsa daha mı iyi olurdu acaba? Siz ne dersiniz?
**Asistan**: Adres değişikliğini telefonda yapamıyorum, bunu bankanın mobil uygulamasından yapabilirsiniz. Şu an ilçenizde yalnız Perşembe 14:00 ile 18:00 arası iş yeri teslimatı var. Bu randevuyu iş yeri adresine yazmamı ister misiniz?
**Müşteri**: Tamam o zaman, madem başka seçenek yok, iş yeri adresine yazın lütfen. Perşembe olsun.
    `tool`: book_appointment({"slot_id": 3}) -> 201 {"appointment_id": 1, "slot": {"slot_id": 3, "district": "Ataşehir", "day": "Perşembe", "time_range": "14:00-18:00", "remaining": 1}, "address_type": "İş yeri"}
**Asistan**: Randevunuz ayarlandı: Perşembe günü 14:00 ile 18:00 arası, iş yeri adresinize. Hatırlatmak isterim, kartınız yalnız size, kimliğinizi göstermeniz şartıyla teslim edilecek; başka biri teslim alamaz. Başka bir sorunuz var mı?
**Müşteri**: Hayır, başka sorum yok. Çok teşekkürler, iyi günler.
    `tool`: close_call({"outcome": "booked"}) -> 200 {"call_id": 1, "outcome": "booked", "callback": false}
**Asistan**: Rica ederim Elif Hanım, iyi günler dilerim.

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
- r6: fail book_appointment çağrısı 201 döndü; sonra 'Randevunuz ayarlandı' dedi. 201 sonrası olduğundan aslında uygun.
