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