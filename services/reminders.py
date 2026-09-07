# ==========================
# services/reminders.py
# O'QITUVCHILARGA QARZDOR O'QUVCHILAR HAQIDA ESLATMA
# ==========================
#
# Har oyning 5, 15 va 25-kunlarida, agar o'qituvchining
# shu oy uchun hali to'lamagan o'quvchisi bo'lsa - unga
# eslatma yuboriladi. Barcha to'lagan bo'lsa - xabar
# yuborilmaydi (ortiqcha bezovta qilinmaydi).
#
# ==========================


import time
import threading

from datetime import datetime

from database import (
    get_approved_teacher_accounts,
    get_unpaid_students,
    get_parents_of_student,
    get_setting,
    set_setting
)


REMINDER_DAYS = {5, 15, 25}

# necha soatda bir marta tekshiradi
CHECK_INTERVAL_HOURS = 1

# kunning qaysi soatida yuboriladi (server vaqti bo'yicha) - tunda
# emas, ish vaqtida kelsin
SEND_HOUR = 10

# oxirgi yuborilgan sana bazada saqlanadi (daily_reminders.py dagidek) -
# bot bir kunda bir necha marta qayta ishga tushsa (masalan yangi kod
# yuklanganda), eslatma takror-takror yuborilib ketmasin
LAST_SENT_KEY = "payment_reminder_last_sent"


def _current_month():
    return datetime.now().strftime("%Y-%m")


def _month_name(month):
    """'2026-09' -> '2026-yil sentabr'"""

    names = [
        "yanvar", "fevral", "mart", "aprel", "may", "iyun",
        "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"
    ]

    try:
        year, index = month.split("-")
        return year + "-yil " + names[int(index) - 1]

    except (ValueError, IndexError):
        return month


def _money(amount):
    return "{:,}".format(int(amount)).replace(",", " ")


def _notify_parents(bot, teacher, student, fee, month):
    """
    Ota-onaga to'g'ridan-to'g'ri eslatma.

    Ilgari eslatma faqat o'qituvchiga borardi va o'qituvchi
    ota-onani o'zi quvib yurardi. Endi bot to'g'ridan-to'g'ri
    xabar beradi - o'qituvchi bu ishdan qutuladi.

    Yuborilgan ota-onalar sonini qaytaradi.
    """

    sent = 0

    for telegram_id, parent_name in get_parents_of_student(teacher, student):

        try:

            bot.send_message(
                telegram_id,
                "⏰ To'lov eslatmasi\n\n"
                "👨‍🎓 " + student + "\n"
                "📅 " + _month_name(month) + "\n"
                "💰 " + _money(fee) + " so'm\n\n"
                "Bu oy uchun badal to'lovi hali qayd etilmagan.\n\n"
                "To'lovni amalga oshirgan bo'lsangiz, kvitansiyani "
                "o'qituvchiga (" + teacher + ") yuboring - u tizimga "
                "kiritadi.\n\n"
                "Agar allaqachon yuborgan bo'lsangiz, bu xabarga "
                "e'tibor bermang - tasdiqlanishi bir necha kun olishi mumkin."
            )

            sent += 1

        except Exception:
            # ota-ona botni bloklagan yoki chatni o'chirgan bo'lishi mumkin
            pass

    return sent


def _send_reminders(bot):

    month = _current_month()

    parents_notified = 0

    for name, telegram_id in get_approved_teacher_accounts():

        unpaid = get_unpaid_students(name, month)

        if not unpaid:
            continue

        lines = []

        for student, fee in unpaid:

            reached = _notify_parents(bot, name, student, fee, month)

            parents_notified += reached

            lines.append(
                "- " + student + " (" + _money(fee) + " so'm)"
                + (" 📨" if reached else "")
            )

        text = (
            "⏰ Eslatma\n\n"
            + month + " uchun quyidagi o'quvchilar hali "
            "badal to'lovini amalga oshirmagan:\n\n"
            + "\n".join(lines)
            + "\n\n📨 belgisi - ota-onasiga ham xabar yuborildi.\n\n"
            "Kvitansiya kelganda \"💳 To'lov kvitansiyasi\" "
            "orqali yuboring."
        )

        try:
            bot.send_message(telegram_id, text)

        except Exception:
            pass

    return parents_notified


def _loop(bot, stop_event):

    while not stop_event.is_set():

        now = datetime.now()

        today = now.strftime("%Y-%m-%d")

        if (
            now.day in REMINDER_DAYS
            and now.hour >= SEND_HOUR
            and get_setting(LAST_SENT_KEY) != today
        ):

            try:
                count = _send_reminders(bot)

                set_setting(LAST_SENT_KEY, today)

                print("⏰ Qarzdorlik eslatmasi yuborildi, ota-onalarga:", count)

            except Exception as e:
                print("❌ Eslatma xatosi:", e)

        stop_event.wait(CHECK_INTERVAL_HOURS * 3600)


def start(bot):
    """Eslatma oqimini fonda ishga tushiradi."""

    stop_event = threading.Event()

    thread = threading.Thread(
        target=_loop,
        args=(bot, stop_event),
        daemon=True,
        name="payment-reminders"
    )

    thread.start()

    return stop_event
