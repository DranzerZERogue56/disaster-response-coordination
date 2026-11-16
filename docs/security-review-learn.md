# Learn guide: how to review this project's security (for Ben)

This guide is to **help you understand** before you write `docs/security-review.md`. It is the assistant's explanation, not your review: nothing here goes in your review unless you have looked and agree. Open each file listed, read the few lines named, and then write what you found in your own words.

**How to use it (about 75 minutes):** go area by area. For each: (1) read "What it means", (2) open the files under "Where to look", (3) run the command if you want to see it happen, (4) ask the "What to decide" questions, (5) write your answer in `docs/security-review.md`. Line numbers were checked on 2026-11-15 and may drift if the code changes.

---

## The 8 words you need

| Word | Plain meaning | Where it shows up here |
|---|---|---|
| **Authentication** | proving *who you are* (a login) | none exists: area 3, S-01 |
| **Authorization** | deciding *what you may do* once known (roles) | dispatcher / admin / observer: area 4 |
| **CSRF** | a hostile web page makes your browser send a request to a site you are logged in to, so it acts as you | no protection yet: S-02 |
| **CSP and security headers** | instructions the server sends the browser: do not frame me, do not guess file types, only load my own files | added for DEF-031: S-11 |
| **Loopback** | the address 127.0.0.1: this machine talking to itself, never over a network | the app and the model client are limited to it |
| **Advisory** | a published report that a version of a package has a security hole (an id like PYSEC-2022-43012 or GHSA-...) | the 5 `setuptools` ones: area 6, S-07 |
| **Reachability** | whether the vulnerable part of a package can actually be run by *your* program | your judgment per advisory |
| **Severity vs priority** | severity = how bad the product fact is (S1 to S4); priority = how soon you act. You set both separately | every finding |

---

## Area 1. Secrets (is any password or key in the repository?)

**What it means:** a secret in git history stays there even after deletion, so the check covers every commit, not just today's files.
**Where to look**
- `.gitignore` (is `.env` ignored?) and `.env.example` (is it all placeholders?)
- `script/secrets-check` and `tools/secrets_scan.py` (what patterns it looks for)
- `src/web_ui/app.py` around line 225: `BANNER_SIGNER`, a random key made fresh each time the app starts, never written down
**See it yourself:** `./script/secrets-check` (expect "0 matches")
**What to decide:** Is it true that no real key, token or password is committed? Did you ever paste a real one into a file here, even once? (Part E of the review is for exactly that.)
**Facts to read:** F1.1 to F1.8 in `docs/security-review-facts.md`.

## Area 2. Input handling (what happens when someone sends rubbish?)

**What it means:** every route takes input from outside; the question is whether bad input is refused cleanly instead of crashing or being stored blindly.
**Where to look**
- The route list: `src/web_ui/app.py` lines 248, 257, 268, 277 (`POST /reports`), 313, 322, 351, 359, 388, 416, 431, 452, 463, 478, and `src/web_ui/dispatcher.py` lines 91, 129, 157, 175
- `src/intake_gateway/service.py`: the validation of a report
- `tests/data/hostile.json` and `tests/integration/test_data_families_http.py`: the nasty inputs the tests throw at it
- `src/web_ui/app.py`: `json_object()` (a JSON list instead of an object no longer crashes: DEF-023)
**See it yourself:** `grep -n "@app\.\(get\|post\)\|@bp\.\(get\|post\)" src/web_ui/app.py src/web_ui/dispatcher.py`
**What to decide:** Is the validation good enough for a demo that listens only on this machine? **Finding S-05 lives here**: there is no cap on request size, so a 100,000-character text is accepted and stored (DEF-019). Fix (a 64 KB cap) or accept?
**Facts to read:** F2.1 to F2.19.

## Area 3. Authentication (who is "the dispatcher"?)

**What it means:** today nobody logs in. Every action is performed as one seeded stand-in account.
**Where to look**
- `src/decide_proposal/service.py` line 119: `stub_dispatcher_id`, the function that picks "the dispatcher" for everyone
- `seed/iteration-1.sql` (the demo account, with placeholder hash and salt)
- `script/start`: the app listens on 127.0.0.1 only
- `docs/defect-log.md`: DEF-018
**What to decide:** This is the biggest open finding (**S-01**). The honest facts: anyone who can reach port 8080 on this machine can approve or override. What protects it is only the localhost bind. Decide accept-for-now or fix, and write why. This is the area most likely to be "Fail", and that is allowed.
**Facts to read:** F3.1 to F3.7.

## Area 4. Authorization (what may each role do?)

