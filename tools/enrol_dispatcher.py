#!/usr/bin/env python3
"""enrol_dispatcher.py - create a dispatcher account (or reset one, such as the seeded demo-dispatcher) for two-factor sign-in.

    python tools/enrol_dispatcher.py USERNAME [admin|dispatcher|observer] [DB_PATH]     (default role dispatcher, default data/dev.sqlite)

It prints, ONCE, a random password and the setup key for the authenticator app on the person's own phone (type the key
into any authenticator app that takes a time-based code, for example Duo Mobile's third-party account option; or
open the otpauth link). Only a salted hash of the password and the phone secret are stored. Run it again to reset.
"""
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.auth.service import enrol  # noqa: E402


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 2
    username, role = argv[0], (argv[1] if len(argv) > 1 else "dispatcher")
    db_path = argv[2] if len(argv) > 2 else os.environ.get("DB_PATH", "data/dev.sqlite")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        account = enrol(conn, username, role)
    except ValueError as exc:
        print(f"cannot enrol: {exc}", file=sys.stderr)
        return 2
    finally:
        conn.close()
    print(f"Account ready: {account['username']} ({account['role']}) in {db_path}")
    print(f"  Password (shown once, write it down now): {account['password']}")
    print(f"  Phone setup key (type it into your authenticator app): {account['totp_secret']}")
    print(f"  Or open this link on the phone: {account['otpauth']}")
    print("Then start the app with ./script/start and sign in at http://127.0.0.1:8080/login")
    return 0


if __name__ == "__main__":
    sys.exit(main())
