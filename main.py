import os

from datetime import datetime

import telebot
from telebot import types

from config import TOKEN, ADMIN_IDS, WEBAPP_URL
from database import (
    create_tables,
    migrate_schema,
    seed_teachers,
    get_departments,
    get_teachers_by_department,
    get_teacher_by_name,
    find_teacher_binding,
    request_teacher_binding,
    approve_teacher_binding,
    reject_teacher_binding,
    get_students,
    get_student_fee,
    get_department_for_teacher,
    request_staff,
    approve_staff,
    reject_staff,
    is_staff,
    get_staff_ids,
    get_pending_payments,
    create_payment_request,
    approve_payment,
    reject_payment
)

from services import gdrive, backup, reminders

from data.teachers import teachers as SEED_TEACHERS

from handlers.admin import register_admin
from handlers.teacher_documents import register_teacher_documents, safe_name
from handlers.students import register_students
from handlers.student_documents import register_student_documents
from handlers.parents import register_parents
from handlers.teacher_schedule import register_teacher_schedule


# ==========================
# BOT
# ==========================

bot = telebot.TeleBot(TOKEN)


# ==========================
# DATABASE
# ==========================

create_tables()

migrate_schema()


# birinchi ishga tushirishda 52 ta o'qituvchini bazaga yozadi
# (qayta-qayta chaqirish xavfsiz - faqat yo'qlarini qo'shadi)

seed_teachers(
    (name, dept)
    for dept, names in SEED_TEACHERS.items()
    for name in names
)


# ==========================
# XOTIRA
# ==========================

selected_teachers = {}

# foydalanuvchi hozir qaysi bo'limni ko'rib turibdi
# (bir xil ismli o'qituvchilar turli bo'limda bo'lsa adashmaslik uchun)

browsing_department = {}

# to'lov kvitansiyasi yuklash jarayonidagi vaqtinchalik ma'lumot

payment_pending = {}


# ==========================
# YORDAMCHI
# ==========================


def is_admin(chat_id):
    return chat_id in ADMIN_IDS


def show_main_menu(chat_id, teacher_name):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add(
        types.KeyboardButton("👨‍🎓 O‘quvchilar ro‘yxati")
    )

    markup.add(
        types.KeyboardButton("📂 Hujjatlar")
    )

    markup.add(
        types.KeyboardButton("💳 To'lov kvitansiyasi")
    )

    markup.add(
        types.KeyboardButton("🗓 Dars jadvali")
    )

    if WEBAPP_URL.startswith("https://"):

        markup.add(
            types.KeyboardButton(
                "📱 Mini App",
                web_app=types.WebAppInfo(url=WEBAPP_URL)
            )
        )

    markup.add(
        types.KeyboardButton("⬅️ Ortga")
    )

    bot.send_message(
        chat_id,
        "👨‍🏫 " + teacher_name + "\n\n📋 Bosh menyu:",
        reply_markup=markup
    )


def show_buxgalter_menu(chat_id):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add(
        types.KeyboardButton("📋 Kutilayotgan kvitansiyalar")
    )

    bot.send_message(
        chat_id,
        "🧮 Buxgalter paneli",
        reply_markup=markup
    )


# ==========================
# START
# ==========================

@bot.message_handler(commands=["start"])
def start(message):

    chat_id = message.chat.id


    # admin bo'lsa - to'g'ridan-to'g'ri bo'lim tanlashga o'tadi,
    # tasdiqlash talab qilinmaydi

    if not is_admin(chat_id):

        if is_staff(chat_id, "buxgalter"):

            show_buxgalter_menu(chat_id)

            return


        binding = find_teacher_binding(chat_id)

        if binding:

            name, department = binding

            selected_teachers[chat_id] = name

            show_main_menu(chat_id, name)

            return


    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for dep in get_departments():
        markup.add(
            types.KeyboardButton(dep)
        )

    markup.add(
        types.KeyboardButton("👨‍👩‍👦 Ota-ona")
    )

    markup.add(
        types.KeyboardButton("🧮 Men buxgalterman")
    )

    bot.send_message(
        chat_id,
        "🏢 Bo‘limni tanlang:",
        reply_markup=markup
    )


