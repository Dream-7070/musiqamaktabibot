# -*- coding: utf-8 -*-
# ==========================
# handlers/tabel.py
# OYLIK TABEL - XO'JALIK MUDIRI
# ==========================
#
# Tabel ISTISNO bo'yicha to'ldiriladi: hamma kun "+" deb turadi,
# mudir faqat kasallik/ta'til/safar/sababsiz kunlarni belgilaydi.
# Oyiga 480 emas, 5-10 marta bosiladi.
#
# Kunlar oralig'i matn bilan kiritiladi ("6-10") - kasallik ham,
# ta'til ham bir necha kun davom etadi, har kunini alohida bosish
# ma'nosiz bo'lardi.
# ==========================


import os
import tempfile

from datetime import date

from telebot import types

from database import (
    is_cancel_text,
    get_staff_role,
    log_action,
    get_school_name,
    TABEL_MARKS,
    days_in_month,
    suggested_rest_days,
    get_rest_days,
    set_rest_days,
    toggle_rest_day,
    is_month_confirmed,
    set_mark_range,
    get_marks,
    month_row,
    get_tech_staff,
    get_tech_staff_one,
)

from services.tabel_export import export_tabel_to_excel, tabel_filename, OYLAR


BUTTON = "📋 Tabel"


# chat_id -> {"year":..., "month":..., "staff_id":..., "mark":...}
ctx = {}


