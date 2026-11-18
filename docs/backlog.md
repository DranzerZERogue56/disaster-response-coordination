# Backlog

Proposed by the assistant from the repo's records (2026-11-15). **Dispositions, ordering and every estimate marked "Ben to confirm" are Ben's.** Acceptance criteria are copied intact from `docs/requirements.md` (v1.4); where the requirement still holds a `TODO` placeholder, that placeholder is copied as it stands. Estimates marked PERT are `(O + 4M + P) / 6` from `docs/wbs.csv`, as in `docs/plan.md`.

| ID | Item | Requirement | Source | Estimate (h) | Priority in spec |
|---|---|---|---|---:|---|
| B-01 | Duplicate report detection | FR-INTAKE-03 | Milestone 7 deferral, `docs/plan.md` section 7, CR-012 (draft) | 4.17 (T-3.3) | Won't (this release) |
| B-02 | Hardware capability check | FR-INFER-03 | Milestone 7 deferral, CR-012 (draft) | 1.17 (T-2.1b) | Won't (this release) |
| B-03 | Zone boundary display | FR-MAP-01 | Milestone 7 deferral, CR-012 (draft) | 4.17 (T-10.2 + T-12.4) | Won't (this release) |
| B-04 | A real way to notify a responder | FR-ALERT-01 | DEF-017; peer reviewer, Milestone 10, Q10 | Ben to confirm | Must |
| B-05 | Notification acknowledgment tracking | FR-ALERT-02 | not built; `docs/test-plan.md` section 2 | Ben to confirm (T-8.1 holds the reserved column; its PERT is 2.00 for the whole task, not for this) | Should |
| B-06 | Reasoning timeout of about 60 s | FR-AGENT-04 | no test, no verified row in `docs/traceability.csv` | 2.00 (T-4.3, PERT) | Should |
| B-07 | Login and roles | FR-AUTH-01 | DEF-018 | Ben to confirm | Should |
| B-08 | Decide whether a far-future report time is rejected | FR-INTAKE-02 | DEF-020 | Ben to confirm | Must |
| B-09 | Unit positions on the dashboard | FR-MAP-02 | not built; `docs/test-plan.md` section 2 | Ben to confirm | Could |
| B-10 | Verify the two target-hardware Musts | FR-INFER-02, NFR-PERF-01 | `docs/test-results.md` ("Must requirements not yet verified") | Ben to confirm | Must |

Other Should and Could requirements with no test and no verified row in `docs/traceability.csv` (FR-COORD-04, FR-DEGRADE-03, FR-DEGRADE-04, FR-INFER-04, NFR-REL-04, NFR-USE-01) are not given backlog items here: whether they are built is not stated in the records read for this file. **Ben to confirm** whether any belongs on the backlog.

---

## B-01: Duplicate report detection (FR-INTAKE-03)
- **Source:** Milestone 7 scope decision (`docs/plan.md` section 7, 2026-10-10), recorded retroactively in CR-012 (draft). The `incident_reports` table already supports it (`duplicate_of_id`, `docs/architecture.md` section 6).
- **Estimate:** 4.17 h, the hours recovered by deferring T-3.3 (PERT 2 / 4 / 7).
- **Acceptance criteria (copied intact):**
  - Given two reports are submitted within 1 block and 10 minutes of each other, when their addresses match or their event descriptions describe the same kind of event (e.g., "building on fire" and "burning house" both describing a structure fire), then the system tags them as the same incident and combines both reports' data to improve accuracy.
  - Given two reports are submitted within 1 block and 10 minutes of each other but their addresses are different, when the system checks them, then it does not merge them and keeps them as separate incidents — the address field is what the system uses to make that distinction.

## B-02: Hardware capability check (FR-INFER-03)
- **Source:** Milestone 7 scope decision, CR-012 (draft). A failed model load still surfaces an error through FR-DEGRADE-02's fallback chain.
- **Estimate:** 1.17 h, the hours recovered by deferring T-2.1b (PERT 1 / 1 / 2).
- **Acceptance criteria (copied intact; the requirement still holds placeholders):**
  - `[ TODO — Given..., when..., then... ]`
  - `[ TODO — Given <failure case>..., when..., then... ]`
- **Note:** these cannot be tested until Ben writes them.

## B-03: Zone boundary display (FR-MAP-01)
- **Source:** Milestone 7 scope decision, CR-012 (draft). The requirement's own rationale named it as the first thing to slip.
- **Estimate:** 4.17 h, the hours recovered by deferring T-10.2 and its demo-clip task T-12.4 together.
- **Acceptance criteria (copied intact; placeholders):**
  - `[ TODO — Given..., when..., then... ]`
  - `[ TODO — Given <failure case>..., when..., then... ]`

