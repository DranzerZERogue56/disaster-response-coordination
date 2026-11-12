# Milestone 12: questions and inputs needed from Ben

How to use this: answer in the file (type after each `Ben:`), or tell the assistant. ★ marks the assistant's recommendation; it is only a recommendation. Questions marked **[YOURS]** must be answered in your own words because the assignment's AI policy makes them your claims (change dispositions, security findings, the memo). Questions marked **[FACT]** need a fact only you have. Anything you leave blank, the assistant will take as "use the ★ default" except the **[YOURS]** ones, which stay blank until you write them.
Plan: `2026-11-09-milestone-12-plan.md`. Due Sun Nov 15, 11:59 PM Central.

---

## A. Strategy, time and ground rules

**Q1.** What is the real goal for this assignment?
a) Full 150% (all of Normal + full Medium + full Hard) ★ b) 100% plus Medium only c) 100% plus Hard only d) 100% safely, extras only if time remains.
Ben:

**Q2.** How many hours can you really give each day, Mon-Sun? (Last week was 4 h/day against a 3 h plan.) The plan assumes about 15 h total.
Ben: Mon __ Tue __ Wed __ Thu __ Fri __ Sat __ Sun __

**Q3.** Which days are fixed for other work (Week 12 Quiz, Pen Testing Assignment 11, anything outside school)? 
Ben:

**Q4.** The Milestone 11 Hard-tier memo (`docs/quality-memo.md`) is still unfinished and its due date has passed. Do you want to finish it this week?
a) Yes, 1 h ★ (it is submitted work; finishing it keeps the repo honest) b) No, leave as is c) Remove the unfinished file so the repo does not contain a half-memo.
Ben:

**Q5.** Do you want the assistant to build code and tests natively (as in Milestone 11) with you deciding, or do you want to write more of the code yourself this time?
a) Assistant builds, you decide and review ★ b) You write, assistant reviews c) Mixed: you write the security fixes, assistant does the harnesses.
Ben:

**Q6.** How much of the assistant's code do you want to read before it is committed this week? (Last week you read very little; the review burden is a memo topic.)
a) All security-related changes, the rest sampled ★ b) Everything c) Only what the tests say changed.
Ben:

**Q7.** Is there any outside person you can ask for the observed sessions (NFR-USE-01, Q37) and for a second look? (A roommate worked as a reviewer last time.)
Ben: [FACT]

**Q8.** Do you want a stop-loss rule agreed now (what gets cut first if Wednesday night is behind)? ★ Proposed order of cuts: Medium item 4 (performance in CI), then the Ollama client (document it as designed-not-integrated), then the threat model, never the Normal-tier rows.
Ben: agree / change to:

---

## B. Written exit criteria for the release candidate (6 pts; written BEFORE evaluating)

**Q9.** Format: one line per criterion, each either a number or a command, with a PASS/FAIL slot dated. Agree? ★ yes. 
Ben:

**Q10.** Must-requirement acceptance: what is the bar?
a) All Must requirements have a passing acceptance test, except those that are documented as impossible without target hardware (FR-INFER-02, NFR-PERF-01) ★ b) at least 90% verified-Must (currently 94%) c) 100% with no exceptions (cannot be met without the RTX machine).
Ben:

**Q11.** Open-defect bar by severity: today DEF-018 (no login) is open at S2. Which bar do you want?
a) Zero open S1 or S2 (the same as Milestone 11) ★ b) Zero S1, S2 allowed only with a written acceptance c) Zero S1 and S2 plus at most N open S3 (give N).
Ben:

**Q12.** Do you want to FIX DEF-018 (build a real login) so criterion Q11a can pass, or accept a miss and write it down? (See Q44.)
Ben:

**Q13.** Security pass criterion: "all seven areas worked, every finding fixed or accepted in writing, every dependency finding carries a verified advisory ID". Agree? ★ yes
Ben:

**Q14.** Non-functional targets: "every one of the 14 NFRs has a recorded measurement or evidence row in `docs/performance.md`; each miss has a recorded decision". Agree? ★ yes
Ben:

**Q15.** Clean-clone criterion: "a fresh clone at the tag, following only README.md, reaches a running app in under __ minutes and `./script/test` passes". What number? (NFR-MNT-01 says under 5 minutes with local model files already downloaded.) ★ 5 minutes.
Ben:

**Q16.** CI criterion: "CI green on the tagged commit, both Python versions". ★ yes. Anything else?
Ben:

**Q17.** Do you want line coverage and verified-requirement coverage as criteria too (currently 95.85% line, 94% verified-Must)? ★ yes, keep the Milestone 11 numbers (>= 90% each) so they cannot quietly drop.
Ben:

**Q18.** The assignment's "Strong" example records a failure and the day it was fixed. Do you agree that the first evaluation (even if a criterion fails) is recorded and not replaced? ★ yes.
Ben:

---

## C. Integration evidence and the seam map (12 pts)

**Q19.** Definition check: a "Tier 1 seam" = a seam that crosses a process, network or storage boundary AND sits on an acceptance path. Confirm or correct this list (✓ = ★ treat as Tier 1):
1. Browser form to Flask route (network/HTTP) ✓
2. Flask to SQLite, including migrations and triggers (storage) ✓
3. Intake to classify to registry to decide to notify (the money path through the database) ✓
4. Scenario CLI to the running app (network) ✓
5. Heartbeat node processes to the shared SQLite file (process + storage) ✓
6. Classify service to model provider (today in-process; network if Ollama is wired) ✓ if wired
7. Scenario file and evidence files (file system) ✓
8. Purge job to the database (storage, scheduled)  ✓
9. CI runner to the repo (GitHub Actions) - Tier 2 (not on an acceptance path)
10. Dispatcher console HTML forms to the JSON/decision routes ✓
Ben: add / remove / change tiers:

**Q20.** Which of these has NO real-boundary test today in your opinion? (The assistant will also check.) 
Ben:

**Q21.** Where should the seam map live? a) New section in `docs/architecture.md` (Mermaid diagram plus table) ★ b) separate `docs/seam-map.md`. The assignment's file list says architecture.md.
Ben:

**Q22.** Diagram style: Mermaid text diagrams render on GitHub and are diffable. ★ OK? Or do you prefer a drawn image (then you provide it)?
Ben:

**Q23.** For each Tier 1 seam the plan wants "at least one named passing test" in a table (`docs/integration-evidence.md`). Is a test that uses the real database through the real route and a real thread "crossing a real seam" in your reading, and are mocks forbidden? ★ yes, nothing mocked at the seam under test.
Ben:

**Q24.** Seam 5 (real killed node processes) takes about 33 seconds. OK to keep it in the standard suite? ★ yes.
Ben:

**Q25.** Do you want an end-to-end "whole system" run documented as integration evidence: start the real app, play the demo scenario with the CLI, make decisions through the console, kill a node, show the alert? ★ yes, as a scripted run saved as a transcript like the M10 demo.
Ben:

**Q26.** Should that run also be recorded on video (like `docs/demo/iteration-1-demo.mp4`)? a) transcript only ★ b) transcript + new recording.
Ben:

**Q27.** The assignment says components have never been run "as a system on a machine that is not yours". Do you have a second machine (or can you borrow one) for one clean run? a) yes: which b) no: use a clean fresh clone + new virtual env on this machine and say so honestly ★.
Ben: [FACT]

**Q28.** Anything about how the pieces meet that has worried you since Week 9 and that no test covers? (The "hum of unease" from the Milestone 11 text.)
Ben: [FACT]

---

## D. Performance against your own targets (12 pts)

**Q29.** NFR-PERF-01 (classification p95 <= 5 s) names a 24 GB GPU and a local model. Which route?
a) Measure the fake model and say plainly it proves only the method (current state) b) Wire Ollama and measure the real model on THIS laptop, naming the laptop and calling it "not the target hardware", verdict "unverified on target" ★ (best evidence if feasible) c) Both.
Ben:

**Q30.** What is your laptop? CPU, RAM, GPU (model and VRAM), OS. (Needed to name the environment next to the numbers.)
Ben: [FACT]

**Q31.** Is Ollama installed on this laptop, and is a model already pulled? Which one (HARDWARE.md and ADR 0001 mention `llama3.2:3b` and `phi4-mini`)?
Ben: [FACT]

**Q32.** If measuring a real model: how many reports (the requirement says 20 seeded), and warm or cold start? ★ 20 seeded reports, warm; plus 1 cold start recorded separately.
Ben:

**Q33.** Is NFR-PERF-01 allowed to be recorded as "measured on laptop, 5 s target missed or met, target hardware not available, verdict Unverified-on-target"? That is honest and keeps the row filled. ★ yes
Ben:

**Q34.** NFR-REL-01 (30 s detection): the 5 trials gave 20.98 s worst case from missed heartbeat. For a real tail statistic do you want 20 trials (about 2.5 min of runtime)? ★ yes
Ben:

**Q35.** NFR-REL-02 (unit freed within 4 minutes): measure with the real sweeper and wall clock (4 minutes per trial). How many trials? ★ 5 trials run in parallel on 5 units (about 4.5 min total).
Ben:

