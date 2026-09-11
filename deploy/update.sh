#!/bin/bash

# ==== MAQSAD VA UMUMIY QOIDALAR ====
# Bu skript maktab botining joriy versiyasini GitHub'dan tortib olib o'rnatadi.
# Biz xatolik yuz bersa avtomatik to'xtash uchun (e), e'lon qilinmagan
# o'zgaruvchilardan himoya qilish uchun (u) va quvurlardagi xatoni ushlash
# uchun (o pipefail) qat'iy rejimni yoqamiz.
set -euo pipefail

# ==== STANDART SOZLAMALAR ====
# Quyidagi o'zgaruvchilar skriptning asosiy ishlash muhitini belgilaydi.
# Ularni o'zgartirish uchun alohida konfiguratsiya faylidan foydalaniladi.
CODE_DIR="/opt/school_bot"
SCHOOLS_DIR="/opt/schools"
BRANCH="main"
OWNER="botuser"
BACKUP_DIR="/var/backups/school_bot"
PORTS_MAP="/etc/nginx/school-ports.map"
BASE_DOMAIN="cybermate.uz"

# ==== SOZLAMALARNI YUKLASH ====
# Konfiguratsiyani qattiq kodlash o'rniga, moslashuvchanlik uchun tashqi
# fayldan o'qiymiz. Agar fayl bor bo'lsa, tepadagi sozlamalar ustidan yozadi.
CONFIG_FILE="${SCHOOLS_CONF:-/etc/school-bot/schools.conf}"
if [[ -f "$CONFIG_FILE" ]]; then
    # shellcheck disable=SC1090
    . "$CONFIG_FILE"
fi

# ==== YORDAMCHI FUNKSIYALAR ====
# Skript bo'ylab bir xil xato va xabar chiqarish mantig'ini takrorlamaslik uchun.
xato() {
    echo "XATO: $1" >&2
    exit 1
}

say() {
    echo ""
    echo "=== $1 ==="
}

# ==== ARGUMENTLARNI O'QISH ====
# Foydalanuvchi qanday rejimda ishlashni xohlayotganini aniqlash.
MODE_CHECK=0
ONLY_SLUG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --check)
            MODE_CHECK=1
            shift
            ;;
        --only)
            if [[ -z "${2:-}" ]]; then
                xato "--only argumenti maktab nomini (slug) talab qiladi."
            fi
            ONLY_SLUG="$2"
            shift 2
            ;;
        -h|--help)
            echo "Foydalanish: $0 [--check] [--only <slug>] [-h|--help]"
            echo "  --check   Faqat tekshirish, o'zgartirmaydi"
            echo "  --only    Faqat bitta maktabni yangilash"
            exit 0
            ;;
        *)
            xato "Noto'g'ri argument: $1"
            ;;
    esac
done

# ==== DASTLABKI RUHSAT VA MUHIT TEKSHIRUVI ====
# Tizim fayllarini o'zgartirish va xizmatlarni boshqarish uchun root huquqi kerak.
if [[ "$(id -u)" -ne 0 ]]; then
    xato "Skriptni root huquqi (sudo) bilan ishga tushiring."
fi

# Kod joylashuvi git repozitoriysi bo'lishi shart, aks holda manbadan yangilab bo'lmaydi.
if [[ ! -d "$CODE_DIR/.git" ]]; then
    xato "$CODE_DIR papkasida git repozitoriy topilmadi.
Yordam uchun deploy/GIT_DEPLOY.md fayliga qarang."
fi

# ==== JOYLASHUVNI ANIQLASH ====
# Skript ham eski bitta maktabli tizimni (LEGACY), ham yangi ko'p maktabli 
# tizimni (MULTI) qo'llab-quvvatlaydi. Har bir topilgan maktabni massivga saqlaymiz.
declare -a SCHOOLS_SLUG=()
declare -a SCHOOLS_IS_LEGACY=()
declare -a SCHOOLS_DIR_PATH=()
declare -a SCHOOLS_ENV=()
declare -a SCHOOLS_BOT_SVC=()
declare -a SCHOOLS_WEB_SVC=()
declare -a SCHOOLS_DOMAIN=()

HAS_MULTI=0
HAS_LEGACY=0

