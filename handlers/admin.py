from telebot import types

from config import ADMIN_IDS

from datetime import datetime

from database import (
    add_teacher,
    get_all_teachers,
    delete_teacher,
    connect,
    get_departments,
    teacher_exists,
    get_teachers_by_department,
    rename_teacher,
    move_teacher_department,
    get_monthly_debt_rows
)

from services.reports import build_debt_report
from handlers.admin_search import register_admin_search
from handlers.admin_schedule import register_admin_schedule
from handlers.admin_staff import register_admin_staff


admin_data = {}


def register_admin(bot):


    def admin_menu(message):

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        buttons = [
            "👨‍🏫 O'qituvchilar",
            "👨‍🎓 O'quvchilar",
            "👥 Xodimlar",
            "👨‍🏫 O'qituvchi rejimi",
            "🔍 Hujjat qidirish",
            "🗓 Dars jadvallari",
            "📊 Oylik hisobot (Excel)",
            "📊 Statistika"
        ]

        for btn in buttons:
            markup.add(
                types.KeyboardButton(btn)
            )

        # Mini App kiritish maydoni yonidagi doimiy tugma orqali
        # ochiladi (main.py da global sozlangan)

        bot.send_message(
            message.chat.id,
            "🔐 Admin panel",
            reply_markup=markup
        )


    @bot.message_handler(commands=["admin"])
    def admin_start(message):

        if message.chat.id not in ADMIN_IDS:

            bot.send_message(
                message.chat.id,
                "❌ Ruxsat yo'q"
            )
            return

        admin_menu(message)



    @bot.message_handler(
        func=lambda m:
        m.text == "👨‍🏫 O'qituvchilar"
        and m.chat.id in ADMIN_IDS
    )
    def teachers_menu(message):

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        buttons = [
            "➕ O'qituvchi qo'shish",
            "📋 O'qituvchilar ro'yxati",
            "✏️ O'qituvchi tahrirlash",
            "🗑 O'qituvchi o'chirish",
            "⬅️ Ortga"
        ]

        for btn in buttons:
            markup.add(
                types.KeyboardButton(btn)
            )

        bot.send_message(
            message.chat.id,
            "👨‍🏫 O'qituvchilar boshqaruvi:",
            reply_markup=markup
        )



    @bot.message_handler(
        func=lambda m:
        m.text == "📋 O'qituvchilar ro'yxati"
        and m.chat.id in ADMIN_IDS
    )
    def teacher_list(message):

        data = get_all_teachers()

        if not data:

            bot.send_message(
                message.chat.id,
                "❌ O'qituvchi yo'q"
            )
            return


        text = "👨‍🏫 O'qituvchilar:\n\n"

        for name, dep in data:

            text += (
                f"👤 {name}\n"
                f"📂 {dep}\n\n"
            )


        bot.send_message(
            message.chat.id,
            text
        )



    @bot.message_handler(
        func=lambda m:
        m.text == "➕ O'qituvchi qo'shish"
        and m.chat.id in ADMIN_IDS
    )
    def add_teacher_start(message):

        bot.send_message(
            message.chat.id,
            "👨‍🏫 O'qituvchi ism familiyasini yozing:"
        )

        bot.register_next_step_handler(
            message,
            teacher_name
        )


    def teacher_name(message):

        admin_data[message.chat.id] = message.text.strip()

        markup = types.InlineKeyboardMarkup()

        for index, dept in enumerate(get_departments()):

            markup.add(
                types.InlineKeyboardButton(
                    dept,
                    callback_data="adddept:" + str(index)
                )
            )

        bot.send_message(
            message.chat.id,
            "📂 Qaysi bo'limga qo'shamiz?",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("adddept:")
        and c.message.chat.id in ADMIN_IDS
    )
    def save_teacher(call):

        name = admin_data.pop(call.message.chat.id, None)

        if not name:

            bot.answer_callback_query(call.id, "Ism topilmadi, qaytadan boshlang")

            return

        index = int(call.data.split(":", 1)[1])

        departments = get_departments()

        if index >= len(departments):

            bot.answer_callback_query(call.id, "Bo'lim topilmadi")

            return

        dept = departments[index]

        if teacher_exists(name, dept):

            bot.answer_callback_query(call.id, "⚠️ Bu o'qituvchi allaqachon mavjud")

            bot.edit_message_text(
                "⚠️ " + name + " (" + dept + ") allaqachon mavjud",
                call.message.chat.id,
                call.message.message_id
            )

            return

        add_teacher(name, dept)

        bot.answer_callback_query(call.id, "✅ Qo'shildi")

        bot.edit_message_text(
            "✅ Qo'shildi: " + name + " (" + dept + ")",
            call.message.chat.id,
            call.message.message_id
        )


            # ==========================
    # DELETE TEACHER
    # ==========================

    @bot.message_handler(
        func=lambda m:
        m.text == "🗑 O'qituvchi o'chirish"
        and m.chat.id in ADMIN_IDS
    )
    def delete_teacher_start(message):

        bot.send_message(
            message.chat.id,
            "O'chiriladigan o'qituvchi ismini yozing:"
        )

        bot.register_next_step_handler(
            message,
            delete_teacher_save
        )


    def delete_teacher_save(message):

        delete_teacher(
            message.text
        )

        bot.send_message(
            message.chat.id,
            "🗑 O'qituvchi o'chirildi"
        )



    # ==========================
    # EDIT TEACHER
    # ==========================

    @bot.message_handler(
        func=lambda m:
        m.text == "✏️ O'qituvchi tahrirlash"
        and m.chat.id in ADMIN_IDS
    )
    def edit_teacher_start(message):

        markup = types.InlineKeyboardMarkup()

        for index, dept in enumerate(get_departments()):

            markup.add(
                types.InlineKeyboardButton(
                    dept,
                    callback_data="editdept:" + str(index)
                )
            )

        bot.send_message(
            message.chat.id,
            "📂 Qaysi bo'limdagi o'qituvchini tahrirlaymiz?",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("editdept:")
        and c.message.chat.id in ADMIN_IDS
    )
    def edit_teacher_dept_picked(call):

        index = int(call.data.split(":", 1)[1])

        departments = get_departments()

        if index >= len(departments):

            bot.answer_callback_query(call.id, "Bo'lim topilmadi")

            return

        dept = departments[index]

        teachers = get_teachers_by_department(dept)

        if not teachers:

            bot.answer_callback_query(call.id, "Bu bo'limda o'qituvchi yo'q")

            return

        markup = types.InlineKeyboardMarkup()

        for teacher_id, name, status in teachers:

            label = name

            if status == "approved":
                label = "🔒 " + name

            markup.add(
                types.InlineKeyboardButton(
                    label,
                    callback_data="editpick:" + str(teacher_id)
                )
            )

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            "👨‍🏫 " + dept + "\n\nTahrirlanadigan o'qituvchini tanlang:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("editpick:")
        and c.message.chat.id in ADMIN_IDS
    )
    def edit_teacher_picked(call):

        teacher_id = int(call.data.split(":", 1)[1])

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "✏️ Ism-familiyani o'zgartirish",
                callback_data="editname:" + str(teacher_id)
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "📂 Bo'limini o'zgartirish",
                callback_data="editmove:" + str(teacher_id)
            )
        )

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            "Nimani tahrirlaymiz?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )


    # ==========================
    # ISM-FAMILIYANI O'ZGARTIRISH
    # ==========================

    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("editname:")
        and c.message.chat.id in ADMIN_IDS
    )
    def edit_teacher_name_start(call):

        teacher_id = int(call.data.split(":", 1)[1])

        admin_data[
            str(call.message.chat.id) + "_edit_id"
        ] = teacher_id

        bot.answer_callback_query(call.id)

        sent = bot.send_message(
            call.message.chat.id,
            "✏️ Yangi ism-familiyani yozing:"
        )

        bot.register_next_step_handler(
            sent,
            edit_teacher_save
        )


    def edit_teacher_save(message):

        teacher_id = admin_data.pop(
            str(message.chat.id) + "_edit_id",
            None
        )

        if not teacher_id:

            bot.send_message(
                message.chat.id,
                "❌ Xatolik yuz berdi. Qaytadan boshlang."
            )

            return

        new_name = message.text.strip()

        old_name = rename_teacher(teacher_id, new_name)

        if not old_name:

            bot.send_message(
                message.chat.id,
                "❌ O'qituvchi topilmadi."
            )

            return

        bot.send_message(
            message.chat.id,
            "✅ Yangilandi: " + old_name + " → " + new_name
        )


    # ==========================
    # BO'LIMINI O'ZGARTIRISH
    # ==========================

    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("editmove:")
        and c.message.chat.id in ADMIN_IDS
    )
    def edit_teacher_move_start(call):

        teacher_id = int(call.data.split(":", 1)[1])

        markup = types.InlineKeyboardMarkup()

        for index, dept in enumerate(get_departments()):

            markup.add(
                types.InlineKeyboardButton(
                    dept,
                    callback_data="editmoveto:" + str(teacher_id) + ":" + str(index)
                )
            )

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            "📂 Yangi bo'limni tanlang:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("editmoveto:")
        and c.message.chat.id in ADMIN_IDS
    )
    def edit_teacher_move_save(call):

        _, teacher_id, index = call.data.split(":")

        teacher_id = int(teacher_id)

        departments = get_departments()

        index = int(index)

        if index >= len(departments):

            bot.answer_callback_query(call.id, "Bo'lim topilmadi")

            return

        new_department = departments[index]

        result = move_teacher_department(teacher_id, new_department)

        if result is None:

            bot.answer_callback_query(call.id, "O'qituvchi topilmadi")

            return

        if result == "exists":

            bot.answer_callback_query(
                call.id,
                "⚠️ Bu bo'limda shu ism allaqachon bor"
            )

            return

        name, old_department = result

        bot.answer_callback_query(call.id, "✅ Ko'chirildi")

        bot.edit_message_text(
            "✅ " + name + ": " + old_department + " → " + new_department,
            call.message.chat.id,
            call.message.message_id
        )



    # ==========================
    # STUDENTS MENU
    # ==========================

    @bot.message_handler(
        func=lambda m:
        m.text == "👨‍🎓 O'quvchilar"
        and m.chat.id in ADMIN_IDS
    )
    def students_menu(message):

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )


        buttons = [
            "➕ O'quvchi qo'shish",
            "📋 O'quvchilar ro'yxati",
            "⬅️ Ortga"
        ]


        for btn in buttons:

            markup.add(
                types.KeyboardButton(btn)
            )


        bot.send_message(
            message.chat.id,
            "👨‍🎓 O'quvchilar boshqaruvi:",
            reply_markup=markup
        )



    # ==========================
    # STUDENT LIST
    # ==========================

    @bot.message_handler(
        func=lambda m:
        m.text == "📋 O'quvchilar ro'yxati"
        and m.chat.id in ADMIN_IDS
    )
    def student_list(message):

        from database import get_all_students


        data = get_all_students()


        if not data:

            bot.send_message(
                message.chat.id,
                "❌ O'quvchi yo'q"
            )

            return


        text = "👨‍🎓 O'quvchilar:\n\n"


        for teacher, student in data:

            text += (
                f"👤 {student}\n"
                f"👨‍🏫 {teacher}\n\n"
            )


        bot.send_message(
            message.chat.id,
            text
        )
            # ==========================
    # ADD STUDENT
    # ==========================

    @bot.message_handler(
        func=lambda m:
        m.text == "➕ O'quvchi qo'shish"
        and m.chat.id in ADMIN_IDS
    )
    def add_student_start(message):

        admin_data[
            message.chat.id
        ] = {}


        bot.send_message(
            message.chat.id,
            "👨‍🏫 O'qituvchi ismini yozing:"
        )


        bot.register_next_step_handler(
            message,
            student_teacher
        )



    def student_teacher(message):

        admin_data[
            message.chat.id
        ]["teacher"] = message.text


        bot.send_message(
            message.chat.id,
            "👤 O'quvchi ism familiyasini yozing:"
        )


        bot.register_next_step_handler(
            message,
            student_name
        )



    def student_name(message):

        admin_data[
            message.chat.id
        ]["student"] = message.text


        bot.send_message(
            message.chat.id,
            "📅 Tug'ilgan sanasini yozing:\nMisol: 2012-05-20"
        )


        bot.register_next_step_handler(
            message,
            student_birth
        )



    def student_birth(message):

        admin_data[
            message.chat.id
        ]["birth_date"] = message.text


        bot.send_message(
            message.chat.id,
            "🪪 Tug'ilganlik haqidagi guvohnoma raqamini yozing:"
        )


        bot.register_next_step_handler(
            message,
            student_metrika
        )



    def student_metrika(message):

        admin_data[
            message.chat.id
        ]["metrika"] = message.text


        bot.send_message(
            message.chat.id,
            "🏫 Sinfini yozing:\nMisol: 5-A"
        )


        bot.register_next_step_handler(
            message,
            save_student
        )



    def save_student(message):

        from database import add_student


        data = admin_data.get(
            message.chat.id
        )


        add_student(

            data["teacher"],

            data["student"],

            data["birth_date"],

            data["metrika"],

            message.text

        )


        bot.send_message(
            message.chat.id,
            "✅ O'quvchi barcha ma'lumotlari bilan saqlandi"
        )


        admin_data.pop(
            message.chat.id,
            None
        )



    # ==========================
    # STATISTICS
    # ==========================

    @bot.message_handler(
        func=lambda m:
        m.text == "📊 Statistika"
        and m.chat.id in ADMIN_IDS
    )
    def statistics(message):

        db = connect()
        cursor = db.cursor()


        tables = [
            "teachers",
            "students",
            "payments",
            "parents"
        ]


        result = {}


        for table in tables:

            cursor.execute(
                f"SELECT COUNT(*) FROM {table}"
            )

            result[table] = cursor.fetchone()[0]


        db.close()


        bot.send_message(
            message.chat.id,

            f"""
📊 STATISTIKA

👨‍🏫 O'qituvchilar:
{result['teachers']}

👨‍🎓 O'quvchilar:
{result['students']}

💳 To'lovlar:
{result['payments']}

👨‍👩‍👦 Ota-onalar:
{result['parents']}
"""
        )



    # ==========================
    # ORTGA
    # ==========================

    @bot.message_handler(
        func=lambda m:
        m.text == "⬅️ Ortga"
        and m.chat.id in ADMIN_IDS
    )
    def admin_back(message):

        admin_menu(message)



    # ==========================
    # OYLIK HISOBOT (Excel)
    # ==========================

    @bot.message_handler(
        func=lambda m:
        m.text == "📊 Oylik hisobot (Excel)"
        and m.chat.id in ADMIN_IDS
    )
    def monthly_report(message):

        month = datetime.now().strftime("%Y-%m")

        rows = get_monthly_debt_rows(month)

        if not rows:

            bot.send_message(
                message.chat.id,
                "❌ Hozircha o'quvchi yo'q, hisobot bo'sh."
            )

            return

        buffer, filename = build_debt_report(month, rows)

        bot.send_document(
            message.chat.id,
            (filename, buffer),
            caption="📊 " + month + " uchun qarzdorlik hisoboti"
        )


    # ==========================
    # HUJJAT QIDIRISH
    # ==========================

    register_admin_search(bot)

    register_admin_schedule(bot)

    register_admin_staff(bot)