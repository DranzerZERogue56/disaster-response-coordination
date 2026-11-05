# AI Usage Policy & Log

> I will use AI to perform actions I already understand how to do, but would like to focus on other aspects of the project. 
---

## Spine rule

If I can't describe what, why and how the AI is supposed to perform the action, I shouldn't have it do it.

## Zones

| Zone | Meaning | Examples |
|---|---|---|
| 🟢 Green | `[ can describe why I delegated ]` | `[ I delegated Claude to, grab a live map API I have found so I can pull in real time maps into my project.]` |
| 🟡 Amber | I might have trouble fully completing it myself | I had AI complete it with only partial knowledge of why |
| 🔴 Red | I had not clue what I was doing | I had AI do whatever it thought was best without reviewing it |

## Tools I have decided to use
Claude, Claude Code/CLI, Claude CoWork.
ChatGPT.
Geminai, geminai Notebook.
local-hosted LLm models for agents.
as well as AI artists, and UI assistents that will be included as I research them. 

## Log

Blank entry template — copy the block below and paste it, with a blank
line before and after, each time you have a use to log:

```
**Date:** YYYY-MM-DD
**Zone:** Green/Amber/Red
**Tool:**
**What I asked for:**
**What I kept/changed:**
**Why:**
```

---

**Date:** 2026-08-30 to 2026-08-31
**Zone:** Green
**Tool:** `[Claude helping push]`
**What I asked for:** I asked for a github repo, and created the nessecary documents the HW asked for alongside filling in the idea I have already been brainstorming.
**What I kept/changed:** changed the formatting as I didn't like how it looks.

---

**Date:** 2026-09-06
**Zone:** 🟢 Green
**Tool:** Claude (chat)
**What I asked for:** Research existing commercial competitors to a disaster-response coordination system
**What I kept/changed:** Kept Juvare/WebEOC, Esri/ArcGIS, and Everbridge's acquisition details as verified real products; flagged the Palantir–FEMA claim as unconfirmed after independently fact-checking it; the closing "novelty positioning" conclusion is mine to decide, not something I'm adopting as written
**Why:** Delegated the factual survey (which products exist, what they do) — that's a describable, mechanical research task; the judgment about what it means for my project stays mine

---

**Date:** 2026-09-06
**Zone:** 🟡 Amber
**Tool:** Claude
**What I asked for:** Open brainstorm for two Milestone 2 candidate ideas — no constraints given beyond generating real candidates
**What I kept/changed:** AI proposed both project concepts (estate/probate accounting tool; dealership title/registration tool) and drafted their full scope, out-of-scope lists, feasibility/tech analysis, and risk reasoning. I reviewed every section, independently verified the Illinois employee-invention-law claim in Candidate B (checks out at the statute level), and added an explicit caution that Candidate B touches my actual employer and needs my real employment agreement read before it goes anywhere past a class exercise. Problem statements, interview evidence, feasibility verdicts, and hour estimates are still mine to fill in, untouched.
**Why:** This is a bigger AI role than the Green-zone entry above — it proposed the actual projects and did real design/risk work, not just fact-gathering. Amber because I'm only claiming it as mine after actually reviewing and verifying it, not because I generated it myself.

---

**Date:** `[ DRAFT — rank/edit ]` 2026-09-03/04
**Zone:** `[ DRAFT: Green ]`
**Tool:** Claude Code
**What I asked for:** Set up Week 2 folder structure, pulled the real course templates (idea canvas, scoping memo, Scope Sizer script) from the course's public code repo, wrote the manual checklist file
**What I kept/changed:** Kept the real templates as-is (they're the course's own files, not AI content); the checklist is AI-written but is just a reorg of the assignment's own instructions, not new content
**Why:** Mechanical setup work, described and directed step by step — closest thing to a "grab an API and wire it in" delegation

---

**Date:** `[ DRAFT — rank/edit ]` 2026-09-04
**Zone:** `[ DRAFT: Amber ]`
**Tool:** Claude Code
**What I asked for:** Asked to redesign `PROJECT.md`'s architecture from a live-negotiation-demo concept to a roster-competition-and-report concept, after I described the new idea in my own words and answered several rounds of direct questions about it
**What I kept/changed:** I supplied the actual concept and made every decision when asked (competition axis, whether to keep the research framing, how to score effectiveness, what happens to the live demo). AI wrote the actual document sections, chose section structure, and drafted the prose implementing my decisions, plus made judgment calls on things I didn't specify (report format, scope-discipline cut order, which risks to add/remove). I reviewed and pushed all of it.
**Why:** I directed the what/why, but AI did real authorship of a graded-adjacent document (not this milestone directly, but feeds `docs/charter.md` §6/§7 later) — Amber because of how much independent judgment went into the wording and structure, even though the concept was mine

---

**Date:** `[ DRAFT — rank/edit ]` 2026-09-04
**Zone:** `[ DRAFT: Green ]`
**Tool:** Claude Code
**What I asked for:** Research whether existing technology/research already resembles the pivoted concept, for a "Related work" section
**What I kept/changed:** Kept RoboCup Rescue Simulation League, the contract-net-protocol precedent, and the scenario-parsing prior art as cited; kept the "what's actually different" conclusion largely as researched, since it's a factual gap analysis, not a creative claim
**Why:** Describable factual research task, same shape as the competitor-research entry above

---

**Date:** `[ DRAFT — rank/edit ]` 2026-09-06
**Zone:** `[ DRAFT: Green ]`
**Tool:** Claude Code
**What I asked for:** Build Candidate C's idea canvas by pulling from already-written, already-disclosed `PROJECT.md` content (scope table, out-of-scope list, tech list) rather than writing anything new
**What I kept/changed:** Kept the mapping as-is since it's just repackaging decisions already made and logged elsewhere; the parts requiring new judgment (problem statement, feasibility verdicts, hour numbers, rejection paragraph) were left `[ TODO ]`, not filled in
**Why:** Mechanical reformatting of already-disclosed content into a new template, not new design work


