# ==========================
# handlers/students.py
# O'QUVCHILAR TIZIMI
# ==========================


from telebot import types

import os
import time
import traceback


from database import (

    add_student,
    get_students,
    get_student_info,

    save_student_file,
    list_student_files,
    delete_student_file,

    MONTHLY_FEES,
    STUDENT_FIELDS,
    update_student_field

)


from services import gdrive


# papka nomi yordamchilari o'qituvchi modulida
from handlers.teacher_documents import (
    DEPARTMENTS,
    safe_name,
    human_size
)


from state import (

    user_state,
    STUDENT_DOCUMENTS

)



# ==========================
# XOTIRA
# ==========================


selected_students = {}

student_temp = {}

student_files = {}

# tahrirlash jarayonidagi vaqtinchalik holat
edit_temp = {}


def fee_text(amount):
    """123600 -> '123 600 so'm'"""

    if not amount:
        return "kiritilmagan"

    return "{:,}".format(int(amount)).replace(",", " ") + " so'm"




# ==========================
# PAPKA
# ==========================


# Fayllar diskka emas, Google Drive ga saqlanadi



# ==========================
# HUJJAT TURLARI
# ==========================


student_document_types = {


    "🪪 Tug'ilganlik guvohnomasi":
        "metrika_rasm",


    "🪪 Ota-ona pasporti":
        "ota_ona_pasport",


    "📝 O‘quvchi arizasi":
        "oquvchi_ariza",


    "🏥 Tibbiy ma'lumotnoma":
        "tibbiy_malumotnoma",


    "📄 Shartnoma":
        "shartnoma",


    "💳 Badal to‘lovi cheki":
        "badal_chek",


    "📝 Ota-ona arizasi":
        "ota_ona_ariza",


    "📑 Boshqa hujjatlar":
        "boshqa_hujjat"

}





# ==========================
# REGISTER
# ==========================