# ==========================
# OTA-ONA
# ==========================

@bot.message_handler(
    func=lambda m: m.text == "👨‍👩‍👦 Ota-ona"
)
def parent_button(message):

    bot.send_message(
        message.chat.id,
        "👨‍👩‍👦 Ota-ona paneli uchun /parent yuboring"
    )


# ==========================
# BUXGALTER RO'YXATDAN O'TISH
# ==========================

@bot.message_handler(
    func=lambda m: m.text == "🧮 Men buxgalterman"
)
def buxgalter_button(message):

    chat_id = message.chat.id

    full_name = (
        (message.from_user.first_name or "")
        + " " + (message.from_user.last_name or "")
    ).strip()

    username = message.from_user.username


    result = request_staff(chat_id, "buxgalter", full_name, username)


    if result == "already":

        show_buxgalter_menu(chat_id)


    elif result == "pending":

        bot.send_message(
            chat_id,
            "⏳ So'rovingiz hali ko'rib chiqilmoqda. Iltimos, kuting."
        )


    elif result == "ok":

        bot.send_message(
            chat_id,
            "✅ So'rovingiz administratorga yuborildi.\n"
            "Tasdiqlanishini kuting."
        )

        username_text = "@" + username if username else "username yo'q"

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "✅ Tasdiqlash",
                callback_data="sapprove:" + str(chat_id)
            ),
            types.InlineKeyboardButton(
                "❌ Rad etish",
                callback_data="sreject:" + str(chat_id)
            )
        )

        for admin_id in ADMIN_IDS:

            try:

                bot.send_message(
                    admin_id,
                    "🔔 Yangi buxgalter so'rovi\n\n"
                    "👤 " + (full_name or "noma'lum") + "\n"
                    "🔗 " + username_text + "\n"
                    "🆔 " + str(chat_id),
                    reply_markup=markup
                )

            except Exception:
                pass


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("sapprove:")
)
def approve_staff_request(call):

    if call.message.chat.id not in ADMIN_IDS:
        return

    telegram_id = int(call.data.split(":", 1)[1])

    result = approve_staff(telegram_id)

    if not result:

        bot.answer_callback_query(call.id, "So'rov topilmadi yoki eskirgan")

        return

    _, full_name = result

    bot.answer_callback_query(call.id, "✅ Tasdiqlandi")

    bot.edit_message_text(
        "✅ Tasdiqlandi: " + (full_name or str(telegram_id)),
        call.message.chat.id,
        call.message.message_id
    )

    try:

        bot.send_message(
            telegram_id,
            "✅ Siz buxgalter sifatida tasdiqlandingiz!\n"
            "/start bosing."
        )

    except Exception:
        pass


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("sreject:")
)
def reject_staff_request(call):

    if call.message.chat.id not in ADMIN_IDS:
        return

    telegram_id = int(call.data.split(":", 1)[1])

    result = reject_staff(telegram_id)

    if not result:

        bot.answer_callback_query(call.id, "So'rov topilmadi yoki eskirgan")

        return

    bot.answer_callback_query(call.id, "❌ Rad etildi")

    bot.edit_message_text(
        "❌ Rad etildi",
        call.message.chat.id,
        call.message.message_id
    )

    try:

        bot.send_message(
            telegram_id,
            "❌ So'rovingiz rad etildi."
        )

    except Exception:
        pass


# ==========================
# BO'LIM TANLASH
# ==========================

@bot.message_handler(
    func=lambda m: m.text in get_departments()
)
def department(message):

    chat_id = message.chat.id

    browsing_department[chat_id] = message.text


    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for _, name, status in get_teachers_by_department(message.text):

        label = name

        if status == "approved":
            label = "🔒 " + name

        markup.add(
            types.KeyboardButton(label)
        )

    markup.add(
        types.KeyboardButton("⬅️ Ortga")
    )

    bot.send_message(
        chat_id,
        "📂 " + message.text + "\n\n👨‍🏫 O'qituvchini tanlang:\n\n"
        "🔒 - band (allaqachon ro'yxatdan o'tgan)",
        reply_markup=markup
    )


