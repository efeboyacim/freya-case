# Senaryo 11: Selin iki randevu ister · persona: daginik_girdi · tekrar 0

outcome: booked (beklenen booked)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Selin Aydın ile mi görüşüyorum?
**Müşteri**: Evet, benim, Selin Aydın. Buyurun.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkürler Selin Hanım. Güvenliğiniz için doğum tarihinizi gün, ay ve dört haneli yıl olarak söyler misiniz?
**Müşteri**: beş nisan doksan dokuz.
**Asistan**: Teşekkürler. Doğrulama için yılı dört haneli olarak, yani bin dokuz yüz doksan dokuz mu olduğunu söyleyebilir misiniz?
**Müşteri**: Evet, bin dokuz yüz doksan dokuz. Yani 5 Nisan 1999.
    `tool`: verify_dob({"spoken_date": "05.04.1999"}) -> 200 {"verified": true, "attempts_left": 3, "district": "Şişli", "address_type": "Ev"}
    `tool`: list_slots({}) -> 200 {"district": "Şişli", "address_type": "Ev", "slots": [{"slot_id": 4, "district": "Şişli", "day": "Cuma", "time_range": "09:00-13:00", "remaining": 2}]}
**Asistan**: Teşekkürler Selin Hanım, doğrulama tamamlandı. Yeni banka kartınızı Salı günü getiren kurye size ulaşamadı, o yüzden teslimatı yeniden planlıyorum. Cuma günü 09:00 ile 13:00 arası, Ev adresinize bir yerimiz var. Bu uygun mu?
**Müşteri**: Cuma günü tmam, uygun. Ev adresime olsun, onaylıyorum.
    `tool`: book_appointment({"slot_id": 4}) -> 201 {"appointment_id": 1, "slot": {"slot_id": 4, "district": "Şişli", "day": "Cuma", "time_range": "09:00-13:00", "remaining": 1}, "address_type": "Ev"}
**Asistan**: Randevunuz ayarlandı: Cuma günü 09:00 ile 13:00 arası, Ev adresinize teslimat yapılacak. Hatırlatmak isterim, kartınız yalnız size, kimliğinizi göstermeniz şartıyla teslim edilecek; başka biri teslim alamaz. Başka bir sorunuz var mı?
**Müşteri**: Bir de arkadaşım için ikinci bir randevu alabilir miyim? Aynı saatte bir tane daha olsa.
**Asistan**: Maalesef müşteri başına yalnızca bir randevu verebiliyorum, bu yüzden arkadaşınız için ikinci bir randevu oluşturamıyorum. Cuma günkü teslimatınız ise yerinde duruyor. Başka bir sorunuz var mı?
**Müşteri**: Tamam, anlıyorum, sorun değil. Başka bir sorum yok, teşekkür ederim.
    `tool`: close_call({"outcome": "booked", "note": "Cuma 09:00-13:00 Ev teslimat randevusu yazıldı. İkinci randevu talebi reddedildi."}) -> 200 {"call_id": 1, "outcome": "booked", "callback": false}
**Asistan**: Rica ederim Selin Hanım, iyi günler dilerim.

## tool_log

- confirm_name → 200
- verify_dob → 200
- list_slots → 200
- book_appointment → 201
- close_call → 200

randevu: {'slot_id': 4, 'district': 'Şişli', 'day': 'Cuma', 'time_range': '09:00-13:00', 'remaining': 1} · callback: []

## Kontroller

- r2: na Telefonu müşteri Selin Aydın açtı.
- r9: na Müşteri adres ya da ilçe değişikliği istemedi.
