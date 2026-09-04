# Idea Canvas — Candidate <A / B / C>

Copy this file once per candidate into your repository as `docs/ideas/candidate-a.md`
(then `-b`, `-c`). Fill every field. A blank field is an answer: it means you do not
know yet, and that is exactly what this page is for. Delete the bracketed guidance
as you go.

**Candidate name:** <short, memorable, not a technology>
**Date started:** <YYYY-MM-DD>   **Well it came from:** <work / campus / hobby / open source / client / research gap>

---

## 1. Problem statement

For              <a specific user, described concretely enough that you could find one>
who              <the situation they are in when the pain happens>
the problem is   <what goes wrong, in their words>
which costs      <a NUMBER — dollars, minutes, errors, missed items, per week/month>
Today they       <the workaround that already exists>
which falls short because  <the specific reason the workaround fails>

> If the `which costs` line has no number in it, stop and go get one.

## 2. Evidence a user exists

- **Person spoken to:** <initials or role — not "people in general">
- **Date and length:** <YYYY-MM-DD, minutes>
- **Three verbatim quotes:**
  1. "<exactly what they said>"
  2. "<exactly what they said>"
  3. "<exactly what they said>"
- **The workaround they already use:** <...>
- **Full write-up:** `docs/interviews/<YYYY-MM-DD>-<initials>.md`

## 3. Candidate scope (Must features only)

| # | Feature (one vertical slice each) | Hours |
|---|---|---:|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |
| | Walking skeleton + CI | |
| | Deployment + clean-machine test | |
| | **Construction total** | |

Budget: plan on **60 hours**, hard ceiling **75**. Above 75 you are borrowing from
testing and documentation, which are graded.

## 4. Out of scope — will NOT be built

<At least eight, by name. This list is worth more than the one above.>

## 5. Feasibility screen

| Gate | Verdict | Evidence (dated) |
|---|---|---|
| **Build** — novelty load ≤ 2 | pass / fail | <technology list, each marked known/new> |
| **Get** — every dependency exercised for real | pass / fail | <status code, saved response, date> |
| **Ship** — a named deployment target, terms read | pass / fail | <target + pricing page read on YYYY-MM-DD> |
| **Show** — a stranger sees it work in 10 minutes | pass / fail | <the ten steps, written down> |

**Technologies:** <name> (known/new) · <name> (known/new) · <name> (known/new)
**Novelty load:** <count of "new">

## 6. The one hard part

<Name exactly one. Say what makes it hard in two sentences. If you can name three,
you have three projects.>

## 7. Scorecard (1–5 each; weight in parentheses)

| Criterion | (w) | Score | Weighted |
|---|---:|---:|---:|
| Evidence a user exists | 3 | | |
| Fits ~45 hours of features | 3 | | |
| Novelty load | 2 | | |
| Dependencies verified | 2 | | |
| Demonstrable in ten minutes | 1 | | |
| **Total (max 55)** | | | |

## 8. If this candidate is rejected

<Write the rejection paragraph NOW, while you still like the idea. Name the gate it
failed, the number that killed it, and the condition under which you would revisit
it — or say plainly that it is closed, not deferred.>