# ==========================
# O'QITUVCHI TANLASH
# ==========================

def _extract_name(text):
    """Tugma matnidan 🔒 belgisini olib tashlaydi."""
    return text[2:].strip() if text.startswith("🔒") else text


@bot.message_handler(
    func=lambda m: _extract_name(m.text) in [
        name
        for dept in get_departments()
        for _, name, _ in get_teachers_by_department(dept)
    ]
)
def teacher_selected(message):

    chat_id = message.chat.id

    name = _extract_name(message.text)

    department = browsing_department.get(chat_id)


    row = get_teacher_by_name(name, department) if department else None

    if not row:
        # bo'lim tanlanmasdan to'g'ridan-to'g'ri ism kelgan bo'lishi mumkin
        # (masalan eski xabar tugmasi bosilsa) - barcha bo'limlarni qidiramiz

        for dept in get_departments():

            found = get_teacher_by_name(name, dept)

            if found:
                row = found
                department = dept
                break

    if not row:

        bot.send_message(
            chat_id,
            "❌ O'qituvchi topilmadi. Qaytadan /start bosing."
        )

        return


    teacher_id = row[0]


    # ADMIN - tasdiqsiz, to'g'ridan-to'g'ri kira oladi (nazorat uchun)

    if is_admin(chat_id):

        selected_teachers[chat_id] = name

        show_main_menu(chat_id, name)

        return


    result = request_teacher_binding(
        teacher_id,
        chat_id,
        message.from_user.username,
        (message.from_user.first_name or "") + " " + (message.from_user.last_name or "")
    )


    if result == "already_mine":

        selected_teachers[chat_id] = name

        show_main_menu(chat_id, name)


    elif result == "taken":

        bot.send_message(
            chat_id,
            "❌ Bu o'qituvchi allaqachon ro'yxatdan o'tgan.\n"
            "Agar bu xato bo'lsa, administratorga murojaat qiling."
        )


    elif result == "pending_self":

        bot.send_message(
            chat_id,
            "⏳ So'rovingiz hali ko'rib chiqilmoqda. Iltimos, kuting."
        )


    elif result == "pending_other":

        bot.send_message(
            chat_id,
            "⏳ Bu o'qituvchi uchun boshqa so'rov ko'rib chiqilmoqda.\n"
            "Bu siz bo'lsangiz - biroz kuting. Aks holda administratorga murojaat qiling."
        )


    elif result == "ok":

        bot.send_message(
            chat_id,
            "✅ So'rovingiz administratorga yuborildi.\n"
            "Tasdiqlanishini kuting."
        )

        username = (
            "@" + message.from_user.username
            if message.from_user.username else "username yo'q"
        )

        full_name = (
            (message.from_user.first_name or "")
            + " " + (message.from_user.last_name or "")
        ).strip()

        approve_markup = types.InlineKeyboardMarkup()

        approve_markup.add(
            types.InlineKeyboardButton(
                "✅ Tasdiqlash",
                callback_data="tapprove:" + str(teacher_id)
            ),
            types.InlineKeyboardButton(
                "❌ Rad etish",
                callback_data="treject:" + str(teacher_id)
            )
        )

        for admin_id in ADMIN_IDS:

            try:

                bot.send_message(
                    admin_id,
                    "🔔 Yangi so'rov\n\n"
                    "👨‍🏫 O'qituvchi: " + name + "\n"
                    "📂 Bo'lim: " + department + "\n\n"
                    "👤 So'rovchi: " + (full_name or "noma'lum") + "\n"
                    "🔗 " + username + "\n"
                    "🆔 " + str(chat_id),
                    reply_markup=approve_markup
                )

            except Exception:
                pass


# ==========================
# ADMIN - TASDIQLASH / RAD ETISH
# ==========================

