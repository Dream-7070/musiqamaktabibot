# -*- coding: utf-8 -*-
# ==========================
# handlers/schedule_suggest.py
# JADVAL TAKLIFLARI
# ==========================
#
# O'qituvchidan minimal so'rovlar asosida to'qnashuvsiz 
# jadval variantlarini hisoblaydi va Excel qilib beradi.
# ==========================


import os
import tempfile

from telebot import types

from database import (
    is_cancel_text,
    can,
    get_rooms,
    get_students,
    get_student_info,
    DAYS_OF_WEEK,
)

from services.schedule_planner import generate_variants
from services.schedule_export import export_variant_to_excel, variant_filename


BUTTON = "🧩 Jadval takliflari"


# chat_id -> {"teacher": ..., "students": {...}, "days": set(...), "rooms": set(...)}
ctx = {}


DEFAULT_SUBJECT = "Mutaxassislik"
DEFAULT_DURATION_MINUTES = 45


def register_schedule_suggest(bot, selected_teachers):


    # ==========================
    # BOSHLASH
    # ==========================


    @bot.message_handler(func=lambda m: m.text == BUTTON)
    def start_suggest(message):

        chat_id = message.chat.id

        teacher = selected_teachers.get(chat_id)

        if not teacher:

            bot.send_message(chat_id, "❌ Avval o'qituvchini tanlang.")

            return

        if not can(teacher, "can_manage_schedule"):

            bot.send_message(
                chat_id,
                "❌ Sizda dars jadvalini boshqarish huquqi yo'q."
            )

            return

        students = get_students(teacher)

        if not students:

            bot.send_message(
                chat_id,
                "❌ Avval «👨‍🎓 O'quvchilar ro'yxati» dan o'quvchi qo'shing."
            )

            return

        ctx[chat_id] = {
            "teacher": teacher,
            "students": {name: "none" for name in students},
            "order": students,
            "days": set(DAYS_OF_WEEK),
            "rooms": set()
        }

        show_student_picker(chat_id)


    # ==========================
    # O'QUVCHILAR
    # ==========================
    #
    # Har bir o'quvchi uchun smenani belgilash.
    # none (farqi yo'q) -> before (tushlikgacha) -> after (tushlikdan keyin) -> skip (kerak emas)


    def show_student_picker(chat_id, message_id=None):

        data = ctx.get(chat_id)

        if not data:
            return

        markup = types.InlineKeyboardMarkup()

        prefixes = {
            "none": "🕓 ",
            "before": "🌅 ",
            "after": "🌇 ",
            "skip": "🚫 "
        }

        for i, name in enumerate(data["order"]):

            state = data["students"][name]

            prefix = prefixes.get(state, "🕓 ")

            markup.add(
                types.InlineKeyboardButton(
                    prefix + name,
                    callback_data="sug:stu:" + str(i)
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "✅ Davom etish",
                callback_data="sug:stu:done"
            )
        )
        
        markup.add(
            types.InlineKeyboardButton(
                "❌ Bekor qilish", 
                callback_data="sug:cancel"
            )
        )

        text = (
            "👥 O'quvchilarni bosib, smenasini tanlang (har bosishda almashadi):\n"
            "🕓 farqi yo'q → 🌅 tushlikgacha → 🌇 tushlikdan keyin → 🚫 bu safar kerak emas\n\n"
            "Hech narsa bosmasangiz ham bo'ladi - hammasi \"farqi yo'q\" holatida "
            "ishtirok etadi."
        )

        if message_id:

            bot.edit_message_text(
                text, chat_id, message_id, reply_markup=markup
            )

        else:

            bot.send_message(
                chat_id, text, reply_markup=markup
            )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("sug:stu:"))
    def pick_student(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data:

            bot.answer_callback_query(call.id, "Muddati o'tdi")

            return

        action = call.data[len("sug:stu:"):]

        if action == "done":

            active = [s for s in data["students"].values() if s != "skip"]

            if not active:

                bot.answer_callback_query(
                    call.id, 
                    "❌ Hech bo'lmasa bitta o'quvchi tanlang.", 
                    show_alert=True
                )

                return
                
            bot.answer_callback_query(call.id)

            show_day_picker(chat_id, call.message.message_id)

            return

        index = int(action)

        name = data["order"][index]

        state = data["students"][name]

        next_state = {
            "none": "before",
            "before": "after",
            "after": "skip",
            "skip": "none"
        }

        data["students"][name] = next_state.get(state, "none")

        bot.answer_callback_query(call.id)

        show_student_picker(chat_id, call.message.message_id)


    # ==========================
    # KUNLAR
    # ==========================
    #
    # Qaysi kunlarda dars qo'yish ruxsat etilgan.
    # Barcha kunlar avvaldan tanlangan.


    def show_day_picker(chat_id, message_id=None):

        data = ctx.get(chat_id)

        if not data:
            return

        markup = types.InlineKeyboardMarkup()

        for i, day in enumerate(DAYS_OF_WEEK):

            prefix = "✅ " if day in data["days"] else "▫️ "

            markup.add(
                types.InlineKeyboardButton(
                    prefix + day,
                    callback_data="sug:day:" + str(i)
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "✅ Davom etish",
                callback_data="sug:day:done"
            )
        )
        
        markup.add(
            types.InlineKeyboardButton(
                "❌ Bekor qilish", 
                callback_data="sug:cancel"
            )
        )

        text = "📅 Qaysi kunlarda dars qo'yish mumkin? (barchasi tanlangan, keraksizini bosib olib tashlang)"

        if message_id:

            bot.edit_message_text(
                text, chat_id, message_id, reply_markup=markup
            )

        else:

            bot.send_message(
                chat_id, text, reply_markup=markup
            )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("sug:day:"))
    def pick_day(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data:

            bot.answer_callback_query(call.id, "Muddati o'tdi")

            return

        action = call.data[len("sug:day:"):]

        if action == "done":

            if not data["days"]:

                bot.answer_callback_query(
                    call.id, 
                    "❌ Hech bo'lmasa bitta kun qoldiring.", 
                    show_alert=True
                )

                return
                
            bot.answer_callback_query(call.id)

            show_room_picker(chat_id, call.message.message_id)

            return

        index = int(action)

        day = DAYS_OF_WEEK[index]

        if day in data["days"]:
            data["days"].remove(day)
        else:
            data["days"].add(day)

        bot.answer_callback_query(call.id)

        show_day_picker(chat_id, call.message.message_id)


    # ==========================
    # XONALAR
    # ==========================
    #
    # Qaysi xonalarga ruxsat etilgan.
    # Bo'sh qoldirilsa ixtiyoriy.


    def show_room_picker(chat_id, message_id=None):

        data = ctx.get(chat_id)

        if not data:
            return

        markup = types.InlineKeyboardMarkup()
        
        row = []

        for room in get_rooms():

            prefix = "✅ " if room["code"] in data["rooms"] else "▫️ "

            row.append(
                types.InlineKeyboardButton(
                    prefix + room["label"],
                    callback_data="sug:room:" + str(room["code"])
                )
            )
            
            if len(row) == 3:
                markup.row(*row)
                row = []
                
        if row:
            markup.row(*row)

        markup.add(
            types.InlineKeyboardButton(
                "✅ Yakunlash va hisoblash",
                callback_data="sug:room:done"
            )
        )
        
        markup.add(
            types.InlineKeyboardButton(
                "❌ Bekor qilish", 
                callback_data="sug:cancel"
            )
        )

        text = "🚪 Afzal ko'rilgan xonalar bo'lsa tanlang (ixtiyoriy - hech birini tanlamasangiz, bo'sh turgan istalgan xona ishlatiladi)."

        if message_id:

            bot.edit_message_text(
                text, chat_id, message_id, reply_markup=markup
            )

        else:

            bot.send_message(
                chat_id, text, reply_markup=markup
            )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("sug:room:"))
    def pick_room(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data:

            bot.answer_callback_query(call.id, "Muddati o'tdi")

            return

        action = call.data.split(":", 2)[2]

        if action == "done":
            
            bot.answer_callback_query(call.id)

            build_and_send(chat_id)

            return

        if action in data["rooms"]:
            data["rooms"].remove(action)
        else:
            data["rooms"].add(action)

        bot.answer_callback_query(call.id)

        show_room_picker(chat_id, call.message.message_id)


    # ==========================
    # HISOBLASH VA YUBORISH
    # ==========================


    def build_and_send(chat_id):

        data = ctx.get(chat_id)

        if not data:
            return

        shift_map = {
            "none": None, 
            "before": "tushlikgacha", 
            "after": "tushlikdan_keyin"
        }

        lessons = []

        for student in data["order"]:

            state = data["students"][student]

            if state == "skip":
                continue

            info = get_student_info(student, data["teacher"])

            class_name = info[5] if info else None

            lessons.append({
                "who": student,
                "student_teacher": data["teacher"],
                "subject": DEFAULT_SUBJECT,
                "class_name": class_name,
                "duration_minutes": DEFAULT_DURATION_MINUTES,
                "shift": shift_map[state],
                "is_group": False,
                "members": None,
            })

        allowed_days = [d for d in DAYS_OF_WEEK if d in data["days"]]

        preferred_rooms = list(data["rooms"]) if data["rooms"] else None

        wait = bot.send_message(chat_id, "⏳ Variantlar hisoblanmoqda...")

        try:

            variants = generate_variants(
                data["teacher"], 
                lessons, 
                allowed_days, 
                preferred_rooms, 
                max_variants=3
            )

        except Exception as error:

            bot.edit_message_text(
                "❌ Hisoblab bo'lmadi.\n\n" + str(error)[:300], 
                chat_id, 
                wait.message_id
            )
            
            return

        if not variants:

            bot.edit_message_text(
                "❌ Hech qanday variant chiqmadi. Kunlar yoki xonalarni ko'proq tanlab qayta urinib ko'ring.", 
                chat_id, 
                wait.message_id
            )

            ctx.pop(chat_id, None)

            return

        bot.delete_message(chat_id, wait.message_id)

        lines = []

        for index, variant in enumerate(variants, start=1):

            unplaced = len(variant.get("unplaced") or [])

            if unplaced == 0:

                lines.append(
                    "Variant " + str(index) + ": to'liq ("
                    + str(len(variant.get("lessons") or [])) + " ta dars)"
                )

            else:

                lines.append(
                    "Variant " + str(index) + ": to'liq emas - "
                    + str(unplaced) + " ta dars joy topmadi"
                )

        bot.send_message(
            chat_id,
            "📊 " + str(len(variants)) + " ta variant tayyor.\n\n"
            + "\n".join(lines) + "\n\n"
            "Har biri alohida fayl bo'lib keladi. Yoqqanini oching, "
            "kerak bo'lsa katakchani qo'lda tuzating va O'SHA faylni "
            "«📥 Jadvalni Excel'dan yuklash» orqali qayta yuboring.\n\n"
            "Bazaga hech narsa yozilmagan - bular faqat takliflar."
        )

        # Har bir variant ALOHIDA fayl: import faylning faqat
        # birinchi varag'ini o'qiydi, shuning uchun variantlarni
        # bitta faylning varaqlariga joylab bo'lmaydi.

        for index, variant in enumerate(variants, start=1):

            handle, path = tempfile.mkstemp(suffix=".xlsx")

            os.close(handle)

            try:

                export_variant_to_excel(
                    data["teacher"], variant, path, index
                )

                with open(path, "rb") as source:

                    bot.send_document(
                        chat_id,
                        source,
                        visible_file_name=variant_filename(
                            data["teacher"], index
                        ),
                        caption="Variant " + str(index) + (
                            "" if variant.get("complete", True)
                            else " (to'liq emas)"
                        )
                    )

            finally:

                if os.path.exists(path):

                    try:
                        os.remove(path)

                    except OSError:
                        pass

        ctx.pop(chat_id, None)


    # ==========================
    # BEKOR QILISH
    # ==========================


    @bot.callback_query_handler(func=lambda c: c.data == "sug:cancel")
    def cancel_suggest(call):

        chat_id = call.message.chat.id

        ctx.pop(chat_id, None)
        
        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            "❌ Bekor qilindi.", 
            chat_id, 
            call.message.message_id
        )
