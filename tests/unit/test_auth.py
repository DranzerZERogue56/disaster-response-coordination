"""Two-factor sign-in (docs/superpowers/plans/2026-11-15-two-factor-login.md, Tasks 1 to 3): codes, passwords, lockout."""
import glob
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from src.auth.passwords import check_password, hash_password, new_one_time_password
from src.auth.service import AuthError, enrol, sign_in
from src.auth.totp import STEP_SECONDS, code_at, new_secret, step_for, verify

RFC_SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"  # the ASCII key 12345678901234567890 from RFC 6238
NOW = datetime(2026, 11, 16, 12, 0, 0, tzinfo=UTC)


# ---- Task 1: one-time codes ------------------------------------------------------------------


def test_the_rfc_6238_test_vector_for_time_59_seconds():
    assert code_at(RFC_SECRET, step_for(59)) == "287082"


def test_a_new_secret_is_random_base32_that_works():
    a, b = new_secret(), new_secret()
    assert a != b and len(a) == 32 and code_at(a, 1).isdigit()


def test_verify_accepts_the_current_step_and_one_either_side_but_not_two():
    now = 1_700_000_000.0
    step = step_for(now)
    for s in (step - 1, step, step + 1):
        assert verify(RFC_SECRET, code_at(RFC_SECRET, s), now, None) == s
    assert verify(RFC_SECRET, code_at(RFC_SECRET, step + 2), now, None) is None
    assert verify(RFC_SECRET, code_at(RFC_SECRET, step - 2), now, None) is None


def test_a_code_cannot_be_used_twice_or_after_a_later_one():
    now = 1_700_000_000.0
    step = step_for(now)
    code = code_at(RFC_SECRET, step)
    assert verify(RFC_SECRET, code, now, step) is None  # replay of the same step
    assert verify(RFC_SECRET, code_at(RFC_SECRET, step - 1), now, step) is None  # an older step after a newer one


@pytest.mark.parametrize("bad", ["", "12345", "1234567", "abcdef", "12 456", None, 123456, "１２３４５６"])
def test_malformed_codes_are_refused_without_raising(bad):
    assert verify(RFC_SECRET, bad, 1_700_000_000.0, None) is None


def test_the_step_length_is_thirty_seconds():
    assert STEP_SECONDS == 30 and step_for(59) == 1 and step_for(60) == 2


# ---- Task 2: passwords -----------------------------------------------------------------------


def test_the_same_password_hashes_differently_each_time_and_checks():
    h1, s1 = hash_password("correct horse")
    h2, s2 = hash_password("correct horse")
    assert (h1, s1) != (h2, s2) and "correct horse" not in h1 + s1
    assert check_password("correct horse", h1, s1) is True


@pytest.mark.parametrize("attempt", ["", "correct hors", "CORRECT HORSE", "correct horse ", None])
def test_a_wrong_or_empty_password_does_not_check(attempt):
    h, s = hash_password("correct horse")
    assert check_password(attempt, h, s) is False


def test_the_placeholder_hash_in_the_seed_never_checks():
    assert check_password("anything", "not-a-real-hash", "not-a-real-salt") is False


def test_one_time_passwords_are_long_and_different():
    a, b = new_one_time_password(), new_one_time_password()
    assert a != b and len(a) >= 16


# ---- Task 3: signing in ----------------------------------------------------------------------


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "auth.sqlite")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    for path in sorted(glob.glob("migrations/*.sql")):
        c.executescript(Path(path).read_text(encoding="utf-8"))
    c.executescript(Path("seed/iteration-1.sql").read_text(encoding="utf-8"))
    yield c
    c.close()


