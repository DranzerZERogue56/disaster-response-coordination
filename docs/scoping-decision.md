# Scoping Decision — Disaster Response Coordination

**Author:** Dranzer Rogue  ·  **Date:** 2026-09-06  ·  **Course week:** 2

---

## 1. Problem

An emergency management planner at a county or small-city agency has to decide how to allocate a fixed pool of responders — medical, fire, shelter, and security — before or during a disaster. Existing tools show the incident queue and a map, but none of them recommend or test different responder allocations against a likely scenario ahead of time, so planners fall back on manual tabletop exercises to compare options. Those exercises are slow and expensive to organize, which means an agency can't cheaply test more than one or two team compositions before committing to a plan. What the problem itself costs an agency hasn't been researched yet — no interview data exists for that number. The one real number available is the cost of running an independent alternative: roughly $400–4,000 in local hardware, depending on the route chosen (several cheaper machines running smaller models vs. one larger box).

## 2. Evidence a user exists

No interview conducted — substituting a competitive scan of three existing tools, per this milestone's accepted alternative, since a real emergency-management planner wasn't reachable on this timeline.

- **Juvare/WebEOC Nexus** (cloud SaaS, 4,000+ agencies): logs incidents and resource requests well, but is a system of record — it doesn't propose an allocation or reason about tradeoffs.
- **Esri/ArcGIS Mission**: strong spatial analysis (routing, hotspot detection, shelter inventory), but answers "where," not "who does what next and why."
- **Everbridge** (critical event management, acquired by Thoma Bravo 2024): fast alerting/notification at enterprise scale, but is communication infrastructure, not a planning tool.

None of the three try multiple responder compositions against a scenario or produce a written recommended plan — that's the gap this project fills. Full write-up: `docs/ideas/candidate-c.md` §2.

## 3. Chosen scope — Must features

| # | Feature | Hours |
|---|---|---:|
| 1 | Scenario engine + incident generator + naive baseline | 20 |
| 2 | Resource agents + LLM-based negotiation (swappable backend) | 15 |
| 3 | Incident-command reasoning + disruption injection + renegotiation | 10 |
| 4 | Scenario reader (plain-English scenario → simulation settings) | 5 |
| 5 | Team-size competition harness | 10 |
| | Evaluation harness + report generator | 4 |
| | **Feature total** | **64** |
| | Walking skeleton + continuous integration | 10 |
| | Deployment + clean-machine test | 15 |
| | **Construction total** | **89** |

