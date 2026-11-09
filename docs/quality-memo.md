# Quality Judgment Memo

<!--
HOW TO USE THIS FILE
- Everything in an HTML comment like this one is a guide for you. It does not show when the file is read as Markdown,
  but DELETE every comment before you commit so the grader reads only your words.
- The assignment: 2 to 3 pages, addressed to the engineer who will inherit this project, four sections, each answering a
  question you cannot look up. Graded on judgment, specificity and candor. A memo that says everything went well earns
  nothing; a memo that names a real weakness and defends a real tradeoff earns full marks, even when the tradeoff is
  uncomfortable.
- Write it yourself, in your own words. Do not paste text from the assistant or any other AI: the memo is the one document
  in this milestone that is supposed to be you owning decisions. First person ("I chose...") is right.
- Keep a number or a file name in almost every paragraph. "Specific" beats "thorough".
- Roughly 2 to 3 pages is about 700 to 1,100 words. Four sections, so about 200 to 275 words each.
-->

**To:** the engineer who inherits this project
**From:** Ben (Dranzer Rogue)
**Date:** 11/7/2026
**Re:** Milestone 11, what the tests say, and how far to trust the build

<!-- A two or three sentence opening is enough: what this memo is, and the one sentence you most want the reader to remember. Write it LAST, after the four sections. -->
This memo is about the Disaster Response Coordination project and what its tests tell you about the build. If you remember one thing from it, remember this: my inexperience caused real problems in this project, but I put real effort into a big, ambitious problem. I built it to help people make response plans, first as a way for dispatchers to learn, and in the long run, I hope, as a real-time resource allocator for first responders.

---

## 1. Why these exit criteria


THE QUESTION (from the assignment): Why these numbers? Why is zero-open-S2 the right bar for your project and not
zero-open-S3? Name the user impact behind each threshold. Then state plainly whether you met them, and where you did not.

WHAT TO LOOK AT FIRST
- docs/test-plan.md, section 6: the six exit criteria. They are yours; you chose them.
- docs/test-results.md, the "Exit criteria ... checked against this build" table: which are MET and which MISSED.
- docs/test-plan.md, the note next to the first criterion: you raised verified-Must coverage from 60% to 90% on
  2026-11-05. Why did you raise it instead of keeping the lower bar? Was that a good call in hindsight?

THINGS TO TALK ABOUT (answer in your own words; these are prompts, not answers)
- For each threshold, who is the user that gets hurt if it is not met? (The dispatcher? The person waiting for a unit?)
  Why 90% and not 100%? Why do FR-INFER-02 and NFR-PERF-01 not count against you?
- Why is an open S2 unacceptable but an open S3 tolerable here? What would have to be true about the project for you to
  have drawn the line somewhere else?
- The miss: one criterion was MISSED. Which, and do you agree it should have been a miss? Say what you would tell the
  inheriting engineer about when that miss has to be fixed.
- Honesty check: a pass rate can be raised by building things or by weakening criteria. Which did you do, and how could a
  stranger tell?


## 2. What ships with known defects

THE QUESTION: For every open defect in v1.0, state the severity, the priority, the workaround, and (this is the part)
the user who is affected and why you decided their inconvenience is acceptable this semester. Write it as though they
will read it, because your Week 14 handoff guide means someone will.