**What it means:** even with a login, a viewer must not be able to approve a dispatch.
**Where to look** (each is a role check):
- `src/decide_proposal/service.py` line 189 (approve, reject, modify)
- `src/override_assignment/service.py` line 36 (override)
- `src/negotiation/reconcile.py` line 102 (reconciliation override)
- `src/heartbeat/service.py` line 119 (confirm a node's recovery)
- `tests/unit/test_human_decision.py` (an `observer` is refused)
**What to decide:** The role checks exist and are tested, but because the caller cannot name an account, they cannot be exercised through the web routes (so they matter once a login exists). Findings **S-01** and **S-03** (`POST /nodes/<id>/heartbeat`, `app.py` line 452, has no caller check at all).
**Facts to read:** F4.1 to F4.10.

## Area 5. Transport and the browser (how traffic and pages are protected)

**What it means:** plain HTTP is readable on a network; here it never leaves the machine. Browser headers and CSRF tokens protect the page itself.
**Where to look**
- `script/start` (HTTP, 127.0.0.1:8080) and `src/classify_propose/ollama_client.py` lines 29 and 69 (`LOOPBACK_HOSTS`, `_check_local`: the model client refuses any host but this machine)
- `src/web_ui/app.py` lines 214 to 246: `SECURITY_HEADERS` and `add_security_headers` (the DEF-031 fix)
- `src/web_ui/dispatcher.py` lines 9 to 11 (the docstring that says there is no CSRF token yet) and the signed banner code (`BANNER_SIGNER`, two-minute expiry)
- `docs/change-requests/CR-013-https-transport.md` (your decision: HTTPS deferred)
**See it yourself:** `./.venv/Scripts/python -c "from src.web_ui.app import create_app; print(dict(create_app().test_client().get('/healthz').headers))"` (you should see the four headers)
**What to decide:** Findings **S-02** (no CSRF), **S-04** (plain HTTP, your CR-013 deferral), **S-11** (headers, fixed). Is plain HTTP on localhost acceptable for a release candidate? Your CR-013 says yes for now.
**Facts to read:** F5.1 to F5.6.

## Area 6. Dependencies (the code you did not write)

**What it means:** a package you install can have a known hole. `pip-audit` checks your installed versions against public advisory lists.
**Where to look**
- `requirements.txt` (the 16 pinned packages that CI installs)
- `docs/security-review-facts.md` section 6 (the audit output)
**See it yourself:** `./.venv/Scripts/pip-audit -r requirements.txt` (the project's own packages) and `./.venv/Scripts/pip-audit` (the whole virtual environment)
**What to decide:** The project's own 16 packages are clean. The whole-environment audit lists 5 advisories against `setuptools 65.5.0`, which is **not** in `requirements.txt` and is not imported anywhere. **Only you can verify them:** open each link in Part D of the review (https://osv.dev/...), confirm the id exists and that version 65.5.0 is in the affected range, then write your reachability judgment. Finding **S-07**.
**Facts to read:** F6.1 to F6.4.

## Area 7. Logging and data kept (what is recorded, and for how long?)

**What it means:** logs are evidence, but they can also hold things that should not be kept (personal data) or be silently edited.
**Where to look**
- The append-only tables (the database refuses edits): `migrations/0003-override-follow-ups.sql`, `0006-tiebreak-log-and-escalations.sql`, `0007-incident-versions.sql`
- `src/purge/job.py` line 47 (`purge`), line 60 (the list of tables it empties) and line 117 (`run_once`, the hourly job added for DEF-030); `script/start` starts it
- `src/web_ui/app.py` line 199: `start_purge_job`
- `docs/defect-log.md`: DEF-030
**What to decide:** Is any personal data stored (the design says none: no names or phone numbers)? Is the purge doing its job (it now runs hourly)? Finding **S-08**: the node alert and notice tables are not purged because they hold only node health and unit numbers. Finding **S-10** (the purge now runs by itself).
**Facts to read:** F7.1 to F7.16.

## The model integration (new this week; not one of the seven areas, but worth reading)

**Where to look:** `src/classify_propose/ollama_client.py` (no redirects at line 61, a 1 MB reply cap at line 28, the time limit at line 106, host check at line 69); `src/decide_proposal/service.py` line 19 and line 32 (the confidence bar of 85 for real-model answers, which you confirmed).
**What to decide:** Finding **S-06**: the 60 second limit applies to each read from the model server, not the whole call; only a process on this machine could abuse that. Finding **S-09** (DEF-029) is the one where a real model gave a vague report confidence 75: you chose the 85 bar.
**Facts to read:** section 8 of the fact sheet.

---

## How to decide each finding (a short method)

1. **What is the fact?** (read it; run the command if you want)
2. **Who could be hurt, and how?** (a dispatcher, a person waiting for help, a data subject)
3. **How likely, given this runs only on 127.0.0.1?**
4. **What does fixing it cost, and what would it displace this week?**
5. **FIXED or ACCEPTED?** If accepted, write the reason in one to three sentences, and say what would make you change your mind.
6. **Severity** (S1 to S4) separately from how soon you would fix it.

A good ACCEPTED reason names the risk, the thing that limits it, and when it will be revisited. "It's fine" is not a reason. A finding you cannot honestly accept (a leaked key, say) must be FIXED.

## Where to write each answer (the map back to the review)

| Your task | Location in `docs/security-review.md` |
|---|---|
| Date and your name | top, "Reviewer / date" |
| Seven area results (Pass, Pass with findings, Fail + one sentence) | Part B, the **Result** column |
| Severity, disposition, reason for S-01 to S-08 | Part C |
| Confirm S-09, S-10, S-11 | Part C, the **Reason** line of each |
| Verify and judge the 5 advisories | Part D |
| Anything only you know | Part E |
| One concluding sentence | Part F |

Your own words matter: the assignment says a stranger should reach your conclusion reading only your file.
