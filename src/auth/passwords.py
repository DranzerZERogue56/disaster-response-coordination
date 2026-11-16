"""Password storage: a salted scrypt hash, compared in constant time. The password itself is never stored or logged."""
import hashlib
import hmac
import secrets

N, R, P = 2**14, 8, 1


def _derive(password, salt):
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=N, r=R, p=P, dklen=32)


def hash_password(password):
    salt = secrets.token_bytes(16)
    return _derive(password, salt).hex(), salt.hex()


def check_password(password, hash_hex, salt_hex):
    """True only for the right password. Any malformed stored value (such as the seed's placeholder) is simply False."""
    if not isinstance(password, str) or password == "":
        return False
    try:
        expected = bytes.fromhex(hash_hex)
        salt = bytes.fromhex(salt_hex)
    except (ValueError, TypeError):
        _derive(password, b"\x00" * 16)  # spend the same time, so a bad record is not faster to refuse
        return False
    return hmac.compare_digest(_derive(password, salt), expected)


def new_one_time_password():
    """A random first password, shown once at enrolment."""
    return secrets.token_urlsafe(16)
