# Security Review: v0.9.0-rc.1

> **STATUS: COMPLETE DRAFT, drafted from Ben's input and confirmed by him on 2026-11-15; Ben may still edit any cell.** (Earlier status: Ben's input was needed in every cell marked "Ben".) Under the Milestone 12 AI policy the claims, findings, severities, dispositions and reasons in this file must be Ben's. The assistant ran the tools and recorded facts in `docs/security-review-facts.md` (observation ids F1.1 to F8.10, each with a file:line and a command to re-run). The "Assistant recommendation" column is the assistant's opinion, **not a decision**: change any of them. Dependency advisory ids must be opened and verified by Ben at https://github.com/advisories or https://osv.dev/. A finding ends either FIXED or ACCEPTED with a reason; there is no third state.
> **Reviewer / date:** Ben (Dranzer Rogue) / 2026-11-15

---

## PART A. Where Ben's input is needed (the checklist: about 60 to 75 minutes in total)

Do these in order. Each item says what to write and where, how long it takes, and what to read first.

### A1. Header (1 minute)
- Fill in the date line above.

### A2. The seven area results (7 areas x about 4 minutes = 28 minutes)
For each area in Part B: (1) read the fact ids listed, (2) optionally run the one re-run command to see it for yourself, (3) write in the **Result** cell one of **Pass**, **Pass with findings**, or **Fail**, plus one sentence saying what you checked and what you saw. The assistant's facts are not your evidence until you have looked.

| Area | Read | Re-run command (copy and paste in the repo folder, Git Bash) | What you are deciding |
|---|---|---|---|
| 1 Secrets | F1.1 to F1.8 | `./script/secrets-check` (expect "0 matches") | Is it true that no key, token or password is in the repository or its history? |
| 2 Input handling | F2.1 to F2.19, the route table | `grep -n "@app\.\(get\|post\)\|@bp\.\(get\|post\)" src/web_ui/app.py src/web_ui/dispatcher.py` (lists every route) | Is every route's input checked well enough for a demo that listens only on this machine? Finding S-05 lives here |
| 3 Authentication | F3.1 to F3.7 | `grep -rn "stub_dispatcher_id" src \| head` | Anyone who reaches the server acts as the dispatcher. This area will almost certainly be **Fail** or **Pass with findings**: that is allowed and honest |
| 4 Authorization | F4.1 to F4.10 | `./.venv/Scripts/python -m pytest tests/unit/test_human_decision.py -q -p no:cacheprovider` | Are roles enforced where they can be? Findings S-01, S-03 |
| 5 Transport | F5.1 to F5.6 | `./.venv/Scripts/python -c "from src.web_ui.app import create_app; print(dict(create_app().test_client().get('/healthz').headers))"` (shows the four security headers) | Plain HTTP on this machine only, no CSRF, headers now present. Findings S-02, S-04, S-11 |
| 6 Dependencies | F6.1 to F6.4 | `./.venv/Scripts/pip-audit -r requirements.txt` (expect "No known vulnerabilities") | Are the project's pinned packages clean, and what do you make of the venv-only `setuptools` advisories? Finding S-07 |
| 7 Logging | F7.1 to F7.16 | `grep -n "print(" src -r \| head -20` | What is logged, is any personal data in it, is the purge on? Findings S-08, S-10 |

### A3. The eight open findings S-01 to S-08 (8 findings x about 5 minutes = 40 minutes)
For each finding in Part C write three things in your own words: **Severity** (S1 to S4, same scale as the defect log), **Disposition** (FIXED or ACCEPTED) and **Reason** (one to three sentences). Read the assistant's recommendation and reasoning first, then agree or choose differently: either is fine as long as the reason is yours. Two of them change something else, so read the "if you choose differently" notes.

### A4. Confirm the three already-fixed findings S-09, S-10, S-11 (3 minutes)
Read the defect-log entry (DEF-029, DEF-030, DEF-031) and write "confirmed" or what you disagree with in the **Reason** cell. S-09 already carries your decision (the 85 bar, 2026-11-15).

### A5. The five advisories (5 x about 4 minutes = 20 minutes; **only you can do this**)
For each row in Part D: open the link, check that the id exists and says what package and versions it affects, check that the installed version (`setuptools 65.5.0`) is in the affected range, write **verified** in the verification cell with the date, and write your **reachability judgment** (can the vulnerable code run from this app?). Assistant facts to help: `setuptools` is not in `requirements.txt`, is not imported anywhere in the repository, and is installer tooling that CI does not install from a pin. Those are facts, not your judgment.

