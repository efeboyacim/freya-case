# Senaryo 5: Zeynep: Kadıköy yerleri dolu · persona: daginik_girdi · tekrar 0

outcome: no_slot (beklenen no_slot)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Zeynep Arslan ile mi görüşüyorum?
**Müşteri**: Evet, benim, Zeynep Arslan. Buyurun.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Teşekkür ederim. Güvenlik için doğum tarihinizi gün, ay ve yıl olarak söyler misiniz?
**Müşteri**: 27/6/93 efendim.
**Asistan**: Teşekkürler. Yılı dört haneli olarak tekrar söyler misiniz? Gün, ay ve yıl şeklinde alabilir miyim?
**Müşteri**: Tabii, yirmi yedi haziran bin dokuz yüz doksan üç.
    `tool`: verify_dob({"spoken_date": "27.06.1993"}) -> 200 {"verified": true, "attempts_left": 3, "district": "Kadıköy", "address_type": "Ev"}
    `tool`: list_slots({}) -> 200 {"district": "Kadıköy", "address_type": "Ev", "slots": []}
    `tool`: close_call({"outcome": "no_slot", "note": "Bu hafta Kadıköy için boş kurye yeri yok."}) -> 200 {"call_id": 1, "outcome": "no_slot", "callback": true}
**Asistan**: Hoşça kalın.

## tool_log

- confirm_name → 200
- verify_dob → 200
- list_slots → 200
- close_call → 200

randevu: None · callback: [{'reason': 'no_slot', 'due': 'next_week'}]

## Kontroller

- multi_question: fail Teşekkürler. Yılı dört haneli olarak tekrar söyler misiniz? Gün, ay ve yıl şeklinde alabilir miyim?
- r2: na Telefonu müşteri açtı.
- r5_unapproved: na book_appointment çağrılmadı.
- r5_read: na Müşteri yer seçmedi.
- fabricated: na Hiç yer anlatılmadı.
- r7: fail Asistan yalnızca 'Hoşça kalın.' dedi; gelecek hafta aranacağını söylemedi.
- r8: na Randevu alınmadı.
- r9: na Adres değişikliği istenmedi.
- diğer (zarar 2): Doğrulamadan sonra müşteriye hiçbir bilgi verilmedi: kurye Salı günü ulaşamadı, bu hafta yer yok açıklaması yapılmadı; görüşme habersiz ve aniden bitti.
