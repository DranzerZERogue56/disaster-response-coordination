# ADR 0010 — Move to MongoDB behind a data-access layer (supersedes ADR 0009)

- **Status:** DRAFT for Ben to confirm. Decision given by Ben on 2026-11-18, after the PostgreSQL direction (ADR 0009) was recorded the same day. The migration itself is not scheduled (backlog B-17).
- **Date:** 2026-11-18
- **Decider:** Dranzer Rogue
- **Requirements affected:** NFR-PRIV-01, NFR-MNT-01, NFR-SEC-01, FR-RES-01, FR-RES-03, FR-AUDIT-01, FR-AUDIT-02
- **Related ADRs:** 0002, 0008, 0009 (superseded)

## Context
Same goal as ADR 0009: a multi-user deployment, which SQLite does not serve. The options analysis is `docs/superpowers/plans/2026-11-18-database-options.md`. Ben chose MongoDB over the PostgreSQL option the assistant had recommended.

## Trade-offs accepted (listed so the choice is made with them in view)
| Gives up | What replaces it |
|---|---|
| 11 triggers and 39 CHECK rules that stop a unit being double-booked, an override log being edited, and so on | application code in the repositories, `$jsonSchema` validators on collections, unique indexes, and one test per rule that fails first |
| 36 foreign keys | application checks; orphan checks in a scheduled test |
| Multi-statement atomicity for free | multi-document transactions, which need a replica set (a single-node replica set for development) |
| One file, no server | a server prerequisite (or container); NFR-MNT-01 must be re-measured |
| SQL injection class | NoSQL operator injection (`$where`, `$ne` keys) instead: see `docs/database-hardening.md` |

What MongoDB gives: flexible documents and TTL indexes for the 24-hour purge.

## Decision
1. Target database: MongoDB.
2. Keep the data-access layer from ADR 0009 point 2 (`src/data/`); the boundary test stays.
3. Rules that were triggers move into code and validators one at a time, each with a failing test first.
4. Hardening follows `docs/database-hardening.md`, and nothing is called secure until Ben has run each check.

## Consequences a reader would notice
- Today the database is still SQLite.
- The architecture section 0 "surprise" (safety rules enforced inside the database) changes: after the move they are enforced by validators, unique indexes and repository code. Update that section at migration time.
- Because the database no longer refuses a bad write on its own, every writer must go through the repositories.
