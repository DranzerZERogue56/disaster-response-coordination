# Idea Canvas — Candidate A

> **Content status:** the project concept, scope table, out-of-scope list,
> feasibility/technology analysis, and "one hard part" reasoning below came
> from a heavily-AI-assisted brainstorm, reviewed and adopted (see
> `docs/ai-usage.md`, 2026-09-06, Amber). The problem statement, interview
> evidence, feasibility-gate verdicts, hour numbers, and rejection
> paragraph are still genuinely `[ TODO ]` — real work, not yet done, and
> required to be in my own words per this milestone's AI policy.

**Candidate name:** Estate Contents to accurately inform Accounting
**Date started:** 2026-09-06   **Well it came from:** `[ TODO — declare this honestly; the candidate list originated in an AI brainstorming session, which is a different provenance than "hobby" or "work", but is used in my life as my grandfather recently died and this was a tool I resonated with]`

---

## 1. Problem statement

For              an person  managing a deceased relative's estate
who              has to inventory and value all personal property (furniture, collectibles, household goods) for the probate court's personal property accounting
the problem is   they have no fast way to identify what an item actually is or what it's worth, so they either guess low, pay for a full appraisal they can't afford, or spend weeks doing it by hand
which costs      probably 50 hours getting everything ready, then another 50 fine tuning the information for accuracy among items and handling the massive amount of data throughput for each video. (But so far no real cost)
Today they       hire an estate sale company to handle liquidation, or do a rough walkthrough themselves
which falls short because  estate sale companies take a cut and don't itemize for the court the way a personal property accounting requires; doing it themselves risks a rejected filing for insufficient itemization

> If the `which costs` line has no number in it, stop and go get one.

**Where to go get that number.** Do not estimate it. The candidates are: hours
the executor spent on the personal property accounting, dollar value of items
disposed of without valuation, number of court filing rejections and the
re-filing delay, or the percentage an estate sale company charged. Any one of
those is a defensible number. All of them come out of section 2, not out of
your head.

## 2. Evidence a user exists

- I exist and everyone has people die. 

**Who to approach, in order of how fast they will answer.** A probate or elder
law attorney in McDonough County. The county circuit clerk's probate division,
who can tell you the rejection rate on personal property accountings without
naming anyone. An estate sale operator, who is a competitor but will talk about
what they turn down and why. A family member who has served as executor, which
is the actual end user but the hardest to find cold.

## 3. Candidate scope (Must features only)

> **This is a narrowed slice, not the full system.** The version discussed
> originally included walkthrough-video inventory, multi-channel listing
> agents, and sale tracking. That is roughly 150+ hours. Everything below
> assumes single-photo input and stops at the court document.

| # | Feature (one vertical slice each) | Hours |
|---|---|---:|
| 1 | Photo upload → fine-grained item identification returned as structured JSON | |
| 2 | Identification → comp retrieval against sold prices → valuation range with confidence | |
| 3 | Valuation + effort heuristic → triage decision (keep / sell / donate / dump) with a stated reason | |
| 4 | Item register: persist, edit, correct, and override any machine decision | |
| 5 | Register → probate personal property accounting export, itemized with valuations and dispositions | |
| | Walking skeleton + CI | |
| | Deployment + clean-machine test | |
| | **Construction total** | |

Budget: plan on **60 hours**, hard ceiling **75**. Above 75 you are borrowing from
testing and documentation, which are graded.

## 4. Out of scope — will NOT be built

1. Walkthrough video ingestion and object tracking across frames.
2. Duplicate detection of the same physical object seen from multiple angles.
3. Any listing generation, posting, or marketplace integration.
4. Sale tracking, shipping, payment, or fee reconciliation.
5. Multi-user accounts, executor/heir roles, or permissions.
6. Real-time or streaming comp pricing; comps are fetched on demand and cached.
7. Support for more than one county's accounting format.
8. Authentication beyond a single local user.
9. Firearms, vehicles, real property, and securities, which have separate
   valuation and disposition law and would each be their own project.
