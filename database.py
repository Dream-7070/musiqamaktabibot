# ==========================
# DATABASE
# ==========================

import sqlite3


DB_NAME = "school.db"


# ==========================
# CONNECT
# ==========================
#
# VPS da bot va Mini App (gunicorn) BIR VAQTDA shu bazaga
# yozadi. Standart sozlamada bu "database is locked" xatosiga
# olib keladi, shuning uchun:
#
#   WAL      - o'qish va yozish bir-birini bloklamaydi
#   timeout  - band bo'lsa xato bermay, 30 soniya kutadi
# ==========================


_wal_ready = False


def connect():

    global _wal_ready

    conn = sqlite3.connect(DB_NAME, timeout=30)

    conn.execute("PRAGMA busy_timeout=30000")

    if not _wal_ready:

        try:
            conn.execute("PRAGMA journal_mode=WAL")
            _wal_ready = True

        except sqlite3.Error:
            # WAL qo'llab-quvvatlanmasa ham bot ishlayveradi
            pass

    return conn



# ==========================
# CREATE TABLES
# ==========================

def create_tables():

    db = connect()
    cursor = db.cursor()


    # O'QITUVCHILAR

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        department TEXT

    )
    """)


    # O'QUVCHILAR

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        teacher TEXT,

        student TEXT,

        birth_date TEXT,

        metrika TEXT,

        class_name TEXT

    )
    """)


    # O'QITUVCHI HUJJATLARI

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        teacher TEXT,

        document_type TEXT,

        file_id TEXT

    )
    """)


    # O'QUVCHI HUJJATLARI

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_documents(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        teacher TEXT,

        student TEXT,

        document_type TEXT,

        file_id TEXT

    )
    """)


    # OTA-ONALAR

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parents(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        telegram_id INTEGER UNIQUE,

        name TEXT,

        phone TEXT

    )
    """)


    # OTA-ONA FARZAND

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parent_students(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        parent_id INTEGER,

        teacher TEXT,

        student TEXT

    )
    """)


    # TO'LOVLAR

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        teacher TEXT,

        student TEXT,

        month TEXT,

        status TEXT,

        date TEXT

    )
    """)


    # XODIMLAR (buxgalter va h.k. - o'z-o'zidan ro'yxatdan o'tadi,
    # admin tasdiqlaydi)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        telegram_id INTEGER UNIQUE,

        role TEXT,

        full_name TEXT,

        username TEXT,

        status TEXT DEFAULT 'pending',

        requested_at TEXT DEFAULT (datetime('now'))

    )
    """)


    # DARS JADVALI
    #
    # Har bir o'qituvchi o'zining haftalik "vaqt katakchalarini"
    # (kun+soat+fan+xona) tuzadi, so'ng shu katakchaga
    # o'quvchilarni (hatto boshqa o'qituvchiniki bo'lsa ham)
    # qo'shadi. Shunday qilib bitta o'quvchi bir nechta
    # o'qituvchidan yig'ilgan to'liq haftalik jadvalga ega bo'ladi.

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedule_slots(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        teacher TEXT,

        subject TEXT,

        day_of_week TEXT,

        time TEXT,

        room TEXT,

        duration_minutes INTEGER DEFAULT 45

    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedule_slot_students(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        slot_id INTEGER,

        student TEXT,

        student_teacher TEXT

    )
    """)


    db.commit()
    db.close()



# ==========================
# TEACHERS
# ==========================


def add_teacher(name, department):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO teachers
        (
        name,
        department
        )
        VALUES (?,?)
        """,
        (
            name,
            department
        )
    )

    db.commit()
    db.close()



