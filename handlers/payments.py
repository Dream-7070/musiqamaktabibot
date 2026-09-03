# ==========================
# PAYMENTS HANDLER
# ==========================

from telebot import types

from database import (
    get_parent,
    get_parent_students,
    get_student_payments
)



def register_payments(bot):


    # ==========================
    # OTA-ONA TO'LOVLARI
    # ==========================

    @bot.message_handler(
        func=lambda message:
        message.text == "💳 To'lovlar"
    )
    def payment_start(message):


        parent = get_parent(
            message.chat.id
        )


        if not parent:

            bot.send_message(
                message.chat.id,
                "❌ Ro'yxatdan o'tmagansiz"
            )

            return



        children = get_parent_students(
            parent[0]
        )


        if not children:

            bot.send_message(
                message.chat.id,
                "❌ Farzand ulanmagan"
            )

            return



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
            show_payment
        )





    # ==========================
    # TO'LOV TARIXI
    # ==========================

    def show_payment(message):


        parent = get_parent(
            message.chat.id
        )


        children = get_parent_students(
            parent[0]
        )


        for teacher, student in children:


            if student == message.text:


                payments = get_student_payments(
                    teacher,
                    student
                )


                if not payments:


                    bot.send_message(
                        message.chat.id,
                        "❌ To'lovlar topilmadi"
                    )

                    return



                text = (
                    f"💳 {student} "
                    "to'lovlari:\n\n"
                )


                for month, status, date in payments:


                    text += (
                        f"📅 {month}\n"
                        f"Holat: {status}\n"
                        f"Sana: {date}\n\n"
                    )



                bot.send_message(
                    message.chat.id,
                    text
                )


                return