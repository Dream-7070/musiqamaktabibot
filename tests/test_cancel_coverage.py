# -*- coding: utf-8 -*-
"""
Qamrov sinovi: `bot.register_next_step_handler` bilan matn kutayotgan
HAR BIR funksiyada bekor qilish himoyasi (is_cancel_text) borligini
tekshiradi.

Nega bu kerak: guard bo'lmasa, foydalanuvchi menyu tugmasini bosganda
tugma matni ma'lumot sifatida qabul qilinadi va bazaga yozilib ketadi.
Kelajakda yangi next-step funksiya qo'shilsa - shu sinov uni darrov
ushlaydi.
"""

import ast
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, ROOT)

FILES = [
    "main.py",
    "handlers/admin.py",
    "handlers/admin_permissions.py",
    "handlers/admin_rooms.py",
    "handlers/admin_schedule.py",
    "handlers/admin_staff.py",
    "handlers/parents.py",
    "handlers/schedule_excel.py",
    "handlers/students.py",
    "handlers/teacher_documents.py",
    "handlers/teacher_schedule.py",
]

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


def next_step_targets(tree):
    """register_next_step_handler(..., X) chaqiruvlaridagi X nomlari."""

    names = set()

    for node in ast.walk(tree):

        if not isinstance(node, ast.Call):
            continue

        func = node.func

        if not (isinstance(func, ast.Attribute)
                and func.attr == "register_next_step_handler"):
            continue

        if len(node.args) < 2:
            continue

        target = node.args[1]

        if isinstance(target, ast.Name):
            names.add(target.id)

    return names


def functions_by_name(tree):

    found = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            found.setdefault(node.name, []).append(node)

    return found


def has_cancel_guard(fn_node):
    """
    Funksiya tanasining boshida is_cancel_text tekshiruvi bormi.

    "Boshida" - birinchi bir necha ifodadan biri bo'lishi kifoya
    (ba'zi funksiyalar avval chat_id ni oladi).
    """

    for stmt in fn_node.body[:6]:

        for node in ast.walk(stmt):

            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "is_cancel_text"):
                return True

    return False


# ==========================
# 1. HAR BIR FAYL BO'YICHA QAMROV
# ==========================

total_targets = 0
covered = 0

for rel in FILES:

    path = os.path.join(ROOT, rel)

    tree = ast.parse(io.open(path, encoding="utf-8").read())

    targets = next_step_targets(tree)

    if not targets:
        continue

    defs = functions_by_name(tree)

    for name in sorted(targets):

        total_targets += 1

        nodes = defs.get(name)

        if not nodes:
            # funksiya boshqa modulda - bu yerda tekshirib bo'lmaydi
            check(rel + " :: " + name + " (ta'rifi topilmadi)", False)
            continue

        guarded = all(has_cancel_guard(n) for n in nodes)

        if guarded:
            covered += 1

        check(rel + " :: " + name, guarded)


# ==========================
# 2. UMUMIY QAMROV
# ==========================

check(
    "kamida 24 ta next-step funksiya topildi: " + str(total_targets),
    total_targets >= 24
)

check(
    "qamrov 100%: " + str(covered) + "/" + str(total_targets),
    covered == total_targets
)


# ==========================
# 3. is_cancel_text O'ZI TO'G'RI ISHLAYDI
# ==========================

import database as db

check("menyu tugmasi aniqlandi", db.is_cancel_text("⬅️ Ortga") is True)
check("/cancel aniqlandi", db.is_cancel_text("/cancel") is True)
check("bo'sh joyli /cancel ham", db.is_cancel_text("  /cancel  ") is True)
check("oddiy ism o'tadi", db.is_cancel_text("Ali Valiyev") is False)
check("bo'sh matn o'tadi", db.is_cancel_text("") is False)
check("None xato bermaydi", db.is_cancel_text(None) is False)

check(
    "barcha menyu tugmalari qamrab olingan: " + str(len(db.MENU_BUTTON_TEXTS)),
    len(db.MENU_BUTTON_TEXTS) >= 40
)


# ==========================
# NATIJA
# ==========================

print()
for line in ok:
    print("  OK   " + line)

for line in bad:
    print("  XATO " + line)

print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