Plan: 60 hours. Hard ceiling: 75. My number: **89** (Scope Sizer's independent estimate: 124h, range 99–185). Both are over the ceiling — I'm accepting the overage and closing the gap with planned overtime because this is the project I want to commit to, not by pretending the scope is smaller than it is; if overtime doesn't materialize, `PROJECT.md`'s scope-discipline cut order is the fallback, decided in advance rather than under pressure.

## 4. Should features — built only if there is room

None scoped with real hours/weeks for this course cycle. Two "if I can" aspirations exist but are explicitly not committed to: a better mapping/visualization system, and — if this ever went beyond a class project — dispatcher-facing access to create and view plans on demand. The second one directly conflicts with §5's "no multi-user accounts" line, so it's a future-beyond-the-course idea, not something pulled into this semester's scope.

## 5. Out of scope — will not be built

A live, real-time interactive dashboard (React/Leaflet) · paid/hosted LLM APIs (Anthropic, OpenAI, etc.) · classical (non-LLM) contract-net as a formal comparison baseline · a MILP/optimal-solver ceiling comparison (PuLP/CBC) · more than one city/road-network per scenario · firearms/hazmat-specific responder types · multi-user accounts or role-based access · a PDF/HTML-rendered report · real-time/streaming disruption injection beyond the three fixed types · scenarios beyond ~30–50 incidents / 25–40 units

## 6. Accepted tradeoffs

**Dropped the live, real-time dashboard for a static/recorded visualization.** Costs: a less interactive, less impressive-looking final demo. Accepted because it removes the live-demo-crash and venue-network risks the earlier plan carried, and frees hours for the scenario reader and report generator instead. Would revisit if construction finishes early with real slack left.

**Markdown-only report, not PDF/HTML.** Costs: a less polished-looking deliverable for something meant to double as a company policy document. Accepted because it's free, diffable, and viewable directly on GitHub with no extra tooling. Would revisit if there's spare time in week 13 (documentation week).

`[ TODO — any other tradeoff you want named here? ]`

## 7. Rejected candidates

**Rejected: Estate Contents to Probate Accounting (Candidate A).** Rejected — closed for this course, not deferred to a date. Two things killed it: cost and fit. The vision-API dependency for Feature 1 isn't free per call, and at the volume a real estate inventory needs, that cost isn't something I can justify on a class budget with no grant or funding behind it. Separately, the one hard part of this project — getting item identification specific enough to retrieve a valid comp, with no way to tell a correct answer from a confidently wrong one except by checking comp variance after the fact — is an open-ended data/ML-calibration problem, and perfecting that isn't where I want to spend a 240-hour capstone. Scorecard total: 13/55.

**Rejected: Out-of-State Title and Registration Completion (Candidate B).** Rejected — closed for now, not closed forever. Two compounding reasons: the actual regulatory content this tool needs has no machine-readable source, which fails the Get gate as written; and more decisively for me personally, I don't want to take on the state regulatory research and my employer's invention-assignment policy that comes with this, given it plainly relates to Kunes' line of business under the Illinois Employee Patent Act's carve-out. I'd revisit this if I left the dealership or got a written carve-out. Scorecard total: **29/55 — the highest of the three.** This is a judgment-based rejection, not an arithmetic one: B scores better on the mechanical criteria (fits the hour budget cleanly, lowest novelty load, easiest to demo), but it's rejected anyway because of an external constraint the scorecard doesn't capture, and because it's a simpler, less ambitious project than I want to spend a capstone on.

## 8. Hour budget, reconciled

| Weeks | Phase | Hours |
|---|---|---:|
| 1–2 | Inception | 30 |
| 3–4 | Requirements | 30 |
| 5–6 | Design | 30 |
| 7 | Planning | 15 |
| 8 | Design review + midterm | 15 |
| 9–12 | Construction + verification | 60 |
| 13 | Documentation | 15 |
| 14 | Deployment + handoff | 15 |
| 15–16 | Presentation + delivery | 30 |
| | **Total** | **240** |

My construction total (89h) does not fit inside the 60/75 line in the table above — construction is nominally budgeted 60h across weeks 9–12. I'm not cutting scope to force a fit; the difference gets absorbed by overtime hours logged beyond the course's 240-hour accounting, which is a real risk to the rest of the schedule if it doesn't materialize (see §10).

## 9. The one hard part

The real hard part is pipeline quality: the negotiation pipeline (scenario reader → agent bidding → allocation) has to be clean and structured enough that its output data (miles traveled, response times, etc.) can actually tell a good team-composition plan apart from a bad one — a sloppy pipeline just produces noisy numbers that make every team size look about the same. That's compounded by environmental variability: obscure or unexpected values in a given scenario can break the pipeline in ways that are hard to predict ahead of time.

## 10. Risks and the scope-cut trigger

| Risk | Likelihood | What it costs me | Early warning sign |
|---|---|---|---|
| Scope exceeds the 240-hour budget (this candidate runs 80–100h against a 60h construction line) | High | Overtime hours I have to actually log, or scope cut under pressure later | Construction hours tracked in `docs/hours-log.csv` exceeding plan by week 10 |
| Local LLM produces weak/inconsistent bids, undermining plan quality | Medium (raised to High) | The whole "team-size competition" signal becomes noise — see §9 | GPU server (`HARDWARE.md` Phase 1) not built by mid-week 8 |
| Scenario reader misparses a scenario, producing a broken simulation setup | Medium | A bad run gets scored and reported as if it were valid | Schema-validation check (planned) catching malformed output during testing |

**Scope-cut trigger.** Any Must feature that isn't implemented within 2 weeks of when work on it started gets cut — checked continuously through construction (weeks 9–12), not just at one fixed milestone. Catching up on a delayed feature has to happen on top of the current week's already-scheduled tasks, not by skipping them. When something has to give, I cut in this order: (1) reduce how many candidate team sizes get tried per scenario, (2) reduce the number of authored benchmark scenarios, (3) fall back from the real road network to a synthetic grid graph, (4) shrink scenario scale from medium to small. Decided now, in advance, so I don't have to decide it while panicking mid-semester.

---

**Signed:** Dranzer Rogue, 2026-09-06
**AI use for this document:** Assembled from already-disclosed reasoning in `docs/ideas/candidate-*.md` and `PROJECT.md`/`RISKS.md` (mechanical reformatting, not new content) plus direct Q&A for the pieces that were genuinely new (rejection reasoning, cost numbers, the hard part) — see `docs/ai-usage.md` for the itemized log.
