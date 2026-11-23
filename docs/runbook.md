# Runbook: Disaster Response Coordination

For the person operating this system, possibly at an inconvenient hour, possibly without the author.

**Verification status, stated up front:** the commands in sections 2, 3 and 4 marked "recorded" were run in a fresh clone on the author's machine on 2026-11-22 and their output is in `docs/evidence/m13-command-outputs.md`. **No part of this runbook has yet been run by a second person on another machine.** Everything not recorded is marked **UNVERIFIED**. Run 2 of the clean-machine test (`docs/clean-machine-test.md`) is where that changes.

## 1. Where it runs

| Environment | Where | Who has access | How to get in |
|---|---|---|---|
| Local | the developer's machine, `http://127.0.0.1:8080`, plain HTTP | anyone who can open a browser on that machine and has a dispatcher account | see `README.md` |
| Staging | none | n/a | n/a |
| Production | none (nothing is hosted) | n/a | n/a |

Where the data actually lives: the SQLite file named by `DB_PATH`, `data/dev.sqlite` by default, inside the repository folder (not committed). Test data: `data/test.sqlite`.
Where the logs actually live: the terminal window that runs `./script/start` (the app writes nothing else to disk). Sign-in events are rows in the `auth_events` table of the database.

## 2. Start, stop, restart

```
# start (Git Bash on Windows, from the repository folder)
./script/start
# expected: the terminal stays busy and serves http://127.0.0.1:8080 (recorded: the health check answers within seconds)

# stop
# press Ctrl+C in the window running ./script/start   (UNVERIFIED by a second person)

# restart after a config change
# stop as above, then ./script/start again           (UNVERIFIED by a second person)
```

If the database file does not exist `./script/start` creates it from the migrations; it does **not** add demo data. Demo data: `./script/seed` (section 4).

## 3. Health check

The one thing you run to answer "is it alive?":

```
curl http://127.0.0.1:8080/healthz
```

Healthy looks like: `{"status":"ok"}` (recorded, HTTP 200).
Unhealthy looks like: HTTP 500, which is what `/healthz` returns when it cannot open the database; `./script/smoke` proves this on purpose by pointing the app at a missing database and printing `smoke: /healthz correctly fails when the data store is unavailable (500)` (recorded). Go to section 6, F-08.

A signed-out request to any other page, for example `GET /dispatcher`, returns HTTP 401 (recorded): that is normal, not a fault.

## 4. Routine operations

| Task | Command | How often | Expected result |
|---|---|---|---|
| Create or reset a dispatcher account | `python tools/enrol_dispatcher.py demo-dispatcher dispatcher` | once per person, and when a phone is lost | prints `Account ready: demo-dispatcher (dispatcher) in data/dev.sqlite`, then a one-time password and phone setup key (recorded) |
| Apply schema changes | `./script/setup` (or `python tools/migrate.py data/dev.sqlite`) | on release | `migrate.py: N migration(s) applied, database at data/dev.sqlite` (recorded for `./script/setup`) |
| Seed demo data | `./script/seed` | for demos | ends with `seed complete` (recorded) |
| Put one proposal in front of the console | `python tools/add_demo_proposal.py` | for demos | `Proposal 1 is waiting for a person (unit 1 is held for it).` (recorded) |
| Back up the data | copy the SQLite file (stop the app first) | before any change you cannot undo | **UNVERIFIED**: no backup command has been run |
| Restore from a backup | put the copy back at `DB_PATH` with the app stopped | on demand | **UNVERIFIED** |
| Rotate a secret | the session signing key is random at each start unless `SESSION_SIGNER` is set; restart to rotate; there are no other stored secrets | on suspicion | **UNVERIFIED** |

**Destructive commands, never run casually:**
- `./script/seed --reset` **deletes the database file** at `DB_PATH` before re-creating it. All reports, proposals, accounts and logs in that file are gone.
- `./script/seed-test-data` deletes `data/test.sqlite` and rebuilds it.
- Deleting `data/dev.sqlite` by hand has the same effect as the first.
The override, tiebreak, reconciliation and sign-in logs are protected by database triggers and cannot be edited or deleted through the app; do not drop the triggers to "fix" a log.

## 5. Normal readings

- Install (`./script/setup`) took 75.6 s on the recorded run (an earlier run took 109.7 s).
- `./script/test` ran 820 tests in about 7 minutes on the recorded run.
- A proposal that needs a person holds its unit for **4 minutes**; after that the unit is released and the proposal times out. That is normal, not a fault.
- Severe or Critical reports always wait for a person, whatever the confidence.
- Normal terminal lines: Flask's development-server warning and one line per request. A Python traceback ending `sqlite3.OperationalError: unable to open database file` printed by `./script/smoke` is expected (it breaks the database on purpose).
- Known limits: request bodies over 1 MiB are refused with HTTP 413; the console shows at most 200 waiting proposals and says how many are hidden; one machine, one SQLite file.

## 6. Failure catalogue

Each entry comes from `docs/defect-log.md`. Commands marked UNVERIFIED have not been run by a second person.

### F-01: Field reports, the scenario tool or node heartbeats answer HTTP 401 (DEF-032, open)

