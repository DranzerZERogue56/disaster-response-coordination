# Iteration 1 Demo Script — Milestone 10

Run on seeded data (`seed/iteration-1.sql` or equivalent, committed). Five slices, five minutes, one failure path shown on purpose.

**Slices closed this iteration:**
1. Classify & Propose — FR-AGENT-01, FR-AGENT-02
2. Resource/Unit Registry `reserve()` — FR-RES-01, FR-RES-03
3. Decide Proposal auto-path — FR-AGENT-03, NFR-SEC-02
4. Decide Proposal escalation branch (human intervention, auth stubbed this week) — FR-AGENT-03, NFR-SEC-02
5. Notify Responder — FR-ALERT-01

**Seed data (to commit under `seed/`):**
- One `scenario_run` (interactive mode)
- One `Medical` agent node, two `Medical` units (`unit-med-1`, `unit-med-2`) — deliberately only two, so the failure-path beat can exhaust them
- Report A — happy path: location "4th & Main St", severity_raw "person fell, visible leg injury, conscious and talking," reporting_unit "field-unit-7"
- Report B — escalation path: location "near the old warehouse on 2nd", severity_raw "something happened, not sure how bad, no one's answering", description empty — deliberately vague, aimed at a sub-75 confidence classification
- Report C — failure path: a Medical-needing report submitted after Reports A and B hold both Medical units, so reserve() finds nothing free (HTTP 409)

<!-- MODEL SWAP: to demo on Ollama instead of the fake model, (1) set CLASSIFY_MODEL=ollama once that model class exists, and (2) in the 1:00 beat below, replace "fake-rules (the rules-based stand-in; Ollama is not wired in yet and the script says so out loud)" with "phi4-mini:latest (ADR 0001 amendment -- the dev-laptop fallback model, not the GPU-server target)". No code or seed changes needed. -->

---

```
0:00  "This is Milestone 10's core increment: a report comes in, an agent classifies
       it, reserves a real unit, and either auto-decides or escalates to a human --
       end to end, on the real SQLite database Milestone 9 proved out."
0:20  Terminal: start the app (./script/start). Confirm /healthz is ok.
0:35  Submit Report A (curl or the Web UI). Point at the response: severity,
      confidence, recommended_unit_id.
1:00  Show the database row directly: the proposal landed in agent_proposals with
      a confidence score and model_identifier = fake-rules (the rules-based
      stand-in; Ollama is not wired in yet and the script says so out loud).
1:20  Confidence >= 75 -> Decide Proposal's auto-path fires. Show
      agent_proposals.final_status = 'approved', decided_by = 'auto', and the
      unit's status go from 'reserved' to 'assigned' in the units table.
1:45  Notify Responder fires. Show the new row in notifications -- sent_at set,
      acknowledged_at still null (FR-ALERT-02 is Should-priority, not built yet).
2:10  Submit Report B (the vague one). Point out the lower confidence score in
      the response.
2:30  Confidence < 75 -> escalates instead of auto-deciding. Show the proposal
      sitting with final_status still NULL, decided_by still NULL -- pending.
2:50  curl localhost:8080/proposals/pending, then POST /proposals/2/decision with {"decision":"approve"} (the stubbed demo-dispatcher decides; no login yet).
      Show final_status flip to 'approved', decided_by set to the dispatcher's
      id, not 'auto' -- the audit trail tells the two paths apart.
      SAY OUT LOUD: "There is no login yet. Anyone who can reach this address could press
      approve, and it always counts as the stand-in demo-dispatcher. Real login is
      planned before Milestone 12. This is a known, accepted gap for the demo."
3:15  Submit Report C. Report A's unit is assigned and Report B's unit is
      held for the dispatcher (or assigned, after the 2:50 approval), so both
      Medical units are taken.
3:35  FAILURE PATH: the response is HTTP 409 UNIT_ALREADY_RESERVED, listing both
      units it tried (the recommended one, then the alternative). The report
      and proposal rows stay in place, nothing is dispatched. The retry
      (next-best unit when one is free) is shown by the test suite at 4:10,
      not live.
4:10  Terminal: run the test suite. Point at the tests covering slices 1-5.
4:35  "Not done yet this iteration: the offline queue (T-3.2), real dispatcher
      login replacing today's stubbed identity (T-7.4), and the Scenario Reader
      for scripted playback (T-3.4). All three are GitHub issues already, with
      Milestone 10/11 as the target."
4:55  Stop talking.
```

## What's not done, and when

| Deferred | Why | Scheduled |
|---|---|---|
| Offline queue (FR-INTAKE-01's queued path) | Not part of this week's money-path chain | Milestone 11 (tracked: issue for T-3.2) |
| Real dispatcher auth (FR-AUTH-01, T-7.4) | Slice 5's escalation branch uses a stubbed single dispatcher identity this week — building real login/session this week risked the scope-creep trap Milestone 9 warned about | Its own slice, before Milestone 12 |
| Scenario Reader / scripted playback (FR-SIM-01, T-3.4) | Not part of this week's money-path chain | Milestone 11 |
| Override Assignment (FR-RES-02) | Milestone 10's human-intervention slice covers the *escalation* branch only, not post-decision overrides, per this week's scoping decision | Milestone 11 or 12 |

## Open question going in

On the fake model, Report B reliably scores 40 (no recognizable keywords), so the escalation beat is deterministic. <!-- OLLAMA: when the real model is used, Report B's wording is a best guess at producing a sub-75 confidence from `phi4-mini`, and depends on the model's actual output, not a fixed rule. If the real run doesn't land under 75, tune the report text until it reliably does, and note the tuning in `docs/ai-usage.md` if AI helped pick the wording. -->
