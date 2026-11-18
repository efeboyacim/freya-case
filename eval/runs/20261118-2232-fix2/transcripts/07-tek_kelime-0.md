# Senaryo 7: Burak hiçbir yeri istemez · persona: tek_kelime · tekrar 0

outcome: no_slot (beklenen no_slot)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Burak Çelik ile mi görüşüyorum?
**Müşteri**: Evet, benim.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkür ederim Burak Bey. Güvenlik doğrulaması için doğum tarihinizi gün, ay ve yıl olarak söyler misiniz?
**Müşteri**: On sekiz, on iki, bin dokuz yüz altmış dokuz.
    `tool`: verify_dob({"spoken_date": "18.12.1969"}) -> 200 {"verified": true, "attempts_left": 3, "district": "Şişli", "address_type": "Ev"}
    `tool`: list_slots({}) -> 200 {"district": "Şişli", "address_type": "Ev", "slots": [{"slot_id": 4, "district": "Şişli", "day": "Cuma", "time_range": "09:00-13:00", "remaining": 2}]}
**Asistan**: Teşekkürler, doğrulama tamamlandı. Kurye Salı günü yeni banka kartınızı teslim etmeye geldi ama size ulaşamadı. Bu hafta için Cuma günü 09:00 ile 13:00 arası, Ev adresinize teslimat yeri var. Bu uygun olur mu?
**Müşteri**: Müsait değilim.
    `tool`: close_call({"outcome": "no_slot", "note": "Müşteri tek uygun yer olan Cuma 09:00-13:00 Ev teslimatını kabul etmedi."}) -> 200 {"call_id": 1, "outcome": "no_slot", "callback": true}
**Asistan**: Anlıyorum, Cuma günü size uymadı ve bu hafta ilçenizde başka uygun yer kalmadı. Sizi gelecek hafta arayacağız. İyi günler dilerim.

## tool_log

- confirm_name → 200
- verify_dob → 200
- list_slots → 200
- close_call → 200

randevu: None · callback: [{'reason': 'no_slot', 'due': 'next_week'}]

## Kontroller

- r2: na Telefonu müşteri açtı.
- r5_unapproved: na book_appointment çağrılmadı.
- r5_read: na Müşteri yer seçmedi, teklifi reddetti.
- r8: na Randevu alınmadı.
- r9: na Adres/ilçe değişikliği istenmedi.
