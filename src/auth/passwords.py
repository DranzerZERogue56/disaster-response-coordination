"""Password storage: Argon2id (OWASP settings: 19 MiB memory, 2 passes, 1 lane), compared in constant time by the library.
The encoded string carries its own algorithm, settings and random salt, so the settings can be raised later and old hashes
are upgraded when their owner next signs in. Hashes made before 2026-11-18 (salted scrypt, hex hash plus hex salt) still
verify and are marked for upgrade. The password itself is never stored or logged. See docs/password-hashing-audit.md."""
import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

MAX_PASSWORD_CHARS = 1024  # no real password is longer; stops a huge value being used to burn time
_ARGON2 = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
_LEGACY_N, _LEGACY_R, _LEGACY_P = 2**14, 8, 1


def _legacy_derive(password, salt):
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_LEGACY_N, r=_LEGACY_R, p=_LEGACY_P, dklen=32)


def hash_password(password):
    """(encoded hash, salt column). The salt lives inside the encoded string, so the separate column is empty."""
    if not isinstance(password, str) or not password or len(password) > MAX_PASSWORD_CHARS:
        raise ValueError(f"a password must be 1 to {MAX_PASSWORD_CHARS} characters")
    return _ARGON2.hash(password), ""


def needs_rehash(stored_hash):
    """True for an old scrypt hash or an Argon2 hash made with weaker settings than the current ones."""
    if not str(stored_hash).startswith("$argon2"):
        return True
    try:
        return _ARGON2.check_needs_rehash(stored_hash)
    except InvalidHashError:
        return True


def check_password(password, hash_value, salt_hex):
    """True only for the right password. Any malformed stored value (such as the seed's placeholder) is simply False."""
    if not isinstance(password, str) or not password or len(password) > MAX_PASSWORD_CHARS:
        return False
    if isinstance(hash_value, str) and hash_value.startswith("$argon2"):
        try:
            return _ARGON2.verify(hash_value, password)
        except (VerificationError, InvalidHashError):
            return False
    try:
        expected = bytes.fromhex(hash_value)
        salt = bytes.fromhex(salt_hex)
    except (ValueError, TypeError):
        _ARGON2.hash(password)  # spend similar time, so a malformed record is not faster to refuse
        return False
    return hmac.compare_digest(_legacy_derive(password, salt), expected)


def new_one_time_password():
    """A random first password, shown once at enrolment."""
    return secrets.token_urlsafe(16)
