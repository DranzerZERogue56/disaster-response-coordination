"""One-time codes from an authenticator app (RFC 6238, SHA-1, 6 digits, 30-second steps), standard library only.

The phone and the server share a secret; each computes the same six digits for the current 30-second step, so the code
proves the person holds the enrolled phone, with no network involved. A code is accepted once: `verify` is told the last
step already used and refuses that step and anything older.
"""
import base64
import hashlib
import hmac
import secrets
import struct

STEP_SECONDS = 30
DIGITS = 6


def new_secret():
    """A fresh shared secret: 20 random bytes as base32 (the form authenticator apps take)."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def step_for(timestamp):
    return int(timestamp // STEP_SECONDS)


def code_at(secret, step):
    key = base64.b32decode(secret.upper() + "=" * (-len(secret) % 8))
    digest = hmac.new(key, struct.pack(">Q", step), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 10**DIGITS
    return f"{value:0{DIGITS}d}"


def verify(secret, code, now, last_used_step):
    """The step the code belongs to if it is right for the previous, current or next step and has not been used, else None."""
    if not (isinstance(code, str) and len(code) == DIGITS and code.isascii() and code.isdigit()):
        return None
    current = step_for(now)
    for step in (current - 1, current, current + 1):
        if last_used_step is not None and step <= last_used_step:
            continue
        if hmac.compare_digest(code_at(secret, step), code):
            return step
    return None