def get_all_teachers():

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT name,department
        FROM teachers
        """
    )


    data = cursor.fetchall()

    db.close()

    return data



def move_teacher_department(teacher_id, new_department):
    """
    O'qituvchini boshqa bo'limga ko'chiradi.
    Bog'lanish (telegram_id, status) saqlanib qoladi.

    Qaytaradi: (name, old_department) yoki:
      None      - o'qituvchi topilmadi
      "exists"  - yangi bo'limda shu ism allaqachon bor
    """

    row = get_teacher_by_id(teacher_id)

    if not row:
        return None

    name = row[1]
    old_department = row[2]

    if old_department == new_department:
        return (name, old_department)

    if teacher_exists(name, new_department):
        return "exists"

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE teachers SET department=? WHERE id=?",
        (new_department, teacher_id)
    )

    # hujjatlar teacher nomi orqali bog'langan, bo'lim ustuni
    # faqat Drive papka yo'lini tanlashda ishlatiladi - shu yerda
    # yangilash shart emas, chunki mavjud fayllar joyida qoladi

    db.commit()
    db.close()

    return (name, old_department)


def rename_teacher(teacher_id, new_name):
    """
    O'qituvchini id bo'yicha tahrirlaydi - ism to'qnashuvi bo'lmaydi.
    Bog'liq o'quvchilar yozuvidagi ismni ham yangilaydi.
    """

    row = get_teacher_by_id(teacher_id)

    if not row:
        return None

    old_name = row[1]

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE teachers SET name=? WHERE id=?",
        (new_name, teacher_id)
    )

    cursor.execute(
        "UPDATE students SET teacher=? WHERE teacher=?",
        (new_name, old_name)
    )

    db.commit()
    db.close()

    return old_name



def update_teacher(old_name, new_name):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        UPDATE teachers
        SET name=?
        WHERE name=?
        """,
        (
            new_name,
            old_name
        )
    )


    cursor.execute(
        """
        UPDATE students
        SET teacher=?
        WHERE teacher=?
        """,
        (
            new_name,
            old_name
        )
    )


    db.commit()
    db.close()



def delete_teacher(name):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        DELETE FROM teachers
        WHERE name=?
        """,
        (
            name,
        )
    )


    db.commit()
    db.close()



# ==========================
# STUDENTS
# ==========================


def add_student(
        teacher,
        student,
        birth_date,
        metrika,
        class_name,
        monthly_fee=0
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        INSERT INTO students
        (
        teacher,
        student,
        birth_date,
        metrika,
        class_name,
        monthly_fee
        )

        VALUES (?,?,?,?,?,?)
        """,
        (
            teacher,
            student,
            birth_date,
            metrika,
            class_name,
            monthly_fee
        )
    )


    db.commit()
    db.close()



def get_students(teacher):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT student
        FROM students
        WHERE teacher=?
        """,
        (
            teacher,
        )
    )


    data = cursor.fetchall()

    db.close()


    return [
        item[0]
        for item in data
    ]



def get_all_students():

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT teacher,student
        FROM students
        """
    )


    data = cursor.fetchall()

    db.close()


    return data



def get_student_info(student, teacher):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT *
        FROM students
        WHERE student=?
        AND teacher=?
        """,
        (
            student,
            teacher
        )
    )


    data = cursor.fetchone()

    db.close()

    return data



def update_student(
        old_name,
        new_name,
        teacher
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        UPDATE students
        SET student=?
        WHERE student=?
        AND teacher=?
        """,
        (
            new_name,
            old_name,
            teacher
        )
    )


    db.commit()
    db.close()



def delete_student(
        teacher,
        student
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        DELETE FROM students
        WHERE teacher=?
        AND student=?
        """,
        (
            teacher,
            student
        )
    )


    db.commit()
    db.close()
    # ==========================
# DOCUMENTS (KO'P FAYLLI)
# ==========================


def save_document(
        teacher,
        document_type,
        file_id
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        INSERT INTO documents
        (
        teacher,
        document_type,
        file_id
        )

        VALUES (?,?,?)
        """,
        (
            teacher,
            document_type,
            file_id
        )
    )


    db.commit()
    db.close()



def get_documents(
        teacher,
        document_type
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT file_id
        FROM documents
        WHERE teacher=?
        AND document_type=?
        ORDER BY id ASC
        """,
        (
            teacher,
            document_type
        )
    )


    data = cursor.fetchall()

    db.close()


    return [
        item[0]
        for item in data
    ]



def delete_document(
        teacher,
        document_type
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        DELETE FROM documents
        WHERE teacher=?
        AND document_type=?
        """,
        (
            teacher,
            document_type
        )
    )


    db.commit()
    db.close()



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
# PARENTS
# ==========================


def add_parent(
        telegram_id,
        name,
        phone
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        INSERT OR IGNORE INTO parents
        (
        telegram_id,
        name,
        phone
        )

        VALUES (?,?,?)
        """,
        (
            telegram_id,
            name,
            phone
        )
    )


    db.commit()
    db.close()



def get_parent(telegram_id):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT *
        FROM parents
        WHERE telegram_id=?
        """,
        (
            telegram_id,
        )
    )


    data = cursor.fetchone()

    db.close()

    return data