# MULTI maktablarni qidirish
if [[ -d "$SCHOOLS_DIR" ]]; then
    for s_dir in "$SCHOOLS_DIR"/*; do
        if [[ -d "$s_dir" && -f "$s_dir/.env" ]]; then
            slug=$(basename "$s_dir")
            if [[ -n "$ONLY_SLUG" && "$slug" != "$ONLY_SLUG" ]]; then
                continue
            fi
            SCHOOLS_SLUG+=("$slug")
            SCHOOLS_IS_LEGACY+=(0)
            SCHOOLS_DIR_PATH+=("$s_dir")
            SCHOOLS_ENV+=("$s_dir/.env")
            SCHOOLS_BOT_SVC+=("school-bot@$slug")
            SCHOOLS_WEB_SVC+=("school-webapp@$slug")
            SCHOOLS_DOMAIN+=("$slug.$BASE_DOMAIN")
            HAS_MULTI=1
        fi
    done
fi

# LEGACY maktabni qidirish
if [[ -f "$CODE_DIR/.env" ]]; then
    legacy_slug=$(grep '^SCHOOL_SLUG=' "$CODE_DIR/.env" | cut -d '=' -f 2 | tr -d ' ' || true)
    if [[ -z "$legacy_slug" ]]; then
        legacy_slug="maktab"
    fi
    
    if [[ -z "$ONLY_SLUG" || "$ONLY_SLUG" == "legacy" || "$ONLY_SLUG" == "$legacy_slug" ]]; then
        SCHOOLS_SLUG+=("$legacy_slug")
        SCHOOLS_IS_LEGACY+=(1)
        SCHOOLS_DIR_PATH+=("$CODE_DIR")
        SCHOOLS_ENV+=("$CODE_DIR/.env")
        SCHOOLS_BOT_SVC+=("school-bot")
        SCHOOLS_WEB_SVC+=("school-webapp")
        SCHOOLS_DOMAIN+=("")
        HAS_LEGACY=1
    fi
fi

if [[ ${#SCHOOLS_SLUG[@]} -eq 0 ]]; then
    xato "Tizimda hech qanday maktab .env fayli topilmadi yoki so'ralgan maktab mavjud emas.
Maktab sozlanmagan."
fi

if [[ $HAS_MULTI -eq 1 && $HAS_LEGACY -eq 1 ]]; then
    echo "OGOHLANTIRISH: Joylashuv aralash! Ham shablon (MULTI), ham asosiy (LEGACY) papkada maktab mavjud."
    echo "Eski maktabni shablon sxemasiga ko'chirish tavsiya etiladi (qarang: deploy/KOP_MAKTAB.md)."
fi

# ==== GIT ORQALI YANGILANISHLARNI TEKSHIRISH ====
# Yangilanish bor yoki yo'qligini aniqlash. Agar o'zgarish bo'lmasa ishni to'xtatamiz.
say "Git repozitoriydan yangilanishlarni tekshirish"
cd "$CODE_DIR" || xato "$CODE_DIR ga o'tib bo'lmadi."
git fetch origin "$BRANCH" --quiet

OLD_COMMIT=$(git rev-parse HEAD)
NEW_COMMIT=$(git rev-parse "origin/$BRANCH")

if [[ "$OLD_COMMIT" == "$NEW_COMMIT" ]]; then
    echo "Yangilanish yo'q. Joriy versiya: $OLD_COMMIT"
    exit 0
fi

echo "Quyidagi o'zgarishlar topildi:"
git log --oneline "${OLD_COMMIT}..${NEW_COMMIT}"
git diff --stat "$OLD_COMMIT" "$NEW_COMMIT" | tail -1

# ==== PREFLIGHT (DASTLABKI) TEKSHIRUVLAR ====
# Tizim ishlashi uchun barcha zaruriy muhit o'zgaruvchilari va 
# port mosliklarini o'zgartirishlardan oldin tekshiramiz.
say "Preflight tekshiruvlari boshlandi"

for i in "${!SCHOOLS_SLUG[@]}"; do
    slug="${SCHOOLS_SLUG[$i]}"
    env_file="${SCHOOLS_ENV[$i]}"
    bot_svc="${SCHOOLS_BOT_SVC[$i]}"
    web_svc="${SCHOOLS_WEB_SVC[$i]}"
    domain="${SCHOOLS_DOMAIN[$i]}"
    
    echo "Tekshirilmoqda: $slug"
    
    # a) BOT_TOKEN va ADMIN_IDS tekshiruvi (bash 'source' ishlatilmaydi, chunki
    # .env da bo'sh joyli nomlar bo'lishi mumkin va bash xato beradi)
    if ! grep -q "^BOT_TOKEN=.\+" "$env_file"; then
        xato "$env_file faylida BOT_TOKEN topilmadi yoki bo'sh."
    fi
    if ! grep -q "^ADMIN_IDS=.\+" "$env_file"; then
        xato "$env_file faylida ADMIN_IDS topilmadi yoki bo'sh."
    fi
    
    # b) WEBAPP_PORT tekshiruvi
    webapp_port=$(grep '^WEBAPP_PORT=' "$env_file" | cut -d '=' -f 2 | tr -d ' ' || true)
    if [[ -z "$webapp_port" ]] || ! [[ "$webapp_port" =~ ^[0-9]+$ ]]; then
        xato "$env_file faylida WEBAPP_PORT noto'g'ri yoki yo'q."
    fi
    
    # c) PORT MOSLIGI tekshiruvi
    # Nega muhim: ilgari port .env da va nginx/servis fayllarida qattiq yozilgan edi.
    # Agar ular turli xil bo'lsa, gunicorn va nginx ulanolmaydi va 502 xato beradi.
    if [[ "${SCHOOLS_IS_LEGACY[$i]}" -eq 0 ]]; then
        # MULTI rejimi
        if [[ ! -f "$PORTS_MAP" ]]; then
            xato "MULTI rejim uchun $PORTS_MAP fayli topilmadi."
        fi
        
        map_port=$(grep "^[[:space:]]*${domain}[[:space:]]\+" "$PORTS_MAP" | awk '{print $2}' | tr -d ';' || true)
        if [[ "$map_port" != "$webapp_port" ]]; then
            xato "Port mos kelmadi (MULTI)! $env_file dagi WEBAPP_PORT=$webapp_port, lekin $PORTS_MAP da $domain uchun $map_port ko'rsatilgan.
Iltimos, ularni bir xil qilib sozlang."
        fi
    else
        # LEGACY rejimi
        found_nginx_ports=""
        port_matched=0
        if [[ -d "/etc/nginx/sites-enabled" ]]; then
            for conf_file in /etc/nginx/sites-enabled/*; do
                if [[ -f "$conf_file" ]]; then
                    # "proxy_pass http://127.0.0.1:<port>" yoki shunga o'xshash qatorni izlash
                    ports=$(grep -Eo 'proxy_pass[[:space:]]+http://(127\.0\.0\.1|localhost):[0-9]+' "$conf_file" | grep -Eo '[0-9]+$' || true)
                    for p in $ports; do
                        found_nginx_ports="${found_nginx_ports}${conf_file}: ${p}
"
                        if [[ "$p" == "$webapp_port" ]]; then
                            port_matched=1
                        fi
                    done
                fi
            done
        fi
        
        if [[ -z "$found_nginx_ports" ]]; then
            echo "OGOHLANTIRISH: nginx sozlamasida proxy_pass topilmadi, portni qo'lda tekshiring."
        elif [[ $port_matched -eq 0 ]]; then
            xato "Port mos kelmadi (LEGACY)! $env_file dagi WEBAPP_PORT=$webapp_port, lekin nginx sozlamalarida quyidagi portlar topildi:
${found_nginx_ports}Ularni to'g'rilang."
        fi
    fi
    
    # d) Python venv va requirements tekshiruvi
    if [[ ! -f "${SCHOOLS_DIR_PATH[$i]}/venv/bin/python" ]]; then
        xato "${SCHOOLS_DIR_PATH[$i]}/venv/bin/python topilmadi. Virtual muhit yaratilmagan."
    fi
    
    # requirements.txt doim asosiy repo ichidan tekshiriladi
    if [[ ! -f "$CODE_DIR/requirements.txt" ]]; then
        xato "$CODE_DIR/requirements.txt topilmadi."
    fi
    
    # e) Systemd servislar tekshiruvi
    if ! systemctl cat "$bot_svc" >/dev/null 2>&1; then
        xato "$bot_svc servisi o'rnatilmagan."
    fi
    if ! systemctl cat "$web_svc" >/dev/null 2>&1; then
        xato "$web_svc servisi o'rnatilmagan."
    fi
done

if [[ $MODE_CHECK -eq 1 ]]; then
    say "Check rejimi yakunlandi. Barcha tekshiruvlar muvaffaqiyatli."
    exit 0
fi

# ==== ZAXIRA NUSXALARI ====
# Ma'lumotlar yo'qolishining oldini olish uchun har safar yangilashdan oldin
# ma'lumotlar bazasidan (school.db) xavfsiz zaxira nusxasi olinadi.
say "Zaxira nusxalarini yaratish"
mkdir -p "$BACKUP_DIR"

for i in "${!SCHOOLS_SLUG[@]}"; do
    slug="${SCHOOLS_SLUG[$i]}"

    # Baza fayli nomi .env dagi DB_PATH dan olinadi - "school.db" deb
    # qotib qolmasin. Nisbiy yo'l maktab papkasiga nisbatan hisoblanadi,
    # config.py ham xuddi shunday qiladi (_yol funksiyasi).
    db_rel=$(grep '^DB_PATH=' "${SCHOOLS_ENV[$i]}" | cut -d '=' -f 2 | tr -d ' ' || true)

    if [[ -z "$db_rel" ]]; then
        db_rel="school.db"
    fi

    case "$db_rel" in
        /*) db_file="$db_rel" ;;
        *)  db_file="${SCHOOLS_DIR_PATH[$i]}/$db_rel" ;;
    esac


    if [[ -f "$db_file" ]]; then
        ts=$(date +%Y%m%d_%H%M%S)
        backup_file="$BACKUP_DIR/${slug}_${ts}.db"
        
        if command -v sqlite3 >/dev/null 2>&1; then
            sqlite3 "$db_file" ".backup '$backup_file'"
        else
            cp "$db_file" "$backup_file"
        fi
        
        # Har bir maktab uchun faqat oxirgi 20 ta nusxani qoldirish
        # ls va wc orqali hisoblaymiz, eski fayllarni o'chiramiz
        # shellcheck disable=SC2012
        count=$(ls -1q "$BACKUP_DIR/${slug}_"*.db 2>/dev/null | wc -l)
        if [[ $count -gt 20 ]]; then
            # shellcheck disable=SC2012
            ls -1tr "$BACKUP_DIR/${slug}_"*.db | head -n "$((count - 20))" | xargs rm -f
        fi
        echo "$slug uchun zaxira olindi: $backup_file"
    fi
done

echo "$OLD_COMMIT" > "$BACKUP_DIR/last_commit.txt"

# ==== KODNI YANGILASH VA TARQATISH ====
say "Kodni yangilash va fayllarni tarqatish"

cd "$CODE_DIR"
# git reset --hard maxfiy va .gitignore dagi fayllarga ta'sir qilmaydi
# (masalan: .env, *.db, token.json kabilar o'zgarmaydi)
git reset --hard "origin/$BRANCH"

declare -a RSYNC_EXCLUDES=(
    "--exclude" ".git"
    "--exclude" "venv"
    "--exclude" "__pycache__"
    "--exclude" "*.db"
    "--exclude" "*.db-wal"
    "--exclude" "*.db-shm"
    "--exclude" "*.db-journal"
    "--exclude" "school.db.before_*"
    "--exclude" ".env"
    "--exclude" "token.json"
    "--exclude" "credentials.json"
    "--exclude" "service_account.json"
    "--exclude" "tests/_tmp"
    "--exclude" "uploads/"
    "--exclude" "*.log"
)

for i in "${!SCHOOLS_SLUG[@]}"; do
    slug="${SCHOOLS_SLUG[$i]}"
    s_dir="${SCHOOLS_DIR_PATH[$i]}"
    
    if [[ "${SCHOOLS_IS_LEGACY[$i]}" -eq 0 ]]; then
        echo "$slug uchun fayllar nusxalanmoqda..."
        rsync -a --delete "$CODE_DIR/" "$s_dir/" "${RSYNC_EXCLUDES[@]}"
    fi
    
    chown -R "$OWNER:$OWNER" "$s_dir"
done

# ==== KUTUBXONALARNI YANGILASH ====
# Faqatgina requirements.txt faylida o'zgarish bo'lsagina ishga tushadi
say "Kutubxonalarni tekshirish"
cd "$CODE_DIR"
REQUIREMENTS_CHANGED=0
if ! git diff --quiet "$OLD_COMMIT" "$NEW_COMMIT" -- requirements.txt; then
    REQUIREMENTS_CHANGED=1
    echo "requirements.txt o'zgargan, paketlar yangilanadi."
fi

if [[ $REQUIREMENTS_CHANGED -eq 1 ]]; then
    for i in "${!SCHOOLS_SLUG[@]}"; do
        slug="${SCHOOLS_SLUG[$i]}"
        s_dir="${SCHOOLS_DIR_PATH[$i]}"
        echo "$slug uchun kutubxonalar o'rnatilmoqda..."
        sudo -u "$OWNER" "$s_dir/venv/bin/pip" install -q -r "$CODE_DIR/requirements.txt"
    done
fi

# ==== SERVISLARNI QAYTA ISHGA TUSHIRISH ====
# Xizmatlar qayta ishga tushirilganda migratsiyalar botning o'zi orqali 
# (main.py -> run_migrations) avtomatik bajariladi. Skript o'zi SQL yozmaydi.
say "Xizmatlarni qayta ishga tushirish"

declare -a FAILED_SERVICES=()

for i in "${!SCHOOLS_SLUG[@]}"; do
    bot_svc="${SCHOOLS_BOT_SVC[$i]}"
    web_svc="${SCHOOLS_WEB_SVC[$i]}"
    
    echo "$bot_svc va $web_svc qayta ishga tushirilmoqda..."
    systemctl restart "$bot_svc"
    systemctl restart "$web_svc"
done

echo "Kutib turamiz (6 soniya)..."
sleep 6

say "Holatni tekshirish"
for i in "${!SCHOOLS_SLUG[@]}"; do
    bot_svc="${SCHOOLS_BOT_SVC[$i]}"
    web_svc="${SCHOOLS_WEB_SVC[$i]}"
    
    # is-active "active" qaytarmasa, demak xato yoki "activating" da qotib qolgan
    if [[ "$(systemctl is-active "$bot_svc")" != "active" ]]; then
        FAILED_SERVICES+=("$bot_svc")
    fi
    
    if [[ "$(systemctl is-active "$web_svc")" != "active" ]]; then
        FAILED_SERVICES+=("$web_svc")
    fi
done

# ==== XATO BO'LSA ORQAGA QAYTARISH (ROLLBACK) ====
if [[ ${#FAILED_SERVICES[@]} -gt 0 ]]; then
    say "XATOLIK: Ba'zi xizmatlar ishga tushmadi. Orqaga qaytarilmoqda!"
    
    cd "$CODE_DIR"
    git reset --hard "$OLD_COMMIT"
    
    for i in "${!SCHOOLS_SLUG[@]}"; do
        slug="${SCHOOLS_SLUG[$i]}"
        s_dir="${SCHOOLS_DIR_PATH[$i]}"
        
        if [[ "${SCHOOLS_IS_LEGACY[$i]}" -eq 0 ]]; then
            rsync -a --delete "$CODE_DIR/" "$s_dir/" "${RSYNC_EXCLUDES[@]}"
        fi
        
        chown -R "$OWNER:$OWNER" "$s_dir"
        
        systemctl restart "${SCHOOLS_BOT_SVC[$i]}"
        systemctl restart "${SCHOOLS_WEB_SVC[$i]}"
    done
    
    echo ""
    echo "Yiqilgan xizmatlar loglari:"
    for svc in "${FAILED_SERVICES[@]}"; do
        echo "--- $svc jurnalidan oxirgi 25 qator ---"
        journalctl -u "$svc" -n 25 --no-pager
    done
    
    echo ""
    echo "DIQQAT: Migratsiyalar ma'lumotlar bazasini o'zgartirgan bo'lishi mumkin."
    echo "Bunday holatda ma'lumotlar bazasini qo'lda tiklashingiz kerak:"
    echo "Zaxira papkasi: $BACKUP_DIR"
    echo "Qayta tiklash misoli: cp $BACKUP_DIR/<nusxa_nomi>.db /opt/schools/<slug>/school.db"
    
    exit 1
fi

# ==== XULOSA ====
say "YANGILASH MUVAFFAQIYATLI YAKUNLANDI"

for i in "${!SCHOOLS_SLUG[@]}"; do
    slug="${SCHOOLS_SLUG[$i]}"
    s_dir="${SCHOOLS_DIR_PATH[$i]}"
    bot_svc="${SCHOOLS_BOT_SVC[$i]}"
    web_svc="${SCHOOLS_WEB_SVC[$i]}"
    
    # Bazaning migratsiya versiyasini olish
    cd "$s_dir"
    version=$(sudo -u "$OWNER" venv/bin/python -c "from db.migrations import current_version; print(current_version())" 2>/dev/null || echo "?")
    
    bot_stat=$(systemctl is-active "$bot_svc")
    web_stat=$(systemctl is-active "$web_svc")
    
    echo "- Maktab: $slug | Bot: $bot_stat | WebApp: $web_stat | Baza versiyasi: $version"
done
