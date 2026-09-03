# ==========================
# handlers/documents.py
# 1-QISM
# ==========================

from telebot import types

import os
import re
import uuid

from database import (
    save_document,
    get_documents,
    delete_document
)

from state import (
    user_state,
    TEACHER_DOCUMENTS
)

# ==========================
# VAQTINCHALIK XOTIRA
# ==========================

teacher_files = {}

# ==========================
# HUJJAT TURLARI
# ==========================

teacher_document_types = {

    # SHAXSIY HUJJATLAR

    "🪪 Pasport": "pasport",
    "🎓 Diplom": "diplom",
    "📜 Toifa sertifikati": "toifa",
    "📜 Malaka sertifikati": "malaka",

    # PEDAGOGIK HUJJATLAR

    "📅 Dars jadvali": "dars_jadvali",
    "📒 Sinf jurnali": "sinf_jurnali",
    "📊 Chorak hisoboti": "chorak_hisobot",

    # ARIZALAR

    "🌴 Mehnat ta'tili": "mehnat_tatili",
    "🤒 Kasallik ta'tili": "kasallik_tatili",
    "👶 Dekret arizasi": "dekret",
    "📚 O‘qish ta'tili": "oqish_tatili",
    "💰 Moddiy yordam": "moddiy_yordam",
    "📄 Boshqa arizalar": "boshqa_ariza",

    # RASMLAR

    "👨‍🏫 Ochiq darslar": "ochiq_darslar",
    "🎉 Tadbirlar": "tadbirlar",
    "🏆 Tanlovlar": "tanlovlar"

}

# ==========================
# REGISTER
# ==========================

