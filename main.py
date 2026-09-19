import os
import re

from datetime import datetime

import telebot
from telebot import types

from config import TOKEN, ADMIN_IDS, WEBAPP_URL, SCHOOL_NAME, SCHOOL_SLUG
from db.migrations import run_migrations
from database import (
    is_cancel_text,
    ensure_school_identity,
    get_school_name,
    seed_teachers,
    get_departments,
    get_teachers_by_department,
    get_teacher_by_name,
    get_teacher_by_id,
    search_teachers_by_name,
    find_teacher_binding,
    request_teacher_binding,
    approve_teacher_binding,
    reject_teacher_binding,
    get_students,
    get_student_fee,
    FEE_PRIVILEGED,
    get_department_for_teacher,
    get_parent,
    get_staff_role,
    is_staff,
    get_staff_ids,
    get_pending_payments,
    create_payment_request,
    get_payment,
    suggested_received,
    get_commission_percent,
    gross_amount,
    net_amount,
    approve_payment,
    reject_payment,
    TEACHER_TYPES,
    PERMISSION_LABELS,
    set_teacher_type,
    get_teacher_permissions,
    remember_broadcast,
    get_broadcast_copies,
    clear_broadcast,
    prune_broadcasts,
    set_view_as,
    get_view_as,
    clear_view_as,
    log_action
)

from state import SelectedTeachers

from services import gdrive, backup, reminders, daily_reminders, specialty_reminder
from services.students_export import send_students_excel

from data.teachers import teachers as SEED_TEACHERS
from data.curriculum import THEORY_DEPARTMENT

from handlers.admin import register_admin
from handlers.admin_permissions import register_admin_permissions
from handlers.teacher_documents import register_teacher_documents, safe_name
from handlers.tech_staff import register_tech_staff, MENU_BUTTONS as TECH_MENU
from handlers.school_documents import register_school_documents, BUTTON as SCHOOL_DOCS_BUTTON
from handlers.tabel import register_tabel, BUTTON as TABEL_BUTTON
from handlers.students import register_students
from handlers.parents import register_parents
from handlers.teacher_schedule import register_teacher_schedule
from handlers.schedule_excel import register_schedule_excel, BUTTON as EXCEL_IMPORT_BUTTON


# ==========================
# BOT
# ==========================

# num_threads standart holatda 2 ta - butun maktabga (50+
# o'qituvchi, yuzlab ota-ona) shuncha oqim yetmaydi: ikkita
# fayl yuklanayotganda uchinchi odam navbatda turadi.

bot = telebot.TeleBot(TOKEN, num_threads=16)


# ==========================
# DATABASE
# ==========================
#
# Sxema endi versiyalanadi (db/migrations.py). run_migrations()
# birinchi marta baseline'ni qo'llaydi - u o'z navbatida eski
# create_tables() + migrate_schema() ni chaqiradi, shuning uchun
# mavjud baza uchun hech narsa o'zgarmaydi.

run_migrations()


# Maktab nomi/slugi .env dan bazaga ko'chiriladi - FAQAT bazada
# hali yo'q bo'lsa. Keyin BAZA haqiqiy manba bo'ladi, ya'ni admin
# nomni o'zgartirsa qayta ishga tushishda u saqlanib qoladi.

ensure_school_identity(SCHOOL_NAME, SCHOOL_SLUG)


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

selected_teachers = SelectedTeachers(
    is_admin=lambda chat_id: chat_id in ADMIN_IDS,
    get_view_as=get_view_as,
    get_binding=find_teacher_binding
)

# to'lov kvitansiyasi yuklash jarayonidagi vaqtinchalik ma'lumot

payment_pending = {}


# ==========================
# YORDAMCHI
# ==========================


def is_admin(chat_id):
    return chat_id in ADMIN_IDS


def _foiz(qiymat):
    """0.3 -> "0,3". O'zbekchada kasr vergul bilan yoziladi."""

    return str(qiymat).replace(".", ",")


def _pul(son):
    """123972 -> "123 972". Pul har doim to'liq son ko'rinishida."""

    return "{:,}".format(int(son or 0)).replace(",", " ")


# ==========================
# BIR NECHTA ADMINGA YUBORILGAN XABARNOMA
# ==========================
#
# Tugmali xabarnoma hamma adminga boradi - hech biri o'tkazib
# yubormasin. Lekin biri javob bergach, qolganlarnikida tugmalar
# turib qolmasligi kerak: ular bosilsa «eskirgan» xatosi chiqardi
# va xabar ikkilangandek tuyulardi.
#
# Shuning uchun yuborilgan nusxalar daftarga yoziladi
# (`db/broadcasts.py`) va javob berilganda hammasi bir xil natija
# matniga almashtiriladi: kim javob bergani ham ko'rinadi.


