# -*- coding: utf-8 -*-
# ==========================
# handlers/school_documents.py
# MAKTABNING UMUMIY HUJJATLARI
# ==========================
#
# Ish rejasi, kadastr, guvohnoma, INN, maktab pasporti, nizom.
# Bular biror odamga emas, maktabning o'ziga tegishli.
#
# Bu bo'limga bir nechta rol kiradi: admin, direktor, yordamchi
# va xo'jalik mudiri - hammasi ham ko'radi, ham yuklaydi.
# ==========================


import os

from telebot import types

from database import (
    get_staff_role,
    log_action,
    SCHOOL_DOCUMENT_TYPES,
    save_school_document,
    list_school_documents,
    get_school_missing_documents,
)

from services import gdrive


BUTTON = "🏫 Maktab hujjatlari"


# Shu rollar kiradi. Admin alohida tekshiriladi (u `staff`
# jadvalida bo'lmasligi mumkin).

ALLOWED_ROLES = ("direktor", "yordamchi", "xojalik_mudiri")


# chat_id -> {"doc": tur}
ctx = {}


def _size(num):
    """102400 -> '100 KB'"""

    try:
        num = int(num or 0)
    except (TypeError, ValueError):
        return "?"

    if num >= 1024 * 1024:
        return str(round(num / 1024 / 1024, 1)) + " MB"

    return str(max(1, num // 1024)) + " KB"


def register_school_documents(bot, admin_ids):

    def _allowed(chat_id):

        return chat_id in admin_ids or get_staff_role(chat_id) in ALLOWED_ROLES


    @bot.message_handler(func=lambda m: m.text == BUTTON)
    def open_section(message):

        chat_id = message.chat.id

        if not _allowed(chat_id):

            bot.send_message(
                chat_id,
                "❌ Bu bo'lim rahbariyat va xo'jalik mudiri uchun."
            )

            return

        show_types(chat_id)


    def show_types(chat_id, message_id=None):

        yetishmayotgan = {key for _, key in get_school_missing_documents()}

        markup = types.InlineKeyboardMarkup()

        for label, key in SCHOOL_DOCUMENT_TYPES.items():

            soni = len(list_school_documents(key))

            belgi = "⚠️ " if key in yetishmayotgan else "✅ "

            suffix = "" if not soni else " (" + str(soni) + " ta)"

            markup.add(
                types.InlineKeyboardButton(
                    belgi + label + suffix,
                    callback_data="sd:t:" + key
                )
            )

        text = (
            "🏫 Maktab hujjatlari\n\n"
            "Turni bosing: yuklangan fayllarni ko'rasiz yoki yangisini "
            "qo'shasiz.\n\n"
            "⚠️ - hali yuklanmagan."
        )

        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(func=lambda c: c.data.startswith("sd:t:"))
    def show_one_type(call):

        chat_id = call.message.chat.id

        if not _allowed(chat_id):

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        key = call.data[len("sd:t:"):]

        label = next(
            (lbl for lbl, k in SCHOOL_DOCUMENT_TYPES.items() if k == key),
            key
        )

        rows = list_school_documents(key)

        text = label + "\n\n"

        if rows:

            for _rid, _t, name, size, link, at in rows:

                text += "📎 " + (name or "fayl") + " · " + _size(size)

                if at:
                    text += " · " + str(at)[:16]

                if link:
                    text += "\n" + link

                text += "\n\n"

        else:
            text += "Hali fayl yuklanmagan.\n\n"

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "📤 Fayl yuklash",
                callback_data="sd:up:" + key
            )
        )

        markup.add(
            types.InlineKeyboardButton("‹ Orqaga", callback_data="sd:back")
        )

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            text.strip(), chat_id, call.message.message_id, reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data == "sd:back")
    def back(call):

        bot.answer_callback_query(call.id)

        show_types(call.message.chat.id, call.message.message_id)


    # Admin bu bo'limga «🔍 Hujjat qidirish» ichidan kiradi -
    # o'sha yerda o'qituvchi va o'quvchi hujjatlari ham turadi,
    # ya'ni hamma hujjat bitta joyda.

    @bot.callback_query_handler(func=lambda c: c.data == "sd:open")
    def open_from_search(call):

        chat_id = call.message.chat.id

        if not _allowed(chat_id):

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        bot.answer_callback_query(call.id)

        show_types(chat_id, call.message.message_id)


    @bot.callback_query_handler(func=lambda c: c.data.startswith("sd:up:"))
    def wait_file(call):

        chat_id = call.message.chat.id

        if not _allowed(chat_id):

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        ctx[chat_id] = {"doc": call.data[len("sd:up:"):]}

        bot.answer_callback_query(call.id)

        bot.send_message(
            chat_id,
            "📤 Faylni yuboring (rasm yoki hujjat).\n\n"
            "Bekor qilish uchun /cancel yozing."
        )


    @bot.message_handler(
        content_types=["document", "photo"],
        func=lambda m: ctx.get(m.chat.id, {}).get("doc") is not None
    )
    def receive_file(message):

        chat_id = message.chat.id

        data = ctx.get(chat_id)

        if not data:
            return

        key = data["doc"]

        if message.content_type == "photo":
            file_id = message.photo[-1].file_id
            original_name = None
        else:
            file_id = message.document.file_id
            original_name = message.document.file_name

        wait_msg = bot.send_message(chat_id, "⏳ Drive'ga yuklanmoqda...")

        try:

            info = bot.get_file(file_id)

            content = bot.download_file(info.file_path)

            ext = os.path.splitext(info.file_path)[1]

            if not ext:
                ext = gdrive.detect_extension(content) or ".jpg"

            filename = original_name or (key + ext)

            drive_id, link = gdrive.upload_bytes(
                content,
                filename,
                ["Maktab hujjatlari", key]
            )

            save_school_document(
                document_type=key,
                file_name=filename,
                file_size=len(content),
                drive_file_id=drive_id,
                drive_link=link,
                file_id=file_id,
                uploaded_by=chat_id
            )

            log_action(
                str(get_staff_role(chat_id) or "admin"),
                "maktab hujjatini yukladi", key, filename
            )

            bot.edit_message_text("✅ Yuklandi.", chat_id, wait_msg.message_id)

        except Exception as error:

            bot.edit_message_text(
                "❌ Yuklab bo'lmadi: " + str(error)[:200],
                chat_id,
                wait_msg.message_id
            )

            return

        finally:
            ctx.pop(chat_id, None)

        show_types(chat_id)
