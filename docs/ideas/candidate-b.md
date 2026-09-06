# Idea Canvas — Candidate B

> **Content status:** the project concept, scope table, out-of-scope list,
> feasibility/technology analysis, and "one hard part" reasoning below came
> from a heavily-AI-assisted brainstorm, reviewed and adopted (see
> `docs/ai-usage.md`, 2026-09-06, Amber). The problem statement, interview
> evidence, feasibility-gate verdicts, hour numbers, and rejection
> paragraph are still genuinely `[ TODO ]` — real work, not yet done, and
> required to be in my own words per this milestone's AI policy.
>
> **Real, outside-the-classroom flag, not just a course-integrity one:**
> this candidate is built directly on my actual job. Before this goes any
> further than a class exercise, I need to actually read my employment
> agreement (not just trust a paragraph an AI wrote about Illinois law in
> general) and decide accordingly. `[ TODO — did I actually do that? ]`

**Candidate name:** Out-of-State Title and Registration Completion
**Date started:** 2026-09-06   **Well it came from:** `[ TODO — declare this honestly; the candidate list originated in an AI brainstorming session, and the domain familiarity comes from my employment,]'

---

## 1. Problem statement

For              a title clerk at an independent used-car dealership
who              processes an out-of-state deal
the problem is   figuring out which forms and tax treatment apply for that buyer's state, then assembling and checking the paperwork by hand
which costs      `[ TODO — a NUMBER: days of delay, dollars paid to an outside title service, or the rejection/resubmission rate — get this from section 2, not from memory ]`
Today they       use a generic DMS (Dealertrack/DLRdmv) or pay an outside title service
which falls short because  existing DMS tools don't have out-of-state-specific document-set logic built in, so the clerk still manually researches and assembles the state-specific packet

> If the `which costs` line has no number in it, stop and go get one.

**Where to go get that number, each state has different taxes and items needed so it varies and would need to be processed after the fact and then fine tuned per state.

**Read your employment agreement before this file goes any further.** Illinois
protects employee inventions developed on your own time without employer
equipment or confidential information, but the protection has a carve-out for
inventions relating to the employer's line of business, and a dealership title
tool plainly relates. What governs is what you signed. This is not legal advice
and is worth an hour of an actual attorney's time. (General statute checked
independently 2026-09-06 — 765 ILCS 1060 does have this carve-out at the
general level; whether/how it applies depends on your actual signed agreement.)

## 2. Evidence a user exists

- **Person spoken to:** `[ TODO — initials or role, not "people in general" ]`
- **Date and length:** `[ TODO — YYYY-MM-DD, minutes ]`
- **Three verbatim quotes:**
  1. `[ TODO ]`
  2. `[ TODO ]`
  3. `[ TODO ]`
- **The workaround they already use:** `[ TODO ]`
- **Full write-up:** `docs/interviews/<YYYY-MM-DD>-<initials>.md`

**Who to approach.** Title clerks at independent lots, not franchise groups, and
not Kunes. The title clerk is the actual user; the GM is the buyer. Interview the
clerk. Ask specifically whether they are already on DLRdmv or Dealertrack and
what those tools still make them do by hand, because the gap is the project.

## 3. Candidate scope (Must features only)

> **This is a narrowed slice.** Three states, not fifty. No DMV submission, no
> status tracking to title issuance. Those are the business and they are not
> a 60-hour course project.

| # | Feature (one vertical slice each) | Hours |
|---|---|---:|
| 1 | Deal intake form → structured deal record (buyer state/county, vehicle, lienholder, tax basis) | |
| 2 | Rule engine: deal record → required document set + tax treatment for 3 supported states | |
| 3 | Form generation: pre-filled, printable documents for that state's required set | |
| 4 | Scanned-return validation: uploaded signed docs checked for presence, signature, date, odometer | |
| 5 | Deal status board with per-document completion state and a blocking-issues list | |
| | Walking skeleton + CI | |
| | Deployment + clean-machine test | |
| | **Construction total** | |

Budget: plan on **60 hours**, hard ceiling **75**. Above 75 you are borrowing from
testing and documentation, which are graded.

## 4. Out of scope — will NOT be built

1. All states except the three chosen; no attempt at a general 50-state engine.
2. Any electronic submission to any DMV or state agency.
3. Status tracking through to title issuance.
4. Sales and use tax calculation as an authoritative figure; the tool states
   the treatment and the required form, it does not certify the amount.
5. Temporary tag issuance or tracking.
6. Lien perfection and lienholder ETS integration.
7. DMS integration of any kind (CDK, Reynolds, Dealertrack).
8. Multi-store, multi-user, or role-based permissions.
9. E-signature capture; documents are printed, signed on paper, scanned back.
10. Any handling of real customer PII during development; all test data is
    synthetic.

## 5. Feasibility screen

| Gate | Verdict | Evidence (dated) |
|---|---|---|
| **Build** — novelty load ≤ 2 | `[ TODO — pass/fail ]` | See technology list below |
| **Get** — every dependency exercised for real | `[ TODO — likely FAIL as written; see below ]` | `[ TODO ]` |
| **Ship** — a named deployment target, terms read | `[ TODO — pass/fail ]` | `[ TODO — target + pricing page read on YYYY-MM-DD ]` |
| **Show** — a stranger sees it work in 10 minutes | `[ TODO — pass/fail ]` | `[ TODO — the ten steps, written down ]` |

**Technologies:** Python + FastAPI (known) · React front end (known) · rule/data
modeling for state requirements (known, it is data modeling) · PDF form fill
and generation (known, prior wkhtmltopdf work) · vision or OCR field validation
on scanned documents (new) · SQLite persistence (known)

**Novelty load:** 1 by this count. This candidate passes the Build gate more
comfortably than Candidate A.

**The Get gate is the problem, and you should resolve it before committing.**
There is no API for state title and registration requirements. The source of
truth is a mix of state DMV PDFs, dealer manuals, and phone calls to a title
desk. So there may be no dependency you can exercise for real, no status code to
save, and no dated response to paste into the evidence column. Read the gate's
exact wording in the assignment. If it requires a live external dependency, this
candidate fails it, and the honest response is either to rewrite scope so the
scanned-document validation model becomes the exercised dependency, or to reject
the candidate for this course and keep it as a business.

This is the central tension: the absence of a machine-readable rule source is
precisely what makes the idea commercially defensible and precisely what makes
it awkward as a course project.

## 6. The one hard part

Encoding three states' title requirements as a rule set that is correct, and
knowing when it stops being correct. The difficulty is not the code, it is that
the ground truth lives in inconsistent PDFs and undocumented practice, changes
without announcement, and has no authoritative machine-readable source, so
correctness cannot be verified against anything except a human who already knows
the answer. A rule engine that is silently 90% right is worse than no tool,
because the failure surfaces weeks later as a rejected title.

## 7. Scorecard (1–5 each; weight in parentheses)

| Criterion | (w) | Score | Weighted |
|---|---:|---:|---:|
| Evidence a user exists | 3 | | |
| Fits ~45 hours of features | 3 | | |
| Novelty load | 2 | | |
| Dependencies verified | 2 | | |
| Demonstrable in ten minutes | 1 | | |
| **Total (max 55)** | | | |

> Expect this candidate to score high on novelty load and demonstrability and
> low on dependencies verified. Score it after section 2 and after you have
> ruled on the Get gate.

## 8. If this candidate is rejected

**Rejected — closed for now, not closed forever.** Two compounding reasons. First, the actual regulatory content this tool needs — state-by-state title and registration requirements — has no machine-readable source; it lives in inconsistent PDFs, dealer manuals, and phone calls to title desks, which fails the Get gate as written and turns "build software" into "maintain a legal-compliance rule set by hand." Second, and more decisive for me personally: I don't want to take on the state regulatory research and my employer's invention-assignment policy that comes with this, especially given it plainly relates to Kunes' line of business under the Illinois Employee Patent Act's carve-out. I'd revisit this if I left the dealership or got a written carve-out — until then, it stays closed, not deferred.

> Most likely killers: the Get gate as discussed above, or a broad invention
> assignment clause in your employment agreement. The second one is worth
> writing as "closed for now, revisit on separation or written carve-out"
> rather than closed outright.