def events(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM auth_events ORDER BY id")]


def code_now(secret, now):
    return code_at(secret, step_for(now.timestamp()))


@pytest.mark.covers("FR-AUTH-01-AC1")
def test_the_right_password_and_the_right_code_sign_in_and_are_logged(conn):
    account = enrol(conn, "ana", "dispatcher", now=NOW)
    who = sign_in(conn, "ana", account["password"], code_now(account["totp_secret"], NOW), now=NOW)
    assert who == conn.execute("SELECT id FROM dispatcher_accounts WHERE username = 'ana'").fetchone()[0]
    assert [(e["kind"], e["ok"]) for e in events(conn)] == [("enrolled", 1), ("sign_in", 1)]


def test_enrolling_turns_the_seeded_demo_account_into_a_real_one(conn):
    account = enrol(conn, "demo-dispatcher", "dispatcher", now=NOW)
    assert conn.execute("SELECT COUNT(*) FROM dispatcher_accounts WHERE username = 'demo-dispatcher'").fetchone()[0] == 1
    assert sign_in(conn, "demo-dispatcher", account["password"], code_now(account["totp_secret"], NOW), now=NOW) == 1


@pytest.mark.covers("FR-AUTH-01-AC1")
def test_a_right_password_with_a_wrong_code_is_refused_and_logged(conn):
    account = enrol(conn, "ana", "dispatcher", now=NOW)
    with pytest.raises(AuthError) as exc:
        sign_in(conn, "ana", account["password"], "000000", now=NOW)
    assert exc.value.code == "SIGN_IN_FAILED"
    assert events(conn)[-1]["ok"] == 0


def test_the_same_code_cannot_sign_in_twice(conn):
    account = enrol(conn, "ana", "dispatcher", now=NOW)
    code = code_now(account["totp_secret"], NOW)
    sign_in(conn, "ana", account["password"], code, now=NOW)
    with pytest.raises(AuthError):
        sign_in(conn, "ana", account["password"], code, now=NOW + timedelta(seconds=5))


def test_a_wrong_password_with_the_right_code_is_refused(conn):
    account = enrol(conn, "ana", "dispatcher", now=NOW)
    with pytest.raises(AuthError):
        sign_in(conn, "ana", "not the password", code_now(account["totp_secret"], NOW), now=NOW)


def test_an_unknown_user_gets_exactly_the_same_error(conn):
    enrol(conn, "ana", "dispatcher", now=NOW)
    with pytest.raises(AuthError) as unknown:
        sign_in(conn, "nobody", "x", "123456", now=NOW)
    with pytest.raises(AuthError) as wrong:
        sign_in(conn, "ana", "bad", "123456", now=NOW)
    assert (unknown.value.code, str(unknown.value)) == (wrong.value.code, str(wrong.value))


def test_five_failures_lock_the_account_for_five_minutes_even_for_the_right_credentials(conn):
    account = enrol(conn, "ana", "dispatcher", now=NOW)
    for _ in range(5):
        with pytest.raises(AuthError):
            sign_in(conn, "ana", "bad", "000000", now=NOW)
    good = code_now(account["totp_secret"], NOW)
    with pytest.raises(AuthError) as exc:
        sign_in(conn, "ana", account["password"], good, now=NOW + timedelta(seconds=10))
    assert exc.value.code == "SIGN_IN_FAILED"  # the same error: a lock is not announced
    later = NOW + timedelta(seconds=301)
    assert sign_in(conn, "ana", account["password"], code_now(account["totp_secret"], later), now=later)


def test_a_success_resets_the_failure_count(conn):
    account = enrol(conn, "ana", "dispatcher", now=NOW)
    for _ in range(4):
        with pytest.raises(AuthError):
            sign_in(conn, "ana", "bad", "000000", now=NOW)
    sign_in(conn, "ana", account["password"], code_now(account["totp_secret"], NOW), now=NOW)
    assert conn.execute("SELECT failed_attempts FROM dispatcher_accounts WHERE username = 'ana'").fetchone()[0] == 0


def test_neither_the_password_nor_the_code_appears_in_the_event_log(conn):
    account = enrol(conn, "ana", "dispatcher", now=NOW)
    code = code_now(account["totp_secret"], NOW)
    sign_in(conn, "ana", account["password"], code, now=NOW)
    with pytest.raises(AuthError):
        sign_in(conn, "ana", "hunter2-secret", "654321", now=NOW + timedelta(seconds=60))
    dump = str(events(conn)) + str(conn.execute("SELECT password_hash, password_salt FROM dispatcher_accounts").fetchall())
    assert account["password"] not in dump and "hunter2-secret" not in dump and "654321" not in dump


def test_an_observer_can_sign_in_but_keeps_the_observer_role(conn):
    account = enrol(conn, "watcher", "observer", now=NOW)
    who = sign_in(conn, "watcher", account["password"], code_now(account["totp_secret"], NOW), now=NOW)
    assert conn.execute("SELECT role FROM dispatcher_accounts WHERE id = ?", (who,)).fetchone()[0] == "observer"


def test_the_event_log_cannot_be_edited(conn):
    enrol(conn, "ana", "dispatcher", now=NOW)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        conn.execute("UPDATE auth_events SET ok = 0")


def test_enrolling_with_a_bad_role_or_empty_name_is_refused(conn):
    for name, role in (("", "dispatcher"), ("ana", "root"), ("  ", "admin")):
        with pytest.raises(ValueError):
            enrol(conn, name, role, now=NOW)