def register_tabel(bot, admin_ids):

    def _allowed(chat_id):

        return chat_id in admin_ids or get_staff_role(chat_id) == "xojalik_mudiri"


    def _oy(chat_id):
        """Tanlangan oy yoki bugungi oy."""

        data = ctx.get(chat_id) or {}

        if data.get("year"):
            return data["year"], data["month"]

        bugun = date.today()

        return bugun.year, bugun.month


    # ==========================
    # OY TANLASH
    # ==========================


    @bot.message_handler(func=lambda m: m.text == BUTTON)
    def open_tabel(message):

        chat_id = message.chat.id

        if not _allowed(chat_id):

            bot.send_message(chat_id, "❌ Tabel xo'jalik mudiri uchun.")

            return

        show_month_picker(chat_id)


    def show_month_picker(chat_id, message_id=None):

        bugun = date.today()

        markup = types.InlineKeyboardMarkup()

        # joriy oy va oldingi ikkitasi - odatda shular kerak bo'ladi

        year, month = bugun.year, bugun.month

        for _ in range(3):

            belgi = "✅ " if is_month_confirmed(year, month) else ""

            markup.add(
                types.InlineKeyboardButton(
                    belgi + OYLAR[month - 1] + " " + str(year),
                    callback_data="tb:oy:" + str(year) + ":" + str(month)
                )
            )

            month -= 1

            if month == 0:
                month, year = 12, year - 1

        text = (
            "📋 Tabel\n\n"
            "Qaysi oy?\n\n"
            "✅ - dam kunlari tasdiqlangan."
        )

        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(func=lambda c: c.data.startswith("tb:oy:"))
    def pick_month(call):

        chat_id = call.message.chat.id

        if not _allowed(chat_id):

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        _, _, year, month = call.data.split(":")

        ctx[chat_id] = {"year": int(year), "month": int(month)}

        bot.answer_callback_query(call.id)

        if is_month_confirmed(int(year), int(month)):
            show_staff(chat_id, call.message.message_id)
        else:
            show_rest_days(chat_id, call.message.message_id)


    # ==========================
    # DAM KUNLARINI TASDIQLASH
    # ==========================
    #
    # Bot yakshanba va qat'iy sanali bayramlarni o'zi biladi.
    # Ko'chma bayramlar (Ramazon, Qurbon hayiti) har yili siljiydi -
    # ularni mudir shu yerda qo'shadi.


    def show_rest_days(chat_id, message_id=None):

        year, month = _oy(chat_id)

        tanlangan = get_rest_days(year, month) or suggested_rest_days(year, month)

        ctx.setdefault(chat_id, {})["rest"] = list(tanlangan)

        markup = types.InlineKeyboardMarkup()

        qator = []

        for day in range(1, days_in_month(year, month) + 1):

            belgi = "🔴" if day in tanlangan else ""

            qator.append(
                types.InlineKeyboardButton(
                    belgi + str(day),
                    callback_data="tb:dam:" + str(day)
                )
            )

            if len(qator) == 7:
                markup.row(*qator)
                qator = []

        if qator:
            markup.row(*qator)

        markup.add(
            types.InlineKeyboardButton(
                "✅ Tasdiqlash",
                callback_data="tb:damok"
            )
        )

        text = (
            "📅 " + OYLAR[month - 1] + " " + str(year) + " - dam kunlari\n\n"
            "Bot yakshanba va bayramlarni o'zi belgiladi (🔴).\n"
            "Ko'chma bayram (Ramazon, Qurbon hayiti) yoki qo'shimcha "
            "dam kuni bo'lsa - sanani bosing.\n\n"
            "Tanlangan: " + ", ".join(str(d) for d in sorted(tanlangan))
        )

        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(func=lambda c: c.data.startswith("tb:dam:"))
    def toggle_day(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data:

            bot.answer_callback_query(call.id, "Muddati o'tdi")

            return

        day = int(call.data.split(":", 2)[2])

        tanlangan = set(data.get("rest") or [])

        if day in tanlangan:
            tanlangan.discard(day)
        else:
            tanlangan.add(day)

        data["rest"] = sorted(tanlangan)

        bot.answer_callback_query(call.id)

        _qayta_chiz_dam(chat_id, call.message.message_id)


    def _qayta_chiz_dam(chat_id, message_id):

        year, month = _oy(chat_id)

        tanlangan = ctx.get(chat_id, {}).get("rest") or []

        markup = types.InlineKeyboardMarkup()

        qator = []

        for day in range(1, days_in_month(year, month) + 1):

            belgi = "🔴" if day in tanlangan else ""

            qator.append(
                types.InlineKeyboardButton(
                    belgi + str(day),
                    callback_data="tb:dam:" + str(day)
                )
            )

            if len(qator) == 7:
                markup.row(*qator)
                qator = []

        if qator:
            markup.row(*qator)

        markup.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="tb:damok")
        )

        bot.edit_message_text(
            "📅 " + OYLAR[month - 1] + " " + str(year) + " - dam kunlari\n\n"
            "Tanlangan: " + ", ".join(str(d) for d in sorted(tanlangan)),
            chat_id, message_id, reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data == "tb:damok")
    def confirm_rest(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data:

            bot.answer_callback_query(call.id, "Muddati o'tdi")

            return

        year, month = _oy(chat_id)

        set_rest_days(year, month, data.get("rest") or [])

        log_action(
            "xo'jalik mudiri", "tabel dam kunlarini tasdiqladi",
            OYLAR[month - 1] + " " + str(year), ""
        )

        bot.answer_callback_query(call.id, "Tasdiqlandi")

        show_staff(chat_id, call.message.message_id)


    # ==========================
    # XODIMLAR VA BELGILAR
    # ==========================


    def show_staff(chat_id, message_id=None):

        year, month = _oy(chat_id)

        markup = types.InlineKeyboardMarkup()

        for staff_id, name, position, _t, _s, _st in get_tech_staff():

            r = month_row(staff_id, year, month)

            istisno = sum(r[key] for key in TABEL_MARKS)

            belgi = " · " + str(istisno) + " istisno" if istisno else ""

            markup.add(
                types.InlineKeyboardButton(
                    name + " (" + str(r["ishlangan"]) + " kun)" + belgi,
                    callback_data="tb:xod:" + str(staff_id)
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "📊 Excel qilib olish",
                callback_data="tb:excel"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "📅 Dam kunlarini o'zgartirish",
                callback_data="tb:damedit"
            )
        )

        text = (
            "📋 " + OYLAR[month - 1] + " " + str(year) + "\n\n"
            "Hamma kun \"+\" deb turibdi. Faqat istisnoni belgilang: "
            "xodimni bosing.\n\n"
            "Dam kunlari: " + ", ".join(str(d) for d in get_rest_days(year, month))
        )

        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(func=lambda c: c.data == "tb:damedit")
    def edit_rest(call):

        bot.answer_callback_query(call.id)

        show_rest_days(call.message.chat.id, call.message.message_id)


    @bot.callback_query_handler(func=lambda c: c.data.startswith("tb:xod:"))
    def staff_marks(call):

        chat_id = call.message.chat.id

        if not _allowed(chat_id):

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        staff_id = int(call.data.split(":", 2)[2])

        ctx.setdefault(chat_id, {})["staff_id"] = staff_id

        year, month = _oy(chat_id)

        row = get_tech_staff_one(staff_id)

        r = month_row(staff_id, year, month)

        belgilar = get_marks(staff_id, year, month)

        text = (
            "👤 " + (row[1] if row else "?") + "\n"
            "🧰 " + (row[2] if row else "") + "\n\n"
            "Ishlangan: " + str(r["ishlangan"]) + " kun · "
            + str(r["soat"]) + " soat\n"
        )

        if belgilar:

            text += "\nBelgilangan kunlar:\n"

            for day in sorted(belgilar):
                text += "  " + str(day) + " - " + belgilar[day] + "\n"

        text += "\nQaysi turdagi istisno qo'shamiz?"

        markup = types.InlineKeyboardMarkup()

        for belgi, izoh in TABEL_MARKS.items():

            markup.add(
                types.InlineKeyboardButton(
                    belgi + " - " + izoh,
                    callback_data="tb:mark:" + belgi
                )
            )

        if belgilar:

            markup.add(
                types.InlineKeyboardButton(
                    "🧹 Belgilarni tozalash",
                    callback_data="tb:clear"
                )
            )

        markup.add(
            types.InlineKeyboardButton("‹ Orqaga", callback_data="tb:orqaga")
        )

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            text, chat_id, call.message.message_id, reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data == "tb:orqaga")
    def back_to_staff(call):

        bot.answer_callback_query(call.id)

        show_staff(call.message.chat.id, call.message.message_id)


    @bot.callback_query_handler(func=lambda c: c.data.startswith("tb:mark:"))
    def ask_days(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data or not data.get("staff_id"):

            bot.answer_callback_query(call.id, "Muddati o'tdi")

            return

        data["mark"] = call.data.split(":", 2)[2]

        bot.answer_callback_query(call.id)

        sent = bot.send_message(
            chat_id,
            "📆 Qaysi kunlar?\n\n"
            "Bitta kun: 7\n"
            "Oraliq: 6-10\n\n"
            "Dam kunlariga tegilmaydi - ular \"D\" bo'lib qoladi."
        )

        bot.register_next_step_handler(sent, step_days)


    def step_days(message):

        chat_id = message.chat.id

        if is_cancel_text(message.text):

            bot.send_message(chat_id, "❌ Bekor qilindi.")

            return

        data = ctx.get(chat_id)

        if not data or not data.get("mark"):
            return

        matn = (message.text or "").replace(" ", "")

        try:

            if "-" in matn:
                boshi, oxiri = matn.split("-", 1)
            else:
                boshi = oxiri = matn

            boshi, oxiri = int(boshi), int(oxiri)

        except (TypeError, ValueError):

            sent = bot.send_message(
                chat_id,
                "❌ Tushunarsiz. Masalan: 7 yoki 6-10"
            )

            bot.register_next_step_handler(sent, step_days)

            return

        year, month = _oy(chat_id)

        if not 1 <= boshi <= days_in_month(year, month) or oxiri < boshi:

            sent = bot.send_message(
                chat_id,
                "❌ Bu oyda bunday kun yo'q. Qaytadan yozing:"
            )

            bot.register_next_step_handler(sent, step_days)

            return

        set_mark_range(
            data["staff_id"], year, month, boshi, oxiri, data["mark"]
        )

        row = get_tech_staff_one(data["staff_id"])

        log_action(
            "xo'jalik mudiri", "tabelga belgi qo'ydi",
            row[1] if row else "?",
            data["mark"] + " " + str(boshi) + "-" + str(oxiri)
        )

        data.pop("mark", None)

        bot.send_message(chat_id, "✅ Belgilandi.")

        show_staff(chat_id)


    @bot.callback_query_handler(func=lambda c: c.data == "tb:clear")
    def clear_marks(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data or not data.get("staff_id"):

            bot.answer_callback_query(call.id, "Muddati o'tdi")

            return

        year, month = _oy(chat_id)

        from database import set_mark

        for day in list(get_marks(data["staff_id"], year, month)):
            set_mark(data["staff_id"], year, month, day, None)

        bot.answer_callback_query(call.id, "Tozalandi")

        show_staff(chat_id, call.message.message_id)


    # ==========================
    # EXCEL
    # ==========================


    @bot.callback_query_handler(func=lambda c: c.data == "tb:excel")
    def send_excel(call):

        chat_id = call.message.chat.id

        if not _allowed(chat_id):

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        year, month = _oy(chat_id)

        bot.answer_callback_query(call.id)

        wait = bot.send_message(chat_id, "⏳ Tayyorlanmoqda...")

        path = os.path.join(tempfile.gettempdir(), tabel_filename(year, month))

        try:

            export_tabel_to_excel(year, month, path, get_school_name())

            with open(path, "rb") as handle:

                bot.send_document(
                    chat_id,
                    handle,
                    visible_file_name=tabel_filename(year, month),
                    caption="📋 " + OYLAR[month - 1] + " " + str(year) + " tabeli"
                )

            bot.edit_message_text("✅ Tayyor.", chat_id, wait.message_id)

        except Exception as error:

            bot.edit_message_text(
                "❌ Chiqarib bo'lmadi: " + str(error)[:200],
                chat_id, wait.message_id
            )

        finally:

            if os.path.exists(path):

                try:
                    os.remove(path)
                except OSError:
                    pass
