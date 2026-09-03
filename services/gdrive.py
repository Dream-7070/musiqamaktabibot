# ==========================
# services/gdrive.py
# GOOGLE DRIVE SAQLAGICH
# ==========================
#
# Fayllar VPS diskiga yozilmaydi.
# Telegramdan kelgan baytlar to'g'ridan-to'g'ri
# Drive'ga uzatiladi va xotiradan o'chadi.
#
# Papka tuzilmasi:
#
#   Maktab arxivi/
#       O'qituvchilar/
#           Xalq cholg'u/
#               Qayumov Qobil/
#                   diplom/
#       O'quvchilar/
#           Qayumov Qobil/
#               Alisherov Zafar/
#                   metrika_rasm/
#       Zaxira/
#           school_2026-09-02_14-00.db
#
# ==========================


import io
import os
import time
import threading
import mimetypes

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from googleapiclient.discovery import build
from googleapiclient.http import (
    MediaIoBaseUpload,
    MediaIoBaseDownload
)
from googleapiclient.errors import HttpError


# ==========================
# SOZLAMALAR
# ==========================


SCOPES = ["https://www.googleapis.com/auth/drive.file"]


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")


ROOT_FOLDER_NAME = "Maktab arxivi"

FOLDER_MIME = "application/vnd.google-apps.folder"


# googleapiclient thread-safe emas,
# bot esa ko'p oqimda ishlaydi

_lock = threading.Lock()

_service = None


# (parent_id, nom) -> folder_id

_folder_cache = {}


# ==========================
# AUTH
# ==========================


def _credentials():

    if not os.path.exists(TOKEN_FILE):

        raise RuntimeError(
            "token.json topilmadi. Avval kompyuteringizda "
            "`python scripts/get_token.py` ni ishga tushiring."
        )


    creds = Credentials.from_authorized_user_file(
        TOKEN_FILE,
        SCOPES
    )


    if not creds.valid:

        if creds.expired and creds.refresh_token:

            creds.refresh(Request())

            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

        else:

            raise RuntimeError(
                "token.json yaroqsiz. "
                "scripts/get_token.py orqali qayta oling."
            )


    return creds


def service():
    """Drive API klienti (bir marta yaratiladi)."""

    global _service

    if _service is None:

        _service = build(
            "drive",
            "v3",
            credentials=_credentials(),
            cache_discovery=False
        )

    return _service


# ==========================
# QAYTA URINISH
# ==========================


def _retry(func, tries=4):
    """Tarmoq va vaqtinchalik server xatolarida qayta uriladi."""

    delay = 2

    for attempt in range(tries):

        try:
            return func()

        except HttpError as e:

            code = getattr(e.resp, "status", 0)

            if code in (403, 429, 500, 502, 503, 504) and attempt < tries - 1:

                time.sleep(delay)
                delay *= 2
                continue

            raise

        except Exception:

            if attempt < tries - 1:

                time.sleep(delay)
                delay *= 2
                continue

            raise


# ==========================
# PAPKALAR
# ==========================


def _escape(name):
    """Drive so'rovi uchun maxsus belgilarni himoyalaydi."""

    return name.replace("\\", "\\\\").replace("'", "\\'")


def _find_or_create_folder(name, parent_id):

    key = (parent_id, name)

    if key in _folder_cache:
        return _folder_cache[key]


    query = (
        "name='" + _escape(name) + "' "
        "and mimeType='" + FOLDER_MIME + "' "
        "and trashed=false"
    )

    if parent_id:
        query += " and '" + parent_id + "' in parents"


    result = _retry(
        lambda: service().files().list(
            q=query,
            spaces="drive",
            fields="files(id)",
            pageSize=1
        ).execute()
    )


    files = result.get("files", [])


    if files:

        folder_id = files[0]["id"]

    else:

        body = {
            "name": name,
            "mimeType": FOLDER_MIME
        }

        if parent_id:
            body["parents"] = [parent_id]

        folder = _retry(
            lambda: service().files().create(
                body=body,
                fields="id"
            ).execute()
        )

        folder_id = folder["id"]


    _folder_cache[key] = folder_id

    return folder_id


