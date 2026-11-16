# Two-Factor Dispatcher Login Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (native, one session). Steps use checkbox syntax.

**Goal:** A dispatcher signs in with a password plus a six-digit code from an authenticator app on their own phone (works offline, no cloud), and every action that changes anything is refused without that session.

**Architecture:** A new `src/auth/` package (pure functions: TOTP, password hashing, login steps, lockout), one new migration (columns on `dispatcher_accounts`, an append-only `auth_events` table), and a gate in the Flask app (`before_request`) that is on whenever `AUTH_ENFORCED=1`. `script/start` sets it to 1; the existing 615 tests leave it unset and so are unchanged. The existing `stub_dispatcher_id(conn)` calls become one helper that returns the signed-in account when enforcement is on.

**Tech Stack:** Python standard library only (`hmac`, `hashlib.scrypt`, `secrets`, `struct`, `base64`), Flask sessions (signed cookie), SQLite. No new dependency.

**Spec:** `docs/backlog.md` B-07 (Ben's requirement statement and the proposed acceptance criteria), FR-AUTH-01 (currently a Should), DEF-018, `docs/security-review.md` S-01 to S-03.

## Hard cut-off (read this first)

It is about 22:45 and the deadline is 23:59. The release-candidate tag, push and CI check need about 25 minutes, so **work on a branch named `login` and stop building at 23:20 at the latest.** If the full test run is not green on the branch at 23:25, **the branch is not merged**, the tag goes on `main` as it stands, and the login stays on backlog B-07 with this plan done as far as it got. Main is never left half-built. A safety tag `v0.9.0-rc.1` on `main` is made first (see Task 0), so there is always a valid submission.

## Global Constraints

- Offline only: no outbound call, consistent with NFR-SEC-01 (the only network module stays `ollama_client.py`).
- No credential, token or key committed (NFR-SEC-04): secrets are generated at enrolment and printed once; the scan must stay at 0 matches.
- Passwords are never stored or logged in plain form: `hashlib.scrypt` with a per-account random salt; compare with `hmac.compare_digest`.
- A one-time code is accepted once only (replay refused) and only within one 30-second step either side of now.
- The enforcement default must not change the 615 existing tests: the gate is off unless `AUTH_ENFORCED=1`.
- Roles stay `admin`, `dispatcher`, `observer`; an `observer` can sign in and read but cannot act.
- Plain HTTP on 127.0.0.1 for now (HTTPS is CR-013, deferred): the session cookie is `HttpOnly` and `SameSite=Strict`; `Secure` is set when the request is HTTPS.
- Ben writes any change to requirement text (FR-AUTH-01); this plan changes code and the backlog only.

## Review Focus

1. **A correct password with a wrong, expired or reused code** must be refused and logged, never "partly" signed in. (Task 3 test.)
2. **A session cookie from before a restart or after logout** must not work. (Task 4 test.)
3. **A POST from another web page** (no CSRF token) must be refused even with a valid session. (Task 4 test.)
4. **An observer** with a valid session must be refused every action (the existing role checks must now see a real account id). (Task 4 test.)
5. **Guessing:** five wrong attempts for one username lock that username for five minutes, and the lock does not reveal whether the username exists. (Task 3 test.)

## File Structure

| File | Responsibility |
|---|---|
| `src/auth/totp.py` (new) | RFC 6238 one-time codes: `new_secret()`, `code_at(secret, step)`, `verify(secret, code, now, last_used_step) -> int | None` |
| `src/auth/passwords.py` (new) | `hash_password(password) -> (hash_hex, salt_hex)`, `check_password(password, hash_hex, salt_hex) -> bool`, `new_one_time_password() -> str` |
| `src/auth/service.py` (new) | `enrol(conn, username, role, now=None) -> dict`, `sign_in(conn, username, password, code, now=None) -> int`, `AuthError(code)`, lockout, `auth_events` writes |
| `migrations/0009-two-factor-login.sql` (new) | `dispatcher_accounts` gets `totp_secret`, `totp_last_step`, `failed_attempts`, `locked_until`; new append-only `auth_events` |
| `src/web_ui/auth_gate.py` (new) | blueprint with `GET/POST /login`, `POST /logout`; `install_gate(app)` (`before_request`: session, CSRF, open routes); `current_dispatcher_id(conn)` |
| `src/web_ui/templates/login.html` (new) | one labelled form: username, password, six-digit code |
| `src/web_ui/app.py`, `src/web_ui/dispatcher.py` (modify) | call `install_gate`; replace every `stub_dispatcher_id(conn)` call with `current_dispatcher_id(conn)`; add the hidden `csrf_token` to each form |
| `tools/enrol_dispatcher.py` (new) | prints the one-time password and the authenticator setup key once |
| `script/start`, `.env.example` (modify) | `AUTH_ENFORCED=1` by default for a real run |

## Routes that stay open when enforcement is on (decision Q-A for Ben)

`GET /healthz`, `GET/POST /login`, static files, `POST /reports` (field agents submit incidents; they have no dispatcher account) and `POST /nodes/<id>/heartbeat` (node processes). Everything else needs a session; every `POST` also needs the CSRF token. These two open routes are findings S-03 and the intake note and stay recorded.

---

### Task 0: Safety tag first (about 5 minutes, on `main`, only with Ben's go-ahead)

- [ ] Commit Ben's finished security-review and CR edits on `main`; run the final `tools/write_test_results.py`; run `tools/clean_machine_test.py`; create the annotated tag `v0.9.0-rc.1`; push main and the tag; confirm CI is green.
- [ ] `git switch -c login` and build everything below there.

### Task 1: One-time codes

**Files:** Create `src/auth/__init__.py`, `src/auth/totp.py`; Test `tests/unit/test_totp.py`.
**Produces:** `new_secret() -> str` (20 random bytes, base32), `code_at(secret: str, step: int) -> str` (6 digits, SHA-1, RFC 6238), `verify(secret: str, code: str, now: float, last_used_step: int | None) -> int | None` (returns the step used, or None).

- [ ] **Step 1: Failing tests**, with the RFC 6238 test vector (secret `GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ`, step for time 59 gives `287082`), plus: `verify` accepts the current step and one step either side, refuses two steps away, refuses a code at or below `last_used_step` (replay), refuses non-digits and wrong length without raising.
- [ ] **Step 2:** run, expect import failure. **Step 3:** implement with `hmac`/`struct`/`base64`; compare with `hmac.compare_digest`. **Step 4:** run, expect pass. **Step 5:** commit.

### Task 2: Passwords, the migration and the enrolment tool

**Files:** Create `src/auth/passwords.py`, `migrations/0009-two-factor-login.sql`, `tools/enrol_dispatcher.py`; Test `tests/unit/test_passwords.py`, `tests/integration/test_database_rule.py` (add `auth_events_no_edit` to the trigger list).
**Produces:** `hash_password(password) -> (hash_hex, salt_hex)` (`scrypt`, n=2**14, r=8, p=1), `check_password(...) -> bool`, `new_one_time_password() -> str` (16 characters from `secrets`).

- [ ] **Step 1: Failing tests:** a hash differs per call (random salt); the right password checks, a wrong one and an empty one do not; the stored text never contains the password; the migration applies on the seeded database and `auth_events` refuses UPDATE and DELETE... (UPDATE only: the purge never touches it).
- [ ] **Step 2 to 4:** implement; the migration adds `totp_secret TEXT`, `totp_last_step INTEGER`, `failed_attempts INTEGER NOT NULL DEFAULT 0`, `locked_until TEXT` and `auth_events(id, at, username, kind, ok, detail)` with `kind IN ('sign_in','sign_out','locked','enrolled')` and an UPDATE-refusing trigger. The enrolment tool creates (or resets) an account, prints the one-time password and the setup key (and the `otpauth://` link) **once**, and stores only the hash and the secret.
- [ ] **Step 5:** commit.

### Task 3: Signing in

**Files:** Create `src/auth/service.py`; Test `tests/unit/test_auth_service.py`.
**Produces:** `sign_in(conn, username, password, code, now=None) -> int` (the account id) or raises `AuthError` with code `INVALID_CREDENTIALS` (the same message for an unknown user, a wrong password and a wrong code) or `LOCKED`.

- [ ] **Step 1: Failing tests** (Review Focus 1 and 5): right password and right code returns the id and writes a `sign_in` event; right password, wrong code is refused and counts as a failure; the same code twice is refused the second time; unknown username is refused with the identical error; five failures lock the username for 300 seconds even for the right credentials, and the lock expires; a success resets the counter; no event or error text contains the password or the code.
- [ ] **Step 2 to 4:** implement; check the password before the code but always do both, so timing and messages do not say which was wrong. **Step 5:** commit.

### Task 4: The gate, the pages and the forms

**Files:** Create `src/web_ui/auth_gate.py`, `src/web_ui/templates/login.html`; Modify `src/web_ui/app.py`, `src/web_ui/dispatcher.py`, `src/web_ui/templates/dispatcher.html`; Test `tests/integration/test_login_http.py`.
**Produces:** `install_gate(app)`, `current_dispatcher_id(conn) -> int` (the signed-in account when `AUTH_ENFORCED=1`, otherwise `stub_dispatcher_id(conn)`).

- [ ] **Step 1: Failing tests** with `AUTH_ENFORCED=1`: (a) every gated route answers a redirect to `/login` (pages) or HTTP 401 (JSON) with no session, and changes nothing; (b) `/healthz`, `POST /reports` and the heartbeat stay open; (c) a full sign-in through the real form with a code from `totp.code_at` reaches `/dispatcher`; (d) a POST with a valid session and no CSRF token is refused (Review Focus 3); (e) logout ends the session and the old cookie no longer works; a cookie signed by a different key is refused (Review Focus 2); (f) an `observer` signs in but approving is refused (Review Focus 4); (g) the login page is a labelled form (the accessibility tests still pass); (h) with `AUTH_ENFORCED` unset the whole existing suite is unchanged.
- [ ] **Step 2 to 4:** implement. Session: Flask signed cookie, key from `SESSION_SIGNER` (random per start, never written), `SameSite=Strict`, `HttpOnly`, 8 hours. CSRF: a random token per session, hidden field `csrf_token` in each form and header `X-CSRF-Token` for JSON; checked on every POST except `/login`. **Step 5:** commit.

### Task 5: Turn it on, prove it, record it

**Files:** Modify `script/start`, `.env.example`, `docs/defect-log.md`, `docs/security-review.md` (facts only), `docs/backlog.md`, `CHANGELOG.md`; Test `tests/acceptance/test_acceptance_criteria.py` (the strict-xfail `test_FR_AUTH_01_AC2_an_unauthenticated_caller_cannot_approve` now runs with enforcement on and passes; remove its xfail marker).

- [ ] **Step 1:** `script/start` exports `AUTH_ENFORCED="${AUTH_ENFORCED:-1}"`; `.env.example` documents `AUTH_ENFORCED`, `SESSION_SIGNER`; the README gets a "First sign-in" section (run the enrolment tool, scan the key into any authenticator app, including Duo Mobile's third-party account option).
- [ ] **Step 2:** log the change in `docs/defect-log.md` first (DEF-018 updates to Fixed with the commit; its regression test is the acceptance test above), then `tools/verify_regression.py`.
- [ ] **Step 3:** full `./script/test` (expect 615+ passed, only the intended xfail removed); `./script/lint`; `./script/secrets-check` (0 matches); the clean-machine check (the README's Run it steps must still reach a healthy app: `/healthz` is open).
- [ ] **Step 4:** merge `login` into `main` only if every check is green before 23:25; then re-tag as `v0.9.0-rc.2` (the rc.1 tag is never moved), push, confirm CI.

## Not in this plan (recorded as still open, B-07)

A trusted-device rule ("a private computer"), the station IP allow-list, a Duo cloud push, role-level powers beyond the existing three roles, a password-change page, QR-code display of the setup key (the key is typed into the app by hand), and HTTPS (CR-013).
