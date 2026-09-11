# Serverni GitHub'dan yangilash

Ilgari kod `scp` bilan ko'chirilardi. Muammo: serverda qaysi
versiya turgani **hech qayerda yozilmasdi** va o'chirilgan fayl
serverda qolib ketaverardi.

Endi server GitHub'dan yangilanadi.

> **Holat:** 19-BMSM serveri allaqachon git repozitoriyga
> o'tkazilgan — pastdagi «BIR MARTALIK O'TKAZISH» bo'limi
> tarix uchun qoldirilgan (yangi serverda kerak bo'ladi).
> Kundalik yangilash va joylashuv haqida — `README.md`,
> kengayish haqida — `KOP_MAKTAB.md`.
>
> `update.sh` endi ko'p maktabli joylashuvni ham biladi: har
> maktabga alohida zaxira, rsync va servis restart. Shu sabab
> pastdagi «faqat `school-bot` va `school-webapp` qayta ishga
> tushadi» degan jumla bitta maktabli holat uchun to'g'ri.

**Avtomatik pull yo'q** — yangilanish faqat siz buyruq
berganingizda bo'ladi.

---

## Kundalik ishlatish

```bash
ssh root@189.74.98.21
cd /opt/school_bot
sudo bash deploy/update.sh
```

Avval nima o'zgarishini ko'rmoqchi bo'lsangiz:

```bash
sudo bash deploy/update.sh --check
```

`--check` hech narsani o'zgartirmaydi — faqat qo'shiladigan
commitlarni ro'yxat qilib ko'rsatadi.

---

## Skript nima qiladi

1. GitHub'dan yangi kod bor-yo'qligini tekshiradi
2. Qanday o'zgarishlar kelishini ko'rsatadi
3. `school.db` dan zaxira nusxa oladi (`/var/backups/school_bot/`)
4. Kodni yangilaydi
5. `requirements.txt` o'zgargan bo'lsa kutubxonalarni o'rnatadi
6. `school-bot` va `school-webapp` ni qayta ishga tushiradi
7. **Ko'tarilmasa — eski kodga qaytaradi** va jurnalni ko'rsatadi

---

## Maxfiy fayllar xavfsiz

Bular `.gitignore` da, ya'ni git ularni umuman ko'rmaydi:

```
.env            config.py       school.db
token.json      credentials.json    service_account.json
uploads/        venv/
```

`git reset --hard` faqat **kuzatilayotgan** fayllarni almashtiradi.
Baza, tokenlar va sozlamalar joyida qoladi.

Shunga qaramay skript har safar bazadan nusxa oladi.

---

## BIR MARTALIK O'TKAZISH

Serverdagi papka hozir git repozitoriysi emas — oddiy fayllar
to'plami. Uni bir marta repoga aylantirish kerak.

### 1. To'liq zaxira (eng muhim qadam)

```bash
ssh root@189.74.98.21
cd /opt
tar czf /root/school_bot_zaxira_$(date +%F).tar.gz school_bot
ls -lh /root/school_bot_zaxira_*.tar.gz
```

Butun papka arxivga olinadi. Biror narsa noto'g'ri ketsa,
shundan tiklanadi.

### 2. Maxfiy fayllar joyidami — tekshirish

```bash
cd /opt/school_bot
ls -la .env config.py school.db token.json credentials.json
```

Hammasi ko'rinishi kerak. Ko'rinmasa — TO'XTANG.

### 3. Repozitoriyga aylantirish

```bash
cd /opt/school_bot
git init
git remote add origin https://github.com/Dream-7070/musiqamaktabibot.git
git fetch origin main
```

Bu yerda hali hech narsa o'zgarmaydi — faqat kod yuklab olinadi.

### 4. Nima almashishini ko'rish

```bash
git diff --stat origin/main
```

Ro'yxatda `.env`, `school.db`, `config.py` **bo'lmasligi kerak**.
Agar ular chiqsa — TO'XTANG va ayting.

### 5. Kodni almashtirish

```bash
git reset --hard origin/main
chown -R botuser:botuser /opt/school_bot
```

### 6. Migratsiya va qayta ishga tushirish

```bash
systemctl restart school-bot school-webapp
sleep 6
systemctl is-active school-bot school-webapp
journalctl -u school-bot -n 30 --no-pager
```

Ikkalasi ham `active` bo'lishi kerak.

### 7. Tekshirish

Telegram'da botga `/start` yuboring. Ishlasa — tayyor.

Bundan keyin yangilanish faqat `sudo bash deploy/update.sh`.

---

## Biror narsa noto'g'ri ketsa

### Kodni orqaga qaytarish

```bash
cd /opt/school_bot
git log --oneline -10          # qaysi versiyaga qaytish
git reset --hard <commit>
chown -R botuser:botuser /opt/school_bot
systemctl restart school-bot school-webapp
```

### Bazani tiklash

```bash
systemctl stop school-bot school-webapp
ls -lt /var/backups/school_bot/
cp /var/backups/school_bot/school_YYYYMMDD_HHMMSS.db /opt/school_bot/school.db
chown botuser:botuser /opt/school_bot/school.db
systemctl start school-bot school-webapp
```

### Butun papkani tiklash

```bash
systemctl stop school-bot school-webapp
cd /opt
mv school_bot school_bot_buzuq
tar xzf /root/school_bot_zaxira_YYYY-MM-DD.tar.gz
systemctl start school-bot school-webapp
```

---

## Diqqat

**Migratsiyalarni orqaga qaytarib bo'lmaydi.** Kodni eski
versiyaga qaytarsangiz ham, baza yangi sxemada qolaveradi.
Odatda bu muammo tug'dirmaydi (migratsiyalar faqat qo'shadi),
lekin shuning uchun zaxira har safar olinadi.

**Lokal botni to'xtatib qo'ying.** Telegram bitta tokenga bitta
ulanishga ruxsat beradi — Windows'da bot ishlab tursa, serverdagi
`409 Conflict` beradi.
