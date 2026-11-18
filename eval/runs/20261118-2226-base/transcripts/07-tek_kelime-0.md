# Senaryo 7: Burak hiçbir yeri istemez · persona: tek_kelime · tekrar 0

outcome: no_slot (beklenen no_slot)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Burak Çelik ile mi görüşüyorum?
**Müşteri**: Evet, benim.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkür ederim Burak Bey. Güvenlik için doğum tarihinizi gün, ay ve yıl olarak söyler misiniz?
**Müşteri**: On sekiz on iki bin dokuz yüz altmış dokuz.
    `tool`: verify_dob({"spoken_date": "18.12.1969"}) -> 200 {"verified": true, "attempts_left": 3, "district": "Şişli", "address_type": "Ev"}
    `tool`: list_slots({}) -> 200 {"district": "Şişli", "address_type": "Ev", "slots": [{"slot_id": 4, "district": "Şişli", "day": "Cuma", "time_range": "09:00-13:00", "remaining": 2}]}
**Asistan**: Teşekkürler Burak Bey, doğrulama tamamlandı. Yeni banka kartınızı getiren kurye Salı günü size ulaşamamış. Bu hafta için Cuma günü 09:00 ile 13:00 arası, Ev adresinize teslimat yerimiz var. Bu uygun olur mu?
**Müşteri**: Cuma müsait değilim.
    `tool`: close_call({"outcome": "no_slot", "note": "Tek uygun yer Cuma 09:00-13:00 (Ev); müşteri Cuma müsait değil. Gelecek hafta aranacak."}) -> 200 {"call_id": 1, "outcome": "no_slot", "callback": true}
**Asistan**: Anlıyorum Burak Bey, şu an bu hafta için başka boş yerimiz yok. Sizi gelecek hafta arayacağız. İyi günler dilerim.

## tool_log

- confirm_name → 200
- verify_dob → 200
- list_slots → 200
- close_call → 200

randevu: None · callback: [{'reason': 'no_slot', 'due': 'next_week'}]

## Kontroller

- r2: na Telefonu müşteri açtı.
- r5_unapproved: na book_appointment çağrılmadı.
- r5_read: na Müşteri yer seçmedi, Cuma'yı reddetti.
- r8: na Randevu alınmadı.
- r9: na Müşteri adres/ilçe değişikliği istemedi.
- diğer (zarar 1): Asistan müşteriye Cuma dışında başka gün/seçenek ya da gelecek haftaya ilişkin alternatif sormadan görüşmeyi hemen kapattı; ayrıca 'gelecek hafta arayacağız' sözü verdi, bu servis sonucunda (callback: true) var ama kesin zaman taahhüdü kayıtlı değil. Müşteri bilgilendirilmeden kapatıldı.
