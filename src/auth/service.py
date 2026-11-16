"""Signing in with a password and a one-time code (docs/superpowers/plans/2026-11-15-two-factor-login.md).

`sign_in` checks both factors every time, so neither the time taken nor the message says which one was wrong, and an
unknown user gets exactly the same error as a wrong password. Five failures lock the account for five minutes; the lock
is not announced either (a locked account just fails). Every attempt is written to the append-only `auth_events`; the
password and the code are never written anywhere.
"""
from datetime import UTC, datetime, timedelta

from src.auth.passwords import check_password, hash_password, new_one_time_password
from src.auth.totp import new_secret, verify

LOCK_AFTER = 5
LOCK_SECONDS = 300
ROLES = ("admin", "dispatcher", "observer")
ISSUER = "DisasterResponse"
_DUMMY = hash_password("no such account")


class AuthError(Exception):
    """The one error a failed sign-in ever shows: code SIGN_IN_FAILED."""

    def __init__(self):
        self.code = "SIGN_IN_FAILED"
        super().__init__("Sign-in failed. Check the username, password and code, or try again later.")


def _stamp(now):
    return (now or datetime.now(UTC)).isoformat()


def _event(conn, now, username, kind, ok, detail=None):
    conn.execute(
        "INSERT INTO auth_events (at, username, kind, ok, detail) VALUES (?, ?, ?, ?, ?)",
        (_stamp(now), str(username)[:64], kind, int(ok), detail),
    )


def enrol(conn, username, role="dispatcher", now=None):
    """Create the account (or reset an existing one, such as the seeded demo account) with a new password and phone
    secret. Returns the one-time password and the setup key; they are shown once and only hashes/secrets are kept."""
    username = (username or "").strip()
    if not username:
        raise ValueError("a username is required")
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    password = new_one_time_password()
    pw_hash, pw_salt = hash_password(password)
    secret = new_secret()
    stamp = _stamp(now)
    existing = conn.execute("SELECT id FROM dispatcher_accounts WHERE username = ?", (username,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE dispatcher_accounts SET password_hash = ?, password_salt = ?, role = ?, totp_secret = ?, "
            "totp_last_step = NULL, failed_attempts = 0, locked_until = NULL WHERE id = ?",
            (pw_hash, pw_salt, role, secret, existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO dispatcher_accounts (username, password_hash, password_salt, role, is_fictional_test_account, created_at, totp_secret) "
            "VALUES (?, ?, ?, ?, 1, ?, ?)",
            (username, pw_hash, pw_salt, role, stamp, secret),
        )
    _event(conn, now, username, "enrolled", True)
    conn.commit()
    uri = f"otpauth://totp/{ISSUER}:{username}?secret={secret}&issuer={ISSUER}"
    return {"username": username, "role": role, "password": password, "totp_secret": secret, "otpauth": uri}


def sign_in(conn, username, password, code, now=None):
    """The account id if the password and the code are both right, else AuthError (always the same one)."""
    moment = now or datetime.now(UTC)
    row = conn.execute("SELECT * FROM dispatcher_accounts WHERE username = ?", (username,)).fetchone() if isinstance(username, str) else None
    locked = bool(row and row["locked_until"] and datetime.fromisoformat(row["locked_until"]) > moment)
    stored_hash, stored_salt = (row["password_hash"], row["password_salt"]) if row else _DUMMY
    password_ok = check_password(password, stored_hash, stored_salt)
    step = verify(row["totp_secret"], code, moment.timestamp(), row["totp_last_step"]) if row and row["totp_secret"] else None
    if row and password_ok and step is not None and not locked:
        conn.execute("UPDATE dispatcher_accounts SET failed_attempts = 0, locked_until = NULL, totp_last_step = ? WHERE id = ?", (step, row["id"]))
        _event(conn, moment, username, "sign_in", True)
        conn.commit()
        return row["id"]
    if row and not locked:
        failures = row["failed_attempts"] + 1
        if failures >= LOCK_AFTER:
            conn.execute("UPDATE dispatcher_accounts SET failed_attempts = 0, locked_until = ? WHERE id = ?", ((moment + timedelta(seconds=LOCK_SECONDS)).isoformat(), row["id"]))
            _event(conn, moment, username, "locked", False, "too many failed attempts")
        else:
            conn.execute("UPDATE dispatcher_accounts SET failed_attempts = ? WHERE id = ?", (failures, row["id"]))
    _event(conn, moment, username, "sign_in", False)
    conn.commit()
    raise AuthError()
