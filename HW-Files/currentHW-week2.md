# Current Homework — Week 2 Manual Checklist

**Milestone 2 — Idea Portfolio & Scoping Decision**
Week 2 (Aug 31–Sep 6) · Hat: Product owner · Phase: Inception (final week) ·
**Due: Sun Sep 6, 11:59 PM Central** · 100 pts (+up to 50% extra credit
across Medium/Hard tiers) · Hours target: 30/240 cumulative

This is the manual, in-order process. Everything here is work only you can
do — the assignment states AI may not choose your project, write your
problem statement, invent your user, or produce your hour estimates. It's
a sparring partner and hostile skeptic this week, not a decision-maker.

---

## 0. Templates — already pulled in, no Canvas hunt needed

Unlike Week 1, these were found directly in the course's public code repo
(`github.com/litman-books/capstone-project-code`, chapter 2 folder) and are
already copied into this repo — nothing to download yourself:

- `HW-Files/idea-canvas-template.md` — the real candidate-canvas structure
- `HW-Files/scoping-decision-memo-template.md` — the real memo structure
- `tools/size_check.py` + `tools/candidate-scorecard.csv` — the offline
  twin of the "240-Hour Scope Sizer" mentioned in the assignment; run
  `python3 tools/size_check.py` once you've filled in your own rows

## 1. Files & folders (scaffolded already)

```
docs/ideas/candidate-a.md        # from idea-canvas-template.md, all fields [ TODO ]
docs/ideas/candidate-b.md
docs/ideas/candidate-c.md
docs/scoping-decision.md         # from scoping-decision-memo-template.md, all fields [ TODO ]
docs/interviews/                 # drop <YYYY-MM-DD>-<initials>.md here
docs/evidence/dependency-checks/ # drop dated proof of each exercised dependency here
tools/size_check.py              # real Scope Sizer twin — run against your own data
tools/candidate-scorecard.csv    # header row only — fill in one row per candidate
```

Nothing above has real content yet — every field is a `[ TODO ]`. Filling
them in is the rest of this list.

## 2. Do the interview first (~30–60 min elapsed, but book it now)

`docs/interviews/<YYYY-MM-DD>-<initials>.md` — this is the only deliverable
that depends on somebody else's calendar, so book it before doing anything
else on this list. Five past-tense questions ("tell me about the last time
you had trouble with..."), three verbatim quotes, their current workaround.

No real user available? A competitive scan of three existing tools is an
accepted substitute — say plainly why there's no external user, don't
invent one.

## 3. Three real candidates (~4 hrs total)

Fill `docs/ideas/candidate-a.md`, `-b.md`, `-c.md` — three ideas you would
genuinely accept, not one favorite plus two decoys. Each needs:

- A costed problem statement (the `which costs` line needs a real number)
- The feasibility screen (Build / Get / Ship / Show gates)
- A Must-feature list with hours
- Section 8's rejection paragraph, written now while you still like the
  idea — a rejection written after you've committed reads like a
  rationalization

**Write the rejections while you still like the ideas** — if you can't
bring yourself to kill two, you didn't generate three real candidates.

## 4. Exercise every dependency for real (~1–2 hrs)

Not "read the docs page" — an actual `curl` call, download, or signup, for
every external dependency of every candidate. Save the evidence (with a
date) in `docs/evidence/dependency-checks/`, then transcribe it into the
dependency-verification table in `docs/scoping-decision.md` §2 area (or
wherever you land the table — the memo template doesn't have a dedicated
slot, so add one). Anything not exercised gets marked **UNVERIFIED**.

## 5. Bottom-up hour estimate + the Scope Sizer (~1 hr)

For your chosen candidate: vertical slices, not layers, including the
walking-skeleton/CI/deployment lines. Then fill `tools/candidate-scorecard.csv`
with a row per candidate and run:

```bash
python3 tools/size_check.py
```

Reconcile the sizer's number against your hand estimate — if they disagree
by more than 2x, find out which one is wrong before writing it down as
settled.

## 6. The scoping decision memo (32/100 pts — the big one)

`docs/scoping-decision.md`, all 10 sections. The two sections graders find
weakest:

- **§5 Out of scope:** ≥8 items **by name** — "camera-based barcode
  scanning," not "extra features." A stranger should be able to hold any
  feature up against the list and get a yes/no.
- **§10 Scope-cut trigger:** a checkable condition, a real date, and a
  named cut order — not "I'll reduce scope as needed."

## 7. Cut order, pre-committed

Same §10 as above: name the first three features that die, in order, if
you're behind at the Week-8 halfway audit (Oct 18–19), plus the condition
that fires it. Decide this now, calmly — the version of you deciding under
pressure in Week 12 usually cuts nothing and ships seven things at 80%.

## 8. Board + logs current

- A project-board card for every Must feature
- `docs/hours-log.csv` — Week 2's real hours, honestly (yes, including the
  "your AI slop is pissing me off" kind of honest, though maybe keep the
  language PG since this repo is public)
- `docs/ai-usage.md` — an entry for every session that shaped this
  milestone: what you asked, what came back, what you kept, what you
  changed

## 9. Week 2 Quiz

Finding an Idea Worth 240 Hours — take it *after* doing the reps above;
several questions ask whether the interview, dependency checks, and
estimates actually happened.

## 10. Weekly status block — paste into the Canvas submission comment

```
Shipped:     what actually works this week, in one line
Cut:         what I dropped or deferred, and where it went (backlog / change request / gone)
Hours:       planned N / actual N        (from docs/hours-log.csv)
Blocked on:  the one thing in my way, or "nothing"
Ship confidence: green | amber | red — if amber or red, the one thing that would move it
```

Say *red* when it's red — an honest amber costs nothing, a green that
wasn't true costs a lot more later.

---

## When you're done

- [ ] Three complete candidate canvases committed, no decoys
- [ ] `which costs` line filled with a real number on all three
- [ ] One user conversation conducted, written up, dated, three verbatim quotes
- [ ] Every external dependency exercised for real; evidence saved with dates
- [ ] Novelty load counted for each candidate; anything above 2 has a swap named
- [ ] Bottom-up estimate done by hand, feature by feature, in vertical slices
- [ ] Sizer run on all three (`tools/size_check.py`); the gap explained
- [ ] Two candidates killed in writing, each with the gate it failed
- [ ] Out-of-scope list: at least eight items, by name
- [ ] The one hard part named — exactly one
- [ ] Scope-cut trigger written with a checkable condition and a real date
- [ ] Board updated, hours logged honestly, `docs/ai-usage.md` current
- [ ] Everything committed; repository link submitted

Commit message the assignment suggests: `milestone-2: scoping decision, three candidates, two rejected`