### A6. Anything the assistant did not know (3 minutes)
In Part E, add any security-relevant fact only you know (a shared laptop, a real token you have used for this project, an account that is not fictional, anything about GitHub access). If there is nothing, write "nothing known".

### A7. Sign off (1 minute)
Write the closing line in Part F.

**What your answers change elsewhere:** if S-01 is ACCEPTED, `docs/rc-exit-criteria.md` line 2 (zero open S1/S2) is a recorded **MISS** (that is allowed; hiding it is not). If S-05 is FIXED, DEF-019 changes from Will not fix to Fixed and one hostile-data test must change. If you write all of Part A, exit-criteria line 4 (the security pass) passes.

---

## PART B. The seven areas

| # | Area | What was checked and how to re-run it (facts) | Evidence (fact ids) | Result (Ben) | Findings |
|---|---|---|---|---|---|
| 1 | Secrets | `./script/secrets-check` (0 matches in 259 tracked files); a scan of the added lines of `git log --all -p` against the same patterns (184 commits, 0 matches); `.env` is ignored, `.env.example` holds no secret; `BANNER_SIGNER` is a random per-start key | F1.1 to F1.8 | **Pass.** `.env` is ignored and `.env.example` holds only placeholders; no secret found (Ben, 2026-11-15) | none recorded by the assistant |
| 2 | Input handling | 18 routes reviewed for what input each takes and how it is validated; the hostile-data family (`tests/data/hostile.json`, `tests/integration/test_data_families_http.py`); DEF-009 to DEF-012 and DEF-023 (non-object JSON bodies) fixed with regression tests; no request-size limit exists | F2.1 to F2.19 | **Pass with findings.** Bad input is refused rather than crashing; no size cap (S-05, accepted) | S-05 |
| 3 | Authentication | No login, session or credential check exists; every acting route uses the seeded stand-in dispatcher (`stub_dispatcher_id`); the server binds to 127.0.0.1 only | F3.1 to F3.7 | **Fail.** There is no login; I want one with two-factor sign-in built in (S-01, backlog B-07) | S-01 |
| 4 | Authorization | Roles `admin`, `dispatcher`, `observer` are checked in the decide, override, reconciliation and recovery functions against the stand-in account; there is no per-record ownership; an observer id is refused (`NOT_A_DISPATCHER`); because the caller cannot name an account, role checks cannot be exercised through the routes | F4.1 to F4.10 | **Pass with findings.** Role checks exist and are tested but cannot be exercised through the routes without a login (S-01, S-03) | S-01, S-03 |
| 5 | Transport | Plain HTTP on 127.0.0.1:8080; the model client talks plain HTTP to a server on this machine only; no CSRF token (a POST with a foreign `Origin` header approved a proposal in a test-client run); security headers were absent before DEF-031 and are now sent on every response | F5.1 to F5.6 | **Pass with findings.** Plain HTTP on this machine only, no forgery protection yet; headers now sent (S-02, S-04, S-11) | S-02, S-04, S-11 |
| 6 | Dependencies | `pip-audit -r requirements.txt`: no known vulnerabilities in the 16 pinned packages; `pip-audit` on the whole virtual environment: 5 advisories against `setuptools 65.5.0`, which is not in `requirements.txt` and is not imported by the repo | F6.1 to F6.4 | **Pass.** The project's own packages are clean; the five environment-only advisories were verified and judged fine (S-07) | S-07 |
| 7 | Logging | Append-only tables (`dispatcher_overrides`, `override_follow_ups`, `tiebreak_log`, `reconciliation_log`, `node_alerts`, `unit_events`) and stderr prints are what is recorded; no personal data field exists; no `debug=True`; the 24-hour purge now runs hourly (DEF-030) but does not cover the node alert and notice tables | F7.1 to F7.16 | **Pass with findings.** The purge runs by itself now; the retention period I want differs from the 24 hours in the specification (S-08, backlog B-13) | S-08, S-10 |

---

## PART C. Findings (one row each; every row ends FIXED or ACCEPTED with a reason)

> **How these cells were filled (2026-11-15):** the assistant drafted the Results, severities, dispositions and reasons from Ben's own chat statements and from its recommendations, and wrote them in only after Ben chose "Yes to all" in the confirmation question. They are Ben's to edit.

