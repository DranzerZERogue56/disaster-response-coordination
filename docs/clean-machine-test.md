# The clean-machine test: protocol and observer log

Filled in from what the author and the tester reported. Nothing here was estimated or reconstructed to look complete: a field that was not recorded says so. Run 1 was not timed or logged during the run, which the protocol asks for, so it is recorded honestly as a partial run, and run 2 (below) is the one meant to meet the protocol in full.

## Rules (from the course protocol)

1. A clean machine: a fresh container, cloud environment, classmate's laptop, or a new user account.
2. A real tester who is not the author.
3. The author is silent: no speaking, pointing or typing.
4. The docs are the only input: the tester gets the repository URL and nothing else.
5. The clock runs from opening the repository to the acceptance action; stop at 60 minutes and record the failure.
6. Every stumble is logged.

## 1. Run header: run 1

| Field | Value |
|---|---|
| Date | 2026-11-21 (Saturday) |
| Tester | LW (initials) |
| Tester's background | CS student |
| Machine / OS / architecture | The tester's own personal laptop, Windows (version and architecture not recorded) |
| Environment type | A Docker container on that laptop, so only that container had the project's requirements (the image used was not recorded) |
| Repository URL and commit SHA | `https://github.com/DranzerZERogue56/disaster-response-coordination`; the author reports the tester cloned "the most recent commit we had" on 2026-11-21. The exact branch and SHA were not recorded; the latest pushed commits that day were `5b53888` on `main` and `43b94eb` on `HW-submissions` |
| Observer | Not recorded. The author reports giving the tester no instructions and no help; the tester used only the README |
| Database | The tester's own local SQLite file inside the container (nothing is hosted; the project runs entirely on one machine) |

## 2. Stopwatch: run 1

Not timed. No checkpoint times were recorded for run 1, so none are stated here.

| Checkpoint | Target | Actual |
|---|---|---|
| Repository opened | 0:00 | not recorded |
| Prerequisites installed / confirmed | 0:05 | not recorded |
| Dependencies installed | 0:08 | not recorded |
| Configuration complete | 0:11 | not recorded |
| Application running | 0:13 | not recorded |
| Acceptance action completed | 0:15 | not recorded |
| Test suite run and green | 0:20 | not recorded |

## 3. The acceptance action

> Create a dispatcher account, add the phone code to an authenticator app, sign in, and approve the waiting proposal at `http://127.0.0.1:8080/dispatcher` before its 4-minute hold runs out.

The action was chosen by the author on 2026-11-21 evening after run 1, and run 1 used the README as it then stood, which did not include the step that puts a proposal in front of the console. **Run 1 therefore did not test this action.** The tester reported verbally that the project "ran without a hitch"; no one recorded which checks that covered.

Result of run 1: not established.

## 4. Friction log: run 1

| # | Time | What the tester did or said | Root cause in the docs | Severity |
|---|---|---|---|---|
| 1 | not recorded | The tester said most dispatchers would not know how to use a terminal, and proposed an actual dashboard with a minimal number of buttons to streamline the workflow (relayed by the author) | The README tells a reader to run commands in a terminal to create an account and start the app; the console itself needs a terminal to receive a report (DEF-032) | slow (a usability finding, not a blocker) |

No other friction was reported to the author. The tester said it ran without a hitch; the author did not see the run, so a real count of stumbles is unknown.

## 5. Fixes applied

| Friction # | Document changed | Change made | Commit |
|---|---|---|---|
| 1 | `docs/backlog.md` | Added B-18, a terminal-free dispatcher dashboard, with proposed criteria for the author to confirm; to be built after Milestone 13 | see the Git history of this file |

## 6. Run 2 (to do, on the final documentation)

The README, runbook and onboarding guide were rewritten on 2026-11-22 after run 1, so run 1 did not exercise the submitted documents. The tester repeats the test in a fresh container, with the author silent, with the stopwatch table above filled in during the run.

| Field | Value |
|---|---|
| Date of re-run | |
| Tester | |
| Time to acceptance action | |
| Remaining blockers | |

## 7. Signed statement

To be written after run 2, and only if it is true. What can honestly be said now: on 2026-11-21 LW cloned this repository into a Docker container on a personal Windows laptop and, using only the README, reported that it ran without a hitch. The author did not observe the run, the times were not recorded, and the acceptance action above was not part of it.
