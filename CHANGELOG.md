## Specification changes since baseline v1.0

Baseline declared 2026-10-18 (`docs/baseline.md`). Every change request raised since is a row below, with its file under `docs/change-requests/`. A row marked "pending Ben" is a draft: the disposition is Ben's and has not been written.

| CR | Date | Change | Requirements | Hours | Decision |
|---|---|---|---|---:|---|
| CR-001 | 2026-11-01 | Database triggers: a unit is `assigned` only while its proposal is `approved`/`modified` (migration 0002) | FR-AGENT-03, NFR-SEC-02, FR-RES-01 | +0.5 | approved |
| CR-002 | 2026-11-01 | Override follow-ups become an append-only table; override rows can no longer be edited (migration 0003) | FR-RES-02, FR-AUDIT-02 | +0.5 | approved |
| CR-003 | 2026-11-05 | Acceptance criteria written for FR-ALERT-01, FR-AUDIT-01, FR-AUDIT-02, FR-SIM-01, FR-INFER-01, FR-INFER-02; "[X] seconds" set to 10 (FR-ALERT-01) and 5 (FR-INFER-02) | those six | +0.5 | approved |
| CR-004 | 2026-11-05 | Proposals record the input data the agent used (`agent_proposals.input_data`, final once written; migration 0004) | FR-AUDIT-01 | +0.5 | approved |
| CR-005 | 2026-11-05 | NFR-SEC-03: synthetic reports live in `tests/data/` and `seed/` (not `data/synthetic/`); check script `tools/check_synthetic.py` | NFR-SEC-03 | +0.5 | approved |
| CR-006 | 2026-11-05 | Tiebreak log (append-only, both richness scores) and human-escalation queue (migration 0006) | FR-COORD-01, FR-COORD-03 | +0.5 | approved |
| CR-007 | 2026-11-05 | Incident versions and an append-only reconciliation log (migration 0007) | FR-COORD-02 | +0.5 | approved |
| CR-008 | 2026-11-05 | Node-failure alerts and notices (migration 0005): flagged after 30 s silent, recovery only after a human confirms | FR-DEGRADE-01, NFR-REL-01 | +0.5 | approved |
| CR-009 | 2026-11-05 | Purge Job: units are reset not deleted, nodes untouched; success shape lists purged and reset tables (NFR-PRIV-01) | NFR-PRIV-01 | +0.25 | approved |
| CR-010 | 2026-11-05 | Unit status changes published to every other agent: events, inboxes with a cache for down nodes, warning notices (migration 0008) | FR-RES-03 | +0.75 | approved |
| CR-011 | 2026-11-11 | Ollama client as the primary model tier (kill switch `OLLAMA_ENABLED`) | FR-INFER-01, FR-INFER-02, FR-DEGRADE-02, FR-AGENT-04, NFR-SEC-01, NFR-PERF-01 | Ben to confirm | ACCEPT, with CR-013 (DEFER) and CR-014 (REJECT) carved out; Ben's notes of 2026-11-15 expanded by the assistant, Ben to rewrite and confirm (draft, `docs/change-requests/CR-011-ollama-client.md`) |
| CR-012 | 2026-11-15 | Retroactive record of the three Milestone 7 deferrals (FR-INTAKE-03, FR-INFER-03, FR-MAP-01: Should to Won't, decided 2026-10-10) | FR-INTAKE-03, FR-INFER-03, FR-MAP-01 | Ben to confirm | pending Ben (draft, `docs/change-requests/CR-012-record-of-milestone-7-deferrals.md`) |
| CR-013 | 2026-11-15 | Move the app and the model connection from HTTP to HTTPS: DEFER to the next build period (about 2026-11-29), backlog B-11 | NFR-SEC-01 (transport, security review area 5) | Ben to confirm | DEFER (Ben's notes expanded by the assistant, Ben to rewrite and confirm; `docs/change-requests/CR-013-https-transport.md`) |
| CR-014 | 2026-11-15 | Several or larger locally hosted models and the target-hardware work: REJECT in favour of one demo model (`qwen3:1.7b`) | FR-INFER-02, NFR-PERF-01 | Ben to confirm | REJECT (Ben's notes expanded by the assistant, Ben to rewrite and confirm; `docs/change-requests/CR-014-no-multi-model-or-target-hardware.md`) |

### The threshold rule — when a change needs a CR

Raise a change request (`docs/change-requests/CR-000-template.md`) if the change does any of these:

1. Adds, removes, or materially rewords a **Must** requirement.
2. Changes an **interface contract** or the **data model**.
3. Moves a **milestone date** or changes the total plan by more than **4 hours**.
4. Changes the **stack** — a new language, framework, database, or hosting provider.
5. Changes the **definition of done**.

Everything else — typos, clarifications that don't change meaning, formatting, added examples — is an ordinary commit with a clear message.

---

## Release changelog

Format: [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/). Ids in parentheses are requirements (FR-, NFR-), defects (DEF-, `docs/defect-log.md`) and change requests (CR-). Numbers come from `docs/test-results.md` and the defect log; nothing here is a claim the repo does not record.

History before this file's first release section: tag `milestone-3` (2026-09-13), tag `v0.1.0-skeleton` (2026-10-25, the walking skeleton), tag `iteration-1` (2026-11-01, Milestone 10: classify and propose, unit registry, decide proposal, notify responder, intake, override, web UI; migrations 0001 to 0003; CR-001, CR-002; defects DEF-001 to DEF-007 were found and fixed inside that tag). Everything below is after `iteration-1`.

## [Unreleased]

### Added
- `docs/backlog.md`: ten deferred or cut items B-01 to B-10, each with its source, estimate and acceptance criteria copied intact (proposed by the assistant; dispositions are Ben's) (CR-012, DEF-017, DEF-018, DEF-020).
- Draft change request CR-012, a retroactive record of the Milestone 7 deferrals (FR-INTAKE-03, FR-INFER-03, FR-MAP-01), and a Status line under each of those three requirements.

### Changed
- Decisions waiting on Ben: CR-011, CR-013 and CR-014 (drafted from Ben's notes) and CR-012 dispositions, to rewrite and confirm; the confidence bar of 85 for real-model answers (DEF-029), which is the assistant's provisional number.

## [0.9.0-rc.1] - 2026-11-15

Release candidate. Exit criteria are in `docs/rc-exit-criteria.md` (written 2026-11-11, results pending). At the last full run recorded in `docs/test-results.md` (commit `f2d477c`, 2026-11-08): 547 passed, 1 expected failure, line coverage 95.85%, verified-Must 29 of 31 (94%), regression proof 28 of 28. Later commits (DEF-029, the Ollama client) are not in that run.

### Added
- Purge Job: units are reset, not deleted; nodes untouched; the success answer lists purged and reset tables (NFR-PRIV-01, CR-009).
- Synthetic-data check `tools/check_synthetic.py`; synthetic reports live in `tests/data/` and `seed/` (NFR-SEC-03, CR-005).
- Clean-machine test that follows the README and times it (NFR-MNT-01).
- Acceptance criteria for FR-ALERT-01, FR-AUDIT-01, FR-AUDIT-02, FR-SIM-01, FR-INFER-01, FR-INFER-02; the "[X] seconds" placeholders set to 10 and 5 (FR-ALERT-01, FR-INFER-02, DEF-008, CR-003).
- Proposals keep a fixed snapshot of the input data the agent used (FR-AUDIT-01, DEF-014, CR-004, migration 0004).
- Negotiation and tiebreak: conflicts resolved against the registry by a defined richness score, an append-only tiebreak log, and a human-escalation queue (FR-COORD-01, FR-COORD-03, CR-006, migration 0006).
- Reconciliation: incident versions, newest-data-wins, and an append-only log of a human override (FR-COORD-02, CR-007, migration 0007).
- Scenario Reader: paced playback of a prewritten scenario file, a demo scenario and an operator command-line tool (FR-SIM-01).
- Heartbeats and alerts: a node silent for 30 s is flagged, a late recovery is marked, and recovery counts only after a human confirms; detection time measured with five killed node processes, worst case 20.98 s (FR-DEGRADE-01, NFR-REL-01, CR-008, migration 0005).
- Model fallback chain: six retries ten seconds apart, then escalation to a human (FR-DEGRADE-02).
- Modify action: approve with a different available unit, atomically, and notify the chosen unit (FR-AGENT-03-AC2).
- Dispatcher console at `/dispatcher`: native forms, visible focus, word-plus-symbol severity, with a written keyboard-only script for Ben's pass (NFR-ACC-01, NFR-ACC-02).
- Unit-status broadcast: every status change is published to every other agent node, cached for a silent node, with warning notices to its peers (FR-RES-03, DEF-016, CR-010, migration 0008).
- Console banners are signed so a link cannot display a forged message (NFR-ACC-01 console, DEF-028).
- Ollama client as the primary model tier: loopback hosts only, no redirects, no proxy, replies over 1 MB refused, a time cap per call (default 60 s), one retry on a wrong-shaped answer, and distinct errors for down, slow, busy and changed responses; kill switch `OLLAMA_ENABLED` (off or unset means the rules tier only) (FR-INFER-01, FR-INFER-02, FR-DEGRADE-02, FR-AGENT-04, NFR-SEC-01, NFR-PERF-01, CR-011 pending). Evidence: 24 client tests, 7 wiring tests, 14 chaos tests through the real intake route, and one real run against `qwen3:1.7b` on 2026-11-11.
- Test suite in `tests/unit`, `tests/integration`, `tests/acceptance`, `tests/data` (happy, boundary and hostile families, fixed seed 20261105), property-based tests P1 to P4 with Hypothesis, a 90% line-coverage gate in `./script/test`, and `docs/traceability.csv` built from `@pytest.mark.covers` markers (NFR-MNT-01, DEF-015).

### Changed
- Real-model answers need a confidence of at least 85 before automatic dispatch; the rules tier keeps the spec's 75. Adjustable with `MODEL_AUTO_APPROVE_MIN`, never below 75. The 85 is provisional (FR-AGENT-03, NFR-SEC-02, DEF-029).
- The no-network-library rule in the acceptance tests now exempts only `src/classify_propose/ollama_client.py`, and checks that it contains the loopback-only test (NFR-SEC-01, CR-011 pending).
- `docs/requirements-traceability.csv` is the Week-4 requirement-level file renamed; `docs/traceability.csv` is the criterion-level matrix (CR-003).
- Intake accepts only a JSON object whose text fields are non-blank strings (FR-INTAKE-02, DEF-009 to DEF-012).
- Approving a held proposal whose unit was lost now tries the alternatives before failing (FR-RES-01-AC2, DEF-013).

### Fixed
- Intake and routes: a JSON list or string body, or a list or object where text belongs, answered HTTP 500; whitespace-only text and numbers or booleans as text were accepted (FR-INTAKE-02, DEF-009, DEF-010, DEF-011, DEF-012). The same crash on four more routes (decision, override, follow-up, connectivity) (NFR-REL-01, DEF-023). An unknown console action returned a 404 with a redirect (NFR-REL-01, DEF-025).
- Approval: no second path when the held unit was lost (FR-RES-01-AC2, DEF-013).
- Audit: the proposal log lacked the input data (FR-AUDIT-01-AC1, DEF-014).
- Model answers: non-text reasoning and boolean confidence were accepted (FR-AGENT-01-AC2, DEF-015).
- Broadcast and negotiation: updates stranded for a node whose recovery was confirmed first, and false "could not be delivered" warnings for a node that had answered again (FR-RES-03-AC2, DEF-021, DEF-022); a tiebreak loser's replacement left with no unit and no escalation (FR-COORD-01-AC2, DEF-024); proposals ignoring the broadcast view (FR-RES-03-AC3, DEF-026); the tiebreak applied only to same-unit conflicts (FR-COORD-03-AC1, DEF-027); no broadcast to other agents at all (FR-RES-03-AC1 to AC3, DEF-016).
- Two Must requirements with a literal "[X] seconds" (FR-ALERT-01, FR-INFER-02, DEF-008).
- A real model could score a barely informative report at exactly 75 and dispatch with no human review (FR-AGENT-03, NFR-SEC-02, DEF-029).
- Every fixed defect above names a regression test that fails on the commit before the fix; `docs/regression-proof.md` records the check.

### Security
- The model client refuses any host but 127.0.0.1, localhost or ::1, follows no redirects, uses no proxy, and has a 1 MB reply cap (NFR-SEC-01, CR-011 pending).
- A real model's confidence can no longer authorize automatic dispatch on its own at 75 (NFR-SEC-02, DEF-029).
- A forged address banner can no longer show a false "approved" message in the console (DEF-028).
- Purge Job and synthetic-data check protect personal data handling (NFR-PRIV-01, NFR-SEC-03, CR-009, CR-005).
- Still open: there is no login (FR-AUTH-01, DEF-018); see the known issues below.

### Known issues in 0.9.0-rc.1
- DEF-017 (S3) - the software only writes a notification row; nothing is sent to a responder. Workaround: the dispatcher notifies the responder outside the software. Planned: backlog B-04.
- DEF-018 (S2) - there is no login; anyone who can reach the server can approve or override. Workaround: the app listens only on 127.0.0.1, and the demo says so aloud. Planned: backlog B-07 (the defect log says v1.0 must not ship like this).
- DEF-019 (S4) - a 100,000-character location is accepted and stored; no requirement sets a length limit. Workaround: none needed, it is stored safely and nothing crashes. Planned: Ben to confirm (the log says Will not fix this release, priority P4; revisit if a real feed shows long text).
- DEF-020 (S4) - a report stamped in the year 2099 is accepted and sorts last in the queue. Workaround: the dispatcher reads the report time on the page; the queue is oldest-first. Planned: backlog B-08 (needs Ben's decision on a margin).

