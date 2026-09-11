#!/usr/bin/env bash
# ==========================
# deploy/update.sh
# SERVERNI GITHUB'DAN YANGILASH
# ==========================
#
# Qo'lda ishga tushiriladi - avtomatik pull YO'Q:
#
#     ssh root@SERVER
#     cd /opt/school_bot
#     sudo bash deploy/update.sh            # yangilaydi
#     sudo bash deploy/update.sh --check    # faqat ko'rsatadi
#
# Nima qiladi:
#   1. bazadan zaxira nusxa oladi
#   2. GitHub'dan yangi kodni oladi
#   3. kutubxonalar o'zgargan bo'lsa o'rnatadi
#   4. xizmatlarni qayta ishga tushiradi
#   5. ko'tarilmasa - ESKI HOLATGA QAYTARADI
#
# Maxfiy fayllarga TEGMAYDI: .env, config.py, school.db,
# token.json, credentials.json - hammasi .gitignore da,
# shuning uchun git ularni ko'rmaydi ham.
# ==========================

set -euo pipefail

APP_DIR="/opt/school_bot"
BRANCH="main"
OWNER="botuser"
SERVICES="school-bot school-webapp"
BACKUP_DIR="/var/backups/school_bot"

CHECK_ONLY="no"

if [ "${1:-}" = "--check" ]; then
    CHECK_ONLY="yes"
fi


say() {
    echo ""
    echo "=== $* ==="
}


cd "$APP_DIR"


# ==========================
# 1. GIT REPO EKANINI TEKSHIRISH
# ==========================

if [ ! -d .git ]; then
    echo "XATO: $APP_DIR git repozitoriysi emas."
    echo "Avval bir martalik o'tkazishni bajaring: deploy/GIT_DEPLOY.md"
    exit 1
fi


# ==========================
# 2. NIMA O'ZGARISHINI KO'RSATISH
# ==========================

say "GitHub'dan ma'lumot olinmoqda"

git fetch origin "$BRANCH" --quiet

OLD_COMMIT="$(git rev-parse HEAD)"
NEW_COMMIT="$(git rev-parse "origin/$BRANCH")"

if [ "$OLD_COMMIT" = "$NEW_COMMIT" ]; then
    echo "Yangilanish yo'q - serverdagi kod eng so'nggisi."
    echo "Joriy: $(git log -1 --format='%h %s')"
    exit 0
fi

say "Qo'shiladigan o'zgarishlar"

git --no-pager log --oneline "$OLD_COMMIT..$NEW_COMMIT"

echo ""
echo "Fayllar:"
git --no-pager diff --stat "$OLD_COMMIT" "$NEW_COMMIT" | tail -1

if [ "$CHECK_ONLY" = "yes" ]; then
    echo ""
    echo "(--check rejimi - hech narsa o'zgartirilmadi)"
    exit 0
fi


# ==========================
# 3. ZAXIRA
# ==========================
#
# Migratsiyalar bazani o'zgartiradi va ularni orqaga qaytarib
# bo'lmaydi - shuning uchun nusxa yangilanishdan OLDIN olinadi.

say "Zaxira"

mkdir -p "$BACKUP_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"

if [ -f school.db ]; then
    # sqlite WAL rejimida - oddiy cp yarim holatni olishi mumkin
    sqlite3 school.db ".backup '$BACKUP_DIR/school_$STAMP.db'" \
        || cp school.db "$BACKUP_DIR/school_$STAMP.db"

    echo "Baza: $BACKUP_DIR/school_$STAMP.db"
fi

echo "$OLD_COMMIT" > "$BACKUP_DIR/last_commit.txt"

# eski zaxiralar joyni band qilmasin - oxirgi 20 tasi qoladi
ls -1t "$BACKUP_DIR"/school_*.db 2>/dev/null | tail -n +21 | xargs -r rm -f


# ==========================
# 4. KODNI YANGILASH
# ==========================

say "Kod yangilanmoqda"

git reset --hard "origin/$BRANCH" --quiet

chown -R "$OWNER:$OWNER" "$APP_DIR"

echo "$(git log -1 --format='%h %s')"


# ==========================
# 5. KUTUBXONALAR
# ==========================

if ! git diff --quiet "$OLD_COMMIT" "$NEW_COMMIT" -- requirements.txt; then

    say "requirements.txt o'zgardi - kutubxonalar o'rnatilmoqda"

    sudo -u "$OWNER" "$APP_DIR/venv/bin/pip" install -q -r requirements.txt
fi


# ==========================
# 6. QAYTA ISHGA TUSHIRISH
# ==========================
#
# Migratsiyalar botning o'zi startida bajariladi
# (main.py -> run_migrations).

say "Xizmatlar qayta ishga tushmoqda"

# shellcheck disable=SC2086
systemctl restart $SERVICES

sleep 6

FAILED=""

for service in $SERVICES; do

    if ! systemctl is-active --quiet "$service"; then
        FAILED="$FAILED $service"
    fi

done


# ==========================
# 7. KO'TARILMASA - ORQAGA
# ==========================

if [ -n "$FAILED" ]; then

    say "XATO: ko'tarilmadi -$FAILED"

    journalctl -u school-bot -n 25 --no-pager | tail -25

    say "Eski holatga qaytarilmoqda"

    git reset --hard "$OLD_COMMIT" --quiet

    chown -R "$OWNER:$OWNER" "$APP_DIR"

    # shellcheck disable=SC2086
    systemctl restart $SERVICES

    echo ""
    echo "Kod $OLD_COMMIT ga qaytarildi."
    echo "DIQQAT: migratsiya bazani o'zgartirgan bo'lishi mumkin."
    echo "Kerak bo'lsa: $BACKUP_DIR/school_$STAMP.db"

    exit 1
fi


say "Tayyor"

for service in $SERVICES; do
    echo "$service: $(systemctl is-active "$service")"
done

echo ""
echo "Versiya: $(git log -1 --format='%h %s (%ci)')"