def _actor_name(call):
    """Tugmani bosgan odamning ko'rsatiladigan nomi."""

    user = call.from_user

    name = ((user.first_name or "") + " " + (user.last_name or "")).strip()

    if not name and user.username:
        name = "@" + user.username

    return name or str(call.message.chat.id)


def _broadcast_to_admins(kind, ref_id, text, markup=None):
    """Barcha adminlarga yuboradi va nusxalarni eslab qoladi."""

    for admin_id in ADMIN_IDS:

        try:

            sent = bot.send_message(admin_id, text, reply_markup=markup)

            remember_broadcast(kind, ref_id, admin_id, sent.message_id)

        except Exception:
            # admin botni bloklagan yoki hali /start bosmagan
            pass

    prune_broadcasts()


def _close_broadcast(kind, ref_id, call, text):
    """
    Xabarnomaning barcha nusxalarini natija matniga almashtiradi.

    Javob bergan odamning o'z xabari ham shu ro'yxatda bo'ladi.
    Nusxa topilmasa (bot qayta o'rnatilgan, daftar bo'sh) - hech
    bo'lmasa bosilgan xabarning o'zi yangilanadi.
    """

    final = text + "\n\n👤 " + _actor_name(call)

    copies = get_broadcast_copies(kind, ref_id)

    if not copies:
        copies = [(call.message.chat.id, call.message.message_id)]

    for chat_id, message_id in copies:

        try:
            bot.edit_message_text(final, chat_id, message_id)

        except Exception:

            # rasm bo'lsa matn emas, izoh tahrirlanadi

            try:
                bot.edit_message_caption(final, chat_id, message_id)

            except Exception:
                pass

    clear_broadcast(kind, ref_id)


VIEW_EXIT_BUTTON = "🚪 Ko'rish rejimidan chiqish"


def show_main_menu(chat_id, teacher_name):

    # Admin "ko'rish rejimi"da bo'lsa menyu xuddi o'qituvchinikidek
    # bo'ladi, faqat tepasida ogohlantirish va chiqish tugmasi
    # qo'shiladi - aks holda admin o'z panelini qanday qaytarishni
    # bilmay qolardi.

    viewing = is_admin(chat_id) and get_view_as(chat_id) == teacher_name

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    # Kunlik eng kerakli ma'lumot birinchi o'rinda

    markup.add(
        types.KeyboardButton("📅 Bugungi darslarim")
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

    markup.add(
        types.KeyboardButton(EXCEL_IMPORT_BUTTON)
    )

    # Mini App alohida tugma emas - kiritish maydoni yonidagi
    # doimiy "Ochish" tugmasi orqali ochiladi (pastda sozlanadi)

    markup.add(
        types.KeyboardButton("⬅️ Ortga")
    )

    if viewing:

        markup.add(
            types.KeyboardButton(VIEW_EXIT_BUTTON)
        )

    header = (
        "👁 Ko'rish rejimi\n"
        "Siz " + teacher_name + " sifatida ko'rmoqdasiz.\n"
        "Bot ham, Mini App ham unga qanday ko'rinsa - shunday.\n\n"
        if viewing else ""
    )

    bot.send_message(
        chat_id,
        header + "👨‍🏫 " + teacher_name + "\n\n📋 Bosh menyu:",
        reply_markup=markup
    )


# ==========================
# KIRISH - ROL TANLASH
# ==========================
#
# Botga kirgan odam kim ekanini bot bilmaydi, shuning uchun
# undan so'raladi. Faqat ikkita rol o'z-o'zidan tanlanadi:
#
#   O'qituvchi - ism-familiyasini yozadi, admin tasdiqlaydi
#   Ota-ona    - farzandining ITV raqamini kiritadi
#
# Qolgan rollar (buxgalter, direktor, yordamchi) admin
# tomonidan qo'lda beriladi - o'z-o'zidan olinmaydi.
# ==========================


STAFF_MENUS = {
    "buxgalter": ("🧮 Buxgalter paneli", ["📋 Kutilayotgan kvitansiyalar"]),
    "direktor":  ("🏫 Direktor paneli",  ["📋 O'quvchilar ro'yxati (Excel)", SCHOOL_DOCS_BUTTON]),
    "yordamchi": ("🤝 Yordamchi paneli", [SCHOOL_DOCS_BUTTON]),
    "xojalik_mudiri": ("🔧 Xo'jalik mudiri paneli",
                       TECH_MENU + [TABEL_BUTTON, SCHOOL_DOCS_BUTTON])
}


def show_staff_menu(chat_id, role):

    title, buttons = STAFF_MENUS.get(role, ("👤 Panel", []))

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for btn in buttons:
        markup.add(types.KeyboardButton(btn))

    hint = (
        "\n\nMa'lumotlarni ko'rish uchun pastdagi "
        "«Ochish» tugmasini bosing."
        if WEBAPP_URL.startswith("https://") else ""
    )

    bot.send_message(
        chat_id,
        title + hint,
        reply_markup=markup if buttons else types.ReplyKeyboardRemove()
    )


def show_role_choice(chat_id):

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "👨‍🏫 Men o'qituvchiman",
            callback_data="role:teacher"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "👨‍👩‍👦 Men ota-onaman",
            callback_data="role:parent"
        )
    )

    # ID ni shu yerda ko'rsatamiz: xodim (buxgalter, direktor,
    # xo'jalik mudiri) ro'yxatdan o'zi o'tolmaydi - uni admin
    # Telegram ID bo'yicha qo'shadi. Ilgari odam /start bosardi-yu,
    # ID sini qayerdan olishni bilmasdi.

    bot.send_message(
        chat_id,
        "👋 Xush kelibsiz!\n\n"
        + get_school_name() + " boti.\n\n"
        "Kim sifatida kirmoqchisiz?\n\n"
        "🆔 Sizning ID: " + str(chat_id) + "\n"
        "Agar sizni xodim sifatida qo'shishlari kerak bo'lsa - "
        "shu raqamni administratorga yuboring.",
        reply_markup=markup
    )


