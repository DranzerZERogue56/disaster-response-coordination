"""Password hashing (docs/password-hashing-audit.md): Argon2id, self-describing, old scrypt hashes upgraded at sign-in."""
import glob
import hashlib
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.auth.passwords import MAX_PASSWORD_CHARS, check_password, hash_password, needs_rehash
from src.auth.service import enrol, sign_in
from src.auth.totp import code_at, step_for

NOW = datetime(2026, 11, 18, 12, 0, 0, tzinfo=UTC)


def legacy_scrypt(password):
    salt = b"\x01" * 16
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32).hex(), salt.hex()


@pytest.mark.defect("DEF-040")
def test_a_new_hash_is_argon2id_with_the_owasp_settings():
    stored, _ = hash_password("correct horse battery staple")
    assert stored.startswith("$argon2id$v=19$m=19456,t=2,p=1$")
    assert "correct horse" not in stored


@pytest.mark.defect("DEF-040")
def test_the_same_password_hashed_twice_gives_different_hashes_with_different_salts():
    first, _ = hash_password("same password")
    second, _ = hash_password("same password")
    assert first != second and first.split("$")[4] != second.split("$")[4]


@pytest.mark.defect("DEF-040")
def test_the_right_password_verifies_and_wrong_ones_do_not():
    stored, salt = hash_password("right one")
    assert check_password("right one", stored, salt)
    assert not check_password("wrong one", stored, salt)
    assert not check_password("", stored, salt)
    assert not check_password(None, stored, salt)


def test_the_whole_password_counts_there_is_no_72_byte_truncation():
    stored, salt = hash_password("a" * 72 + "x")
    assert not check_password("a" * 72 + "y", stored, salt)
    assert check_password("a" * 72 + "x", stored, salt)


def test_a_password_with_a_nul_byte_or_unicode_round_trips():
    for password in ["ab\x00cd", "pässwörd-日本語-🔒"]:
        stored, salt = hash_password(password)
        assert check_password(password, stored, salt)
    stored, salt = hash_password("ab\x00cd")
    assert not check_password("ab", stored, salt)


@pytest.mark.defect("DEF-040")
def test_a_very_long_password_is_refused_not_hashed():
    stored, salt = hash_password("short")
    assert not check_password("x" * (MAX_PASSWORD_CHARS + 1), stored, salt)
    with pytest.raises(ValueError):
        hash_password("x" * (MAX_PASSWORD_CHARS + 1))


def test_malformed_stored_values_are_simply_false():
    for bad in ["", "not a hash", "$argon2id$garbage", "zz"]:
        assert check_password("anything", bad, "") is False


@pytest.mark.defect("DEF-040")
def test_an_old_scrypt_hash_still_verifies_and_is_marked_for_upgrade():
    stored, salt = legacy_scrypt("old password")
    assert check_password("old password", stored, salt)
    assert not check_password("other", stored, salt)
    assert needs_rehash(stored)
    assert not needs_rehash(hash_password("new")[0])


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "a.sqlite")
    c.row_factory = sqlite3.Row
    for path in sorted(glob.glob("migrations/*.sql")):
        c.executescript(Path(path).read_text(encoding="utf-8"))
    c.executescript(Path("seed/iteration-1.sql").read_text(encoding="utf-8"))
    return c


@pytest.mark.defect("DEF-040")
def test_enrolment_stores_an_argon2id_hash(conn):
    enrol(conn, "new-dispatcher", "dispatcher", NOW)
    stored = conn.execute("SELECT password_hash FROM dispatcher_accounts WHERE username = 'new-dispatcher'").fetchone()[0]
    assert stored.startswith("$argon2id$")


@pytest.mark.defect("DEF-040")
def test_signing_in_with_an_old_scrypt_hash_upgrades_it_to_argon2id(conn):
    account = enrol(conn, "veteran", "dispatcher", NOW)
    old_hash, old_salt = legacy_scrypt(account["password"])
    conn.execute("UPDATE dispatcher_accounts SET password_hash = ?, password_salt = ? WHERE username = 'veteran'", (old_hash, old_salt))
    conn.commit()
    code = code_at(account["totp_secret"], step_for(NOW.timestamp()))
    assert sign_in(conn, "veteran", account["password"], code, NOW)
    stored = conn.execute("SELECT password_hash FROM dispatcher_accounts WHERE username = 'veteran'").fetchone()[0]
    assert stored.startswith("$argon2id$")
    later = datetime(2026, 11, 18, 12, 5, 0, tzinfo=UTC)
    assert sign_in(conn, "veteran", account["password"], code_at(account["totp_secret"], step_for(later.timestamp())), later)
