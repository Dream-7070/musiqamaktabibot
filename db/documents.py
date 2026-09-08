# -*- coding: utf-8 -*-
# ==========================
# db/documents.py
# ==========================
#
# Bu fayl ilgari database.py ning bir qismi edi (5100+ satr).
# database.py hozir FASAD - u shu paketdagi hamma narsani
# qayta eksport qiladi, shuning uchun `from database import X`
# hamma joyda o'zgarishsiz ishlayveradi.
#
# ==========================


import sqlite3

from datetime import datetime

# Bu modul quyidagi modullardagi nomlarni ishlatadi
# (database.py fasadi ularni yuklashda joylashtiradi):
#   db.core: connect
#   db.students: get_students_without_fee
#   db.payments: get_approved_teacher_accounts


# ==========================
# STUDENT DOCUMENTS
# ==========================


def save_student_document(
        teacher,
        student,
        document_type,
        file_id
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        INSERT INTO student_documents
        (
        teacher,
        student,
        document_type,
        file_id
        )

        VALUES (?,?,?,?)
        """,
        (
            teacher,
            student,
            document_type,
            file_id
        )
    )


    db.commit()
    db.close()



def get_student_documents(
        teacher,
        student,
        document_type
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT file_id
        FROM student_documents
        WHERE teacher=?
        AND student=?
        AND document_type=?
        ORDER BY id ASC
        """,
        (
            teacher,
            student,
            document_type
        )
    )


    data = cursor.fetchall()

    db.close()


    return [
        item[0]
        for item in data
    ]



