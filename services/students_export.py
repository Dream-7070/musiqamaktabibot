# ==========================
# services/students_export.py
# O'QUVCHILAR RO'YXATINI EXCEL QILIB YUBORISH
# ==========================
#
# Bir joyda turadi, chunki bir nechta joydan chaqiriladi:
# admin panelidan ham, direktor menyusidan ham.
#
# ==========================


import traceback

from datetime import datetime

from database import get_students_report_rows

from services.reports import build_students_report


def send_students_excel(bot, chat_id):
    """Faylni tayyorlab, chatga yuboradi. Xatoni foydalanuvchiga aytadi."""

    try:

        rows = get_students_report_rows()

    except Exception:

        traceback.print_exc()

        bot.send_message(chat_id, "❌ Ma'lumotni o'qishda xatolik.")

        return


    if not rows:

        bot.send_message(chat_id, "❌ O'quvchi yo'q")

        return

    notice = bot.send_message(chat_id, "📊 Ro'yxat tayyorlanmoqda...")

    try:

        buffer, filename = build_students_report(rows)

    except Exception:

        traceback.print_exc()

        bot.edit_message_text(
            "❌ Faylni tayyorlashda xatolik.",
            chat_id,
            notice.message_id
        )

        return


    # sana fayl nomida bo'lsa, bir nechta nusxa aralashib ketmaydi

    stamped = filename.replace(
        ".xlsx",
        "_" + datetime.now().strftime("%Y-%m-%d") + ".xlsx"
    )

    buffer.name = stamped

    bot.send_document(
        chat_id,
        buffer,
        visible_file_name=stamped,
        caption=(
            "👨‍🎓 O'quvchilar ro'yxati — " + str(len(rows)) + " ta\n\n"
            "Tartib: bo'lim → sinf → alifbo\n"
            "Sariq bilan belgilanganlar: sinfi yoki guvohnoma "
            "raqami to'g'ri kiritilmagan."
        )
    )

    try:
        bot.delete_message(chat_id, notice.message_id)

    except Exception:
        # xabarni o'chirib bo'lmasa ham fayl yetib bordi
        pass
