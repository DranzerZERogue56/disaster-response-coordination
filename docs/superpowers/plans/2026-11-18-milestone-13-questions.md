# Milestone 13: questions and three surgical options per rubric line

**Due:** Sun Nov 22, 11:59 PM Central. **Submit:** repository link + the commit SHA of the documentation commit + the completed `docs/clean-machine-test.md`.
**The hard boundary:** the assistant may draft, restructure and tighten text, but may not be the source of any command, path, version, port or expected output **that Ben has not executed himself**. So every drafted command goes through a "Ben runs it and pastes the real output" step. The clean-machine test is closed to AI: the assistant is not the tester and must not coach.
**Option labels:** A is the assistant's recommendation (not a decision), B and C are real alternatives. "Time" is the assistant's estimate of Ben's hands-on time.

Facts used below (checked 2026-11-18): licence is MIT (done, ADR 0005); Python 3.11.8 (`.python-version`); Ollama 0.40.16 (it was 0.40.15 on Nov 15); the model is `qwen3:1.7b` (ADR 0001 still says `phi4-mini`); ADRs 0001 to 0007 are all "Accepted"; `README.md` has sections but not the 11-section structure; `docs/architecture.md` is v0.1 from 2026-09-30 and starts at section 1; no runbook, onboarding or ADR index exists.

---

## Cross-cutting questions (answer these first)

1. Who runs the documented commands, and when? (Every command in every document must be executed by Ben, in order, from a clean state, with the real output pasted in.)
2. How many hours can you give each day through Sunday? (Last week: 4 h a day.)
3. What is the clean environment? (Question 9a below.)
4. What is the acceptance action the tester must complete? It must be written before the run (9b).
5. Which Medium items do you want? Two done well beat five thin. (Section M.)
6. Do you want the Hard-tier "Undocumented Memo"? It is your own words, 2 to 3 pages. (Section H.)
7. Milestone 12 loose ends (still yours): the three CR impact lines, the memo from Milestone 11, the Week 12 quiz and Pen Testing 11. Do any of them need time this week?
8. Is it acceptable that the README leads with the sign-in setup, since the app now needs an account before anything works?

---

## 1. README.md, all eleven sections (18 pts)

**Where we are:** a README exists (what this is, who owns it, run it, tests, status, navigation, not-here-yet). Missing or thin: non-goals, demo, prerequisites with versions, configure, project layout, troubleshooting, licence, contact and further reading. It still contains Week-9 era wording.

**Questions:**
- Which sentence in "what it is" would a stranger actually understand? (The current opening describes the older Roster Competition idea.)
- What are the non-goals? (Candidates: real notification channel, HTTPS, map routing, target-GPU performance, live field intake while the sign-in is on.)
- What is the demo: the Milestone 10 recording (before the login), a new GIF, or a text transcript?
- What contact is public: GitHub issues, your email, nothing?

**Three surgical options:**
- **A (recommended): restructure the existing README into the template, reusing today's text** (about 2 h). Keeps what is already verified; add the missing sections; move the long "how to navigate the docs" list to `docs/` and link it.
- **B: write a short new README and keep the current one as `docs/PROJECT-OVERVIEW.md`** (about 3 h). Cleaner for a stranger, but more new text to verify.
- **C: keep the README and add the missing sections at the bottom** (about 1 h). Fastest, but the "eleven-section standard" is judged by order and completeness, so it risks the 18 points.

## 2. Prerequisites pinned to real versions, each with a check command and a failure mode (8 pts)

**Where we are:** Python 3.11.8 is pinned in `.python-version`; `requirements.txt` pins 16 packages; bash is needed (Git Bash on Windows); Ollama is optional. None is written as a table with check commands.

**Questions:**
- Which prerequisites are *required* and which are optional? (Python, git, bash required; Ollama and the phone authenticator optional or required for the login?)
- What failure did you really hit for each? (Port 8080 busy: we hit it twice this week. Wrong Python: ? No bash: ?)

**Three surgical options:**
- **A (recommended): a table** (tool, pinned version, check command, expected output, named failure mode and its fix) where Ben runs every check command and pastes the real output (about 1 h). Failure modes drawn from real events: busy port 8080, Python not 3.11, bash missing, Ollama not running (the app falls back to the rules tier).
- **B: add a `script/doctor` command** that runs every check and prints PASS/FAIL, and document it (about 1.5 h; also counts toward the Medium bootstrap idea).
- **C: pin only in files** (`.python-version`, `requirements.txt`) and describe in prose (about 20 min; weakest against "check command" and "failure mode").

## 3. Every README command paired with its real expected output (8 pts)

**Where we are:** `tools/clean_machine_test.py` already ran the setup and start steps and recorded timings (84.2 s), but the README does not show outputs.

