# ADR 0009 — Move to PostgreSQL behind a data-access layer (MongoDB evaluated, not chosen)

- **Status:** Accepted as a direction (Ben, 2026-11-18); the migration itself is not scheduled (backlog B-15). It supersedes the "SQLite for v1" part of ADR 0002 only once the migration is done.
- **Date:** 2026-11-18
- **Decider:** Dranzer Rogue
- **Requirements affected:** NFR-PRIV-01, NFR-MNT-01, NFR-SEC-01, FR-RES-01, FR-RES-03, FR-AUDIT-01, FR-AUDIT-02
- **Related ADRs:** 0002 (the original data-store choice), 0008 (the sign-in)

## Context
The project runs on SQLite: one file, no server (ADR 0002). Ben's goal for the next phase is a real multi-user deployment: several dispatchers and stations at once. SQLite allows one writer at a time and has no network access control, so that is where it stops being enough. Ben first proposed MongoDB with an API in front of it and input filtering against injection. An audit on 2026-11-18 (`docs/superpowers/plans/2026-11-18-database-options.md`) found: 113 SQL calls in 22 files, every user value already passed as a bound parameter, one reviewed SQL string built from constants (the purge job), and 11 triggers, 39 CHECK rules and 36 foreign keys that enforce the safety rules inside the database.

## Options considered
| Option | For | Against |
|---|---|---|
| Stay on SQLite | zero setup; the clean-machine run takes about 85 s | one writer; no network access control; not a multi-user deployment |
| **PostgreSQL** | keeps relational integrity, triggers, constraints and transactions (the rules that make a unit impossible to double-book); real multi-user concurrency; role-based access | needs a database server (affects the 5-minute clean-clone target); a multi-day port of 22 files and 109 test files |
| MongoDB | flexible documents; TTL indexes make the 24-hour purge trivial | no foreign keys; no triggers in the Community edition, so the safety rules become application code that any other writer can skip; multi-document transactions need a replica set; needs a server too; nothing here is safer against injection |
| A separate network "database API" service | one controlled entry point | an extra process and an extra failure mode (slow, down, rate-limited, changed) for one process on one machine |

## Decision
1. **Target database: PostgreSQL**, chosen for the multi-user goal because it keeps the database-enforced safety rules.
2. **Introduce a data-access layer first.** SQL moves behind repository classes that return plain Python values. The pilot is `src/data/units_repo.py` (every statement on the `units` table); the unit registry service now calls it, and the existing tests pass unchanged. A test (`tests/unit/test_architecture_boundaries.py`) fails the build if the registry service touches `units` directly again, and if any SQL in `src/` is built from variables except the one reviewed purge line.
3. **The migration is staged after Milestone 13** and gets its own change request (it changes the stack); see backlog B-15.
4. **MongoDB is not chosen.** Reason: it would turn database-enforced rules into code that the application must remember, and it adds a server prerequisite without adding injection safety.

## Consequences a reader would notice
- Today the database is still SQLite; the repository is the first visible step.
- Injection safety does not come from the database brand: it comes from bound parameters (already used everywhere) plus allow-list validation at the web boundary (backlog B-16).
- The architecture section 0 "surprise" (the safety rules live in the database as triggers) stays true after the move, because PostgreSQL has triggers and constraints.
- The clean-machine prerequisite list will grow by one server (or a container) at migration time; NFR-MNT-01 (under 5 minutes) must be re-measured then.
