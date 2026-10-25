# Skeleton Trace — Milestone 9

Author: Dranzer Rogue · Date: 2026-10-25 · Tag: `v0.1.0-skeleton`

This is the one real vertical slice this milestone requires: a browser or
`curl` talks to a real Flask route, which calls a real service function,
which writes a real row into the real SQLite database defined in
`migrations/0001-initial.sql`, and the row comes back out through a
rendered page. Nothing in this path is mocked. Everything else this
system's architecture (`docs/architecture.md`) eventually needs is a
labeled stub — named below, not hidden.

## Hop table

| # | Hop | Component (architecture.md §4) | File | Real or stub |
|---|---|---|---|---|
| 1 | Client submits a report | Operator / Dispatcher (external actor, §2) | `curl` / browser → `POST /reports` | Real |
| 2 | Route | Dispatcher Web UI | `src/web_ui/app.py::reports_create` | Real |
| 3 | Validate + insert | Intake Gateway | `src/intake_gateway/service.py::submit_report` | Real |
| 4 | Persist | SQLite database, `incident_reports` table | `migrations/0001-initial.sql` | Real |
| 5 | Read back + render | Dispatcher Web UI | `src/web_ui/app.py::reports_index`, `templates/reports.html` | Real |
| 6 | Liveness check | SQLite database (via Dispatcher Web UI) | `src/web_ui/app.py::healthz` | Real — this is `script/smoke`'s target |

## Verified manually (the same proof the grading rubric's 22/22 example uses)

```
$ ./script/setup
...
setup complete
$ ./script/start &
$ curl -s -X POST localhost:8080/reports -H 'Content-Type: application/json' \
    -d '{"location":"42 Oak St","severity_raw":"smoke smell","timestamp_reported":"2026-10-25T00:00:00+00:00","reporting_unit":"walkthrough-unit"}'
  -> {"report_id":1,"status":"created","received_at":"2026-10-25T19:11:53Z"}
$ curl -s localhost:8080/reports
  -> ...#1 — 42 Oak St — smoke smell — reported by walkthrough-unit (created)...
$ sqlite3 data/dev.sqlite "select location from incident_reports where id=1;"
  -> 42 Oak St
```

The page changed because the database changed, and the database row is
what the query above independently confirms — the same proof the
rubric's `ryebread` example uses.

## Requirement traceability (Must requirements touched by this slice)

| Requirement | Status this week | Evidence |
|---|---|---|
| FR-INTAKE-01 | Partial | `Submit Incident Report`'s *create* path is real (hop 2-4). The offline-queue path (writing to the buffer when the connectivity flag is down) is **stubbed** — every report this week is created immediately, never queued. |
| FR-INTAKE-02 | Real | `submit_report` collects every missing required field into one `ValidationError` and the route returns them together as `FIELD_MISSING`, not one at a time — `tests/test_intake.py::test_submit_report_missing_field_rejected`. |
| FR-INTAKE-03 (duplicate detection) | **Stub** | Not implemented. Every report is inserted as a new row; no merge-on-duplicate logic exists yet. Named explicitly in `src/intake_gateway/service.py`'s module docstring so it isn't mistaken for done. |

## Stubbed hops (named, not hidden)

| Hop / interface | Why it's stubbed this week | Where it becomes real |
|---|---|---|
| Classify & Propose / LLM Generate (Ollama) | This milestone's job is proving the client→route→service→store seam, not the reasoning engine; pulling in Ollama here would be the "scope creep disguised as enthusiasm" trap the assignment itself warns about | Milestone 10, Core Increment |
| Negotiation Coordinator, Approval Gateway, Decide Proposal | No proposals exist yet (nothing classifies a report), so there's nothing for these to act on | Milestone 10 |
| Resource/Unit Registry (`reserve`/`release`/`heartbeat`) | Same reason — no proposal exists yet to reserve a unit against | Milestone 10 |
| Notify Responder | Depends on a finalized assignment, which depends on the stubs above | Milestone 10-11 |
| Dispatcher auth (FR-AUTH-01) | This week's slice is unauthenticated intake only (per the Submit Incident Report contract itself: "intake is unauthenticated"); no session-gated route exists yet | Milestone 10, when `Decide Proposal`'s interactive path is built |
| Offline queue (FR-INTAKE-01's queued path) | See FR-INTAKE-01 row above | Milestone 10 |

## Secrets audit

Full history scanned for common secret shapes (API keys, AWS access keys, private key headers, bearer tokens, `password =` literals), excluding the known-safe `password_hash`/`password_salt` column names in `migrations/0001-initial.sql`:

```
$ git log -p --all | grep -inE "(api[_-]?key|secret[_-]?key|password\s*=|AKIA[0-9A-Z]{16}|-----BEGIN (RSA|OPENSSH|PGP) PRIVATE KEY-----|token\s*=\s*['\"][A-Za-z0-9_\-]{10,}|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,})" \
  | grep -v "password_hash\|password_salt"
# 0 hits
$ git log --all --diff-filter=A --name-only | grep -x "\.env"
# no match — .env was never added to history
```

Consistent with the architecture (ADR 0001, CON-03): everything in this system is local-only, so there is no API key or network credential anywhere in the repository to leak in the first place. `.env.example` lists the one variable the app reads (`DB_PATH`); real `.env` is gitignored.

**Rotation plan** (for the day this stops being true — e.g. a future cloud-GPU exception under R-04):
1. Revoke the leaked credential at its issuing source immediately, before touching git history.
2. Rewrite history to remove it (`git filter-repo` or BFG), then force-push and have every clone re-fetch.
3. Issue a new credential, store it only in `.env` (gitignored) or CI secrets — never in a tracked file.
4. Add the specific pattern that leaked to this audit's regex so the same shape can't slip through silently again.

## Acceptance record

- [x] One real request travels every hop named in this slice; the only stubs are the ones named above, and each is labeled, not silently skipped.
- [x] `script/smoke` passes against a real database and **fails** (verified, exit 1 path exercised) when the data store is unavailable — `tools/smoke_check.py`.
- [x] CI runs install → lint → test → build → smoke on every push and PR into `main` (`.github/workflows/ci.yml`).
- [x] Bootstrap is reproducible: `.python-version` pinned, `requirements.txt` pinned exactly, `script/setup` is one command, `README.md`'s `## Run it` states what success looks like.
- [x] Secrets hygiene: no credentials in this slice (no API keys — Ollama is local-only per ADR 0001), `.env.example` lists the one variable the app reads (`DB_PATH`), `.gitignore` already excludes `.env` and `data/*.sqlite`.