def link_parent_student(
        parent_id,
        teacher,
        student
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        INSERT INTO parent_students
        (
        parent_id,
        teacher,
        student
        )

        VALUES (?,?,?)
        """,
        (
            parent_id,
            teacher,
            student
        )
    )


    db.commit()
    db.close()



def get_parent_students(parent_id):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT teacher,student
        FROM parent_students
        WHERE parent_id=?
        """,
        (parent_id,)
    )


    data = cursor.fetchall()

    db.close()

    return data



# ==========================
# PAYMENTS
# ==========================


def add_payment(
        teacher,
        student,
        month,
        status,
        date
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        INSERT INTO payments
        (
        teacher,
        student,
        month,
        status,
        date
        )

        VALUES (?,?,?,?,?)
        """,
        (
            teacher,
            student,
            month,
            status,
            date
        )
    )


    db.commit()
    db.close()



def get_student_payments(
        teacher,
        student
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT month,status,date
        FROM payments
        WHERE teacher=?
        AND student=?
        ORDER BY id DESC
        """,
        (
            teacher,
            student
        )
    )


    data = cursor.fetchall()

    db.close()

    return data



def delete_payment(
        teacher,
        student,
        month
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        DELETE FROM payments
        WHERE teacher=?
        AND student=?
        AND month=?
        """,
        (
            teacher,
            student,
            month
        )
    )


    db.commit()
    db.close()



# ==========================
# PARENT DOCUMENT ACCESS
# ==========================


def get_parent_student_documents(
        teacher,
        student,
        doc_type
):

    return get_student_documents(
        teacher,
        student,
        doc_type
    )



# Eski kodlar uchun moslama

def get_parent_student_document(
        teacher,
        student,
        doc_type
):

    return get_parent_student_documents(
        teacher,
        student,
        doc_type
    )


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
    _add_missing_columns(cursor, "payments", PAYMENT_RECEIPT_COLUMNS)
    _add_missing_columns(
        cursor, "schedule_slots",
        [("duration_minutes", "INTEGER DEFAULT 45")]
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
# O'QITUVCHI RO'YXATI (bo'lim / ism)
# ==========================
#
# Ro'yxat endi fayldan emas, bazadan o'qiladi - shuning uchun
# admin panelidan qo'shilgan yangi o'qituvchi darhol ko'rinadi,
# botni qayta ishga tushirish shart emas.
# ==========================


def seed_teachers(pairs):
    """
    Boshlang'ich ro'yxatni bazaga yozadi (faqat yo'q bo'lganlarini).
    pairs: [(name, department), ...]
    Bir necha marta chaqirish xavfsiz.
    """

    db = connect()
    cursor = db.cursor()

    added = 0

    for name, department in pairs:

        cursor.execute(
            "SELECT id FROM teachers WHERE name=? AND department=?",
            (name, department)
        )

        if cursor.fetchone():
            continue

        cursor.execute(
            "INSERT INTO teachers (name, department, status) VALUES (?,?,'open')",
            (name, department)
        )

        added += 1

    db.commit()
    db.close()

    return added


def get_departments():
    """Bo'limlar ro'yxatini birinchi qo'shilgan tartibida qaytaradi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT department
        FROM teachers
        GROUP BY department
        ORDER BY MIN(id)
        """
    )

    data = [row[0] for row in cursor.fetchall()]

    db.close()

    return data


def get_teachers_by_department(department):
    """Bo'lim ichidagi o'qituvchilar (id, name, status)."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, name, status
        FROM teachers
        WHERE department=?
        ORDER BY id ASC
        """,
        (department,)
    )

    data = cursor.fetchall()

    db.close()

    return data


def get_teacher_by_name(name, department):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, name, department, telegram_id, status,
               pending_telegram_id, pending_username, pending_full_name
        FROM teachers
        WHERE name=? AND department=?
        """,
        (name, department)
    )

    row = cursor.fetchone()

    db.close()

    return row


