# ==========================
# PARENTS HANDLER
# ==========================
#
# Ota-ona farzandini ro'yxatdan TANLAMAYDI - bu xavfsiz emas
# edi (istalgan kishi istalgan bolani "o'zimniki" deb bog'lab
# olardi). Buning o'rniga tug'ilganlik guvohnomasidagi ITV
# raqamini kiritadi - bu raqamni faqat hujjat egasi biladi,
# shuning uchun tasodifiy kishi boshqa bolaga "ega chiqa" olmaydi.
#
# Bir nechta farzand: har safar bitta ITV kiritiladi, so'ng
# "Yana farzand qo'shish" so'raladi - xohlagancha takrorlanadi.
#
# ==========================

from telebot import types

from database import (
    add_parent,
    get_parent,
    get_parent_students,
    link_parent_student,
    find_students_by_metrika,
    get_parent_student_document
)


parent_data = {}


def register_parents(bot):


    # ==========================
    # /parent
    # ==========================

    @bot.message_handler(commands=["parent"])
    def parent_start(message):

        parent = get_parent(message.chat.id)

        if parent:

            show_parent_menu(message)

            return

        bot.send_message(
            message.chat.id,
            "👋 Xush kelibsiz!\n\n👤 Ismingizni yozing:"
        )

        bot.register_next_step_handler(message, save_parent_name)


    def save_parent_name(message):

        parent_data[message.chat.id] = {"name": message.text}

        bot.send_message(
            message.chat.id,
            "📱 Telefon raqamingizni yozing:"
        )

        bot.register_next_step_handler(message, save_parent_phone)


    def save_parent_phone(message):

        data = parent_data.get(message.chat.id)

        add_parent(message.chat.id, data["name"], message.text)

        bot.send_message(message.chat.id, "✅ Ro'yxatdan o'tdingiz")

        ask_metrika(message)


    # ==========================
    # FARZANDNI ITV ORQALI TOPISH
    # ==========================

    def ask_metrika(message):

        bot.send_message(
            message.chat.id,
            "👨‍🎓 Farzandingizning tug'ilganlik guvohnomasidagi "
            "ITV (yoki shunga o'xshash) raqamini kiriting:\n\n"
            "Masalan: I-TV 0860700"
        )

        bot.register_next_step_handler(message, receive_metrika)


    def receive_metrika(message):

        matches = find_students_by_metrika(message.text)

        if not matches:

            bot.send_message(
                message.chat.id,
                "❌ Bunday raqamli o'quvchi topilmadi.\n"
                "Qaytadan urinib ko'ring, yoki maktab bilan bog'laning."
            )

            bot.register_next_step_handler(message, receive_metrika)

            return

        if len(matches) > 1:

            # kamdan-kam holat: bir nechta yozuvda bir xil raqam

            markup = types.InlineKeyboardMarkup()

            for index, (teacher, student) in enumerate(matches):

                markup.add(
                    types.InlineKeyboardButton(
                        student + " (" + teacher + ")",
                        callback_data="plink:" + str(index)
                    )
                )

            parent_data[message.chat.id] = {"matches": matches}

            bot.send_message(
                message.chat.id,
                "Bir nechta mos yozuv topildi, to'g'risini tanlang:",
                reply_markup=markup
            )

            return

        _link_child(message.chat.id, matches[0])

        ask_add_another(message.chat.id)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("plink:")
    )
    def pick_match(call):

        chat_id = call.message.chat.id

        data = parent_data.get(chat_id)

        if not data or "matches" not in data:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        index = int(call.data.split(":", 1)[1])

        matches = data["matches"]

        if index >= len(matches):

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        bot.answer_callback_query(call.id)

        _link_child(chat_id, matches[index])

        ask_add_another(chat_id)


    def _link_child(chat_id, match):

        teacher, student = match

        parent = get_parent(chat_id)

        existing = get_parent_students(parent[0])

        if (teacher, student) in existing:

            bot.send_message(
                chat_id,
                "ℹ️ " + student + " allaqachon bog'langan."
            )

            return

        link_parent_student(parent[0], teacher, student)

        bot.send_message(
            chat_id,
            "✅ Farzandingiz topildi: " + student + " (" + teacher + ")\n"
            "Bog'landi!"
        )


    def ask_add_another(chat_id):

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "➕ Yana farzand qo'shish",
                callback_data="paddmore"
            ),
            types.InlineKeyboardButton(
                "✅ Tayyor",
                callback_data="pdone"
            )
        )

        bot.send_message(
            chat_id,
            "Yana farzand qo'shmoqchimisiz?",
            reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data == "paddmore")
    def add_more(call):

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "👨‍🎓 Yana bitta farzandning ITV raqamini kiriting:"
        )

        bot.register_next_step_handler(call.message, receive_metrika)


    @bot.callback_query_handler(func=lambda c: c.data == "pdone")
    def finish_adding(call):

        bot.answer_callback_query(call.id)

        show_parent_menu(call.message)


    # ==========================
    # MENU
    # ==========================

    def show_parent_menu(message):

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        buttons = [
            "👤 Farzandim",
            "➕ Farzand qo'shish",
            "📄 Hujjatlar",
            "💳 To'lovlar",
            "📢 E'lonlar"
        ]

        for btn in buttons:
            markup.add(types.KeyboardButton(btn))

        # Mini App kiritish maydoni yonidagi doimiy tugma orqali
        # ochiladi (main.py da global sozlangan)

        bot.send_message(
            message.chat.id,
            "👨‍👩‍👦 Ota-ona paneli:",
            reply_markup=markup
        )


    @bot.message_handler(
        func=lambda message: message.text == "➕ Farzand qo'shish"
    )
    def add_child_button(message):

        if not get_parent(message.chat.id):

            bot.send_message(message.chat.id, "❌ Avval /parent orqali ro'yxatdan o'ting.")

            return

        ask_metrika(message)


    # ==========================
    # CHILD INFO
    # ==========================

    @bot.message_handler(
        func=lambda message: message.text == "👤 Farzandim"
    )
    def child_info(message):

        parent = get_parent(message.chat.id)

        if not parent:
            return

        children = get_parent_students(parent[0])

        if not children:

            bot.send_message(message.chat.id, "❌ Farzand ulanmagan")

            return

        text = "👤 Farzandlar:\n\n"

        for teacher, student in children:

            text += "👨‍🎓 " + student + "\n👨‍🏫 " + teacher + "\n\n"

        bot.send_message(message.chat.id, text)


    # ==========================
    # DOCUMENTS
    # ==========================

    @bot.message_handler(
        func=lambda message: message.text == "📄 Hujjatlar"
    )
    def documents(message):

        parent = get_parent(message.chat.id)

        if not parent:
            return

        children = get_parent_students(parent[0])

        if not children:

            bot.send_message(message.chat.id, "❌ Farzand ulanmagan")

            return

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        for teacher, student in children:

            markup.add(types.KeyboardButton(student))

        bot.send_message(
            message.chat.id,
            "👨‍🎓 Farzandni tanlang:",
            reply_markup=markup
        )

        bot.register_next_step_handler(message, document_child)


    def document_child(message):

        parent = get_parent(message.chat.id)

        children = get_parent_students(parent[0])

        for teacher, student in children:

            if student == message.text:

                parent_data[message.chat.id] = {
                    "teacher": teacher,
                    "student": student
                }

                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

                markup.add(types.KeyboardButton("💳 Badal cheki"))
                markup.add(types.KeyboardButton("📄 Ota-ona arizasi"))

                bot.send_message(
                    message.chat.id,
                    "📂 Hujjat tanlang:",
                    reply_markup=markup
                )

                return


    # ==========================
    # BADAL / ARIZA
    # ==========================

    @bot.message_handler(
        func=lambda message: message.text == "💳 Badal cheki"
    )
    def badal(message):

        send_document(message, "badal")


    @bot.message_handler(
        func=lambda message: message.text == "📄 Ota-ona arizasi"
    )
    def ariza(message):

        send_document(message, "ariza")


    def send_document(message, doc_type):

        data = parent_data.get(message.chat.id)

        if not data or "teacher" not in data:

            bot.send_message(message.chat.id, "❌ Farzand tanlanmagan")

            return

        file_id = get_parent_student_document(
            data["teacher"], data["student"], doc_type
        )

        if file_id:

            bot.send_document(message.chat.id, file_id)

        else:

            bot.send_message(message.chat.id, "❌ Hujjat topilmadi")
