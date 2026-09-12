# -*- coding: utf-8 -*-
# ==========================
# handlers/tech_staff.py
# TEXNIK XODIMLAR - XO'JALIK MUDIRI PANELI
# ==========================
#
# Farrosh, qorovul, elektrik, duradgor... Ular botdan
# foydalanmaydi: yozuvini va hujjatlarini xo'jalik mudiri
# yuritadi - xuddi o'qituvchi o'quvchinikini yuritganidek.
#
# Hujjatlar Drive'ga boradi, bazada faqat havola qoladi.
# ==========================


import os

from telebot import types

from database import (
    is_cancel_text,
    get_staff_role,
    log_action,
    TECH_DOCUMENT_TYPES,
    get_tech_positions,
    add_tech_position,
    set_position_night_fee,
    add_tech_staff,
    get_tech_staff,
    get_tech_staff_one,
    dismiss_tech_staff,
    save_tech_document,
    list_tech_documents,
    get_tech_missing_documents,
)

from services import gdrive


BUTTON_STAFF = "👷 Texnik xodimlar"
BUTTON_POSITIONS = "🧰 Lavozimlar"

MENU_BUTTONS = [BUTTON_STAFF, BUTTON_POSITIONS]


# chat_id -> yarim to'ldirilgan forma
ctx = {}


def safe_name(text):
    """Drive papkasi uchun xavfsiz nom."""

    bad = '\\/:*?"<>|'

    return "".join("_" if ch in bad else ch for ch in str(text or "")).strip()


def _money(value):
    """1067640 -> '1 067 640'"""

    try:
        return "{:,}".format(int(value)).replace(",", " ")
    except (TypeError, ValueError):
        return str(value or "0")