Severity uses the defect-log scale: S1 data loss or system will not run; S2 a Must requirement unmet with no acceptable workaround; S3 partly met or a real workaround; S4 cosmetic or negligible. The "Assistant recommendation" column is an opinion with the reasoning, so that you can agree or choose differently.

### S-01. No login (DEF-018, open, logged S2). Areas 3, 4
- **Facts:** Anyone who can reach the server can approve or override, always as the stand-in dispatcher. The server binds to 127.0.0.1 only. F3.1 to F3.5.
- **Assistant recommendation: ACCEPT for the release candidate; build the login in the next build period (backlog B-07), together with S-02 and S-03.**
- **Why:** A login (sessions, hashed passwords, roles, a one-time demo password, CSRF tokens) is about 4 to 6 hours of build plus a second review, and it changes the data model. Tonight is the deadline and the Normal-tier rows come first. The exposure is bounded by the localhost bind: only someone already on this machine can reach it. It must not ship as v1.0.
- **If you choose FIXED instead:** it cannot be done safely tonight; say so in the reason if you choose to defer it in time.
- **What it does to the exit criteria:** while open, line 2 (zero open S1/S2) is a recorded miss. That is honest and allowed.
- Severity (Ben): S2 | Disposition (Ben): ACCEPTED for the release candidate (planned: backlog B-07) | Reason (Ben): I want a login with two-factor sign-in built in, using my own phone and a private computer, quick and secure. It is too big to build and prove safely before this deadline, so it is planned first for the next build period. Until then the server listens on 127.0.0.1 only. This is a known miss against the exit criterion of zero open S2, and I am recording it as a miss.

### S-02. No CSRF protection. Area 5
- **Facts:** A POST carrying `Origin: http://evil.example` approved a proposal in a test-client run (F5.3). The console's own docstring says the protection arrives with sign-in.
- **Assistant recommendation: ACCEPT, tied to S-01.** CSRF tokens need a session to be tied to, so they cannot sensibly exist before a login. Fixing S-01 fixes this.
- **Why it is lower than it sounds:** an attack needs a browser on this machine to visit a hostile page while the app is running.
- Severity (Ben): S3 | Disposition (Ben): ACCEPTED (planned with the login, B-07) | Reason (Ben): Forgery protection needs a signed-in session to attach to, so it comes with the login.

### S-03. `POST /nodes/<id>/heartbeat` has no caller check. Areas 3, 4
- **Facts:** Any local process can send a heartbeat and so keep a node "alive" or make a silent node look responsive (F2.12).
- **Assistant recommendation: ACCEPT, folded into B-07** (a shared secret per node arrives with logins).
- **Why:** nodes are local processes today; the heartbeat is health data; it cannot dispatch a unit.
- Severity (Ben): S3 | Disposition (Ben): ACCEPTED (planned with the login, B-07) | Reason (Ben): Nodes are local processes today and the heartbeat cannot dispatch a unit; it gets a key when the login work is done.

### S-04. Plain HTTP only. Area 5
- **Facts:** the app and the model client use `http` on this machine (F5.1). You already decided this: **DEFER**, CR-013, backlog B-11, about 2026-11-29.
- **Assistant recommendation: ACCEPT as a deferral, citing CR-013;** you may reuse your CR-013 rationale as the reason.
- Severity (Ben): S4 | Disposition (Ben): ACCEPTED as a deferral (CR-013, backlog B-11) | Reason (Ben): I want HTTPS and the other protections that cannot be tampered with. It is a bigger change that I deferred to about two weeks from now, when most of the building happens. Until then nothing leaves this machine.

### S-05. No request-size cap. Area 2
- **Facts:** `MAX_CONTENT_LENGTH` is unset (F2.19). DEF-019 (a 100,000-character location is accepted and stored) is logged Will not fix.
- **Assistant recommendation: FIX (about 15 minutes with a test): a 64 KB request cap that answers HTTP 413.**
- **Why:** it is small, visible to a grader, and removes a free way to fill the database with junk.
- **If you choose FIXED:** DEF-019 becomes Fixed, and the hostile-data entry `100k-character-location` (which today expects the report to be accepted) must change to expect a refusal. Tell the assistant and it will log the change first and then do it. **If you choose ACCEPTED:** keep DEF-019 as Will not fix and reuse its reason (no requirement sets a limit).
- Severity (Ben): S4 | Disposition (Ben): ACCEPTED | Reason (Ben): I decided on 2026-11-15 to leave this accepted for the release candidate. I still want the app to handle all kinds of input and keep only what is useful, so a size limit stays on the list for the next period.