@bot.callback_query_handler(
    func=lambda c: c.data.startswith("tapprove:")
)
def approve_request(call):

    if call.message.chat.id not in ADMIN_IDS:
        return

    teacher_id = int(call.data.split(":", 1)[1])

    result = approve_teacher_binding(teacher_id)

    if not result:

        bot.answer_callback_query(call.id, "So'rov topilmadi yoki eskirgan")

        return

    telegram_id, name, department = result

    bot.answer_callback_query(call.id, "✅ Tasdiqlandi")

    bot.edit_message_text(
        "✅ Tasdiqlandi: " + name + " (" + department + ")",
        call.message.chat.id,
        call.message.message_id
    )

    try:

        bot.send_message(
            telegram_id,
            "✅ So'rovingiz tasdiqlandi!\n\n"
            "Endi botdan " + name + " sifatida foydalanishingiz mumkin.\n"
            "/start bosing."
        )

    except Exception:
        pass


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("treject:")
)
def reject_request(call):

    if call.message.chat.id not in ADMIN_IDS:
        return

    teacher_id = int(call.data.split(":", 1)[1])

    telegram_id = reject_teacher_binding(teacher_id)

    if not telegram_id:

        bot.answer_callback_query(call.id, "So'rov topilmadi yoki eskirgan")

        return

    bot.answer_callback_query(call.id, "❌ Rad etildi")

    bot.edit_message_text(
        "❌ Rad etildi",
        call.message.chat.id,
        call.message.message_id
    )

    try:

        bot.send_message(
            telegram_id,
            "❌ So'rovingiz rad etildi.\n"
            "Administrator bilan bog'laning."
        )

    except Exception:
        pass


# ==========================
# TO'LOV KVITANSIYASI (O'QITUVCHI YUBORADI)
# ==========================

@bot.message_handler(
    func=lambda m: m.text == "💳 To'lov kvitansiyasi"
)
def payment_menu(message):

    chat_id = message.chat.id

    teacher = selected_teachers.get(chat_id)

    if not teacher:

        bot.send_message(
            chat_id,
            "❌ Avval o'qituvchini tanlang."
        )

        return

    students = get_students(teacher)

    if not students:

        bot.send_message(
            chat_id,
            "❌ Sizda hali o'quvchi yo'q."
        )

        return

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for student in students:

        markup.add(
            types.KeyboardButton(student)
        )

    markup.add(
        types.KeyboardButton("⬅️ Ortga")
    )

    bot.send_message(
        chat_id,
        "👨‍🎓 Qaysi o'quvchi uchun kvitansiya yuborasiz?",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        message,
        payment_student_picked
    )


def payment_student_picked(message):

    chat_id = message.chat.id

    teacher = selected_teachers.get(chat_id)

    if message.text == "⬅️ Ortga":

        show_main_menu(chat_id, teacher or "")

        return

    if not teacher or message.text not in get_students(teacher):

        bot.send_message(
            chat_id,
            "❌ O'quvchi topilmadi. Qaytadan urinib ko'ring."
        )

        return

    payment_pending[chat_id] = {
        "teacher": teacher,
        "student": message.text
    }

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add(
        types.KeyboardButton("⬅️ Ortga")
    )

    bot.send_message(
        chat_id,
        "📎 Kvitansiya rasmini (yoki skanini) yuboring:",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        message,
        payment_receive_file
    )


