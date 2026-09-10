# Migratsiyalar

Bu papkada baza sxemasini o'zgartiradigan `.sql` fayllar turadi.
Bot ishga tushganda `db.migrations.run_migrations()` ularni
tartib bilan qo'llaydi va `schema_version` jadvaliga yozib qo'yadi.

Nega kerak: bot bir nechta maktabda ALOHIDA bazalar bilan ishlaydi.
Versiyalash bo'lmasa, 10 ta maktab 10 xil sxemada qolib ketadi va
har yangilanish qo'lda tuzatishga aylanadi.

## Nomlash qoidasi

    NNN_nom.sql

`NNN` - kamida 3 xonali versiya raqami, `nom` - lotin harflari,
raqam va pastki chiziq. Masalan:

    002_maktab_sozlamalari.sql
    003_oquvchiga_telefon_ustuni.sql

Qoidaga mos kelmagan fayllar (shu README ham) e'tiborsiz qoladi.

## 001 - baseline, fayl emas

Versiya 1 uchun fayl YO'Q. U kod orqali qo'llanadi:
`create_tables()` + `migrate_schema()` chaqiriladi, ya'ni loyihaning
o'sha paytdagi to'liq sxemasi quriladi. Bu ikkalasi idempotent,
shuning uchun bo'sh bazada ham, allaqachon ishlab turgan bazada
ham xavfsiz.

Yangi fayllaringizni **002** dan boshlang.

## Idempotent yozing - bu majburiy

SQLite'ning `executescript()` funksiyasi ochiq tranzaksiyani o'zi
commit qilib yuboradi. Ya'ni skript o'rtasida xato chiqsa, undan
oldingi buyruqlar bazada QOLIB KETADI - orqaga qaytarilmaydi.

Shuning uchun har bir fayl qayta yugurtirilganda xato bermasligi
kerak:

    CREATE TABLE IF NOT EXISTS ...
    CREATE INDEX IF NOT EXISTS ...
    INSERT OR IGNORE INTO ...

`ALTER TABLE ... ADD COLUMN` da IF NOT EXISTS yo'q. Ustun qo'shish
kerak bo'lsa - uni .sql ga emas, `db/documents.py` dagi
`_add_missing_columns` ro'yxatiga qo'shing, u allaqachon tekshirib
qo'shadi.

## Chiqarilgan migratsiyani TAHRIRLAMANG

Bir marta biror maktabga yetib borgan fayl o'zgarmaydi. Xato bo'lsa -
uni tuzatadigan YANGI fayl qo'shing. Aks holda maktablarning
sxemasi bir-biridan farq qila boshlaydi.

## Tekshirish

Joriy versiya:

    python -c "from db.migrations import current_version; print(current_version())"

Kutilayotganlar:

    python -c "from db.migrations import pending; print(pending())"
