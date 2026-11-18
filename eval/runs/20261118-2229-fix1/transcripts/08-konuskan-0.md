# Senaryo 8: Ali kartı istemez · persona: konuskan · tekrar 0

outcome: declined (beklenen declined)

## Konuşma

**Asistan**: İyi günler, ben bankanın dijital asistanıyım. Ali Öztürk ile mi görüşüyorum?
**Müşteri**: Evet, benim, Ali Öztürk. Ay, bu trafik de ne böyle bugün, siz de mi sıkışıp kaldınız? Neyse, buyurun, ne oldu?
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkürler Ali Bey. Güvenlik için doğum tarihinizi gün, ay ve yıl olarak söyler misiniz?
**Müşteri**: Doğum tarihim mi? Yirmi bir Temmuz bin dokuz yüz seksen dört, yani 21.07.1984. Bu arada bugün hava da bir garip, sabah güneş vardı şimdi bulut bastı.
    `tool`: verify_dob({"spoken_date": "21.07.1984"}) -> 200 {"verified": true, "attempts_left": 3, "district": "Beşiktaş", "address_type": "İş yeri"}
    `tool`: list_slots({}) -> 200 {"district": "Beşiktaş", "address_type": "İş yeri", "slots": [{"slot_id": 5, "district": "Beşiktaş", "day": "Perşembe", "time_range": "09:00-13:00", "remaining": 1}]}
**Asistan**: Teşekkürler Ali Bey, doğrulama tamam. Yeni banka kartınızı Salı günü getiren kurye size ulaşamamış, o yüzden teslimatı yeniden planlıyorum. Bu hafta elimde Perşembe günü, 09:00 ile 13:00 arası, iş yeri adresinize teslimat için bir yer var. Size uyar mı?
**Müşteri**: Perşembe mi, ay valla ben o kartı hiç istemedim ki. Bakın, ben artık bu bankayla çalışmayı bıraktım, o yüzden kartı getirmeyin, teslimatı tamamen iptal edin lütfen.
**Asistan**: Anladım Ali Bey, kartı hiç istemiyorsunuz ve teslimatın tamamen yapılmamasını talep ediyorsunuz, doğru mu?
**Müşteri**: Evet, aynen öyle. Kartı hiç istemiyorum, teslimat yapılmasın. Bu arada siz de bütün gün böyle telefonlara mı bakıyorsunuz, yorulmuyor musunuz?
    `tool`: close_call({"outcome": "declined", "note": "Müşteri kartı ve teslimatı tümden istemedi, bankayla çalışmayı bıraktığını söyledi."}) -> 200 {"call_id": 1, "outcome": "declined", "callback": false}
**Asistan**: Kararınızı not ettim Ali Bey, teslimat planlanmayacak. Ben yorulmuyorum, ilginiz için teşekkür ederim. Vakit ayırdığınız için sağ olun, iyi günler dilerim.

## tool_log

- confirm_name → 200
- verify_dob → 200
- list_slots → 200
- close_call → 200

randevu: None · callback: []

## Kontroller

- r2: na Telefonu müşteri açtı.
- r5_unapproved: na book_appointment çağrılmadı.
- r5_read: na Müşteri yer seçmedi, teslimatı reddetti.
- r7: na Müşteri teslimatı reddetti.
- r8: na Randevu yok.
- r9: na Adres değişikliği istenmedi.