---

**Date:** `[ DRAFT — rank/edit ]` 2026-09-06 (good)
**Zone:** `[ DRAFT: Green ]`
**Tool:** Claude Code
**What I asked for:** Run a real OSMnx dependency spike (install, geocode test, build a real road graph for Macomb IL, route between two real businesses)
**What I kept/changed:** Kept the actual results as evidence (graph size, route distance/time); no interpretation was handed to me beyond "pass/fail," which I still have to confirm I agree with
**Why:** Mechanical technical execution with a clearly describable task and objective pass/fail result

---

**Date:** `[ DRAFT — rank/edit ]` 2026-09-13 (good)
**Zone:** `[ DRAFT: Green ]`
**Tool:** Claude Code
**What I asked for:** Scaffold `docs/requirements.md` from the real course SRS template, pull the course's own worked example (PantryPilot) for reference boxes only
**What I kept/changed:** Kept the real template structure and the course's own sample text as clearly-labeled reference material, not my content; every real field left `[ TODO ]`
**Why:** Mechanical setup, same shape as the Week 2 template-pulling entry above


---

**Date:** `[ DRAFT — rank/edit ]` 2026-09-13 (good)
**Zone:** `[ DRAFT: Green ]`
**Tool:** Claude Code
**What I asked for:** Mechanically reformat 30 self-written requirements from a bulleted Actor/Action/Object/Condition shape into the linter-required `**Requirement:**` sentence shape (merge only, no wording changes beyond joining the sentence), fix heading levels, flat-field formatting
**What I kept/changed:** All content is my own words from the bulleted draft, merged rather than rewritten; verified against `tools/check_requirements.py` afterward (0 errors, 0 warnings) rather than just trusting the reformat
**Why:** Pure mechanical transformation of my own text into the required shape — no new sentences authored

---