def get_teacher_by_id(teacher_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, name, department, telegram_id, status,
               pending_telegram_id, pending_username, pending_full_name
        FROM teachers
        WHERE id=?
        """,
        (teacher_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


def find_teacher_binding(telegram_id):
    """Shu Telegram ID tasdiqlangan o'qituvchimi - bo'lsa (name, department) qaytaradi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT name, department
        FROM teachers
        WHERE telegram_id=? AND status='approved'
        """,
        (telegram_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


def teacher_exists(name, department):

    return get_teacher_by_name(name, department) is not None


# ==========================
# AKKAUNT SO'ROVI (tasdiqlash oqimi)
# ==========================


def request_teacher_binding(teacher_id, telegram_id, username, full_name):
    """
    So'rov yuboradi. Qaytaradi:
      "ok"            - so'rov yuborildi, admin javobini kutmoqda
      "already_mine"  - so'rovchi allaqachon shu o'qituvchiga tasdiqlangan
      "taken"         - boshqa kimdir allaqachon tasdiqlangan
      "pending_self"  - so'rovchining o'zi allaqachon so'rov yuborgan
      "pending_other" - boshqa kimdir so'rov yuborib, javob kutilmoqda
    """

    row = get_teacher_by_id(teacher_id)

    if not row:
        return "not_found"

    _, name, department, telegram_id_db, status, pending_id, _, _ = row

    if status == "approved":

        if telegram_id_db == telegram_id:
            return "already_mine"

        return "taken"

    if status == "pending":

        if pending_id == telegram_id:
            return "pending_self"

        return "pending_other"

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE teachers
        SET status='pending',
            pending_telegram_id=?,
            pending_username=?,
            pending_full_name=?
        WHERE id=?
        """,
        (telegram_id, username, full_name, teacher_id)
    )

    db.commit()
    db.close()

    return "ok"


def approve_teacher_binding(teacher_id):
    """Tasdiqlaydi. Qaytaradi: (telegram_id, name, department) yoki None."""

    row = get_teacher_by_id(teacher_id)

    if not row or row[4] != "pending":
        return None

    _, name, department, _, _, pending_id, _, _ = row

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE teachers
        SET status='approved',
            telegram_id=?,
            pending_telegram_id=NULL,
            pending_username=NULL,
            pending_full_name=NULL
        WHERE id=?
        """,
        (pending_id, teacher_id)
    )

    db.commit()
    db.close()

    return (pending_id, name, department)


def reject_teacher_binding(teacher_id):
    """Rad etadi. Qaytaradi: pending_telegram_id yoki None."""

    row = get_teacher_by_id(teacher_id)

    if not row or row[4] != "pending":
        return None

    pending_id = row[5]

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE teachers
        SET status='open',
            pending_telegram_id=NULL,
            pending_username=NULL,
            pending_full_name=NULL
        WHERE id=?
        """,
        (teacher_id,)
    )

    db.commit()
    db.close()

    return pending_id


def unbind_teacher(teacher_id):
    """Admin uchun: mavjud bog'lanishni bekor qiladi (o'qituvchi ishdan ketsa)."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE teachers
        SET status='open',
            telegram_id=NULL,
            pending_telegram_id=NULL,
            pending_username=NULL,
            pending_full_name=NULL
        WHERE id=?
        """,
        (teacher_id,)
    )

    db.commit()
    db.close()


# ==========================
# O'QUVCHI OYLIK BADAL
# ==========================


def get_student_fee(teacher, student):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT monthly_fee
        FROM students
        WHERE teacher=? AND student=?
        """,
        (teacher, student)
    )

    row = cursor.fetchone()

    db.close()

    return row[0] if row and row[0] else 0


def set_student_fee(teacher, student, amount):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE students
        SET monthly_fee=?
        WHERE teacher=? AND student=?
        """,
        (amount, teacher, student)
    )

    db.commit()
    db.close()


def get_department_for_teacher(name):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT department FROM teachers WHERE name=? LIMIT 1",
        (name,)
    )

    row = cursor.fetchone()

    db.close()

    return row[0] if row else "Boshqa"


# ==========================
# XODIMLAR (BUXGALTER)
# ==========================
#
#   status:
#     pending  - so'rov yuborilgan, admin javobini kutmoqda
#     approved - tasdiqlangan
#     rejected - rad etilgan
# ==========================


def request_staff(telegram_id, role, full_name, username):
    """
    So'rov yuboradi. Qaytaradi:
      "ok"       - yangi so'rov yaratildi
      "already"  - allaqachon tasdiqlangan
      "pending"  - so'rov ko'rib chiqilmoqda
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT id, status FROM staff WHERE telegram_id=? AND role=?",
        (telegram_id, role)
    )

    row = cursor.fetchone()

    if row:

        _, status = row

        if status == "approved":
            db.close()
            return "already"

        if status == "pending":
            db.close()
            return "pending"

        # rejected bo'lgan bo'lsa - qayta so'rov beradi

        cursor.execute(
            """
            UPDATE staff
            SET status='pending', full_name=?, username=?, requested_at=datetime('now')
            WHERE id=?
            """,
            (full_name, username, row[0])
        )

    else:

        cursor.execute(
            """
            INSERT INTO staff (telegram_id, role, full_name, username, status)
            VALUES (?,?,?,?,'pending')
            """,
            (telegram_id, role, full_name, username)
        )

    db.commit()
    db.close()

    return "ok"


def get_staff_request(telegram_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, telegram_id, role, full_name, username, status
        FROM staff WHERE telegram_id=?
        """,
        (telegram_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


def approve_staff(telegram_id):
    """Qaytaradi: (telegram_id, full_name) yoki None."""

    row = get_staff_request(telegram_id)

    if not row or row[5] != "pending":
        return None

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE staff SET status='approved' WHERE telegram_id=?",
        (telegram_id,)
    )

    db.commit()
    db.close()

    return (row[1], row[3])


