# Deploy — serverdagi tartib

Bot va Mini App **bitta serverda birga** ishlaydi — ularni ajratib
bo'lmaydi, chunki ikkalasi ham bir xil `school.db` bazasi bilan
ishlaydi.

## Hozirgi holat

| | |
|---|---|
| Maktab | 19-BMSM (bitta) |
| Papka | `/opt/school_bot` — git repozitoriy, maktabning o'zi shu yerda |
| Servislar | `school-bot`, `school-webapp` |
| Domen | **app.cybermate.uz** → `127.0.0.1:5000` |
| Sozlamalar | `/opt/school_bot/.env` (git'da yo'q) |

Kengayganda joylashuv o'zgaradi: `/opt/school_bot` faqat **kod
shabloni** bo'lib qoladi, maktablar `/opt/schools/<slug>/` ichiga
o'tadi. Tartibi va ko'chish cheklisti — **`KOP_MAKTAB.md`**.

## Qaysi fayl nima uchun

| Fayl | Nima haqida |
|---|---|
| `README.md` (shu fayl) | Bugungi holat va kundalik ish |
| `GIT_DEPLOY.md` | Serverni git'dan yangilashga o'tkazish + orqaga qaytarish yo'llari |
| `KOP_MAKTAB.md` | Ko'p maktab rejimi: wildcard DNS/SSL, shablon servislar, yangi maktab qo'shish |
| `update.sh` | **Yangilashning yagona yo'li** — ikkala joylashuvni ham biladi |
| `setup_vps.sh` | Bo'sh serverda bir martalik o'rnatish (bitta maktab) |
| `new_school.sh` | Ko'p maktab rejimida yangi maktab qo'shish |

---

## Kundalik ish: yangilash

```bash
ssh root@SERVER
cd /opt/school_bot
sudo bash deploy/update.sh --check
sudo bash deploy/update.sh
```

`--check` hech narsani o'zgartirmaydi: qanday commitlar kelishini
ko'rsatadi va barcha tekshiruvlarni bajaradi.

Skript o'zi: zaxira oladi → kodni yangilaydi → kutubxonalar
o'zgargan bo'lsa o'rnatadi → servislarni ko'taradi →
**ko'tarilmasa eski kodga qaytaradi** va jurnalni ko'rsatadi.

Sxema migratsiyalari bot startida o'zi qo'llanadi
(`db/migrations.py`) — qo'lda SQL yozilmaydi.

⚠️ **Lokal botni to'xtatib qo'ying.** Telegram bitta tokenga bitta
ulanishga ruxsat beradi — Windows'da bot ishlab tursa serverdagi
`409 Conflict` beradi.

### Birinchi yangilashda bir martalik diqqat: `config.py`

`config.py` ilgari `.gitignore` da edi (token o'sha faylda turgan
davrdan qolgan) — ya'ni serverdagi nusxa git bilan **yangilanmagan**,
u qachonlardir qo'lda ko'chirilgan fayl. Endi u repozitoriyda, shuning
uchun keyingi `update.sh` serverdagi nusxani **repodagi versiya bilan
almashtiradi**.

Almashtirishdan oldin serverdagi `.env` to'liq bo'lishi kerak — aks
holda bot startda "`.env` faylida BOT_TOKEN ko'rsatilmagan" deb
to'xtaydi. Tekshirish (bir marta, yangilashdan oldin):

```bash
cp /opt/school_bot/config.py /root/config.py.eski      # ehtiyot nusxa
grep -E '^(BOT_TOKEN|ADMIN_IDS|WEBAPP_URL|WEBAPP_PORT|DB_PATH)=' /opt/school_bot/.env
```

Beshtasi ham qiymat bilan chiqishi kerak. `update.sh` ning preflight
tekshiruvi `BOT_TOKEN` va `ADMIN_IDS` ni o'zi ham tekshiradi.

---

## PORT qoidasi