- **Symptom:** HTTP 401 from `POST /reports`, `python tools/play_scenario.py ...` or a heartbeat.
- **First check:** was the app started with `./script/start`? That turns the sign-in on.
- **Likely cause:** with the sign-in on, only a signed-in dispatcher is allowed through; these callers have no account.
- **Fix:** for demos, stop the app and start it with `AUTH_ENFORCED=0 ./script/start` (no sign-in at all: only on a machine nobody else can reach).
- **Verify the fix:** `POST /reports` answers HTTP 201.
- **If that does not work:** stop and escalate (section 7).

### F-02: Sign-in keeps failing (DEF-018 and its fix)

- **Symptom:** `Sign-in failed. Check the username, password and code, or try again later.` (the same message for every cause, on purpose).
- **First check:** is the phone clock correct, was the code already used, were there 5 failures in a row (the account locks for 300 seconds)?
- **Likely cause:** wrong password or code, reused code, lockout.
- **Fix:** wait for a fresh code and retry; if the password or phone key is lost, `python tools/enrol_dispatcher.py <username> dispatcher` creates a new password and phone key (the old ones stop working).
- **Verify the fix:** the sign-in page lets the person in and `/dispatcher` loads.
- **If that does not work:** read the person's rows in the `auth_events` table; if they show sign-ins you do not recognise, section 7 (secret exposed).

### F-03: A proposal disappeared before it was approved (DEF-002, DEF-003 fixed; by design)

- **Symptom:** the proposal is gone from "Proposals waiting for a decision" and its unit is available again.
- **First check:** was it more than 4 minutes since it appeared?
- **Likely cause:** the 4-minute hold ended and the sweeper released the unit.
- **Fix:** none needed; re-file the report, or for a demo run `python tools/add_demo_proposal.py`.
- **Verify the fix:** reload `/dispatcher`; the new proposal is listed.
- **If that does not work:** check the app is running (section 3).

### F-04: Every request answers HTTP 400 (DEF-036)

- **Symptom:** HTTP 400 for any URL, from a browser or a tool.
- **First check:** what host name is in the address bar or the `Host` header?
- **Likely cause:** only `localhost` and `127.0.0.1` are served; any other name is refused on purpose.
- **Fix:** use `http://127.0.0.1:8080`; for another name set `ALLOWED_HOSTS=name` before `./script/start` (**UNVERIFIED**).
- **Verify the fix:** the health check answers `{"status":"ok"}`.
- **If that does not work:** stop and escalate.

### F-05: HTTP 413 on a report or form (DEF-038)

- **Symptom:** HTTP 413 (request too large).
- **First check:** size of the body being sent.
- **Likely cause:** bodies over 1 MiB (or a form with more than 100 fields) are refused.
- **Fix:** send a smaller body.
- **Verify the fix:** the report is accepted (HTTP 201).
- **If that does not work:** stop and escalate.

### F-06: The console says "N more proposals are waiting and are not shown here" (DEF-039)

- **Symptom:** that notice under the waiting list.
- **First check:** count of waiting proposals.
- **Likely cause:** more than 200 are waiting; only the oldest 200 are drawn.
- **Fix:** decide the ones shown and reload.
- **Verify the fix:** the notice number goes down.
- **If that does not work:** stop and escalate.

### F-07: A responder says they were never told (DEF-017, open)

- **Symptom:** an approved proposal, but nobody was contacted.
- **First check:** the notification row for the proposal (`python tools/dbq.py "SELECT * FROM notifications"` reads it without changing anything; **UNVERIFIED**).
- **Likely cause:** "notify" only records a row; there is no real channel yet.
- **Fix:** tell the responder by an outside channel; there is no software fix yet.
- **Verify the fix:** the responder confirms.
- **If that does not work:** section 7.

### F-08: `/healthz` answers HTTP 500, or the app will not start

- **Symptom:** HTTP 500 from `/healthz`, or a traceback ending `sqlite3.OperationalError: unable to open database file`.
- **First check:** does the file named by `DB_PATH` exist, and is the folder writable?
- **Likely cause:** missing or locked database file, wrong working directory.
- **Fix:** run `./script/start` from the repository folder; if the file is missing and no data matters, `./script/setup` re-creates it (**not** `./script/seed --reset`, which deletes data).
- **Verify the fix:** `curl http://127.0.0.1:8080/healthz` answers `{"status":"ok"}`.
- **If that does not work:** stop and escalate.

## 7. Escalation and the things only a human can decide

- **Data loss suspected:** stop. Do not restart and do not run `./script/seed --reset`. Copy the database file somewhere safe first.
- **A third-party service is down:** the only optional one is the local Ollama model; if it is down or slow the report is classified by the next tier (the rules stand-in) and the reasoning says so. Nothing else outside the machine is called.
- **A secret may be exposed** (a password, phone key or session signer): reset the account with `python tools/enrol_dispatcher.py <username> dispatcher`, restart the app (new random session key), then investigate `auth_events`.
- **Contact:** the author, Dranzer Rogue, through an issue at https://github.com/DranzerZERogue56/disaster-response-coordination. After handoff, the owner is whoever the handoff document written in Week 14 names.

## 8. Last verified

Sections 2 (start), 3 (healthy output), 4 (enrol, seed, add a proposal, setup) and the numbers in section 5 were recorded by running `tools/m13_capture.py` on 2026-11-22 in a fresh clone on Windows 11 (Windows 11 Home, the author's machine; run by the assistant at the author's request). The failure entries are traced to the defect log but their fixes were not executed for this runbook. Not yet verified by a second person: see the status line at the top.
