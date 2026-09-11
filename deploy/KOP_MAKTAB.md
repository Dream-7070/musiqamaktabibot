# Ko'p maktab rejimi

Bot endi bitta kod bazasi bilan bir nechta maktabda ishlaydi.
Har maktabning **o'z boti, o'z bazasi, o'z Google Drive akkaunti**
bo'ladi — ma'lumotlar bir-biriga umuman aralashmaydi.

Bu fayl serverni shu rejimga bir marta tayyorlash tartibini
tushuntiradi. Kundalik ish esa bitta buyruqqa qisqaradi:

```bash
sudo /opt/school_bot/deploy/new_school.sh 5mmm "5-son bolalar musiqa maktabi" 123456:AA... 566206701
```

---

## Qanday joylashadi

```
/opt/school_bot/            umumiy kod (git checkout) — shablon
/opt/schools/19bmsm/        maktab: kod nusxasi + venv + .env + school.db
/opt/schools/5mmm/          maktab: ...
/etc/nginx/school-ports.map subdomen -> port jadvali
```

Har maktabga ikkita servis: `school-bot@<slug>` va `school-webapp@<slug>`.

---

## 1. Wildcard DNS (bir marta)

Domen provayderida bitta yozuv:

```
*.cybermate.uz    A    <SERVER_IP>
```

Shundan keyin **yangi maktabga DNS yozuvi kerak emas** — istalgan
subdomen o'zi ishlaydi.

## 2. Wildcard SSL sertifikat (bir marta)

Wildcard sertifikat HTTP-01 bilan **olinmaydi**, faqat DNS-01 bilan:

```bash
certbot certonly --manual --preferred-challenges dns \
        --cert-name cybermate.uz-wildcard \
        -d "*.cybermate.uz" -d cybermate.uz
```

certbot so'ragan TXT yozuvini DNS ga qo'shasiz, tasdiqlaydi.
Provayderingizda DNS API bo'lsa (`--dns-cloudflare` va h.k.),
yangilanish ham avtomatlashadi — aks holda 90 kunda bir marta
qo'lda takrorlanadi.

## 3. nginx

```bash
cp /opt/school_bot/deploy/nginx-wildcard.conf /etc/nginx/sites-available/schools
ln -s /etc/nginx/sites-available/schools /etc/nginx/sites-enabled/

# port jadvali — new_school.sh keyin o'zi to'ldiradi
touch /etc/nginx/school-ports.map

nginx -t && systemctl reload nginx
```

Mavjud `app.cybermate.uz` bloki **tegilmaydi**: nginx'da aniq nomli
server bloki wildcard'dan doim ustun turadi, shuning uchun 19-BMSM
eski manzilida uzilishsiz ishlayveradi.

## 4. systemd shablonlari

```bash
cp /opt/school_bot/deploy/school-bot@.service     /etc/systemd/system/
cp /opt/school_bot/deploy/school-webapp@.service  /etc/systemd/system/
systemctl daemon-reload
```

`@` belgisi — bu shablon. `school-bot@5mmm` deb chaqirilganda `%i`
o'rniga `5mmm` qo'yiladi.

## 5. Foydalanuvchi

```bash
id botuser || useradd -r -s /usr/sbin/nologin botuser
```

---

## Yangi maktab qo'shish

```bash
sudo /opt/school_bot/deploy/new_school.sh \
     <slug> "<Maktab to'liq nomi>" <BOT_TOKEN> <ADMIN_IDS>
```

Skript o'zi: port ajratadi, kodni ko'chiradi, venv quradi, `.env`
yozadi, nginx jadvaliga qo'shadi, servislarni ko'taradi va holatini
tekshiradi. Xatolik bo'lsa nginx o'zgarishini qaytaradi.

Keyin **qo'lda bitta** qadam qoladi: Google Drive ulanishi —
avtorizatsiya brauzerda tasdiqlanadi, buni skript qila olmaydi.

```bash
# maktab akkaunti bilan, kompyuterda
python scripts/get_token.py

# so'ng ikki faylni serverga
scp credentials.json token.json root@SERVER:/opt/schools/<slug>/
chown botuser:botuser /opt/schools/<slug>/{credentials,token}.json
chmod 600 /opt/schools/<slug>/{credentials,token}.json
systemctl restart school-bot@<slug>
```

⚠️ Cloud Console → OAuth consent screen → **PUBLISH APP**. Ilova
"Testing" holatida qolsa token **7 kunda** o'ladi (19-BMSM da
2026-09-10 da shu bo'lgan).

**Service account ishlatmang** — shaxsiy Gmail bilan ishlamaydi:
papka yaratadi, fayl yuklashda 403 "do not have storage quota"
qaytaradi. Faqat Google Workspace + Shared Drive holida to'g'ri
ishlaydi (`services/gdrive.py` → `use_service_account()`).

**Mini App menyu tugmasi qo'lda sozlanmaydi** — bot ishga tushganda
uni o'zi qo'yadi (`main.py`, `set_chat_menu_button`). BotFather'ga
kirish shart emas.

---

## Yangilanish tartibi

Yangilash **bitta buyruq** — `deploy/update.sh` joylashuvni o'zi
aniqlaydi (bitta maktabmi, `/opt/schools/*` mi), zaxira oladi,
rsync qiladi, servislarni ko'taradi va ko'tarilmasa **orqaga
qaytaradi**. Qo'lda rsync yozish kerak emas.

