# HW-Files — staging area, not a graded location

Also holds the working checklist for each milestone — a personal planning
note, not a graded artifact, so it lives here rather than at the repo root:

- [`currentHW.md`](currentHW.md) — Week 1
- [`currentHW-week2.md`](currentHW-week2.md) — Week 2

## Week 1 — still outstanding

Drop the real course templates here after downloading them from
Canvas → this course's Files/Modules (see [`currentHW.md`](currentHW.md) step 0):

- [ ] `charter-template.md`
- [ ] `hours-log.csv`
- [ ] `hours_report.py`

## Week 2 — done

Found directly in the course's public code repo
(`github.com/litman-books/capstone-project-code`), no Canvas hunt needed:

- [x] `idea-canvas-template.md`
- [x] `scoping-decision-memo-template.md`
- [x] `size_check.py` — copied straight to [`tools/size_check.py`](../tools/size_check.py) since it's a real, runnable script, not a scaffold

## Why this folder exists

This is **not** where graded artifacts live — it's a holding pen so the
real templates can be diffed against the placeholder scaffolding already
sitting at:

| Real template (goes here) | Scaffold it replaces |
|---|---|
| `charter-template.md` | [`docs/charter.md`](../docs/charter.md) |
| `hours-log.csv` | [`docs/hours-log.csv`](../docs/hours-log.csv) |
| `hours_report.py` | [`tools/hours_report.py`](../tools/hours_report.py) |
| `idea-canvas-template.md` | [`docs/ideas/candidate-a.md`](../docs/ideas/candidate-a.md) (`-b`, `-c`) |
| `scoping-decision-memo-template.md` | [`docs/scoping-decision.md`](../docs/scoping-decision.md) |

Once the real Week 1 templates are here: copy their structure/columns into
the Week 1 scaffolds above (adjusting them if the real template differs).
Once a folder's templates are all matched to their scaffolds, that part of
this folder can be emptied or deleted — it isn't part of the submission.
