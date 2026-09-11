# -*- coding: utf-8 -*-
# ==========================
# handlers/schedule_excel.py
# JADVALNI EXCEL'DAN YUKLASH
# ==========================
#
# O'qituvchilar jadvalni qog'ozda tuzib, keyin Excel'ga
# ko'chirishadi. Ilgari uni botga qayta kiritish kerak edi -
# 11 ta dars uchun ~85 ta tugma bosish. Endi o'sha faylning
# o'zini yuborsa bo'ladi.
#
# Oqim:
#   1. fayl qabul qilinadi va o'qiladi (services/schedule_import)
#   2. birinchi varaq o'qiladi (boshqasi e'tiborga olinmaydi)
#   3. tanilmagan fan nomlari so'raladi - javob lug'atga yoziladi
#   4. xona so'raladi (fayllarda xona ustuni yo'q)
#   5. bazada topilmagan o'quvchilar aytiladi, darsi tashlanadi
#   6. NIMA O'ZGARISHI ko'rsatiladi va tasdiqlanadi
#
# Tasdiqlanmaguncha bazaga hech narsa yozilmaydi.
# ==========================


import os
import tempfile

from telebot import types

from services import schedule_import

from database import (
    is_cancel_text,
    can,
    get_rooms,
    search_students,
    get_subject_aliases,
    add_subject_alias,
    get_teacher_slots,
    get_slot_students,
    get_slot_class,
    get_slot_duration,
    create_slot,
    update_slot_schedule,
    delete_slot,
    add_student_to_slot,
    find_room_conflict,
    log_action,
)


BUTTON = "📥 Jadvalni Excel'dan yuklash"


# chat_id -> import holati (fayl natijasi, savollar, tanlangan varaq)
ctx = {}


MAX_SIZE = 5 * 1024 * 1024


