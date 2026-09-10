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

Keyin **qo'lda** ikki qadam qoladi (avtomatlashtirib bo'lmaydi):

| Qadam | Nega qo'lda |
|---|---|
| `credentials.json` ni maktab papkasiga qo'yish + OAuth | Google avtorizatsiyasi brauzerda tasdiqlanadi |
| @BotFather → `/setmenubutton` → Mini App manzili | BotFather API orqali sozlanmaydi |

---

## Yangilanish tartibi

Avval **pilot** (19-BMSM), ishlab tursa — qolganlarga.

```bash
# 1) umumiy kodni yangilash
cd /opt/school_bot && git pull

# 2) pilot maktab
rsync -a --exclude venv --exclude .env --exclude '*.db' \
      --exclude token.json --exclude credentials.json \
      /opt/school_bot/ /opt/schools/19bmsm/
/opt/schools/19bmsm/venv/bin/pip install -q -r /opt/schools/19bmsm/requirements.txt
systemctl restart school-bot@19bmsm school-webapp@19bmsm

# 3) bir hafta kuzating, keyin qolgan maktablarga xuddi shunday
```

Sxema migratsiyalari bot ishga tushganda **o'zi** qo'llanadi
(`db/migrations.py`) — qo'lda SQL yozish kerak emas.

Versiyani tekshirish:

```bash
cd /opt/schools/19bmsm && venv/bin/python -c "from db.migrations import current_version; print(current_version())"
```

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
