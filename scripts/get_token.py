# ==========================
# scripts/get_token.py
# BIR MARTALIK GOOGLE AVTORIZATSIYA
# ==========================
#
# Bu skriptni BROUZERI BOR kompyuterda ishga tushiring
# (VPS da emas - u yerda brouzer yo'q).
#
#   python scripts/get_token.py
#
# Natijada token.json hosil bo'ladi.
# Uni VPS ga ko'chirsangiz, bot brouzersiz ishlayveradi.
#
# ==========================


import os
import sys

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from google_auth_oauthlib.flow import InstalledAppFlow

from services.gdrive import (
    SCOPES,
    TOKEN_FILE,
    CREDENTIALS_FILE
)


def main():

    if not os.path.exists(CREDENTIALS_FILE):

        print("❌ credentials.json topilmadi.")
        print()
        print("Uni quyidagicha oling:")
        print()
        print("  1. console.cloud.google.com ga kiring")
        print("  2. Yangi loyiha yarating")
        print("  3. 'Google Drive API' ni yoqing")
        print("  4. OAuth consent screen -> External -> o'zingizni")
        print("     Test users ro'yxatiga qo'shing")
        print("  5. Credentials -> Create -> OAuth client ID")
        print("     -> Desktop app")
        print("  6. JSON ni yuklab olib, shu papkaga")
        print("     credentials.json nomi bilan saqlang")
        print()
        print("Papka:", os.path.dirname(CREDENTIALS_FILE))

        return 1


    if os.path.exists(TOKEN_FILE):

        answer = input(
            "token.json allaqachon bor. "
            "Qayta olinsinmi? (ha/yo'q): "
        ).strip().lower()

        if answer not in ("ha", "h", "y", "yes"):
            print("Bekor qilindi.")
            return 0


    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE,
        SCOPES
    )

    print()
    print("🌐 Brouzer ochiladi - Google akkauntingizga kiring")
    print("   va ruxsat bering.")
    print()

    creds = flow.run_local_server(

        port=0,

        # refresh_token olish uchun shart
        access_type="offline",
        prompt="consent"

    )


    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())


    print()
    print("✅ token.json saqlandi:", TOKEN_FILE)
    print()


    # darhol sinab ko'ramiz

    from services import gdrive

    info = gdrive.check()

    print("👤 Akkaunt:", info["email"])

    if info["limit_gb"]:
        print(
            "💾 Band:",
            info["used_gb"], "GB /",
            info["limit_gb"], "GB"
        )

    print()
    print("Endi token.json ni VPS ga ko'chiring:")
    print("  scp token.json user@vps:/opt/school_bot/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