```bash
cd /opt/school_bot

sudo bash deploy/update.sh --check     # nima o'zgaradi + tekshiruvlar
sudo bash deploy/update.sh             # hammasini yangilaydi
```

Avval **pilot**da sinab ko'rish uchun (bir maktab):

```bash
sudo bash deploy/update.sh --only 19bmsm
# bir hafta kuzatiladi, keyin argumentsiz - qolganlarga
```

Skript yangilashdan **oldin** quyidagilarni tekshiradi va biror
narsa noto'g'ri bo'lsa hech narsaga tegmasdan to'xtaydi:
`.env` to'liqmi, `WEBAPP_PORT` **nginx bilan mos kelyaptimi**,
venv bormi, systemd birliklari o'rnatilganmi.

Sxema migratsiyalari bot ishga tushganda **o'zi** qo'llanadi
(`db/migrations.py`) — qo'lda SQL yozilmaydi. Skript oxirida har
maktabning sxema versiyasini ko'rsatadi.

Qo'lda tekshirish:

```bash
cd /opt/schools/19bmsm && venv/bin/python -c "from db.migrations import current_version; print(current_version())"
```

---

## Birinchi maktabni shablon sxemasiga ko'chirish

Hozir 19-BMSM **eski joylashuvda**: `/opt/school_bot` ning o'zi
ishlayotgan maktab, servislari `school-bot` va `school-webapp`,
nginx `app.cybermate.uz` → `127.0.0.1:5000`.

Ikkinchi maktab qo'shilishidan **oldin** shu ko'chishni bajarish
kerak, aks holda bir serverda ikki xil tartib yashab qoladi
(`update.sh` bunda ogohlantirish beradi).

**Shart:** wildcard DNS va SSL (1-2 bo'lim), nginx va systemd
shablonlari (3-4 bo'lim) o'rnatilgan bo'lishi kerak.

**Eng nozik joy — PORT.** `.env` dagi `WEBAPP_PORT` va nginx
bir-biriga mos bo'lmasa Mini App 502 beradi. Shuning uchun
tartib aynan shunday: avval nginx jadvaliga yozamiz, keyin
`.env` ni o'zgartiramiz, eng oxirida servisni almashtiramiz.

```bash
# 0) Zaxira - eng muhim qadam
systemctl stop school-bot school-webapp
cd /opt && tar czf /root/19bmsm_kochish_$(date +%F).tar.gz school_bot

# 1) Maktab papkasini yasash (kod + maxfiy fayllar + baza)
mkdir -p /opt/schools/19bmsm
rsync -a --exclude venv --exclude .git /opt/school_bot/ /opt/schools/19bmsm/
python3 -m venv /opt/schools/19bmsm/venv
/opt/schools/19bmsm/venv/bin/pip install -q -r /opt/schools/19bmsm/requirements.txt
chown -R botuser:botuser /opt/schools/19bmsm

# 2) nginx: ikkala nom ham yangi portga (app.* ni ham qoldiramiz,
#    ota-onalardagi eski havolalar ishlab tursin)
printf '19bmsm.cybermate.uz 8000;\napp.cybermate.uz 8000;\n' >> /etc/nginx/school-ports.map

#    eski aniq nomli blok olib tashlanadi - aks holda u wildcard'dan
#    ustun turib, hamon 5000 ga uzatadi
rm -f /etc/nginx/sites-enabled/app.cybermate.uz
nginx -t && systemctl reload nginx

# 3) .env dagi portni moslash
sed -i 's/^WEBAPP_PORT=.*/WEBAPP_PORT=8000/' /opt/schools/19bmsm/.env

# 4) Servislarni almashtirish
systemctl disable --now school-bot school-webapp
systemctl enable --now school-bot@19bmsm school-webapp@19bmsm
sleep 5 && systemctl is-active school-bot@19bmsm school-webapp@19bmsm

# 5) Tekshirish: botga /start, Mini App ochilishi, hujjat yuklash
curl -I https://app.cybermate.uz
curl -I https://19bmsm.cybermate.uz

# 6) Shundan keyin /opt/school_bot faqat SHABLON bo'lib qoladi -
#    undagi .env va bazani olib tashlash SHART, aks holda
#    update.sh uni ham maktab deb hisoblaydi
mv /opt/school_bot/.env /root/eski_19bmsm.env
mv /opt/school_bot/school.db /root/eski_19bmsm.school.db
rm -f /opt/school_bot/token.json /opt/school_bot/credentials.json
```

Xato bo'lsa orqaga: `systemctl disable --now school-bot@19bmsm
school-webapp@19bmsm`, `.env` ni qaytarib qo'yib
`systemctl enable --now school-bot school-webapp`, ports.map dan
ikki qatorni o'chirib `app.cybermate.uz` blokini tiklash.

---

## Zaxira

Har maktab o'z bazasini **o'z Google Drive akkauntiga** yuboradi
(`services/backup.py`, 6 soatda bir marta, 30 nusxa saqlanadi).
Akkauntlar alohida bo'lgani uchun zaxiralar ham aralashmaydi —
qo'shimcha sozlash talab qilinmaydi.

---

## Foydali buyruqlar

```bash
systemctl status school-bot@5mmm
journalctl -u school-bot@5mmm -f
systemctl restart school-webapp@5mmm
cat /etc/nginx/school-ports.map
ls /opt/schools/
```
