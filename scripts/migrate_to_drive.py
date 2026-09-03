# ==========================
# scripts/migrate_to_drive.py
# ESKI ARXIVNI GOOGLE DRIVE GA KO'CHIRISH
# ==========================
#
# Bazadagi har bir hujjat Telegramdan yuklab olinadi va
# Google Drive ga joylanadi. Disk ishlatilmaydi - fayl
# faqat xotiradan o'tadi.
#
#   python scripts/migrate_to_drive.py
#
# Uzilib qolsa, qayta ishga tushiring - ko'chirilganlarini
# tashlab ketib, qolganidan davom etadi.
#
# ==========================


import os
import sys
import time
import mimetypes

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

import telebot

from config import TOKEN

from data.teachers import teachers as TEACHERS_BY_DEPT

from services import gdrive

from database import (
    create_tables,
    migrate_schema,
    pending_drive_rows,
    set_teacher_file_drive,
    set_student_file_drive
)


bot = telebot.TeleBot(TOKEN)


# ==========================
# O'QITUVCHI -> BO'LIM
# ==========================


def _department_map():

    mapping = {}

    for dept, names in TEACHERS_BY_DEPT.items():

        for name in names:
            mapping[name] = dept

    return mapping


DEPARTMENTS = _department_map()


# ==========================
# NOM TOZALASH
# ==========================


def safe_name(name):
    """Drive papka nomi uchun xavfli belgilarni olib tashlaydi."""

    if not name:
        return "Nomalum"

    cleaned = str(name)

    for ch in ["/", "\\", ":", "*", "?", "\"", "<", ">", "|", "\n", "\r"]:
        cleaned = cleaned.replace(ch, " ")

    cleaned = " ".join(cleaned.split())

    return cleaned[:120] or "Nomalum"


# ==========================
# KO'CHIRISH
# ==========================


def migrate_one(row):

    table, row_id, teacher, student, doc_type, file_id = row


    # 1. Telegramdan olamiz

    info = bot.get_file(file_id)

    data = bot.download_file(info.file_path)


    # 2. Nom tayyorlaymiz

    ext = os.path.splitext(info.file_path)[1]

    if not ext:
        # Telegram fotosurat uchun kengaytma bermaydi -
        # tarkibga qarab aniqlaymiz
        ext = gdrive.detect_extension(data) or ".jpg"

    if student:
        base = safe_name(student)
    else:
        base = safe_name(teacher)

    filename = (
        base.replace(" ", "_")
        + "_" + doc_type
        + "_" + str(row_id)
        + ext
    )


    # 3. Drive papka yo'li

    dept = safe_name(
        DEPARTMENTS.get(teacher, "Boshqa")
    )

    if student:
        parts = [
            "O'quvchilar",
            dept,
            safe_name(teacher),
            safe_name(student),
            doc_type
        ]
    else:
        parts = [
            "O'qituvchilar",
            dept,
            safe_name(teacher),
            doc_type
        ]


    # 4. Yuklaymiz

    drive_id, link = gdrive.upload_bytes(
        data,
        filename,
        parts,
        mimetypes.guess_type(filename)[0]
    )


    # 5. Bazaga yozamiz

    if table == "documents":
        set_teacher_file_drive(row_id, drive_id, link, filename)
    else:
        set_student_file_drive(row_id, drive_id, link, filename)


    return len(data)


def main():

    create_tables()
    migrate_schema()


    print("🔌 Google Drive tekshirilmoqda...")

    info = gdrive.check()

    print("👤 Akkaunt:", info["email"])

    if info["limit_gb"]:
        print(
            "💾 Band:",
            info["used_gb"], "GB /",
            info["limit_gb"], "GB"
        )

    print()


    rows = pending_drive_rows()

    total = len(rows)

    if not total:
        print("✅ Ko'chiriladigan fayl qolmadi.")
        return 0


    print("📦 Ko'chiriladi:", total, "ta fayl")
    print()


    ok = 0
    failed = []
    total_bytes = 0

    start = time.time()


    for index, row in enumerate(rows, 1):

        table, row_id, teacher, student, doc_type, _ = row

        label = (
            (student or teacher)
            + " / " + doc_type
        )

        print(
            "[" + str(index) + "/" + str(total) + "]",
            label,
            end=" ... ",
            flush=True
        )

        try:

            size = migrate_one(row)

            total_bytes += size
            ok += 1

            print("✅", round(size / 1024), "KB")

        except Exception as e:

            failed.append((table, row_id, label, str(e)))

            print("❌", e)


        # Telegram va Drive limitlarini urmaslik uchun

        time.sleep(0.3)


    elapsed = int(time.time() - start)

    print()
    print("=" * 40)
    print("✅ Ko'chirildi:", ok, "/", total)
    print("📊 Hajm:", round(total_bytes / 1024 / 1024, 1), "MB")
    print("⏱  Vaqt:", elapsed, "soniya")


    if failed:

        print()
        print("❌ Ko'chmagan", len(failed), "ta:")

        for table, row_id, label, err in failed:
            print("   ", table, row_id, label, "->", err)

        print()
        print("Sabab odatda: fayl Telegram serveridan o'chgan")
        print("yoki file_id boshqa botga tegishli.")
        print("Skriptni qayta ishga tushirsangiz, faqat shular")
        print("qayta urinib ko'riladi.")

    print("=" * 40)

    return 0


if __name__ == "__main__":
    sys.exit(main())
