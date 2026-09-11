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


# Ruxsat doirasi ulanish usuliga qarab farq qiladi:
#
#   OAuth (odam nomidan) - drive.file: ilova FAQAT o'zi yaratgan
#   fayllarni ko'radi. Bu "nozik" ruxsat emas, tekshiruv talab
#   qilinmaydi.
#
#   Service account - drive: unga ulashilgan papkadagi ESKI
#   fayllarni ham o'qiy olishi kerak (ular ilgari odam nomidan
#   yuklangan, ya'ni service account ularni "o'zi yaratmagan").
#   Service account rozilik oynasidan o'tmaydi, shuning uchun
#   bu ruxsat uchun Google tekshiruvi kerak emas.

OAUTH_SCOPES = ["https://www.googleapis.com/auth/drive.file"]

SERVICE_ACCOUNT_SCOPES = ["https://www.googleapis.com/auth/drive"]

SCOPES = OAUTH_SCOPES


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# Yo'llar .env dan keladi - har maktabning O'Z Google akkaunti
# bo'ladi, shuning uchun bu fayllar maktabga xos.

from config import (
    GOOGLE_TOKEN_FILE,
    GOOGLE_CREDENTIALS_FILE,
    GOOGLE_SERVICE_ACCOUNT_FILE,
    DRIVE_ROOT_FOLDER,
    DRIVE_ROOT_FOLDER_ID,
)


TOKEN_FILE = GOOGLE_TOKEN_FILE

CREDENTIALS_FILE = GOOGLE_CREDENTIALS_FILE

SERVICE_ACCOUNT_FILE = GOOGLE_SERVICE_ACCOUNT_FILE


ROOT_FOLDER_NAME = DRIVE_ROOT_FOLDER

ROOT_FOLDER_ID = DRIVE_ROOT_FOLDER_ID


def use_service_account():
    """Service account usuli yoqilganmi."""

    return bool(SERVICE_ACCOUNT_FILE) and os.path.exists(SERVICE_ACCOUNT_FILE)

FOLDER_MIME = "application/vnd.google-apps.folder"


# googleapiclient klienti thread-safe emas (ichida bitta http
# ulanish bor), bot esa ko'p oqimda ishlaydi. Ilgari BARCHA
# so'rovlar bitta global lock ostida ketardi - bitta o'qituvchi
# fayl yuklayotganda qolganlar navbatda turardi.
#
# Endi har bir oqim o'zining klientini oladi (thread-local),
# shuning uchun yuklash/yuklab olish parallel ketadi. Lock
# faqat papka keshini himoyalash uchun qoladi.

_local = threading.local()

_cache_lock = threading.Lock()

# token.json ni ikki oqim bir vaqtda yangilamasin

_creds_lock = threading.Lock()


# (parent_id, nom) -> folder_id

_folder_cache = {}

# bir xil papkani ikki oqim bir vaqtda yaratib yubormasin

_folder_locks = {}


# ==========================
# AUTH
# ==========================


def _credentials():

    with _creds_lock:
        return _load_credentials()


def _load_credentials():

    # 1-USUL: SERVICE ACCOUNT
    #
    # Server uchun to'g'ri usul: brauzer ham, rozilik oynasi ham,
    # muddat ham yo'q. Kalit faylning o'zi yetarli, token kerak
    # bo'lganda kutubxona o'zi oladi va yangilaydi.

    if use_service_account():

        from google.oauth2 import service_account

        return service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SERVICE_ACCOUNT_SCOPES
        )


    # 2-USUL: OAUTH (odam nomidan, eski)

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
    """Drive API klienti - har bir oqim uchun alohida."""

    client = getattr(_local, "service", None)

    if client is None:

        client = build(
            "drive",
            "v3",
            credentials=_credentials(),
            cache_discovery=False
        )

        _local.service = client

    return client


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


def _folder_lock(key):
    """Har bir papka uchun alohida qulf - boshqalari kutib turmaydi."""

    with _cache_lock:

        lock = _folder_locks.get(key)

        if lock is None:
            lock = threading.Lock()
            _folder_locks[key] = lock

        return lock


def _find_or_create_folder(name, parent_id):

    key = (parent_id, name)

    cached = _folder_cache.get(key)

    if cached:
        return cached


    # ayni papkani qidirayotgan oqimlar navbat kutadi, boshqa
    # papkalar bilan ishlayotganlar esa parallel ketaveradi

    with _folder_lock(key):

        cached = _folder_cache.get(key)

        if cached:
            return cached

        return _lookup_or_create_folder(name, parent_id, key)


def _lookup_or_create_folder(name, parent_id, key):

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


    # ILDIZ PAPKA
    #
    # Service account'ning o'z Drive'i yo'q - u ildizda papka
    # YARATA OLMAYDI. Shuning uchun unga maktab ulashgan tayyor
    # papkaning ID si beriladi (.env dagi DRIVE_ROOT_FOLDER_ID).
    #
    # OAuth usulida esa papka nomi bo'yicha topiladi/yaratiladi.

    if ROOT_FOLDER_ID:
        parent = ROOT_FOLDER_ID

    else:

        if use_service_account():
            raise RuntimeError(
                "DRIVE_ROOT_FOLDER_ID ko'rsatilmagan. Service account "
                "ildizda papka yarata olmaydi - unga maktab Drive'idagi "
                "papka ulashilib, uning ID si .env ga yozilishi kerak."
            )

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


    # SERVICE ACCOUNT
    #
    # Uning o'z Drive'i yo'q, shuning uchun storageQuota ma'nosiz
    # (fayllar maktab diskida turadi, uning kvotasidan yeydi).
    # Buning o'rniga ulashilgan papkaga kira olishini tekshiramiz -
    # aslida bizga kerak bo'lgan yagona narsa shu.

    if use_service_account():

        if not ROOT_FOLDER_ID:
            raise RuntimeError(
                "DRIVE_ROOT_FOLDER_ID ko'rsatilmagan."
            )

        folder = _retry(
            lambda: service().files().get(
                fileId=ROOT_FOLDER_ID,
                fields="id, name"
            ).execute()
        )

        import json

        with open(SERVICE_ACCOUNT_FILE) as handle:
            email = json.load(handle).get("client_email")

        return {
            "email": email,
            "folder": folder.get("name"),
            "used_gb": None,
            "limit_gb": None
        }


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