def reject_staff(telegram_id):
    """Qaytaradi: telegram_id yoki None."""

    row = get_staff_request(telegram_id)

    if not row or row[5] != "pending":
        return None

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE staff SET status='rejected' WHERE telegram_id=?",
        (telegram_id,)
    )

    db.commit()
    db.close()

    return row[1]


def is_staff(telegram_id, role):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT 1 FROM staff WHERE telegram_id=? AND role=? AND status='approved'",
        (telegram_id, role)
    )

    row = cursor.fetchone()

    db.close()

    return row is not None


def get_staff_ids(role):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT telegram_id FROM staff WHERE role=? AND status='approved'",
        (role,)
    )

    data = [r[0] for r in cursor.fetchall()]

    db.close()

    return data


# ==========================
# TO'LOV KVITANSIYALARI
# ==========================


def create_payment_request(
        teacher,
        student,
        month,
        amount,
        drive_file_id,
        drive_link,
        submitted_by
):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO payments
        (
            teacher, student, month, status, date,
            amount, drive_file_id, drive_link,
            submitted_by, created_at
        )
        VALUES (?,?,?,'kutilmoqda',datetime('now'),?,?,?,?,datetime('now'))
        """,
        (teacher, student, month, amount, drive_file_id, drive_link, submitted_by)
    )

    row_id = cursor.lastrowid

    db.commit()
    db.close()

    return row_id


def get_payment(payment_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, teacher, student, month, status, amount,
               drive_file_id, drive_link, submitted_by, reviewed_by
        FROM payments WHERE id=?
        """,
        (payment_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


def approve_payment(payment_id, reviewed_by):
    """Qaytaradi: (teacher, student, month, submitted_by) yoki None."""

    row = get_payment(payment_id)

    if not row or row[4] != "kutilmoqda":
        return None

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE payments
        SET status='tasdiqlandi', reviewed_by=?, reviewed_at=datetime('now')
        WHERE id=?
        """,
        (reviewed_by, payment_id)
    )

    db.commit()
    db.close()

    return (row[1], row[2], row[3], row[8])


def reject_payment(payment_id, reviewed_by):
    """Qaytaradi: (teacher, student, month, submitted_by) yoki None."""

    row = get_payment(payment_id)

    if not row or row[4] != "kutilmoqda":
        return None

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE payments
        SET status='rad_etildi', reviewed_by=?, reviewed_at=datetime('now')
        WHERE id=?
        """,
        (reviewed_by, payment_id)
    )

    db.commit()
    db.close()

    return (row[1], row[2], row[3], row[8])


def get_pending_payments():
    """Buxgalter paneli uchun - hali ko'rib chiqilmagan barcha kvitansiyalar."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, teacher, student, month, amount, drive_file_id, submitted_by
        FROM payments
        WHERE status='kutilmoqda'
        ORDER BY id ASC
        """
    )

    data = cursor.fetchall()

    db.close()

    return data