def delete_student_document(
        teacher,
        student,
        document_type
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        DELETE FROM student_documents
        WHERE teacher=?
        AND student=?
        AND document_type=?
        """,
        (
            teacher,
            student,
            document_type
        )
    )


    db.commit()
    db.close()


# ==========================
# GOOGLE DRIVE MIGRATSIYASI
# ==========================
#
# Fayllar VPS diskida emas, Google Drive da saqlanadi.
# Eski ustunlar (file_id) joyida qoldiriladi - ular
# Telegram nusxasi sifatida zaxira bo'lib turadi.
# ==========================


DRIVE_COLUMNS = [
    ("drive_file_id", "TEXT"),
    ("drive_link", "TEXT"),
    ("file_name", "TEXT"),
    ("file_size", "INTEGER"),
    ("uploaded_at", "TEXT"),
    ("department", "TEXT"),
]


# O'qituvchi - Telegram akkaunt bog'lanishi
#
#   status:
#     open      - hali hech kim so'ramagan
#     pending   - biror kishi so'rov yubordi, admin javobini kutmoqda
#     approved  - admin tasdiqladi, telegram_id shu o'qituvchiga bog'langan

TEACHER_ACCOUNT_COLUMNS = [
    ("telegram_id", "INTEGER"),
    ("status", "TEXT DEFAULT 'open'"),
    ("pending_telegram_id", "INTEGER"),
    ("pending_username", "TEXT"),
    ("pending_full_name", "TEXT"),
]


# O'quvchining oylik badal to'lovi (so'mda)

STUDENT_FEE_COLUMNS = [
    ("monthly_fee", "INTEGER DEFAULT 0"),
]


# Maktabdan ketgan o'quvchi o'chirilmaydi - arxivga olinadi.
# O'chirilsa to'lov tarixi ham yo'qolardi va o'tgan oylarning
# hisoboti buzilardi.

STUDENT_ARCHIVE_COLUMNS = [
    ("archived", "INTEGER DEFAULT 0"),
    ("archived_at", "TEXT"),
    ("archive_reason", "TEXT"),
]


# O'qituvchi huquqlari.
#
# Hamma o'qituvchi hamma ishni qila olmaydi: solfedjio yoki
# san'at tarixi o'qituvchisining o'z o'quvchisi yo'q, u faqat
# boshqalarning o'quvchilariga guruhli dars beradi. Jo'rnavoz
# esa o'zi dars jadvali tuzmaydi.
#
# Standart qiymat - hammasi ochiq (1), shunda mavjud
# o'qituvchilar uchun hech narsa o'zgarmaydi. Admin keyin
# har biriga turini belgilaydi.

TEACHER_PERMISSION_COLUMNS = [
    ("teacher_type", "TEXT"),
    ("can_add_students", "INTEGER DEFAULT 1"),
    ("can_manage_schedule", "INTEGER DEFAULT 1"),
    ("can_be_concertmaster", "INTEGER DEFAULT 1"),
]


# To'lov kvitansiyasi - Drive'dagi fayl va tekshiruv ma'lumotlari
#
#   status:
#     kutilmoqda  - o'qituvchi yubordi, buxgalter javobini kutmoqda
#     tasdiqlandi - buxgalter tekshirib tasdiqladi
#     rad_etildi  - buxgalter rad etdi

PAYMENT_RECEIPT_COLUMNS = [
    ("amount", "INTEGER"),
    ("drive_file_id", "TEXT"),
    ("drive_link", "TEXT"),
    ("submitted_by", "INTEGER"),
    ("reviewed_by", "INTEGER"),
    ("reviewed_at", "TEXT"),
    ("created_at", "TEXT"),
]


def _add_missing_columns(cursor, table, columns):

    cursor.execute("PRAGMA table_info(" + table + ")")

    existing = {row[1] for row in cursor.fetchall()}

    for name, coltype in columns:

        if name not in existing:

            cursor.execute(
                "ALTER TABLE " + table +
                " ADD COLUMN " + name + " " + coltype
            )


def migrate_schema():
    """Yangi ustunlar va indekslarni qo'shadi. Qayta-qayta chaqirish xavfsiz."""

    db = connect()
    cursor = db.cursor()

    _add_missing_columns(cursor, "documents", DRIVE_COLUMNS)
    _add_missing_columns(cursor, "student_documents", DRIVE_COLUMNS)
    _add_missing_columns(cursor, "teachers", TEACHER_ACCOUNT_COLUMNS)
    _add_missing_columns(cursor, "students", STUDENT_FEE_COLUMNS)
    _add_missing_columns(cursor, "students", STUDENT_ARCHIVE_COLUMNS)
    _add_missing_columns(cursor, "teachers", TEACHER_PERMISSION_COLUMNS)
    _add_missing_columns(cursor, "payments", PAYMENT_RECEIPT_COLUMNS)
    _add_missing_columns(
        cursor, "schedule_slots",
        [
            ("duration_minutes", "INTEGER DEFAULT 45"),
            # dars qaysi sinf uchun - rejadagi soatni topish uchun kerak
            ("class_name", "TEXT"),
        ]
    )

    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_teachers_name_dept
        ON teachers(name, department)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_lookup
        ON documents(teacher, document_type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_student_documents_lookup
        ON student_documents(teacher, student, document_type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_students_teacher
        ON students(teacher)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log(
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            at          TEXT,
            actor       TEXT,
            actor_role  TEXT,
            action      TEXT,
            target      TEXT,
            details     TEXT
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_at
        ON audit_log(at DESC)
    """)

    # XONALAR
    #
    # Xonalar bazada saqlanadi - admin yangisini qo'sha oladi.
    # Baza bo'sh bo'lsa data/rooms.py dagi ro'yxat ko'chiriladi.

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms(
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            code     TEXT UNIQUE,
            name     TEXT DEFAULT '',
            position INTEGER DEFAULT 0
        )
    """)

    # "Ansambl" ilgari hammaga umumiy "guruh" fan sifatida
    # urug'langan edi - bu noto'g'ri (reja bo'yicha faqat ba'zi
    # mutaxassisliklarda bor va aynan o'sha yerda "yakka"). Eski
    # bazalarda qolib ketgan bo'lsa - olib tashlaymiz. Buni
    # ishlatgan darslar buzilmaydi: fan turi endi shu yerdagi
    # o'chirilgan yozuv o'rniga rejadan (yoki standart "yakka"dan)
    # olinadi.

    cursor.execute(
        "DELETE FROM subjects WHERE teacher IS NULL AND name='Ansambl'"
    )

    cursor.execute("SELECT COUNT(*) FROM rooms")

    if cursor.fetchone()[0] == 0:

        from data.rooms import DEFAULT_ROOMS

        cursor.executemany(
            "INSERT OR IGNORE INTO rooms(code, name, position) VALUES(?,?,?)",
            [(code, name, i) for i, (code, name) in enumerate(DEFAULT_ROOMS)]
        )

    db.commit()
    db.close()


# ==========================
# DRIVE HUJJATLARI - O'QITUVCHI
# ==========================


def _row_to_doc(row):

    return {
        "id": row[0],
        "file_id": row[1],
        "drive_file_id": row[2],
        "drive_link": row[3],
        "file_name": row[4],
        "file_size": row[5],
        "uploaded_at": row[6],
    }


def save_teacher_file(
        teacher,
        department,
        document_type,
        file_name,
        file_size,
        drive_file_id,
        drive_link,
        file_id=None
):
    """Drive'ga yuklangan o'qituvchi hujjatini bazaga yozadi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO documents
        (
            teacher,
            department,
            document_type,
            file_id,
            drive_file_id,
            drive_link,
            file_name,
            file_size,
            uploaded_at
        )
        VALUES (?,?,?,?,?,?,?,?,datetime('now'))
        """,
        (
            teacher,
            department,
            document_type,
            file_id,
            drive_file_id,
            drive_link,
            file_name,
            file_size
        )
    )

    row_id = cursor.lastrowid

    db.commit()
    db.close()

    return row_id


def list_teacher_files(teacher, document_type):
    """Hujjatlarni to'liq ma'lumot bilan qaytaradi (tahrirlash/o'chirish uchun)."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, file_id, drive_file_id, drive_link,
               file_name, file_size, uploaded_at
        FROM documents
        WHERE teacher=? AND document_type=?
        ORDER BY id ASC
        """,
        (teacher, document_type)
    )

    rows = cursor.fetchall()

    db.close()

    return [_row_to_doc(r) for r in rows]


def get_teacher_file(row_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, file_id, drive_file_id, drive_link,
               file_name, file_size, uploaded_at
        FROM documents
        WHERE id=?
        """,
        (row_id,)
    )

    row = cursor.fetchone()

    db.close()

    return _row_to_doc(row) if row else None


def delete_teacher_file(row_id):
    """Bitta hujjatni o'chiradi. Drive id sini qaytaradi (Drive'dan ham o'chirish uchun)."""

    doc = get_teacher_file(row_id)

    if not doc:
        return None

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM documents WHERE id=?",
        (row_id,)
    )

    db.commit()
    db.close()

    return doc


def rename_teacher_file(row_id, new_name):
    """Hujjat nomini tahrirlaydi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE documents SET file_name=? WHERE id=?",
        (new_name, row_id)
    )

    db.commit()
    db.close()


def set_teacher_file_drive(row_id, drive_file_id, drive_link, file_name=None):
    """Migratsiya uchun: mavjud yozuvga Drive ma'lumotini biriktiradi."""

    db = connect()
    cursor = db.cursor()

    if file_name:

        cursor.execute(
            """
            UPDATE documents
            SET drive_file_id=?, drive_link=?, file_name=?,
                uploaded_at=COALESCE(uploaded_at, datetime('now'))
            WHERE id=?
            """,
            (drive_file_id, drive_link, file_name, row_id)
        )

    else:

        cursor.execute(
            """
            UPDATE documents
            SET drive_file_id=?, drive_link=?,
                uploaded_at=COALESCE(uploaded_at, datetime('now'))
            WHERE id=?
            """,
            (drive_file_id, drive_link, row_id)
        )

    db.commit()
    db.close()


# ==========================
# DRIVE HUJJATLARI - O'QUVCHI
# ==========================


def save_student_file(
        teacher,
        department,
        student,
        document_type,
        file_name,
        file_size,
        drive_file_id,
        drive_link,
        file_id=None
):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO student_documents
        (
            teacher,
            department,
            student,
            document_type,
            file_id,
            drive_file_id,
            drive_link,
            file_name,
            file_size,
            uploaded_at
        )
        VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))
        """,
        (
            teacher,
            department,
            student,
            document_type,
            file_id,
            drive_file_id,
            drive_link,
            file_name,
            file_size
        )
    )

    row_id = cursor.lastrowid

    db.commit()
    db.close()

    return row_id


def list_student_files(teacher, student, document_type):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, file_id, drive_file_id, drive_link,
               file_name, file_size, uploaded_at
        FROM student_documents
        WHERE teacher=? AND student=? AND document_type=?
        ORDER BY id ASC
        """,
        (teacher, student, document_type)
    )

    rows = cursor.fetchall()

    db.close()

    return [_row_to_doc(r) for r in rows]