## B-04: A real way to notify a responder (FR-ALERT-01, DEF-017)
- **Source:** DEF-017 (S3/P3, Open): "Notify" writes a `notifications` row and nothing leaves the machine. The peer reviewer's answer to Q10 in Milestone 10: "there should be a way to do it in the software". The delivery channel is open question OQ-2 (`docs/architecture.md` section 11).
- **Estimate:** Ben to confirm.
- **Acceptance criteria (copied intact):**
  - Given an assignment has been finalized, when the system notifies the assigned responder, then the notification is sent within 10 seconds of the assignment being finalized.
  - Given a unit that is not assigned to an approved proposal (for example a unit that is only reserved for a proposal still waiting for a dispatcher, a unit whose proposal was rejected, or a unit assigned to a different incident), when the system is asked to notify that unit, then no notification is recorded for it, the system answers that the unit is not assigned, and the assignment it was asked about is left unchanged, so that a responder is never told to go somewhere nobody has approved.
- **Note in the requirement:** criteria wording is from Ben's answers of 2026-11-05 (CR-003), put into Given/when/then form by the assistant; Ben to confirm the wording.

## B-05: Notification acknowledgment tracking (FR-ALERT-02)
- **Source:** not built. `notifications.acknowledged_at` exists but is never populated (`migrations/0001-initial.sql`, `src/notify_responder/service.py`). OQ-2 (what the acknowledgment channel is) blocks it.
- **Estimate:** Ben to confirm.
- **Acceptance criteria (copied intact; placeholders):**
  - `[ TODO — Given..., when..., then... ]`
  - `[ TODO — Given <failure case>..., when..., then... ]`
- **Note:** the requirement text also contains a literal "[X] minutes" placeholder (the same kind of defect as DEF-008). **Ben to confirm** the number.

## B-06: Reasoning timeout of about 60 seconds (FR-AGENT-04)
- **Source:** `docs/traceability.csv` shows no test for FR-AGENT-04-AC1 or AC2. The assistant has not verified in this task how far the model chain's per-call time cap (default 60 s, CR-011 draft) and its retries cover this requirement. **Ben to confirm** whether it counts as built.
- **Estimate:** 2.00 h (T-4.3, PERT 1 / 2 / 3, from `docs/wbs.csv`; status in the file: open).
- **Acceptance criteria (copied intact):**
  - Given a reasoning attempt completes within ~60 seconds, when it finishes, then it produces a proposal as normal.
  - Given a reasoning attempt exceeds ~60 seconds without producing a proposal, when the timeout triggers, then the system abandons it, returns an error to the human overseer, and falls back to a non-LLM path instead of continuing to wait.

