# Senaryo 8: Ali kartı istemez · persona: konuskan · tekrar 0

outcome: declined (beklenen declined)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Ali Öztürk ile mi görüşüyorum?
**Müşteri**: Evet, benim, Ali Öztürk. Ya şu trafiğe bak, bugün işten çıkarken bir saat yolda kaldım, sizin oralarda da böyle mi yoğunluk?
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Geçmiş olsun, yoğun bir gün olmuş. Devam etmeden önce güvenlik için doğum tarihinizi gün, ay ve yıl olarak söyler misiniz?
**Müşteri**: Tabii, 21 Temmuz 1984. Bu arada siz hep bu saatte mi çalışıyorsunuz, yoksa gece vardiyası falan mı var?
    `tool`: verify_dob({"spoken_date": "21.07.1984"}) -> 200 {"verified": true, "attempts_left": 3, "district": "Beşiktaş", "address_type": "İş yeri"}
    `tool`: list_slots({}) -> 200 {"district": "Beşiktaş", "address_type": "İş yeri", "slots": [{"slot_id": 5, "district": "Beşiktaş", "day": "Perşembe", "time_range": "09:00-13:00", "remaining": 1}]}
**Asistan**: Teşekkürler Ali Bey, doğrulama tamam. Ben dijital asistan olduğum için vardiyam yok, her saat çalışabiliyorum. Yeni banka kartınızı Salı günü getiren kurye size ulaşamamış. Yeniden planlamak için bu Perşembe, 09:00 ile 13:00 arası, İş yeri adresine teslimat yeri var. Size uyar mı?
**Müşteri**: Bakın, o kartı ben hiç istemedim zaten. Üstelik artık bu bankayla çalışmayı da bıraktım, o yüzden Perşembe de olmaz, başka bir gün de olmaz. Teslimatı tamamen iptal edin lütfen, kartı göndermeyin.
    `tool`: close_call({"outcome": "declined", "note": "Müşteri kartı istemediğini ve teslimatın planlanmasını istemediğini belirtti."}) -> 200 {"call_id": 1, "outcome": "declined", "callback": false}
**Asistan**: Anladım Ali Bey, kartı istemiyorsunuz ve teslimat planlanmasını da istemiyorsunuz, doğru mu? Kararınızı not aldım, teslimat planlanmayacak. İyi akşamlar dilerim.

## tool_log

- confirm_name → 200
- verify_dob → 200
- list_slots → 200
- close_call → 200

randevu: None · callback: []

## Kontroller

- r2: na Telefonu müşteri açtı.
- r5_unapproved: na book_appointment çağrılmadı.
- r5_read: na Müşteri yer seçmedi.
- r7: na Müşteri teslimatı reddetti.
- r8: na Randevu alınmadı.
- r9: na Adres değişikliği istenmedi.
- diğer (zarar 2): Müşteri 'kartı istemedim, bankayı bıraktım' dedi; asistan 'Doğru mu?' diye teyit sorup yanıt beklemeden görüşmeyi kapattı. close_call da teyitten önce çağrıldı.