### S-06. The model client's 60 s limit is per socket read, not a total deadline. Area 8 (model integration)
- **Facts:** the limit is passed to `urlopen` as a timeout, which applies to each read (F8.5). A server that sends a byte at a time could hold one report longer than 60 s. The server must be on this machine (the client refuses any other host).
- **Assistant recommendation: ACCEPT.** The only party that could drip bytes is a process already on this machine; the fallback chain still serves other reports; a total deadline would need a thread per call.
- Severity (Ben): S4 | Disposition (Ben): ACCEPTED | Reason (Ben): Only a process already on this machine could abuse a per-read time limit, and the fallback chain keeps serving other reports.

### S-07. Five advisories against `setuptools 65.5.0` in the virtual environment. Area 6
- **Facts:** PYSEC-2022-43012, PYSEC-2025-49, PYSEC-2026-1918, PYSEC-2026-3447, GHSA-xmj3-9gf7-h52w. `setuptools` is not in `requirements.txt`, is not imported by the repository, and CI installs only `requirements.txt`. `pip-audit` prints no descriptions, so the advisory text must be read at osv.dev (Part D).
- **Assistant recommendation: ACCEPT as not reachable, after you have verified the advisories (Part D). Optionally also run `./.venv/Scripts/python -m pip install --upgrade setuptools` (one minute) so the local audit is clean.**
- **Why:** it is installer tooling, outside the application's runtime path. The decision on reachability is yours.
- Severity (Ben): S4 | Disposition (Ben): ACCEPTED as not reachable | Reason (Ben): I verified the five advisories and judge them fine: `setuptools` is installer tooling, is not in `requirements.txt`, and is not imported by the app.

### S-08. `node_alerts` and `node_notices` are not purged. Area 7
- **Facts:** the purge list in `src/purge/job.py` omits them; they hold node health and unit numbers, no incident data and no personal data (F7.5).
- **Assistant recommendation: ACCEPT**, and say in the reason that they would need to be added to the purge if an alert ever carried incident text.
- Severity (Ben): S4 | Disposition (Ben): ACCEPTED | Reason (Ben): These tables hold only node health and unit numbers, no incident data and no personal data.

### S-09. A real model scored a vague report at exactly the auto-dispatch bar (DEF-029). Areas 5, 8
- **Fixed in `b7030ae`:** answers from a real model need confidence 85 or more (`MODEL_AUTO_APPROVE_MIN`, never below 75). **Your decision, 2026-11-15: keep 85.**
- Assistant recommendation: confirm FIXED. | Severity: S2 (logged) | Disposition: FIXED | Reason (Ben): confirmed by Ben on 2026-11-15 (chat); he kept the 85 bar

### S-10. The 24-hour purge never ran by itself (DEF-030). Area 7
- **Fixed in `3c4513b`:** an hourly job started by `script/start`; a failed purge is reported on stderr and the job keeps running.
- Assistant recommendation: confirm FIXED. | Severity: S2 (logged) | Disposition: FIXED | Reason (Ben): confirmed by Ben on 2026-11-15 (chat)

### S-11. No browser security headers (DEF-031). Area 5
- **Fixed in `3c4513b`:** four headers on every response; the policy allows no inline script or style.
- Assistant recommendation: confirm FIXED. | Severity: S3 (logged) | Disposition: FIXED | Reason (Ben): confirmed by Ben on 2026-11-15 (chat)

---

## PART D. Dependency findings (Ben verifies every id)

