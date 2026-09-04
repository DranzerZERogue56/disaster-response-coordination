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

## Current status

Concept and scope locked (Week 1), then pivoted in Week 2 away from an
earlier version that set out to prove one negotiation style beats
classical optimization with a live real-time map as the demo centerpiece
— this version instead focuses on trying different team sizes against a
scenario and producing a usable written plan, no live map. Week 1's
Project Charter & Engineering System milestone is still in progress —
charter content, AI-usage log, hours log, and project board are not yet
filled in. No application code yet — Phase 1 (Weeks 1–8) is
planning/design deliverables only; construction starts Week 9. See
`docs/charter.md` for capacity, non-goals, and the ranked cut order if
the schedule slips.

## How to navigate the docs

- [`PROJECT.md`](PROJECT.md) — architecture, tech stack, evaluation plan, team-size competition, report generation
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
- No scenario reader or report generator yet — both new pieces from the
  Week 2 pivot, also starting Week 9+

---

Detailed weekly build scope and the ranked drop-if-behind cut order live
in [`PROJECT.md`](PROJECT.md)'s "Scope discipline" section, not here —
this file stays a short orientation, not a duplicate of it.
