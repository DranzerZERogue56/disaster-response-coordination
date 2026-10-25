# The Skeleton Memo

To whoever inherits this project in Week 16 (most likely: me, with less context than I have right now).
From: Dranzer Rogue · 2026-10-25 · Milestone 9, Hard tier

This memo exists because Week 16 me will not remember why Week 9 me made these calls. Five decisions, each one mine.

---

## 1. What I stubbed, and why

The walking skeleton proves one seam: a browser or `curl` talks to Flask, Flask calls the Intake Gateway, the Intake Gateway writes a real row into SQLite, and the row comes back out rendered. That's it. Everything else `docs/architecture.md` eventually needs is a labeled stub. Here's each one, what it would have cost to make real this week, and why I didn't:

| Stub | Cost to build this week (from the Week-7 WBS, `docs/wbs.csv`) | What I did instead | Becomes real |
|---|---|---|---|
| LLM Generate / Classify & Propose (Ollama) | T-2.1a + T-2.2 + T-2.3 ≈ 7-18.5h (O/M/P summed) | Nothing calls Ollama yet | Milestone 10 (issue tracking T-2.1a, T-2.2, T-2.3) |
| Offline queue (FR-INTAKE-01's queued path) | T-3.2 ≈ 3-9h | Every report is created immediately; no queue exists | Milestone 10 (issue tracking T-3.2) |
| Resource/Unit Registry reserve/release | T-5.1 ≈ 2-5h | No unit reservation happens anywhere | Milestone 10 |
| Decide Proposal / Approval Gateway | T-6.2 ≈ 2-4h | No proposal exists yet to decide on | Milestone 10 |
| Dispatcher auth (FR-AUTH-01) | T-7.4 ≈ 2-4h | Intake route is unauthenticated, matching the real contract (intake *is* unauthenticated by design) | Milestone 10, with Decide Proposal's interactive path |
| Scenario Reader / Play Scenario | T-3.4 ≈ 3-8h | No scripted scenario playback | Milestone 10 |

The tradeoff: building any one of these this week would have cost real hours *and* broken the point of a walking skeleton, which the assignment itself names as the first trap — "scope creep disguised as enthusiasm." The Ollama path alone is 7-18.5h by my own Week-7 estimate; spending that now, before the seam itself was proven, would have meant discovering an architecture mistake *after* already investing in the reasoning layer, not before. I'd rather find out the seam is wrong when the cost of being wrong is one afternoon, not two weeks.

## 2. What the skeleton proved, and what it disproved

Nothing broke. The real SQLite table (`migrations/0001-initial.sql`) and the real interface contract (`docs/architecture.md` §5, Submit Incident Report) matched what I built exactly — same field names, same required-field list, same error shape. I didn't have to change one column name or one field to make the slice work.

That's suspicious in exactly the way my own Milestone 8 design review warned about: "a specification that survives first contact perfectly is either excellent or untested." I think it's the second one, honestly, more than the first. The slice I built is the *easiest* hop in the whole system — plain CRUD against a table I already fully specified in Week 6, with no concurrency, no LLM nondeterminism, no negotiation protocol. I'd know I was wrong to feel confident here if the *next* hop — Classify & Propose, which touches Ollama, a process I don't control the timing of — also went in without a single surprise. I'm not betting on that. If T-2.1a comes in clean against its 3-5-7.5h estimate too, then I'll believe the spec is genuinely solid rather than just untested in the hard places yet.

## 3. The re-estimate

This is a rough comparison, not a WBS-task comparison, and I want to say that plainly rather than dress it up as more rigorous than it is. This week's work (repo restructure, CI, the intake slice) was never itemized as its own line in the Week-7 WBS — it's course-required Milestone 9 infrastructure that sits outside `docs/wbs.csv` entirely. So instead of picking three WBS tasks I haven't actually built yet, I'm comparing my own gut estimate going in against what it actually took:

- **Estimated:** 7 hours
- **Actual:** 5 hours
- **Correction factor:** 5/7 ≈ **0.71** — I ran *under*, not over.

That's the opposite direction from what R-07 (optimism bias) worries about, and I don't trust it enough to loosen anything. Two reasons: first, it's one data point against an estimate I made for a task type I'd never scoped before, which is exactly the condition R-07's own trigger (needing several data points, not one) exists to guard against. Second, and more honestly — this week landed in a stretch where other coursework and exams ate into my available hours, so "came in under" might partly be "had less time and compressed the work" rather than "the work itself was faster than expected." I can't fully separate those two explanations from one data point, so I'm not applying this factor to the remaining plan at all.

What I *am* flagging instead: the real threat to Week 16 isn't pace, it's hours availability. `docs/risk-register.md`'s R-06 (schedule/personal — illness or unavailability with no substitute) already covers this, but "other coursework and exams compete for project hours" is a more concrete, more likely trigger of R-06 than the generic "illness" framing that risk was written around. I'm not opening a new risk for this — R-06's response (the declared buffer absorbs it) and contingency (trigger the scope-decision table if a loss exceeds the remaining slack) already fit. I'm noting here that I expect R-06 to get exercised for real reasons, not hypothetical ones, in the next few weeks, and I should watch it rather than assume it stays quiet.

## 4. The build-failure policy

If `main` goes red on a Tuesday night in Week 12: if nothing else in flight depends on main being green that night, I let it sit red overnight and fix it first thing at my next work session, rather than dropping whatever else I'm doing to chase it immediately. I'm not pretending this is the maximally disciplined answer — the Normal-tier submission note above states "say red when it is red," and I mean to keep doing that honestly rather than rushing a bad fix at 1 a.m. to make the badge green before I've actually diagnosed the problem. The one condition that overrides this: if something *else* I need to build depends on main being green (a migration, a dependent branch), then it stops being "nothing's blocked" and I fix it immediately instead.

Signed, 2026-10-25.

## 5. The AI accounting

Nothing specific stood out to reject this session, and I want to be honest about what that actually means rather than claim it as a clean bill of health. My review process this week was mostly *execution-based*, not *reading-based* — I had Claude prove the walking skeleton worked by querying the real SQLite file after a POST, watched the CI run go green → red (on purpose) → green on the actual GitHub Actions logs, and ran the secrets scan against a planted fake key to confirm it actually fails. That's real verification, not blind trust. But it's verification that something *works*, not verification that I've read and understood every line of `src/intake_gateway/service.py` or `src/web_ui/app.py` closely enough to say I'd have written it the same way. Running the tests catches "does it work." It doesn't catch "would I have made the same design call," which is the thing this accounting question is actually trying to surface. That's the honest gap: I reviewed by running it, not by reading it line by line, and I should go back and do the second kind of review before I lean on this code much further.