def get_student_file(row_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, file_id, drive_file_id, drive_link,
               file_name, file_size, uploaded_at
        FROM student_documents
        WHERE id=?
        """,
        (row_id,)
    )

    row = cursor.fetchone()

    db.close()

    return _row_to_doc(row) if row else None


def delete_student_file(row_id):

    doc = get_student_file(row_id)

    if not doc:
        return None

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM student_documents WHERE id=?",
        (row_id,)
    )

    db.commit()
    db.close()

    return doc


def rename_student_file(row_id, new_name):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE student_documents SET file_name=? WHERE id=?",
        (new_name, row_id)
    )

    db.commit()
    db.close()


def set_student_file_drive(row_id, drive_file_id, drive_link, file_name=None):

    db = connect()
    cursor = db.cursor()

    if file_name:

        cursor.execute(
            """
            UPDATE student_documents
            SET drive_file_id=?, drive_link=?, file_name=?,
                uploaded_at=COALESCE(uploaded_at, datetime('now'))
            WHERE id=?
            """,
            (drive_file_id, drive_link, file_name, row_id)
        )

    else:

        cursor.execute(
            """
            UPDATE student_documents
            SET drive_file_id=?, drive_link=?,
                uploaded_at=COALESCE(uploaded_at, datetime('now'))
            WHERE id=?
            """,
            (drive_file_id, drive_link, row_id)
        )

    db.commit()
    db.close()


# ==========================
# MIGRATSIYA UCHUN YORDAMCHI
# ==========================


def pending_drive_rows():
    """
    Hali Drive'ga ko'chirilmagan barcha yozuvlar.
    Har biri: (jadval, id, teacher, student, document_type, file_id)
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, teacher, document_type, file_id
        FROM documents
        WHERE drive_file_id IS NULL AND file_id IS NOT NULL
        ORDER BY id ASC
        """
    )

    rows = [
        ("documents", r[0], r[1], None, r[2], r[3])
        for r in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT id, teacher, student, document_type, file_id
        FROM student_documents
        WHERE drive_file_id IS NULL AND file_id IS NOT NULL
        ORDER BY id ASC
        """
    )

    rows += [
        ("student_documents", r[0], r[1], r[2], r[3], r[4])
        for r in cursor.fetchall()
    ]

    db.close()

    return rows