def register_students(bot, selected_teachers):


    # ==========================
    # O'QUVCHILAR RO'YXATI
    # ==========================


    @bot.message_handler(
        func=lambda m:
        m.text in [

            "👨‍🎓 O‘quvchilar ro‘yxati",
            "👨‍🎓 O'quvchilar ro'yxati"

        ]
    )
    def student_list(message):


        teacher = selected_teachers.get(
            message.chat.id
        )


        if not teacher:

            bot.send_message(

                message.chat.id,

                "❌ Avval o‘qituvchini tanlang"

            )

            return



        students = get_students(
            teacher
        )


        markup = types.ReplyKeyboardMarkup(

            resize_keyboard=True

        )


        for student in students:


            markup.add(

                types.KeyboardButton(student)

            )


        markup.add(

            types.KeyboardButton(
                "➕ O'quvchi qo'shish"
            )

        )


        markup.add(

            types.KeyboardButton(
                "⬅️ Ortga"
            )

        )


        bot.send_message(

            message.chat.id,

            "👨‍🎓 O‘quvchilar ro‘yxati:",

            reply_markup=markup

        )



    # ==========================
    # O'QUVCHI QO'SHISH
    # ==========================


    @bot.message_handler(
        func=lambda m:
        m.text == "➕ O'quvchi qo'shish"
    )
    def add_student_start(message):


        student_temp[message.chat.id] = {}


        bot.send_message(

            message.chat.id,

            "👤 O‘quvchi ism familiyasini yozing:"

        )


        bot.register_next_step_handler(

            message,

            student_name

        )



    def student_name(message):


        student_temp[message.chat.id]["name"] = message.text


        bot.send_message(

            message.chat.id,

            "📅 Tug‘ilgan sanani yozing:"

        )


        bot.register_next_step_handler(

            message,

            student_birth

        )



    def student_birth(message):


        student_temp[message.chat.id]["birth"] = message.text


        bot.send_message(

            message.chat.id,

            "🪪 Tug'ilganlik haqidagi guvohnoma raqamini yozing:\n\n"
            "Masalan: I-TV 0860700"

        )


        bot.register_next_step_handler(

            message,

            student_metrika

        )



    def student_metrika(message):


        student_temp[message.chat.id]["metrika"] = message.text


        bot.send_message(

            message.chat.id,

            "🏫 Sinfni yozing:"

        )


        bot.register_next_step_handler(

            message,

            student_class

        )



    def student_class(message):

        student_temp[message.chat.id]["class_name"] = message.text

        markup = types.InlineKeyboardMarkup()

        for index, fee in enumerate(MONTHLY_FEES):

            markup.add(
                types.InlineKeyboardButton(
                    fee_text(fee),
                    callback_data="newfee:" + str(index)
                )
            )

        bot.send_message(
            message.chat.id,
            "💰 Oylik badal summasini tanlang:",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("newfee:")
    )
    def save_new_student(call):

        chat_id = call.message.chat.id

        teacher = selected_teachers.get(chat_id)

        data = student_temp.get(chat_id)

        if not data or not teacher:

            bot.answer_callback_query(call.id, "Ma'lumot topilmadi")

            return

        index = int(call.data.split(":", 1)[1])

        if index >= len(MONTHLY_FEES):

            bot.answer_callback_query(call.id, "Summa topilmadi")

            return

        monthly_fee = MONTHLY_FEES[index]

        add_student(
            teacher,
            data["name"],
            data["birth"],
            data["metrika"],
            data["class_name"],
            monthly_fee
        )

        student_temp.pop(chat_id, None)

        bot.answer_callback_query(call.id, "✅ Saqlandi")

        bot.edit_message_text(
            "✅ O'quvchi saqlandi: " + data["name"]
            + "\n💰 Oylik badal: "
            + fee_text(monthly_fee),
            chat_id,
            call.message.message_id
        )


    # ==========================
    # O'QUVCHI TANLASH
    # ==========================


    @bot.message_handler(
        func=lambda m: (
            selected_teachers.get(m.chat.id) is not None
            and m.text in get_students(selected_teachers[m.chat.id])
        )
    )
    def select_student(message):


        selected_students[message.chat.id] = message.text



        markup = types.ReplyKeyboardMarkup(

            resize_keyboard=True

        )


        for btn in [

            "📋 Ma'lumot",

            "✏️ Tahrirlash",

            "📂 O‘quvchi hujjatlari",

            "🗑 O'quvchini o'chirish",

            "⬅️ Ortga"

        ]:


            markup.add(

                types.KeyboardButton(btn)

            )



        bot.send_message(

            message.chat.id,

            f"👨‍🎓 {message.text}\n\n"
            "O‘quvchi menyusi:",

            reply_markup=markup

        )





    # ==========================
    # O'QUVCHI MA'LUMOTI
    # ==========================


    @bot.message_handler(
        func=lambda m:
        m.text == "📋 Ma'lumot"
    )
    def student_info(message):


        teacher = selected_teachers.get(

            message.chat.id

        )


        student = selected_students.get(

            message.chat.id

        )


        if not teacher or not student:


            bot.send_message(

                message.chat.id,

                "❌ O‘quvchi tanlanmagan"

            )

            return



        data = get_student_info(

            student,

            teacher

        )



        if data:


            bot.send_message(

                message.chat.id,

                f"""
👨‍🎓 O‘quvchi ma'lumoti

F.I.Sh:
{data[2]}

📅 Tug‘ilgan sana:
{data[3]}

🪪 Tug‘ilganlik guvohnomasi:
{data[4]}

🏫 Sinf:
{data[5]}

💰 Oylik badal:
{data[6] or 0} so'm
"""

            )


        else:


            bot.send_message(

                message.chat.id,

                "❌ Ma'lumot topilmadi"

            )



    # Dars jadvali endi o'quvchi menyusida emas - o'qituvchining
    # bosh menyusida ("🗓 Dars jadvali", handlers/teacher_schedule.py),
    # chunki bitta vaqt katakchasiga boshqa o'qituvchining
    # o'quvchisi ham qo'shilishi mumkin.


    # ==========================
    # O'QUVCHINI TAHRIRLASH
    # ==========================
    #
    # Ilgari qo'shilgan o'quvchilarda badal summasi yo'q edi -
    # shu tugma orqali to'ldiriladi. Boshqa maydonlarni ham
    # tuzatish mumkin.
    # ==========================


    @bot.message_handler(
        func=lambda m: m.text == "✏️ Tahrirlash"
    )
    def edit_student_menu(message):

        teacher = selected_teachers.get(message.chat.id)

        student = selected_students.get(message.chat.id)

        if not teacher or not student:

            bot.send_message(message.chat.id, "❌ O‘quvchi tanlanmagan")

            return

        _show_edit_menu(message.chat.id, teacher, student)


    def _show_edit_menu(chat_id, teacher, student):

        data = get_student_info(student, teacher)

        if not data:

            bot.send_message(chat_id, "❌ Ma'lumot topilmadi")

            return

        current = {
            "student":     data[2],
            "birth_date":  data[3],
            "metrika":     data[4],
            "class_name":  data[5],
            "monthly_fee": data[6] if len(data) > 6 else 0
        }

        markup = types.InlineKeyboardMarkup()

        for field, label in STUDENT_FIELDS.items():

            value = current.get(field)

            shown = fee_text(value) if field == "monthly_fee" else (value or "—")

            markup.add(
                types.InlineKeyboardButton(
                    label + ": " + str(shown)[:28],
                    callback_data="edf:" + field
                )
            )

        bot.send_message(
            chat_id,
            "✏️ " + student + "\n\nQaysi maydonni o'zgartiramiz?",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("edf:")
    )
    def edit_field_chosen(call):

        chat_id = call.message.chat.id

        teacher = selected_teachers.get(chat_id)

        student = selected_students.get(chat_id)

        if not teacher or not student:

            bot.answer_callback_query(call.id, "O‘quvchi tanlanmagan")

            return

        field = call.data.split(":", 1)[1]

        if field not in STUDENT_FIELDS:

            bot.answer_callback_query(call.id, "Noto‘g‘ri maydon")

            return

        edit_temp[chat_id] = {
            "teacher": teacher,
            "student": student,
            "field": field
        }

        bot.answer_callback_query(call.id)


        # badal - tayyor summalardan tanlanadi

        if field == "monthly_fee":

            markup = types.InlineKeyboardMarkup()

            for index, fee in enumerate(MONTHLY_FEES):

                markup.add(
                    types.InlineKeyboardButton(
                        fee_text(fee),
                        callback_data="edfee:" + str(index)
                    )
                )

            bot.send_message(
                chat_id,
                "💰 Yangi badal summasini tanlang:",
                reply_markup=markup
            )

            return


        sent = bot.send_message(
            chat_id,
            "✏️ Yangi qiymatni yozing — " + STUDENT_FIELDS[field] + ":"
        )

        bot.register_next_step_handler(sent, edit_field_save)


    def edit_field_save(message):

        chat_id = message.chat.id

        data = edit_temp.pop(chat_id, None)

        if not data:

            bot.send_message(chat_id, "❌ Xatolik. Qaytadan boshlang.")

            return

        value = (message.text or "").strip()

        if not value:

            bot.send_message(chat_id, "❌ Bo‘sh qiymat. Qaytadan boshlang.")

            return

        update_student_field(data["teacher"], data["student"], data["field"], value)

        # ism o'zgargan bo'lsa - tanlangan o'quvchini yangilaymiz

        if data["field"] == "student":
            selected_students[chat_id] = value

        bot.send_message(
            chat_id,
            "✅ " + STUDENT_FIELDS[data["field"]] + " yangilandi: " + value
        )

        _show_edit_menu(chat_id, data["teacher"], selected_students[chat_id])


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("edfee:")
    )
    def edit_fee_save(call):

        chat_id = call.message.chat.id

        data = edit_temp.pop(chat_id, None)

        if not data:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        index = int(call.data.split(":", 1)[1])

        if index >= len(MONTHLY_FEES):

            bot.answer_callback_query(call.id, "Summa topilmadi")

            return

        fee = MONTHLY_FEES[index]

        update_student_field(data["teacher"], data["student"], "monthly_fee", fee)

        bot.answer_callback_query(call.id, "✅ Saqlandi")

        bot.edit_message_text(
            "✅ Oylik badal yangilandi: " + fee_text(fee),
            chat_id,
            call.message.message_id
        )


    # ==========================
    # HUJJATLAR MENYUSI
    # ==========================


    @bot.message_handler(
        func=lambda m:
        m.text == "📂 O‘quvchi hujjatlari"
    )
    def student_documents(message):


        user_state[message.chat.id] = STUDENT_DOCUMENTS



        markup = types.ReplyKeyboardMarkup(

            resize_keyboard=True

        )


        for doc in student_document_types:


            markup.add(

                types.KeyboardButton(doc)

            )


        markup.add(

            types.KeyboardButton(
                "⬅️ Ortga"
            )

        )


        bot.send_message(

            message.chat.id,

            "📂 O‘quvchi hujjatlari:",

            reply_markup=markup

        )
            # ==========================
    # HUJJAT TANLASH
    # ==========================


    @bot.message_handler(
        func=lambda m:
        m.text in student_document_types
    )
    def select_document(message):


        teacher = selected_teachers.get(

            message.chat.id

        )


        student = selected_students.get(

            message.chat.id

        )


        if not teacher or not student:


            bot.send_message(

                message.chat.id,

                "❌ Avval o‘quvchini tanlang"

            )

            return



        student_files[message.chat.id] = {


            "teacher": teacher,

            "student": student,

            "doc": student_document_types[message.text],

            "files": []

        }



        user_state[message.chat.id] = STUDENT_DOCUMENTS



        markup = types.ReplyKeyboardMarkup(

            resize_keyboard=True

        )


        for btn in [


            "📤 O‘quvchi yuklash",

            "📥 O‘quvchi yuklab olish",

            "🗑 O‘quvchi o‘chirish",

            "⬅️ Ortga"


        ]:


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
        func=lambda m:
        m.text in [

            "📤 O‘quvchi yuklash",

            "📥 O‘quvchi yuklab olish",

            "🗑 O‘quvchi o‘chirish"

        ]
    )
    def document_action(message):


        if user_state.get(message.chat.id) != STUDENT_DOCUMENTS:

            return


        data = student_files.get(
            message.chat.id
        )


        if not data:

            bot.send_message(
                message.chat.id,
                "❌ Hujjat turi tanlanmagan"
            )

            return


        teacher = data["teacher"]
        student = data["student"]
        doc = data["doc"]


        # ==========================
        # YUKLASH
        # ==========================

        if message.text == "📤 O‘quvchi yuklash":

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
                receive_student_files
            )


        # ==========================
        # YUKLAB OLISH
        # ==========================

        elif message.text == "📥 O‘quvchi yuklab olish":

            files = list_student_files(
                teacher,
                student,
                doc
            )


            if not files:

                bot.send_message(
                    message.chat.id,
                    "❌ Fayl topilmadi"
                )

                return


            bot.send_message(
                message.chat.id,
                "📥 " + str(len(files)) + " ta fayl yuborilmoqda..."
            )


            for item in files:

                try:

                    if item["drive_file_id"]:

                        content = gdrive.download_bytes(
                            item["drive_file_id"]
                        )

                        bot.send_document(
                            message.chat.id,
                            (item["file_name"] or "hujjat", content)
                        )

                    elif item["file_id"]:

                        bot.send_document(
                            message.chat.id,
                            item["file_id"]
                        )

                except Exception:

                    traceback.print_exc()

                    bot.send_message(
                        message.chat.id,
                        "⚠️ Yuborilmadi: "
                        + str(item["file_name"] or item["id"])
                    )


        # ==========================
        # O'CHIRISH
        # ==========================

        elif message.text == "🗑 O‘quvchi o‘chirish":

            files = list_student_files(
                teacher,
                student,
                doc
            )


            if not files:

                bot.send_message(
                    message.chat.id,
                    "❌ O‘chiriladigan fayl yo‘q"
                )

                return


            markup = types.InlineKeyboardMarkup()

            for item in files:

                title = item["file_name"] or ("Fayl " + str(item["id"]))

                markup.add(
                    types.InlineKeyboardButton(
                        "🗑 " + title[:40],
                        callback_data="sdel:" + str(item["id"])
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
        func=lambda c: c.data.startswith("sdel:")
    )
    def delete_student_one(call):

        row_id = int(call.data.split(":", 1)[1])

        doc = delete_student_file(row_id)


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
            "🗑 O‘chirildi: " + str(doc["file_name"] or row_id),
            call.message.chat.id,
            call.message.message_id
        )


    # ==========================
    # FAYL QABUL QILISH
    # ==========================


    def receive_student_files(message):

        data = student_files.get(
            message.chat.id
        )


        if not data:

            bot.send_message(
                message.chat.id,
                "❌ Yuklash bekor qilindi"
            )

            return


        if message.text in ("⬅️ Ortga", "❌ Bekor"):

            bot.send_message(
                message.chat.id,
                "↩️ Bekor qilindi."
            )

            student_documents(message)

            return


        if message.text in ("✅ Tugatish", "✅ Done"):

            bot.send_message(
                message.chat.id,
                "✅ " + str(len(data["files"]))
                + " ta fayl Google Drive ga saqlandi."
            )

            data["files"] = []

            student_documents(message)

            return


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
                receive_student_files
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
                    safe_name(data["student"]).replace(" ", "_")
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
                    "O'quvchilar",
                    dept,
                    safe_name(data["teacher"]),
                    safe_name(data["student"]),
                    data["doc"]
                ]
            )


            save_student_file(
                teacher=data["teacher"],
                department=dept,
                student=data["student"],
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
            receive_student_files
        )
