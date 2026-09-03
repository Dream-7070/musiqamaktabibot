# ==========================
# PARENTS HANDLER
# ==========================

from telebot import types

from database import (
    add_parent,
    get_parent,
    get_parent_students,
    link_parent_student,
    get_all_students,
    get_parent_student_document
)


parent_data = {}





def register_parents(bot):


    # ==========================
    # /parent
    # ==========================

    @bot.message_handler(commands=["parent"])
    def parent_start(message):


        parent = get_parent(
            message.chat.id
        )


        if parent:

            show_parent_menu(
                message
            )

            return



        bot.send_message(
            message.chat.id,
            "👤 Ismingizni yozing:"
        )


        bot.register_next_step_handler(
            message,
            save_parent_name
        )





    # ==========================
    # NAME
    # ==========================

    def save_parent_name(message):


        parent_data[
            message.chat.id
        ] = {

            "name": message.text

        }


        bot.send_message(
            message.chat.id,
            "📱 Telefon raqamingizni yozing:"
        )


        bot.register_next_step_handler(
            message,
            save_parent_phone
        )





    # ==========================
    # PHONE
    # ==========================

    def save_parent_phone(message):


        data = parent_data.get(
            message.chat.id
        )


        add_parent(

            message.chat.id,

            data["name"],

            message.text

        )


        bot.send_message(
            message.chat.id,
            "✅ Ro'yxatdan o'tdingiz"
        )


        choose_child(
            message
        )





    # ==========================
    # CHILD SELECT
    # ==========================

    def choose_child(message):


        students = get_all_students()


        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )


        for teacher, student in students:


            markup.add(
                types.KeyboardButton(
                    student
                )
            )


        bot.send_message(
            message.chat.id,
            "👨‍🎓 Farzandingizni tanlang:",
            reply_markup=markup
        )





    @bot.message_handler(
        func=lambda message:
        get_parent(message.chat.id)
    )
    def select_child(message):


        students = get_all_students()


        parent = get_parent(
            message.chat.id
        )


        for teacher, student in students:


            if message.text == student:


                link_parent_student(

                    parent[0],

                    teacher,

                    student

                )


                bot.send_message(
                    message.chat.id,
                    "✅ Farzand bog'landi"
                )


                show_parent_menu(
                    message
                )


                return





    # ==========================
    # MENU
    # ==========================

    def show_parent_menu(message):


        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )


        buttons = [

            "👤 Farzandim",

            "📄 Hujjatlar",

            "💳 To'lovlar",

            "📢 E'lonlar"

        ]


        for btn in buttons:

            markup.add(
                types.KeyboardButton(btn)
            )


        bot.send_message(
            message.chat.id,
            "👨‍👩‍👦 Ota-ona paneli:",
            reply_markup=markup
        )





    # ==========================
    # CHILD INFO
    # ==========================

    @bot.message_handler(
        func=lambda message:
        message.text == "👤 Farzandim"
    )
    def child_info(message):


        parent = get_parent(
            message.chat.id
        )


        children = get_parent_students(
            parent[0]
        )


        if not children:

            bot.send_message(
                message.chat.id,
                "❌ Farzand ulanmagan"
            )

            return


        text = "👤 Farzandlar:\n\n"


        for teacher, student in children:


            text += (
                f"👨‍🎓 {student}\n"
                f"👨‍🏫 {teacher}\n\n"
            )


        bot.send_message(
            message.chat.id,
            text
        )





    # ==========================
    # DOCUMENTS
    # ==========================

    @bot.message_handler(
        func=lambda message:
        message.text == "📄 Hujjatlar"
    )
    def documents(message):


        parent = get_parent(
            message.chat.id
        )


        children = get_parent_students(
            parent[0]
        )


        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )


        for teacher, student in children:


            markup.add(
                types.KeyboardButton(
                    student
                )
            )


        bot.send_message(
            message.chat.id,
            "👨‍🎓 Farzandni tanlang:",
            reply_markup=markup
        )


        bot.register_next_step_handler(
            message,
            document_child
        )





    def document_child(message):


        parent = get_parent(
            message.chat.id
        )


        children = get_parent_students(
            parent[0]
        )


        for teacher, student in children:


            if student == message.text:


                parent_data[
                    message.chat.id
                ] = {

                    "teacher": teacher,

                    "student": student

                }


                markup = types.ReplyKeyboardMarkup(
                    resize_keyboard=True
                )


                markup.add(
                    types.KeyboardButton(
                        "💳 Badal cheki"
                    )
                )


                markup.add(
                    types.KeyboardButton(
                        "📄 Ota-ona arizasi"
                    )
                )


                bot.send_message(
                    message.chat.id,
                    "📂 Hujjat tanlang:",
                    reply_markup=markup
                )

                return





    # ==========================
    # BADAL
    # ==========================

    @bot.message_handler(
        func=lambda message:
        message.text == "💳 Badal cheki"
    )
    def badal(message):

        send_document(
            message,
            "badal"
        )





    # ==========================
    # ARIZA
    # ==========================

    @bot.message_handler(
        func=lambda message:
        message.text == "📄 Ota-ona arizasi"
    )
    def ariza(message):

        send_document(
            message,
            "ariza"
        )





    def send_document(message, doc_type):


        data = parent_data.get(
            message.chat.id
        )


        if not data:

            bot.send_message(
                message.chat.id,
                "❌ Farzand tanlanmagan"
            )

            return



        file_id = get_parent_student_document(

            data["teacher"],

            data["student"],

            doc_type

        )


        if file_id:


            bot.send_document(
                message.chat.id,
                file_id
            )

        else:

            bot.send_message(
                message.chat.id,
                "❌ Hujjat topilmadi"
            )