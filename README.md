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
- `docs/adr/` — architecture decision records (Week 5+)
- `docs/` (site root) — static GitHub Pages progress dashboard, live at
  https://dranzerzerogue56.github.io/disaster-response-coordination/

## What's intentionally not here yet

- Most application code — Week 9 built only the one walking-skeleton
  vertical slice (incident intake). Mesa, the negotiation engine,
  classification, and the dispatcher web console's real decision flow
  start in Milestone 10 (see `docs/skeleton-trace.md`'s stub list)
- No finalized license — see `LICENSE` for the deferral status
- No LLM integration — Ollama backend work starts Week 9+
- No scenario reader or report generator yet — both new pieces from the
  Week 2 pivot, also starting Week 9+

---

Detailed weekly build scope and the ranked drop-if-behind cut order live
in [`PROJECT.md`](PROJECT.md)'s "Scope discipline" section, not here —
this file stays a short orientation, not a duplicate of it.