@bot.message_handler(commands=["start"])
def start(message):

    chat_id = message.chat.id


    # 1. ADMIN

    if is_admin(chat_id):

        bot.send_message(
            chat_id,
            "🔐 Administrator\n\n"
            "Boshqaruv uchun /admin buyrug'ini yuboring."
            + (
                "\nMa'lumotlarni ko'rish uchun «Ochish» tugmasi."
                if WEBAPP_URL.startswith("https://") else ""
            ),
            reply_markup=types.ReplyKeyboardRemove()
        )

        return


    # 1a. KO'RISH REJIMIDAGI ADMIN
    #
    # Rejim bazada saqlanadi, shuning uchun bot qayta ishga
    # tushgandan keyin ham /start o'sha o'qituvchi menyusini
    # qaytaradi.

    if is_admin(chat_id):

        viewed = get_view_as(chat_id)

        if viewed:

            selected_teachers[chat_id] = viewed

            show_main_menu(chat_id, viewed)

            return


    # 2. XODIM (admin tomonidan qo'shilgan)

    staff_role = get_staff_role(chat_id)

    if staff_role:

        show_staff_menu(chat_id, staff_role)

        return


    # 3. TASDIQLANGAN O'QITUVCHI

    binding = find_teacher_binding(chat_id)

    if binding:

        name, _ = binding

        selected_teachers[chat_id] = name

        show_main_menu(chat_id, name)

        return


    # 4. RO'YXATDAN O'TGAN OTA-ONA

    if get_parent(chat_id):

        parents_api["entry"](message)

        return


    # 5. YANGI FOYDALANUVCHI

    show_role_choice(chat_id)


# ==========================
# ROL TANLANDI
# ==========================

@bot.message_handler(
    func=lambda m: m.text == "📋 O'quvchilar ro'yxati (Excel)"
)
def students_excel(message):
    """Direktor va admin uchun - butun maktab o'quvchilari fayl ko'rinishida."""

    chat_id = message.chat.id

    if chat_id not in ADMIN_IDS and get_staff_role(chat_id) != "direktor":

        bot.send_message(chat_id, "❌ Ruxsat yo'q")

        return

    send_students_excel(bot, chat_id)


@bot.callback_query_handler(func=lambda c: c.data == "role:parent")
def role_parent(call):

    bot.answer_callback_query(call.id)

    parents_api["entry"](call.message)


@bot.callback_query_handler(func=lambda c: c.data == "role:teacher")
def role_teacher(call):

    chat_id = call.message.chat.id

    bot.answer_callback_query(call.id)

    sent = bot.send_message(
        chat_id,
        "👨‍🏫 Ism-familiyangizni to'liq yozing:\n\n"
        "Masalan: Qayumov Qobil"
    )

    bot.register_next_step_handler(sent, teacher_name_entered)


def teacher_name_entered(message):

    chat_id = message.chat.id

    if is_cancel_text(message.text):
        bot.send_message(chat_id, "❌ Bekor qilindi.")
        return


    query = (message.text or "").strip()

    if len(query) < 3:

        sent = bot.send_message(
            chat_id,
            "❌ Juda qisqa. Ism-familiyangizni to'liq yozing:"
        )

        bot.register_next_step_handler(sent, teacher_name_entered)

        return


    matches = search_teachers_by_name(query)


    if not matches:

        bot.send_message(
            chat_id,
            "❌ «" + query + "» ro'yxatda topilmadi.\n\n"
            "Ismingiz boshqacha yozilgan bo'lishi mumkin, yoki "
            "hali ro'yxatga kiritilmagansiz.\n"
            "Administrator siz bilan bog'lanadi."
        )

        _notify_admins_unknown_teacher(message, query)

        return


    markup = types.InlineKeyboardMarkup()

    for teacher_id, name, department, status in matches:

        if status == "approved":
            continue

        markup.add(
            types.InlineKeyboardButton(
                name + " · " + department,
                callback_data="tpick:" + str(teacher_id)
            )
        )

    if not markup.keyboard:

        bot.send_message(
            chat_id,
            "⚠️ «" + query + "» allaqachon ro'yxatdan o'tgan.\n"
            "Agar bu siz bo'lsangiz, administratorga murojaat qiling."
        )

        return

    markup.add(
        types.InlineKeyboardButton(
            "🔄 Qaytadan qidirish",
            callback_data="role:teacher"
        )
    )

    bot.send_message(
        chat_id,
        "Quyidagilardan o'zingizni tanlang:",
        reply_markup=markup
    )