**Date:** `[ DRAFT — rank/edit ]` 2026-09-13 (good)
**Zone:** `[ DRAFT: Green ]`
**Tool:** Claude Code
**What I asked for:** For 6 requirements, asked guiding questions (happy path? failure case? what's the actual number for this placeholder?) one at a time instead of proposing answers
**What I kept/changed:** Every Given/When/Then sentence and every resolved number (1 block/10 min, 5 seconds, confidence threshold 75) is my answer to a question; AI reformatted my answers into Given/When/Then structure but the content itself is mine
**Why:** This is exactly the "ask, I decide" mode the policy allows — AI enumerated what a complete criterion needs, I supplied the actual behavior

---

**Date:** `[ DRAFT — rank/edit ]` 2026-09-13 (good)
**Zone:** `[ DRAFT: Green ]`
**Tool:** Claude Code
**What I asked for:** Add a project-board card for every Must-priority requirement identifier, per the assignment's board-mirroring requirement
**What I kept/changed:** Card titles are exact requirement identifiers already in the doc; descriptions/stopping-conditions are generic ("linter passes + acceptance criteria satisfied") not project-specific judgment calls
**Why:** Mechanical mirroring of already-decided identifiers onto the board, same pattern as Milestone 2's board setup

---

**Date:** `[ DRAFT — rank/edit ]` 2026-09-14 to 2026-09-20
**Zone:** `[ DRAFT: Green ]`
**Tool:** Claude Code
**What I asked for:** Kept working through Milestone 3's acceptance criteria one requirement at a time (FR-AGENT-04, FR-COORD-01 to 04, FR-RES-01 to 03, FR-DEGRADE-01 to 04), plus §1 Purpose and §3 Definitions
**What I kept/changed:** Every behavior, number, and priority change came from my answers (60 s agent timeout, 5 min consensus timeout, 4 min reservation release, 30 s node detection, 6 retries at 10 s, raising FR-DEGRADE-04 to Should). AI asked the guiding question, reformatted my answers into Given/When/Then, and pointed out gaps I then decided on (what releases a reserved unit, the DEGRADE-03/04 priority conflict). 12 of 30 requirements still have no acceptance criteria.
**Why:** Same "AI asks, I decide" mode as the earlier requirements entries; the AI raised cases, I supplied the behavior

---

**Date:** `[ DRAFT — rank/edit ]` 2026-09-20
**Zone:** `[ DRAFT: Green ]`
**Tool:** Claude Code
**What I asked for:** Scaffold Milestone 4: pull the course templates (NFR template, traceability checker, definition-of-done), generate `docs/traceability.csv` from my own FR and NFR text, run the checker, link the DoD from the README
**What I kept/changed:** Requirement text in the CSV is copied from my own document; the source, design, test, and status columns are placeholders. Checker reports 0 findings, which only shows the columns are filled, not that design and tests exist yet.
**Why:** Mechanical setup and transcription of my own text

---

**Date:** `[ DRAFT — rank/edit — READ THIS ONE ]` 2026-09-20
**Zone:** `[ DRAFT: Amber — AI proposed wording and methods, I set the numbers and decisions ]`
**Tool:** Claude Code
**What I asked for:** Help writing the 14 NFRs one at a time. AI translated my existing FR numbers into NFR form, suggested a measurement method for each, and listed candidate NFRs for the categories I hadn't covered. I answered each with the threshold or decision (5 s, 30 s, 4 min, 2-minute and 20-minute outage tests, 24 h retention, no caller data, web UI, 45 s decision, 5 min clean clone).
**What I kept/changed:** Thresholds and decisions are mine. Corrections that changed the result: AI pointed out that "0% to 2% loss" cannot be measured on 5 to 10 reports (one lost report is 10%), so I split it into a 0-loss demo test and a 2% stress test; my "run secretly" was clarified into a separate secret-scan requirement; my privacy answer was reversed from "keep the caller number" to "keep no caller data". Things AI wrote that I did not explicitly confirm and should check: the SEC-03 method (synthetic folder plus marker plus check script), the "model files already downloaded" condition on the 5-minute clone test, the ACC-01 and ACC-02 methods, and the 100-report stress size.
**Why:** The assignment says not to let the assistant write measurement methods unsupervised, so this is Amber until I confirm each method is something I would actually run in an afternoon

---

**Date:** `[ DRAFT — rank/edit — READ THIS ONE ]` 2026-09-20
**Zone:** `[ DRAFT: Green for the lookups, Amber for the tables AI drafted ]`
**Tool:** Claude Code
**What I asked for:** Draft the constraints, assumptions, dependencies, obligations, and data inventory tables from what I'd told it, and look up versions and licenses at their primary sources
**What I kept/changed:** AI fetched versions and license terms directly from PyPI, the GitHub API, Hugging Face, spdx.org, openstreetmap.org, and the Nominatim policy page, all dated 2026-09-20; I have not re-checked them myself and should spot-check at least one. I suggested Anthropic's Haiku as the model, and AI corrected me: it is a hosted API model, which breaks CON-03, FR-INFER-01, and NFR-SEC-01, so I am choosing between Phi-3.5-mini (MIT) and Qwen2.5-7B (Apache-2.0). I moved "no real data" from the constraints table to a decision (it is mine, not imposed). AI set the assumption verify-by dates from my calendar and added three inventory rows (admin credential, queued reports, unit status) that I need to confirm. The license position is a deferral in my words: MIT leading, GPL-3.0-only as backup.
**Why:** Version and license lookup is a describable factual task; the dates, the added rows, and the license choice are judgment calls I still have to own
---

**Date:** `[ DRAFT — rank/edit — READ THIS ONE ]` 2026-09-27
**Zone:** `[ DRAFT: Amber — AI drafted the matrix, ADRs, and spikes; I set the two real decisions and need to check the sourced facts myself ]`
**Tool:** Claude Code
**What I asked for:** Build out Milestone 5 end to end under a tight deadline (due tonight): the weighted matrix (4 decisions), 5 ADRs, 3 spike plans, the LICENSE file, and the tech-evaluation.md writeup. I made exactly two calls myself: `llama3.2:3b` over `mistral:7b` for the local model, and demoting OSMnx (defending Ollama and Mesa as the remaining novelty load, since Ollama is core and Mesa was a risk-reducer). Every weight, score, evidence line, ADR paragraph, and seam-inventory row beyond those two calls is AI-drafted and not yet reviewed by me line by line.
**What I kept/changed:** The two decisions above are mine. AI looked up versions/licenses at vendor sources (Ollama, Mesa, OSMnx, SQLite, the Llama 3.2 model license, the Mistral model card), all dated 2026-09-27 in the verification log — I have not independently re-checked any of these myself yet. One correction worth flagging: AI's first draft of Spike SP-01 said both OSMnx test address pairs succeeded; when I had it re-check the actual session transcript from 2026-09-06, only the second pair (McDonald's to Chick-fil-A) actually worked — the first pair (Taco Bell to Dad's Garage) failed at geocoding, not routing. AI caught its own error against the transcript and corrected SP-01 and ADR 0004 to match before I saw the wrong version, but I'm recording it since it's exactly the kind of factual claim this week's policy says can't come from AI unverified — I should re-read the transcript excerpt myself to confirm the correction is now right.
**Why:** Amber rather than Green because the volume of matrix scores, evidence citations, and ADR consequence/revisit-trigger content is large relative to what I've personally verified so far under tonight's time limit; Amber rather than Red because the two decisions that actually required my judgment were mine, and the one factual error found so far was caught and disclosed rather than left in.

---

**Rep 12 verification hit rate — `[ TODO — fill in yourself, see note ]`**

The assignment requires this as a fraction (claims personally checked / claims found accurate) plus the category of claim you now distrust most. This can't be filled in by the assistant — the whole point is that *you* sample-check a handful of the claims in the verification log (`docs/tech-evaluation.md` §7) against their cited source yourself, not that the assistant re-asserts them. Suggested minimum before resubmitting: pick 3-5 rows from that log (the Llama 3.2 license clause and the Ollama model sizes are the highest-stakes ones, since they drove ADR 0001's decision), open the cited URL yourself, and record here how many held up.

Format: `Checked N of M claims in the verification log; N-x held up as stated. The category I'd distrust most: ___.` (One real candidate for that last blank: model-card claims about relative reasoning quality between llama3.2:3b and mistral:7b — that evidence is a vendor's own marketing framing ("outperforms Llama 2 13B on all benchmarks"), not an independent benchmark, and it's the softest evidence in the whole matrix.)

---

**Date:** `[ DRAFT — rank/edit — READ THIS ONE ]` 2026-10-04
**Zone:** `[ DRAFT: Green — the four answers are mine, AI only structured the prose ]`
**Tool:** Claude Code
**What I asked for:** Milestone 6's Hard-tier Design Defense Memo. AI asked the assignment's four required questions directly (weakest decision, most-regretted decision with a numeric signal, the cut line, the AI honesty call), offered one candidate answer per question to react to, then wrote the memo from my actual answers rather than its own candidates where I gave a different or more specific answer.
**What I kept/changed:** Section 1 (node granularity) and section 2 (the confidence-60 threshold) are my own picks — AI's node-granularity candidate matched what I'd have said anyway, but the "demo machine, not a real-time tracker" justification for proceeding is mine, not something AI offered. Section 3's cut line (zone display, unit tracking, network-partition recovery) is my list, not AI's suggested order from the prior turn, and I did not confirm whether the Web UI itself would also be cut, so AI correctly left that off rather than assuming. Section 4 is the one I want a reviewer to actually read closely: it's a direct criticism of how this assistant's work held onto live-real-time-tool assumptions after the 2026-09-04 pivot, visible concretely in the 2026-09-20 NFR session logged above (the 45-second decision window, the keyboard-reachable web UI language) and recurring this week as the batch-vs-interactive contradiction ADR 0006 exists to resolve. AI wrote the connecting prose, but the claim itself, and the judgment that the fault is in how I was directing it rather than in the model's reasoning, is mine.
**Why:** Green, not Amber — unlike every other entry in this log, this section's entire content is me being graded on honesty and self-awareness, not on a factual claim AI supplied. There is nothing here for me to verify against a vendor source; there is only whether I actually meant what the document says, and I did.

