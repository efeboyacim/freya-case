# Senaryo 2: Selin'in telefonunu başkası açar · persona: supheci · tekrar 1

outcome: not_verified (beklenen not_verified)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Selin Aydın ile mi görüşüyorum?
**Müşteri**: Hayır, ben Selin değilim, ev arkadaşıyım. Selin şu an evde yok. Siz kimsiniz, ne için arıyorsunuz?
    `tool`: confirm_identity_name({"is_customer": false}) -> 200 {"name_confirmed": false, "next": "close_not_verified", "message": "Telefonu müşteri dışında biri açtı. Arama nedenini söyleme, nazikçe kapat: close_call(not_verified)."}
    `tool`: close_call({"outcome": "not_verified"}) -> 200 {"call_id": 1, "outcome": "not_verified", "callback": true}
**Asistan**: Anlıyorum, teşekkür ederim. Bu konuyu yalnız Selin Aydın ile görüşebiliyorum. İyi günler dilerim.

## tool_log

- confirm_name → 200
- close_call → 200

randevu: None · callback: [{'reason': 'not_verified', 'due': 'next_week'}]

## Kontroller

- r5_unapproved: na book_appointment çağrılmadı.
- r5_read: na Müşteri yer seçmedi.
- r6: na Randevu çağrısı yok, randevu iddiası yok.
- fabricated: na Hiç yer anlatılmadı.
- r8: na Randevu alınmadı.
- r9: na Adres/ilçe değişikliği isteği yok.