def _notify_admins_unknown_teacher(message, query):

    username = (
        "@" + message.from_user.username
        if message.from_user.username else "username yo'q"
    )

    for admin_id in ADMIN_IDS:

        try:

            bot.send_message(
                admin_id,
                "❓ Ro'yxatda yo'q o'qituvchi so'rov yubordi\n\n"
                "✍️ Yozgan ismi: " + query + "\n"
                "🔗 " + username + "\n"
                "🆔 " + str(message.chat.id) + "\n\n"
                "Agar haqiqiy o'qituvchi bo'lsa, /admin → "
                "O'qituvchilar → ➕ O'qituvchi qo'shish orqali "
                "ro'yxatga kiriting."
            )

        except Exception:
            pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("tpick:"))
def teacher_picked(call):

    chat_id = call.message.chat.id

    teacher_id = int(call.data.split(":", 1)[1])

    row = get_teacher_by_id(teacher_id)

    if not row:

        bot.answer_callback_query(call.id, "Topilmadi")

        return

    name, department = row[1], row[2]

    result = request_teacher_binding(
        teacher_id,
        chat_id,
        call.from_user.username,
        (call.from_user.first_name or "") + " " + (call.from_user.last_name or "")
    )

    bot.answer_callback_query(call.id)


    if result == "already_mine":

        selected_teachers[chat_id] = name

        show_main_menu(chat_id, name)

        return


    if result == "taken":

        bot.send_message(
            chat_id,
            "❌ Bu o'qituvchi allaqachon ro'yxatdan o'tgan.\n"
            "Agar bu xato bo'lsa, administratorga murojaat qiling."
        )

        return


    if result in ("pending_self", "pending_other"):

        bot.send_message(
            chat_id,
            "⏳ So'rov ko'rib chiqilmoqda. Iltimos, kuting."
        )

        return


    if result == "ok":

        bot.send_message(
            chat_id,
            "✅ So'rovingiz administratorga yuborildi.\n"
            "Tasdiqlangach xabar beramiz."
        )

        username = (
            "@" + call.from_user.username
            if call.from_user.username else "username yo'q"
        )

        full_name = (
            (call.from_user.first_name or "")
            + " " + (call.from_user.last_name or "")
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

        _broadcast_to_admins(
            "teacher_request",
            teacher_id,
            "🔔 O'qituvchi so'rovi\n\n"
            "👨‍🏫 " + name + "\n"
            "📂 " + department + "\n\n"
            "👤 So'rovchi: " + (full_name or "noma'lum") + "\n"
            "🔗 " + username + "\n"
            "🆔 " + str(chat_id),
            approve_markup
        )


# ==========================
# ADMIN - O'QITUVCHI REJIMI
# ==========================
#
# Oddiy foydalanuvchi butun maktab tuzilmasini ko'ra olmaydi.
# Lekin adminga kerak - o'quvchi qo'shish, hujjat yuklash va
# jadval tuzishni tekshirish uchun. Shu tugma orqali admin
# istalgan o'qituvchi rejimiga o'tadi.
# ==========================

@bot.message_handler(
    func=lambda m: m.text == "👨‍🏫 O'qituvchi rejimi" and is_admin(m.chat.id)
)
def admin_teacher_mode(message):

    markup = types.InlineKeyboardMarkup()

    for index, dept in enumerate(get_departments()):

        markup.add(
            types.InlineKeyboardButton(
                dept,
                callback_data="amode:dept:" + str(index)
            )
        )

    bot.send_message(
        message.chat.id,
        "📂 Qaysi bo'lim?",
        reply_markup=markup
    )


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("amode:dept:") and is_admin(c.message.chat.id)
)
def admin_mode_dept(call):

    index = int(call.data.split(":", 2)[2])

    departments = get_departments()

    if index >= len(departments):

        bot.answer_callback_query(call.id, "Topilmadi")

        return

    dept = departments[index]

    markup = types.InlineKeyboardMarkup()

    for teacher_id, name, status in get_teachers_by_department(dept):

        markup.add(
            types.InlineKeyboardButton(
                ("🔒 " if status == "approved" else "") + name,
                callback_data="amode:pick:" + str(teacher_id)
            )
        )

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        "📂 " + dept + " - o'qituvchini tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("amode:pick:") and is_admin(c.message.chat.id)
)
def admin_mode_pick(call):

    chat_id = call.message.chat.id

    teacher_id = int(call.data.split(":", 2)[2])

    row = get_teacher_by_id(teacher_id)

    if not row:

        bot.answer_callback_query(call.id, "Topilmadi")

        return

    name = row[1]

    selected_teachers[chat_id] = name

    # Mini App boshqa jarayon - tanlovni faqat bazadan biladi

    set_view_as(chat_id, name)

    log_action(
        str(chat_id),
        "ko'rish rejimi yoqildi",
        target=name,
        actor_role="admin"
    )

    bot.answer_callback_query(call.id)

    show_main_menu(chat_id, name)


