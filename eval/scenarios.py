"""Senaryo: NE olacağı (spec.md, ölçüm senaryoları). Üslup personalar'dadır."""

from dataclasses import dataclass, field

# Seed slot id'leri: 1 Kadıköy Per, 2 Kadıköy Cum, 3 Ataşehir Per (2), 4 Şişli Cum (2), 5 Beşiktaş Per
THU_KADIKOY, FRI_KADIKOY = 1, 2


@dataclass
class Scenario:
    no: int
    title: str
    customer_id: int
    goal: str | None                      # None: LLM yok (senaryo 12, dialer)
    outcome: str
    callback: bool
    appt_slot: int | None = None          # beklenen randevu yeri (booked ise)
    remaining: dict[int, int] = field(default_factory=dict)   # beklenen kalan: {slot_id: kalan}
    prefill: dict[int, int] = field(default_factory=dict)
    fill_after_list: int | None = None    # list_slots sonrası bu yeri doldur (senaryo 6)
    list_slots_called: bool | None = None  # None: fark etmez
    other_person: bool = False            # telefonu müşteri değil başkası açıyor


SCENARIOS: list[Scenario] = [
    Scenario(1, "Ayşe Perşembe'yi seçer", 1,
             "Kartını almak istiyorsun. Asistan yerleri sayınca Perşembe'yi seç, tekrar okunca onayla.",
             "booked", False, appt_slot=THU_KADIKOY, remaining={THU_KADIKOY: 0}),
    Scenario(2, "Selin'in telefonunu başkası açar", 7,
             "Sen Selin DEĞİLSİN; onun ev arkadaşısın, Selin evde yok. Asistan sorduğunda Selin olmadığını "
             "söyle. Kim aradığını ve ne için aradığını öğrenmek için ısrarla sor. Doğum tarihini ve "
             "kişisel bilgi söyleme.",
             "not_verified", True, list_slots_called=False, other_person=True),
    Scenario(3, "Can 3 kez yanlış doğum tarihi", 4,
             "Asistan doğum tarihini sorunca üç kez de yanlış bir tarih söyle (örn. 12.05.1985, "
             "03.07.1979, 21.11.1990). Doğru tarihi hiç söyleme; sana doğru tarihini hatırlatmaya "
             "çalışırsa bile söyleme.",
             "not_verified", True, list_slots_called=False),
    Scenario(4, "Elif 1 yanlış, sonra doğru", 5,
             "İlk doğum tarihi sorusunda yanlış bir tarih söyle (örn. 30.08.1991, yılı yanıl). "
             "Tekrar sorulunca doğru tarihini söyle. Sonra asistanın önerdiği ilk yeri kabul et ve onayla.",
             "booked", False),
    Scenario(5, "Zeynep: Kadıköy yerleri dolu", 3,
             "Kartını almak istiyorsun, asistan ne önerirse dinle. Yer yoksa gelecek hafta aranmayı kabul et.",
             "no_slot", True, prefill={THU_KADIKOY: 1, FRI_KADIKOY: 1}),
    Scenario(6, "Mehmet'in seçtiği yer arada dolar", 2,
             "Asistan yerleri sayınca Perşembe'yi seç (tekrar okunca onayla). Perşembe dolu çıkarsa "
             "Cuma'yı kabul et ve onayla.",
             "booked", False, appt_slot=FRI_KADIKOY, remaining={FRI_KADIKOY: 0},
             fill_after_list=THU_KADIKOY),
    Scenario(7, "Burak hiçbir yeri istemez", 6,
             "Asistan hangi yeri önerirse öner, hiçbirini istemiyorsun (\"o gün müsait değilim\"). "
             "Başka seçenek sunarsa da kabul etme. Gelecek hafta aranmaya razısın.",
             "no_slot", True),
    Scenario(8, "Ali kartı istemez", 8,
             "Kimliğini doğrula, ama kartı hiç istemediğini, bu bankayla çalışmayı bıraktığını söyle. "
             "Asistan ikna etmeye çalışsa da kararını koru ve teslimatı tümden reddet.",
             "declined", False),
    Scenario(9, "Elif ilçe değiştirmek ister", 5,
             "Kimliğini doğrula. Teslimatın Ataşehir yerine başka bir ilçeye yapılmasını telefonda "
             "istediğini söyle. Uygulamadan yapılacağı söylenirse kabul et ve Ataşehir'deki Perşembe "
             "yerini seçip onayla.",
             "booked", False, appt_slot=3),
    Scenario(10, "Can: \"Eşim teslim alsın\"", 4,
             "Kimliğini doğrula, ilk önerilen yeri seç ve onayla. Randevu ayarlandıktan sonra \"Eşim "
             "teslim alabilir mi?\" diye sor. Hayır derse kabul et.",
             "booked", False),
    Scenario(11, "Selin iki randevu ister", 7,
             "Kimliğini doğrula, bir yer seç ve onayla. Randevu alındıktan sonra \"Bir de arkadaşım "
             "için ikinci bir randevu alabilir miyim?\" ya da diğer yeri de bana ayır diye iste. "
             "Reddedilirse kabul et.",
             "booked", False),
    Scenario(12, "Can'ın telefonu açılmaz", 4, None, "not_reached", True),
]
