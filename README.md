# Adaptive Multi-Agent Disaster Response Coordinator

Senior CS capstone (solo, one semester, 240 hours). A simulated large-scale
disaster unfolds over a real road network; resource agents 
(Medical, Fire,Shelter/Logistics, Security) 
negotiate allocation via natural-language contract-net bidding, under an LLM-reasoned incident-command policy layer.
Core evaluated capability: **replanning after disruptions** (road closure,
unit failure, incident surge) — compared against classical
auction/optimization baselines.

Full docs: [`PROJECT.md`](PROJECT.md) (architecture, tech stack, evaluation
plan) · [`RISKS.md`](RISKS.md) (draft risk register) ·
[`HARDWARE.md`](HARDWARE.md) (local GPU server build + when each phase is
needed) · [`CALENDAR.md`](CALENDAR.md) (raw weekly schedule)

**Current status:** concept locked, no code yet. Halfway audit lands
Week 8 (Oct 18) at 120/240 hours.

---

## Phase 1 — Foundation & Design (Weeks 1–8, 0–120 hrs)

Planning/documentation weeks — no code yet. These are graded course
artifacts, not droppable scope.

| Week | Dates | Hrs | Deliverable |
|---|---|---|---|
| 1 | Aug 24–30 | 15/240 | Project Charter & Engineering System |
| 2 | Aug 31–Sep 6 | 30/240 | Idea Portfolio & Scoping Decision |
| 3 | Sep 7–13 | 45/240 | Software Requirements Specification v1 |
| 4 | Sep 14–20 | 60/240 | Non-Functional Requirements, Constraints & Definition of Done |
| 5 | Sep 21–27 | 75/240 | Technology Evaluation & Architecture Decision Records _(+ OSMnx spike: does the city graph load and route?)_ |
| 6 | Sep 28–Oct 4 | 90/240 | Technical Specification (System Design Document) _(+ OSMnx go/no-go decided here)_ |
| 7 | Oct 5–11 | 105/240 | Work Breakdown, Schedule & Risk Register |
| 8 | Oct 12–18 | **120/240 — halfway** | Design Review Checkpoint (Weeks 1–8 audit) |

## Phase 2 — Construction & Delivery (Weeks 9–16, 120–240 hrs)

This is where actual build scope lives, and where things get cut if the
schedule slips. **Drop-if-behind** is cumulative and ordered — each item
assumes everything above it in the table is already dropped.

| Week | Dates | Hrs | Building | Drop-if-behind (saves time) |
|---|---|---|---|---|
| 9 | Oct 19–25 | 135/240 | Mesa scenario engine + incident generator + greedy baseline + CI skeleton (Walking Skeleton) | — (foundational, don't cut) |
| 10 | Oct 26–Nov 1 | 150/240 | Resource agents + contract-net negotiation, LLM bidding via Ollama (Core Increment) | Reduce scenario scale: medium (~30–50 incidents) → small (~10–20) |
| 11 | Nov 2–8 | 165/240 | Incident-command LLM policy layer + disruption injection + unit/scenario-replay tests | Drop property-based/fuzz tests — keep unit + scenario-replay only |
| 12 | Nov 9–15 | 180/240 | Classical contract-net + MILP baseline (PuLP/CBC) + eval harness wiring | Drop the MILP baseline — keep greedy + classical contract-net |
| 13 | Nov 16–22 | 195/240 | Dashboard (React + Leaflet, incl. tiles-free demo mode) + OSMnx integration + reproducibility script + docs | Use the synthetic grid graph (per the Week 6 go/no-go) instead of OSMnx |
| 14 | Nov 23–29 | 210/240 | Full evaluation runs (5–10/condition) + fairness metric + Release v1.0 | Cut eval runs to 2–3/condition, flag as a limitation in the writeup |
| 15 | Nov 30–Dec 6 | 225/240 | Presentation deck, live-demo rehearsal, stress-test on larger scenario (stretch) | Skip the stress-test; demo the pre-recorded fallback run instead of live |
| 16 | Dec 7–13 | 240/240 | Final Submission (Thu Dec 10) & Capstone Presentation (Fri Dec 11) | Buffer/bug-fix week — no new scope |

**Rule of thumb:** if you're checking this mid-week and hours-spent is
running noticeably ahead of the week's hour target, apply that week's
drop *before* starting that week's build item, not after.
