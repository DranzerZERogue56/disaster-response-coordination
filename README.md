# Adaptive Multi-Agent Disaster Response Coordinator

## What this is

A senior CS capstone project: an adaptive multi-agent system that
coordinates resource allocation (Medical, Fire, Shelter/Logistics,
Security) for a simulated large-scale disaster on a real road network.
Resource agents negotiate allocation via natural-language contract-net
bidding under an LLM-reasoned incident-command policy layer. The core
evaluated capability is replanning after disruptions (road closures, unit
failures, incident surges), benchmarked against classical
auction/optimization baselines. Full research question and locked
architecture: [`PROJECT.md`](PROJECT.md).

## Who owns it

Solo capstone project, one semester, 240 hours total, graded per a
weekly-deliverable course schedule (see [`CALENDAR.md`](CALENDAR.md)).

## Current status

Concept and scope locked (Week 1). Week 1's Project Charter &
Engineering System milestone is still in progress — charter content,
AI-usage log, hours log, and project board are not yet filled in. No
application code yet — Phase 1 (Weeks 1–8) is planning/design
deliverables only; construction starts Week 9. See `docs/charter.md`
for capacity, non-goals, and the ranked cut order if the schedule slips.

## How to navigate the docs

- [`PROJECT.md`](PROJECT.md) — architecture, tech stack, evaluation plan
- [`CALENDAR.md`](CALENDAR.md) — full 16-week schedule with weekly deliverables
- [`RISKS.md`](RISKS.md) — draft risk register
- [`HARDWARE.md`](HARDWARE.md) — local GPU server build plan, phased by readiness week
- [`docs/charter.md`](docs/charter.md) — project charter (purpose, constraints, non-goals, risks, cut order)
- [`docs/ai-usage.md`](docs/ai-usage.md) — AI usage policy and dated log
- [`docs/hours-log.csv`](docs/hours-log.csv) — logged work sessions
- `docs/adr/` — architecture decision records (Week 5+)
- `docs/` (site root) — static GitHub Pages progress dashboard, live at
  https://dranzerzerogue56.github.io/disaster-response-coordination/

## What's intentionally not here yet

- No application code — `src/` and `tests/` are empty scaffolding until
  Week 9 (Mesa scenario engine, contract-net negotiation, etc.)
- No CI — `.github/workflows/` is empty scaffolding
- No architecture decision records — `docs/adr/` is empty until Week 5
- No finalized license — see `LICENSE` for the deferral status
- No LLM integration — Ollama backend work starts Week 9+

---

Detailed weekly build scope and the ranked drop-if-behind cut order live
in [`PROJECT.md`](PROJECT.md)'s "Scope discipline" section, not here —
this file stays a short orientation, not a duplicate of it.
