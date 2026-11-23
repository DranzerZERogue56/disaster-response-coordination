# ADR 0008 — Dispatcher sign-in: password plus a time-based code from the person's own phone

- **Status:** DRAFT for Ben to confirm (the choice is Ben's, made 2026-11-15; the assistant recorded it from the plan and the code).
- **Date:** 2026-11-15 (Ben here: I CONFIRM!)
- **Decider:** Dranzer Rogue
- **Requirements affected:** FR-AUTH-01, NFR-SEC-02; closes DEF-018 and security-review findings S-01 to S-03
- **Related ADRs:** 0002 (the sign-in data lives in the same database), 0010 (the data store direction)

## Context
Before release candidate 2 the dispatcher console had no sign-in: anyone who could reach the port could approve a unit (DEF-018, severity S2). Ben asked for a dispatcher sign-in with more than a password, and for it to work offline and without a cloud account, because the system runs on one machine and must not call external hosts (NFR-SEC-01).

## Options considered
| Option | For | Against |
|---|---|---|
| Password only | simplest | one stolen or guessed password is enough |
| **Password plus a time-based six-digit code (RFC 6238) from an authenticator app on the person's own phone** | works offline; no vendor account; standard apps accept it; second factor is something the person holds | the person needs a phone and a one-time setup |
| Hardware keys | strongest | needs hardware the team does not have |
| Email or SMS codes | familiar | needs outbound network and a provider; breaks NFR-SEC-01 |

## Decision
1. Sign-in needs the password and the current code. The code is checked within one 30-second step either side and **a code is accepted only once**.
2. Failures always show the same message; five failures lock the account for 300 seconds; every sign-in, failure, lock and enrolment is written to an append-only `auth_events` table.
3. Sessions are tracked on the server as well as in a signed cookie (`HttpOnly`, `SameSite=Strict`); every form carries a per-session forgery token.
4. Accounts are created with `python tools/enrol_dispatcher.py <username> [role]`, which prints a one-time password and a phone setup key once.
5. The sign-in is on when the app is started with `./script/start` (`AUTH_ENFORCED=1`) and off by default in tests and imports.
6. Password storage was salted scrypt and became Argon2id on 2026-11-18 (`docs/password-hashing-audit.md`, DEF-040); old hashes upgrade at the next sign-in.

## Consequences a reader would notice
- With the sign-in on, field reports, the scenario tool and node heartbeats over HTTP are refused (DEF-032); run with `AUTH_ENFORCED=0` for those demos. A shared service key for those callers is planned.
- A fresh install has an empty console, so `python tools/add_demo_proposal.py` puts one waiting proposal in front of it.
- HTTPS is deferred (CR-013); on plain `http://127.0.0.1` the cookie is not marked `Secure`.
- TOTP uses HMAC-SHA1 because authenticator apps require it; that is not the weak use of SHA-1.