def register_documents(bot, selected_teachers):

    # ==========================
    # ASOSIY MENYU
    # ==========================

    @bot.message_handler(
        func=lambda m: m.text == "📂 Hujjatlar"
    )
    def documents_menu(message):

        teacher = selected_teachers.get(message.chat.id)

        if not teacher:
            bot.send_message(
                message.chat.id,
                "❌ Avval o‘qituvchini tanlang."
            )
            return

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        buttons = [

            "🪪 Pasport",
            "🎓 Diplom",
            "📜 Toifa sertifikati",
            "📜 Malaka sertifikati",

            "📅 Dars jadvali",
            "📒 Sinf jurnali",
            "📊 Chorak hisoboti",

            "📝 Arizalar",
            "🖼 Rasmlar",

            "⬅️ Ortga"

        ]

        for btn in buttons:
            markup.add(
                types.KeyboardButton(btn)
            )

        bot.send_message(
            message.chat.id,
            "📂 O‘qituvchi hujjatlari:",
            reply_markup=markup
        )
            # ==========================
    # ARIZALAR MENYUSI
    # ==========================

    @bot.message_handler(
        func=lambda m: m.text == "📝 Arizalar"
    )
    def applications_menu(message):

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        buttons = [

            "🌴 Mehnat ta'tili",
            "🤒 Kasallik ta'tili",
            "👶 Dekret arizasi",
            "📚 O‘qish ta'tili",
            "💰 Moddiy yordam",
            "📄 Boshqa arizalar",

            "⬅️ Ortga"

        ]

        for btn in buttons:
            markup.add(
                types.KeyboardButton(btn)
            )

        bot.send_message(
            message.chat.id,
            "📝 Arizalar bo‘limi:",
            reply_markup=markup
        )


    # ==========================
    # RASMLAR MENYUSI
    # ==========================

    @bot.message_handler(
        func=lambda m: m.text == "🖼 Rasmlar"
    )
    def photos_menu(message):

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        buttons = [

            "👨‍🏫 Ochiq darslar",
            "🎉 Tadbirlar",
            "🏆 Tanlovlar",

            "⬅️ Ortga"

        ]

        for btn in buttons:
            markup.add(
                types.KeyboardButton(btn)
            )

        bot.send_message(
            message.chat.id,
            "🖼 Rasmlar bo‘limi:",
            reply_markup=markup
        )
            # ==========================
    # HUJJAT TANLASH
    # ==========================

    @bot.message_handler(
        func=lambda m: m.text in teacher_document_types
    )
    def select_document(message):

        teacher = selected_teachers.get(
            message.chat.id
        )

        if not teacher:

            bot.send_message(
                message.chat.id,
                "❌ Avval o‘qituvchini tanlang."
            )
            return

        doc = teacher_document_types[
            message.text
        ]

        teacher_files[message.chat.id] = {

            "teacher": teacher,
            "doc": doc,
            "files": []

        }

        user_state[
            message.chat.id
        ] = TEACHER_DOCUMENTS

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        buttons = [

            "📤 Yuklash",
            "📥 Yuklab olish",
            "🗑 O‘chirish",

            "⬅️ Ortga"

        ]

        for btn in buttons:

            markup.add(
                types.KeyboardButton(btn)
            )

        bot.send_message(

            message.chat.id,

            f"📄 {message.text}\n\n"
            "Amalni tanlang:",

            reply_markup=markup

        )
            # ==========================
    # HUJJAT AMALLARI
    # ==========================

    @bot.message_handler(
        func=lambda m: m.text in [
            "📤 Yuklash",
            "📥 Yuklab olish",
            "🗑 O‘chirish"
        ]
    )
    def document_actions(message):
        
        print("DOCUMENT ACTION ISHLADI")

        if user_state.get(message.chat.id) != TEACHER_DOCUMENTS:
            return

        data = teacher_files.get(message.chat.id)

        if not data:
            bot.send_message(
                message.chat.id,
                "❌ Avval hujjat turini tanlang."
            )
            return

        teacher = data["teacher"]
        doc = data["doc"]

        # ======================
        # YUKLASH
        # ======================

        if message.text == "📤 Yuklash":

            bot.send_message(

                message.chat.id,

                "📎 Fayl yuboring.\n\n"
                "Rasm, PDF, Word, Excel qabul qilinadi.\n"
                "Bir nechta fayl yuborishingiz mumkin.\n\n"
                "Tugatish uchun /done yozing."

            )

            bot.register_next_step_handler(
                message,
                receive_teacher_files
            )

        # ======================
        # YUKLAB OLISH
        # ======================

        elif message.text == "📥 Yuklab olish":

            files = get_documents(
                teacher,
                doc
            )

            if not files:

                bot.send_message(
                    message.chat.id,
                    "❌ Fayl topilmadi."
                )
                return

            for file_id in files:

                bot.send_document(
                    message.chat.id,
                    file_id
                )

        # ======================
        # O‘CHIRISH
        # ======================

        elif message.text == "🗑 O‘chirish":

            delete_document(
                teacher,
                doc
            )

            bot.send_message(
                message.chat.id,
                "✅ Hujjatlar o‘chirildi."
            )
            # ==========================
# FAYLNI QABUL QILISH
# ==========================

def receive_teacher_files(message):

    data = teacher_files.get(message.chat.id)

    if not data:
        bot.send_message(
            message.chat.id,
            "❌ Yuklash jarayoni topilmadi."
        )
        return

    # Tugatish
    if getattr(message, "text", "") == "/done":

        for file_id in data["files"]:
            save_document(
                data["teacher"],
                data["doc"],
                file_id
            )

        bot.send_message(
            message.chat.id,
            f"✅ {len(data['files'])} ta fayl saqlandi."
        )

        teacher_files.pop(message.chat.id, None)
        return

    file_id = None

    # Rasm
    if message.photo:
        file_id = message.photo[-1].file_id

    # Hujjat
    elif message.document:
        file_id = message.document.file_id

    if file_id:

        data["files"].append(file_id)

        bot.send_message(
            message.chat.id,
            "✅ Fayl qabul qilindi.\n"
            "Yana fayl yuboring yoki /done yozing."
        )

        bot.register_next_step_handler(
            message,
            receive_teacher_files
        )

    else:

        bot.send_message(
            message.chat.id,
            "❌ Rasm yoki hujjat yuboring."
        )

        bot.register_next_step_handler(
            message,
            receive_teacher_files
        )