# ==========================
# services/daily_reminders.py
# KUNLIK ESLATMA
# ==========================
#
# Har kuni bir marta tekshiradi va o'qituvchiga eslatadi:
#
#   1. Majburiy hujjatlar yuklanganmi
#      (pasport nusxasi, diplom nusxasi, 3x4 rasm)
#
#   2. O'quvchilarga oylik badal summasi kiritilganmi
#
# Hammasi joyida bo'lsa - xabar yuborilmaydi.
#
# ==========================


import threading
import traceback

from datetime import datetime

from database import (
    REQUIRED_TEACHER_DOCS,
    get_teachers_needing_reminder,
    get_understaffed_groups,
    get_setting,
    set_setting
)

from config import ADMIN_IDS


# oxirgi yuborilgan sana bazada saqlanadi - bot qayta
# ishga tushsa ham eslatma takror yuborilmaydi

LAST_SENT_KEY = "daily_reminder_last_sent"


# kunning qaysi soatida yuboriladi (server vaqti bo'yicha)
SEND_HOUR = 10

# necha soatda bir marta tekshiradi
CHECK_INTERVAL_HOURS = 1


def build_message(missing_docs, no_fee):
    """Eslatma matnini tuzadi."""

    parts = ["📋 Eslatma\n"]

    if missing_docs:

        parts.append("Quyidagi hujjatlar hali yuklanmagan:\n")

        for key in missing_docs:
            parts.append("  " + REQUIRED_TEACHER_DOCS[key])

        parts.append(
            "\nYuklash: «📂 Hujjatlar» → kerakli turni tanlang → «📤 Yuklash»\n"
        )

    if no_fee:

        parts.append(
            "\n💰 Quyidagi o'quvchilarga oylik badal summasi kiritilmagan:\n"
        )

        for student in no_fee[:10]:
            parts.append("  • " + student)

        if len(no_fee) > 10:
            parts.append("  ... va yana " + str(len(no_fee) - 10) + " ta")

        parts.append(
            "\nKiritish: «👨‍🎓 O'quvchilar ro'yxati» → o'quvchi → "
            "«✏️ Tahrirlash» → «Oylik badal»"
        )

    return "\n".join(parts)


def send_reminders(bot):
    """Bir marta tekshirib, kerakli o'qituvchilarga yuboradi."""

    sent = 0

    for name, telegram_id, missing_docs, no_fee in get_teachers_needing_reminder():

        try:

            bot.send_message(
                telegram_id,
                build_message(missing_docs, no_fee)
            )

            sent += 1

        except Exception:
            # foydalanuvchi botni bloklagan bo'lishi mumkin
            pass

    send_understaffed_reminder(bot)

    return sent


def build_understaffed_message(groups):
    """Meʼyordan kam guruhlar - admin uchun bitta xabar."""

    parts = ["👥 Meʼyordan kam guruhlar\n"]

    for g in groups:

        parts.append(
            "\n• " + g["subject"] + " · " + g["teacher"] + "\n"
            "  " + g["day"] + " " + g["time"] + " — "
            + str(g["count"]) + " ta (meʼyor: " + str(g["min"]) + "+)"
        )

    parts.append(
        "\n\nGuruhni boshqa bo'lim/sinf o'quvchilari bilan "
        "birlashtirish rejaning 5.2-bandiga muvofiq."
    )

    return "\n".join(parts)


def send_understaffed_reminder(bot):
    """Meʼyordan kam guruhlar bo'lsa - har bir adminga bitta xabar."""

    groups = get_understaffed_groups()

    if not groups:
        return

    text = build_understaffed_message(groups)

    for admin_id in ADMIN_IDS:

        try:
            bot.send_message(admin_id, text)
        except Exception:
            pass


def _loop(bot, stop_event):

    while not stop_event.is_set():

        now = datetime.now()

        today = now.strftime("%Y-%m-%d")

        if now.hour >= SEND_HOUR and get_setting(LAST_SENT_KEY) != today:

            try:

                count = send_reminders(bot)

                set_setting(LAST_SENT_KEY, today)

                print("📋 Kunlik eslatma yuborildi:", count, "ta o'qituvchiga")

            except Exception as e:

                print("❌ Kunlik eslatma xatosi:", e)

                traceback.print_exc()

        stop_event.wait(CHECK_INTERVAL_HOURS * 3600)


def start(bot):
    """Kunlik eslatma oqimini fonda ishga tushiradi."""

    stop_event = threading.Event()

    thread = threading.Thread(
        target=_loop,
        args=(bot, stop_event),
        daemon=True,
        name="daily-reminders"
    )

    thread.start()

    return stop_event
