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
| `database.py` | Butun baza qatlami (~4700 satr) — jadvallar, migratsiya, biznes-mantiq |
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
- Sirlar git'da yo'q: `config.py`, `token.json`, `credentials.json`, `*.db`.
  Shablon — `config.example.py`.

## Sinovlar

```bash
python tests/run_all.py
```

342 ta tekshiruv, 11 ta faylda. Har biri `tests/_tmp/` ichida **o'z bazasini**
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