`.env` dagi `WEBAPP_PORT` va nginx dagi `proxy_pass` **bir xil
port** bo'lishi shart. Ilgari port ikki joyda alohida yozilgan edi
(`.env` da 8000, nginx va servisda 5000) — bu yashirin tuzoq edi:
gunicorn bir portda tinglab, nginx boshqasiga uzatsa Mini App 502
beradi va tashqaridan "ilova ochilmayapti" ko'rinadi.

Endi **yagona manba — `.env`**: `school-webapp.service` portni
shundan oladi. `update.sh` har yangilanishda mosligini tekshiradi
va mos kelmasa hech narsaga tegmasdan to'xtaydi.

Portni o'zgartirish kerak bo'lsa — ikki joyni **birga**:

```bash
sed -i 's/^WEBAPP_PORT=.*/WEBAPP_PORT=5000/' /opt/school_bot/.env
# va /etc/nginx/sites-enabled/app.cybermate.uz ichidagi proxy_pass
nginx -t && systemctl reload nginx
systemctl restart school-webapp
```

---

## Bo'sh serverda birinchi o'rnatish

```bash
ssh root@SERVER_IP
git clone https://github.com/Dream-7070/musiqamaktabibot.git /opt/school_bot
cd /opt/school_bot

cp .env.example .env
nano .env          # BOT_TOKEN, ADMIN_IDS, WEBAPP_URL, WEBAPP_PORT

sudo bash deploy/setup_vps.sh
```

`setup_vps.sh`: paketlar, `botuser`, venv, `chmod 600` maxfiy
fayllarga, systemd birliklari, nginx, Let's Encrypt sertifikati.
`.env` bo'lmasa darhol to'xtaydi — servislar unga tayanadi.

Keyin Google Drive ulanishi (qo'lda, brauzer orqali):

```bash
python scripts/get_token.py            # kompyuterda, maktab akkaunti bilan
scp credentials.json token.json root@SERVER:/opt/school_bot/
chown botuser:botuser /opt/school_bot/{credentials,token}.json
chmod 600 /opt/school_bot/{credentials,token}.json
systemctl restart school-bot
```

⚠️ Cloud Console → OAuth consent screen → **PUBLISH APP**. Ilova
"Testing" holatida qolsa token **7 kunda** o'ladi va hujjatlar
yuklanmay qoladi (19-BMSM da 2026-09-10 da shu bo'lgan).

**Service account ishlatmang** — shaxsiy Gmail bilan ishlamaydi
(`services/gdrive.py` → `use_service_account()` izohiga qarang).
Faqat Google Workspace + Shared Drive holida to'g'ri ishlaydi.

Mini App menyu tugmasini bot **o'zi** qo'yadi (`main.py`,
`set_chat_menu_button`) — BotFather'ga kirish kerak emas.

---

## Tekshirish

```bash
systemctl status school-bot school-webapp
curl -I https://app.cybermate.uz
journalctl -u school-bot -f
journalctl -u school-webapp -f
```

Sxema versiyasi:

```bash
cd /opt/school_bot && sudo -u botuser venv/bin/python -c "from db.migrations import current_version; print(current_version())"
```

---

## Eslatmalar

- **Zaxira**: bot har 6 soatda bazani Google Drive'dagi
  `Maktab arxivi/Zaxira/` papkasiga yuklaydi (oxirgi 30 nusxa).
  Bundan tashqari `update.sh` har yangilanishda
  `/var/backups/school_bot/` ga nusxa oladi (oxirgi 20 ta).
- **Maxfiy fayllar git'da yo'q**: `.env`, `*.db`, `token.json`,
  `credentials.json`, `service_account.json`. `git reset --hard`
  ularga tegmaydi.
- **SSL**: certbot systemd timer bilan o'zi yangilaydi.
- **Orqaga qaytarish va baza tiklash** — `GIT_DEPLOY.md`.