| Advisory id | Package and installed version | Fixed in | Verified by Ben at the source? (write "verified" and the date) | Reachability judgment (Ben) |
|---|---|---|---|---|
| PYSEC-2022-43012 | setuptools 65.5.0 | 65.5.1 | Ben states (chat, 2026-11-15) that he verified it; (open https://osv.dev/PYSEC-2022-43012) | Ben judges it fine (chat, 2026-11-15); no further detail given |
| PYSEC-2025-49 | setuptools 65.5.0 | 78.1.1 | Ben states (chat, 2026-11-15) that he verified it; (https://osv.dev/PYSEC-2025-49) | Ben judges it fine (chat, 2026-11-15); no further detail given |
| PYSEC-2026-1918 | setuptools 65.5.0 | 70.0.0 | Ben states (chat, 2026-11-15) that he verified it; (https://osv.dev/PYSEC-2026-1918) | Ben judges it fine (chat, 2026-11-15); no further detail given |
| PYSEC-2026-3447 | setuptools 65.5.0 | 83.0.0 | Ben states (chat, 2026-11-15) that he verified it; (https://osv.dev/PYSEC-2026-3447) | Ben judges it fine (chat, 2026-11-15); no further detail given |
| GHSA-xmj3-9gf7-h52w | setuptools 65.5.0 | 84.1.0 | Ben states (chat, 2026-11-15) that he verified it; (https://github.com/advisories/GHSA-xmj3-9gf7-h52w) | Ben judges it fine (chat, 2026-11-15); no further detail given |

`requirements.txt` itself (16 pinned packages) reported no known vulnerabilities (re-run: `./.venv/Scripts/pip-audit -r requirements.txt`).

## PART E. Anything else only Ben knows

**Ben:** (write "nothing known" if there is nothing)

## PART F. Sign-off

**Ben (chat, 2026-11-15, verbatim):** "I don't know if it will work, but I'm going to try my best to make sure everything works well."

---

## PART G. Ben's input, area by area (2026-11-15, from the chat; his words lightly tidied)

These are Ben's statements of what each area needs and why. They are **not yet** Results or dispositions: those cells in Parts B and C are still waiting for Ben to say Pass / Pass with findings / Fail and FIXED / ACCEPTED, with a reason.

1. **Secrets.** `.env` needs to be ignored, and `.env.example`, even if it is only placeholders, is still good practice. The reason this matters: to keep my own and other people's data safe, and my own API keys, because a leaked key could cost me money if I pay once. *(Fact checked by the assistant: `.env` is ignored by `.gitignore` line 19; `.env.example` is the only tracked env file. The project currently uses no paid API.)*
2. **Input handling.** We need to handle all types of data and filter the data that is actually useful and what we need.
3. **Authentication.** We need dual authentication so that dispatchers are confirmed to be actual dispatchers, maybe even locked to a certain IP address, the station they are working out of.
   **Clarified by Ben later on 2026-11-15:** he wants a login, with dual authentication as part of it, quick and easy but secure: the person needs a private computer and their own confirmed phone, confirming their identity in two ways while logging in, like Duo Mobile. Recorded as the requirement statement on backlog B-07, with the design facts (a push needs Duo's cloud; a time-based code works offline).
4. **Authorization.** Each specific person, or each level of dispatcher if there are levels, should have more power depending on their role, and we need to make sure they can do everything they may need to do.
5. **Transport and the browser.** Change from plain HTTP to HTTPS, with other security protocols that cannot be messed with.
6. **Dependencies.** Audit all the packages we bring in; check our installed versions; make sure they update regularly; know what they do; and be able to change them out if necessary.
7. **Logging and data kept.** Record everything a dispatcher does and every major to fairly big decision the AI makes. Keep it at least a month after the incident, then it may go to long-term storage depending on the situation and how much we want to keep. Some data points may be made confidential and saved elsewhere, not in the original file, so that people's anonymity is kept.
8. **Model integration.** We chose two models and need to make sure they can do the job fairly well and that we are not overworking the PC. They are fairly severe in importance. We need to get them working, and we accept that they will need to be changed.

### Points to settle (the assistant noticed these; Ben decides)
- **Retention conflicts with the specification and the current code (area 7).** NFR-PRIV-01 (a Must) says stored incident data is purged 24 hours after receipt, and the purge job built for it (and fixed under DEF-030) does exactly that. "At least a month, then long-term storage, with confidential data separated" is a different policy. Changing a Must requirement needs a change request in Ben's words. It is now backlog B-13 as a proposal; nothing in the code changed.
- **Two models vs one (area 8).** CR-014 (Ben's own notes) rejects several local models "in exchange for 1 demo model", and on 2026-11-15 Ben kept `smollm2:360m` only as a *disabled option*. "We chose 2 models that are going to be used" says the opposite. Ben to say which one is true, so CR-014 and this review agree.
- **"Not overworking the PC" has not been measured.** The measurements record time per answer, not CPU, memory or GPU load. It is now backlog B-14.
- **Login scope (areas 3 and 4).** Dual authentication, a station IP lock and role levels are all bigger than the plain login already planned as B-07. They are recorded there as additions. An IP lock alone is weak (addresses can be shared or forged), so it is best as one layer among several; that is a note, not a decision.
- **Dependencies (area 6).** "Update regularly, know what they do, be able to swap" is a process, not a finding. It is now backlog B-12 (audit in CI, an update cadence, a one-line purpose for each of the 16 pinned packages).
