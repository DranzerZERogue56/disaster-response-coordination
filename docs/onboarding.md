# Onboarding: your first ten minutes

For someone who has just been handed this repository and has never spoken to the author. Read this, then `README.md` to run it.

## 1. What you are looking at

A dispatcher decision-support tool. Reports come in; the system proposes **one unit** to send and a **confidence**; a **person** approves, modifies or rejects. It is one Flask app on one machine with one SQLite file. The best single page for the design is **`docs/architecture.md`, section 0**.

## 2. The words this project uses

| Word | Meaning here |
|---|---|
| Report | one incident: where, what happened, when |
| Proposal | the system's suggestion for a report: a unit and a confidence from 0 to 100 |
| Unit | a responder resource (Medical, Fire, Shelter, Security) that can be reserved and assigned |
| Hold / reservation | a unit is held for a proposal for **4 minutes**; if nobody decides, it is released |
| Safety rule | a person must decide when confidence is below the bar (75 rules tier, 85 real model) or severity is Severe or Critical |
| Override | a dispatcher changes an assignment after the fact; logged and uneditable |
| Tiebreak | when two proposals want the same unit: severity first, then information richness (ADR 0007), then reported first |
| Model chain | classify with a local model if enabled, then a smaller one, then the rules stand-in |
| Sign-in | password plus a six-digit phone code (ADR 0008) |
| DEF-nnn, CR-nnn, B-nn, ADR nnnn | a defect (`docs/defect-log.md`), a change request (`docs/change-requests/`), a backlog item (`docs/backlog.md`), a decision record (`docs/adr/`) |

## 3. Where a feature lives in the code

| Feature | Code | Tests |
|---|---|---|
| Receive and validate a report, queue it offline | `src/intake_gateway/` (`service.py`, `queue.py`) | `tests/unit/`, `tests/integration/` |
| Classify and propose (model chain, rules fallback) | `src/classify_propose/` (`chain.py`, `ollama_client.py`) | `tests/unit/test_classify_propose.py`, `tests/unit/test_ollama_client.py` |
| Reserve, release, assign a unit; the 4-minute clock | `src/unit_registry/service.py` | `tests/unit/test_clock_and_atomicity.py` |
| Safety rule, automatic and human decisions | `src/decide_proposal/service.py` | `tests/unit/test_human_decision.py` |
| Dispatcher console and sign-in | `src/web_ui/` (`dispatcher.py`, `auth_gate.py`, `templates/`), `src/auth/` | `tests/integration/`, `tests/acceptance/` |

Database rules (triggers, constraints) live in `migrations/*.sql`, not only in Python (architecture section 0 explains why).

## 4. How work moves

- Work happens on a branch, never straight on `main`. Current branches: `HW-submissions` (course work), plus `tester`, `functions`, `features`, `error-testing`. Merge to `main` only after the change has been tested live and the owner agrees.
- Every push and pull request runs CI (`docs/ci-pipeline.md`): secrets scan, Ruff with its security rules, 820 tests with a 90% coverage gate, build, smoke, and a dependency audit.
- A bug gets a row in `docs/defect-log.md` with a failing test **before** the fix; `tools/verify_regression.py` proves each fixed defect's test fails on the code before the fix.
- A change to a requirement goes through a change request. The requirement text is the owner's to write, not an assistant's.

## 5. Where decisions live

`docs/adr/README.md` (the index), `docs/requirements.md` (what it must do), `docs/change-requests/`, `docs/backlog.md` (what was cut or proposed), `docs/security-review.md` and the other audits, `CHANGELOG.md`.

## 6. Your first issue

**B-12 (second half): write `docs/dependencies.md`.** Nobody has claimed it.

*Why:* the project pins every package so installs are repeatable (`requirements.txt`, hash-checked) and CI audits them for known vulnerabilities, but nothing says what each package is for or when someone last looked at it. A new maintainer cannot tell which ones are safe to swap or remove.

*What to do:* create `docs/dependencies.md` with one row for each package in `requirements.txt` (there are 11 pins today): its name and pinned version, a one-line purpose in plain words, its licence (read it from the package's own metadata, for example `python -m pip show <name>` after `./script/setup`), the date you reviewed it, and a short paragraph stating how often the list is reviewed. Dependabot already opens weekly update pull requests (`.github/dependabot.yml`); say how you will handle them.

*How you know you are done:* every package in `requirements.txt` appears in the file exactly once, `./script/test` and `./script/lint` still pass, and a reviewer can read one row and know what removing that package would break. The acceptance criteria are in `docs/backlog.md` under B-12.

*If you get stuck:* the defect log shows how this project records what it found, and `docs/runbook.md` shows the day-to-day commands.