@bot.message_handler(
    func=lambda m: m.text == VIEW_EXIT_BUTTON and is_admin(m.chat.id)
)
def admin_mode_exit(message):
    """Ko'rish rejimidan chiqish - admin o'z paneliga qaytadi."""

    chat_id = message.chat.id

    name = get_view_as(chat_id)

    clear_view_as(chat_id)

    selected_teachers.pop(chat_id, None)

    if name:

        log_action(
            str(chat_id),
            "ko'rish rejimi o'chirildi",
            target=name,
            actor_role="admin"
        )

    bot.send_message(
        chat_id,
        "✅ Ko'rish rejimi tugadi.\n\n"
        "Admin panel uchun /admin buyrug'ini yuboring.",
        reply_markup=types.ReplyKeyboardRemove()
    )


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

    log_action(
        str(call.message.chat.id), "o'qituvchini tasdiqladi",
        name, department, actor_role="admin"
    )

    # xabarnoma barcha adminlarga borgan - hammasida yopiladi

    _close_broadcast(
        "teacher_request",
        teacher_id,
        call,
        "✅ Tasdiqlandi: " + name + " (" + department + ")"
    )


    # Turi darrov shu yerda tanlanadi - keyinga qoldirilsa
    # esdan chiqadi va o'qituvchi hamma huquq bilan qolib ketadi.

    markup = types.InlineKeyboardMarkup()

    for key, preset in TEACHER_TYPES.items():

        markup.add(
            types.InlineKeyboardButton(
                preset["label"],
                callback_data="ttype:" + key + ":" + str(teacher_id)
            )
        )

    hints = "\n".join(
        preset["label"] + "\n   " + preset["hint"]
        for preset in TEACHER_TYPES.values()
    )

    # Nazariya bo'limi o'qituvchilarining o'z o'quvchisi bo'lmaydi -
    # ular boshqalarning o'quvchilariga umumiy fan o'tishadi.

    suggestion = ""

    if department == THEORY_DEPARTMENT:

        suggestion = (
            "\n\n💡 " + department + " bo'limi uchun odatda «"
            + TEACHER_TYPES["umumiy"]["label"] + "» tanlanadi: "
            "o'z o'quvchisi bo'lmaydi, boshqalarning o'quvchilariga "
            "dars beradi."
        )

    bot.send_message(
        call.message.chat.id,
        "👨‍🏫 " + name + " qanday o'qituvchi?\n\n" + hints + suggestion,
        reply_markup=markup
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
    func=lambda c: c.data.startswith("ttype:")
)
def set_type_after_approve(call):

    if call.message.chat.id not in ADMIN_IDS:
        return

    _, type_key, teacher_id = call.data.split(":", 2)

    row = get_teacher_by_id(int(teacher_id))

    name = row[1] if row else None

    if not name or not set_teacher_type(name, type_key):

        bot.answer_callback_query(call.id, "Xatolik")

        return

    bot.answer_callback_query(call.id, "✅ Belgilandi")

    log_action(
        str(call.message.chat.id), "o'qituvchi turini belgiladi",
        name, TEACHER_TYPES[type_key]["label"], actor_role="admin"
    )

    permissions = get_teacher_permissions(name)

    lines = [
        ("✅ " if permissions[key] else "🚫 ") + label
        for key, label in PERMISSION_LABELS.items()
    ]

    bot.edit_message_text(
        "👨‍🏫 " + name + "\n"
        + TEACHER_TYPES[type_key]["label"] + "\n\n"
        + "\n".join(lines) + "\n\n"
        "O'zgartirish: /admin → 🔑 O'qituvchi huquqlari",
        call.message.chat.id,
        call.message.message_id
    )


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

    _close_broadcast(
        "teacher_request",
        teacher_id,
        call,
        "❌ Rad etildi"
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

    # menyu tugmasi yoki /cancel - kiritish bekor qilinadi
    if is_cancel_text(message.text):

        payment_pending.pop(chat_id, None)

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

    fee = get_student_fee(teacher, message.text)
    if fee and fee != FEE_PRIVILEGED:
        percent = get_commission_percent()
        gross = gross_amount(fee, percent)
        msg = (
            f"💰 {message.text} uchun oylik badal: {_pul(fee)} so'm\n"
            f"🏦 Bank o'tkazmada {_foiz(percent)}% ushlab qoladi.\n"
            f"Maktabga to'liq tushishi uchun {_pul(gross)} so'm to'lang."
        )
        bot.send_message(chat_id, msg)

    sent = bot.send_message(
        chat_id,
        "💵 Kvitansiyada ko'rsatilgan summani yozing (faqat raqam):",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        sent,
        payment_receive_amount
    )


def payment_receive_file(message):

    chat_id = message.chat.id

    if is_cancel_text(message.text):
        payment_pending.pop(chat_id, None)
        bot.send_message(chat_id, "❌ Bekor qilindi.")
        return

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

        # imtiyozli o'quvchi badal to'lamaydi - summa 0 yoziladi

        if fee == FEE_PRIVILEGED:
            fee = 0

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

        # summa bu bosqichgacha so'ralgan - o'qituvchi rasmni
        # yuborgan zahoti kvitansiya buxgalterga ketadi

        summa = data.get("summa") or fee

        payment_id = create_payment_request(
            teacher, student, month, summa,
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
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="payapprove:" + str(payment_id)),
        types.InlineKeyboardButton("❌ Rad etish", callback_data="payreject:" + str(payment_id))
    )

    percent = get_commission_percent()
    net = net_amount(summa, percent)

    caption = (
        "🧾 Yangi kvitansiya\n\n"
        f"👨‍🏫 O'qituvchi: {teacher}\n"
        f"👨‍🎓 O'quvchi: {student}\n"
        f"📅 Oy: {month}\n"
        f"💰 O'qituvchi kiritgan: {_pul(summa)} so'm\n"
        f"🏦 Hisobga tushadi: {_pul(net)} so'm ({_foiz(percent)}% komissiya)"
    )
    if float(summa) != float(fee):
        caption += f"\n📌 Oylik badal: {_pul(fee)} so'm"

    for staff_id in get_staff_ids("buxgalter"):

        # Kvitansiya bir nechta buxgalterga boradi. Yuborilgan
        # nusxa daftarga yoziladi - biri ko'rib chiqqach,
        # qolganlarnikida ham tugmalar yopilsin.

        sent = None

        try:

            sent = bot.send_photo(
                staff_id,
                file_id,
                caption=caption,
                reply_markup=review_markup
            )

        except Exception:

            try:

                sent = bot.send_document(
                    staff_id,
                    file_id,
                    caption=caption,
                    reply_markup=review_markup
                )

            except Exception:
                pass

        if sent:
            remember_broadcast("payment", payment_id, staff_id, sent.message_id)


