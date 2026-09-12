-- ==========================
-- 008 - mavjud xodimlarni tabeldan ko'chirish
-- ==========================
--
-- Xodimlar ro'yxati maktabning haqiqiy tabel faylidan olindi
-- (Iyul 2026 varag'i - eng oxirgisi): ism, lavozim, tabel raqami
-- va stavka miqdori.
--
-- Mudir endi ularni qo'lda kiritmaydi, faqat hujjatlarini yuklab
-- chiqadi.
--
-- DIQQAT: tabel raqami NOYOB EMAS - faylda 6-raqam ikki xodimda
-- uchraydi (Karimova D.E va Ismatullaev S.A). Shuning uchun
-- takrorlanishni ism+lavozim bo'yicha tekshiramiz.
--
-- Idempotent: qayta yugurtirilsa hech narsa ikkilanmaydi.

-- Lavozimlar - 005 da faqat texnik lavozimlar bor edi, tabelda
-- esa ma'muriy lavozimlar ham qatnashadi.

INSERT OR IGNORE INTO tech_positions (name) VALUES
    ('Bosh xisobchi'),
    ('Direktor'),
    ('Duradgor'),
    ('Elektrik'),
    ('Farrosh'),
    ('Ish yurituvchi'),
    ('Kutibxonachi'),
    ('Liboschi'),
    ('Ovoz operatori'),
    ('O‘MIBDO‘'),
    ('Qorovul'),
    ('Santexnik'),
    ('XIBDO‘'),
    ('Xovlibon');


-- Xodimlar

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Raxmatullaev O‘.G‘', 'Direktor', '15', 5178562
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Raxmatullaev O‘.G‘' AND position='Direktor'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Abduraximov A.A', 'O‘MIBDO‘', '68', 4847213
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Abduraximov A.A' AND position='O‘MIBDO‘'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Surobov F.F', 'XIBDO‘', '5', 2768238
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Surobov F.F' AND position='XIBDO‘'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Mamatova A.N', 'Bosh xisobchi', '12', 2230605
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Mamatova A.N' AND position='Bosh xisobchi'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Ergasheva A.A', 'Ish yurituvchi', '157', 1612899
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Ergasheva A.A' AND position='Ish yurituvchi'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Nabieva D.M', 'Kutibxonachi', '129', 2038684
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Nabieva D.M' AND position='Kutibxonachi'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Normatova Z.R', 'Liboschi', '52', 1338363
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Normatova Z.R' AND position='Liboschi'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Xolto‘raev G‘.U', 'Ovoz operatori', '2', 1405726
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Xolto‘raev G‘.U' AND position='Ovoz operatori'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Musaqulov A.I', 'Santexnik', '8', 702863
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Musaqulov A.I' AND position='Santexnik'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Qosimova D.A', 'Xovlibon', '64', 635500
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Qosimova D.A' AND position='Xovlibon'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Ibragimov M.A', 'Duradgor', '139', 702863
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Ibragimov M.A' AND position='Duradgor'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Raxmonov Z.A', 'Elektrik', '131', 669182
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Raxmonov Z.A' AND position='Elektrik'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Karimova D.E', 'Farrosh', '6', 1067640
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Karimova D.E' AND position='Farrosh'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Mirsaidova M.R', 'Farrosh', '39', 1054930
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Mirsaidova M.R' AND position='Farrosh'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Yo‘ldosheva X.U', 'Farrosh', '138', 1054930
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Yo‘ldosheva X.U' AND position='Farrosh'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Abduramonov K.E', 'Qorovul', '55', 1271000
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Abduramonov K.E' AND position='Qorovul'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Sancharov A.M', 'Qorovul', '10', 1271000
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Sancharov A.M' AND position='Qorovul'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Ismatullaev S.A', 'Qorovul', '6', 1271000
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Ismatullaev S.A' AND position='Qorovul'
);

INSERT INTO tech_staff (full_name, position, tabel_raqami, stavka)
SELECT 'Qosimov M.O‘', 'Qorovul', '4', 1271000
WHERE NOT EXISTS (
    SELECT 1 FROM tech_staff WHERE full_name='Qosimov M.O‘' AND position='Qorovul'
);