## B-07: Login and roles (FR-AUTH-01, DEF-018)
- **Progress, 2026-11-15:** the two-factor sign-in core was built and is in v0.9.0-rc.2 (password plus a time-based phone code, sessions, forgery tokens, enrolment command; DEF-018 Fixed). **Still open under this item:** a trusted "private computer" rule, the station IP allow-list, a QR code for the phone app, role levels beyond admin/dispatcher/observer, a password-change page, and a service key so field reports, the scenario tool and node heartbeats can reach the app while the gate is on (DEF-032).
- **Additions from Ben, 2026-11-15 (security review areas 3 and 4):** a second authentication factor so dispatchers are confirmed to be real dispatchers; optionally an allow-list of the station's IP address as one extra layer (weak on its own, since addresses can be shared or forged); role levels so each level of dispatcher has the powers its role needs and nothing is blocked that a role legitimately needs.
- **Ben's requirement statement for the login (2026-11-15, chat, lightly tidied):** "I do want a login, but dual authentication needs to be a part of the login. The login should be quick and easy using a secure method. They need to have a private computer, and they also need to have their phone on them that is confirmed to be that person's own phone, so that they can confirm their identity in two ways while logging in, like the app Duo Mobile."
- **Facts for designing it (assistant, Ben to confirm before relying on them):** (1) A Duo push goes through Duo's cloud (an account, an API key and a live connection), so it adds a third-party dependency that must be documented (slow, down, rate-limited, changed) and it fails when the internet is down, which matters for an emergency tool. (2) A time-based one-time code from an authenticator app on the person's own phone works offline and needs no cloud; Duo Mobile can also hold such codes. (3) "A private computer" needs a concrete rule (for example a trusted-device cookie after first sign-in, or the station's address on an allow-list); an address alone is weak. (4) FR-AUTH-01 is currently a Should; this wording would change it, so Ben writes the change request and the new requirement text.
- **Proposed acceptance criteria (assistant, Ben to confirm):** Given no session, when anyone requests a page or posts an action, then they are sent to the sign-in page and nothing changes. Given a correct password and a correct code from the person's enrolled phone, when they sign in, then they get a session of limited length. Given a correct password and a wrong or reused code, then sign-in is refused and the attempt is logged. Given an `observer`, when they try to approve, then it is refused (and the existing role tests run through the real routes). Given a sign-in from a computer that is not the person's trusted one, then a second confirmation is required. Given any state-changing form, then it carries a per-session token that a foreign page cannot supply.
- **Source:** DEF-018 (S2/P2, Open): there is no login, so anyone who reaches the server can approve or override. The defect log states it must not ship v1.0 like this.
- **Estimate:** Ben to confirm.
- **Acceptance criteria (copied intact):**
  - Given a user takes an action their role permits (for example the admin creating, changing, or deleting records), when the action runs, then it is recorded in a log file where only put (add an entry) and get (read entries) are allowed, and no one, including the admin, can delete entries.
  - Given a user attempts an action outside their role (for example a dispatcher test account trying to delete records directly), when the attempt is made, then it is blocked and the attempt is logged.

## B-08: Decide whether a far-future report time is rejected (FR-INTAKE-02, DEF-020)
- **Source:** DEF-020 (S4/P3, Open): a report stamped in 2099 is accepted. The specification does not say whether the future is a "bad value". The defect log says this needs Ben's decision on a margin.
- **Estimate:** Ben to confirm.
- **Acceptance criteria (copied intact; unchanged by this item until Ben decides):**
  - Given a report is submitted with one field missing or improperly filled, when the system validates it, then it returns a rejection response identifying that field and, where a regex pattern applies to that field, an explanation of what's wrong with the format.
  - Given a report is submitted with multiple bad or missing fields, when the system validates it, then it evaluates fields top-down and returns a rejection response listing all of the bad fields, so the sender sees every problem at once instead of fixing one and resubmitting to find the next.

## B-09: Unit positions on the dashboard (FR-MAP-02)
- **Source:** not built; Could priority.
- **Estimate:** Ben to confirm.
- **Acceptance criteria (copied intact; placeholders):**
  - `[ TODO — Given..., when..., then... ]`
  - `[ TODO — Given <failure case>..., when..., then... ]`

## B-10: Verify the two target-hardware Musts (FR-INFER-02, NFR-PERF-01)
- **Source:** `docs/test-results.md`: both name the target hardware (RTX 3090 or 4090, 24 GB) and a real model, neither of which was available, so they stay unverified. A fake-model measurement exists in `docs/measurements.md` but is not claimed as verification.
- **Estimate:** Ben to confirm.
- **Acceptance criteria, FR-INFER-02 (copied intact):**
  - Given a report, when the agent returns a classification or a proposal, then it returns within 5 seconds on the target hardware (RTX 3090 or 4090, 24 GB VRAM).
  - `[ TODO — left blank on purpose (CR-003): a failure-case criterion for the 5-second limit needs a real model on the target hardware (RTX 3090 or 4090), which is neither wired in nor available yet. Ben to write it when the model is connected (Milestone 12). ]`
- **Criterion, NFR-PERF-01 (copied intact from the requirements table):** Report classification (FR-AGENT-01) completes within 5 s of intake, p95 over 20 seeded reports, on the target hardware (24 GB GPU, local model). Verification method: Script timestamps intake to severity tag for 20 runs; p95 recorded in `docs/measurements.md`.
- **Related:** CR-014 (REJECT, 2026-11-15) rejects the target-hardware sections in favour of one demo model; this item stays as the record of what would be needed to verify the two requirements.

## B-11: HTTPS for the dispatcher app and the model connection (CR-013, DEFER)
- **Source:** `docs/change-requests/CR-013-https-transport.md` (Ben, 2026-11-15): everything speaks plain HTTP today (the app on 127.0.0.1:8080, the Ollama client to a model server on this machine); the move to HTTPS is a bigger change deferred to the next build period.
- **Destination:** the build period about two weeks from 2026-11-15 (roughly the week of 2026-11-29, Milestone 14).
- **Estimate:** Ben to confirm.
- **Acceptance criteria (proposed by the assistant, Ben to confirm):**
  - Given the app is started with the documented command, when a browser opens the console, then it is served over HTTPS (a self-signed certificate for localhost is acceptable and documented).
  - Given the model client is configured with an `https` URL to this machine, when it classifies a report, then the call succeeds; and given a non-local host, then it is still refused.
  - Given the existing loopback-only tests, when the transport changes, then they still pass with the scheme rule updated in one place.

## B-12: Dependency audit in CI, an update cadence, and a purpose line for every package (proposed from Ben's security-review input)
- **Source:** Ben, 2026-11-15, security review area 6: audit all packages, check installed versions, update regularly, know what each does, be able to swap them.
- **Estimate:** Ben to confirm.
- **Acceptance criteria (proposed by the assistant, Ben to confirm):**
  - Given a push, when CI runs, then `pip-audit -r requirements.txt` runs and the build fails on a High or Critical advisory unless Ben has recorded a reasoned exception.
  - Given `requirements.txt`, when someone reads `docs/dependencies.md`, then each of the pinned packages has a one-line purpose, a licence and the date it was last reviewed, and the update cadence (for example monthly) is written down.

## B-13: Retention policy: keep a month, long-term storage, confidential data kept apart (proposed; conflicts with NFR-PRIV-01 as written)
- **Source:** Ben, 2026-11-15, security review area 7: record every dispatcher action and every major AI decision; keep at least a month after the incident; then possibly long-term storage; some data points confidential and stored elsewhere to keep people anonymous.
- **Needs a change request first:** NFR-PRIV-01 (Must) says incident data is purged 24 hours after receipt, and `src/purge/job.py` implements that. Ben writes the change request and any new requirement text.
- **Estimate:** Ben to confirm.
- **Acceptance criteria (proposed, Ben to confirm):** Given the new retention rule is approved, when an incident is older than the retention period, then it moves to the long-term store or is deleted as the rule says, and the decision and override trail is kept; and given a field marked confidential, when the record is stored, then that field lives in a separate store and the main record holds only a reference.

## B-14: Measure the load a model puts on the machine (CPU, memory, GPU) and judge whether the chosen models do the job (proposed from Ben's security-review input)
- **Source:** Ben, 2026-11-15, area 8: make sure the models can do the job fairly well and do not overwork the PC.
- **Estimate:** Ben to confirm.
- **Acceptance criteria (proposed, Ben to confirm):** Given the 20 seeded reports, when each model classifies them, then peak memory and CPU and GPU use are recorded in `docs/performance.md` with the machine named; and given a labelled set of reports, then the share classified to the expected severity and unit type is recorded for each model.

## B-15: SUPERSEDED by B-17 (PostgreSQL migration; ADR 0009 was replaced by ADR 0010). Kept for history.
- **Source:** Ben, 2026-11-18, for a real multi-user deployment. Staged after Milestone 13.
- **Steps:** (1) put the rest of the SQL behind repositories (units is done: `src/data/units_repo.py`): proposals, reports, accounts, logs, nodes; (2) port the nine migrations and the 11 triggers to PostgreSQL; (3) a second repository implementation with the same methods; (4) run the whole suite against both; (5) re-measure NFR-MNT-01 and the timing NFRs; (6) a change request in Ben's words (it changes the stack).
- **Estimate:** Ben to confirm (the assistant's rough view: several days).
- **Acceptance criteria (proposed, Ben to confirm):** Given the app is configured for PostgreSQL, when the test suite runs, then it passes. Given two dispatchers act at the same moment, then no unit is double-booked. Given a clean clone, then the README's steps reach a running app within the NFR-MNT-01 limit.

## B-16: An allow-list input-validation layer at the web boundary (proposed from Ben's database request)
- **Source:** Ben, 2026-11-18: include data input filtering so that no one can use SQL injection. The database already receives every value as a bound parameter; this adds a second layer.
- **Estimate:** Ben to confirm.
- **Acceptance criteria (proposed, Ben to confirm):** Given any route that takes text, when a value contains SQL-looking text, operator-looking keys (a dollar sign key) or control characters, then it is either stored as plain text or refused with a clear error, never run as a command. Given a field outside the allowed names, types or lengths, then it is refused. A test fails the build if a route skips the validation.

## B-17: Migrate the data store from SQLite to MongoDB, hardened (ADR 0010; needs a change request first)
- **Source:** Ben, 2026-11-18, reversing the PostgreSQL choice. Staged after Milestone 13.
- **Steps:** (1) finish the repository layer (units done; proposals, reports, accounts, logs, nodes remain); (2) a MongoDB repository implementation with the same methods; (3) move each of the 11 triggers and the CHECK/foreign-key rules into code plus `$jsonSchema` validators and unique indexes, one rule at a time, each with a test that fails first; (4) a single-node replica set, because multi-document transactions need one; (5) apply `docs/database-hardening.md`; (6) run the whole suite against both stores; (7) re-measure NFR-MNT-01 and the timing NFRs; (8) a change request in Ben's words (it changes the stack).
- **Estimate:** Ben to confirm (the assistant's rough view: longer than the PostgreSQL port, because rules move from the database into code).
- **Acceptance criteria (proposed, Ben to confirm):** Given the app is configured for MongoDB, when the suite runs, then it passes. Given two dispatchers reserve the same unit at once, then exactly one succeeds. Given the hardening checklist, then every line has a recorded check Ben ran.

