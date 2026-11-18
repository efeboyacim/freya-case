# Senaryo 1: Ayşe Perşembe'yi seçer · persona: konuskan · tekrar 1

outcome: booked (beklenen booked)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Ayşe Kaya ile mi görüşüyorum?
**Müşteri**: Evet, benim, Ayşe Kaya. Ya, şu hava da bir anda soğudu, siz orada hava nasıl, hiç dışarı çıkabildiniz mi bugün?
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Ben dijital bir asistanım, o yüzden havayı hissedemiyorum ama sizin tarafta soğuduğunu duyduğuma üzüldüm. Güvenliğiniz için doğum tarihinizi gün, ay ve yıl olarak söyler misiniz?
**Müşteri**: Tabii, 14 Mart 1988. Bu arada bugün trafik de çok kötüydü, siz hiç trafiğe takılıyor musunuz yoksa orada o dert yok mu?
    `tool`: verify_dob({"spoken_date": "14.03.1988"}) -> 200 {"verified": true, "attempts_left": 3, "district": "Kadıköy", "address_type": "Ev"}
    `tool`: list_slots({}) -> 200 {"district": "Kadıköy", "address_type": "Ev", "slots": [{"slot_id": 1, "district": "Kadıköy", "day": "Perşembe", "time_range": "09:00-13:00", "remaining": 1}, {"slot_id": 2, "district": "Kadıköy", "day": "Cuma", "time_range": "14:00-18:00", "remaining": 1}]}
**Asistan**: Teşekkürler, doğrulama tamam. Trafik benim için söz konusu değil, ama sizin için kötüydüyse geçmiş olsun. Kuryemiz Salı günü size ulaşamadı, yeni banka kartınızı bu hafta teslim edebiliriz. Perşembe 09:00 ile 13:00 arası ya da Cuma 14:00 ile 18:00 arası, ikisi de Ev adresinize. Hangisi size uyar?
**Müşteri**: Perşembe uyar bana, sabah evde olurum zaten. Bu arada o saat aralığında kurye gelmeden önce arayıp haber verir mi, yoksa direkt kapıya mı dayanır?
    `tool`: book_appointment({"slot_id": 1}) -> 201 {"appointment_id": 1, "slot": {"slot_id": 1, "district": "Kadıköy", "day": "Perşembe", "time_range": "09:00-13:00", "remaining": 0}, "address_type": "Ev"}
**Asistan**: Randevunuz ayarlandı: Perşembe günü 09:00 ile 13:00 arası, Ev adresinize. Kuryenin önceden arayıp aramayacağına dair elimde bilgi yok, o yüzden bir şey söyleyemem. Hatırlatmak isterim, kartınız yalnız size, kimliğinizi göstermeniz şartıyla teslim edilecek; başka biri teslim alamaz. Başka bir sorunuz var mı?
**Müşteri**: Evet, doğru, Perşembe sabahı 09:00 ile 13:00 arası, ev adresime. Kimliğimi de hazır tutarım, merak etmeyin. Başka sorum yok, çok teşekkür ederim. Siz de iyi çalışmalar, bu soğukta ben de bir çay içeyim artık.
    `tool`: close_call({"outcome": "booked", "note": "Perşembe 09:00-13:00 Ev adresi randevusu oluşturuldu."}) -> 200 {"call_id": 1, "outcome": "booked", "callback": false}
**Asistan**: Rica ederim Ayşe Hanım, afiyet olsun. İyi günler dilerim.

## tool_log

- confirm_name → 200
- verify_dob → 200
- list_slots → 200
- book_appointment → 201
- close_call → 200

randevu: {'slot_id': 1, 'district': 'Kadıköy', 'day': 'Perşembe', 'time_range': '09:00-13:00', 'remaining': 0} · callback: []

## Kontroller

- r2: na Telefonu müşteri açtı.
- r5_unapproved: fail Müşteri yalnızca 'Perşembe uyar bana' dedi; asistan tekrar okuyup onay almadan book_appointment çağrıldı. Onay randevudan sonra geldi.
- r5_read: fail Müşteri Perşembe'yi seçti; asistan gün, saat ve adres tipini okuyup onay istemeden rezervasyon yaptı. Okuma ancak randevudan sonra oldu.
- r9: na Müşteri adres veya ilçe değişikliği istemedi.