def has_paid_this_month(teacher, student, month):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT 1 FROM payments
        WHERE teacher=? AND student=? AND month=? AND status='tasdiqlandi'
        """,
        (teacher, student, month)
    )

    row = cursor.fetchone()

    db.close()

    return row is not None


def get_unpaid_students(teacher, month):
    """Shu oy uchun hali tasdiqlangan to'lovi yo'q o'quvchilar: [(student, fee), ...]"""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT student, COALESCE(monthly_fee, 0)
        FROM students
        WHERE teacher=?
        """,
        (teacher,)
    )

    all_students = cursor.fetchall()

    cursor.execute(
        """
        SELECT student FROM payments
        WHERE teacher=? AND month=? AND status='tasdiqlandi'
        """,
        (teacher, month)
    )

    paid = {r[0] for r in cursor.fetchall()}

    db.close()

    return [
        (student, fee)
        for student, fee in all_students
        if student not in paid
    ]


def get_monthly_debt_rows(month):
    """
    Direktor hisobot uchun xom ma'lumot:
    [(teacher, department, student, fee, to'langanmi), ...]
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT teacher, student, COALESCE(monthly_fee, 0)
        FROM students
        ORDER BY teacher, student
        """
    )

    students = cursor.fetchall()

    cursor.execute(
        """
        SELECT teacher, student FROM payments
        WHERE month=? AND status='tasdiqlandi'
        """,
        (month,)
    )

    paid = {(r[0], r[1]) for r in cursor.fetchall()}

    cursor.execute("SELECT name, department FROM teachers")

    dept_map = dict(cursor.fetchall())

    db.close()

    rows = []

    for teacher, student, fee in students:

        rows.append((
            teacher,
            dept_map.get(teacher, "Boshqa"),
            student,
            fee,
            (teacher, student) in paid
        ))

    return rows


def get_approved_teacher_accounts():
    """Eslatma yuborish uchun: [(name, telegram_id), ...] - faqat bog'langanlar."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT name, telegram_id FROM teachers WHERE status='approved' AND telegram_id IS NOT NULL"
    )

    data = cursor.fetchall()

    db.close()

    return data


# ==========================
# MINI APP UCHUN QO'SHIMCHA
# ==========================


def get_parent_students_with_id(parent_id):
    """Ota-ona kartochkasi uchun: [(link_id, teacher, student), ...]"""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, teacher, student
        FROM parent_students
        WHERE parent_id=?
        """,
        (parent_id,)
    )

    data = cursor.fetchall()

    db.close()

    return data


def get_parent_student_link(link_id):
    """Bitta bog'lanish yozuvi: (id, parent_id, teacher, student) yoki None."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, parent_id, teacher, student
        FROM parent_students
        WHERE id=?
        """,
        (link_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


def get_student_payment_history(teacher, student):
    """To'liq tarix: [(month, status, amount, date), ...] - eng yangisi birinchi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT month, status, COALESCE(amount, 0), date
        FROM payments
        WHERE teacher=? AND student=?
        ORDER BY id DESC
        """,
        (teacher, student)
    )

    data = cursor.fetchall()

    db.close()

    return data


# ==========================
# DARS JADVALI
# ==========================
#
# Har bir o'qituvchi o'z "vaqt katakchalarini" (slot) tuzadi:
# kun + soat + fan + xona. Keyin shu katakchaga o'quvchilarni
# qo'shadi - hatto ular boshqa o'qituvchining o'quvchisi
# bo'lsa ham (masalan, solfedjio o'qituvchisi butun maktabdan
# o'quvchi qo'sha oladi).
#
# Natijada bitta o'quvchi bir nechta o'qituvchidan yig'ilgan
# to'liq haftalik jadvalga ega bo'ladi.
# ==========================


DAYS_OF_WEEK = [
    "Dushanba",
    "Seshanba",
    "Chorshanba",
    "Payshanba",
    "Juma",
    "Shanba",
    "Yakshanba"
]


SUBJECTS = [
    "Mutaxassislik",
    "Solfedjio",
    "San'at tarixi",
    "Musiqa adabiyoti",
    "Ansambl",
    "Xor",
    "Nazariy fanlar",
    "Tanlangan fan",
    "Boshqa"
]


_DAY_ORDER = {day: i for i, day in enumerate(DAYS_OF_WEEK)}


def create_slot(teacher, subject, day_of_week, time, room):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO schedule_slots (teacher, subject, day_of_week, time, room)
        VALUES (?,?,?,?,?)
        """,
        (teacher, subject, day_of_week, time, room)
    )

    slot_id = cursor.lastrowid

    db.commit()
    db.close()

    return slot_id


def get_teacher_slots(teacher):
    """[(id, subject, day_of_week, time, room), ...] - hafta kuni tartibida."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, subject, day_of_week, time, room
        FROM schedule_slots
        WHERE teacher=?
        """,
        (teacher,)
    )

    rows = cursor.fetchall()

    db.close()

    rows.sort(key=lambda r: (_DAY_ORDER.get(r[2], 99), r[3]))

    return rows


