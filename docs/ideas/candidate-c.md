# Idea Canvas — Candidate C

> **Content status:** this candidate is Disaster Response Coordination —
> already scoped in `PROJECT.md` since Week 1 (pivoted 2026-09-04). The
> scope table, out-of-scope list, and technology list below are pulled
> straight from that already-decided architecture, not newly invented for
> this canvas. The problem statement, feasibility-gate verdicts, hour
> estimates, and rejection paragraph are still genuinely `[ TODO ]` —
> real work, not yet done.

**Candidate name:** Disaster Response Coordination
**Date started:** 2026-08-24   **Well it came from:** talking with a dispatcher while at work — the conversation sparked the idea to work on this.

---

## 1. Problem statement

For              an emergency management planner at a county or small-city agency
who              has to decide how to allocate a fixed pool of Medical/Fire/Shelter/Security responders before or during a disaster
the problem is   current tools (WebEOC, ArcGIS Mission, Everbridge — see the competitive scan below) show the incident queue and the map, but none of them recommend or test different responder allocations against a likely scenario ahead of time
which costs      not yet researched in terms of what the problem itself costs an agency (no interview/agency-cost data yet — see §2's competitive scan for what existing tools cost instead). The one real number I do have is the cost of running this independently: roughly $400–4,000 in local hardware, depending on the route (several cheaper PCs running smaller models vs. one larger GPU box, per `HARDWARE.md`) — a build-cost number, not a problem-cost number, stated honestly as the distinction it is
Today they       run manual tabletop exercises, or rely on the existing EOC software's live logging with no simulated dry run beforehand
which falls short because  tabletop exercises are slow and expensive to organize, so agencies can't cheaply test many different team-composition options before committing to one

> If the `which costs` line has no number in it, stop and go get one. The
> competitive scan below (Juvare/Esri/Everbridge) tells you what existing
> tools cost agencies in dollars/licensing — that's a real place to pull
> a number from, not out of your head.

## 2. Evidence a user exists

**No interview conducted — competitive scan substituted instead**, per this
milestone's accepted alternative. Three existing tools that address
overlapping ground, each independently verified 2026-09-06:

| Tool | What it is | Does well | Does badly |
|---|---|---|---|
| [Juvare / WebEOC Nexus](https://www.juvare.com/products/webeoc-nexus/) | Cloud SaaS used by 4,000+ agencies for incident logging, resource requests, ICS form workflows | Auditability, FEMA-reporting interoperability, low-code configurability | System of record, not decision — shows the resource-request queue but doesn't propose an allocation or reason about tradeoffs |
| [Esri / ArcGIS Mission](https://www.esri.com/en-us/arcgis/products/arcgis-mission/overview) | Geospatial common operating picture: damage-assessment layers, live responder tracking, incident mapping | Spatial analysis (routing, hotspot detection, shelter inventory as of the March 2026 release) | Answers "where," not "who does what next and why" — a map, not a negotiation between responders with partial information |
| [Everbridge](https://www.everbridge.com/newsroom/article/thoma-bravo-completes-acquisition-of-everbridge/) | Critical event management / mass-notification platform (acquired by Thoma Bravo, taken private, 2024) | Getting alerts and status requests to the right people fast, at enterprise scale | Routes information, doesn't decide allocation — communication infrastructure, not a planning tool |

All three independently verified 2026-09-06.

**The gap this fills:** none of the three reason about *which* responders
to send where, try multiple team compositions against a scenario, or
produce a written recommended plan — they're systems of record, mapping,
or communication, not negotiation/decision tools. See `PROJECT.md`'s
"Related work" section for the fuller writeup, including what's NOT
novel (the contract-net bidding pattern and multi-agent disaster
simulation are both well-established separately).

- **Full write-up:** this section (no separate interview file — the
  competitive scan is the evidence for this candidate)

## 3. Candidate scope (Must features only)

Pulled from `PROJECT.md`'s "Rough scope" and "Scope & scale" sections —
hours are not filled in below; that estimate is still real work to do.

| # | Feature (one vertical slice each) | Hours |
|---|---|---:|
| 1 | Scenario engine (Mesa) + incident generator + naive greedy baseline | 20 |
| 2 | Resource agents + LLM-based bidding/negotiation via Ollama (swappable backend) | 15 |
| 3 | Incident-command reasoning role + disruption injection + renegotiation | 10 |
| 4 | Scenario reader (NL scenario text → simulation settings + candidate team sizes) | 5 |
| 5 | Team-size competition harness (run several candidate rosters per scenario) | 10 |
| | Evaluation harness (weighted scoring, fairness metric, greedy comparison) + Report generator | 4 |
| | Walking skeleton + CI | 10 |
| | Deployment + clean-machine test | 15 |
| | **Construction total** | **89** |

Budget: plan on **60 hours**, hard ceiling **75** — this candidate goes
over both. Scope Sizer's independent estimate was **124h (range
99–185)**, using 7 features + 2 integrations (OSMnx, Ollama), complex
data, novelty load 2. My hand estimate (89h) is lower than the
sizer's but still well above the stated ceiling. **Reconciliation:** I'm
accepting the overage rather than cutting scope to fit, because this is
the project I want to commit to — the gap gets closed with planned
overtime hours beyond the course's 240-hour budget line, not by pretending
the scope is smaller than it is. If overtime doesn't materialize, `PROJECT.md`'s
scope-discipline cut order (fewer team sizes tried first, then fewer
scenarios, then the OSMnx/synthetic-grid fallback) is the fallback plan,
not a surprise decided under pressure later.

## 4. Out of scope — will NOT be built

Pulled directly from `PROJECT.md`'s locked stack decisions:

1. A live, real-time interactive dashboard (React/Leaflet) — dropped
   Week 2; final demo uses a static/recorded visualization instead.
2. Paid/hosted LLM APIs (Anthropic, OpenAI, etc.) — Ollama-only, by
   constraint.
3. Classical (non-LLM) contract-net as a formal comparison baseline —
   only greedy nearest-unit survives as a sanity check.
4. A MILP/optimal-solver ceiling comparison (PuLP/CBC) — dropped Week 2
   along with the research-comparison framing.
5. More than one city/road-network per scenario.
6. Firearms/hazmat-specific responder types — Medical, Fire,
   Shelter/Logistics, Security only.
7. Multi-user accounts or role-based access beyond the single admin account. The MVP has one account; FR-AUTH-01 is the design it scales into.
8. A PDF/HTML-rendered report — Markdown only for now; nicer rendering is
   a nice-to-have, not required.
9. Real-time/streaming disruption injection beyond the three fixed types
   (road closure, unit failure, incident surge).
10. Support for scenarios beyond ~30–50 incidents / 25–40 units (medium
    scale, per `PROJECT.md` Scope & scale).

## 5. Feasibility screen

| Gate | Verdict | Evidence (dated) |
|---|---|---|
| **Build** — novelty load ≤ 2 | `[ TODO — pass/fail ]` | See technology list below; count "new" yourself |
| **Get** — every dependency exercised for real | Partial — OSMnx passes, Ollama is UNVERIFIED | Ollama/local LLM: **UNVERIFIED** — validation deliberately deferred to week 9 per `RISKS.md` #2 (no GPU server yet, dev laptop judged not worth prototyping on). OSMnx: **PASS** — real road graph for Macomb, IL loaded (641 nodes, 1804 edges) and routed correctly (McDonald's → Chick-fil-A, 2.12mi, 8ms) 2026-09-06; see `docs/evidence/dependency-checks/2026-09-06-osmnx-macomb-spike.md` |
| **Ship** — a named deployment target, terms read | `[ TODO — pass/fail ]` | `[ TODO ]` |
| **Show** — a stranger sees it work in 10 minutes | `[ TODO — pass/fail ]` | `[ TODO ]` |

**Technologies:** Mesa (known) · OSMnx (new — real road network, not yet
exercised) · Ollama/local LLM (new — not yet exercised, deferred to week
9 by prior decision) · hand-rolled contract-net (known concept, new
implementation) · Matplotlib static visualization (known)

**Novelty load:** 2 by this count — same as Candidate A, and higher-risk
than Candidate B, since two of the "new" pieces (Ollama negotiation
quality, OSMnx integration) are both explicitly unverified as of tonight.

**Honest tension worth naming:** this milestone's rubric wants every
dependency "exercised once for real this week." This candidate's own
risk register already documents that its central dependency (local LLM
bid quality) is deliberately not being tested until week 9 — that's an
accepted, documented risk, not new information, but it means this
candidate's Get-gate evidence will be thin compared to A and B unless
the OSMnx piece gets a real spike tonight.

## 6. The one hard part

The real hard part is pipeline quality: the negotiation pipeline (scenario reader → agent bidding → allocation) has to be clean and structured enough that its output data (miles traveled, response times, etc.) can actually tell a good team-composition plan apart from a bad one — a sloppy pipeline just produces noisy numbers that make every team size look about the same. That's compounded by environmental variability: obscure or unexpected values in a given scenario can break the pipeline in ways that are hard to predict ahead of time.

## 7. Scorecard (1–5 each; weight in parentheses)

| Criterion | (w) | Score | Weighted |
|---|---:|---:|---:|
| Evidence a user exists | 3 | 3 | 9 |
| Fits ~45 hours of features | 3 | 1 | 3 |
| Novelty load | 2 | 2 | 4 |
| Dependencies verified | 2 | 3 | 6 |
| Demonstrable in ten minutes | 1 | 2 | 2 |
| **Total (max 55)** | | | **24** |

> Score honestly — this candidate has the most sunk work and the most
> existing conviction behind it, which is exactly the bias the assignment
> warns about. If it wins, it should win on this table, not by default.

## 8. If this candidate is rejected

This is the presumptive front-runner, and I don't expect to reject it — but honestly: I'd drop it only if I'm 2+ weeks behind on real work with no credible path to finishing on time. Not one missed deadline — a sustained, compounding delay where I genuinely can't see myself catching up, even with the overtime already planned into the hour budget (§3). If that point is reached, it isn't an instant "closed" — §10's scope-cut order (fewer team sizes, fewer scenarios, synthetic grid fallback) gets invoked first. Only if those cuts still don't close the gap would walking away from the project actually be on the table, and given the sunk work by that point, that would mean the semester itself is in trouble, not just this candidate.

> The most likely real killer, given tonight's evidence: if the OSMnx
> spike fails AND local LLM bid quality (tested properly in week 9) turns
> out unusable, per `RISKS.md`'s own cut order this degrades to a
> synthetic-grid, smaller-scenario version of the same idea — not a full
> rejection. A full rejection would need the core negotiation mechanism
> itself to fail, not just the road network.
