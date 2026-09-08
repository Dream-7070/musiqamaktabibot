# 19-BMSM — maktab boti

Bolalar musiqa va san'at maktabi uchun Telegram bot + Telegram Mini App.
Ikkalasi **bitta `school.db`** bazasi bilan ishlaydi, shuning uchun bitta
serverda birga ishga tushiriladi.

Interfeys tili — **o'zbekcha**. Kod izohlari, commit xabarlari va
foydalanuvchiga ko'rinadigan barcha matn o'zbek tilida yoziladi.

## Stack

- **Bot:** `pyTelegramBotAPI` (`telebot`) — aiogram EMAS, `sync` uslub
- **Mini App:** Flask + gunicorn (`webapp/server.py`), statik fayllar `webapp/static/`
- **Baza:** SQLite (`database.py`), serverda WAL rejimida
- **Fayllar:** Google Drive (`services/gdrive.py`), lokal `uploads/` ishlatilmaydi

## Tuzilma

| Yo'l | Vazifasi |
|---|---|
| `main.py` | Kirish nuqtasi, menyu, handlerlarni ro'yxatga olish |
| `database.py` | **Fasad** (128 satr) — `db/` paketidagi hamma narsani qayta eksport qiladi. Import qilish nuqtasi shu bo'lib qoladi: `from database import X` |
| `db/` | Baza qatlami, 11 ta modul: `core` (ulanish/jadval/migratsiya/sozlama), `teachers`, `students`, `documents`, `parents`, `payments`, `staff`, `subjects`, `schedule`, `audit`, `miniapp` |
| `handlers/` | Telegram oqimlari: `admin*`, `students`, `parents`, `teacher_schedule`, `*_documents` |
| `services/` | `gdrive`, `backup`, `reminders`, `daily_reminders`, `reports`, `students_export` |
| `data/curriculum.py` | O'quv reja: fan → bo'lim/sinf → soat. Jadval tuzishda shu manba |
| `data/teachers.py` | Boshlang'ich o'qituvchilar ro'yxati (seed) |
| `data/rooms.py` | Xonalarning boshlang'ich ro'yxati (urug'); keyin baza yuritadi |
| `webapp/` | Mini App backend (`server.py`) va `auth.py` (Telegram initData tekshiruvi) |
| `scripts/` | Bir martalik yordamchi skriptlar (curriculum yig'ish, Drive'ga ko'chirish) |
| `tests/` | Sinovlar — pastga qarang |

## Rollar

- **Admin** — `config.ADMIN_IDS`, to'liq huquq
- **Xodim** (`STAFF_ROLES`) — `direktor`, `buxgalter`, `yordamchi`; adminni tayinlaydi
- **O'qituvchi** — huquqlari alohida beriladi (`PERMISSION_LABELS`):
  `can_add_students`, `can_manage_schedule`, `can_be_concertmaster`.
  Huquq belgilanmagan bo'lsa — hammasi ochiq (eski yozuvlar buzilmasligi uchun)
- **Ota-ona** — bolasiga guvohnoma raqami orqali bog'lanadi

## Muhim qoidalar

- **O'quvchi ITV (tug'ilganlik guvohnomasi) raqami bilan aniqlanadi**, ism bilan emas.
  Bir bola bir nechta mutaxassislikda o'qishi mumkin — har biri alohida yozuv,
  alohida badal, lekin **jadval to'qnashuvi ITV bo'yicha tekshiriladi**.
- Dars jadvali `data/curriculum.py` dagi soatlarga bog'langan; reja to'lmaguncha
  bot qolgan bo'laklarni joylashtirishni taklif qiladi.
- **Xona qo'lda yozilmaydi** — `rooms` jadvalidagi ro'yxatdan tanlanadi.
  Bandligi `get_room_availability(day, time, duration)` orqali hisoblanadi va
  band xona kim tomonidan band qilinganini ko'rsatadi. Admin yangi xona
  qo'shadi (botda «🚪 Xonalar», Mini App'da «Xonalar» bo'limi).
  `data/rooms.py` faqat **urug'** — baza bo'sh bo'lgandagina ishlatiladi.
- **Fan turi (yakka/guruh)** avval `subjects` jadvalidan, topilmasa
  `data/curriculum.py`dagi `SUBJECT_TYPES` (2026-reja, faqat 10 ta musiqa
  mutaxassisligida bor), aks holda standart "yakka" (`get_subject_type`).
  Reja jim turgan hollar uchun (masalan amaliy san'at) admin
  `admin_set_subject_type(teacher, name, lesson_type)` orqali bitta
  o'qituvchi uchun alohida belgilaydi — umumiy fanga tegmaydi.
- **Guruh hajmi**: meʼyordan ortiq bo'lsa TO'SILMAYDI, adminga real vaqtda
  xabar boradi (`services/group_capacity.py`). Meʼyordan kam bo'lsa —
  kunlik eslatma (`services/daily_reminders.py`, `get_understaffed_groups`).
  Meʼyorlar `data/curriculum.py` dagi `GROUP_SIZE_NORMS`.
- **Admin istalgan o'qituvchiga istalgan vaqtga dars qo'ya oladi**
  (`handlers/admin_schedule.py`, «➕ Yangi dars qo'shish») — o'qituvchining
  tayyor jadval katakchalari bilan cheklanmaydi (masalan 07:15).
- **Dars o'chirishda ogohlantirish**: o'quvchisi bor vaqtni o'chirish
  ikki bosqichli (bot: `tsch:delslotask:`, Mini App: `tg.showConfirm`) —
  cascade o'chirish (`delete_slot`) qaytarib bo'lmaydi.
- **Kun/vaqt/xonani tahrirlash** (`update_slot_schedule`, bot:
  «✏️ Kun/vaqt/xonani tahrirlash») — o'quvchi va jo'rnavozlarni
  yo'qotmasdan joyini o'zgartiradi. Ilgari buning yagona yo'li darsni
  butunlay o'chirib qayta yaratish edi (Durdona voqeasining sababi).
- **«🔁 Oxirgisidek» tezkor tugma** (`get_teacher_last_pick`) — fan va
  sinfni oxirgi qo'shilgan darsdan olib, to'g'ridan-to'g'ri kunga
  o'tkazadi. Bir xil fan/sinfni haftada bir necha marta qo'yadigan
  o'qituvchilar uchun 5-6 bosqichni 3 taga tushiradi.
- **Mini App'da kutilmagan xato har doim JSON** (`@app.errorhandler`,
  `webapp/server.py`) — aks holda Flask HTML 500 qaytaradi, frontend
  esa JSON kutgani uchun oq ekran bo'lib qotib qolardi.
- **`services/reminders.py`** (qarzdorlik eslatmasi, oyning 5/15/25-
  kunlari) endi `daily_reminders.py` kabi oxirgi yuborilgan sanani
  bazada saqlaydi — ilgari xotirada saqlangani uchun bot bir kunda
  bir necha marta qayta ishga tushsa, eslatma qayta-qayta (spam)
  yuborilib ketishi mumkin edi.
- **`database.is_cancel_text(text)`** — matnli kiritish o'rniga menyu
  tugmasi yoki `/cancel` yuborilganini aniqlaydi (`MENU_BUTTON_TEXTS`
  ro'yxatiga qarshi). `handlers/students.py`dagi ism/sana/guvohnoma/
  tahrirlash bosqichlarida ishlatiladi — aks holda menyu tugmasi
  matni ma'lumot sifatida bazaga yozilib qolardi. **Barcha 30 ta
  next-step funksiyasida qo'llangan** (9 ta fayl). Yangi next-step
  funksiya qo'shsangiz, guard ham qo'shing —
  `tests/test_cancel_coverage.py` buni avtomatik tekshiradi va
  unutilsa sinov yiqiladi.
- Sirlar git'da yo'q: `config.py`, `token.json`, `credentials.json`, `*.db`.
  Shablon — `config.example.py`.

## Baza qatlami: fasad naqshi

`database.py` faqat **fasad** — kod `db/` paketida. Muhim qoidalar:

- **Import qilish har doim `database` dan**: `from database import get_students`.
  To'g'ridan-to'g'ri `from db.students import ...` yozmang — modullar
  bir-birini import qilmaydi (halqali bog'liqlik bor edi), ular faqat
  fasad ularni bog'lagandan keyin ishlaydi.
- **Modullar bir-birini import QILMAYDI.** Fasad hamma modulni yuklab
  bo'lgach, yetishmayotgan nomlarni har birining `globals()` iga o'zi
  joylashtiradi. Shuning uchun modul ichida begona funksiyani import
  qilmasdan chaqiraverish mumkin — lekin faqat funksiya ICHIDA
  (import paytida emas).
- **`DB_NAME`**: haqiqiy qiymat `db/core.py` da. `database.DB_NAME = ...`
  deb yozilganda fasad uni `core` va barcha modullarga uzatadi
  (sinovlar shunga tayanadi).
- Ajratish `scripts/split_database.py` bilan bir marta bajarilgan —
  qanday bo'lingani o'sha skriptda ko'rinadi.
- `tests/test_db_facade.py` fasad butunligini tekshiradi: har bir modul
  alohida yuklanishi, hamma nom eksport qilinishi, `DB_NAME` uzatilishi.

## Sinovlar

```bash
python tests/run_all.py
```

544 ta tekshiruv, 18 ta faylda. Har biri `tests/_tmp/` ichida **o'z bazasini**
yaratadi — haqiqiy `school.db` ga tegmaydi.

`concurrent_test.py` alohida, argument bilan ishlaydi (parallel yozuv sinovi):

```bash
python tests/concurrent_test.py A
```

⚠️ Windows konsoli `cp1251` — sinovlarni **alohida** ishga tushirganda emoji
xatosi chiqadi. `run_all.py` buni o'zi hal qiladi; qo'lda ishlatganda:
`PYTHONIOENCODING=utf-8 python tests/test_flow.py`

## Deploy

Domen: **app.cybermate.uz**. To'liq tartib — `deploy/README.md`.

Muhim: serverga chiqarishdan oldin **lokal botni to'xtating** — Telegram bitta
tokenga bitta ulanishga ruxsat beradi (aks holda `409 Conflict`).

Xizmatlar: `school-bot.service`, `school-webapp.service`; nginx + SSL proxy.
