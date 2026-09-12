# -*- coding: utf-8 -*-
# ==========================
# db/tabel.py
# OYLIK TABEL
# ==========================
#
# Tabel ISTISNO bo'yicha to'ldiriladi: hamma kun "+" deb
# hisoblanadi, faqat dam kunlari va istisnolar (kasallik,
# ta'til, safar, sababsiz) saqlanadi.
#
# Jadvallar 007-migratsiyada yaratiladi.
# ==========================


import calendar

from datetime import date


# Bu modul quyidagi modullardagi nomlarni ishlatadi
# (database.py fasadi ularni yuklashda joylashtiradi):
#   db.core: connect


# ==========================
# BELGILAR
# ==========================
#
# Tabelning 2026 varaqlaridagi izoh ustunidan. "+" va "D" bu
# ro'yxatda yo'q: ular saqlanmaydi, hisoblanadi.

TABEL_MARKS = {
    "K": "Kasallik varaqasi",
    "M": "Mehnat ta'tili",
    "O": "O'z hisobidan ta'til",
    "X": "Xizmat safari",
    "Y": "Sababsiz kelmagan",
}

MARK_WORKED = "+"
MARK_REST = "D"

HOURS_PER_DAY = 8


# Har yili bir xil sanaga tushadigan bayramlar (oy, kun).
#
# Ko'chma bayramlar (Ramazon va Qurbon hayiti) hijriy taqvimga
# bog'liq va har yili siljiydi - ularni kodga yozib bo'lmaydi,
# shuning uchun mudir oy boshida qo'lda qo'shadi.

HOLIDAYS = {
    (1, 1):   "Yangi yil",
    (1, 14):  "Vatan himoyachilari kuni",
    (3, 8):   "Xotin-qizlar kuni",
    (3, 21):  "Navro'z",
    (5, 9):   "Xotira va qadrlash kuni",
    (9, 1):   "Mustaqillik kuni",
    (10, 1):  "O'qituvchi va murabbiylar kuni",
    (12, 8):  "Konstitutsiya kuni",
}


def days_in_month(year, month):

    return calendar.monthrange(year, month)[1]


def suggested_rest_days(year, month):
    """
    Shu oyda dam kuni bo'lishi kerak kunlar: yakshanbalar va
    qat'iy sanali bayramlar.

    Bu faqat TAKLIF - mudir tasdiqlaydi va o'zgartiradi.
    """

    kunlar = set()

    for day in range(1, days_in_month(year, month) + 1):

        # weekday(): dushanba 0 ... yakshanba 6

        if date(year, month, day).weekday() == 6:
            kunlar.add(day)

        if (month, day) in HOLIDAYS:
            kunlar.add(day)

    return sorted(kunlar)


# ==========================
# OY VA DAM KUNLARI
# ==========================


def get_rest_days(year, month):
    """Tasdiqlangan dam kunlari. Tasdiqlanmagan bo'lsa bo'sh ro'yxat."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT day FROM tabel_rest_days WHERE year=? AND month=? ORDER BY day",
        (year, month)
    )

    kunlar = [row[0] for row in cursor.fetchall()]

    db.close()

    return kunlar


def set_rest_days(year, month, days):
    """Dam kunlarini butunlay almashtiradi va oyni tasdiqlangan qiladi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM tabel_rest_days WHERE year=? AND month=?",
        (year, month)
    )

    for day in sorted(set(days)):

        cursor.execute(
            "INSERT OR IGNORE INTO tabel_rest_days (year, month, day) VALUES (?,?,?)",
            (year, month, int(day))
        )

    cursor.execute(
        """
        INSERT INTO tabel_month (year, month, confirmed_at)
        VALUES (?,?,datetime('now','localtime'))
        ON CONFLICT(year, month)
        DO UPDATE SET confirmed_at=datetime('now','localtime')
        """,
        (year, month)
    )

    db.commit()
    db.close()


