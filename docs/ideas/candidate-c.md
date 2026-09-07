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

**Juvare / WebEOC Nexus** — cloud-based SaaS used by 4,000+ agencies for
incident logging, resource requests, and ICS form workflows. Does well:
auditability, interoperability with FEMA reporting formats, low-code
configurability. Does badly: it's a system of record, not a system of
decision — it shows the resource-request queue but doesn't propose an
allocation or reason about tradeoffs. [Juvare](https://www.juvare.com/products/webeoc-nexus/)

**Esri / ArcGIS Mission** — the geospatial common operating picture:
damage-assessment layers, live responder tracking, incident mapping via
Mission Manager/Responder/Server. Does well: spatial analysis (routing,
hotspot detection, shelter inventory as of the March 2026 release). Does
badly: answers "where," not "who does what next and why" — it's a map,
not a negotiation between responders with partial information.
[Esri](https://www.esri.com/en-us/arcgis/products/arcgis-mission/overview)

**Everbridge** — critical event management and mass-notification platform
(acquired by Thoma Bravo, taken private, 2024). Does well: getting alerts
and status requests to the right people fast at enterprise scale. Does
badly: routing information, not deciding allocation — it's communication
infrastructure, not a planning tool.
[Everbridge](https://www.everbridge.com/newsroom/article/thoma-bravo-completes-acquisition-of-everbridge/)

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
| 1 | Scenario engine (Mesa) + incident generator + naive greedy baseline | |
| 2 | Resource agents + LLM-based bidding/negotiation via Ollama (swappable backend) | |
| 3 | Incident-command reasoning role + disruption injection + renegotiation | |
| 4 | Scenario reader (NL scenario text → simulation settings + candidate team sizes) | |
| 5 | Team-size competition harness (run several candidate rosters per scenario) | |
| | Evaluation harness (weighted scoring, fairness metric, greedy comparison) | |
| | Report generator (Markdown template + incident-command reasoning trace) | |
| | Walking skeleton + CI | |
| | Deployment + clean-machine test | |
| | **Construction total** | **80–100** |

Budget: plan on **60 hours**, hard ceiling **75** — this candidate goes
over both. Scope Sizer's independent estimate was **124h (range
99–185)**, using 7 features + 2 integrations (OSMnx, Ollama), complex
data, novelty load 2. My hand estimate (80–100h) is lower than the
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
7. Multi-user accounts or role-based access — single local user.
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

`[ TODO — even though this is the presumptive front-runner, write this honestly: what would actually have to be true for you to walk away from 2+ weeks of sunk work? Name the gate and the number. ]`

> The most likely real killer, given tonight's evidence: if the OSMnx
> spike fails AND local LLM bid quality (tested properly in week 9) turns
> out unusable, per `RISKS.md`'s own cut order this degrades to a
> synthetic-grid, smaller-scenario version of the same idea — not a full
> rejection. A full rejection would need the core negotiation mechanism
> itself to fail, not just the road network.