WHAT TO LOOK AT FIRST
- docs/defect-log.md, summary table: filter the Status column for "Open" and "Will not fix". (Fixed ones are not this
  section's subject.) The list is short; count it before you write.
- For each open one, re-read its Severity and Priority lines. Severity is a fact about the product; priority is your
  decision. Where do they disagree, and why is that the right call?

THINGS TO TALK ABOUT
- One short paragraph or bullet per open defect: what the user would hit, the workaround, why it is acceptable now.
- DEF-018 (no login, S2) is the uncomfortable one: it is S2, and your own exit criterion says no open S2. Do not smooth
  that over. What is the real risk, who could be affected, what stops it from being worse today (the server only listens
  on 127.0.0.1), and what is the first thing the inheriting engineer must do?
- DEF-017 (notify only records a row) and DEF-019 / DEF-020 (no length limit; a 2099 timestamp is accepted): who is the
  affected user, and is "no requirement says" a good enough reason to leave them?
- Is there anything open that you would NOT be comfortable shipping to a real user, even though it is allowed to ship to a
  grader? Say so.


## 3. What I chose not to test, and what that costs


THE QUESTION: Every test plan has an out-of-scope section. Yours is a set of bets. Name the two you are least
comfortable with, describe the failure that would prove you wrong, and say what a successor should test first when they
pick this up.

WHAT TO LOOK AT FIRST
- docs/test-plan.md, section 2 (Out of scope), as amended on 2026-11-06. Read every row and ask, "if I am wrong about
  this one, what breaks, and for whom?"
- docs/test-results.md: the two Must requirements still unverified, and why.

THINGS TO TALK ABOUT
- Pick TWO rows and commit to them. Candidates a reader would expect you to weigh (you choose; do not pick because they
  are listed here): the real model (Ollama) never tested; the fallback chain's primary and smaller tiers only tested with
  simulated failures; nodes tested as processes on one machine, not across a network; no screen reader or second browser;
  no real notification channel; no login or CSRF.
- For each: the concrete failure that would prove you wrong ("if X happens in front of a real dispatcher, my bet was
  wrong"), and how likely you think that is.
- What should the successor test FIRST, and why that one?
- Be honest about how much of the suite was written against the fake model, and what that means for how much a green
  test run is worth.


## 4. My assistant's review burden


THE QUESTION: Report your assistant's review burden honestly. From Rep 10: out of ten generated test cases, how many
asserted the wrong thing, and what kind of wrong were they? Then draw the conclusion: at that error rate, what is the
fastest you are actually allowed to accept generated tests without reading every assertion? Cite docs/ai-usage.md.

IMPORTANT: THIS SECTION NEEDS A REAL EXERCISE FIRST
- "Rep 10" means: take ten test cases generated from the REQUIREMENT TEXT ONLY (not from the code), and judge each one
  yourself: did it assert the right thing? That exercise has not been done yet. Do not write this section from memory or
  from a guess. If you cannot do the exercise before the deadline, say plainly in this section that you did not, and
  report what you do have (see below), rather than inventing a count.
- How to run it: give the assistant ONLY the text of ten acceptance criteria from docs/requirements.md (no code, no
  repository), ask for one test case per criterion, then you read each assertion against the criterion wording and mark it
  right or wrong. Count them, and describe each wrong one: wrong threshold, tested the code's behaviour instead of the
  requirement, vacuous (cannot fail), wrong boundary, and so on.

WHAT YOU DO ALREADY HAVE, AS EVIDENCE (use it, but do not substitute it for Rep 10)
- docs/ai-usage.md: read the Milestone 11 entries. They say the assistant wrote nearly all of the tests AFTER reading the
  code, which the course warns against, and that you have not read most of the test code.
- docs/defect-log.md, defects found by the "independent review" (DEF-021 to DEF-028): a second model found problems the
  first one built in. What does that say about reviewing AI work with more AI?
- The review also found tests that claimed to cover a criterion without really doing so (see DEF-026 and DEF-027). That is
  a real example of "asserted the wrong thing"; decide whether it belongs here.

THINGS TO TALK ABOUT
- The count, and the kinds of wrong. Then the conclusion in terms of a rule: "at N out of 10 wrong I must read every
  assertion" or "at 1 out of 10 I can spot-check". State your actual rule and why.
- What you personally did and did not read this week. Candor is graded: write what is true.
- What you would change about how you use the assistant on the next project.


---

<
CHECKLIST BEFORE YOU COMMIT
[ ] Every HTML comment deleted.
[ ] Between 2 and 3 pages (about 700 to 1,100 words).
[ ] Each section contains at least one concrete number or file name.
[ ] You named a real weakness (not only strengths) in sections 1, 2 and 3.
[ ] Section 4 states a real Rep 10 count, or says plainly that the exercise was not done.
[ ] It reads like you. If a sentence sounds like a report from a consultant, rewrite it the way you would say it.
[ ] Then tell the assistant to commit it (the final commit message stays: milestone 11: test plan, suite, results, defect log).