**Questions:**
- Do you want the outputs shown in full or trimmed with `...` and a stated reason?
- Which commands are in the README: setup, start, enrol, tests, lint, seed, scenario tool, Ollama pull?

**Three surgical options:**
- **A (recommended): run each command in a fresh terminal and paste the real output** (about 1.5 h). Honest by construction.
- **B: the assistant writes `tools/capture_readme_outputs.py`, which Ben runs;** it records each command and its real output into a file that is then pasted in (about 1 h plus review). The outputs are real because Ben ran it; the assistant never invents one.
- **C: reuse the clean-machine tool's evidence and fill the gaps by hand** (about 1 h; leaves several commands unpaired).

## 4. `docs/architecture.md` section 0 (12 pts)

**Where we are:** the file starts at "1. Purpose and Scope" (v0.1, Sept 30). It has a seam map and a failure-mode table from Milestone 12, and diagrams `containers.png`, `context.png` that predate the login, negotiation and heartbeat work.

**Questions:**
- Which four to eight boxes? (Candidates: Browser console, Flask app and routes, sign-in gate, model chain (Ollama and rules), unit registry and negotiation, SQLite with its triggers, background jobs (sweeper, purge, heartbeat), scenario tool.)
- What is **the one thing that would surprise a new reader**? (Candidates: the safety rules live in database triggers as well as in Python; the app has two modes depending on `AUTH_ENFORCED`; the "AI" is optional and the rules tier is always behind it; a held proposal times out in 4 minutes.)
- Must the existing sections be updated as built? (Several still describe designs that changed: model name, prompt path, no login.)

**Three surgical options:**
- **A (recommended): a Mermaid diagram in the file** (renders on GitHub, diffable) with 6 boxes and labelled arrows, plus five paragraphs, linked to ADRs (about 2 h). Update the stale statements in sections 5 to 9 with a dated "as built" note.
- **B: regenerate the existing Graphviz `containers.dot` and embed the PNG** (about 2 h; needs Graphviz installed, which is a command Ben must run).
- **C: ASCII diagram** (about 1 h; allowed by "diagram" but weaker visually).

## 5. `docs/runbook.md`, five real failure entries and a named destructive command (12 pts)

**Where we are:** nothing. We have excellent real defects to use.

**Questions:**
- Which five failures? Candidates with real evidence:
  1. A reserved unit stays "reserved" after 4 minutes (DEF-002 and the sweeper interval).
  2. Incident data is never deleted (DEF-030, the purge job).
  3. The model gives a vague report high confidence and a unit is dispatched (DEF-029: kill switch `OLLAMA_ENABLED=0`, bar `MODEL_AUTO_APPROVE_MIN`).
  4. Field reports or the scenario tool get HTTP 401 (DEF-032, the sign-in is on).
  5. `./script/start` says the port is in use or a stale server answers `/healthz` with 500 (the leftover-server event on Nov 15).
  Others: node updates stranded (DEF-021), a JSON list crashes a route (DEF-009/023).
