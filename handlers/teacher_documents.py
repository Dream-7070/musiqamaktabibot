# ==========================
# handlers/teacher_documents.py
# O'QITUVCHI HUJJATLARI
# ==========================
#
# Fayllar VPS diskiga yozilmaydi.
# Telegramdan kelgan baytlar to'g'ridan-to'g'ri
# Google Drive ga uzatiladi.
#
# ==========================


from telebot import types

import os
import traceback

from data.teachers import teachers as TEACHERS_BY_DEPT

from services import gdrive

from database import (
    save_teacher_file,
    list_teacher_files,
    delete_teacher_file
)

from state import (
    user_state,
    TEACHER_DOCUMENTS
)


teacher_files = {}


teacher_document_types = {

    "🪪 Pasport": "pasport",
    "🎓 Diplom": "diplom",
    "🖼 Rasm": "rasm",
    "📜 Toifa sertifikati": "toifa",
    "📜 Malaka sertifikati": "malaka",

    "📅 Dars jadvali": "dars_jadvali",
    "📒 Sinf jurnali": "sinf_jurnali",
    "📊 Chorak hisoboti": "chorak_hisobot",

    "🌴 Mehnat ta'tili": "mehnat_tatili",
    "🤒 Kasallik ta'tili": "kasallik_tatili",
    "👶 Dekret": "dekret",
    "📚 O‘qish ta'tili": "oqish_tatili",
    "💰 Moddiy yordam": "moddiy_yordam",
    "📄 Boshqa ariza": "boshqa_ariza",

    "👨‍🏫 Ochiq darslar": "ochiq_darslar",
    "🎉 Tadbirlar": "tadbirlar",
    "🏆 Tanlovlar": "tanlovlar"
}


# ==========================
# O'QITUVCHI -> BO'LIM
# ==========================


def _department_map():

    mapping = {}

    for dept, names in TEACHERS_BY_DEPT.items():

        for name in names:
            mapping[name] = dept

    return mapping


DEPARTMENTS = _department_map()


def safe_name(name):
    """Drive papka nomi uchun xavfli belgilarni olib tashlaydi."""

    if not name:
        return "Nomalum"

    cleaned = str(name)

    for ch in ["/", "\\", ":", "*", "?", "\"", "<", ">", "|", "\n", "\r"]:
        cleaned = cleaned.replace(ch, " ")

    cleaned = " ".join(cleaned.split())

    return cleaned[:120] or "Nomalum"


def human_size(size):

    if not size:
        return ""

    if size < 1024 * 1024:
        return str(round(size / 1024)) + " KB"

    return str(round(size / 1024 / 1024, 1)) + " MB"


# ==========================
# REGISTER
# ==========================