**Q36.** NFR-REL-04 asks for a 20-minute outage with 100 reports. Run it for real once (20 minutes, can run while you work) ★, or shorten with a clearly stated method?
Ben:

**Q37.** NFR-USE-01 (a dispatcher decides within 45 s) needs two observed sessions of three seeded proposals, with a stopwatch. Who is the second person, and when (needs about 20 minutes)? If nobody: record it as "not measured, reason" and accept the row as a miss with a decision.
Ben: [FACT]

**Q38.** NFR-MNT-01: what was the measured time in the Milestone 11 clean-machine test (`tests/manual/evidence/mnt-01-*.md`), and do you want it re-run on the tagged commit? ★ yes, re-run on the tag.
Ben:

**Q39.** Which environment will you name for "production-like"? 
a) A clean, seeded run outside the editor: fresh clone, fresh venv, fresh database, started from the terminal ★ b) a deployed instance (do you have one?).
Ben:

**Q40.** The rubric needs at least one target re-measured after a fix with both numbers. We will not invent a failure. Which of these seems most likely to expose something real?
a) Dispatcher console page load with 1,000 stored proposals (nothing is paginated) ★ b) Report intake with 1,000 queued reports draining after an outage c) The `/reports` list and `/alerts` endpoints with many rows d) Purge job on a large database e) Something else you suspect.
Ben:

**Q41.** If that harsher measurement shows no problem, are you OK recording "measured under a harsher condition, no fix needed" and finding the "after a fix" evidence in a defect that already exists (for example the earlier 4-minute sweeper fix)? ★ yes, stated honestly.
Ben:

**Q42.** What realistic data volume should "realistic" mean for this project? (A county dispatcher might see 10-50 active incidents; a large event hundreds.) ★ 200 reports, 20 units, 5 nodes as the standard load.
Ben: [FACT]

---

## E. Security pass (14 pts) **[YOURS: every claim in `security-review.md`]**

**Q43.** Do you want the review organized as a table (area, what was checked, how to re-run it, result, finding, disposition)? ★ yes, one row per area plus a findings list below.
Ben:

**Q44.** DEF-018: no login. Anyone who can reach the server can approve or override. Choose:
a) Build real login now (sessions, password hash with a salt, roles, CSRF token on the console forms): closes DEF-018, strengthens authorization and the banner issue ★ (also earns credit in the security pass), about 4-6 h of assistant work plus your review b) Accept and document (server binds to 127.0.0.1 only; fix scheduled for the next milestone) c) Minimal shared-secret token header for write routes.
Ben:

**Q45.** If login is built: who are the users? Keep the seeded stand-in `demo-dispatcher`, an `admin`, and an `observer`? Password handling: the course says no real credentials in the repo. How will the demo log in (a documented demo password in the README is itself a finding)? 
Ben:

**Q46.** Authorization today: any dispatcher can decide any proposal; observers are refused. Is there any record-level restriction you want (a dispatcher sees only their zone)? ★ no, accept and write the reason.
Ben:

**Q47.** CSRF on the console forms (flagged and accepted last week because there is no login). Fix (token per form) or accept? ★ fix together with login, accept if no login.
Ben:

**Q48.** Transport: the app serves plain HTTP on 127.0.0.1. Options: a) accept for a localhost demo and write the reason ★ b) add TLS with a self-signed certificate c) document that a real deployment needs a TLS-terminating proxy. 
Ben:

**Q49.** Security headers on the console (Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Referrer-Policy): add them? ★ yes, small, testable.
Ben:

**Q50.** Input area: hostile data family, DEF-009..012 and DEF-023 fixed. Anything else you want probed (very large JSON bodies, malformed UTF-8, SQL-looking text, request-size limit)? DEF-019 (no length limit) is "will not fix": revisit? ★ add a 64 KB request-size cap and re-label DEF-019 as fixed? or keep it will-not-fix with the same reason? 
Ben:

**Q51.** Secrets area: `script/secrets-check` scans tracked files; the history scan is manual before each submission. OK to run a full-history scan and add its output as evidence? ★ yes. Do you also want `gitleaks`-style scanning in CI? (A Medium-tier-sized extra.)
Ben:

**Q52.** `.env.example` exists. Confirm `.env` is untracked and ignored. Is there any real credential anywhere on this machine used by the project (GitHub token, API key)? 
Ben: [FACT]

**Q53.** Dependencies area: the assistant will run `pip-audit` (or OSV) against `requirements.txt` and list candidate advisories. **You** must open each at https://github.com/advisories or https://osv.dev and verify the ID, affected versions and fixed version. Do you want to do that Thursday? Agreed? 
Ben:

**Q54.** Reachability judgment: for each advisory, "is the vulnerable code path reachable from this app?" Ben decides. Should the assistant provide the code path analysis as input (without making the call)? ★ yes
Ben:

**Q55.** Policy for dependency findings in CI (Medium item 1): fail the build on High/Critical reachable, warn otherwise? ★ yes. Or fail on any High/Critical regardless of reachability?
Ben:

**Q56.** Logging area: which logs exist? (Append-only override log, tiebreak log, reconciliation log, node alerts, Flask console output.) Is anything personal logged? Is there any place a stack trace could reach a user? Do you want a one-page "what we log and why" inside the review? ★ yes
Ben:

**Q57.** Should a failed login, a refused action (observer), and a purge failure be logged to an audit table? ★ yes if login is built.
Ben:

**Q58.** The purge deletes incident data after 24 hours. For logging that is a retention rule. Confirm that is how you want it described. 
Ben:

**Q59.** Findings: for each accepted finding the reason must be yours. Do you want the assistant to prepare, per finding, a neutral fact sheet (what, where, how reproduced, options with costs) so you only write the decision and reason? ★ yes
Ben:

**Q60.** Severity scale for security findings: reuse the defect-log S1-S4 scale? ★ yes.
Ben:

**Q61.** Do you want an independent review again (another model, read-only) on the security-relevant code, like last week? ★ yes, after your draft is written, as a cross-check (its findings go in as input, you disposition them). 
Ben:

**Q62.** Any area of the system you suspect is the weakest security-wise? 
Ben: [FACT]

---

## F. Third-party failure modes and degradation (10 pts)

**Q63.** Which external dependencies go in the table? ★ proposed: (1) Ollama / the local model, (2) Flask/Werkzeug and the other Python packages (supply chain; "changed response" = a breaking update), (3) GitHub (repo, Actions CI, Pages dashboard), (4) the advisory databases used by the scanner (if CI scanning is added), (5) SQLite itself (local; mostly "down" = locked/corrupt). Add or remove:
Ben:

**Q64.** The big one. Ollama is described in the design but not wired in. Choose:
a) Build a minimal Ollama client as the primary tier of the existing fallback chain, tested against a local stub HTTP server that can be slow, down, rate-limited (429), return changed or malformed JSON; real model optional on top ★ (makes the third-party seam, the failure table, the chaos test, the contract test and the real performance number all genuine) b) Do not wire it; document Ollama as "designed, not integrated" and demonstrate degradation with the existing fallback chain and simulated failures (cheaper, but the table then describes a dependency that does not exist at runtime) c) Wire it with the real model only.
Ben:

**Q65.** If (a): the real model optional layer: if Ollama is installed (Q31), do you want one real run recorded as evidence? ★ yes if it works first time, otherwise skip.
Ben:

**Q66.** Which model identifier should the client default to? (Design says `llama3.2:3b`; you said a "4B-size" and a "super small decision model".) 
Ben: [FACT]

**Q67.** Timeouts and retries for the Ollama client: the design says latency hard cap 60 s (FR-AGENT-04), retries 6 times every 10 s (FR-DEGRADE-02), one retry on invalid output. Keep those? ★ yes.
Ben:

**Q68.** "Rate-limited" for a local server is odd (Ollama has no 429 by default, but a busy server queues). Do you want the table to say so plainly and treat "busy/queue full" as the rate-limited mode? ★ yes.
Ben:

**Q69.** Which degradation do you want DEMONSTRATED (the rubric wants at least one, implemented and shown)? 
a) Model down: chain falls to smaller model, then rules, then a human, with the dispatcher console showing the escalation ★ b) Node down: heartbeat alert, cached updates, human confirmation c) Both.
Ben:

**Q70.** How will it be "demonstrated"? ★ a scripted run saved as a transcript in `docs/evidence/`, plus an automated chaos test (Medium item 3). Add a short screen recording?
Ben:

**Q71.** The user-facing states must be honest. What should a dispatcher see when the model is down? (Banner text, escalation list.) Do you want to word these messages yourself? ★ yes, short.
Ben: [YOURS]

**Q72.** Is there a "kill switch" you want (Medium item 5): a config flag that turns the model integration off without redeploying? ★ yes if Ollama is wired.
Ben:

**Q73.** For the "changed-response" mode: what should happen if the model returns a valid JSON of the wrong shape? (Current validator rejects and falls back.) Anything to change?
Ben:

**Q74.** Dependency version pinning: `requirements.txt` pins exact versions. Do you want the table to include the upgrade policy (who updates, how often)? ★ short paragraph.
Ben:

**Q75.** Do you want a runbook page (`docs/runbook.md`: what to do when the model is down, node alert, purge failure, DB locked)? It supports the kill switch and the Hard-tier "how a user finds out". ★ yes, one page.
Ben:

**Q76.** Licensing note: the Llama 3.2 license is not OSI-approved. Does the table need a line about that? ★ yes, one line referencing architecture section 9.
Ben:

---

## G. Change requests (14 pts) **[YOURS: dispositions, impact analyses in your words, your name and date]**

**Q77.** What real requests have arrived since the Week 8 baseline (Oct 18)? Think: advisor, roommates and reviewers, demo viewers, classmates, your own ideas, tool or dependency changes. List everything, even if you'd refuse it. 
Ben: [FACT]

**Q78.** Candidate requests drawn from the project's own history (the assistant is only listing, you decide which are real and what to do). Mark each: real / not real / merge:
1. A real notification channel (SMS, email or push) instead of a database row (peer reviewer, Milestone 10 Q10; DEF-017)
2. A real login with roles (FR-AUTH-01; DEF-018)
3. A mobile or small-screen responder view
4. A map with real streets (OSMnx / Overpass; ADR 0004 deferred it)
5. Running on the target GPU (RTX 3090/4090) with a bigger model
6. Cloud hosting / a deployed instance
7. Acknowledgment tracking: a responder confirms receipt (FR-ALERT-02)
8. Agent timeout of 60 s on the model call (FR-AGENT-04)
9. A report generator (the PDF/plan write-up from PROJECT.md)
10. The Mesa simulation of team sizes (Roster Competition)
11. A length limit on text fields / reject far-future timestamps (DEF-019, DEF-020)
12. Real-time updates in the console (auto-refresh was avoided for accessibility)
13. A dependency change: a new Flask/Werkzeug version, or Ollama API change
14. Changing the safety threshold (75 confidence) or adding severity-specific rules
Ben:

**Q79.** Which one is your "hardest refusal" (the one you most wanted to accept but turned down)? It feeds the Hard-tier memo. 
Ben: [YOURS]

**Q80.** Which one is "the yes you regret"? (Candidates from the record: raising the verified-Must bar from 60% to 90% on Nov 5, which displaced other work; the console; the broadcast trigger; something else?)
Ben: [YOURS]

**Q81.** How many CR files do you want? The rubric needs "one file per request since the Week-8 baseline". Existing: CR-001 to CR-010 (all approved, built). New ones for this week would be CR-011 onward. ★ at least 5 new (>= 1 REJECT, >= 1 DEFER with destination, >= 1 ACCEPT, >= 1 dependency/"changed under you").
Ben:

**Q82.** Each CR needs a **three-line impact analysis**: Cost (hours), Blast radius (what it touches), Risk both directions (risk of doing, risk of not doing). Do you want to write the three lines for each yourself, with the assistant giving you only neutral facts (which files, which requirements, which tests would change; hours estimates from `docs/wbs.csv` style numbers)? ★ yes
Ben:

**Q83.** Dispositions allowed: ACCEPT, REJECT, DEFER (with a named destination). Define "named destination" for you: a backlog id (B-01...), a milestone, or "version 2 backlog". ★ backlog id in `docs/backlog.md`.
Ben:

**Q84.** Decider and date on every CR: "Ben (Dranzer Rogue)" and the date you decide, not the date typed by the assistant. Agreed? 
Ben:

**Q85.** **Important honesty question.** CR-005 to CR-010 were drafted by the assistant last week (impact, rationale, "Decision: approved, Decided by Ben, Rationale: part of the work plan Ben approved"). This week's policy says the impact analysis and disposition are the owner's, in the owner's words. Options:
a) Add a short "Ben's disposition" section to each (your own sentence, your date), leaving the drafts visible ★ b) Rewrite each in your own words c) Leave them and note in `ai-usage.md` that they were drafted by the assistant and approved in bulk by you on 2026-11-05.
Ben: [YOURS]

**Q86.** The Milestone 11 CRs were all ACCEPT. For the change table, do you want a "Raised by" column (who made the request: you, advisor, reviewer, dependency)? ★ yes.
Ben:

**Q87.** Are there CRs among 001-010 you would now reverse or regret? (Feeds Q80.)
Ben: [YOURS]

**Q88.** For each new CR: who "asked"? If the requester is a person (advisor, roommate, classmate), what did you tell them and when? The Hard memo wants the actual sentence.
Ben: [FACT]

**Q89.** The assignment's Setup mentions a shared shopping list, a mobile version, a feature-vs-bug report, and a dependency advisory as sample requests. They do not apply to this project literally. Should the CRs be built from real requests only? ★ yes, never invent.
Ben:

**Q90.** Dependency advisory as a CR: if the scanner finds an advisory against Flask/Werkzeug/Jinja2, do you want a CR for "upgrade dependency X" (ACCEPT) even if it is a small change? ★ yes (it is exactly "a dependency that changed under you").
Ben:

**Q91.** Do you want the "bug that is actually a missing feature" example from your own log? Candidates: DEF-017 (notify only records a row), DEF-018 (no login). Treat as CRs? ★ yes for DEF-017 (becomes the DEFER with a destination), DEF-018 depends on Q44.
Ben:

**Q92.** Threshold rule check (CHANGELOG): a CR is needed for changes to a Must, an interface or data model, a milestone date or more than 4 hours, the stack, or the definition of done. Does adding an Ollama client count as "stack change"? ★ yes: raise a CR.
Ben:

**Q93.** Does adding a login (if Q44a) count as adding/changing a Must or the data model? ★ yes: CR (data model: sessions/credentials).
Ben:

**Q94.** Format of the three impact lines: sentences or labeled lines like `Cost: 3 h. Blast radius: .. Risk (do): .. Risk (don't): ..`? ★ labeled lines.
Ben:

**Q95.** Who reviews the CRs? The assignment says "a change control board of one". Do you want the assistant to read each and challenge it (devil's advocate questions) before you sign? ★ yes
Ben:

**Q96.** Each CR also gets a row in the change table at the top of CHANGELOG.md. Do you want the table to also list the Milestone 11 reach-90% CRs as they are? ★ yes (already there).
Ben:

---

## H. Scope cuts and backlog (6 pts)

**Q97.** What are you cutting or deferring this week? (Anything from the Q78 list you reject or defer; anything in `requirements.md` that will not ship.) 
Ben: [YOURS]

**Q98.** `docs/backlog.md` must hold each cut item with its estimate and acceptance criteria intact. Do you have estimates (hours) for each? Provide, or ask the assistant to propose and you correct. ★ assistant proposes from `docs/wbs.csv` and `docs/plan.md`; you correct.
Ben:

**Q99.** Backlog ids: ★ `B-01`... in the order added. OK?
Ben:

**Q100.** Requirements marked Deferred need: the word Deferred, a date, and a CR reference. Format ★ `**Status: Deferred** 2026-11-1x, CR-0NN, backlog B-0N`. OK?
Ben:

**Q101.** The three Milestone 7 deferrals (intake dedupe at ~line 94, FR-DEGRADE-02 clean preflight message at ~308, the map output at ~358) have no CR reference. Raise one retroactive CR for them ("record of the Milestone 7 cuts") or three? ★ one CR covering all three, DEFER, destination = backlog items.
Ben:

**Q102.** The rubric says nothing silently deleted. Are there any requirements or features that were quietly dropped during Milestones 9-11 and never recorded? (Think hard: "What did I stop doing without saying so?")
Ben: [FACT]

**Q103.** Should the cuts also be noted in `docs/plan.md` or the risk register? ★ yes, one line each.
Ben:

**Q104.** For the Hard-tier memo (Q137-Q140): which single cut is "the requirement you dropped" whose case you will argue against?
Ben: [YOURS]

---

## I. CHANGELOG and the release candidate (8 + 14 pts)

**Q105.** Format: Keep a Changelog (https://keepachangelog.com): sections Added, Changed, Deprecated, Removed, Fixed, Security. ★ yes, plus "Known issues in 0.9.0-rc.1".
Ben:

**Q106.** Tag name: `v0.9.0-rc.1` (the assignment's example) ★, or something else? Is this version number meaningful for this project (0.9 = nearly ready)? 
Ben:

**Q107.** Existing tags are `milestone-3`, `v0.1.0-skeleton`, `iteration-1`. Is `iteration-1` supposed to count as v0.5? Do you want to cross-reference the earlier tags in the changelog history? ★ yes, brief.
Ben:

**Q108.** The changelog's "Added" entries for this candidate must be traced to requirement ids. The M10/M11 work covers dozens of FR/NFR ids. Granularity: one bullet per requirement id, or grouped (ids in parentheses)? ★ grouped by feature with all ids in parentheses.
Ben:

**Q109.** Known issues (Strong format): id, severity, effect, workaround, planned version. Source list = open defects (DEF-017, 018, 019, 020 plus anything new this week). Is that the complete list of what ships broken? Anything else you know of that is not in the defect log (be candid)? 
Ben: [FACT]

**Q110.** Which defects get fixed before the tag (so they leave the known-issues list)? Choose from: DEF-018 (login), DEF-017 (channel), DEF-019/020 (limits). ★ DEF-019/020 are cheap (a request-size cap and a "future time" check): fix? 
Ben:

**Q111.** Do you want the "freeze" to be a branch (`release/0.9`), or just a tag on main? ★ tag on main, simplest; the freeze rule = no commits except documents and fixes for a disqualifying finding until Sunday.
Ben:

**Q112.** What counts as "disqualifying" (the assignment's word) for the RC? Provide your definition (e.g., any S1, a failing test on the tag, a leaked secret). 
Ben: [YOURS]

**Q113.** After tagging, if a docs-only change is needed (like a typo), is that allowed on main after the tag, with the tag staying put? ★ yes, and recorded.
Ben:

**Q114.** License: `LICENSE` is a dated deferral note ("decide MIT vs GPL by Week 5"). A release candidate should have a license decision. ADR 0005 exists. Is the decision made? Which? 
Ben: [FACT]

**Q115.** `.env.example` is present. Does the README document every environment variable the app reads? (`DB_PATH`, `SWEEP_SECONDS`, `HEARTBEAT_CHECK_SECONDS`, `CLASSIFY_MODEL`, `BANNER_SIGNER`, ... plus Ollama's if wired.) ★ the assistant will grep and update.
Ben:

**Q116.** README top part still describes the original Roster Competition concept. Do you want it rewritten to match what the RC actually does, with a clear "what works / what does not" section for a stranger? ★ yes (a stranger reads this first when cloning).
Ben:

---

## J. Records through Week 12 (4 pts)

**Q117.** Hours: please log each day this week as you go. Planned per day? ★ 3 h/day, actual as worked. Do you want the assistant to remind you at each session start?
Ben:

**Q118.** The Nov 3, 4, 7 rows of last week say "not itemised". Do you want to add detail now (what you did those days)? ★ yes, one line each.
Ben:

**Q119.** Defect log: new defects found this week (security review, performance, integration) get logged BEFORE any fix, with the seven fields and a regression test for each fixed one. Agreed? ★ yes.
Ben:

**Q120.** Traceability matrix: any new requirements arise from the CRs (login, Ollama client)? If yes, do they get new acceptance criteria? Remember **you** author requirement text (assistant proposes, you approve wording). 
Ben:

**Q121.** The test plan: should it get an Amendment 2 listing the new tests and the new exit criteria? ★ yes, short.
Ben:

**Q122.** `docs/ai-usage.md`: every substantive use this week gets an entry, zone chosen by you. Will you rate each (Green/Amber/Red) or leave proposals? ★ you rate at the end of each day.
Ben:

---

## K. Medium tier (+25%)

**Q123.** Which items do you want? Recommended (value order): 1) dependency scanning in CI ★ 2) a written threat model ★ 3) a chaos rep in the test suite ★ 4) performance in CI. Alternates: 5) kill switch, 6) cost/rate telemetry, 7) a second measured target (cold start, memory under load, import time), 8) contract test against a captured Ollama response (Q64a).
Ben: pick (and an order of sacrifice if behind):