def payment_receive_amount(message):
    """Kvitansiyadagi summani qabul qiladi.

    Summa o'qituvchidan so'raladi, chunki u komissiya ustiga
    qo'shilgan holda to'lanishi mumkin - badal bilan bir xil emas.
    """

    chat_id = message.chat.id

    if is_cancel_text(message.text):
        teacher = payment_pending.get(chat_id, {}).get("teacher", "")
        payment_pending.pop(chat_id, None)
        show_main_menu(chat_id, teacher)
        return

    data = payment_pending.get(chat_id)
    if not data:
        bot.send_message(chat_id, "❌ Xatolik yuz berdi. Qaytadan boshlang.")
        return

    # faqat raqamlar: "123 972 so'm" ham to'g'ri qabul qilinsin

    digits = re.sub(r"\D", "", message.text or "")
    if not digits:
        sent = bot.send_message(chat_id, "❌ Noto'g'ri raqam. Qaytadan yozing:")
        bot.register_next_step_handler(sent, payment_receive_amount)
        return

    summa = int(digits)
    if summa <= 0:
        sent = bot.send_message(chat_id, "❌ Noto'g'ri raqam. Qaytadan yozing:")
        bot.register_next_step_handler(sent, payment_receive_amount)
        return

    data["summa"] = summa

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add(types.KeyboardButton("⬅️ Ortga"))

    sent = bot.send_message(
        chat_id,
        "📎 Endi kvitansiya rasmini (yoki skanini) yuboring:",
        reply_markup=markup
    )

    bot.register_next_step_handler(sent, payment_receive_file)


# Tasdiqlash ikki bosqichli: avval hisobga QANCHA tushgani
# belgilanadi, keyin kvitansiya tasdiqlanadi. Sababi - bank
# komissiya ushlaydi, ba'zan esa summa umuman boshqacha keladi
# (Payme/Click, qisman to'lov). Buxgalter bank ko'chirmasiga
# qarab aniq raqamni qo'yadi.
#
# Kim qaysi kvitansiyaga summa kiritayotgani shu yerda turadi.