def register_teacher_documents(bot, selected_teachers):


    @bot.message_handler(
        func=lambda m: m.text == "📂 Hujjatlar"
    )
    def documents_menu(message):

        teacher = selected_teachers.get(
            message.chat.id
        )

        if not teacher:

            bot.send_message(
                message.chat.id,
                "❌ Avval o‘qituvchini tanlang."
            )

            return


        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        for item in teacher_document_types:

            markup.add(
                types.KeyboardButton(item)
            )

        markup.add(
            types.KeyboardButton("⬅️ Ortga")
        )


        bot.send_message(
            message.chat.id,
            "📂 O‘qituvchi hujjatlari:",
            reply_markup=markup
        )


    @bot.message_handler(
        func=lambda m: m.text in teacher_document_types
    )
    def select_document(message):

        teacher = selected_teachers.get(
            message.chat.id
        )

        if not teacher:
            return


        doc_type = teacher_document_types[message.text]


        teacher_files[message.chat.id] = {
            "teacher": teacher,
            "doc": doc_type,
            "label": message.text,
            "files": []
        }


        user_state[message.chat.id] = TEACHER_DOCUMENTS


        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        for btn in [
            "📤 Yuklash",
            "📥 Yuklab olish",
            "🗑 O‘chirish",
            "⬅️ Ortga"
        ]:
            markup.add(
                types.KeyboardButton(btn)
            )


        existing = list_teacher_files(teacher, doc_type)


        bot.send_message(
            message.chat.id,
            "📄 " + message.text + "\n\n"
            "Saqlangan: " + str(len(existing)) + " ta fayl\n\n"
            "Amalni tanlang:",
            reply_markup=markup
        )


    @bot.message_handler(
        func=lambda m: m.text in [
            "📤 Yuklash",
            "📥 Yuklab olish",
            "🗑 O‘chirish"
        ]
    )
    def document_action(message):

        if user_state.get(message.chat.id) != TEACHER_DOCUMENTS:
            return


        data = teacher_files.get(
            message.chat.id
        )

        if not data:

            bot.send_message(
                message.chat.id,
                "❌ Hujjat turi tanlanmagan."
            )

            return


        teacher = data["teacher"]
        doc = data["doc"]


        # ==========================
        # YUKLASH
        # ==========================

        if message.text == "📤 Yuklash":

            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            markup.add(
                types.KeyboardButton("✅ Tugatish")
            )

            markup.add(
                types.KeyboardButton("⬅️ Ortga")
            )


            data["files"] = []


            bot.send_message(

                message.chat.id,

                "📎 Fayl yuboring.\n\n"
                "Rasm, PDF, Word, Excel qabul qilinadi.\n"
                "Bir nechta fayl yuborish mumkin.\n\n"
                "Tugatish uchun ✅ Tugatish bosing.",

                reply_markup=markup
            )


            bot.register_next_step_handler(
                message,
                receive_teacher_files
            )


        # ==========================
        # YUKLAB OLISH
        # ==========================

        elif message.text == "📥 Yuklab olish":

            files = list_teacher_files(teacher, doc)

            if not files:

                bot.send_message(
                    message.chat.id,
                    "❌ Fayl topilmadi."
                )

                return


            bot.send_message(
                message.chat.id,
                "📥 " + str(len(files)) + " ta fayl yuborilmoqda..."
            )


            for item in files:

                try:

                    # Avval Drive dan - asosiy manba

                    if item["drive_file_id"]:

                        content = gdrive.download_bytes(
                            item["drive_file_id"]
                        )

                        bot.send_document(
                            message.chat.id,
                            (item["file_name"] or "hujjat", content)
                        )

                    # Drive da yo'q bo'lsa - eski Telegram nusxasi

                    elif item["file_id"]:

                        bot.send_document(
                            message.chat.id,
                            item["file_id"]
                        )

                except Exception as e:

                    traceback.print_exc()

                    bot.send_message(
                        message.chat.id,
                        "⚠️ Yuborilmadi: "
                        + str(item["file_name"] or item["id"])
                    )


        # ==========================
        # O'CHIRISH
        # ==========================

        elif message.text == "🗑 O‘chirish":

            files = list_teacher_files(teacher, doc)

            if not files:

                bot.send_message(
                    message.chat.id,
                    "❌ O‘chiriladigan fayl yo‘q."
                )

                return


            markup = types.InlineKeyboardMarkup()

            for item in files:

                title = item["file_name"] or ("Fayl " + str(item["id"]))

                markup.add(
                    types.InlineKeyboardButton(
                        "🗑 " + title[:40],
                        callback_data="tdel:" + str(item["id"])
                    )
                )

            markup.add(
                types.InlineKeyboardButton(
                    "🗑 Hammasini o‘chirish (" + str(len(files)) + ")",
                    callback_data="tdelall:" + teacher + "|" + doc
                )
            )


            bot.send_message(
                message.chat.id,
                "🗑 Qaysi faylni o‘chiramiz?\n\n"
                "⚠️ O‘chirilgan fayl Drive korzinasida "
                "30 kun turadi.",
                reply_markup=markup
            )


    # ==========================
    # O'CHIRISH TASDIQI
    # ==========================


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tdel:")
    )
    def delete_one(call):

        row_id = int(call.data.split(":", 1)[1])

        doc = delete_teacher_file(row_id)

        if not doc:

            bot.answer_callback_query(
                call.id,
                "Topilmadi"
            )

            return


        if doc["drive_file_id"]:

            try:
                gdrive.delete_file(doc["drive_file_id"])

            except Exception:
                traceback.print_exc()


        bot.answer_callback_query(
            call.id,
            "🗑 O‘chirildi"
        )

        bot.edit_message_text(
            "🗑 O‘chirildi: "
            + str(doc["file_name"] or row_id),
            call.message.chat.id,
            call.message.message_id
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tdelall:")
    )
    def delete_all(call):

        payload = call.data.split(":", 1)[1]

        teacher, doc_type = payload.split("|", 1)

        files = list_teacher_files(teacher, doc_type)

        count = 0

        for item in files:

            delete_teacher_file(item["id"])

            if item["drive_file_id"]:

                try:
                    gdrive.delete_file(item["drive_file_id"])

                except Exception:
                    traceback.print_exc()

            count += 1


        bot.answer_callback_query(
            call.id,
            "🗑 " + str(count) + " ta o‘chirildi"
        )

        bot.edit_message_text(
            "🗑 " + str(count) + " ta fayl o‘chirildi.",
            call.message.chat.id,
            call.message.message_id
        )


    # ==========================
    # FAYL QABUL QILISH
    # ==========================


    def receive_teacher_files(message):

        data = teacher_files.get(
            message.chat.id
        )

        if not data:

            bot.send_message(
                message.chat.id,
                "❌ Yuklash bekor qilindi."
            )

            return


        # chiqish

        if message.text in ("⬅️ Ortga", "❌ Bekor"):

            bot.send_message(
                message.chat.id,
                "↩️ Bekor qilindi."
            )

            documents_menu(message)

            return


        if message.text in ("✅ Tugatish", "✅ Done"):

            bot.send_message(
                message.chat.id,
                "✅ " + str(len(data["files"]))
                + " ta fayl Google Drive ga saqlandi."
            )

            data["files"] = []

            documents_menu(message)

            return


        # ==========================
        # FAYLNI ANIQLASH
        # ==========================

        file_id = None
        original_name = None

        if message.photo:

            file_id = message.photo[-1].file_id

        elif message.document:

            file_id = message.document.file_id
            original_name = message.document.file_name

        elif message.video:

            file_id = message.video.file_id
            original_name = message.video.file_name


        if not file_id:

            bot.send_message(
                message.chat.id,
                "❌ Faqat rasm yoki hujjat yuboring."
            )

            bot.register_next_step_handler(
                message,
                receive_teacher_files
            )

            return


        # ==========================
        # TELEGRAM -> DRIVE
        # (diskka yozilmaydi)
        # ==========================

        try:

            info = bot.get_file(file_id)

            content = bot.download_file(info.file_path)


            ext = os.path.splitext(info.file_path)[1]

            if not ext:
                # Telegram fotosurat uchun kengaytma bermaydi -
                # tarkibga qarab aniqlaymiz
                ext = gdrive.detect_extension(content) or ".jpg"

            if original_name:
                filename = safe_name(original_name)

            else:
                filename = (
                    safe_name(data["teacher"]).replace(" ", "_")
                    + "_" + data["doc"]
                    + "_" + str(len(data["files"]) + 1)
                    + ext
                )


            dept = safe_name(
                DEPARTMENTS.get(data["teacher"], "Boshqa")
            )

            drive_id, link = gdrive.upload_bytes(
                content,
                filename,
                [
                    "O'qituvchilar",
                    dept,
                    safe_name(data["teacher"]),
                    data["doc"]
                ]
            )


            save_teacher_file(
                teacher=data["teacher"],
                department=dept,
                document_type=data["doc"],
                file_name=filename,
                file_size=len(content),
                drive_file_id=drive_id,
                drive_link=link,
                file_id=file_id
            )


            data["files"].append(filename)


            bot.send_message(
                message.chat.id,
                "✅ Saqlandi: " + filename
                + " (" + human_size(len(content)) + ")\n\n"
                "Yana yuboring yoki ✅ Tugatish bosing."
            )


        except Exception as e:

            traceback.print_exc()

            bot.send_message(
                message.chat.id,
                "❌ Saqlashda xato:\n" + str(e) + "\n\n"
                "Qayta urinib ko‘ring."
            )


        bot.register_next_step_handler(
            message,
            receive_teacher_files
        )
