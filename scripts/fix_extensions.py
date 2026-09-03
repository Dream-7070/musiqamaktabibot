# ==========================
# scripts/fix_extensions.py
# .bin KENGAYTMALARINI TUZATISH
# ==========================
#
# Telegram fotosurat (rasm) fayllar uchun kengaytma bermaydi,
# shuning uchun migratsiyada ular .bin bo'lib qolgan.
# Bu skript fayl tarkibiga (magic bytes) qarab haqiqiy
# kengaytmani aniqlaydi va Drive'dagi nomni ham, bazani ham
# tuzatadi.
#
#   python scripts/fix_extensions.py
#
# ==========================


import os
import sys
import sqlite3

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from database import DB_NAME
from services import gdrive


def detect_extension(data):
    """Fayl boshidagi baytlarga qarab kengaytmani topadi."""

    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"

    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"

    if data[:4] == b"%PDF":
        return ".pdf"

    if data[:4] == b"PK\x03\x04":
        # docx / xlsx / pptx - ichini ochib ko'rish kerak,
        # lekin hozircha eng ehtimolli variant

        if b"word/" in data[:4096]:
            return ".docx"

        if b"xl/" in data[:4096]:
            return ".xlsx"

        if b"ppt/" in data[:4096]:
            return ".pptx"

        return ".zip"

    if data[:4] in (b"RIFF",):
        return ".webp"

    return None


def process_table(cursor, table):

    rows = cursor.execute(
        "SELECT id, file_name, drive_file_id FROM "
        + table
        + " WHERE file_name LIKE '%.bin' AND drive_file_id IS NOT NULL"
    ).fetchall()

    fixed = 0
    skipped = 0

    for row_id, file_name, drive_id in rows:

        try:

            data = gdrive.download_bytes(drive_id)

            ext = detect_extension(data)

            if not ext:

                print(
                    "   ⚠️ ", table, row_id, file_name,
                    "- turi aniqlanmadi, o'zgarishsiz qoldi"
                )

                skipped += 1
                continue

            new_name = file_name[:-4] + ext

            gdrive.service().files().update(
                fileId=drive_id,
                body={"name": new_name}
            ).execute()

            cursor.execute(
                "UPDATE " + table
                + " SET file_name=?, file_size=? WHERE id=?",
                (new_name, len(data), row_id)
            )

            print("   ✅", table, row_id, file_name, "->", new_name)

            fixed += 1

        except Exception as e:

            print("   ❌", table, row_id, file_name, "-", e)

            skipped += 1

    return fixed, skipped


def main():

    db = sqlite3.connect(DB_NAME)

    cursor = db.cursor()

    print("📄 documents jadvali:")

    f1, s1 = process_table(cursor, "documents")

    print()
    print("📄 student_documents jadvali:")

    f2, s2 = process_table(cursor, "student_documents")

    db.commit()
    db.close()

    print()
    print("=" * 40)
    print("✅ Tuzatildi:", f1 + f2)
    print("⚠️  O'tkazib yuborildi:", s1 + s2)
    print("=" * 40)


if __name__ == "__main__":
    main()