def folder_path(*parts):
    """
    Papka yo'lini yaratadi (bo'lmasa) va oxirgi papka id sini qaytaradi.

    folder_path("O'qituvchilar", "Xalq cholg'u", "Qayumov Qobil", "diplom")
    """

    with _lock:

        parent = _find_or_create_folder(
            ROOT_FOLDER_NAME,
            None
        )

        for part in parts:

            if not part:
                continue

            parent = _find_or_create_folder(
                str(part).strip(),
                parent
            )

        return parent


# ==========================
# YUKLASH
# ==========================


def upload_bytes(data, filename, parts, mimetype=None):
    """
    Baytlarni to'g'ridan-to'g'ri Drive'ga yuklaydi.
    VPS diskiga hech narsa yozilmaydi.

    Qaytaradi: (drive_file_id, web_link)
    """

    if mimetype is None:

        mimetype = (
            mimetypes.guess_type(filename)[0]
            or "application/octet-stream"
        )


    parent = folder_path(*parts)


    media = MediaIoBaseUpload(
        io.BytesIO(data),
        mimetype=mimetype,
        resumable=len(data) > 5 * 1024 * 1024
    )


    with _lock:

        result = _retry(
            lambda: service().files().create(
                body={
                    "name": filename,
                    "parents": [parent]
                },
                media_body=media,
                fields="id, webViewLink"
            ).execute()
        )


    return result["id"], result.get("webViewLink")


# ==========================
# YUKLAB OLISH
# ==========================


def download_bytes(drive_file_id):
    """Drive'dan faylni baytlar ko'rinishida oladi."""

    buffer = io.BytesIO()

    with _lock:

        request = service().files().get_media(
            fileId=drive_file_id
        )

        downloader = MediaIoBaseDownload(buffer, request)

        done = False

        while not done:
            _, done = downloader.next_chunk()

    buffer.seek(0)

    return buffer.read()


# ==========================
# O'CHIRISH
# ==========================


def delete_file(drive_file_id):
    """
    Faylni Drive korzinasiga yuboradi.
    Butunlay o'chirmaydi - 30 kun ichida tiklash mumkin.
    """

    if not drive_file_id:
        return False


    try:

        with _lock:

            _retry(
                lambda: service().files().update(
                    fileId=drive_file_id,
                    body={"trashed": True}
                ).execute()
            )

        return True

    except HttpError as e:

        # fayl allaqachon yo'q
        if getattr(e.resp, "status", 0) == 404:
            return False

        raise


# ==========================
# TEKSHIRUV
# ==========================


def check():
    """Ulanishni sinaydi: akkaunt va bo'sh joy haqida ma'lumot."""

    with _lock:

        about = _retry(
            lambda: service().about().get(
                fields="user(emailAddress), storageQuota"
            ).execute()
        )


    quota = about.get("storageQuota", {})

    used = int(quota.get("usage", 0))

    limit = int(quota.get("limit") or 0)


    return {
        "email": about.get("user", {}).get("emailAddress"),
        "used_gb": round(used / 1024 ** 3, 2),
        "limit_gb": round(limit / 1024 ** 3, 2) if limit else None
    }


# ==========================
# KENGAYTMANI ANIQLASH
# ==========================


def detect_extension(data):
    """Fayl boshidagi baytlarga (magic bytes) qarab kengaytmani topadi."""

    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"

    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"

    if data[:4] == b"%PDF":
        return ".pdf"

    if data[:4] == b"PK\x03\x04":

        if b"word/" in data[:4096]:
            return ".docx"

        if b"xl/" in data[:4096]:
            return ".xlsx"

        if b"ppt/" in data[:4096]:
            return ".pptx"

        return ".zip"

    if data[:4] == b"RIFF":
        return ".webp"

    return None