def payment_receive_file(message):

    chat_id = message.chat.id

    data = payment_pending.get(chat_id)

    if not data:

        bot.send_message(
            chat_id,
            "❌ Xatolik yuz berdi. Qaytadan boshlang."
        )

        return

    if message.text == "⬅️ Ortga":

        payment_pending.pop(chat_id, None)

        show_main_menu(chat_id, data["teacher"])

        return


    file_id = None

    if message.photo:

        file_id = message.photo[-1].file_id

    elif message.document:

        file_id = message.document.file_id


    if not file_id:

        bot.send_message(
            chat_id,
            "❌ Faqat rasm yoki hujjat yuboring."
        )

        bot.register_next_step_handler(
            message,
            payment_receive_file
        )

        return


    teacher = data["teacher"]
    student = data["student"]

    try:

        info = bot.get_file(file_id)

        content = bot.download_file(info.file_path)

        ext = os.path.splitext(info.file_path)[1]

        if not ext:
            ext = gdrive.detect_extension(content) or ".jpg"

        month = datetime.now().strftime("%Y-%m")

        fee = get_student_fee(teacher, student)

        dept = get_department_for_teacher(teacher)

        filename = (
            safe_name(student).replace(" ", "_")
            + "_" + month + ext
        )

        drive_id, link = gdrive.upload_bytes(
            content,
            filename,
            [
                "Tolovlar",
                safe_name(dept),
                safe_name(teacher),
                safe_name(student),
                month
            ]
        )

        payment_id = create_payment_request(
            teacher, student, month, fee,
            drive_id, link, chat_id
        )

    except Exception as e:

        bot.send_message(
            chat_id,
            "❌ Saqlashda xato:\n" + str(e)
        )

        bot.register_next_step_handler(
            message,
            payment_receive_file
        )

        return


    bot.send_message(
        chat_id,
        "✅ Kvitansiya yuborildi. Buxgalter tasdig'ini kuting."
    )

    payment_pending.pop(chat_id, None)

    show_main_menu(chat_id, teacher)


    # buxgalterlarga xabar (asl Telegram fayli - tezroq)

    review_markup = types.InlineKeyboardMarkup()

    review_markup.add(
        types.InlineKeyboardButton(
            "✅ Tasdiqlash",
            callback_data="payapprove:" + str(payment_id)
        ),
        types.InlineKeyboardButton(
            "❌ Rad etish",
            callback_data="payreject:" + str(payment_id)
        )
    )

    caption = (
        "🧾 Yangi kvitansiya\n\n"
        "👨‍🏫 O'qituvchi: " + teacher + "\n"
        "👨‍🎓 O'quvchi: " + student + "\n"
        "📅 Oy: " + month + "\n"
        "💰 Summa: " + str(fee) + " so'm"
    )

    for staff_id in get_staff_ids("buxgalter"):

        try:

            bot.send_photo(
                staff_id,
                file_id,
                caption=caption,
                reply_markup=review_markup
            )

        except Exception:

            try:

                bot.send_document(
                    staff_id,
                    file_id,
                    caption=caption,
                    reply_markup=review_markup
                )

            except Exception:
                pass


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("payapprove:")
)
def payment_approve(call):

    chat_id = call.message.chat.id

    if not is_staff(chat_id, "buxgalter") and chat_id not in ADMIN_IDS:

        bot.answer_callback_query(call.id, "Ruxsat yo'q")

        return

    payment_id = int(call.data.split(":", 1)[1])

    result = approve_payment(payment_id, chat_id)

    if not result:

        bot.answer_callback_query(call.id, "Topilmadi yoki allaqachon ko'rib chiqilgan")

        return

    teacher, student, month, submitted_by = result

    bot.answer_callback_query(call.id, "✅ Tasdiqlandi")

    _mark_reviewed(call, "✅ Tasdiqlandi: " + student + " (" + month + ")")

    if submitted_by:

        try:

            bot.send_message(
                submitted_by,
                "✅ " + student + " uchun " + month + " to'lovi tasdiqlandi."
            )

        except Exception:
            pass


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("payreject:")
)
def payment_reject(call):

    chat_id = call.message.chat.id

    if not is_staff(chat_id, "buxgalter") and chat_id not in ADMIN_IDS:

        bot.answer_callback_query(call.id, "Ruxsat yo'q")

        return

    payment_id = int(call.data.split(":", 1)[1])

    result = reject_payment(payment_id, chat_id)

    if not result:

        bot.answer_callback_query(call.id, "Topilmadi yoki allaqachon ko'rib chiqilgan")

        return

    teacher, student, month, submitted_by = result

    bot.answer_callback_query(call.id, "❌ Rad etildi")

    _mark_reviewed(call, "❌ Rad etildi: " + student + " (" + month + ")")

    if submitted_by:

        try:

            bot.send_message(
                submitted_by,
                "❌ " + student + " uchun kvitansiya rad etildi.\n"
                "Qaytadan tekshirib, to'g'ri kvitansiyani yuboring."
            )

        except Exception:
            pass


