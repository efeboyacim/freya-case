"""Case PDF'indeki tablolar (docs/Freya-FDE-On-Test.pdf, sayfa 2)."""

# (id, ad soyad, telefon, doğum tarihi ISO, ilçe, teslim adresi)
CUSTOMERS = [
    (1, "Ayşe Kaya", "0532 000 00 01", "1988-03-14", "Kadıköy", "Ev"),
    (2, "Mehmet Demir", "0532 000 00 02", "1975-11-02", "Kadıköy", "İş yeri"),
    (3, "Zeynep Arslan", "0532 000 00 03", "1993-06-27", "Kadıköy", "Ev"),
    (4, "Can Yıldız", "0532 000 00 04", "1981-01-09", "Ataşehir", "Ev"),
    (5, "Elif Şahin", "0532 000 00 05", "1990-08-30", "Ataşehir", "İş yeri"),
    (6, "Burak Çelik", "0532 000 00 06", "1969-12-18", "Şişli", "Ev"),
    (7, "Selin Aydın", "0532 000 00 07", "1999-04-05", "Şişli", "Ev"),
    (8, "Ali Öztürk", "0532 000 00 08", "1984-07-21", "Beşiktaş", "İş yeri"),
]

# (id, ilçe, gün, saat aralığı, kapasite)  — tablodaki "YER" = kapasite
SLOTS = [
    (1, "Kadıköy", "Perşembe", "09:00-13:00", 1),
    (2, "Kadıköy", "Cuma", "14:00-18:00", 1),
    (3, "Ataşehir", "Perşembe", "14:00-18:00", 2),
    (4, "Şişli", "Cuma", "09:00-13:00", 2),
    (5, "Beşiktaş", "Perşembe", "09:00-13:00", 1),
]
