# -*- coding: utf-8 -*-
# ==========================
# db/migrations.py
# SXEMA VERSIYALARI
# ==========================
#
# Nega kerak: bot bir nechta maktabda alohida bazalar bilan
# ishlaydi. Ilgari sxema `create_tables()` va `migrate_schema()`
# orqali "bor bo'lmasa yarat" tamoyilida qurilardi - bu bitta
# baza uchun yetarli edi, lekin 10 ta bazada har biri qaysi
# holatda ekanini BILIB bo'lmasdi.
#
# Endi har bir bazada `schema_version` jadvali turadi va
# qaysi migratsiyalar qo'llangani aniq yozib boriladi.
#
# BASELINE (versiya 1) - fayl emas, KOD. U mavjud
# `create_tables()` + `migrate_schema()` ni chaqiradi, ya'ni
# bugungi sxemani beradi. Ikkalasi ham idempotent, shuning
# uchun BO'SH bazada ham, ALLAQACHON to'la ishlab turgan
# 19-BMSM bazasida ham xavfsiz ishlaydi.
#
# Bundan keyingi HAR QANDAY sxema o'zgarishi shu yerga emas,
# `migrations/002_nom.sql` fayliga yoziladi.
#
# ==========================


import glob
import os
import re
import sqlite3

from datetime import datetime


# Bu modul db.core ni FUNKSIYA ICHIDA import qiladi - modul
# yuklanish paytida emas. Sabab: database.py fasadi modullarni
# o'zaro bog'laydi va import paytidagi bog'liqlik halqa hosil
# qilardi.


BASELINE_VERSION = 1


def _migrations_dir():
    """migrations/ papkasi - db/ paketining yonida, loyiha ildizida."""

    here = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(os.path.dirname(here), "migrations")


def _now():

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==========================
# VERSIYA JADVALI
# ==========================


def _ensure_version_table(cursor):

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version(
            version    INTEGER PRIMARY KEY,
            name       TEXT,
            applied_at TEXT
        )
    """)


def current_version():
    """
    Bazaga qo'llangan eng oxirgi versiya. Jadval hali yo'q
    bo'lsa - 0 (ya'ni baseline ham qo'llanmagan).

    DIQQAT: faqat "jadval yo'q" xatosi 0 ga aylantiriladi.
    Baza band yoki buzuq bo'lsa - xato yuqoriga uzatiladi,
    aks holda ishlab turgan bazaga baseline qayta yugurtirilardi.
    """

    from db.core import connect

    db = connect()

    try:
        cursor = db.cursor()

        cursor.execute("SELECT MAX(version) FROM schema_version")

        row = cursor.fetchone()

        return row[0] if row and row[0] is not None else 0

    except sqlite3.OperationalError as err:

        if "no such table" in str(err).lower():
            return 0

        raise

    finally:
        db.close()


# ==========================
# FAYLLARNI TOPISH
# ==========================


_FILE_PATTERN = re.compile(r"^(\d{3,})_([A-Za-z0-9_]+)\.sql$")


def discover():
    """
    migrations/ dagi barcha `NNN_nom.sql` fayllari, versiya
    bo'yicha o'sish tartibida: [(versiya, nom, yo'l), ...]

    Qoidaga mos kelmagan fayllar jimgina e'tiborsiz qoldiriladi
    (README.md, .bak va h.k.).
    """

    folder = _migrations_dir()

    if not os.path.isdir(folder):
        return []

    found = []
    seen = {}

    for path in glob.glob(os.path.join(folder, "*.sql")):

        match = _FILE_PATTERN.match(os.path.basename(path))

        if not match:
            continue

        version = int(match.group(1))

        if version in seen:
            raise RuntimeError(
                "Bir xil versiya raqamli ikkita migratsiya fayli: "
                + os.path.basename(seen[version])
                + " va " + os.path.basename(path)
            )

        seen[version] = path

        found.append((version, match.group(2), path))

    return sorted(found, key=lambda item: item[0])


def pending():
    """Hali qo'llanmagan migratsiyalar."""

    version = current_version()

    return [item for item in discover() if item[0] > version]


# ==========================
# QO'LLASH
# ==========================


def apply_baseline():
    """
    Bugungi sxemani quradi va versiyani 1 deb belgilaydi.

    Ikkala chaqiruv ham idempotent, shuning uchun bu funksiya
    to'la ma'lumotli bazada ishga tushsa ham hech narsani
    yo'qotmaydi - faqat yetishmayotgan jadval/ustun qo'shiladi.
    """

    import database

    from db.core import connect

    database.create_tables()
    database.migrate_schema()

    db = connect()
    cursor = db.cursor()

    _ensure_version_table(cursor)

    cursor.execute(
        """
        INSERT OR IGNORE INTO schema_version (version, name, applied_at)
        VALUES (?,?,?)
        """,
        (BASELINE_VERSION, "baseline", _now())
    )

    db.commit()
    db.close()


def run_migrations(verbose=True):
    """
    Dastur ishga tushganda chaqiriladigan YAGONA kirish nuqtasi.
    Qo'llangandan keyingi versiyani qaytaradi.
    """

    from db.core import connect

    if current_version() == 0:
        apply_baseline()

    for version, name, path in pending():

        with open(path, encoding="utf-8") as handle:
            sql = handle.read()

        db = connect()
        cursor = db.cursor()

        try:
            # DIQQAT: sqlite'da executescript() ochiq tranzaksiyani
            # o'zi COMMIT qilib yuboradi va skript o'rtasida xato
            # chiqsa - undan oldingi buyruqlar bazada QOLADI.
            #
            # Shuning uchun har bir .sql fayl IDEMPOTENT yozilishi
            # shart (IF NOT EXISTS va h.k.) - qayta yugurtirilganda
            # xato bermasin. Xato bo'lsa versiya yozilmaydi, ya'ni
            # keyingi ishga tushishda o'sha fayl qaytadan uriniladi.

            if sql.strip():
                cursor.executescript(sql)

            cursor.execute(
                """
                INSERT INTO schema_version (version, name, applied_at)
                VALUES (?,?,?)
                """,
                (version, name, _now())
            )

            db.commit()

        except Exception as err:

            db.rollback()

            raise RuntimeError(
                os.path.basename(path)
                + " migratsiyasini qo'llashda xato: " + str(err)
            ) from err

        finally:
            db.close()

        if verbose:
            print("migratsiya qo'llandi: " + os.path.basename(path))

    return current_version()


def stamp(version, name):
    """
    Sxemaga TEGMASDAN versiyani yozib qo'yadi.

    Qo'lda tuzatish uchun: masalan migratsiya yarim qo'llanib
    xato bergan, siz uni qo'lda tugatgansiz va tizimga "bu
    versiya bor" deb aytmoqchisiz.
    """

    from db.core import connect

    db = connect()
    cursor = db.cursor()

    _ensure_version_table(cursor)

    cursor.execute(
        """
        INSERT INTO schema_version (version, name, applied_at)
        VALUES (?,?,?)
        ON CONFLICT(version) DO UPDATE SET
            name=excluded.name,
            applied_at=excluded.applied_at
        """,
        (version, name, _now())
    )

    db.commit()
    db.close()
