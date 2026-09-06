# AI Usage Policy & Log

> I will use AI to perform actions I already understand how to do, but would like to focus on other aspects of the project. 
---

## Spine rule

If I can't describe what, why and how the AI is supposed to perform the action, I shouldn't have it do it.

## Zones

| Zone | Meaning | Examples |
|---|---|---|
| 🟢 Green | `[ can describe why I delegated ]` | `[ I delegated Claude to, grab a live map API I have found so I can pull in real time maps into my project.]` |
| 🟡 Amber | `[ I might have trouble fully completing it myself] I had AI complete it with only partial knowledge of why]
| 🔴 Red | `[I had not clue what I was doing] I had AI do whatever it thought was best without reviewing it.

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

**Date:** `[ DRAFT — rank/edit ]` 2026-09-06
**Zone:** `[ DRAFT: Green ]`
**Tool:** Claude Code
**What I asked for:** Run a real OSMnx dependency spike (install, geocode test, build a real road graph for Macomb IL, route between two real businesses)
**What I kept/changed:** Kept the actual results as evidence (graph size, route distance/time); no interpretation was handed to me beyond "pass/fail," which I still have to confirm I agree with
**Why:** Mechanical technical execution with a clearly describable task and objective pass/fail result