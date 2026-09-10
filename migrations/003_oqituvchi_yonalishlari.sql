-- ==========================
-- 003 - o'qituvchi yo'nalishlari
-- ==========================
--
-- Bo'limda bir nechta yo'nalish bo'lishi mumkin. "Amaliy san'at"da
-- 13 ta bor, shuning uchun o'sha bo'lim o'qituvchisiga dars
-- qo'shayotganda 34 ta fan chiqardi - ko'pchiligi boshqa kasbniki.
-- Aynan shundan noto'g'ri fan tanlangan.
--
-- Endi har o'qituvchiga o'zi o'qitadigan yo'nalish(lar) belgilanadi
-- va fan ro'yxati o'shalar bilan cheklanadi.
--
-- Bir o'qituvchi BIR NECHTA yo'nalishda bo'lishi mumkin (masalan
-- bitta usta ham naqqoshlik, ham kashtachilik o'qitadi) - shuning
-- uchun alohida jadval, `teachers` ga ustun emas.
--
-- Yo'nalish belgilanmagan bo'lsa - eski xatti-harakat saqlanadi
-- (butun bo'limning fanlari), ya'ni hech kim bloklanmaydi.

CREATE TABLE IF NOT EXISTS teacher_specialties(
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher   TEXT,
    specialty TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_teacher_specialty
ON teacher_specialties(teacher, specialty);
