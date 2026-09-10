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
| `db/broadcasts.py` | Bir nechta adminga yuborilgan xabarnoma nusxalari |
| `db/view_as.py` | Admin "ko'rish rejimi" — qaysi o'qituvchi sifatida ko'rilayotgani |
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
- **Jo'rnavozlik bo'limga bog'liq**: `NO_CONCERTMASTER_DEPARTMENTS`
  (`data/curriculum.py`) - tasviriy va amaliy san'at, teatr.
  Bu ro'yxat "bu darsga jo'rnavoz kerak emas" degani emas -
  "bu bo'lim o'qituvchisi jo'rnavoz bo'la olmaydi" degani
  (jo'rnavoz - musiqachi). Reja bo'yicha teatr darslariga ham
  jo'rnavoz soati ajratiladi, lekin uni musiqachi bajaradi. Bu yerdagi o'qituvchida jo'rnavozlik bo'limi botda
  ham, Mini App'da ham ko'rinmaydi va admin panelida huquq
  tugmasi chiqmaydi. Qoida `get_teacher_permissions` ichida
  qo'llanadi - ya'ni `can()` ham, `/api/teacher/me` ham bir xil
  javob beradi; bazada huquq yoqilgan bo'lsa ham bo'lim ustun
  turadi (bu yakka huquq emas, rejaning qoidasi).
- **Qaysi darsga jo'rnavoz qo'yiladi - fan bo'yicha**
  (`subject_has_concertmaster(department, subject)`). Reja
  jo'rnavoz soatini har bir fanga emas, sanalganlariga
  ajratadi: mutaxassislik (tasviriy/amaliy/dizayn va
  fortepianodan tashqari - fortepianoda uning o'rniga
  akkompanement bor, 4.4-band), akkompanement, jamoa
  ijrochiligi/xor, ovozni yo'lga qo'yish, raqs va ritmika
  fanlari, sahna harakati, vokal hamda **tanlangan fan**
  (7.4-band - u barcha yo'nalishlarda bor, hatto tasviriy
  san'atda ham). Tekshiruv `add_concertmaster` ichida turadi,
  ro'yxatlar esa (bot va Mini App) mos kelmaydigan darslarni
  umuman ko'rsatmaydi.
- **Pul har doim to'liq son**: Mini App'da `moneyBig()` -
  "815 200", "717 ming" emas. Yaxlitlash qarzning aniq
  summasini yashirardi.
- **Guruh hajmi**: meʼyordan ortiq bo'lsa TO'SILMAYDI, adminga real vaqtda
  xabar boradi (`services/group_capacity.py`). Meʼyordan kam bo'lsa —
  kunlik eslatma (`services/daily_reminders.py`, `get_understaffed_groups`).
  Meʼyorlar `data/curriculum.py` dagi `GROUP_SIZE_NORMS`.
- **Admin istalgan o'qituvchiga istalgan vaqtga dars qo'ya oladi**
  (`handlers/admin_schedule.py`, «➕ Yangi dars qo'shish») — o'qituvchining
  tayyor jadval katakchalari bilan cheklanmaydi (masalan 07:15).
- **`delete_slot` uchta jadvalni tozalaydi**: `schedule_slots`,
  `schedule_slot_students` va `slot_concertmasters`. Oxirgisi
  ilgari unutilgan edi (yetim yozuvlar). Eski bazani tozalash:
  `python scripts/cleanup_orphans.py --apply`.
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
- **Admin o'qituvchi sifatida ko'ra oladi** («👁 Ko'rish rejimi»):
  botda «👨‍🏫 O'qituvchi rejimi» → bo'lim → o'qituvchi,
  Mini App'da «Jadvallar» → o'qituvchi → «Shu o'qituvchi sifatida ko'rish».
  Tanlov **bazada** saqlanadi (`admin_view_as`, `db/view_as.py`) — bot va
  Mini App alohida jarayon, umumiy xotira yo'q; shuning uchun botda
  tanlangan o'qituvchi Mini App'da ham ochiladi va bot qayta ishga
  tushganda rejim yo'qolmaydi. Rejimda `/api/whoami` `role="teacher"`
  qaytaradi (`viewing_as` bilan), `_require_teacher()` esa o'sha
  o'qituvchini beradi — ya'ni panel, huquqlar va jadval xuddi
  o'qituvchinikidek. Chiqish: botda «🚪 Ko'rish rejimidan chiqish»,
  Mini App'da tepadagi lentadagi «Chiqish». Yoqish/o'chirish
  `log_action` ga yoziladi.
- **Ko'rish rejimining manbai - baza, xotira emas.** Botdagi
  `selected_teachers` - oddiy lug'at emas, `state.SelectedTeachers`:
  admin uchun har murojaatda `get_view_as` dan tekshiradi. Sababi -
  rejim Mini App'da o'chirilgan bo'lishi mumkin (boshqa jarayon),
  aks holda bot menyusi o'sha o'qituvchida qolib ketardi. Mini App
  o'z tomonidan rejimni o'zgartirsa, botga xabar yuboradi
  (`_tell_bot`) va pastki menyuni tozalaydi.
- **«📅 Bugungi darslarim»** (`handlers/teacher_schedule.py`) -
  kunlik eng kerakli ma'lumot bitta bosishda: vaqt, fan, xona,
  o'quvchilar, hamda hozir/keyin belgilari. Jo'rnavozlik darslari
  ham qo'shiladi (dars egasi ko'rsatiladi).
- **Ikkinchi mutaxassislikda SINF alohida.** Bola boshqa
  o'qituvchida topilganda undan faqat **ism va tug'ilgan sana**
  ko'chiriladi - ular bolaga tegishli. **Sinf ko'chirilmaydi**:
  u mutaxassislikka bog'liq, bola fortepianoda 3-sinf bo'lsa ham
  doirani endi boshlayotgan bo'lishi mumkin (1-sinf). Badal ham
  shunday. Ikkalasini yangi o'qituvchining o'zi tanlaydi -
  botda ham (`samechild:yes` -> sinf so'raladi), Mini App'da ham
  (`same_child=true` da faqat `birth_date` ko'chiriladi).
- **Mini App jadvali kun bo'yicha** (`renderTeacherSlots`):
  tepada 6 ta kun tugmasi (dars bor kunda nuqta), pastda faqat
  tanlangan kunning darslari. Ochilganda bugungi kun, yakshanba
  bo'lsa dushanba. Ilgari butun hafta bitta uzun ro'yxatda edi -
  19 ta karta. Jo'rnavozlik darslari ham shu ro'yxatga
  qo'shiladi (uzuq chiziqli karta), chunki o'qituvchi o'sha kuni
  qayerda bo'lishini bitta joydan ko'rishi kerak.
- **Mini App'da o'quvchi qo'shish** (`/api/teacher/students`, POST) -
  botdagi 5 qadam o'rniga bitta forma. Qoidalar bir xil: guvohnoma
  takrorlanmaydi, boshqa o'qituvchida topilsa `needs_confirm`
  qaytadi va tasdiqlangach bolaning sana/sinfi **qayta yozilmaydi**,
  faqat yangi badal belgilanadi.
- **Tugmali xabarnoma bir nechta odamga boradi** (o'qituvchi
  akkaunt so'rovi - barcha adminlarga, kvitansiya - barcha
  buxgalterlarga). Ular `_broadcast_to_admins` /
  `remember_broadcast` orqali yuboriladi: har bir nusxaning
  `(chat_id, message_id)` si `broadcast_messages` jadvaliga
  yoziladi. Kimdir javob bergach `_close_broadcast` HAMMA
  nusxani natija matniga almashtiradi va kim javob berganini
  yozadi. Ilgari faqat bosgan odamning xabari yangilanardi -
  qolganlarida tugmalar turib qolib, bosilganda «eskirgan»
  xatosi chiqardi. **Yangi tugmali xabarnoma qo'shsangiz, uni
  ham shu ikki funksiya orqali yuboring** -
  `tests/test_broadcast.py` buni tekshiradi.
- **Yakshanba dam olish kuni**: `DAYS_OF_WEEK` da 6 kun bor
  (Dushanba-Shanba), `datetime.weekday()` esa yakshanbada 6
  qaytaradi. `weekday() >= len(DAYS_OF_WEEK)` ni tekshirmasdan
  indekslash `IndexError` beradi - `api_admin_live` da aynan shu
  bo'lib, har yakshanba «Hozir» bo'limi ishlamay qolardi.
- **Vaqt zonasi**: server UTC'da ishlaydi, shuning uchun ikkala
  systemd birligida `Environment=TZ=Asia/Tashkent` turadi -
  `SEND_HOUR=10` haqiqatan Toshkent bilan 10:00 bo'lsin. SQLite'da
  esa `datetime('now')` TZ dan qat'i nazar **har doim UTC**,
  shuning uchun SQL'da doim `datetime('now','localtime')` yoziladi.
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
