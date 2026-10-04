# ADR 0002 — Choose the data store

- **Status:** Accepted
- **Date:** 2026-09-27
- **Decider:** Dranzer Rogue
- **Requirements affected:** NFR-PRIV-01, NFR-MNT-01, FR-RES-03, FR-COORD-01, FR-AUDIT-01, FR-AUDIT-02
- **Related ADRs:** 0003 (the simulation framework decides how many agent processes can write concurrently, which is exactly the seam Spike SP-02 measures for this ADR)

## Context

Several requirements converge on the storage layer. NFR-PRIV-01 requires that incident-report data, including the decision and override audit trail, be purged 24 hours after receipt — a scheduled deletion job that has to run reliably every time. FR-AUDIT-01 and FR-AUDIT-02 require logging every agent proposal and every dispatcher override, which is straightforward write volume but needs to be queryable and purgeable together. FR-RES-03 requires reserving a unit "the moment it is proposed," which means the store has to handle a write happening at the same instant two competing agents might both be evaluating the same unit — this is the seam FR-COORD-01's tiebreak logic exists to resolve, and it puts real pressure on whatever the data store's concurrent-write behavior is.

This project is a solo, 240-hour capstone demo running on one person's hardware, not a production multi-tenant service, and NFR-MNT-01 requires a clean clone to reach a running app in under 5 minutes using only the README. That constraint punishes any option that needs a separate service installed and started before the app can even connect.

SQLite was already the working assumption for the auth/account tables since the Week 4 FR-AUTH-01 work, so it isn't a cold start. PostgreSQL was evaluated as the real alternative — a genuine option I could have chosen, not a strawman, since its concurrent-write model is a better technical fit for the FR-RES-03/FR-COORD-01 race than SQLite's single-writer lock.

## Options considered

| Option | Weighted score | The detail that decided it |
|---|---:|---|
| SQLite | 4.40 | No server process, fits the 5-minute clean-clone test, already in use for auth; the one real risk is single-writer contention under concurrent agent reservations |
| PostgreSQL | 3.30 | Better concurrent-write fit for the FR-RES-03 reservation race, but a separate service to install, run, and back up is a real cost against NFR-MNT-01 and solo operational burden |

## Decision

We will use **SQLite** as the data store for incident reports, the audit trail, dispatcher accounts, and unit-reservation state. It is the matrix's top-scored option (4.40 vs. 3.30), and it is also already the store in use for the auth tables, so this decision keeps one store for the whole project instead of splitting state across two engines.

## Decision override note

SQLite did not win only on preference-adjacent criteria — PostgreSQL actually scored higher on the one criterion (concurrent writes at the reservation moment) that the FR-RES-03/FR-COORD-01 seam most directly stresses. That seam is exactly why Spike SP-02 (`docs/spikes/SP-02-sqlite-write-contention-under-concurrent-mesa-agents.md`) is planned: to measure, rather than guess, whether SQLite's single-writer lock actually causes lost or delayed reservations under the number of concurrent agent processes this project will realistically run. If SP-02 shows unacceptable contention, this ADR gets superseded rather than edited.

## Consequences

**Positive**

- No separate service to install, configure, or keep running — fits NFR-MNT-01's 5-minute clean-clone target directly, and there is nothing new for a Week 14 reviewer to set up.
- Purge and delete (NFR-PRIV-01) is a single `DELETE ... WHERE` plus `VACUUM`, run by one scheduled job, against one file.
- One data store for the whole project (already used for auth since Week 4), instead of splitting operational surface across two engines.

**Negative**

- Single-writer lock is a real risk at the exact moment FR-RES-03 cares about most: two agents proposing the same unit near-simultaneously. If Spike SP-02 shows write contention causing missed or delayed reservations, the mitigation is either a serialization layer in the app (a queue in front of the write, budgeted at ~4 hours to build and test) or moving to PostgreSQL for the reservation table specifically (a bigger change, budgeted at ~8 hours including a new backup/restore runbook).
- No built-in replication or separate backup tooling beyond copying the file — acceptable for a solo capstone demo, but would need re-evaluation before any real multi-user deployment.

## Revisit trigger

Revisit this ADR if Spike SP-02 measures any lost or duplicated reservation across its concurrent-write test, or if the project ever needs more than 3 concurrent agent-writer processes (the current design assumption, based on the competing-team sizes discussed for the negotiation simulation).

## Verification

| Claim in this ADR | Source | Checked on |
|---|---|---|
| SQLite is public domain, no license restriction | https://sqlite.org/copyright.html | 2026-09-27 |

## Update — 2026-10-04

Spike SP-02 (`docs/spikes/SP-02-sqlite-write-contention-under-concurrent-mesa-agents.md`) ran against the real schema from `migrations/0001-initial.sql`: 20 trials, 3 concurrent OS processes racing to reserve the same unit each trial. Zero double-bookings, zero lost writes, max 0.026s per trial. The revisit trigger above — "any lost or duplicated reservation" — did not fire. This ADR's decision stands confirmed, not superseded; this note records the new evidence without editing the original Context/Decision/Consequences above, per this project's own ADR-immutability discipline.
