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

### Optional: use the local language model (Ollama)

By default the app classifies reports with a rules-based stand-in, so it runs with no model installed. To use a
real local model instead (kill switch: unset or `0` turns it off again, with no restart):

```
ollama pull qwen3:1.7b                 # once; about 1.4 GB
OLLAMA_ENABLED=1 ./script/start        # the model becomes the first tier; the rules tier stays behind it as the fallback
```

Settings (`OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`, `OLLAMA_SMALLER_MODEL`) are listed in `.env.example`. The model
server must be on this machine over plain `http` (127.0.0.1, localhost or ::1); anything else is refused. If the model is
down, slow, busy or answers badly, the report is still classified by the next tier and its reasoning says so. Answers from
a real model need confidence 85 or more (`MODEL_AUTO_APPROVE_MIN`, never below 75) before a unit is dispatched without a
person. The dispatcher console is at http://127.0.0.1:8080/dispatcher.

### First sign-in (two-factor)

`./script/start` turns the sign-in on (`AUTH_ENFORCED=1`): every page and action except `/healthz` and `/login` needs a signed-in dispatcher, and every form carries a forgery token. To create the first account (or reset the seeded `demo-dispatcher`):

```
python tools/enrol_dispatcher.py demo-dispatcher dispatcher
```

It prints a random password and a phone setup key **once**. Type the key into an authenticator app on your own phone (any app that takes time-based codes; Duo Mobile's third-party account option works), then sign in at http://127.0.0.1:8080/login with the password and the six-digit code. While the sign-in is on, field reports, the scenario tool and node heartbeats over HTTP are refused (DEF-032); run with `AUTH_ENFORCED=0` for those demos.

## Run the tests

One command runs the whole suite (unit, integration and acceptance, with the 90% line-coverage gate), and it is the command CI runs:

```
./script/test
```

The test plan is `docs/test-plan.md`; the last full run is `docs/test-results.md`; the requirement-to-test matrix is `docs/traceability.csv` (rebuild it with `python tools/build_traceability.py` after a test run); defects are in `docs/defect-log.md`. The dispatcher console is at `http://127.0.0.1:8080/dispatcher` once the app is running. Test data: `./script/seed-test-data`.

## Security checks

CI runs a secrets scan, Ruff with its security rules, the full suite, a build and a smoke check, and a separate dependency audit (`pip-audit`) on every push and weekly. Dependencies are hash-pinned (`requirements.txt`, `requirements-dev.txt`, `requirements-audit.txt`). The reviews are in `docs/security-review.md`, `docs/python-vulnerability-audit.md`, `docs/flask-template-audit.md`, `docs/password-hashing-audit.md` and `docs/pipeline-security-audit.md`.

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

- Language model: an optional local Ollama client exists (see "Optional" above); the rules-based stand-in is the default
  and the last fallback. Only one small demo model (`qwen3:1.7b`) is supported on this laptop; the two requirements that
  name the 24 GB target GPU (FR-INFER-02, NFR-PERF-01) stay unverified on purpose (CR-014).
- No login (FR-AUTH-01): the dispatcher console uses a seeded stand-in account, and there is no CSRF protection (DEF-018).
- Plain HTTP only; HTTPS is deferred (CR-013).
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