def _mark_reviewed(call, text):
    """Rasm yoki oddiy xabar bo'lishidan qat'iy nazar, natijani ko'rsatadi."""

    try:

        bot.edit_message_caption(
            text,
            call.message.chat.id,
            call.message.message_id
        )

    except Exception:

        try:

            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id
            )

        except Exception:
            pass


# ==========================
# BUXGALTER - KUTILAYOTGAN KVITANSIYALAR
# ==========================

@bot.message_handler(
    func=lambda m: m.text == "📋 Kutilayotgan kvitansiyalar"
    and is_staff(m.chat.id, "buxgalter")
)
def pending_payments_list(message):

    chat_id = message.chat.id

    pending = get_pending_payments()

    if not pending:

        bot.send_message(
            chat_id,
            "✅ Kutilayotgan kvitansiya yo'q."
        )

        return

    for payment_id, teacher, student, month, amount, drive_file_id, submitted_by in pending:

        review_markup = types.InlineKeyboardMarkup()

        review_markup.add(
            types.InlineKeyboardButton(
                "✅ Tasdiqlash",
                callback_data="payapprove:" + str(payment_id)
            ),
            types.InlineKeyboardButton(
                "❌ Rad etish",
                callback_data="payreject:" + str(payment_id)
            )
        )

        caption = (
            "🧾 #" + str(payment_id) + "\n\n"
            "👨‍🏫 O'qituvchi: " + teacher + "\n"
            "👨‍🎓 O'quvchi: " + student + "\n"
            "📅 Oy: " + month + "\n"
            "💰 Summa: " + str(amount or 0) + " so'm"
        )

        try:

            if drive_file_id:

                content = gdrive.download_bytes(drive_file_id)

                bot.send_photo(
                    chat_id,
                    content,
                    caption=caption,
                    reply_markup=review_markup
                )

            else:

                bot.send_message(
                    chat_id,
                    caption,
                    reply_markup=review_markup
                )

        except Exception:

            bot.send_message(
                chat_id,
                caption,
                reply_markup=review_markup
            )


# ==========================
# ORTGA
# ==========================

@bot.message_handler(
    func=lambda m: m.text == "⬅️ Ortga"
)
def back(message):

    start(message)


# ==========================
# HANDLERS
# ==========================

# MUHIM:
# Teacher hujjatlari birinchi ulanadi

register_teacher_documents(
    bot,
    selected_teachers
)


register_students(
    bot,
    selected_teachers
)


register_student_documents(
    bot,
    selected_teachers
)


register_teacher_schedule(
    bot,
    selected_teachers
)


register_admin(bot)


register_parents(bot)


# ==========================
# GOOGLE DRIVE
# ==========================

try:

    info = gdrive.check()

    print("☁️  Google Drive:", info["email"])

    if info["limit_gb"]:
        print(
            "💾 Band:",
            info["used_gb"], "GB /",
            info["limit_gb"], "GB"
        )

    # bazani har 6 soatda Drive ga zaxiralaydi

    def notify_admin(error):

        for admin_id in ADMIN_IDS:

            try:
                bot.send_message(
                    admin_id,
                    "⚠️ Zaxira yuklanmadi: " + str(error)
                )
            except Exception:
                pass

    backup.start(on_error=notify_admin)

    print("💾 Zaxira oqimi ishga tushdi (har 6 soatda)")

    reminders.start(bot)

    print("⏰ Qarzdorlik eslatmasi ishga tushdi (har oyning 5,15,25-kunlari)")

except Exception as e:

    print()
    print("❌ Google Drive ga ulanib bo'lmadi:", e)
    print("   Fayl yuklash ishlamaydi.")
    print("   token.json ni tekshiring.")
    print()


# ==========================
# START BOT
# ==========================

print("✅ Bot ishga tushdi...")


bot.infinity_polling(
    skip_pending=True
)
