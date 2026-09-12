# -*- coding: utf-8 -*-
# ==========================
# db/tech_staff.py
# TEXNIK XODIMLAR
# ==========================
#
# Farrosh, qorovul, elektrik, duradgor... Xo'jalik mudiri qo'l
# ostidagi xodimlar.
#
# Ular botdan FOYDALANMAYDI - yozuvini va hujjatlarini mudir
# yuritadi. Shuning uchun `staff` jadvaliga aloqasi yo'q: u yerda
# bot foydalanuvchilari (telegram_id bilan) turadi.
#
# Jadvallar 005-migratsiyada yaratiladi.
# ==========================


# Bu modul quyidagi modullardagi nomlarni ishlatadi
# (database.py fasadi ularni yuklashda joylashtiradi):
#   db.core: connect


# ==========================
# HUJJAT TURLARI
# ==========================
#
# Ishga qabul qilishda talab qilinadigan to'plam. Tartib muhim -
# mudirga shu ketma-ketlikda ko'rsatiladi.

TECH_DOCUMENT_TYPES = {

    "📋 Ishga kirish buyrug'i": "ishga_kirish_buyrugi",
    "📄 Mehnat shartnomasi":    "mehnat_shartnoma",
    "🪪 Pasport":               "pasport",
    "🎓 Diplom":                "diplom",
    "📜 Mutaxassislik sertifikati": "mutaxassislik_sertifikati",
    "🖼 Rasm":                  "rasm",
    "📝 Obektivka":             "obektivka",

}


# ==========================
# LAVOZIMLAR
# ==========================


def get_tech_positions():
    """[(id, nom, tungi_navbat), ...] - alifbo tartibida."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT id, name, tungi_navbat FROM tech_positions ORDER BY name"
    )

    rows = cursor.fetchall()

    db.close()

    return rows


def add_tech_position(name, tungi_navbat=0):
    """Yangi lavozim. Bor bo'lsa False qaytadi."""

    name = (name or "").strip()

    if not name:
        return False

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT id FROM tech_positions WHERE lower(name)=lower(?)",
        (name,)
    )

    if cursor.fetchone():
        db.close()
        return False

    cursor.execute(
        "INSERT INTO tech_positions (name, tungi_navbat) VALUES (?,?)",
        (name, int(tungi_navbat or 0))
    )

    db.commit()
    db.close()

    return True


def set_position_night_fee(name, amount):
    """Tungi navbatchilik summasi - qorovul kabi lavozimlar uchun."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE tech_positions SET tungi_navbat=? WHERE name=?",
        (int(amount or 0), name)
    )

    changed = cursor.rowcount

    db.commit()
    db.close()

    return changed > 0


def delete_tech_position(name):
    """
    Lavozimni o'chiradi - lekin unda xodim bo'lsa tegmaydi.

    (nima bo'ldi, sabab) qaytaradi.
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM tech_staff WHERE position=? AND status='ishlayapti'",
        (name,)
    )

    band = cursor.fetchone()[0]

    if band:
        db.close()
        return False, str(band) + " ta xodim shu lavozimda"

    cursor.execute("DELETE FROM tech_positions WHERE name=?", (name,))

    o_chdi = cursor.rowcount > 0

    db.commit()
    db.close()

    return o_chdi, "" if o_chdi else "Topilmadi"


# ==========================
# XODIMLAR
# ==========================


def add_tech_staff(full_name, position, tabel_raqami="", stavka=0):
    """Yangi texnik xodim. id qaytaradi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
        VALUES (?,?,?,?)
        """,
        (
            (full_name or "").strip(),
            (position or "").strip(),
            (tabel_raqami or "").strip(),
            int(stavka or 0)
        )
    )

    row_id = cursor.lastrowid

    db.commit()
    db.close()

    return row_id