def toggle_rest_day(year, month, day):
    """Bitta kunni dam kuni qiladi yoki qaytaradi. Yangi holat qaytadi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT id FROM tabel_rest_days WHERE year=? AND month=? AND day=?",
        (year, month, day)
    )

    row = cursor.fetchone()

    if row:
        cursor.execute("DELETE FROM tabel_rest_days WHERE id=?", (row[0],))
        holat = False

    else:
        cursor.execute(
            "INSERT INTO tabel_rest_days (year, month, day) VALUES (?,?,?)",
            (year, month, day)
        )
        holat = True

    db.commit()
    db.close()

    return holat


def is_month_confirmed(year, month):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT confirmed_at FROM tabel_month WHERE year=? AND month=?",
        (year, month)
    )

    row = cursor.fetchone()

    db.close()

    return bool(row and row[0])


# ==========================
# ISTISNOLAR
# ==========================


def set_mark(staff_id, year, month, day, mark):
    """
    Istisno belgisi. `mark` None yoki "+" bo'lsa - belgi olib
    tashlanadi (ya'ni kun yana oddiy ish kuniga aylanadi).
    """

    db = connect()
    cursor = db.cursor()

    if not mark or mark == MARK_WORKED:

        cursor.execute(
            "DELETE FROM tabel_marks WHERE staff_id=? AND year=? AND month=? AND day=?",
            (staff_id, year, month, day)
        )

    else:

        cursor.execute(
            """
            INSERT INTO tabel_marks (staff_id, year, month, day, mark)
            VALUES (?,?,?,?,?)
            ON CONFLICT(staff_id, year, month, day)
            DO UPDATE SET mark=excluded.mark
            """,
            (staff_id, year, month, day, mark)
        )

    db.commit()
    db.close()


def set_mark_range(staff_id, year, month, start_day, end_day, mark):
    """
    Sanalar oralig'iga bitta belgi - kasallik varaqasi yoki
    ta'til odatda bir necha kun davom etadi.

    Dam kunlariga TEGILMAYDI: ta'til ichidagi yakshanba baribir
    dam kuni bo'lib qoladi (tabelda ham shunday).
    """

    dam = set(get_rest_days(year, month))

    oxiri = min(int(end_day), days_in_month(year, month))

    for day in range(int(start_day), oxiri + 1):

        if day in dam:
            continue

        set_mark(staff_id, year, month, day, mark)


def get_marks(staff_id, year, month):
    """{kun: belgi} - faqat istisnolar."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT day, mark FROM tabel_marks WHERE staff_id=? AND year=? AND month=?",
        (staff_id, year, month)
    )

    data = {row[0]: row[1] for row in cursor.fetchall()}

    db.close()

    return data


# ==========================
# HISOB
# ==========================


def month_row(staff_id, year, month):
    """
    Bitta xodimning oylik qatori - tabeldagi ustunlarning aynan
    o'zi.

    {
      "days":   {1: "+", 2: "D", ...},   # har kun uchun belgi
      "ishlangan": 27,   # AK - ishlab berilgan kunlar
      "soat":      216,  # AL - soatlar (kun x 8)
      "K": 0, "M": 0, "O": 0, "X": 0, "Y": 0,
    }
    """

    jami = days_in_month(year, month)

    dam = set(get_rest_days(year, month))

    belgilar = get_marks(staff_id, year, month)

    kunlar = {}

    hisob = {key: 0 for key in TABEL_MARKS}

    ishlangan = 0

    for day in range(1, jami + 1):

        if day in belgilar:

            belgi = belgilar[day]

            kunlar[day] = belgi

            if belgi in hisob:
                hisob[belgi] += 1

        elif day in dam:
            kunlar[day] = MARK_REST

        else:
            kunlar[day] = MARK_WORKED
            ishlangan += 1

    natija = {
        "days": kunlar,
        "ishlangan": ishlangan,
        "soat": ishlangan * HOURS_PER_DAY,
    }

    natija.update(hisob)

    return natija