approve_pending = {}


def _tasdiqla(call, payment_id, received):
    """Kvitansiyani tasdiqlaydi va hamma tomonni xabardor qiladi."""

    chat_id = call.message.chat.id

    result = approve_payment(payment_id, chat_id, received=received)

    if not result:

        bot.send_message(
            chat_id,
            "Topilmadi yoki allaqachon ko'rib chiqilgan."
        )

        return

    teacher, student, month, submitted_by = result

    _close_broadcast(
        "payment",
        payment_id,
        call,
        "✅ Tasdiqlandi: " + student + " (" + month + ")"
        + "\nHisobga tushdi: " + _pul(received) + " so'm"
    )

    if submitted_by:

        try:

            bot.send_message(
                submitted_by,
                "✅ " + student + " uchun " + month + " to'lovi tasdiqlandi.\n"
                "Hisobga tushdi: " + _pul(received) + " so'm."
            )

        except Exception:
            pass


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("payapprove:")
)
def payment_approve(call):
    """Tasdiqlash bosildi - avval summani so'raymiz."""

    chat_id = call.message.chat.id

    if not is_staff(chat_id, "buxgalter") and chat_id not in ADMIN_IDS:

        bot.answer_callback_query(call.id, "Ruxsat yo'q")

        return

    payment_id = int(call.data.split(":", 1)[1])

    row = get_payment(payment_id)

    if not row or row[4] != "kutilmoqda":

        bot.answer_callback_query(
            call.id, "Topilmadi yoki allaqachon ko'rib chiqilgan"
        )

        return

    tavsiya = int(suggested_received(row[5]))

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "💵 " + _pul(tavsiya) + " so'm",
            callback_data="payrecv:" + str(payment_id) + ":" + str(tavsiya)
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "✏️ Boshqa summa",
            callback_data="payother:" + str(payment_id)
        )
    )

    bot.answer_callback_query(call.id, "Hisobga qancha tushdi?")

    bot.edit_message_reply_markup(
        chat_id, call.message.message_id, reply_markup=markup
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("payrecv:"))
def payment_receive_suggested(call):
    """Tavsiya qilingan summa tanlandi."""

    chat_id = call.message.chat.id

    if not is_staff(chat_id, "buxgalter") and chat_id not in ADMIN_IDS:

        bot.answer_callback_query(call.id, "Ruxsat yo'q")

        return

    _, payment_id, received = call.data.split(":")

    bot.answer_callback_query(call.id, "✅ Tasdiqlandi")

    _tasdiqla(call, int(payment_id), float(received))


@bot.callback_query_handler(func=lambda c: c.data.startswith("payother:"))
def payment_receive_other(call):
    """Summa qo'lda kiritiladi."""

    chat_id = call.message.chat.id

    if not is_staff(chat_id, "buxgalter") and chat_id not in ADMIN_IDS:

        bot.answer_callback_query(call.id, "Ruxsat yo'q")

        return

    payment_id = int(call.data.split(":")[1])

    row = get_payment(payment_id)

    if not row or row[4] != "kutilmoqda":

        bot.answer_callback_query(
            call.id, "Topilmadi yoki allaqachon ko'rib chiqilgan"
        )

        return

    approve_pending[chat_id] = {"payment_id": payment_id, "call": call}

    bot.answer_callback_query(call.id)

    sent = bot.send_message(
        chat_id,
        "💵 Hisobga tushgan summani yozing (faqat raqam):"
    )

    bot.register_next_step_handler(sent, payment_amount_entered)


