# Scoping Decision — <Project Name>

Copy this into your repository as `docs/scoping-decision.md`. Two pages is plenty.
Every sentence you write here must be checkable by someone who is not you: a number,
a date, a quote, or a named condition. Delete the bracketed guidance as you fill it in.

**Author:** <your name>  ·  **Date:** <YYYY-MM-DD>  ·  **Course week:** 2

---

## 1. Problem

<One paragraph in the §2.1 frame: the user, the situation, what goes wrong, the cost
with a number, the existing workaround, and why the workaround fails. No technology
nouns in this paragraph. None.>

## 2. Evidence a user exists

Interviewed <initials / role> on <YYYY-MM-DD>, <N> minutes, past-tense questions only.
Full write-up in `docs/interviews/<YYYY-MM-DD>-<initials>.md`.

- "<verbatim quote 1>"
- "<verbatim quote 2>"
- "<verbatim quote 3>"

<If your project has no user but you, say so here in one sentence and substitute a
competitive scan of at least three existing tools. Do not invent a user.>

## 3. Chosen scope — Must features

| # | Feature | Hours |
|---|---|---:|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |
| | **Feature total** | |
| | Walking skeleton + continuous integration | |
| | Deployment + clean-machine test | |
| | **Construction total** | |

Plan: 60 hours. Hard ceiling: 75. My number: <N>. <One sentence saying whether that
leaves slack, and what happens if it does not.>

## 4. Should features — built only if there is room

<Each with its hour cost and the week it would be built. Say plainly which one is cut
first when you fall behind.>

## 5. Out of scope — will not be built

<At least eight items, by name, separated by " · ". Be specific: "notifications",
not "extra features". This is the section your Week-10 self will read.>

## 6. Accepted tradeoffs

<Any place you deliberately chose a cheaper design that costs the user something.
Name the cost. Name why you accepted it. Name what would make you revisit.>

## 7. Rejected candidates

**Rejected: <name>.** <Which gate it failed, with the number or the quote that killed
it, and the condition for revisiting — or "closed, not deferred".>

**Rejected: <name>.** <Same.>

## 8. Hour budget, reconciled

| Weeks | Phase | Hours |
|---|---|---:|
| 1–2 | Inception | 30 |
| 3–4 | Requirements | 30 |
| 5–6 | Design | 30 |
| 7 | Planning | 15 |
| 8 | Design review + midterm | 15 |
| 9–12 | Construction + verification | 60 |
| 13 | Documentation | 15 |
| 14 | Deployment + handoff | 15 |
| 15–16 | Presentation + delivery | 30 |
| | **Total** | **240** |

<One sentence: does your construction total fit inside the 60/75 line, and what did
you cut to make it fit?>

## 9. The one hard part

<Name exactly one. Two sentences on what makes it hard. This is what you will talk
about for ten minutes in Week 16.>

## 10. Risks and the scope-cut trigger

| Risk | Likelihood | What it costs me | Early warning sign |
|---|---|---|---|
| | | | |
| | | | |

**Scope-cut trigger.** If <a checkable condition> by <a real date>, I will cut
<feature> first, then <feature>. Decided now, in advance, so I do not have to decide
it while panicking.

---

**Signed:** <your name>, <YYYY-MM-DD>
**AI use for this document:** <what you asked, what you kept, what you changed — and
the matching entry in `docs/ai-usage.md`.>
