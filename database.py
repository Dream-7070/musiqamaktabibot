# -*- coding: utf-8 -*-
# ==========================
# database.py - FASAD
# ==========================
#
# Ilgari bu fayl 5100+ satr edi va butun baza qatlami shu yerda
# turardi. Endi kod `db/` paketidagi 11 ta modulga ajratilgan:
#
#   db/core.py       - ulanish, jadvallar, migratsiya, sozlamalar
#   db/teachers.py   - o'qituvchilar, akkaunt so'rovi, huquqlar
#   db/students.py   - o'quvchilar, badal, arxiv, sinflar
#   db/documents.py  - Google Drive hujjatlari (o'qituvchi + o'quvchi)
#   db/parents.py    - ota-onalar va farzandga bog'lanish
#   db/payments.py   - to'lovlar va kvitansiyalar
#   db/staff.py      - xodimlar (buxgalter, direktor, yordamchi)
#   db/subjects.py   - fanlar va ularning turi (yakka/guruh)
#   db/schedule.py   - dars jadvali, to'qnashuvlar, xonalar, vaqtlar
#   db/audit.py      - o'zgarishlar tarixi
#   db/miniapp.py    - Mini App uchun qo'shimcha so'rovlar
#   db/view_as.py    - admin "ko'rish rejimi" (o'qituvchi sifatida)
#   db/broadcasts.py - bir nechta adminga yuborilgan xabar nusxalari
#
# BU FAYL O'ZGARMAS KIRISH NUQTASI bo'lib qoladi: loyihadagi
# barcha `from database import X` qatorlari ilgarigidek ishlaydi.
# Yangi kod yozganda ham shu fayldan import qilaverish mumkin.
#
# ==========================


import sys
import types

from db import (
    core,
    teachers,
    students,
    documents,
    parents,
    payments,
    staff,
    subjects,
    schedule,
    audit,
    miniapp,
    view_as,
    broadcasts,
)


_MODULES = [
    core, teachers, students, documents, parents,
    payments, staff, subjects, schedule, audit, miniapp,
    view_as, broadcasts,
]


# ==========================
# MODULLARNI O'ZARO BOG'LASH
# ==========================
#
# Bo'limlar orasida halqali bog'liqliklar bor edi (masalan
# students <-> parents <-> documents). Agar modullar bir-birini
# to'g'ridan-to'g'ri import qilsa - "circular import" xatosi
# chiqadi.
#
# Shuning uchun modullar bir-birini IMPORT QILMAYDI. Ular
# yuklangandan keyin, shu yerda, har bir modulning globals()
# iga yetishmayotgan nomlar joylashtiriladi.
#
# Bu xavfsiz: hech bir modul import paytida begona nomni
# ishlatmaydi - faqat funksiya ichida, ya'ni chaqirilganda.
# O'sha payt globals() allaqachon to'ldirilgan bo'ladi.


def _public_names(module):

    return {
        name: getattr(module, name)
        for name in dir(module)
        if not name.startswith("__")
        and not isinstance(getattr(module, name), types.ModuleType)
    }


_EXPORTS = {}

for _mod in _MODULES:
    _EXPORTS.update(_public_names(_mod))


# har bir modulga o'zida yo'q nomlarni beramiz

for _mod in _MODULES:
    for _name, _value in _EXPORTS.items():
        if _name not in _mod.__dict__:
            setattr(_mod, _name, _value)


# fasadning o'ziga ham hammasini chiqaramiz

globals().update(_EXPORTS)


__all__ = sorted(_EXPORTS)


# ==========================
# DB_NAME MOSLASHUVI
# ==========================
#
# Sinovlar va skriptlar `database.DB_NAME = "..."` deb bazani
# almashtiradi. Endi haqiqiy qiymat db/core.py da turadi,
# shuning uchun fasadga yozilgan qiymatni core ga uzatamiz -
# aks holda o'zgartirish e'tiborsiz qolardi va sinovlar
# haqiqiy school.db ga yozib yuborardi.


class _Facade(types.ModuleType):

    def __setattr__(self, name, value):

        if name == "DB_NAME":

            core.DB_NAME = value

            # modullar ham yangi qiymatni ko'rsin
            for mod in _MODULES:
                mod.__dict__["DB_NAME"] = value

        types.ModuleType.__setattr__(self, name, value)


sys.modules[__name__].__class__ = _Facade