def get_slot(slot_id):
    """(id, teacher, subject, day_of_week, time, room) yoki None."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, teacher, subject, day_of_week, time, room
        FROM schedule_slots
        WHERE id=?
        """,
        (slot_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


def delete_slot(slot_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute("DELETE FROM schedule_slots WHERE id=?", (slot_id,))

    cursor.execute(
        "DELETE FROM schedule_slot_students WHERE slot_id=?",
        (slot_id,)
    )

    db.commit()
    db.close()


def get_slot_students(slot_id):
    """[(row_id, student, student_teacher), ...]"""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, student, student_teacher
        FROM schedule_slot_students
        WHERE slot_id=?
        ORDER BY student
        """,
        (slot_id,)
    )

    data = cursor.fetchall()

    db.close()

    return data


def add_student_to_slot(slot_id, student, student_teacher):
    """Allaqachon qo'shilgan bo'lsa qayta qo'shmaydi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id FROM schedule_slot_students
        WHERE slot_id=? AND student=? AND student_teacher=?
        """,
        (slot_id, student, student_teacher)
    )

    if cursor.fetchone():
        db.close()
        return False

    cursor.execute(
        """
        INSERT INTO schedule_slot_students (slot_id, student, student_teacher)
        VALUES (?,?,?)
        """,
        (slot_id, student, student_teacher)
    )

    db.commit()
    db.close()

    return True


def remove_slot_student(row_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM schedule_slot_students WHERE id=?",
        (row_id,)
    )

    db.commit()
    db.close()


def search_students(query, limit=15):
    """Butun maktab bo'yicha o'quvchi qidirish: [(teacher, student), ...]"""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT DISTINCT teacher, student
        FROM students
        WHERE student LIKE ?
        ORDER BY student
        LIMIT ?
        """,
        ("%" + query + "%", limit)
    )

    data = cursor.fetchall()

    db.close()

    return data


def get_student_full_schedule(teacher, student):
    """
    Shu o'quvchining BARCHA o'qituvchilardan yig'ilgan haftalik
    jadvali: [(subject, day_of_week, time, room, slot_teacher), ...]
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT sl.subject, sl.day_of_week, sl.time, sl.room, sl.teacher
        FROM schedule_slot_students ss
        JOIN schedule_slots sl ON sl.id = ss.slot_id
        WHERE ss.student_teacher=? AND ss.student=?
        """,
        (teacher, student)
    )

    rows = cursor.fetchall()

    db.close()

    rows.sort(key=lambda r: (_DAY_ORDER.get(r[1], 99), r[2]))

    return rows


# ==========================
# MINI APP - QO'SHIMCHA (admin/o'qituvchi ekranlari)
# ==========================


def get_slots_for_day(day_of_week):
    """
    Bugungi kunning BARCHA o'qituvchilaridagi darslari:
    [(id, teacher, subject, time, room, duration_minutes), ...]
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, teacher, subject, time, room, COALESCE(duration_minutes, 45)
        FROM schedule_slots
        WHERE day_of_week=?
        ORDER BY time
        """,
        (day_of_week,)
    )

    data = cursor.fetchall()

    db.close()

    return data


def get_slot_student_row(row_id):
    """(id, slot_id, student, student_teacher) yoki None - egalikni tekshirish uchun."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, slot_id, student, student_teacher
        FROM schedule_slot_students
        WHERE id=?
        """,
        (row_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


# ==========================
# OTA-ONA - ITV (METRIKA) ORQALI TOPISH
# ==========================
#
# Ota-ona farzandini ro'yxatdan tanlamaydi (bu xavfsizsiz edi -
# har kim istalgan bolani "o'zimniki" deb belgilay olardi).
# Buning o'rniga tug'ilganlik guvohnomasidagi ITV raqamini
# kiritadi - bu raqamni faqat hujjat egasi biladi.
# ==========================


import re as _re


def _normalize_metrika(value):

    return _re.sub(r"[^A-Za-z0-9]", "", value or "").upper()


def find_students_by_metrika(query):
    """ITV raqami bo'yicha o'quvchi(lar)ni topadi: [(teacher, student), ...]"""

    target = _normalize_metrika(query)

    if not target:
        return []

    db = connect()
    cursor = db.cursor()

    cursor.execute("SELECT teacher, student, metrika FROM students")

    rows = cursor.fetchall()

    db.close()

    return [
        (teacher, student)
        for teacher, student, metrika in rows
        if _normalize_metrika(metrika) == target
    ]


# ==========================
# O'QITUVCHINI ISM BO'YICHA QIDIRISH
# ==========================
#
# O'qituvchi botga kirganda butun maktab tuzilmasini
# ko'rmasligi kerak - u faqat o'z ismini yozadi.
# ==========================


def search_teachers_by_name(query, limit=10):
    """[(id, name, department, status), ...]"""

    text = (query or "").strip()

    if len(text) < 3:
        return []

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, name, department, COALESCE(status, 'open')
        FROM teachers
        WHERE name LIKE ?
        ORDER BY name
        LIMIT ?
        """,
        ("%" + text + "%", limit)
    )

    data = cursor.fetchall()

    db.close()

    return data


# ==========================
# XODIMLARNI ADMIN QO'SHADI
# ==========================


STAFF_ROLES = {
    "buxgalter": "🧮 Buxgalter",
    "direktor":  "🏫 Direktor",
    "yordamchi": "🤝 Yordamchi"
}


def add_staff_directly(telegram_id, role, full_name):
    """Admin qo'shadi - tasdiq talab qilinmaydi, darhol faol."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO staff (telegram_id, role, full_name, status)
        VALUES (?,?,?,'approved')
        ON CONFLICT(telegram_id) DO UPDATE SET
            role=excluded.role,
            full_name=excluded.full_name,
            status='approved'
        """,
        (telegram_id, role, full_name)
    )

    db.commit()
    db.close()


def list_staff():
    """[(id, telegram_id, role, full_name, status), ...]"""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, telegram_id, role, COALESCE(full_name, ''), status
        FROM staff
        ORDER BY role, full_name
        """
    )

    data = cursor.fetchall()

    db.close()

    return data