def register_tech_staff(bot, admin_ids):

    def _mudir(chat_id):
        """Shu odam texnik xodimlarni yuritishga haqlimi."""

        return chat_id in admin_ids or get_staff_role(chat_id) == "xojalik_mudiri"


    def _deny(chat_id):

        bot.send_message(chat_id, "❌ Bu bo'lim xo'jalik mudiri uchun.")


    # ==========================
    # XODIMLAR RO'YXATI
    # ==========================


    @bot.message_handler(func=lambda m: m.text == BUTTON_STAFF)
    def staff_list(message):

        chat_id = message.chat.id

        if not _mudir(chat_id):

            _deny(chat_id)

            return

        show_staff_list(chat_id)


    def show_staff_list(chat_id, message_id=None):

        rows = get_tech_staff()

        markup = types.InlineKeyboardMarkup()

        for staff_id, name, position, _tabel, _stavka, _status in rows:

            yetishmayapti = len(get_tech_missing_documents(staff_id))

            belgi = " ⚠️" if yetishmayapti else ""

            markup.add(
                types.InlineKeyboardButton(
                    name + " · " + position + belgi,
                    callback_data="tx:one:" + str(staff_id)
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "➕ Yangi xodim",
                callback_data="tx:new"
            )
        )

        text = "👷 Texnik xodimlar: " + str(len(rows)) + " ta"

        if not rows:
            text += "\n\nHali xodim qo'shilmagan."
        else:
            text += "\n\n⚠️ - hujjatlari to'liq emas."

        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)


    # ==========================
    # XODIM KARTASI
    # ==========================


    @bot.callback_query_handler(func=lambda c: c.data.startswith("tx:one:"))
    def staff_card(call):

        chat_id = call.message.chat.id

        if not _mudir(chat_id):

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        staff_id = int(call.data.split(":", 2)[2])

        bot.answer_callback_query(call.id)

        show_staff_card(chat_id, staff_id, call.message.message_id)


    def show_staff_card(chat_id, staff_id, message_id=None):

        row = get_tech_staff_one(staff_id)

        if not row:
            return

        _id, name, position, tabel, stavka, status = row

        yetishmayapti = get_tech_missing_documents(staff_id)

        bor = list_tech_documents(staff_id)

        text = (
            "👤 " + name + "\n"
            "🧰 " + position + "\n"
            "🔢 Tabel raqami: " + (tabel or "—") + "\n"
            "💵 Stavka: " + _money(stavka) + " so'm\n\n"
            "📎 Yuklangan hujjatlar: " + str(len(bor)) + " ta"
        )

        if yetishmayapti:

            text += "\n\n⚠️ Yetishmayapti:\n" + "\n".join(
                "• " + label for label, _ in yetishmayapti
            )

        else:
            text += "\n\n✅ Hujjatlar to'liq."

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "📎 Hujjat yuklash",
                callback_data="tx:doc:" + str(staff_id)
            )
        )

        if status == "ishlayapti":

            markup.add(
                types.InlineKeyboardButton(
                    "🚪 Ishdan bo'shatish",
                    callback_data="tx:fire:" + str(staff_id)
                )
            )

        markup.add(
            types.InlineKeyboardButton("‹ Orqaga", callback_data="tx:back")
        )

        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(func=lambda c: c.data == "tx:back")
    def back_to_list(call):

        bot.answer_callback_query(call.id)

        show_staff_list(call.message.chat.id, call.message.message_id)


    @bot.callback_query_handler(func=lambda c: c.data.startswith("tx:fire:"))
    def fire_staff(call):

        chat_id = call.message.chat.id

        if not _mudir(chat_id):

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        staff_id = int(call.data.split(":", 2)[2])

        row = get_tech_staff_one(staff_id)

        dismiss_tech_staff(staff_id)

        if row:
            log_action(
                "xo'jalik mudiri", "texnik xodimni bo'shatdi", row[1], row[2]
            )

        bot.answer_callback_query(call.id, "Bo'shatildi")

        show_staff_list(chat_id, call.message.message_id)


    # ==========================
    # YANGI XODIM
    # ==========================
    #
    # Avval lavozim tanlanadi (ro'yxatdan), keyin uch qadam matn:
    # ism, tabel raqami, stavka.


    @bot.callback_query_handler(func=lambda c: c.data == "tx:new")
    def new_staff(call):

        chat_id = call.message.chat.id

        if not _mudir(chat_id):

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        positions = get_tech_positions()

        if not positions:

            bot.answer_callback_query(
                call.id,
                "Avval «🧰 Lavozimlar» dan lavozim qo'shing.",
                show_alert=True
            )

            return

        markup = types.InlineKeyboardMarkup()

        for _pid, name, _fee in positions:

            markup.add(
                types.InlineKeyboardButton(
                    name,
                    callback_data="tx:pos:" + name
                )
            )

        bot.answer_callback_query(call.id)

        bot.send_message(chat_id, "🧰 Lavozimni tanlang:", reply_markup=markup)


    @bot.callback_query_handler(func=lambda c: c.data.startswith("tx:pos:"))
    def new_staff_name(call):

        chat_id = call.message.chat.id

        if not _mudir(chat_id):

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        ctx[chat_id] = {"position": call.data.split(":", 2)[2]}

        bot.answer_callback_query(call.id)

        sent = bot.send_message(
            chat_id,
            "👤 Xodimning ism-familiyasini yozing:\n\n"
            "Masalan: Karimova Dilnoza"
        )

        bot.register_next_step_handler(sent, step_name)


    def step_name(message):

        chat_id = message.chat.id

        if is_cancel_text(message.text):

            ctx.pop(chat_id, None)

            bot.send_message(chat_id, "❌ Bekor qilindi.")

            return

        data = ctx.get(chat_id)

        if not data:
            return

        name = (message.text or "").strip()

        if not 3 <= len(name) <= 80:

            sent = bot.send_message(
                chat_id,
                "❌ Ism-familiya 3-80 belgi bo'lishi kerak. Qaytadan yozing:"
            )

            bot.register_next_step_handler(sent, step_name)

            return

        data["name"] = name

        sent = bot.send_message(
            chat_id,
            "🔢 Tabeldagi raqamini yozing:\n\n"
            "Tabel jadvalidagi «Tabel raqami» ustuni. Bilmasangiz - 0 yozing."
        )

        bot.register_next_step_handler(sent, step_tabel)


    def step_tabel(message):

        chat_id = message.chat.id

        if is_cancel_text(message.text):

            ctx.pop(chat_id, None)

            bot.send_message(chat_id, "❌ Bekor qilindi.")

            return

        data = ctx.get(chat_id)

        if not data:
            return

        data["tabel"] = (message.text or "").strip()

        sent = bot.send_message(
            chat_id,
            "💵 Stavka miqdorini yozing (faqat raqam):\n\n"
            "Masalan: 1067640"
        )

        bot.register_next_step_handler(sent, step_stavka)


    def step_stavka(message):

        chat_id = message.chat.id

        if is_cancel_text(message.text):

            ctx.pop(chat_id, None)

            bot.send_message(chat_id, "❌ Bekor qilindi.")

            return

        data = ctx.get(chat_id)

        if not data:
            return

        raqam = "".join(ch for ch in (message.text or "") if ch.isdigit())

        if not raqam:

            sent = bot.send_message(
                chat_id,
                "❌ Faqat raqam yozing. Masalan: 1067640"
            )

            bot.register_next_step_handler(sent, step_stavka)

            return

        staff_id = add_tech_staff(
            data["name"], data["position"], data.get("tabel", ""), int(raqam)
        )

        log_action(
            "xo'jalik mudiri", "texnik xodim qo'shdi",
            data["name"], data["position"]
        )

        ctx.pop(chat_id, None)

        bot.send_message(
            chat_id,
            "✅ Qo'shildi: " + data["name"] + " · " + data["position"] + "\n\n"
            "Endi hujjatlarini yuklang."
        )

        show_staff_card(chat_id, staff_id)


    # ==========================
    # LAVOZIMLAR
    # ==========================


    @bot.message_handler(func=lambda m: m.text == BUTTON_POSITIONS)
    def positions_list(message):

        chat_id = message.chat.id

        if not _mudir(chat_id):

            _deny(chat_id)

            return

        show_positions(chat_id)


    def show_positions(chat_id, message_id=None):

        rows = get_tech_positions()

        lines = []

        for _pid, name, fee in rows:

            qator = "• " + name

            if fee:
                qator += " (tungi navbat: " + _money(fee) + " so'm)"

            lines.append(qator)

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "➕ Yangi lavozim",
                callback_data="tx:newpos"
            )
        )

        text = "🧰 Lavozimlar: " + str(len(rows)) + " ta\n\n" + "\n".join(lines)

        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(func=lambda c: c.data == "tx:newpos")
    def new_position(call):

        chat_id = call.message.chat.id

        if not _mudir(chat_id):

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        bot.answer_callback_query(call.id)

        sent = bot.send_message(
            chat_id,
            "🧰 Yangi lavozim nomini yozing:\n\n"
            "Masalan: Bog'bon"
        )

        bot.register_next_step_handler(sent, step_position_name)


    def step_position_name(message):

        chat_id = message.chat.id

        if is_cancel_text(message.text):

            bot.send_message(chat_id, "❌ Bekor qilindi.")

            return

        name = (message.text or "").strip()

        if len(name) < 2:

            sent = bot.send_message(chat_id, "❌ Juda qisqa. Qaytadan yozing:")

            bot.register_next_step_handler(sent, step_position_name)

            return

        if add_tech_position(name):

            log_action("xo'jalik mudiri", "lavozim qo'shdi", name, "")

            bot.send_message(chat_id, "✅ Qo'shildi: " + name)

        else:
            bot.send_message(chat_id, "⚠️ Bunday lavozim allaqachon bor.")

        show_positions(chat_id)


    # ==========================
    # HUJJAT YUKLASH
    # ==========================


    @bot.callback_query_handler(func=lambda c: c.data.startswith("tx:doc:"))
    def pick_document_type(call):

        chat_id = call.message.chat.id

        if not _mudir(chat_id):

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        staff_id = int(call.data.split(":", 2)[2])

        yetishmayotgan = {key for _, key in get_tech_missing_documents(staff_id)}

        markup = types.InlineKeyboardMarkup()

        for label, key in TECH_DOCUMENT_TYPES.items():

            belgi = "" if key in yetishmayotgan else "✅ "

            markup.add(
                types.InlineKeyboardButton(
                    belgi + label,
                    callback_data="tx:dt:" + str(staff_id) + ":" + key
                )
            )

        bot.answer_callback_query(call.id)

        bot.send_message(
            chat_id,
            "📎 Qaysi hujjat?\n\n✅ - allaqachon yuklangan.",
            reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("tx:dt:"))
    def wait_for_file(call):

        chat_id = call.message.chat.id

        if not _mudir(chat_id):

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        _, _, staff_id, doc_key = call.data.split(":", 3)

        ctx[chat_id] = {"staff_id": int(staff_id), "doc": doc_key}

        bot.answer_callback_query(call.id)

        bot.send_message(
            chat_id,
            "📤 Faylni yuboring (rasm yoki hujjat).\n\n"
            "Bekor qilish uchun /cancel yozing."
        )


    @bot.message_handler(
        content_types=["document", "photo"],
        func=lambda m: ctx.get(m.chat.id, {}).get("doc") is not None
    )
    def receive_file(message):

        chat_id = message.chat.id

        data = ctx.get(chat_id)

        if not data or not data.get("doc"):
            return

        row = get_tech_staff_one(data["staff_id"])

        if not row:

            ctx.pop(chat_id, None)

            bot.send_message(chat_id, "❌ Xodim topilmadi.")

            return

        if message.content_type == "photo":
            file_id = message.photo[-1].file_id
            original_name = None
        else:
            file_id = message.document.file_id
            original_name = message.document.file_name

        wait_msg = bot.send_message(chat_id, "⏳ Drive'ga yuklanmoqda...")

        try:

            info = bot.get_file(file_id)

            content = bot.download_file(info.file_path)

            ext = os.path.splitext(info.file_path)[1]

            if not ext:
                ext = gdrive.detect_extension(content) or ".jpg"

            if original_name:
                filename = safe_name(original_name)
            else:
                filename = (
                    safe_name(row[1]).replace(" ", "_")
                    + "_" + data["doc"] + ext
                )

            drive_id, link = gdrive.upload_bytes(
                content,
                filename,
                ["Texnik xodimlar", safe_name(row[2]), safe_name(row[1]), data["doc"]]
            )

            save_tech_document(
                staff_id=data["staff_id"],
                document_type=data["doc"],
                file_name=filename,
                file_size=len(content),
                drive_file_id=drive_id,
                drive_link=link,
                file_id=file_id
            )

            log_action(
                "xo'jalik mudiri", "texnik xodim hujjatini yukladi",
                row[1], data["doc"]
            )

            bot.edit_message_text("✅ Yuklandi.", chat_id, wait_msg.message_id)

        except Exception as error:

            bot.edit_message_text(
                "❌ Yuklab bo'lmadi: " + str(error)[:200],
                chat_id,
                wait_msg.message_id
            )

            return

        finally:
            ctx.pop(chat_id, None)

        show_staff_card(chat_id, row[0])