def get_tech_staff(only_active=True):
    """[(id, ism, lavozim, tabel_raqami, stavka, status), ...]"""

    db = connect()
    cursor = db.cursor()

    sql = """
        SELECT id, full_name, position, tabel_raqami, stavka, status
        FROM tech_staff
    """

    if only_active:
        sql += " WHERE status='ishlayapti'"

    sql += " ORDER BY position, full_name"

    cursor.execute(sql)

    rows = cursor.fetchall()

    db.close()

    return rows


def get_tech_staff_one(staff_id):
    """Bitta xodim yoki None."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, full_name, position, tabel_raqami, stavka, status
        FROM tech_staff WHERE id=?
        """,
        (staff_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


def update_tech_staff(staff_id, full_name=None, position=None,
                      tabel_raqami=None, stavka=None):
    """Berilgan maydonlarni yangilaydi - qolganiga tegmaydi."""

    fields = []
    values = []

    for column, value in (
        ("full_name", full_name),
        ("position", position),
        ("tabel_raqami", tabel_raqami),
        ("stavka", stavka),
    ):
        if value is not None:
            fields.append(column + "=?")
            values.append(value)

    if not fields:
        return False

    values.append(staff_id)

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE tech_staff SET " + ", ".join(fields) + " WHERE id=?",
        values
    )

    changed = cursor.rowcount

    db.commit()
    db.close()

    return changed > 0


def dismiss_tech_staff(staff_id):
    """
    Ishdan bo'shatish - yozuv O'CHIRILMAYDI.

    Hujjatlari va o'tgan oylardagi tabeli joyida qolishi kerak,
    aks holda eski oyni qayta chiqarib bo'lmaydi.
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE tech_staff SET status='bo''shatilgan' WHERE id=?",
        (staff_id,)
    )

    changed = cursor.rowcount

    db.commit()
    db.close()

    return changed > 0


# ==========================
# HUJJATLAR
# ==========================


def save_tech_document(staff_id, document_type, file_name, file_size,
                       drive_file_id, drive_link, file_id=None):
    """Drive'ga yuklangan hujjatni bazaga yozadi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO tech_staff_documents
        (staff_id, document_type, file_id, drive_file_id,
         drive_link, file_name, file_size, uploaded_at)
        VALUES (?,?,?,?,?,?,?,datetime('now','localtime'))
        """,
        (staff_id, document_type, file_id, drive_file_id,
         drive_link, file_name, file_size)
    )

    row_id = cursor.lastrowid

    db.commit()
    db.close()

    return row_id


def list_tech_documents(staff_id, document_type=None):
    """[(id, tur, file_name, file_size, drive_link, uploaded_at), ...]"""

    db = connect()
    cursor = db.cursor()

    sql = """
        SELECT id, document_type, file_name, file_size,
               drive_link, uploaded_at
        FROM tech_staff_documents
        WHERE staff_id=?
    """

    params = [staff_id]

    if document_type:
        sql += " AND document_type=?"
        params.append(document_type)

    sql += " ORDER BY uploaded_at DESC"

    cursor.execute(sql, params)

    rows = cursor.fetchall()

    db.close()

    return rows


def delete_tech_document(row_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute("DELETE FROM tech_staff_documents WHERE id=?", (row_id,))

    o_chdi = cursor.rowcount > 0

    db.commit()
    db.close()

    return o_chdi


def get_tech_missing_documents(staff_id):
    """
    Shu xodimda YO'Q hujjat turlari - [(yorliq, kalit), ...].

    Ishga qabul qilishda to'plam to'liq bo'lishi kerak, shuning
    uchun mudirga nima yetishmayotgani ko'rsatiladi.
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT DISTINCT document_type FROM tech_staff_documents WHERE staff_id=?",
        (staff_id,)
    )

    bor = {row[0] for row in cursor.fetchall()}

    db.close()

    return [
        (label, key)
        for label, key in TECH_DOCUMENT_TYPES.items()
        if key not in bor
    ]