def payment_amount_entered(message):
    """Buxgalter kiritgan summa bilan kvitansiyani tasdiqlaydi."""

    chat_id = message.chat.id

    if is_cancel_text(message.text):

        approve_pending.pop(chat_id, None)

        return

    data = approve_pending.get(chat_id)

    if not data:
        return

    digits = re.sub(r"\D", "", message.text or "")

    if not digits or int(digits) <= 0:

        sent = bot.send_message(
            chat_id,
            "❌ Faqat musbat raqam. Hisobga tushgan summani yozing:"
        )

        bot.register_next_step_handler(sent, payment_amount_entered)

        return

    approve_pending.pop(chat_id, None)

    _tasdiqla(data["call"], data["payment_id"], float(digits))


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

    _close_broadcast(
        "payment",
        payment_id,
        call,
        "❌ Rad etildi: " + student + " (" + month + ")"
    )

    if submitted_by:

        try:

            bot.send_message(
                submitted_by,
                "❌ " + student + " uchun kvitansiya rad etildi.\n"
                "Qaytadan tekshirib, to'g'ri kvitansiyani yuboring."
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


register_tech_staff(
    bot,
    ADMIN_IDS
)


register_school_documents(
    bot,
    ADMIN_IDS
)


register_tabel(
    bot,
    ADMIN_IDS
)


register_students(
    bot,
    selected_teachers
)


register_teacher_schedule(
    bot,
    selected_teachers
)


register_schedule_excel(
    bot,
    selected_teachers
)


register_admin(bot)
register_admin_permissions(bot)


parents_api = register_parents(bot)


# ==========================
# GOOGLE DRIVE
# ==========================

# DIQQAT: Drive tekshiruvi ALOHIDA try ichida turadi.
#
# Ilgari zaxira va barcha eslatmalar ham shu try ning ICHIDA
# ishga tushirilardi. Natijada Drive tokeni eskirganda
# (invalid_grant) gdrive.check() yiqilib, undan keyingi hamma
# narsa - zaxira, qarzdorlik eslatmasi, kunlik eslatma -
# JIMGINA ishga tushmay qolardi. Bot esa "ishlayapti" ko'rinardi.
#
# Endi Drive nosoz bo'lsa faqat fayl yuklash ishlamaydi,
# qolgan hammasi o'z ishini qilaveradi.

try:

    info = gdrive.check()

    print("☁️  Google Drive:", info["email"])

    if info.get("folder"):
        print("📁 Papka:", info["folder"], "(service account)")

    if info["limit_gb"]:
        print(
            "💾 Band:",
            info["used_gb"], "GB /",
            info["limit_gb"], "GB"
        )

except Exception as e:

    print()
    print("❌ Google Drive ga ulanib bo'lmadi:", e)
    print("   Fayl yuklash ishlamaydi, zaxira Drive ga chiqmaydi.")
    print("   token.json ni yangilash kerak.")
    print()


# ==========================
# FON XIZMATLARI
# ==========================
#
# Bular Drive holatidan QAT'I NAZAR ishga tushadi.


def notify_admin(error):

    for admin_id in ADMIN_IDS:

        try:
            bot.send_message(
                admin_id,
                "⚠️ Zaxira yuklanmadi: " + str(error)
            )
        except Exception:
            pass


for _nom, _ishga_tushir, _izoh in [
    (
        "zaxira",
        lambda: backup.start(on_error=notify_admin),
        "💾 Zaxira oqimi ishga tushdi (har 6 soatda)"
    ),
    (
        "qarzdorlik eslatmasi",
        lambda: reminders.start(bot),
        "⏰ Qarzdorlik eslatmasi ishga tushdi (har oyning 5,15,25-kunlari)"
    ),
    (
        "kunlik eslatma",
        lambda: daily_reminders.start(bot),
        "📋 Kunlik eslatma ishga tushdi (hujjat va badal - har kuni soat "
        + str(daily_reminders.SEND_HOUR) + ":00)"
    ),
    # VAQTINCHALIK: ma'lumot to'ldirilgach shu band ham,
    # services/specialty_reminder.py ham olib tashlanadi
    # (fayl boshidagi ro'yxatga qarang).
    (
        "yo'nalish eslatmasi",
        lambda: specialty_reminder.start(bot),
        "🎯 Yo'nalish eslatmasi ishga tushdi (har kuni soat "
        + str(specialty_reminder.SEND_HOUR)
        + ":00, ro'yxat bo'shagach o'zi to'xtaydi)"
    ),
]:

    # Har biri ALOHIDA - bittasi yiqilsa qolganlari ishlayveradi.

    try:
        _ishga_tushir()

        print(_izoh)

    except Exception as _xato:

        print("❌ " + _nom + " ishga tushmadi:", _xato)


# ==========================
# MINI APP - MENYU TUGMASI
# ==========================
#
# Kiritish maydoni yonidagi doimiy "Ochish" tugmasi.
# Bu GLOBAL sozlama - hamma foydalanuvchiga (ota-ona,
# o'qituvchi, buxgalter, direktor) bir xil ko'rinadi.
#
# Mini App o'zi kim kirganini aniqlaydi va tegishli
# ekranni ochadi, shuning uchun bitta tugma yetarli.
# ==========================

if WEBAPP_URL.startswith("https://"):

    try:

        bot.set_chat_menu_button(
            menu_button=types.MenuButtonWebApp(
                type="web_app",
                text="Ochish",
                web_app=types.WebAppInfo(url=WEBAPP_URL)
            )
        )

        print("📱 Mini App menyu tugmasi o'rnatildi:", WEBAPP_URL)

    except Exception as e:

        print("⚠️ Menyu tugmasi o'rnatilmadi:", e)

else:

    print("ℹ️ WEBAPP_URL sozlanmagan - Mini App tugmasi yo'q")


# ==========================
# START BOT
# ==========================

print("✅ Bot ishga tushdi...")


bot.infinity_polling(
    skip_pending=True
)
