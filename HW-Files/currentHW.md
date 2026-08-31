# Current Homework — Week 1 Manual Checklist

**Milestone 1 — Project Charter & Engineering System**
Week 1 (Aug 24–30) · Hat: Project manager (with a little release engineer) ·
Phase: Inception · **Due: Sun Aug 30, 11:59 PM Central** · 100 pts ·
Hours target: 15/240

This is the manual, in-order process. Everything here is work only you can
do — the charter's hard sections are explicitly required to be your own
words about your own life, and generated text there is a policy violation.

---

## 0. First — find the real course templates

I don't have these; they're referenced by exact path in the assignment.
Check Canvas → this course's Files/Modules for:

- `code/charter-template.md`
- `code/hours-log.csv`
- `code/hours_report.py`

Download all three **before starting** — steps 4, 6, and 7 depend on them,
and the scaffolded `docs/hours-log.csv` in this repo may need its columns
changed to match the real template.

---

## 1. Repository structure (~5 min)

```bash
cd ~/Code/Capstone-ideas/disaster-response-coordination
mkdir -p src tests .github/workflows docs/adr
touch src/.gitkeep tests/.gitkeep .github/workflows/.gitkeep docs/adr/.gitkeep
```

Add a `.gitignore` (a generic Python + Node one is fine as a placeholder —
real stack work doesn't start until Week 5). **Commit this on its own** —
it's one of your required 3 distinct commit days.

---

## 2. License decision (~5 min)

Read the actual license texts at [spdx.org/licenses](https://spdx.org/licenses)
or [choosealicense.com](https://choosealicense.com) — **don't ask an AI to
pick one**, the assignment calls this out explicitly.

If you're not ready to decide, write a `LICENSE` file containing one dated
line:

> License decision deferred to Week 5 — reason: [your reason].

A dated deferral counts for the 2 points. An empty file does not.

---

## 3. Project board (~15 min)

GitHub → repo → **Projects** tab → new board.

- **Five columns** (e.g. Backlog / This Week / In Progress / Review / Done)
- **An enforced WIP limit** on "In Progress" (project settings → workflow
  rules, or self-enforce and state it in the charter)
- **≥6 cards**, each with an *estimate* (hours), a *hat* (which of the 16
  roles), and a *stopping condition* (what "done" means)

Good first cards: "Write charter §5 non-goals," "Set up hours log," "Write
ai-usage.md policy header" — this week's own work is fair game.

---

## 4. `docs/charter.md` — the big one (32/100 points)

Copy in the real template, then work the sections **out of order**, per the
assignment's own hint:

1. **§5 Non-goals first.** ≥5, each specific enough to actually stop
   something later.
   - Bad: "I won't over-engineer it"
   - Good: "No mobile client — web only, one browser target"

   Writing these first tells you what §1 actually is.

2. **§1 Purpose.** Two or three checkable sentences — what will be true at
   the end, verifiable by a stranger.

3. **§3 Capacity and constraints.** Do this **with a real calendar open**,
   not from memory. Every row, including administrator rights, money, and
   naming your two already-broken weeks.

4. **§4 Definition of finished.** 3–6 bullets someone else could
   independently check.

5. **§6 Risks.** ≥3, each with a specific early-warning sign and a response.
   - Bad: "Might run out of time"
   - Good: "Weeks 10–11 collide with my other course's group project → I'll
     know the date by Week 6 → I move 6 hours forward into Weeks 8–9, and if
     it's worse than expected I cut per my §7 order and tell my instructor
     by Friday of Week 9"

6. **§7 Working agreement + ranked cut order.** Decide now, while it's cheap,
   what you drop first / second / third when you fall behind.
   `RISKS.md` and `PROJECT.md`'s "Scope discipline" section already contain
   this thinking — reuse the *reasoning*, but write it as your own decision.

**Leave §2 marked `<fill in Week 2>`.** Don't write it yet.

---

## 5. `docs/ai-usage.md` — start today, not later

Copy the template and fill in the policy header:

- The spine rule
- The zones (Green / Amber / Red)
- The "Tools I have decided to use" table — filled in, even if the decision
  is a single dated line saying "none"

Then **log your first AI-assisted action today** as your first entry, all
six columns. Add a row every time you use AI on an Amber-zone task this week.

Graded on **specificity, not abstinence** — a small number of honest,
detailed entries scores well; vague or undisclosed use does not.

---

## 6. Log hours as you go — not afterward

For each real work session:

1. Write `estimate_hours` **before** you start
2. Write `actual_hours` **after** you finish

You need **≥5 real rows and ≥10 real hours** by Sunday. Delete the `SAMPLE`
row in `docs/hours-log.csv` once you have real ones, and swap in the real
course template's columns if they differ.

> If you find yourself reconstructing Wednesday on Friday, mark those rows
> honestly as reconstructed. An admitted gap costs almost nothing; a
> fabricated row costs everything.

---

## 7. `tools/hours_report.py`

Copy the real script from course materials into `tools/`, then **run it
against your log before submitting**. Its total must match your CSV.

---

## 8. Rewrite `README.md` v0

The current README is timeline/dashboard-blurb style. The rubric wants it to
orient a stranger:

- What this repository is
- Who owns it
- Its current status
- How to navigate `docs/`
- What is intentionally **not** here yet

Short and factual — a stranger oriented in 30 seconds.

---

## 9. Spread the work across ≥3 distinct days

You're currently at **2** (Aug 23, Aug 24). Don't do the rest in one sitting
even if you could — the rubric checks commit-history spread, and the
instructor states plainly that they can tell the difference in the writing.

Push each piece as you finish it rather than batching into one commit.

---

## 10. Before submitting

- [ ] Take the **Week 1 quiz** on Canvas
- [ ] Paste the weekly status block into the **Canvas submission comment**
      (not a document):

  ```
  Shipped:     what actually works this week, in one line
  Cut:         what I dropped or deferred, and where it went
  Hours:       planned N / actual N
  Blocked on:  the one thing in my way, or "nothing"
  Ship confidence: green | amber | red
  ```

  Say red when it's red. A red in Week 6 is a conversation and a scope cut;
  a red discovered in Week 15 is a grade.

- [ ] Submit the **repository link** (the repo is the submission — nothing
      is submitted as an attachment)

---

## Quick status — what already exists vs. what's missing

| Item | Status |
|---|---|
| `PROJECT.md`, `CALENDAR.md`, `RISKS.md`, `HARDWARE.md` | ✅ Done (scaffolding, not the graded artifact) |
| `docs/` Pages dashboard | ✅ Done (live) |
| `docs/hours-log.csv` | ⚠️ Scaffold only — 1 sample row, needs ≥5 real |
| Repo structure (`src/`, `tests/`, `.github/workflows/`, `docs/adr/`) | ❌ Missing |
| `.gitignore` | ❌ Missing |
| `LICENSE` (or dated deferral) | ❌ Missing |
| `docs/charter.md` | ❌ Missing — **32 points** |
| `docs/ai-usage.md` | ❌ Missing — 12 points |
| `tools/hours_report.py` | ❌ Missing (needs course template) |
| Project board | ❌ Missing — 12 points |
| `README.md` v0 format | ⚠️ Exists but wrong format for the rubric |
| Commit history ≥3 days | ⚠️ Currently 2 (Aug 23, Aug 24) |
