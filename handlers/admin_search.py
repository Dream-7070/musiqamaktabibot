# ==========================
# handlers/admin_search.py
# ADMIN - HUJJAT QIDIRISH
# ==========================
#
# Bo'lim -> O'qituvchi -> (O'qituvchi/O'quvchi hujjati) ->
# Hujjat turi -> Fayl -> Yuklab olish
#
# Barcha bosqichlar tugma orqali, yozish shart emas.
#
# ==========================


from telebot import types

from config import ADMIN_IDS

from database import (
    get_departments,
    get_teachers_by_department,
    get_teacher_by_id,
    get_students,
    list_teacher_files,
    get_teacher_file,
    list_student_files,
    get_student_file
)

from handlers.teacher_documents import teacher_document_types
from handlers.students import student_document_types

from services import gdrive


def register_admin_search(bot):


    def _is_admin(chat_id):
        return chat_id in ADMIN_IDS


    # ==========================
    # KIRISH
    # ==========================

    @bot.message_handler(
        func=lambda m:
        m.text == "🔍 Hujjat qidirish"
        and m.chat.id in ADMIN_IDS
    )
    def search_start(message):

        _show_departments(
            message.chat.id,
            edit=None
        )


    def _show_departments(chat_id, edit):

        markup = types.InlineKeyboardMarkup()

        for index, dept in enumerate(get_departments()):

            markup.add(
                types.InlineKeyboardButton(
                    dept,
                    callback_data="sdoc:dept:" + str(index)
                )
            )

        text = "🔍 Qaysi bo'limda qidiramiz?"

        if edit:

            bot.edit_message_text(
                text,
                edit[0],
                edit[1],
                reply_markup=markup
            )

        else:

            bot.send_message(
                chat_id,
                text,
                reply_markup=markup
            )


    # ==========================
    # DISPATCHER
    # ==========================

    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("sdoc:")
        and c.message.chat.id in ADMIN_IDS
    )
    def dispatch(call):

        chat_id = call.message.chat.id

        message_id = call.message.message_id

        parts = call.data.split(":")

        step = parts[1]

        args = parts[2:]

        bot.answer_callback_query(call.id)


        # ---- bo'lim tanlandi -> o'qituvchilar ----

        if step == "dept":

            dept_index = int(args[0])

            departments = get_departments()

            if dept_index >= len(departments):

                bot.answer_callback_query(call.id, "Bo'lim topilmadi")

                return

            dept = departments[dept_index]

            teachers = get_teachers_by_department(dept)

            markup = types.InlineKeyboardMarkup()

            for teacher_id, name, status in teachers:

                label = ("🔒 " if status == "approved" else "") + name

                markup.add(
                    types.InlineKeyboardButton(
                        label,
                        callback_data="sdoc:teacher:" + str(teacher_id) + ":" + str(dept_index)
                    )
                )

            markup.add(
                types.InlineKeyboardButton(
                    "⬅️ Bo'limlar",
                    callback_data="sdoc:deptlist"
                )
            )

            bot.edit_message_text(
                "📂 " + dept + "\n\nO'qituvchini tanlang:",
                chat_id,
                message_id,
                reply_markup=markup
            )


        # ---- bo'limlar ro'yxatiga qaytish ----

        elif step == "deptlist":

            _show_departments(chat_id, edit=(chat_id, message_id))


        # ---- o'qituvchi tanlandi -> rejim ----

        elif step == "teacher":

            teacher_id, dept_index = args

            row = get_teacher_by_id(int(teacher_id))

            if not row:

                bot.answer_callback_query(call.id, "Topilmadi")

                return

            name = row[1]

            markup = types.InlineKeyboardMarkup()

            markup.add(
                types.InlineKeyboardButton(
                    "👨‍🏫 O'qituvchi hujjatlari",
                    callback_data="sdoc:mode:" + teacher_id + ":" + dept_index + ":t"
                )
            )

            markup.add(
                types.InlineKeyboardButton(
                    "👨‍🎓 O'quvchi hujjatlari",
                    callback_data="sdoc:mode:" + teacher_id + ":" + dept_index + ":s"
                )
            )

            markup.add(
                types.InlineKeyboardButton(
                    "⬅️ Orqaga",
                    callback_data="sdoc:dept:" + dept_index
                )
            )

            bot.edit_message_text(
                "👨‍🏫 " + name + "\n\nQaysi hujjatlarni ko'ramiz?",
                chat_id,
                message_id,
                reply_markup=markup
            )


        # ---- rejim tanlandi ----

        elif step == "mode":

            teacher_id, dept_index, mode = args

            row = get_teacher_by_id(int(teacher_id))

            if not row:

                bot.answer_callback_query(call.id, "Topilmadi")

                return

            name = row[1]


            if mode == "t":

                markup = types.InlineKeyboardMarkup()

                for label, key in teacher_document_types.items():

                    markup.add(
                        types.InlineKeyboardButton(
                            label,
                            callback_data="sdoc:type_t:" + teacher_id + ":" + dept_index + ":" + key
                        )
                    )

                markup.add(
                    types.InlineKeyboardButton(
                        "⬅️ Orqaga",
                        callback_data="sdoc:teacher:" + teacher_id + ":" + dept_index
                    )
                )

                bot.edit_message_text(
                    "👨‍🏫 " + name + "\n\nHujjat turini tanlang:",
                    chat_id,
                    message_id,
                    reply_markup=markup
                )


            else:

                students = get_students(name)

                if not students:

                    bot.answer_callback_query(call.id, "O'quvchi yo'q")

                    return

                markup = types.InlineKeyboardMarkup()

                for index, student in enumerate(students):

                    markup.add(
                        types.InlineKeyboardButton(
                            student,
                            callback_data="sdoc:student:" + teacher_id + ":" + dept_index + ":" + str(index)
                        )
                    )

                markup.add(
                    types.InlineKeyboardButton(
                        "⬅️ Orqaga",
                        callback_data="sdoc:teacher:" + teacher_id + ":" + dept_index
                    )
                )

                bot.edit_message_text(
                    "👨‍🎓 " + name + "\n\nO'quvchini tanlang:",
                    chat_id,
                    message_id,
                    reply_markup=markup
                )


        # ---- o'qituvchi hujjat turi tanlandi -> fayllar ----

        elif step == "type_t":

            teacher_id, dept_index, doc_key = args

            row = get_teacher_by_id(int(teacher_id))

            name = row[1]

            files = list_teacher_files(name, doc_key)

            markup = types.InlineKeyboardMarkup()

            if not files:

                markup.add(
                    types.InlineKeyboardButton(
                        "⬅️ Orqaga",
                        callback_data="sdoc:mode:" + teacher_id + ":" + dept_index + ":t"
                    )
                )

                bot.edit_message_text(
                    "❌ Bu turda fayl topilmadi.",
                    chat_id,
                    message_id,
                    reply_markup=markup
                )

                return

            for item in files:

                title = item["file_name"] or ("Fayl " + str(item["id"]))

                markup.add(
                    types.InlineKeyboardButton(
                        "📥 " + title[:45],
                        callback_data="sdoc:file_t:" + str(item["id"])
                    )
                )

            markup.add(
                types.InlineKeyboardButton(
                    "⬅️ Orqaga",
                    callback_data="sdoc:mode:" + teacher_id + ":" + dept_index + ":t"
                )
            )

            bot.edit_message_text(
                "📄 " + name + "\n\nYuklab olish uchun faylni tanlang:",
                chat_id,
                message_id,
                reply_markup=markup
            )


        # ---- o'quvchi tanlandi -> hujjat turi ----

        elif step == "student":

            teacher_id, dept_index, student_index = args

            row = get_teacher_by_id(int(teacher_id))

            name = row[1]

            students = get_students(name)

            student_index = int(student_index)

            if student_index >= len(students):

                bot.answer_callback_query(call.id, "O'quvchi topilmadi")

                return

            student = students[student_index]

            markup = types.InlineKeyboardMarkup()

            for label, key in student_document_types.items():

                markup.add(
                    types.InlineKeyboardButton(
                        label,
                        callback_data=(
                            "sdoc:type_s:" + teacher_id + ":" + dept_index
                            + ":" + str(student_index) + ":" + key
                        )
                    )
                )

            markup.add(
                types.InlineKeyboardButton(
                    "⬅️ Orqaga",
                    callback_data="sdoc:mode:" + teacher_id + ":" + dept_index + ":s"
                )
            )

            bot.edit_message_text(
                "👨‍🎓 " + student + "\n\nHujjat turini tanlang:",
                chat_id,
                message_id,
                reply_markup=markup
            )


        # ---- o'quvchi hujjat turi tanlandi -> fayllar ----

        elif step == "type_s":

            teacher_id, dept_index, student_index, doc_key = args

            row = get_teacher_by_id(int(teacher_id))

            name = row[1]

            students = get_students(name)

            student_index = int(student_index)

            student = students[student_index]

            files = list_student_files(name, student, doc_key)

            markup = types.InlineKeyboardMarkup()

            if not files:

                markup.add(
                    types.InlineKeyboardButton(
                        "⬅️ Orqaga",
                        callback_data=(
                            "sdoc:student:" + teacher_id + ":" + dept_index
                            + ":" + str(student_index)
                        )
                    )
                )

                bot.edit_message_text(
                    "❌ Bu turda fayl topilmadi.",
                    chat_id,
                    message_id,
                    reply_markup=markup
                )

                return

            for item in files:

                title = item["file_name"] or ("Fayl " + str(item["id"]))

                markup.add(
                    types.InlineKeyboardButton(
                        "📥 " + title[:45],
                        callback_data="sdoc:file_s:" + str(item["id"])
                    )
                )

            markup.add(
                types.InlineKeyboardButton(
                    "⬅️ Orqaga",
                    callback_data=(
                        "sdoc:student:" + teacher_id + ":" + dept_index
                        + ":" + str(student_index)
                    )
                )
            )

            bot.edit_message_text(
                "📄 " + student + "\n\nYuklab olish uchun faylni tanlang:",
                chat_id,
                message_id,
                reply_markup=markup
            )


        # ---- fayl tanlandi -> yuborish ----

        elif step in ("file_t", "file_s"):

            row_id = int(args[0])

            doc = (
                get_teacher_file(row_id)
                if step == "file_t"
                else get_student_file(row_id)
            )

            if not doc:

                bot.answer_callback_query(call.id, "Fayl topilmadi")

                return

            try:

                if doc["drive_file_id"]:

                    content = gdrive.download_bytes(doc["drive_file_id"])

                    bot.send_document(
                        chat_id,
                        (doc["file_name"] or "hujjat", content)
                    )

                elif doc["file_id"]:

                    bot.send_document(
                        chat_id,
                        doc["file_id"]
                    )

                else:

                    bot.send_message(
                        chat_id,
                        "❌ Fayl manbasi topilmadi."
                    )

            except Exception as e:

                bot.send_message(
                    chat_id,
                    "❌ Yuborishda xato: " + str(e)
                )
