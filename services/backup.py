# ==========================
# services/backup.py
# BAZANI GOOGLE DRIVE GA ZAXIRALASH
# ==========================
#
# school.db VPS diskida ishlaydi (72 KB - joy yemaydi),
# lekin har necha soatda Drive ga nusxasi yuboriladi.
#
# sqlite3.backup() ishlatiladi - bot yozayotgan paytda ham
# butun va buzilmagan nusxa oladi. Oddiy fayl nusxalash
# (copy) buni kafolatlamaydi.
#
# ==========================


import io
import os
import sqlite3
import threading
import traceback

from datetime import datetime

from database import DB_NAME

from services import gdrive


# necha soatda bir marta

INTERVAL_HOURS = 6

# Drive da nechta nusxa saqlansin

KEEP_COPIES = 30

BACKUP_FOLDER = "Zaxira"


# ==========================
# NUSXA OLISH
# ==========================


def snapshot_bytes():
    """
    Bazaning butun nusxasini xotirada oladi.
    Diskka vaqtinchalik fayl yozilmaydi.
    """

    source = sqlite3.connect(DB_NAME)

    memory = sqlite3.connect(":memory:")

    with memory:
        source.backup(memory)

    source.close()

    dump = "\n".join(memory.iterdump())

    memory.close()

    return dump.encode("utf-8")


def upload_backup():
    """Zaxirani Drive ga yuklaydi. Yuklangan fayl nomini qaytaradi."""

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    filename = "school_" + stamp + ".sql"

    data = snapshot_bytes()

    drive_id, link = gdrive.upload_bytes(
        data,
        filename,
        [BACKUP_FOLDER],
        "application/sql"
    )

    cleanup_old()

    return filename, len(data), link


# ==========================
# ESKI NUSXALARNI TOZALASH
# ==========================


def cleanup_old():
    """KEEP_COPIES dan ortiq eski nusxalarni korzinaga yuboradi."""

    try:

        folder = gdrive.folder_path(BACKUP_FOLDER)

        result = gdrive.service().files().list(
            q="'" + folder + "' in parents and trashed=false",
            orderBy="createdTime desc",
            fields="files(id, name)",
            pageSize=200
        ).execute()

        files = result.get("files", [])

        for old in files[KEEP_COPIES:]:
            gdrive.delete_file(old["id"])

    except Exception:
        traceback.print_exc()


# ==========================
# FON OQIMI
# ==========================


def _loop(stop_event, on_error=None):

    # bot ishga tushishi bilan bitta nusxa

    while not stop_event.is_set():

        try:

            name, size, _ = upload_backup()

            print(
                "💾 Zaxira yuklandi:",
                name,
                "(" + str(round(size / 1024)) + " KB)"
            )

        except Exception as e:

            print("❌ Zaxira xatosi:", e)

            traceback.print_exc()

            if on_error:
                try:
                    on_error(e)
                except Exception:
                    pass

        stop_event.wait(INTERVAL_HOURS * 3600)


def start(on_error=None):
    """Zaxira oqimini fonda ishga tushiradi."""

    stop_event = threading.Event()

    thread = threading.Thread(
        target=_loop,
        args=(stop_event, on_error),
        daemon=True,
        name="drive-backup"
    )

    thread.start()

    return stop_event
