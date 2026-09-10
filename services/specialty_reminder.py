# -*- coding: utf-8 -*-
# ==========================
# services/specialty_reminder.py
# YO'NALISH BELGILASH ESLATMASI
# ==========================
#
# Bo'limda bir nechta yo'nalish bo'lsa, o'qituvchiga yo'nalish
# belgilanmaguncha unga dars qo'shishda butun bo'limning fanlari
# chiqadi - "Amaliy san'at"da bu 34 ta fan, ko'pchiligi boshqa
# kasbniki. Aynan shundan noto'g'ri fan tanlangan.
#
# Bu bir martalik ish: 21 ta o'qituvchiga yo'nalish belgilash.
# Uni admin bajaradi, shuning uchun bot har kuni eslatib turadi.
#
# ESLATMA O'Z-O'ZIDAN TO'XTAYDI: ro'yxat bo'shagach hech narsa
# yuborilmaydi. Ya'ni buni keyin qo'lda o'chirish kerak emas.
#
# Xabarda har bir o'qituvchi alohida tugma bo'lib chiqadi -
# bosgan zahoti yo'nalish belgilash ekrani ochiladi, admin
# panelni qidirib yurmaydi.
#
# ==========================


import threading
import traceback

from datetime import datetime

from telebot import types

from database import (
    teachers_without_specialty,
    get_departments,
    get_setting,
    set_setting
)

from config import ADMIN_IDS


# oxirgi yuborilgan sana bazada saqlanadi - bot kun davomida
# bir necha marta qayta ishga tushsa ham eslatma takrorlanmaydi

LAST_SENT_KEY = "specialty_reminder_last_sent"


# Kimga yuboriladi. Bazadagi sozlama (bitta Telegram ID yoki
# vergul bilan bir nechta). Belgilanmagan bo'lsa - barcha
# adminlarga.
#
# Nega kodda emas: aniq odamning ID si git'da turmasligi kerak,
# va bot boshqa maktabda ishlaganda u yerdagi admin boshqa
# bo'ladi.

TARGET_KEY = "specialty_reminder_admin"


# server vaqti bo'yicha (systemd da TZ=Asia/Tashkent)
SEND_HOUR = 11

CHECK_INTERVAL_MINUTES = 20


def _targets():
    """Eslatma boradigan Telegram ID lar."""

    raw = (get_setting(TARGET_KEY) or "").strip()

    if not raw:
        return list(ADMIN_IDS)

    result = []

    for part in raw.replace(";", ",").split(","):

        part = part.strip()

        if not part:
            continue

        try:
            result.append(int(part))

        except ValueError:
            pass

    return result or list(ADMIN_IDS)


def build_message(pending):
    """Eslatma matni."""

    parts = [
        "🎯 Yo'nalish belgilash kerak\n",
        "Quyidagi o'qituvchilarning yo'nalishi hali belgilanmagan. "
        "Shu sababli ularga dars qo'shishda butun bo'limning fanlari "
        "chiqadi - kerak bo'lmagan kasblarniki ham.\n",
    ]

    hozirgi_bolim = None

    for _teacher_id, name, department, nechta in pending:

        if department != hozirgi_bolim:

            hozirgi_bolim = department

            parts.append(
                "\n📂 " + str(department)
                + " (" + str(nechta) + " ta yo'nalish)"
            )

        parts.append("   • " + name)

    parts.append(
        "\n\nQuyidagi tugmalardan birini bosing - yo'nalish "
        "belgilash ekrani ochiladi."
    )

    return "\n".join(parts)


def build_markup(pending):
    """
    Har o'qituvchiga bitta tugma.

    callback_data admin panelidagi mavjud ekranni ochadi
    (handlers/admin_schedule.py -> adyon:new). Unga bo'lim
    indeksi kerak - "orqaga" tugmasi uchun.
    """

    departments = get_departments()

    markup = types.InlineKeyboardMarkup()

    for teacher_id, name, department, _nechta in pending:

        try:
            dept_index = departments.index(department)

        except ValueError:
            # bo'lim ro'yxatdan topilmasa ham tugma ishlashi kerak
            dept_index = 0

        markup.add(
            types.InlineKeyboardButton(
                "🎯 " + name,
                callback_data="adyon:new:" + str(teacher_id)
                + ":" + str(dept_index)
            )
        )

    return markup


def send_once(bot):
    """
    Bir marta tekshirib yuboradi.

    Yuborilgan odamlar sonini qaytaradi. Ro'yxat bo'sh bo'lsa
    hech narsa yuborilmaydi va 0 qaytadi.
    """

    pending = teachers_without_specialty()

    if not pending:
        return 0

    text = build_message(pending)

    markup = build_markup(pending)

    sent = 0

    for chat_id in _targets():

        try:
            bot.send_message(chat_id, text, reply_markup=markup)

            sent += 1

        except Exception:
            # admin botni bloklagan yoki hali /start bosmagan
            pass

    return sent


def _loop(bot, stop_event):

    while not stop_event.is_set():

        now = datetime.now()

        today = now.strftime("%Y-%m-%d")

        if now.hour >= SEND_HOUR and get_setting(LAST_SENT_KEY) != today:

            try:

                count = send_once(bot)

                # Sanani ro'yxat bo'sh bo'lsa ham yozamiz - shunda
                # kun davomida qayta-qayta tekshirilmaydi.

                set_setting(LAST_SENT_KEY, today)

                if count:
                    print("🎯 Yo'nalish eslatmasi yuborildi:", count, "ta adminga")

            except Exception as e:

                print("❌ Yo'nalish eslatmasi xatosi:", e)

                traceback.print_exc()

        stop_event.wait(CHECK_INTERVAL_MINUTES * 60)


def start(bot):
    """Eslatma oqimini fonda ishga tushiradi."""

    stop_event = threading.Event()

    thread = threading.Thread(
        target=_loop,
        args=(bot, stop_event),
        daemon=True,
        name="specialty-reminder"
    )

    thread.start()

    return stop_event
