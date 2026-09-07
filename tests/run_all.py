# -*- coding: utf-8 -*-
"""Barcha sinovlarni ketma-ket ishga tushiradi.

    python tests/run_all.py

Har bir sinov o'zining `tests/_tmp/*.db` bazasida ishlaydi -
haqiqiy `school.db` ga tegmaydi.
"""

import glob
import os
import subprocess
import sys

# Windows konsoli cp1251 - emoji chiqmasligi uchun o`z chiqishimizni ham UTF-8 qilamiz
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:  # Python < 3.7
    pass

HERE = os.path.dirname(os.path.abspath(__file__))

# concurrent_test.py argument talab qiladi - alohida chaqiriladi
SKIP = {"run_all.py", "concurrent_test.py"}


def main():
    files = sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(HERE, "*.py"))
        if os.path.basename(p) not in SKIP
    )

    # Windows konsoli cp1251 - emoji chiqmaydi, shuning uchun UTF-8 majburlanadi
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")

    failed = []
    for name in files:
        print("=" * 60)
        print(name)
        print("=" * 60)
        r = subprocess.run(
            [sys.executable, os.path.join(HERE, name)],
            env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        sys.stdout.write(r.stdout)
        if r.stderr:
            sys.stdout.write(r.stderr)
        if r.returncode != 0:
            failed.append(name)

    print()
    print("=" * 60)
    if failed:
        print("YIQILGAN SINOVLAR:", ", ".join(failed))
        return 1
    print("Barcha fayllar xatosiz tugadi (%d ta)" % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