**Q124.** Dependency scanning: which tool? a) `pip-audit` ★ (PyPA, uses OSV/PyPI data) b) `osv-scanner` c) GitHub Dependabot alerts only. Should CI fail on High/Critical reachable only (can't know reachability automatically) or on any High/Critical? ★ fail on any High/Critical, with an allow-list file where YOU record a reasoned exception for a non-reachable one.
Ben:

**Q125.** Threat model structure: STRIDE, or a plain "assets, attackers, boundaries, top two paths"? ★ plain with two named exposed paths. Which two paths do you consider most exposed? (e.g., the unauthenticated decision routes; the scenario/intake input; the SQLite file; the console banner.)
Ben: [YOURS]

**Q126.** Chaos rep: which dependency fails in the test? ★ the model provider (stub server returning errors/timeouts) end to end through the real intake route, asserting the escalation and the dispatcher-visible state; plus kill one node process mid-scenario. Anything else you'd want killed?
Ben:

**Q127.** Performance in CI: which named target is guarded? ★ intake-to-proposal p95 over the 20 seeded reports against a loose budget (e.g., 250 ms) using the fake model, labeled "in-process regression guard". Or REL-02 timing with an injected clock. Your preference?
Ben:

**Q128.** Budget for that CI performance test: CI machines are slower and noisy. Fail only when p95 exceeds a multiple (e.g., 5x the measured local value)? ★ yes. State the rule.
Ben:

**Q129.** Kill switch (if built): flag name and default (e.g., `MODEL_PRIMARY_ENABLED=0`). Exercised in a test and documented in the runbook. OK? 
Ben:

**Q130.** Cost telemetry: the cost is $0 always (local model). The Medium item asks for a metered dependency. N/A; state so. ★ skip this one.
Ben:

**Q131.** Second measured target: want one (cold start of the app, memory with 1,000 stored proposals)? ★ only if time remains.
Ben:

**Q132.** How will you present the Medium items to the grader? In `docs/` with a short index at the top of the CHANGELOG (so the grader finds them)? ★ yes, plus the status block "Shipped" line.
Ben:

---

## L. Hard tier: Scope Decision Memo (+25%) **[YOURS: all of it]**

The memo is to your advisor, 2-3 pages, `docs/scope-decision-memo.md`, graded on judgment, honesty and self-awareness. A memo that admits a mistake and reasons well scores higher than one claiming every call was right. The assistant will not write any of it. These questions are prompts for you to answer aloud or in bullets; then you write the memo.

**Q133.** Who is your advisor, and have they actually made or relayed any request? (If no one asked, the "refusal" is a request you made to yourself or got from reviewers.) 
Ben:

**Q134. Hardest refusal.** Which single request did you turn down that you most wanted to accept (Q79)? Give: the impact analysis (your three lines), the disposition, and **the actual sentence you said or sent** to the person who asked. If you haven't said it yet, what will you say? Why is "I'll try to fit it in" not an answer in this case?
Ben:

**Q135.** Who was the person, what is their role, and how did they take it (or how do you expect them to)?
Ben:

**Q136. The yes you regret.** What did you accept too quickly, "in a hallway", before counting hours? What did it cost (hours, work displaced)? What rule would have made the answer come out differently? (Think about Nov 5: the decision to raise the bar to 90% and build twelve requirements.)
Ben:

**Q137. Defend the cut.** Which requirement are you dropping (Q104)? Write the STRONGEST argument against dropping it, as its most committed supporter would. Then your answer. If you can't state the opposing case, you haven't decided. 
Ben:

**Q138.** Who would lose the most from that cut, concretely? (A dispatcher? An evaluator? A first responder?)
Ben:

**Q139.** What would change your mind about the cut? What evidence would reverse it?
Ben:

**Q140.** Is the cut reversible later cheaply, and where does it live (backlog id)?
Ben:

**Q141. Honesty call.** List what ships broken in this candidate (from Known issues). For each: severity, workaround, and **how will a user find out**? 
Ben:

**Q142.** Will your demo SHOW the degraded path (model down, no login) or hide it? Say plainly, and why. 
Ben:

**Q143.** Is there anything you'd prefer the grader not notice? (That is exactly the thing to put in the memo.)
Ben:

**Q144. Predict Week 16.** Given your measured velocity (you worked 20 h against 15 planned last week; see `docs/hours-log.csv`), what is the one thing most likely to be unfinished at delivery on Dec 10? 
Ben:

**Q145.** What is the trigger that would tell you early enough that it's happening (a number or an event, with a date)? 
Ben:

**Q146.** What will you do when the trigger fires (cut what, move what)?
Ben:

**Q147.** The memo is addressed to your advisor: tone preference (formal/plain)? Name for the "To:" line?
Ben:

**Q148.** Do you want the assistant to supply facts you can cite (hours totals, velocity per week from the log, defect counts, the list of CRs and dispositions) in a plain table you paste or reference? ★ yes (facts only, no judgment).
Ben:

**Q149.** Do you want the assistant to read a draft and flag factual errors against the repo (not style, not judgment)? ★ yes.
Ben:

**Q150.** When do you want to write it? ★ Friday-Saturday after the CRs and the changelog exist, so the memo describes decisions you have already made.
Ben:

---

## M. Housekeeping and the submission

**Q151.** Status block for Canvas (Shipped / Cut / Hours / Blocked on / Ship confidence): you write the confidence line. Agree to draft it Saturday together? 
Ben:

**Q152.** The Week 12 Quiz is open now (due Nov 15, 10 pts, random pool, "several rationales will tell you whether Milestone 12 is actually underway"). Take it near the end of the week, after the work, or now? ★ after Thursday.
Ben:

**Q153.** Pen Testing Assignment 11: due Nov 15? Confirm the date and what it is. Please check Canvas or tell the assistant to look.
Ben: [FACT]

**Q154.** Milestone 10's Canvas comment (recording link, tag, status block) and the Milestone 11 submission comment: done?
Ben: [FACT]

**Q155.** Milestone 11: confirm you submitted in Canvas and the final commit/CI state is what you want graded. Do you want a tag for Milestone 11 (e.g. `milestone-11`)? ★ yes, harmless and it makes the history legible.
Ben:

**Q156.** Anything in this plan that is more than you want to take on? Say what to remove now, so the stop-loss rule (Q8) is a plan and not a surprise.
Ben:

**Q157.** Anything missing: a requirement of the assignment text you think I overlooked, a person you must consult, a deadline I don't know about?
Ben:
