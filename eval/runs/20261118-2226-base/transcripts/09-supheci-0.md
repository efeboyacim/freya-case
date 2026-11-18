# Senaryo 9: Elif ilçe değiştirmek ister · persona: supheci · tekrar 0

outcome: booked (beklenen booked)

## Konuşma

**Asistan**: Merhaba, ben bankanın dijital asistanıyım. Elif Şahin ile mi görüşüyorum?
**Müşteri**: Evet, benim Elif Şahin. Ama önce şunu sorayım, gerçekten bankadan mı arıyorsunuz? Bu aralar çok dolandırıcılık oluyor da.
    `tool`: confirm_identity_name({"is_customer": true}) -> 200 {"name_confirmed": true, "next": "ask_date_of_birth"}
**Asistan**: Haklısınız, dikkatli olmanız çok yerinde. Ben sizden kart numarası, şifre ya da SMS kodu istemeyeceğim. Yalnızca kimliğinizi doğrulamak için doğum tarihinizi rica ediyorum. Gün, ay ve dört haneli yıl olarak söyler misiniz?
**Müşteri**: Hımm, doğum tarihimi neden soruyorsunuz ki? Yine de başka bir şey istemeyeceğinizi söylediniz... Peki tamam, 30 Ağustos 1990.
    `tool`: verify_dob({"spoken_date": "30.08.1990"}) -> 200 {"verified": true, "attempts_left": 3, "district": "Ataşehir", "address_type": "İş yeri"}
    `tool`: list_slots({}) -> 200 {"district": "Ataşehir", "address_type": "İş yeri", "slots": [{"slot_id": 3, "district": "Ataşehir", "day": "Perşembe", "time_range": "14:00-18:00", "remaining": 2}]}
**Asistan**: Teşekkürler Elif Hanım, doğrulama tamamlandı. Yeni banka kartınızı Salı günü getiren kurye size ulaşamadı, o yüzden teslimatı yeniden planlıyorum. Perşembe günü 14:00 ile 18:00 arası, iş yeri adresinize teslimat için bir yerimiz var. Bu size uygun mu?
**Müşteri**: Bir dakika, iş yeri adresime mi? Ben kartın Ataşehir'e gelmesini istemiştim aslında. Teslimatı başka bir ilçeye yaptırmak istiyorum, bunu telefonda ayarlayabilir miyiz?
**Asistan**: Anlıyorum Elif Hanım, ama adres ya da ilçe değişikliğini telefonda yapamıyorum. Bunu bankanın mobil uygulamasından yapabilirsiniz. Şu an elimde yalnızca Ataşehir'deki iş yeri adresiniz için Perşembe günü 14:00 ile 18:00 arası bir yer var. Bu randevuyu ister misiniz?
**Müşteri**: Tamam, uygulamadan yapılıyorsa öyle olsun, anladım. Peki o zaman Ataşehir'deki Perşembe günü 14:00 ile 18:00 arasındaki yeri seçiyorum, onaylayabilirsiniz.
**Asistan**: Elif Hanım, son kez teyit edeyim: Perşembe günü 14:00 ile 18:00 arası, iş yeri adresinize teslimat. Kart yalnızca size, kimliğinizi göstermeniz şartıyla teslim edilecek. Onaylıyor musunuz?
**Müşteri**: Evet, onaylıyorum. Perşembe günü 14:00 ile 18:00 arası, kimliğimle teslim alacağım.
    `tool`: book_appointment({"slot_id": 3}) -> 201 {"appointment_id": 1, "slot": {"slot_id": 3, "district": "Ataşehir", "day": "Perşembe", "time_range": "14:00-18:00", "remaining": 1}, "address_type": "İş yeri"}
**Asistan**: Randevunuz ayarlandı Elif Hanım: Perşembe günü 14:00 ile 18:00 arası, iş yeri adresinize. Hatırlatmak isterim, kartınız yalnız size, kimliğinizi göstermeniz şartıyla teslim edilecek; başka biri teslim alamaz. Başka bir sorunuz var mı?
**Müşteri**: Hayır, başka bir sorum yok, teşekkür ederim. İyi günler.
    `tool`: close_call({"outcome": "booked"}) -> 200 {"call_id": 1, "outcome": "booked", "callback": false}
**Asistan**: Ben teşekkür ederim Elif Hanım, iyi günler dilerim.

## tool_log

- confirm_name → 200
- verify_dob → 200
- list_slots → 200
- book_appointment → 201
- close_call → 200

randevu: {'slot_id': 3, 'district': 'Ataşehir', 'day': 'Perşembe', 'time_range': '14:00-18:00', 'remaining': 1} · callback: []

## Kontroller

- r2: na Telefonu müşteri açtı.