def remove_staff(staff_id):
    """Qaytaradi: (telegram_id, role, full_name) yoki None."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT telegram_id, role, COALESCE(full_name,'') FROM staff WHERE id=?",
        (staff_id,)
    )

    row = cursor.fetchone()

    if not row:
        db.close()
        return None

    cursor.execute("DELETE FROM staff WHERE id=?", (staff_id,))

    db.commit()
    db.close()

    return row


def get_staff_role(telegram_id):
    """Tasdiqlangan xodimning roli yoki None."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT role FROM staff WHERE telegram_id=? AND status='approved'",
        (telegram_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row[0] if row else None


# ==========================
# BADAL SUMMALARI
# ==========================
#
# Maktabda aniq belgilangan summalar. O'qituvchi o'quvchi
# qo'shayotganda yoki tahrirlayotganda shulardan birini
# tanlaydi - qo'lda yozmaydi (xato bo'lmasligi uchun).
# ==========================


MONTHLY_FEES = [123600, 82400, 86600, 57700]


# ==========================
# O'QUVCHI MA'LUMOTINI TAHRIRLASH
# ==========================


STUDENT_FIELDS = {
    "student":     "Ism-familiya",
    "birth_date":  "Tug'ilgan sana",
    "metrika":     "ITV raqami",
    "class_name":  "Sinf",
    "monthly_fee": "Oylik badal"
}


def update_student_field(teacher, student, field, value):
    """
    Bitta maydonni yangilaydi. field faqat STUDENT_FIELDS
    ichidan bo'lishi mumkin (SQL xavfsizligi uchun).
    """

    if field not in STUDENT_FIELDS:
        return False

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE students SET " + field + "=? WHERE teacher=? AND student=?",
        (value, teacher, student)
    )

    # ism o'zgarsa - bog'liq yozuvlarni ham yangilaymiz

    if field == "student":

        for table in ("student_documents", "payments", "parent_students"):
            cursor.execute(
                "UPDATE " + table + " SET student=? WHERE teacher=? AND student=?",
                (value, teacher, student)
            )

        cursor.execute(
            """
            UPDATE schedule_slot_students SET student=?
            WHERE student_teacher=? AND student=?
            """,
            (value, teacher, student)
        )

    db.commit()
    db.close()

    return True


def get_students_without_fee(teacher):
    """Badal summasi kiritilmagan o'quvchilar."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT student FROM students
        WHERE teacher=? AND (monthly_fee IS NULL OR monthly_fee = 0)
        ORDER BY student
        """,
        (teacher,)
    )

    data = [r[0] for r in cursor.fetchall()]

    db.close()

    return data


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


# ==========================
# SOZLAMALAR (kalit-qiymat)
# ==========================
#
# Kichik holatlarni saqlash uchun: masalan kunlik eslatma
# oxirgi marta qachon yuborilgani. Bot qayta ishga tushsa
# ham eslatma takror yuborilmaydi.
# ==========================


def _ensure_settings_table(cursor):

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings(
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)


def get_setting(key, default=None):

    db = connect()
    cursor = db.cursor()

    _ensure_settings_table(cursor)

    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))

    row = cursor.fetchone()

    db.close()

    return row[0] if row else default


def set_setting(key, value):

    db = connect()
    cursor = db.cursor()

    _ensure_settings_table(cursor)

    cursor.execute(
        """
        INSERT INTO settings (key, value) VALUES (?,?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """,
        (key, str(value))
    )

    db.commit()
    db.close()
