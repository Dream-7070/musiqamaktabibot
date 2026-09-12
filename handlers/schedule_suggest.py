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
    plan_subject_names,
    get_subject_type,
    DAYS_OF_WEEK,
)

from data.curriculum import group_size_norm

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
            "days": set(),
            "rooms": set()
        }

        show_mode_picker(chat_id)


    # ==========================
    # DARS TURI
    # ==========================
    #
    # Yakka va guruhli darslar bir oqimda aralashib ketardi:
    # yakka dars kerak bo'lsa ham guruh ro'yxati chiqardi va
    # o'qituvchi uni qo'lda o'chirib chiqishga majbur bo'lardi.
    # Endi boshida tur tanlanadi va faqat o'shanikisi so'raladi.


    def show_mode_picker(chat_id, message_id=None):

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "👤 Yakka darslar",
                callback_data="sug:mode:yakka"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "👥 Guruhli darslar",
                callback_data="sug:mode:guruh"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "❌ Bekor qilish",
                callback_data="sug:cancel"
            )
        )

        text = (
            "🧩 Qanday dars uchun taklif kerak?\n\n"
            "👤 Yakka - har o'quvchiga alohida dars\n"
            "👥 Guruhli - solfedjio, musiqa adabiyoti kabi fanlar, "
            "guruhlar sinf bo'yicha tuziladi"
        )

        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(func=lambda c: c.data.startswith("sug:mode:"))
    def pick_mode(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data:

            bot.answer_callback_query(call.id, "Muddati o'tdi")

            return

        mode = call.data[len("sug:mode:"):]

        data["mode"] = mode

        bot.answer_callback_query(call.id)

        if mode == "yakka":

            show_student_picker(chat_id, call.message.message_id)

            return

        # guruhli: o'quvchilar bo'yicha smena so'ralmaydi - guruh
        # bir butun, uni bitta smenaga bog'lab bo'lmaydi

        data["groups"] = _build_group_proposal(data)

        if not data["groups"]:

            bot.edit_message_text(
                "❌ Rejada guruhli fan topilmadi.\n\n"
                "Guruhli fanlar o'qituvchining yo'nalishiga qarab "
                "belgilanadi - «👤 Yakka darslar» ni tanlang.",
                chat_id, call.message.message_id
            )

            ctx.pop(chat_id, None)

            return

        show_group_picker(chat_id, call.message.message_id)


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

        texts = {
            "none": "farqi yo'q",
            "before": "tushlikgacha",
            "after": "tushlikdan keyin",
            "skip": "qatnashmaydi"
        }

        for i, name in enumerate(data["order"]):

            state = data["students"][name]

            prefix = prefixes.get(state, "🕓 ")
            suffix = texts.get(state, "farqi yo'q")

            markup.add(
                types.InlineKeyboardButton(
                    prefix + name + " · " + suffix,
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
            "👥 O'quvchini bosing va smenasini tanlang.\n\n"
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

        markup = types.InlineKeyboardMarkup()

        options = [
            ("none", "🕓 Farqi yo'q"),
            ("before", "🌅 Tushlikgacha"),
            ("after", "🌇 Tushlikdan keyin"),
            ("skip", "🚫 Bu safar kerak emas")
        ]

        for opt_val, opt_text in options:
            btn_text = ("✅ " if state == opt_val else "") + opt_text
            markup.add(types.InlineKeyboardButton(btn_text, callback_data="sug:shift:" + str(index) + ":" + opt_val))

        markup.add(types.InlineKeyboardButton("‹ Orqaga", callback_data="sug:shift:" + str(index) + ":back"))

        bot.answer_callback_query(call.id)

        text = "👤 " + name + "\nDarsi qachon bo'lsin?"

        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)


    @bot.callback_query_handler(func=lambda c: c.data.startswith("sug:shift:"))
    def pick_shift(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data:

            bot.answer_callback_query(call.id, "Muddati o'tdi")

            return

        action = call.data[len("sug:shift:"):]

        parts = action.split(":")

        if len(parts) == 2:
            index_str, state = parts
            index = int(index_str)
            name = data["order"][index]

            if state != "back":
                data["students"][name] = state

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
                "🔄 Hammasini tanlash",
                callback_data="sug:day:all"
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

        # Ilgari bu ro'yxat "hammasi tanlangan, keraksizini olib
        # tashlang" tamoyilida edi. Foydalanuvchi esa kerakli kunni
        # bosardi va aynan o'sha kunlar o'chib ketardi - dars boshqa
        # kunlarga tushib qolardi. Endi teskari: bo'sh boshlanadi,
        # bosilgan kun TANLANADI. Tanlanganlar matnda ham yozilib
        # turadi, shunda xato darrov ko'rinadi.

        tanlangan = [d for d in DAYS_OF_WEEK if d in data["days"]]

        text = "📅 Dars qo'yish mumkin bo'lgan kunlarni tanlang.\n\n"

        if tanlangan:
            text += "Tanlangan: " + ", ".join(tanlangan)
        else:
            text += "Hozircha hech qaysi kun tanlanmagan."

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
                    "❌ Hech bo'lmasa bitta kun tanlang.",
                    show_alert=True
                )

                return

            bot.answer_callback_query(call.id)

            show_room_picker(chat_id, call.message.message_id)

            return

        if action == "all":

            data["days"] = set(DAYS_OF_WEEK)

            bot.answer_callback_query(call.id)

            show_day_picker(chat_id, call.message.message_id)

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

            # Guruhlar boshida tanlangan (tur so'ralganda), shuning
            # uchun bu yerda to'g'ridan-to'g'ri hisoblashga o'tamiz.

            build_and_send(chat_id)

            return

        if action in data["rooms"]:
            data["rooms"].remove(action)
        else:
            data["rooms"].add(action)

        bot.answer_callback_query(call.id)

        show_room_picker(chat_id, call.message.message_id)


    # ==========================
    # GURUHLI DARSLAR
    # ==========================
    #
    # Guruhli fanlar (solfedjio, musiqa adabiyoti...) rejadan
    # olinadi, guruhlar esa SINF bo'yicha tuziladi - shu maktabdagi
    # odatiy tartib. Bot taklif qiladi, o'qituvchi ko'rib chiqadi:
    # keraksiz guruhni o'chirib qo'yishi mumkin.


    def _build_group_proposal(data):
        """
        [{"subject", "class_name", "members", "on", "kam"}, ...]

        `members` - (ism, sinf) juftliklari: Excel eksporti shu
        ko'rinishni kutadi. `kam` - me'yordagi eng kichik guruhdan
        ham kam, ya'ni ogohlantirish kerak.
        """

        teacher = data["teacher"]

        subjects = [
            name for name in plan_subject_names(teacher)
            if get_subject_type(teacher, name) == "guruh"
        ]

        if not subjects:
            return []

        # sinf bo'yicha yig'amiz - faqat qatnashadigan o'quvchilar

        by_class = {}

        for student in data["order"]:

            if data["students"][student] == "skip":
                continue

            info = get_student_info(student, teacher)

            class_name = (info[5] if info else None) or "—"

            by_class.setdefault(class_name, []).append(student)

        groups = []

        for subject in subjects:

            low, high = group_size_norm(subject)

            for class_name in sorted(by_class):

                names = by_class[class_name]

                # me'yordan katta guruh bo'laklarga bo'linadi

                for start in range(0, len(names), high):

                    bolak = names[start:start + high]

                    # Avvaldan O'CHIRILGAN holda: rejada guruhli fan
                    # ko'p (bir o'qituvchida 5 tagacha), har sinf uchun
                    # alohida guruh chiqadi. Hammasi yoqilgan bo'lsa
                    # o'nlab dars hosil bo'lib, sig'masdan "to'liq emas"
                    # chiqardi va o'qituvchi hammasini qo'lda o'chirishga
                    # majbur bo'lardi.

                    groups.append({
                        "subject": subject,
                        "class_name": class_name,
                        "members": [(name, class_name) for name in bolak],
                        "on": False,
                        "kam": len(bolak) < low,
                    })

        return groups


    def show_group_picker(chat_id, message_id=None):

        data = ctx.get(chat_id)

        if not data:
            return

        markup = types.InlineKeyboardMarkup()

        for i, group in enumerate(data["groups"]):

            belgi = "✅ " if group["on"] else "▫️ "

            markup.add(
                types.InlineKeyboardButton(
                    belgi + group["subject"] + " · " + group["class_name"]
                    + "-sinf · " + str(len(group["members"])) + " ta"
                    + (" ⚠️" if group["kam"] else ""),
                    callback_data="sug:grp:" + str(i)
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "✅ Tasdiqlash va hisoblash",
                callback_data="sug:grp:done"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "❌ Bekor qilish",
                callback_data="sug:cancel"
            )
        )

        yoqilgan = [g for g in data["groups"] if g["on"]]

        text = (
            "👥 Guruhli fanlar ham kerakmi?\n\n"
            "Kerakli guruhni bosib qo'shing. Faqat yakka darslar "
            "kerak bo'lsa - hech narsa bosmasdan «Tasdiqlash»ni bosing.\n\n"
            "Guruhlar sinf bo'yicha tuzildi."
        )

        if yoqilgan:

            text += "\n\nTanlangan: " + str(len(yoqilgan)) + " ta guruh"

            if any(g["kam"] for g in yoqilgan):
                text += (
                    "\n⚠️ belgisi - guruh me'yordagidan kichik. "
                    "Taqiqlanmaydi, lekin e'tiborga oling."
                )

        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(func=lambda c: c.data.startswith("sug:grp:"))
    def pick_group(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data:

            bot.answer_callback_query(call.id, "Muddati o'tdi")

            return

        action = call.data[len("sug:grp:"):]

        if action == "done":

            if not any(g["on"] for g in data.get("groups") or []):

                bot.answer_callback_query(
                    call.id,
                    "❌ Hech bo'lmasa bitta guruh tanlang.",
                    show_alert=True
                )

                return

            bot.answer_callback_query(call.id)

            show_day_picker(chat_id, call.message.message_id)

            return

        index = int(action)

        group = data["groups"][index]

        group["on"] = not group["on"]

        bot.answer_callback_query(call.id)

        show_group_picker(chat_id, call.message.message_id)


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

        # Tur boshida tanlanadi: yakka bo'lsa guruh darslari umuman
        # qo'shilmaydi, guruhli bo'lsa yakka darslar qo'shilmaydi.

        mode = data.get("mode", "yakka")

        for student in (data["order"] if mode == "yakka" else []):

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

        # Tasdiqlangan guruhlar. Smena faqat HAMMA a'zoda bir xil
        # bo'lsagina qo'llanadi - aks holda guruhni bir smenaga
        # majburlab, joylashtirib bo'lmaydigan qilib qo'yardik.

        for group in (data.get("groups") or [] if mode == "guruh" else []):

            if not group["on"]:
                continue

            smenalar = {
                data["students"][name] for name, _ in group["members"]
            }

            umumiy = smenalar.pop() if len(smenalar) == 1 else "none"

            lessons.append({
                "who": group["subject"] + " · " + group["class_name"] + "-sinf",
                "student_teacher": data["teacher"],
                "subject": group["subject"],
                "class_name": group["class_name"],
                "duration_minutes": DEFAULT_DURATION_MINUTES,
                "shift": shift_map.get(umumiy),
                "is_group": True,
                "members": group["members"],
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