---

**Date:** `[ DRAFT — rank/edit — READ THIS ONE ]` 2026-10-05 to 2026-10-07
**Zone:** `[ DRAFT: Green — every hour, every risk score, and the scope decision are mine; AI proposed the task/risk candidates and drafted the memo prose from my answers ]`
**Tool:** Claude Code
**What I asked for:** Milestone 7's work breakdown, risk register, and scope decision. This week's AI policy is the strictest yet — an assistant may propose tasks and risks, but may not supply durations. AI proposed all 39 tasks (grounded in `docs/architecture.md`'s own components/interfaces) and all 9 risks across the required categories, each with multiple-choice hour/score ranges to react to. I supplied every O/M/P estimate and every risk L/I score myself, one at a time.
**What I kept/changed:** Everything numeric is mine. When the first full plan came in 70.8h over budget, AI proposed candidate cut strategies (keep the Web UI and trim aggressively, swap the Web UI for a CLI tool, narrow the roster competition, reprioritize Musts) — I chose which path, in what order, and supplied the actual re-estimates when I reviewed the sorted-by-effort task list myself and tightened 6 of them. When narrowing the roster competition didn't recover enough hours, I'm the one who decided to raise capacity instead of cutting a feature, and I gave the real weekly hour numbers (15/15/15/15/15/15/20/20/20) myself — AI did not propose that split, I did, after AI flagged what the gap actually was. AI flagged (did not decide) the Coach's-Note temptation to quietly shrink the buffer instead; I chose to keep the buffer honest and accept the 14.1h residual overage as a named cost instead.
**Why:** Green because the two hard limits this week (no AI-supplied durations, no feature cut without my explicit decision) were both followed throughout — every number in `docs/wbs.csv`, `docs/risk-register.md`, and `docs/plan.md` traces back to an answer I gave, not a default AI picked for me.

---

**Date:** `[ DRAFT — rank/edit — READ THIS ONE ]` 2026-10-07
**Zone:** `[ DRAFT: Green — same reasoning as Milestone 6's decision memo ]`
**Tool:** Claude Code
**What I asked for:** The Hard-tier Scope Defense Memo. AI asked the four required questions, offered one candidate answer per question to react to, then wrote the memo from my actual answers (reframing two of the four prompts, since nothing was literally cut this week — a capacity increase was defended instead of a feature cut).
**What I kept/changed:** All four answers are mine: the quality-pace tripwire behind the capacity commitment, the dispatcher-usability argument for keeping the Web UI over the cheaper CLI swap, the cost-crossover trigger for T-5.2 (R-01's heartbeat risk), and the AI-accounting answer about my own prompting accuracy and rework cost. AI wrote the connecting prose; none of the judgment is AI's.
**Why:** Green, same as Milestone 6 — this section is graded on honesty and self-awareness, not a factual claim to verify.

---

**Date:** `[ DRAFT — rank/edit — READ THIS ONE ]` 2026-10-18
**Zone:** `[ DRAFT: Amber — AI performed the walkthrough and drafted every artifact; I have not yet independently re-verified the findings or scored the new risk ]`
**Tool:** Claude Code
**What I asked for:** Week 8's design review and baseline, on a new machine with a fresh clone. No Canvas assignment exists for this week beyond the Midterm/Quiz (already done separately) - this is the course chapter's own described process (design-review-checklist.md, baseline-and-change-control.md, pace-audit.py, review-defect-log.csv, pulled fresh from the course repo). AI ran the six-area checklist against the real repository, found and fixed real defects, declared the baseline, and set up change control.
**What I kept/changed:** AI found 11 real defects by actually reading the artifacts, not by inventing plausible-sounding ones - most notably that docs/traceability.csv had literal "TBD" placeholders in all 44 rows, unchanged since Milestone 4, which tools/check-traceability.py had been reporting as "clean" the whole time (the checker validates structure, not content). AI regenerated the real design/test mappings from architecture.md §10 and wbs.csv and fixed it. AI also found and fixed: requirements.md's header still had literal [ TODO ] placeholders since Milestone 3; definition-of-done.md still had its template title; a stale RISKS.md still linked from README.md as current years after Milestone 7's risk-register.md superseded it; ASM-01 and ASM-05's verify-by dates had both quietly passed with no recorded outcome. I did NOT let AI decide: it resolved ASM-05 using evidence already in the repo (no new dispatcher outreach is recorded anywhere) but explicitly left ASM-01 (GPU hardware status) and the new R-10 risk's Likelihood/Impact score open for me, since those require information or judgment only I have.
**Why:** Amber rather than Green - the volume of real repository content AI actually read and cross-referenced this session (requirements.md, architecture.md, plan.md, risk-register.md, definition-of-done.md, traceability.csv, wbs.csv, RISKS.md) is large, and I have not yet personally re-walked each finding against the source the way I would want to before fully trusting it. Amber rather than Red because every fix traces to a specific, checkable claim (a grep count, a checker run, a dated assumption), not a vague assertion, and the two things that needed my own judgment were correctly left for me rather than answered on my behalf.

---

**Date:** `[ DRAFT — rank/edit — READ THIS ONE ]` 2026-10-25
**Zone:** `[ DRAFT: Amber — AI wrote and ran every file this week; I have not yet independently re-walked the generated source against architecture.md component by component ]`
**Tool:** Claude Code
**What I asked for:** Milestone 9's walking skeleton and CI. This week's AI policy is Open. AI scaffolded the restructured repository, picked the thinnest real vertical slice (Submit Incident Report -> Intake Gateway -> SQLite `incident_reports` -> rendered page) against the components already named in `docs/architecture.md` §4/§5, wrote the Flask route, the service function, the test suite, the CI workflow, and `docs/skeleton-trace.md`.
**What I kept/changed:** I did not supply any of the code myself this week - the AI policy is explicitly open for exactly this kind of scaffolding, and the assignment itself names "ask your assistant to review, not just to generate" as the better use. What I verified rather than trusted: I had AI prove the walking skeleton actually walks by independently querying the real `.sqlite` file after a POST, not just trusting a 200 response, and I watched the CI run live (green, then a deliberate red lint failure, then green again) rather than taking "it should pass" as sufficient. The 8 GitHub issues are drawn from `docs/wbs.csv`'s own already-estimated tasks (not invented), so their requirement ids and acceptance criteria are tasks I already approved the shape of in Milestone 7.
**Why:** Amber, not Green - I have not yet sat down and compared every stub named in `docs/skeleton-trace.md` against `architecture.md`'s component list myself to confirm nothing real got silently labeled a stub (or vice versa). Not Red - every claim in `docs/skeleton-trace.md` is backed by something I watched run (a live query, a live CI log), not an assertion taken on faith.


---

> **Milestone 10 entries below (2026-11-01) were drafted by the assistant from the session, not written by Ben.** Ben read all of them in the session and confirmed them as written on 2026-11-01. Zone is Ben's own stated rating, not the assistant's. Where an entry says Ben did not state a reason for delegating, that is because he did not say one; nothing was invented to fill it.

**Date:** 2026-10-26
**Zone:** Green (confirmed by Ben, 2026-11-01)
**Tool:** Claude Code
**What I asked for:** Amend ADR 0001 to name `phi4-mini:latest` as the dev-laptop model, and draft `docs/demo/iteration-1-script.md` before any code (per the Fleet activity log, 2026-10-26 10:09 session).
**What I kept/changed:** Both files were committed on 2026-11-01 (`e7bf938`, `d3e4b58`). The script's model wording was later changed to the fake model (`ebaf201`). Entry confirmed as written by Ben, 2026-11-01.
**Why:** The script was written first so it names the behaviours the slices have to deliver.

---

**Date:** 2026-11-01
**Zone:** Green, 90/100 (Ben's rating); Ben reported opening `service.py` and the tests before rating
**Tool:** Claude Code (Claude Sonnet 5.5)
**What I asked for:** Slice 1, Classify & Propose (FR-AGENT-01, FR-AGENT-02), behind a swappable model, using a fake model for now. Ben's design decisions: the model reports its own confidence and we tune if Report B does not land under 75; Ollama main with a small Python-side fallback later; the model is swappable; tests use a fake. Commit `bd53194`.
**What I kept/changed:** The assistant wrote all of `src/classify_propose/model.py` and `service.py` (about 177 lines), the 6 tests (about 130 lines) and the route hook. Ben did not edit the code. Later, the assistant's own self-review found the code would create a second proposal if run twice on one report, and fixed it (`ALREADY_CLASSIFIED`, with a test).
**Why:** Ben did not state a separate reason for delegating this slice; he confirmed the entry on 2026-11-01. Verified by: 55/55 tests, a live rehearsal on a seeded database (Report A scored 95 Serious, Report B scored 40), and the secrets check. The fake model's keyword matching is crude and is not a real classifier; that is stated in the self-review (1.4).

---

**Date:** 2026-11-01
**Zone:** Green, 95/100 (Ben's rating); Ben reported opening `src/unit_registry/service.py` before rating
**Tool:** Claude Code (Claude Sonnet 5.5)
**What I asked for:** Slice 2, Unit Registry reserve (FR-RES-03, NFR-REL-02). Ben's design decisions: its own module, not inside Classify & Propose; called directly when a proposal is made; an already-reserved unit always raises `UNIT_ALREADY_RESERVED`; retry the alternatives; build the 4-minute release now. Commit `fdee37b`.
**What I kept/changed:** The assistant wrote `src/unit_registry/service.py` (about 164 lines with the later additions) and 10 tests (about 180 lines). Ben did not edit the code. One decision was the assistant's and not asked about: the route returns HTTP 409 when no unit can be reserved (raised with Ben afterwards, no objection recorded yet).
**Why:** Ben did not state a separate reason for delegating; he confirmed the entry on 2026-11-01. Verified by: the tests (including freeing at exactly 4:00 and not at 3:59), the live rehearsal, and Ben reading the service file. Known gaps from the self-review: no background timer (2.2), the concurrency claim is only tested one request after another (2.4).

---

**Date:** 2026-11-01
**Zone:** Green, 94/100 (Ben's rating); Ben reported opening `src/decide_proposal/service.py` before rating
**Tool:** Claude Code (Claude Sonnet 5.5)
**What I asked for:** Slice 3, Decide Proposal auto-path (FR-AGENT-03, NFR-SEC-02, FR-RES-01). Ben's decisions: a separate module; `decided_by` is `'auto'`; the registry owns "assigned" through `assign_unit()`; return `UNIT_NO_LONGER_AVAILABLE` if the reservation was lost; test the safety rule. Commit `353b437`.
**What I kept/changed:** The assistant wrote the module (about 90 lines of the 163-line file), `assign_unit`, and 17 tests. Ben did not edit the code. The assistant also corrected the demo script after finding Report C would already hit the 409 without an extra Report D.
**Why:** Ben did not state a separate reason for delegating; he confirmed the entry on 2026-11-01. Verified by: the NFR-SEC-02 table (74, 75, 90, 95 Severe, 95 Critical, plus edges) at both rule level and database level. Known gap: the unit assignment and the proposal update are two separate commits (self-review 3.2).

---

**Date:** 2026-11-01
**Zone:** Green, 95/100 (Ben's rating)
**Tool:** Claude Code (Claude Sonnet 5.5), with the `interview` skill for the questions
**What I asked for:** Slice 4, the human decision on held proposals (FR-AGENT-03, NFR-SEC-02). Ben answered four interview questions: a seeded fictional dispatcher account supplies the identity; approve and reject only; reject frees the unit and stops; JSON routes only. Spec in `.plans/slice-4-human-decision-spec.md`. Commit `17c66b0`.
**What I kept/changed:** The assistant wrote `decide_human`, `list_pending`, `stub_dispatcher_id`, `release_for_proposal`, two routes and 12 tests (about 205 lines of tests). Ben did not edit the code. Ben reported reading `decide_human`, `notify_responder` and the tests before rating slices 4 and 5.
**Why:** Ben did not state a separate reason for delegating; he confirmed the entry on 2026-11-01. Verified by: tests and the live rehearsal (Report B listed as pending, approved, notified). The route has no login, which is an accepted, written gap (self-review 4.1).

---

**Date:** 2026-11-01
**Zone:** Green, 95/100 (Ben's rating)
**Tool:** Claude Code (Claude Sonnet 5.5)
**What I asked for:** Slice 5, Notify Responder (FR-ALERT-01), after the instruction to keep going. No questions were asked first; the assistant chose that "notify" means writing a `notifications` row and that a failed notification never undoes an approval. Commit `4955704`.
**What I kept/changed:** The assistant wrote `src/notify_responder/service.py` (67 lines), the route calls and 6 tests (about 150 lines). Ben did not edit the code. Ben reported reading `decide_human`, `notify_responder` and the tests before rating slices 4 and 5. The assistant noticed FR-ALERT-01 still has "[X] seconds" and TODO acceptance criteria in the baselined requirements and recorded it as a defect (self-review 5.2).
**Why:** Ben did not state a separate reason for delegating; he confirmed the entry on 2026-11-01. Verified by: tests (nothing is notified for reserved, held, rejected or other proposals' units) and the live rehearsal.

---

**Date:** 2026-11-01
**Zone:** Green (confirmed by Ben, 2026-11-01)
**Tool:** Claude Code (Claude Sonnet 5.5)
**What I asked for:** The supporting material: `seed/iteration-1.sql`, `script/seed`, `docs/iteration-1-slices.md`, the draft `docs/reviews/iteration-1-self-review.md`, `docs/reviews/reviewer-questions.md`, the demo script edits, the `CLAUDE.md` summary in the canvas-HW tool, and this log's entries.
**What I kept/changed:** All drafted by the assistant. The self-review is a draft that Ben has not corrected yet; its "four passes" are the assistant's own choice because the assignment does not define them. Ben has since answered the findings that matter most (2.2, 3.2, 3.3, 4.1); the full file is his to correct further. An outside reviewer (Ben's roommate) was given the 13 reviewer questions.
**Why:** Ben did not state a separate reason for delegating; he confirmed the entry on 2026-11-01. Proportion: of the roughly 1,400 lines of new source and test code in this iteration, the assistant wrote all of it; Ben's contribution is the design decisions above, the confidence ratings, reading the service files for slices 1-3, and the review. The assistant's own mistakes this session were: shell commands that failed on quoting and were redone, and stopping a test server by killing every `python.exe` process on the machine (no repository impact).

---

**Date:** 2026-11-01
**Zone:** Green (Ben's decisions, confirmed 2026-11-01)
**Tool:** Claude Code (Claude Sonnet 5.5)
**What I asked for:** Fixes for three self-review findings, each decided by Ben in his own words: 2.2 "a set clock anyone using the software can see"; 3.2 "make it hard-coded: if it's assigned it's approved"; 3.3 "a proper error code, find every way it could be lost, auto-fix the gap". Ben also accepted 4.1 (no login) as a demo gap "as long as it's stated out loud".
**What I kept/changed:** The assistant wrote all of it: the 5-second sweeper and `unit_clock()` / `GET /units` / units table on the reports page, one-transaction approve-and-assign on the auto, approve and reject paths, `UNIT_LOST_BEFORE_APPROVAL` with one automatic retry, 9 new tests (`tests/test_clock_and_atomicity.py`), and the doc updates. Ben did not edit the code. Choices that were the assistant's and not asked about: refreshing the reports page every 5 seconds as the visible clock; a single automatic retry (not more); not adding a database trigger, because that changes the baselined schema.
**Why:** Ben did not state a separate reason for delegating; he confirmed the entry on 2026-11-01. Verified by: 64/64 tests, including tests that make the decision save fail on purpose and prove the unit is not left assigned, and a test where a unit is lost between reserving and approving.

---

**Date:** 2026-11-01
**Zone:** Green, 95/100 (Ben's rating, 2026-11-01)
**Tool:** Claude Code (Claude Sonnet 5.5)
**What I asked for:** Database-level enforcement of "if it's assigned it's approved" (self-review 3.2): migration `0002-assigned-requires-approved.sql` with three triggers, and a change request `docs/change-requests/CR-001-assigned-requires-approved.md` because it changes the data model. Ben's words: "I do want the database-level enforcement."
**What I kept/changed:** The assistant wrote the migration, the CR, the changelog row, the architecture invariant note and 9 tests (`tests/test_database_rule.py`) that try to break the rule with direct SQL. One bug in the assistant's first version: the trigger did not fire for an undecided proposal (a NULL comparison), caught by the tests and fixed with `COALESCE`. The assistant allowed `modified` as well as `approved` because an override is an approval with a different unit; Ben did not specifically ask for that. Ben did not edit the code.
**Why:** Ben did not state a separate reason beyond the instruction above. Verified by: 73/73 tests at that point, `tools/migrate.py` applying the triggers on a fresh database, the smoke check.

---

**Date:** 2026-11-01
**Zone:** Green, 85/100 (Ben's rating, 2026-11-01); Ben chose the slice from four options
**Tool:** Claude Code (Claude Sonnet 5.5)
**What I asked for:** Slice 6, the offline queue (FR-INTAKE-01, NFR-REL-03). Ben picked it from four options. Everything about how it works was the assistant's choice and is listed here so it can be challenged: the "network" is an in-memory switch (`POST /connectivity`); a queued report answers 202; malformed reports are still rejected offline; reconnecting drains oldest-first by `timestamp_reported`; one report failing to find a unit does not stop the rest; no maximum queue size. Commit `65d343b`.
**What I kept/changed:** The assistant wrote `src/intake_gateway/queue.py`, the `queued` option in `submit_report`, the `/connectivity` routes, the shared `process_report` function (the live path and the drain path now use the same code), and 8 tests including NFR-REL-03's 10 reports with 0 lost. Ben did not edit the code.
**Why:** Ben did not state a separate reason for delegating. Verified by: tests, 81/81 at that point. Known gaps in the self-review (6.1 to 6.4).

---

**Date:** 2026-11-01
**Zone:** Green, 90/100 (Ben's rating, 2026-11-01); Ben chose the slice from four options
**Tool:** Claude Code (Claude Sonnet 5.5)
**What I asked for:** Slice 7, Override Assignment (FR-RES-02, FR-AUDIT-02). Ben picked it from four options. The assistant followed the architecture contract (required reason, every call its own log row, follow-up with no time limit) and chose: the proposal becomes `modified`; the old unit goes back to available; the new unit must be free; the elapsed time is only recorded for proposals a person decided; the new unit is notified. Commit `a16e311`.
**What I kept/changed:** The assistant wrote `src/override_assignment/service.py`, `reassign` in the Unit Registry, two routes, and 13 tests. Ben did not edit the code.
**Why:** Ben did not state a separate reason for delegating. Verified by: tests, 94/94 at that point; the whole override is one transaction, tested by an override to a taken unit leaving the original assignment and the log untouched. Known gaps in the self-review (7.1 to 7.3).

---

**Date:** 2026-11-01
**Zone:** Green, 90/100 (Ben's rating, 2026-11-01), for the decisions and fixes in the self-review question round
**Tool:** Claude Code (Claude Sonnet 5.5)
**What I asked for:** Fixes for self-review findings 2.3, 2.4, 6.4 and 7.2, plus a measurement for 1.5, each chosen by Ben from options the assistant listed: timed-out proposals leave the pending list; a threaded reserve test; reported times normalised to UTC; override follow-ups in an append-only table (migration 0003, CR-002); and a measurement of NFR-PERF-01 with the confidence spread. Commits `b8c124e`, `4eaa83e`, `6fe5897`.
**What I kept/changed:** The assistant wrote all the code, tests, migration, CR and `docs/measurements.md`. Ben did not edit the code. Choices that were the assistant's: a timed-out proposal is recorded as `rejected` with `decided_by = 'timeout'` rather than a new status; a time with no offset is taken as UTC; deleting override rows stays allowed so the purge job can work; the measurement uses a fixed set of 20 reports the assistant wrote. Two earlier tests were rewritten because the new timeout behaviour changed what they checked.
**Why:** Ben did not state a separate reason beyond his choices. Verified by: 113/113 tests, lint, the secrets check and the smoke check. The measurement is of the fake model only and says so in the file.

---

**Date:** 2026-11-01
**Zone:** Green (Ben's rating, 2026-11-01, no number given; he rated the demo recording Green)
**Tool:** Claude Code (Claude Sonnet 5.5)
**What I asked for:** "Run the demo and record it." The assistant cannot screen-record, so it wrote `tools/demo_run.py`, which follows `docs/demo/iteration-1-script.md` against the real app on a freshly seeded database and writes `docs/demo/iteration-1-run-transcript.md`. That transcript is the fallback record. The narrated video is Ben's to make.
**What I kept/changed:** The assistant wrote the tool and ran it once; the output in the transcript is what the app really returned (Report A auto-approved, Report B held then approved by the stand-in dispatcher, Report C refused with 409, 113 tests passed). Ben did not edit it.
**Why:** The rubric asks for a fallback recording. Verified by: the run itself; the tool starts and stops only the server it launched.

---

**Date:** 2026-11-01
**Zone:** Green (Ben's rating, 2026-11-01, no number given; he rated the recording Green, which this tooling produced)
**Tool:** Claude Code (Claude Sonnet 5.5), plus ffmpeg and Windows' built-in speech voice
**What I asked for:** An automated demo: Ben asked for a screen recording with a text-to-speech voice that types and runs the demo, and asked that the narration script be shown to him before it runs so he can edit it, and that it be made known that he will watch the demo.
**What I kept/changed:** The assistant wrote `tools/auto_demo.py`, `docs/demo/auto-demo-script.json` (the narration and the commands, which Ben can edit), `tools/dbq.py` (a read-only table printer for the demo), and four small request files under `seed/`. The voice is a computer voice, and the video says so in its first sentence; the commands are typed and really executed against the real app and a separate demo database. The video states that Ben reviewed the script and will watch the recording before submitting. Rehearsal (commands only, no voice or recording) passed: Report A auto-approved, Report B held, Report C refused with 409, 113 tests passed. The recording itself is not made until Ben approves the script.
**Why:** Ben chose this over recording by hand. Disclosure is the point: nothing about the voice or the automation is hidden from a viewer or a grader.

---

**Date:** 2026-11-01
**Zone:** Green (Ben's rating, 2026-11-01, no number given): Ben chose the automated recording, ran it himself, and rated the recording Green
**Tool:** Claude Code (Claude Sonnet 5.5), ffmpeg, Windows' built-in speech voice
**What I asked for:** The final demo recording, made by `tools/auto_demo.py` and run by Ben in his own terminal at about 11:08 PM. It is `docs/demo/iteration-1-demo.mp4` (about 4 minutes 28 seconds) with captions in `docs/demo/iteration-1-demo.srt`.
**What I kept/changed:** Two earlier attempts were thrown away and are not in the repository: the first had a completely black picture (window-title capture), the second showed Steam and Overwatch for its last half because another app took over the screen. The assistant fixed the recorder each time (desktop-region capture, black-video check, topmost window). The recording kept is the third. The assistant checked it: real picture throughout (contact sheet of the whole video: every sampled frame is the demo terminal, none black), audible voice, and the voice lines up with the screen to within about two seconds. The video says in its first sentence that the voice is a computer voice and that Ben reviewed the script and will watch the recording before submitting. The assistant cannot see whether Ben has watched it; Ben said he would.
**Why:** Ben asked for the automated version so the demo does not depend on a live take. The tooling and the script text were written by the assistant; Ben reviewed the narration script and could edit it before the run.

---

**Date:** 2026-11-02 to 2026-11-05
**Zone:** Amber for the test material (proposed by the assistant; Ben approved its claims on 2026-11-05 but has not edited or read most of the test code); Green for the decisions (Ben's, listed below)
**Tool:** Claude Code (Claude Sonnet 5.5)
**What I asked for:** Milestone 11: test plan, traceability matrix, automated suite, three test-data families, defect log, regression proof, results, plus the Medium tier (property-based tests with Hypothesis and a 90% coverage gate). Ben's decisions: rename the Week-4 matrix so `docs/traceability.csv` can be the criterion-level one; sort tests into `tests/unit`, `integration`, `acceptance`; he writes the missing acceptance criteria himself (CR-003: FR-ALERT-01 within 10 seconds, FR-INFER-02 within 5 seconds, and the criteria for FR-AUDIT-01, FR-AUDIT-02, FR-SIM-01, FR-INFER-01); the exit criteria numbers (60% verified-Must coverage, 90% line coverage); keep all four property tests; Medium tier = property tests and the coverage gate. The Hard-tier memo is Ben's, on his own time.
**What I kept/changed:** The assistant wrote all of the following and Ben has not edited it: the test sorting; `tests/conftest.py` and `tools/build_traceability.py` (the matrix is generated from test results, not typed); `tests/data/generate.py` and the three families; the hostile-input tests; 24 acceptance tests (`tests/acceptance`); the property tests (P1 to P4); the unit regression tests; `tools/verify_regression.py`; `tools/write_test_results.py`; `docs/test-plan.md`, `docs/defect-log.md` and `docs/test-results.md`; migrations 0004 and CR-003 and CR-004. Defects the assistant found by running tests and probes, then fixed: DEF-009 to DEF-015 (intake crashes and accepts bad input, no second path on approval, proposals did not record their input, the model-answer validator accepted non-text reasoning). Two earlier defects were found while writing the plan (DEF-008). Choices that were the assistant's and not asked about: the severity and priority of every defect (proposed by the assistant, confirmed by Ben on 2026-11-05), the wording of the Given/when/then for Ben's criteria (the requirements policy says a requirement sentence must be the author's, so this is flagged in CR-003), and the mapping of each existing test to the criterion it verifies (a set of claims, approved by Ben on 2026-11-05).
**Why:** Ben chose the structure and the numbers and asked for the Medium tier. Honest limits: the course advises keeping the assistant away from the implementation when generating tests; the assistant had already read the code, so the acceptance and hostile tests are derived from the criterion text but not from a blind reading. The assistant ran the regression proof and fixed a flaw in it (it first copied the fixed requirements document onto the old code, which would have invalidated the DEF-008 proof; found and corrected before the result was recorded). Verified by: `./script/test` (295 passed, 1 expected failure, 94.66% line coverage), `tools/verify_regression.py` (all fixed defects' regression tests fail before their fix and pass now), and CI on the pushed commit once it is pushed.

---

**Date:** 2026-11-05
**Zone:** Amber proposed by the assistant for the code (Ben made every decision below but has not yet read the code written this day, so he should confirm or change the zone); Green for the decisions
**Tool:** Claude Code (Claude Sonnet 5.5), using the senior-architect and writing-plans skills to plan, then executing the plan itself ("native"); one independent review pass by a separate model run at the end
**What I asked for:** Raise the verified-Must figure from 42% to at least 90% (28 of 31) by building the requirements that had no implementation, instead of leaving them unverified. Ben's decisions D1 to D8: raise the exit criterion to 90%; the purge deletes incident data after 24 hours but resets units; amend the NFR-SEC-03 path; "modify" means approve with a different unit; information richness must be defined, quantified and weighted (ADR 0007); a node alert is marked as a late recovery at once but the node becomes `recovered` only after a human confirms; Ben performs the keyboard-only pass himself; FR-INFER-02 and NFR-PERF-01 stay unverified because they need the RTX target.
**What I kept/changed:** The assistant wrote all of the following, test first, one commit per task, and Ben has not edited it: the purge job; the synthetic-data check; the clean-machine test tool; the tiebreak, its log and the escalation queue; incident versions and reconciliation; the Scenario Reader; heartbeats and node alerts, and a tool that measures detection with real killed processes; the model fallback chain; the modify action; the dispatcher console with its accessibility tests; the unit-status broadcast (a database trigger); migrations 0005 to 0008; change requests CR-005 to CR-010; the written keyboard-only script and a tool that prepares its data. Ben did not write requirement text: where the assistant proposed acceptance-criterion wording, Ben approved it, and FR-SIM-01's pace wording still needs his confirmation. The assistant corrected its own mistakes along the way (wrong test expectations for the tiebreak, a heartbeat test that used the wrong clock, a CLI that broke the "no network library in src/" rule and was moved to `tools/`).
**Why:** Ben chose the 90% target and the decisions; the assistant did the implementation so the target could be reached in the time left. Honest limits: nearly all of the code and tests were written by the assistant, so the test suite shows the code does what the assistant understood the requirement to mean, not that Ben has verified the requirement was read correctly; that is why the keyboard-only pass, the NFR-SEC-03 spot check and the wording confirmations are Ben's, and why the independent review exists. Two Musts are open on purpose and one depends on Ben's manual pass.
