# -*- coding: utf-8 -*-
# ==========================
# db/school.py
# MAKTAB KIMLIGI
# ==========================
#
# Bot bir nechta maktabda ishlaydi - har birining o'z bazasi bor.
# Maktab nomi kodda yozilib qolmasligi kerak, aks holda har
# maktabga alohida kod tahrirlash kerak bo'ladi.
#
# Nom va slug bazadagi `settings` jadvalida turadi. Birinchi
# ishga tushishda ular .env dan ko'chiriladi, keyin esa BAZA
# haqiqiy manba bo'ladi - admin nomni o'zgartirsa, har qayta
# ishga tushishda u qaytarib yozilmaydi.
#
# ==========================


import re


# Bu modul quyidagi modullardagi nomlarni ishlatadi
# (database.py fasadi ularni yuklashda joylashtiradi):
#   db.core: get_setting, set_setting


SCHOOL_NAME_KEY = "school_name"

SCHOOL_SLUG_KEY = "school_slug"


_SLUG_PATTERN = re.compile(r"^[a-z0-9_-]+$")


# ==========================
# NOM
# ==========================


def get_school_name(default="Maktab"):
    """Bazadagi maktab nomi. O'rnatilmagan yoki bo'sh bo'lsa - default."""

    value = get_setting(SCHOOL_NAME_KEY)

    if value is None or not str(value).strip():
        return default

    return str(value).strip()


def set_school_name(name):
    """Maktab nomini saqlaydi. Bo'sh bo'lsa - ValueError."""

    value = "" if name is None else str(name).strip()

    if not value:
        raise ValueError("Maktab nomi bo'sh bo'lishi mumkin emas.")

    set_setting(SCHOOL_NAME_KEY, value)


# ==========================
# SLUG
# ==========================
#
# Slug - texnik nom: subdomen, papka va servis nomi shundan
# yasaladi. Shuning uchun faqat xavfsiz belgilarga ruxsat.


def get_school_slug(default="maktab"):
    """Bazadagi maktab slugi. O'rnatilmagan yoki bo'sh bo'lsa - default."""

    value = get_setting(SCHOOL_SLUG_KEY)

    if value is None or not str(value).strip():
        return default

    return str(value).strip()


def set_school_slug(slug):
    """Slugni kichik harfga keltirib saqlaydi. Yaroqsiz bo'lsa - ValueError."""

    value = "" if slug is None else str(slug).strip().lower()

    if not value:
        raise ValueError("Maktab slugi bo'sh bo'lishi mumkin emas.")

    if not _SLUG_PATTERN.match(value):
        raise ValueError(
            "Yaroqsiz maktab slugi: '" + value + "'. Faqat a-z, 0-9, "
            "chiziqcha va pastki chiziqchaga ruxsat."
        )

    set_setting(SCHOOL_SLUG_KEY, value)


# ==========================
# BIRINCHI ISHGA TUSHISH
# ==========================


def ensure_school_identity(name, slug):
    """
    .env dagi qiymatlarni bazaga URUG'LAYDI - faqat bazada
    hali yo'q bo'lsa.

    Yaroqsiz qiymat botni to'xtatmaydi: shunchaki o'tkazib
    yuboriladi. Amaldagi (nom, slug) juftligini qaytaradi.
    """

    if get_setting(SCHOOL_NAME_KEY) is None:

        try:
            set_school_name(name)

        except ValueError:
            pass

    if get_setting(SCHOOL_SLUG_KEY) is None:

        try:
            set_school_slug(slug)

        except ValueError:
            pass

    return get_school_name(), get_school_slug()
