# Password hashing audit (2026-11-18)

Facts are from reading `src/auth/passwords.py` and `src/auth/service.py` and from timings on this laptop. **Recommendation** marks my opinion.

## Before

| Concern | Finding |
|---|---|
| Weak or fast algorithms (MD5, SHA-1) | None for passwords. SHA-1 appears only inside TOTP (HMAC-SHA1, the standard for authenticator apps; HMAC use is not the broken use). |
| Missing or reused salts | Fine: 16 random bytes per hash, new on every enrolment. |
| Computational effort | scrypt N=2^14, r=8, p=1: 0.043 s per hash here. OWASP's scrypt setting is N=2^17 (0.37 s here); its first choice is Argon2id. |
| Custom or nested schemes | None. |
| Quirks | The hash and salt were bare hex in two columns, the settings lived only in code (so raising them would break every stored hash), no re-hash at sign-in, no password length cap. Constant-time comparison and equal-time refusal of unknown users were already in place. |
| Real-world risk | Low: every password is system-generated (128 random bits), nobody chooses one, sign-in locks after 5 failures in 300 s and needs a second code. |

## Choice (Ben, 2026-11-18): Argon2id

| Option | Notes |
|---|---|
| scrypt N=2^17 | No new dependency; I recommended this. |
| **Argon2id** (chosen) | OWASP first choice. Adds `argon2-cffi` 25.1.0 (with `argon2-cffi-bindings` and `cffi`), hash-pinned in `requirements.txt`. |
| bcrypt | Reads only 72 bytes of a password and stops at a NUL byte; workarounds (pre-hashing) would create the nested scheme this review looks for. Not chosen. |

## After

- New hashes: Argon2id, `m=19456 KiB, t=2, p=1` (OWASP profile), random salt inside the encoded string `$argon2id$v=19$...`. About 0.02 s per hash here (the memory cost, not the time, is the defence).
- Passwords of 1 to 1,024 characters; longer values are refused before any hashing.
- Old scrypt hashes (hex hash plus hex salt) still verify, are flagged by `needs_rehash`, and are replaced with Argon2id at that account's next successful sign-in. A test proves it. The `password_salt` column is now an empty string for new hashes (it is `NOT NULL`, so it was not dropped).
- A malformed stored value still costs a comparable amount of time to refuse.
- Dependency note: three new packages enter the supply chain (installed with `--require-hashes`). `pip-audit` (backlog B-12) should cover them.

## Not done

- No pepper (a server-side secret mixed into the hash): it adds key management for little gain here. **Recommendation:** revisit with the database move.
- The Argon2 settings were not tuned on the target hardware. **Recommendation:** raise `memory_cost` if sign-in stays under about 0.5 s on the deployment machine; `needs_rehash` upgrades existing hashes automatically.
- No change to TOTP (SHA-1 is what authenticator apps support).