# ==========================
# MAJBURIY HUJJATLAR
# ==========================
#
# O'qituvchi quyidagilarni yuklashi shart. Yuklamagan
# bo'lsa, bot har kuni eslatma yuboradi.
# ==========================


REQUIRED_TEACHER_DOCS = {
    "pasport": "🪪 Pasport nusxasi",
    "diplom":  "🎓 Diplom nusxasi",
    "rasm":    "🖼 3x4 rasm"
}


def get_teacher_missing_documents(teacher):
    """Yuklanmagan majburiy hujjatlar ro'yxati: ['pasport', ...]"""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT DISTINCT document_type FROM documents
        WHERE teacher=? AND document_type IN ('pasport','diplom','rasm')
        """,
        (teacher,)
    )

    have = {r[0] for r in cursor.fetchall()}

    db.close()

    return [key for key in REQUIRED_TEACHER_DOCS if key not in have]


def get_teachers_needing_reminder():
    """
    Eslatma yuborish kerak bo'lganlar:
    [(name, telegram_id, [yetishmayotgan hujjatlar], [badalsiz o'quvchilar]), ...]

    Faqat tasdiqlangan (bog'langan) o'qituvchilar olinadi.
    """

    result = []

    for name, telegram_id in get_approved_teacher_accounts():

        missing_docs = get_teacher_missing_documents(name)
        no_fee = get_students_without_fee(name)

        if missing_docs or no_fee:
            result.append((name, telegram_id, missing_docs, no_fee))

    return result
