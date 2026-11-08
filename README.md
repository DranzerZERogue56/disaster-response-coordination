# Disaster Response Coordination

## What this is

A senior CS capstone project: you type a disaster scenario in plain
English, and the system works out which kinds of responders would be
needed (medics, firefighters, shelter/logistics crews, security), then
tries a handful of different team sizes against a simulated version of
that disaster on a map of real streets. Every team decides who goes
where the same way — responders negotiate directly with each other in
plain language, the way a real dispatcher radios instructions during an
emergency. Whichever team size handles it best — including recovering
well when a road closes, a unit breaks down, or a new wave of incidents
hits — gets written up as a suggested response plan a company or agency
could keep on file. Full architecture and design: [`PROJECT.md`](PROJECT.md).

## Who owns it

Solo capstone project, one semester, 240 hours total, graded per a
weekly-deliverable course schedule (see [`CALENDAR.md`](CALENDAR.md)).

## Run it

Prerequisite: Python 3.11 (pinned in `.python-version`).

```
./script/setup     # creates .venv, installs pinned deps, applies migrations
./script/start     # runs the walking skeleton on http://127.0.0.1:8080
```

**What success looks like:** `./script/setup` ends by printing `setup
complete` with no errors above it. After `./script/start`, `curl
localhost:8080/healthz` returns `{"status": "ok"}`, and
`curl localhost:8080/reports` renders a (possibly empty) list of incident
reports. Posting to `/reports` (see `docs/skeleton-trace.md` for the exact
command) adds a real row to `data/dev.sqlite` and it appears on that page
immediately.

Other verbs: `./script/lint`, `./script/test`, `./script/build`,
`./script/smoke` — the same four stages CI runs on every push.

## Run the tests

One command runs the whole suite (unit, integration and acceptance, with the 90% line-coverage gate), and it is the command CI runs:

```
./script/test
```

The test plan is `docs/test-plan.md`; the last full run is `docs/test-results.md`; the requirement-to-test matrix is `docs/traceability.csv` (rebuild it with `python tools/build_traceability.py` after a test run); defects are in `docs/defect-log.md`. The dispatcher console is at `http://127.0.0.1:8080/dispatcher` once the app is running. Test data: `./script/seed-test-data`.

## Current status

Concept and scope locked (Week 1), then pivoted in Week 2 away from an
earlier version that set out to prove one negotiation style beats
classical optimization with a live real-time map as the demo centerpiece
— this version instead focuses on trying different team sizes against a
scenario and producing a usable written plan, no live map. Weeks 1-8
(planning/design) are complete and baselined (`docs/baseline.md`).
Construction started Week 9: a real walking skeleton exists —
`POST /reports` -> Intake Gateway -> SQLite `incident_reports` -> a
rendered page, with CI running install/lint/test/build/smoke on every
push (see `docs/skeleton-trace.md` for what's real and what's still
stubbed). See `docs/charter.md` for capacity, non-goals, and the ranked
cut order if the schedule slips.

## How to navigate the docs

- [`PROJECT.md`](PROJECT.md) — architecture, tech stack, evaluation plan, team-size competition, report generation
- [`CALENDAR.md`](CALENDAR.md) — full 16-week schedule with weekly deliverables
- [`RISKS.md`](RISKS.md) — early draft risk register, **superseded by [`docs/risk-register.md`](docs/risk-register.md)**
- [`HARDWARE.md`](HARDWARE.md) — local GPU server build plan, phased by readiness week
- [`docs/charter.md`](docs/charter.md) — project charter (purpose, constraints, non-goals, risks, cut order)
- [`docs/requirements.md`](docs/requirements.md) — requirements specification, baselined Week 8
- [`docs/architecture.md`](docs/architecture.md) — technical specification
- [`docs/plan.md`](docs/plan.md) — work breakdown, schedule, burn-down, scope decision
- [`docs/risk-register.md`](docs/risk-register.md) — the current, scored risk register (10 risks)
- [`docs/baseline.md`](docs/baseline.md) — the Week 8 specification baseline and what's still open
- [`docs/review/`](docs/review/) — the Week 8 design review checklist and defect log
- [`docs/change-requests/`](docs/change-requests/) — change control, for anything touching the baseline from here
- [`CHANGELOG.md`](CHANGELOG.md) — specification changes since the baseline
- [`docs/ai-usage.md`](docs/ai-usage.md) — AI usage policy and dated log
- [`docs/hours-log.csv`](docs/hours-log.csv) — logged work sessions
- [`docs/definition-of-done.md`](docs/definition-of-done.md) — the checklist every work item must pass before it counts as Done
- [`docs/skeleton-trace.md`](docs/skeleton-trace.md) — Week 9 walking-skeleton hop table, traceability, and acceptance record
- [`docs/skeleton-memo.md`](docs/skeleton-memo.md) — Week 9 Hard-tier memo: stubs, re-estimate, build-failure policy, AI accounting
- `docs/adr/` — architecture decision records (Week 5+)
- `docs/` (site root) — static GitHub Pages progress dashboard, live at
  https://dranzerzerogue56.github.io/disaster-response-coordination/

## What's intentionally not here yet

- No real language model: Ollama is not wired in. A rules-based fake model stands in, behind a fallback chain whose
  primary and smaller slots are empty until it is. Two requirements that name the target GPU (FR-INFER-02,
  NFR-PERF-01) are therefore unverified on purpose.
- No login (FR-AUTH-01): the dispatcher console uses a seeded stand-in account (DEF-018).
- No real notification channel: "notify" records a row (DEF-017).
- No map output, no report generator, no Mesa simulation of team sizes yet.
- No finalized license — see `LICENSE` for the deferral status.

Built since the walking skeleton (Milestones 10 and 11): intake with an offline queue, classification and
proposals, the unit registry with its 4-minute clock, the human-approval safety rule, override, negotiation with
a logged tiebreak, reconciliation, the Scenario Reader (`python tools/play_scenario.py FILE --speed N`), node
heartbeats and alerts, the model fallback chain, the 24-hour purge, and a dispatcher console.

---

Detailed weekly build scope and the ranked drop-if-behind cut order live
in [`PROJECT.md`](PROJECT.md)'s "Scope discipline" section, not here —
this file stays a short orientation, not a duplicate of it.
