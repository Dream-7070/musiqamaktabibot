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
    get_unpaid_students
)


REMINDER_DAYS = {5, 15, 25}

# necha soatda bir marta tekshiradi
CHECK_INTERVAL_HOURS = 12


def _current_month():
    return datetime.now().strftime("%Y-%m")


def _send_reminders(bot):

    month = _current_month()

    for name, telegram_id in get_approved_teacher_accounts():

        unpaid = get_unpaid_students(name, month)

        if not unpaid:
            continue

        lines = [
            "- " + student + " (" + str(fee) + " so'm)"
            for student, fee in unpaid
        ]

        text = (
            "⏰ Eslatma\n\n"
            + month + " uchun quyidagi o'quvchilar hali "
            "badal to'lovini amalga oshirmagan:\n\n"
            + "\n".join(lines)
            + "\n\nKvitansiya kelganda \"💳 To'lov kvitansiyasi\" "
            "orqali yuboring."
        )

        try:
            bot.send_message(telegram_id, text)

        except Exception:
            pass


def _loop(bot, stop_event):

    last_sent_day = None

    while not stop_event.is_set():

        today = datetime.now()

        if today.day in REMINDER_DAYS and today.day != last_sent_day:

            try:
                _send_reminders(bot)
                last_sent_day = today.day

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