- Which destructive commands must the operator not run? (Candidates: `./script/seed --reset` deletes the database; `tools/purge.py --retention-hours 0` deletes all incident data; `tools/enrol_dispatcher.py` on an existing name resets that person's password and phone secret; `rm data/dev.sqlite`.)
- Who is "the operator" (a dispatcher admin? a developer?) and where does it run (this laptop only)?

**Three surgical options:**
- **A (recommended): fill the template with the five entries above**, each with symptom, how to confirm, cause, fix, and the defect id; Ben reproduces each fix by hand (about 3 h).
- **B: include seven entries** (adds DEF-021 and DEF-009/023) for margin; more to verify (about 4.5 h).
- **C: five shorter entries** with symptom, cause, fix only (about 2 h); risks "traced to real defects" detail.

## 6. `docs/onboarding.md`, a five-row feature-to-code map and a real first issue (8 pts)

**Where we are:** nothing; the module layout is known (`src/intake_gateway`, `classify_propose`, `unit_registry`, `decide_proposal`, `negotiation`, `heartbeat`, `auth`, `purge`, `scenario`, `web_ui`).

**Questions:**
- Which five features go in the map? (Candidates: report intake, classification, unit reservation and the 4-minute clock, approve/modify/override, sign-in.)
- Which unclaimed first issue could a stranger finish in an afternoon?

**Three surgical options for the first issue:**
- **A (recommended): DEF-020 / backlog B-08, "reject or flag a report time in the far future"** (small, testable, existing hostile-data test shows the case; about 1 h to write up well).
- **B: DEF-019, "cap the request size at 64 KB"** (one setting, one test; but you chose to leave it accepted this week, which makes it a fair "open" item).
- **C: backlog B-12, "pip-audit in CI"** (touches the CI file; a good second issue, but needs more context).

## 7. `docs/adr/README.md`, an index with one new record for a decision never recorded (6 pts)

**Where we are:** seven ADRs, all "Accepted"; ADR 0001 is partly out of date (it names `phi4-mini`; the project now defaults to `qwen3:1.7b`).

**Questions:**
- Which statuses are now wrong? (0001: model choice superseded in part; 0006 and others: still current?)
- Which decision is the best "never recorded" one?

**Three surgical options for the new ADR 0008:**
- **A (recommended): "Two-factor sign-in with time-based codes, not a Duo push"** (alternatives: Duo cloud push, password only, IP allow-list; consequences: works offline, QR and trusted-device left open). A real decision with real alternatives made this week.
- **B: "Qwen3 1.7B as the demo model, the rules tier as the last fallback; supersedes ADR 0001's model"** (also marks 0001 "Superseded in part").
- **C: "Safety rules enforced in database triggers as well as in Python"** (made in Milestone 10 and never recorded).
You can write more than one; each is about 45 minutes. The index itself is about 45 minutes.

## 8. Successor section of `docs/ai-usage.md` (6 pts)

**Where we are:** the file is a usage log; there is no successor-facing section. The AI feature is the model chain.

**Questions:**
- Which six fields apply? (Behaviour and failure behaviour; exact model identifier with the date pinned; the file the prompt lives in; parameters; cost measured by you on a stated date, with a note that pricing changes; what must not be assumed stable.)
- Cost: the model is local, so money cost is $0. What else do you want to call "cost"? (Latency, memory, power.)

**Facts to pin by running them yourself:** `ollama list` (the model digest), `ollama --version` (0.40.16 on 2026-11-18), the prompt is `SYSTEM_PROMPT` in `src/classify_propose/ollama_client.py` (the architecture text says `prompts/classify-and-propose.txt`, which does not exist: a drift to fix or note), parameters `temperature 0.2`, `num_predict 512`, `think false`, `format json`.

**Three surgical options:**
- **A (recommended): measure per-call latency and memory with `tools/measure_nfrs.py model` (already built) on a stated date, state "$0 in money", and note pricing and hardware assumptions can change** (about 1 h).
- **B: also estimate power use** with a stated method (about 2 h; more assumptions to defend).
- **C: add a hosted-model comparison price** (about 1.5 h; **needs prices verified at the vendor's page by you**; pricing changes weekly).
"What must not be assumed stable" should name: the Ollama version, the model weights digest, the confidence calibration (DEF-029), and cold-start time (3.4 to 5.9 s measured).

## 9. The clean-machine test with a real tester on a clean environment (14 pts)

**Rules (void if broken):** a genuinely clean environment; a real tester who is not you, uncoached; silence; the repository URL is the only input; the clock runs from opening the repo to the acceptance action, stop at 60 minutes; every stumble logged, in the tester's own words.

**Questions:**
- 9a. **Which clean environment?**
  - A (recommended): **a new Windows user account on a borrowed or your own laptop**, with no project tools installed except what the README says to install.
  - B: a fresh cloud development environment (GitHub Codespaces; Linux; also gives a second platform for the Medium tier).
  - C: a borrowed laptop that has never had the project.
- 9b. **What is the acceptance action?** It must exist before the run. Candidates: (A, recommended) "sign in as a dispatcher with a phone code and approve one proposal from the seeded scenario on the console"; (B) "start the app and see `/healthz` healthy" (too easy, and the tool already does it); (C) "run the full test suite and see it pass" (less about use).
- 9c. **The phone problem:** the login needs an authenticator app on the tester's *own* phone. Options: (A, recommended) the tester uses their own phone; (B) the acceptance action runs with `AUTH_ENFORCED=0`, documented as a development mode (weakens it); (C) a desktop authenticator (a browser extension) for the tester.
- 9d. **The model:** keep Ollama out of the acceptance action (the rules tier is always there) so a 1.4 GB model download cannot burn the 60 minutes? (Recommended: yes.)
- 9e. Do you have what the test needs: the tester (to be decided), a place, a stopwatch, a way to record the tester's words (notes or screen recording)?

## 10. Friction log turned into fixes, committed, and a second run (8 pts)

**Questions:**
- How are fixes tied to the log? (Each fix commit names its friction entry id.)
- Who does the second run?

**Three surgical options:**
- **A (recommended): fix every friction entry in documentation or code, one commit each naming the entry, then the same tester repeats on a fresh environment** (shows the fixes worked).
- **B: a different tester for the second run** (a cleaner independence test, needs another person).
- **C: split the work: tester 1 on the first run and tester 2 on the second** (best evidence, hardest to arrange).

---

## M. Medium tier (+ up to 25%): pick what fits

Choices and one surgical way each:
1. **A demo that loads:** record a new 60 to 90 s GIF of the sign-in and one decision (the existing recording predates the login); commit it to the repo with alt text (about 1.5 h).
2. **One-command bootstrap:** `script/bootstrap` that runs setup, enrols the first account and starts the app; **write it after the first clean run** so it automates what mattered, and have the tester use it on the second run (about 1 h).
3. **Documentation tested in CI:** a CI job that runs the README's install, run and test steps on a clean Ubuntu runner and fails if a documented command breaks (the repo already has `tools/clean_machine_test.py`; about 2 h).
4. **A second clean run on a different platform:** the Ubuntu CI runner from item 3 could be that record if kept as a record (but a real second tester run is stronger).
5. **A troubleshooting section built from evidence:** every row traced to a real defect or a friction entry (largely a by-product of sections 5 and 10).
6. **Documentation accessibility pass:** alt text, real table headers, headings in order, no color-only meaning (about 1 h).
Recommended pair: **2 and 3** (they reinforce each other and the clean-machine tester uses the script), with 5 as a cheap by-product.

## H. Hard tier (+ up to 25%): the Undocumented Memo (Ben's words only)

Four jobs: name what a successor still cannot learn (specific); price each gap in hours (cost to document vs cost to leave); state the bus factor with evidence; name the one document to delete and defend it.
**Questions:**
- Do you want to write it? (About 2 to 3 hours of your own time.)
- Candidate gaps for you to judge (these are prompts, not claims): why a held proposal expires after 4 minutes and the 1 s sweeper; why 85 for a real model's confidence (set by feel); the trigger-based fan-out of unit status; why `contest()` is not one transaction (DEF-024's note); the Windows two-second "connection refused" quirk; why node tables are not purged; ADR 0007's weights.
- Bus factor: how many people could keep this alive today? (Honest answer: one human plus an assistant.) What artifact would make it two?
- The document to delete: candidates are `docs/superpowers/plans/*` (stale plans), `docs/security-review-facts.md` (duplicates the review), `docs/index.html` and `docs/app.js` (a dashboard).

---

## Suggested order of work (to be agreed)

Wed: decide the questions above; start README and prerequisites (Ben executes commands). Thu: architecture section 0, runbook, ADRs, onboarding. Fri: ai-usage successor section; freeze documentation; **first clean-machine run**. Sat: friction fixes, **second run**, Medium items. Sun: final commit, SHA, status block, submit.

---

## Decisions recorded (Ben, 2026-11-18, by button)

| Question | Ben's choice |
|---|---|
| 9a Clean environment | **A borrowed laptop** (a computer that has never had the project) |
| 9b Acceptance action (fixed before the run) | **"Sign in and approve a proposal":** the tester signs in as a dispatcher with a phone code, then approves one proposal from the seeded scenario on the console |
| 9c Phone-code login | **The tester's own phone**, with an authenticator app and the setup key typed in |
| Medium tier | **One-command bootstrap, documentation tested in CI, a demo GIF or recording, an accessibility pass on the docs** (four items) |
| Tester | still to be chosen by Ben |

**Assistant's notes on these choices (not decisions):**
- The acceptance action must work without Ollama (the rules tier answers), so a 1.4 GB model download cannot use up the 60 minutes. The README's default path must say so.
- The tester needs their own phone and an authenticator app **before** the clock starts, or that setup time is part of the 60 minutes. Decide and write down which, before the run.
- Four Medium items is more than "two done well beat five thin" advises, and the rule is that anything claimed must be demonstrated in the repository. Suggested priority if time is short: bootstrap and CI first (they reinforce each other), then the recording, then the accessibility pass.
- The bootstrap script must be written **after the first clean run** and used by the tester on the second.

### Second round (Ben, 2026-11-18, by button)

| Question | Ben's choice |
|---|---|
| Architecture §0: the one thing that would surprise a new reader | **The rules live in the database too:** the safety rules (a unit is assigned only while its proposal is approved; append-only logs) are enforced by database triggers, not only by Python code |
| Onboarding: the real unclaimed first issue | **pip-audit in CI** (backlog B-12). *Note: it must stay unclaimed and unbuilt, so a stranger could really take it; the Medium item "documentation tested in CI" is a different job and is not the same thing.* |
| ADR 0008: the decision never recorded | **Two-factor sign-in with time-based codes**, with the alternatives (Duo cloud push, password only, IP allow-list) and the consequences |
| Runbook failure entries | **Seven:** DEF-002 (reserved unit stuck), DEF-030 (purge never ran), DEF-029 (overconfident model, kill switch), DEF-032 (field reports refused, HTTP 401), the leftover server on port 8080, DEF-021 (node updates stranded), DEF-009/023 (a JSON list crashed routes) |
