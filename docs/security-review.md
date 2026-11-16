# Security Review: v0.9.0-rc.1

> **STATUS: SCAFFOLD, NOT YET A REVIEW.** Under the Milestone 12 AI policy the claims, findings, dispositions and reasons in this file must be Ben's. The assistant ran the tools and recorded facts in `docs/security-review-facts.md` (observation ids F1.1 to F8.10, each with a file:line and a command to re-run). This file arranges those facts into the seven required areas. Every cell marked **Ben** is empty on purpose. A finding is "fixed" or "accepted with a reason"; there is no third state. Dependency advisory ids must be opened and verified by Ben at https://github.com/advisories or https://osv.dev/.
> **Date written / reviewer:** **Ben** (date) / Ben (Dranzer Rogue)

## The seven areas

| # | Area | What was checked and how to re-run it (facts) | Evidence (fact ids in `docs/security-review-facts.md`) | Result | Findings |
|---|---|---|---|---|---|
| 1 | Secrets | `./script/secrets-check` (0 matches in 259 tracked files); a scan of the added lines of `git log --all -p` against the same patterns (184 commits, 0 matches); `.env` is ignored, `.env.example` holds no secret; `BANNER_SIGNER` is a random per-start key | F1.1 to F1.8 | **Ben** | none recorded by the assistant |
| 2 | Input handling | 18 routes reviewed for what input each takes and how it is validated; the hostile-data family (`tests/data/hostile.json`, `tests/integration/test_data_families_http.py`); DEF-009 to DEF-012 and DEF-023 (non-object JSON bodies) fixed with regression tests; no request-size limit exists | F2.1 to F2.19 | **Ben** | S-05 |
| 3 | Authentication | No login, session or credential check exists; every acting route uses the seeded stand-in dispatcher (`stub_dispatcher_id`); the server binds to 127.0.0.1 only | F3.1 to F3.7 | **Ben** | S-01 |
| 4 | Authorization | Roles `admin`, `dispatcher`, `observer` are checked in the decide, override, reconciliation and recovery functions against the stand-in account; there is no per-record ownership; an observer id is refused (`NOT_A_DISPATCHER`); because the caller cannot name an account, role checks cannot be exercised through the routes | F4.1 to F4.x | **Ben** | S-01, S-03 |
| 5 | Transport | Plain HTTP on 127.0.0.1:8080; the model client talks plain HTTP to a server on this machine only; no CSRF token (a POST with a foreign `Origin` header approved a proposal in a test-client run); security headers were absent before DEF-031 and are now sent on every response | F5.1 to F5.6 | **Ben** | S-02, S-04, S-11 |
| 6 | Dependencies | `pip-audit -r requirements.txt`: no known vulnerabilities in the 16 pinned packages; `pip-audit` on the whole virtual environment: 5 advisories against `setuptools 65.5.0`, which is not in `requirements.txt` and is not imported by the repo | F6.1 to F6.4 | **Ben** | S-07 |
| 7 | Logging | Append-only tables (`dispatcher_overrides`, `override_follow_ups`, `tiebreak_log`, `reconciliation_log`, `node_alerts`, `unit_events`) and stderr prints are what is recorded; no personal data field exists; no `debug=True`; the 24-hour purge now runs hourly (DEF-030) but does not cover the node alert and notice tables | F7.1 to F7.16 | **Ben** | S-08, S-10 |

## Findings (one row per finding; every row ends fixed or accepted with a reason)

Severity uses the defect-log scale (S1 to S4). "Facts" are quoted from the fact sheet and the repo; everything in a **Ben** cell is yours to write.

| ID | Area | Facts | Options and cost (assistant, for reference) | Severity | Disposition (FIXED or ACCEPTED) | Reason |
|---|---|---|---|---|---|---|
| S-01 | 3, 4 | No login: anyone who can reach the server can approve or override, always as the stand-in dispatcher. DEF-018, open, logged S2. Bound to 127.0.0.1 only (F3.1 to F3.5) | build a login (sessions, hashed passwords, roles, a one-time demo password printed by the seed script: about 4 to 6 hours); or accept with the localhost bind. The exit criterion "zero open S1/S2" fails while this is open | **Ben** | **Ben** | **Ben** |
| S-02 | 5 | No CSRF protection; a POST with `Origin: http://evil.example` approved a proposal in a test-client run (F5.3). The console's docstring says the protection arrives with sign-in | token per form (depends on a session, so on S-01); or accept while there is no login | **Ben** | **Ben** | **Ben** |
| S-03 | 3, 4 | `POST /nodes/<id>/heartbeat` has no caller check of any kind (F2.12): any local process can keep a node "alive" or mark a silent one as responding | a shared secret per node; or accept while everything is local | **Ben** | **Ben** | **Ben** |
| S-04 | 5 | Plain HTTP only (F5.1) | **DEFERRED** by Ben: `docs/change-requests/CR-013-https-transport.md`, backlog B-11, about 2026-11-29 | **Ben** | ACCEPTED as a deferral per CR-013 (**Ben to confirm**) | **Ben** (his CR-013 rationale may be reused) |
| S-05 | 2 | No request-size cap (`MAX_CONTENT_LENGTH` unset, F2.19); DEF-019 (a 100,000-character location is accepted and stored) is logged Will not fix | set a cap (a few lines and a test, changes DEF-019); or keep Will not fix | **Ben** | **Ben** | **Ben** |
| S-06 | 8 | The model client's 60 s limit is applied to each socket read, not as one total deadline (F8.x), so a server that drips bytes could hold a report longer. The server is on this machine only | a thread-based total deadline; or accept | **Ben** | **Ben** | **Ben** |
| S-07 | 6 | Five advisories against `setuptools 65.5.0` in the virtual environment: PYSEC-2022-43012, PYSEC-2025-49, PYSEC-2026-1918, PYSEC-2026-3447, GHSA-xmj3-9gf7-h52w; the package is not in `requirements.txt` and is not imported (F6.2 to F6.4). `pip-audit` prints no descriptions | upgrade `setuptools` in the venv (it is installer tooling); or accept as not reachable | **Ben** | **Ben** | **Ben** |
| S-08 | 7 | `node_alerts` and `node_notices` are not in the purge list (`src/purge/job.py`); they hold node health and unit ids, not incident data (F7.5) | add them to the purge; or accept because they hold no incident data | **Ben** | **Ben** | **Ben** |
| S-09 | 5, 8 | A real model scored a barely informative report at exactly the auto-dispatch confidence of 75 (DEF-029) | answers from a real model now need 85 (`MODEL_AUTO_APPROVE_MIN`, never below 75) | S2 (logged) | FIXED: DEF-029, `b7030ae` | the log's reason; the 85 is a provisional number, **Ben to confirm** |
| S-10 | 7 | The 24-hour purge never ran by itself (DEF-030) | an hourly job started by `script/start` | S2 (logged) | FIXED: DEF-030, `3c4513b` | the log's reason |
| S-11 | 5 | No browser security headers were sent (DEF-031) | four headers on every response | S3 (logged) | FIXED: DEF-031, `3c4513b` | the log's reason |

## Dependency findings

| Advisory id | Package and installed version | Fixed in | Verified by Ben at osv.dev / GitHub advisories? | Reachability judgment (Ben) |
|---|---|---|---|---|
| PYSEC-2022-43012 | setuptools 65.5.0 | 65.5.1 | **Ben** (link: https://osv.dev/PYSEC-2022-43012) | **Ben** |
| PYSEC-2025-49 | setuptools 65.5.0 | 78.1.1 | **Ben** (https://osv.dev/PYSEC-2025-49) | **Ben** |
| PYSEC-2026-1918 | setuptools 65.5.0 | 70.0.0 | **Ben** (https://osv.dev/PYSEC-2026-1918) | **Ben** |
| PYSEC-2026-3447 | setuptools 65.5.0 | 83.0.0 | **Ben** (https://osv.dev/PYSEC-2026-3447) | **Ben** |
| GHSA-xmj3-9gf7-h52w | setuptools 65.5.0 | 84.1.0 | **Ben** (https://github.com/advisories/GHSA-xmj3-9gf7-h52w) | **Ben** |

`requirements.txt` itself (16 pinned packages) reported no known vulnerabilities.
