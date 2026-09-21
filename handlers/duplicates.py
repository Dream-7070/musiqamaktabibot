# -*- coding: utf-8 -*-
# ==========================
# handlers/duplicates.py
# DUBLIKAT O'QUVCHINI HAL QILISH
# ==========================
#
# Bitta bola bir o'qituvchida ikki marta yozilgan bo'lsa,
# kunlik eslatma (services/daily_reminders.py) unga tugmali
# xabar yuboradi. Javobi shu yerda qabul qilinadi.
#
# Qaysi yozuv to'g'riligini bazadan bilib bo'lmaydi - sinf ham,
# badal ham har xil bo'lishi mumkin. Buni faqat o'qituvchi
# biladi, shuning uchun tanlov unga qoldirilgan.
#
# ==========================


import traceback

from database import (
    get_approved_teacher_accounts,
    find_duplicate_group,
    archive_student_by_id,
    ignore_duplicate_group
)


ARCHIVE_REASON = "Dublikat - o'qituvchi tanlovi"


def teacher_name_by_telegram(telegram_id):
    """Tugmani bosgan odam qaysi o'qituvchi - shuni aniqlaydi."""

    for name, tid in get_approved_teacher_accounts():

        if str(tid) == str(telegram_id):
            return name

    return None


def close_message(bot, call, text):
    """Xabarni yakuniy matn bilan almashtiradi, tugmalarni oladi."""

    try:

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=None
        )

    except Exception:
        # xabar o'chirilgan yoki juda eski bo'lishi mumkin
        pass


def register_duplicates(bot):

    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("dup:keep:")
    )
    def duplicate_keep(call):
        """Bitta yozuv qoldiriladi, qolganlari arxivga."""

        try:

            parts = call.data.split(":")

            gid = parts[2]

            keep_id = int(parts[3])

            teacher = teacher_name_by_telegram(call.from_user.id)

            if not teacher:

                bot.answer_callback_query(
                    call.id,
                    "Sizning o'qituvchi hisobingiz topilmadi.",
                    show_alert=True
                )

                return

            # Guruh o'qituvchining O'ZI bo'yicha qidiriladi -
            # begona odam tugmani bossa, hech narsa topilmaydi.

            group = find_duplicate_group(teacher, gid)

            if not group:

                bot.answer_callback_query(call.id, "Bu allaqachon hal qilingan")

                close_message(bot, call, "✅ Bu allaqachon hal qilingan")

                return

            qoldi = None

            for sid, student, class_name, fee in group["students"]:

                if sid == keep_id:
                    qoldi = (student, class_name)

                else:
                    archive_student_by_id(sid, ARCHIVE_REASON)

            if qoldi:

                matn = (
                    "✅ Saqlandi: " + qoldi[0] + " · "
                    + str(qoldi[1]) + "-sinf\n\n"
                    "Qolgan nusxalar arxivga olindi."
                )

            else:
                # tanlangan yozuv orada arxivlangan bo'lsa

                matn = "✅ Hal qilindi"

            close_message(bot, call, matn)

            bot.answer_callback_query(call.id)

        except Exception:

            traceback.print_exc()

            bot.answer_callback_query(call.id, "Xatolik yuz berdi")


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("dup:both:")
    )
    def duplicate_both(call):
        """Bola chindan ikki fan bo'yicha o'qiydi - tegilmaydi."""

        try:

            gid = call.data.split(":")[2]

            teacher = teacher_name_by_telegram(call.from_user.id)

            if not teacher:

                bot.answer_callback_query(
                    call.id,
                    "Sizning o'qituvchi hisobingiz topilmadi.",
                    show_alert=True
                )

                return

            if not find_duplicate_group(teacher, gid):

                bot.answer_callback_query(call.id, "Bu allaqachon hal qilingan")

                close_message(bot, call, "✅ Bu allaqachon hal qilingan")

                return

            ignore_duplicate_group(gid)

            close_message(
                bot, call,
                "✅ Ikkalasi ham qoldirildi.\n\n"
                "Bu o'quvchi haqida boshqa so'ralmaydi."
            )

            bot.answer_callback_query(call.id)

        except Exception:

            traceback.print_exc()

            bot.answer_callback_query(call.id, "Xatolik yuz berdi")