def register_schedule_excel(bot, selected_teachers):


    # ==========================
    # BOSHLASH
    # ==========================


    @bot.message_handler(func=lambda m: m.text == BUTTON)
    def start_import(message):

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

        ctx[chat_id] = {"teacher": teacher}

        sent = bot.send_message(
            chat_id,
            "📥 Dars jadvali yozilgan Excel faylini yuboring.\n\n"
            "O'zingiz to'ldirib yurgan odatdagi fayl bo'lsa bo'ldi - "
            "alohida shablon kerak emas.\n\n"
            "Bekor qilish uchun /cancel."
        )

        bot.register_next_step_handler(sent, receive_file)


    def receive_file(message):

        chat_id = message.chat.id

        if is_cancel_text(getattr(message, "text", None)):

            ctx.pop(chat_id, None)

            bot.send_message(chat_id, "❌ Bekor qilindi.")

            return

        document = getattr(message, "document", None)

        if not document:

            sent = bot.send_message(
                chat_id,
                "📎 Excel faylini biriktirib yuboring (.xlsx)."
            )

            bot.register_next_step_handler(sent, receive_file)

            return

        name = (document.file_name or "").lower()

        if not name.endswith((".xlsx", ".xlsm")):

            sent = bot.send_message(
                chat_id,
                "❌ Bu .xlsx fayl emas.\n\n"
                "Eski .xls bo'lsa, Excel'da «Farqli saqlash» → "
                ".xlsx qilib saqlang."
            )

            bot.register_next_step_handler(sent, receive_file)

            return

        if (document.file_size or 0) > MAX_SIZE:

            bot.send_message(chat_id, "❌ Fayl juda katta (5 MB dan ortiq).")

            return

        wait = bot.send_message(chat_id, "⏳ Fayl o'qilmoqda...")

        path = None

        try:

            info = bot.get_file(document.file_id)

            content = bot.download_file(info.file_path)

            # openpyxl faylni diskdan o'qiydi - vaqtinchalik
            # nusxa yaratamiz va darhol o'chiramiz

            handle, path = tempfile.mkstemp(suffix=".xlsx")

            with os.fdopen(handle, "wb") as target:
                target.write(content)

            result = schedule_import.read_workbook(
                path, aliases=get_subject_aliases()
            )

        except Exception as error:

            bot.edit_message_text(
                "❌ Faylni o'qib bo'lmadi.\n\n" + str(error)[:300],
                chat_id, wait.message_id
            )

            return

        finally:

            if path and os.path.exists(path):

                try:
                    os.remove(path)

                except OSError:
                    pass

        data = ctx.setdefault(chat_id, {})

        data["result"] = result

        bot.delete_message(chat_id, wait.message_id)

        use_sheet(chat_id)


    # ==========================
    # FAYLNI QABUL QILISH
    # ==========================
    #
    # Faqat birinchi varaq o'qiladi - o'qituvchi bitta chorak
    # jadvalini bitta faylda yuboradi. Qaysi varaq kerakligini
    # so'rash ham, taxmin qilish ham kerak emas.


    def use_sheet(chat_id):

        data = ctx.get(chat_id) or {}

        sheet = (data.get("result") or {}).get("sheet") or {}

        if not sheet.get("lessons"):

            bot.send_message(
                chat_id,
                "❌ Faylda dars topilmadi.\n\n"
                "Varaqda kun nomlari (Dushanba, Seshanba...) va "
                "vaqtlar borligiga ishonch hosil qiling."
            )

            ctx.pop(chat_id, None)

            return

        data["sheet"] = sheet

        data["lessons"] = [dict(lesson) for lesson in sheet["lessons"]]

        meta = sheet["meta"]

        summary = ["📄 Fayl o'qildi"]

        if meta.get("teacher"):
            summary.append("👨‍🏫 " + meta["teacher"])

        if meta.get("quarter"):
            summary.append("📆 " + meta["quarter"] + "-chorak")

        summary.append("📚 " + str(len(data["lessons"])) + " ta dars")

        bot.send_message(chat_id, "\n".join(summary))

        # faqat shu darslarga tegishli savollar

        keys = {
            lesson["alias_key"]
            for lesson in data["lessons"]
            if lesson.get("alias_key")
        }

        data["questions"] = [
            question
            for question in data["result"].get("questions") or []
            if question.get("key") in keys
        ]

        ask_next_question(chat_id)


    # ==========================
    # TANILMAGAN FAN NOMLARI
    # ==========================


    def ask_next_question(chat_id):

        data = ctx.get(chat_id) or {}

        questions = data.get("questions") or []

        if not questions:

            ask_room(chat_id)

            return

        question = questions[0]

        markup = types.InlineKeyboardMarkup()

        if question.get("guess"):

            markup.add(
                types.InlineKeyboardButton(
                    "✅ Ha, " + question["guess"],
                    callback_data="imp:ans:yes"
                )
            )

        for name in schedule_import.known_subjects():

            markup.add(
                types.InlineKeyboardButton(
                    name,
                    callback_data="imp:ans:set:" + name[:40]
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "⏭ Bu darslarni tashlab ket",
                callback_data="imp:ans:skip"
            )
        )

        text = "❓ «" + question["text"] + "» - bu qaysi fan?"

        if question.get("count", 1) > 1:
            text += "\n\nFaylda " + str(question["count"]) + " joyda uchradi."

        if question.get("guess"):
            text += "\n\nTaxminim: " + question["guess"]

        bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(func=lambda c: c.data.startswith("imp:ans:"))
    def answer_question(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data or not data.get("questions"):

            bot.answer_callback_query(call.id, "Muddati o'tdi")

            return

        question = data["questions"].pop(0)

        action = call.data[len("imp:ans:"):]

        subject = None

        if action == "yes":
            subject = question.get("guess")

        elif action.startswith("set:"):
            subject = action[4:]

        apply_answer(data, question, subject)

        if subject:

            add_subject_alias(
                schedule_import.normalize(question["text"]),
                subject,
                data.get("teacher")
            )

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            "«" + question["text"] + "» → "
            + (subject or "tashlab ketildi"),
            chat_id, call.message.message_id
        )

        ask_next_question(chat_id)


    def apply_answer(data, question, subject):
        """
        Javobni xotiradagi darslarga qo'llaydi.

        Har bir dars o'z `alias_key` ini olib yuradi - fan qaysi
        yozuvdan olingani. Shu sababli javob aynan o'sha darslarga
        tegadi, boshqasiga emas.
        """

        key = question.get("key") or schedule_import.normalize(
            question["text"]
        )

        kept = []

        for lesson in data.get("lessons") or []:

            if lesson.get("alias_key") != key:

                kept.append(lesson)

                continue

            if subject is None:
                continue

            lesson["subject"] = subject

            lesson["alias_key"] = None

            kept.append(lesson)

        data["lessons"] = kept


    # ==========================
    # XONA
    # ==========================
    #
    # O'qituvchilarning fayllarida xona ustuni yo'q - ular buni
    # qog'ozda hech qachon yozmagan. Shuning uchun bir marta
    # suhbatda so'raymiz va xonasi ko'rsatilmagan hamma darsga
    # qo'yamiz. Katakda qavs ichida xona yozilgan bo'lsa
    # (masalan "13:00-14:35 (1/23)") - o'sha ustun turadi.


    def ask_room(chat_id):

        markup = types.InlineKeyboardMarkup()

        row = []

        for room in get_rooms():

            row.append(
                types.InlineKeyboardButton(
                    room["label"],
                    callback_data="imp:room:" + str(room["code"])[:30]
                )
            )

            if len(row) == 3:

                markup.row(*row)

                row = []

        if row:
            markup.row(*row)

        bot.send_message(
            chat_id,
            "🚪 Darslaringiz qaysi xonada o'tadi?\n\n"
            "Faylda xona yozilmagan - shuning uchun bir marta "
            "so'rayapman. Ayrim darslar boshqa xonada bo'lsa, "
            "keyin bittalab tuzatasiz.",
            reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("imp:room:"))
    def pick_room(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data:

            bot.answer_callback_query(call.id, "Muddati o'tdi")

            return

        room = call.data[len("imp:room:"):]

        for lesson in data.get("lessons") or []:

            if not lesson.get("room"):
                lesson["room"] = room

        data["room"] = room

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            "🚪 Xona: " + room, chat_id, call.message.message_id
        )

        resolve_students(chat_id)


    # ==========================
    # O'QUVCHILARNI TOPISH
    # ==========================
    #
    # Faylda faqat ism yozilgan. Bazada o'quvchi ITV raqami bilan
    # aniqlanadi, ism esa takrorlanishi mumkin - shuning uchun
    # topilmagan yoki bir nechta mos kelgan holatda dars
    # TASHLANADI va o'qituvchidan avval o'quvchini qo'shish
    # so'raladi. Bot o'zi o'quvchi yaratmaydi: ITV raqami,
    # tug'ilgan sana va badal faylda yo'q.


    def resolve_students(chat_id):

        data = ctx.get(chat_id) or {}

        sheet = data.get("sheet") or {}

        groups = sheet.get("groups") or {}

        missing = []

        kept = []

        cache = {}

        def lookup(name):

            if name in cache:
                return cache[name]

            found = [
                row for row in search_students(name)
                if schedule_import.normalize(row[1])
                == schedule_import.normalize(name)
            ]

            cache[name] = found

            return found

        for lesson in data.get("lessons") or []:

            if lesson.get("is_group"):

                members = groups.get(lesson["who"]) or []

                people = []

                gaps = []

                for student, _ in members:

                    found = lookup(student)

                    if len(found) == 1:
                        people.append((found[0][1], found[0][0]))

                    else:
                        gaps.append(student)

                missing.extend(gaps)

                # guruhning o'zi qoladi - topilgan a'zolari bilan.
                # Butun guruh darsini bitta bola uchun tashlash
                # noto'g'ri bo'lardi.

                lesson["people"] = people

                kept.append(lesson)

                continue

            found = lookup(lesson["who"])

            if len(found) != 1:

                missing.append(lesson["who"])

                continue

            lesson["people"] = [(found[0][1], found[0][0])]

            kept.append(lesson)

        dropped = len(data.get("lessons") or []) - len(kept)

        data["lessons"] = kept

        data["missing"] = sorted(set(missing))

        if data["missing"]:

            bot.send_message(
                chat_id,
                "⚠️ Bu o'quvchilar bazada topilmadi:\n\n"
                + "\n".join("• " + name for name in data["missing"])
                + "\n\nUlarning darslari yuklanmadi ("
                + str(dropped) + " ta).\n\n"
                "Avval «👨‍🎓 O'quvchilar ro'yxati» bo'limidan "
                "ularni qo'shing, keyin faylni qayta yuboring - "
                "qolgan darslar takrorlanmaydi."
            )

        show_plan(chat_id)


    # ==========================
    # NIMA O'ZGARADI
    # ==========================


    def current_lessons(teacher):
        """Bazadagi darslarni schedule_import tushunadigan ko'rinishga soladi."""

        rows = []

        for slot_id, subject, day, time, room in get_teacher_slots(teacher):

            start = schedule_import.parse_clock(time)

            if start is None:
                continue

            duration = get_slot_duration(slot_id)

            students = [name for _, name, _ in get_slot_students(slot_id)]

            rows.append({
                "slot_id": slot_id,
                "day": day,
                "subject": subject,
                "class": get_slot_class(slot_id) or "",
                "who": students[0] if students else "",
                "people": students,
                "start": start,
                "end": start + duration,
                "room": room,
            })

        return rows


    def show_plan(chat_id):

        data = ctx.get(chat_id) or {}

        lessons = data.get("lessons") or []

        if not lessons:

            bot.send_message(
                chat_id,
                "❌ Yuklanadigan dars qolmadi.\n\n"
                "O'quvchilarni qo'shib, faylni qayta yuboring."
            )

            ctx.pop(chat_id, None)

            return

        current = current_lessons(data["teacher"])

        plan = schedule_import.plan_changes(current, lessons)

        data["plan"] = plan

        lines = schedule_import.describe_changes(plan)

        # o'quvchisi bor darsni o'chirish qaytarilmaydi - alohida
        # ogohlantirish

        risky = [
            item for item in plan["remove"] if item.get("people")
        ]

        text = "📋 Nimalar o'zgaradi:\n\n" + "\n".join(lines[:40])

        if len(lines) > 40:
            text += "\n\n... va yana " + str(len(lines) - 40) + " ta o'zgarish."

        if risky:

            text += (
                "\n\n⚠️ O'chadigan " + str(len(risky)) + " ta darsda "
                "o'quvchi bor. O'chirilgandan keyin qaytarib bo'lmaydi."
            )

        issues = [
            issue for issue in (data.get("result") or {}).get("issues") or []
            if issue.get("sheet") == data["sheet"]["meta"]["sheet"]
        ]

        if issues:

            text += "\n\n🔎 Faylda topilgan xatolar:\n" + "\n".join(
                ("❌ " if issue["level"] == "error" else "⚠️ ") + issue["text"]
                for issue in issues[:10]
            )

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="imp:go"),
            types.InlineKeyboardButton("❌ Bekor", callback_data="imp:no"),
        )

        bot.send_message(chat_id, text[:4000], reply_markup=markup)


    @bot.callback_query_handler(func=lambda c: c.data == "imp:no")
    def cancel_plan(call):

        ctx.pop(call.message.chat.id, None)

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            "❌ Bekor qilindi. Bazaga hech narsa yozilmadi.",
            call.message.chat.id, call.message.message_id
        )


    # ==========================
    # QO'LLASH
    # ==========================


    @bot.callback_query_handler(func=lambda c: c.data == "imp:go")
    def apply_plan(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data or not data.get("plan"):

            bot.answer_callback_query(call.id, "Muddati o'tdi")

            return

        bot.answer_callback_query(call.id)

        teacher = data["teacher"]

        plan = data["plan"]

        added = 0

        moved = 0

        removed = 0

        blocked = []

        for item in plan["remove"]:

            delete_slot(item["slot_id"])

            removed += 1

        for change in plan["move"]:

            old = change["old"]
            new = change["new"]

            time = schedule_import.format_time(new["start"])

            busy = find_room_conflict(
                new["day"], time, new["room"],
                new["minutes"], exclude_slot_id=old["slot_id"]
            )

            if busy:

                blocked.append(_busy_line(new, busy))

                continue

            update_slot_schedule(
                old["slot_id"], new["day"], time,
                new["room"], new["minutes"]
            )

            moved += 1

        for lesson in plan["add"]:

            time = schedule_import.format_time(lesson["start"])

            busy = find_room_conflict(
                lesson["day"], time, lesson["room"], lesson["minutes"]
            )

            if busy:

                blocked.append(_busy_line(lesson, busy))

                continue

            slot_id = create_slot(
                teacher,
                lesson["subject"],
                lesson["day"],
                time,
                lesson["room"],
                lesson["minutes"],
                lesson.get("class") or None
            )

            for student, owner in lesson.get("people") or []:
                add_student_to_slot(slot_id, student, owner)

            added += 1

        log_action(
            teacher,
            "excel_import",
            data["sheet"]["meta"]["sheet"],
            "qo'shildi=" + str(added)
            + " siljidi=" + str(moved)
            + " o'chdi=" + str(removed)
        )

        text = (
            "✅ Jadval yangilandi.\n\n"
            "➕ qo'shildi: " + str(added) + "\n"
            "🔀 siljidi: " + str(moved) + "\n"
            "➖ o'chirildi: " + str(removed)
        )

        if blocked:

            text += (
                "\n\n🚪 Xona band bo'lgani uchun "
                + str(len(blocked)) + " ta dars qo'yilmadi:\n"
                + "\n".join(blocked[:10])
            )

        ctx.pop(chat_id, None)

        bot.edit_message_text(
            text[:4000], chat_id, call.message.message_id
        )


def _busy_line(lesson, busy):

    return (
        "• " + lesson["day"] + " "
        + schedule_import.format_time(lesson["start"])
        + " " + str(lesson["room"]) + "-xona → band ("
        + str(busy[1]) + ")"
    )