10. Any claim of appraisal validity; output is explicitly an executor's aid,
    not a certified appraisal.

## 5. Feasibility screen

| Gate | Verdict | Evidence (dated) |
|---|---|---|
| **Build** — novelty load ≤ 2 | `[ TODO — pass/fail ]` | See technology list below; count the "new" marks yourself after you confirm each one |
| **Get** — every dependency exercised for real | `[ TODO — pass/fail ]` | `[ TODO — status code, saved response, date ]` for: (a) vision model API single-image call, (b) eBay sold-comp query returning real sold prices |
| **Ship** — a named deployment target, terms read | `[ TODO — pass/fail ]` | `[ TODO — target + pricing page read on YYYY-MM-DD ]` |
| **Show** — a stranger sees it work in 10 minutes | `[ TODO — pass/fail ]` | `[ TODO — the ten steps, written down ]` |

**Technologies:** Python + FastAPI (known) · React front end (known) · frontier
vision model over API (new) · eBay sold-comp data source (new) · PDF/document
generation (known, prior wkhtmltopdf work) · SQLite persistence (known)

**Novelty load:** 2 by this count. Confirm it yourself before you rely on it.

**Two dependency warnings, both dated and worth resolving in week one.**

The eBay API is the risk. Access to genuine *sold* prices historically sits
behind the Marketplace Insights API, which requires an application and approval
that is not instant and is not always granted. The Browse API gives you active
listings, which are asking prices, which are not the same number. Hit this in
your first week. If Marketplace Insights is denied, your comp source is gone and
gate two fails, so have a fallback identified before you need it.

Your local 24GB box is the wrong home for feature 1. Fine-grained visual
identification, meaning the difference between "glass bowl" and a specific
pattern and era, is not something an 8B or 13B local model does reliably. Budget
for API calls. The local server is well suited to the orchestration and text
work in features 3 through 5.

## 6. The one hard part

Fine-grained identification that is specific enough to retrieve a valid comp.
Everything downstream of feature 1 is conventional software, but "chair" returns
a useless price distribution while "1960s Danish teak lounge chair" returns a
tight one, and the gap between those two outputs is the entire project. It is
hard because the failure is silent: the model produces a fluent, plausible,
confidently wrong identification, and there is no signal in the output itself
that separates a correct identification from a hallucinated one, so confidence
has to be established externally through comp variance rather than read off the
model.

## 7. Scorecard (1–5 each; weight in parentheses)

| Criterion | (w) | Score | Weighted |
|---|---:|---:|---:|
| Evidence a user exists | 3 | | |
| Fits ~45 hours of features | 3 | | |
| Novelty load | 2 | | |
| Dependencies verified | 2 | | |
| Demonstrable in ten minutes | 1 | | |
| **Total (max 55)** | | | |

> Score this after section 2 exists, not before. The heaviest-weighted criterion
> is the one you currently have no evidence for, so any total you compute now is
> fiction.

## 8. If this candidate is rejected

**Rejected — closed for this course, not deferred to a date.** Two things killed it: cost and fit. The vision-API dependency for Feature 1 isn't free per call, and at the volume a real estate inventory needs, that cost isn't something I can justify on a class budget with no grant or funding behind it. Separately, the one hard part of this project — getting item identification specific enough to retrieve a valid comp, with no way to tell a correct answer from a confidently wrong one except by checking comp variance after the fact — is an open-ended data/ML-calibration problem, and perfecting that isn't where I want to spend a 240-hour capstone. It's a real idea with a real gap in the market. I'm just not the one building it this semester — though I'd revisit it independently if I ever had the budget and the specific interest in that kind of calibration work.

> The two most likely killers, so you know what to write against: comp data
> access denied, or identification specificity below roughly 60% on high-value
> items. Decide the threshold before you measure it.
