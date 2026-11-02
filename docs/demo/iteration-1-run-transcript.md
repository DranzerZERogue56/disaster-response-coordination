# Iteration 1 demo: real run transcript
Run on 2026-11-02 03:32 UTC by `tools/demo_run.py` against the real app (fake model, seeded database). Elapsed times are real. This is the fallback record for `docs/demo/iteration-1-script.md`; the narrated screen recording is separate.

## [0:00] Fresh database and seed

Seeded state: two Medical units, one stand-in dispatcher.

```
SELECT id, unit_type, status FROM units
```
```json
[
  {
    "id": 1,
    "unit_type": "Medical",
    "status": "available"
  },
  {
    "id": 2,
    "unit_type": "Medical",
    "status": "available"
  }
]
```

## [0:01] Start the app and check it is healthy

`GET /healthz` -> HTTP 200

```json
{
  "status": "ok"
}
```

## [0:01] Report A (clear, happy path)

`POST /reports` -> HTTP 201

```json
{
  "decision": {
    "decided_at": "2026-11-02T03:32:19.993197+00:00",
    "decided_by": "auto",
    "final_status": "approved",
    "proposal_id": 1
  },
  "notification": {
    "notification_id": 1,
    "sent_at": "2026-11-02T03:32:19.998195+00:00",
    "unit_id": 1
  },
  "proposal": {
    "alternatives": [
      2
    ],
    "confidence": 95,
    "proposal_id": 1,
    "reasoning": "Matched 3 Medical keyword(s) in the report text.",
    "recommended_unit_id": 1,
    "severity": "Serious"
  },
  "received_at": "2026-11-02T03:32:19.970693+00:00",
  "report_id": 1,
  "reservation": {
    "reserved_until": "2026-11-02T03:36:19.987198+00:00",
    "retried": [],
    "unit_id": 1
  },
  "status": "created"
}
```

## [0:01] The proposal row in the database (model, confidence)

Proposal for Report A:

```
SELECT id, confidence, recommended_unit_id, model_identifier, final_status, decided_by FROM agent_proposals WHERE id = 1
```
```json
[
  {
    "id": 1,
    "confidence": 95,
    "recommended_unit_id": 1,
    "model_identifier": "fake-rules",
    "final_status": "approved",
    "decided_by": "auto"
  }
]
```

## [0:01] Confidence 75 or more and not Severe: auto-approved, unit assigned

Unit 1 after auto-approval:

```
SELECT id, status, reserved_by_proposal_id FROM units WHERE id = 1
```
```json
[
  {
    "id": 1,
    "status": "assigned",
    "reserved_by_proposal_id": 1
  }
]
```

## [0:01] Notify Responder: a notification row, not yet acknowledged

Notifications:

```
SELECT id, assignment_id, unit_id, sent_at, acknowledged_at FROM notifications
```
```json
[
  {
    "id": 1,
    "assignment_id": 1,
    "unit_id": 1,
    "sent_at": "2026-11-02T03:32:19.998195+00:00",
    "acknowledged_at": null
  }
]
```

## [0:01] Report B (vague): low confidence, held for a person

`POST /reports` -> HTTP 201

```json
{
  "decision": {
    "final_status": null,
    "held_for_human": true,
    "proposal_id": 2
  },
  "notification": null,
  "proposal": {
    "alternatives": [
      1
    ],
    "confidence": 40,
    "proposal_id": 2,
    "reasoning": "No recognizable keywords in the report; guessing Medical.",
    "recommended_unit_id": 2,
    "severity": "Moderate"
  },
  "received_at": "2026-11-02T03:32:20.037394+00:00",
  "report_id": 2,
  "reservation": {
    "reserved_until": "2026-11-02T03:36:20.052307+00:00",
    "retried": [],
    "unit_id": 2
  },
  "status": "created"
}
```
Proposal for Report B is still undecided:

```
SELECT id, confidence, final_status, decided_by FROM agent_proposals WHERE id = 2
```
```json
[
  {
    "id": 2,
    "confidence": 40,
    "final_status": null,
    "decided_by": null
  }
]
```

## [0:01] The visible reservation clock

`GET /units` -> HTTP 200

```json
{
  "units": [
    {
      "frees_at": null,
      "seconds_left": null,
      "status": "assigned",
      "unit_id": 1,
      "unit_type": "Medical"
    },
    {
      "frees_at": "2026-11-02T03:36:20.052307+00:00",
      "seconds_left": 239,
      "status": "reserved",
      "unit_id": 2,
      "unit_type": "Medical"
    }
  ]
}
```

## [0:01] Say out loud: there is no login yet

> There is no login yet. Anyone who can reach this address could press approve, and it always counts as the stand-in demo-dispatcher. Real login is planned before Milestone 12. This is a known, accepted gap for the demo.

## [0:01] The stand-in dispatcher approves Report B's proposal

`GET /proposals/pending` -> HTTP 200

```json
{
  "pending": [
    {
      "confidence": 40,
      "location": "near the old warehouse on 2nd",
      "proposal_id": 2,
      "reasoning": "No recognizable keywords in the report; guessing Medical.",
      "recommended_unit_id": 2,
      "report_id": 2,
      "severity": "Moderate"
    }
  ]
}
```
`POST /proposals/2/decision` -> HTTP 200

```json
{
  "decided_at": "2026-11-02T03:32:20.121708+00:00",
  "decided_by": "1",
  "final_status": "approved",
  "notification": {
    "notification_id": 2,
    "sent_at": "2026-11-02T03:32:20.126707+00:00",
    "unit_id": 2
  },
  "proposal_id": 2
}
```
Decided by the dispatcher's id, not 'auto':

```
SELECT id, final_status, decided_by, decided_at FROM agent_proposals WHERE id = 2
```
```json
[
  {
    "id": 2,
    "final_status": "approved",
    "decided_by": "1",
    "decided_at": "2026-11-02T03:32:20.121708+00:00"
  }
]
```

## [0:01] Report C (failure path): both Medical units are taken

`POST /reports` -> HTTP 409

```json
{
  "error": {
    "code": "UNIT_ALREADY_RESERVED",
    "message": "Every candidate unit is already taken: [1, 2]",
    "tried": [
      1,
      2
    ]
  },
  "proposal": {
    "alternatives": [
      2
    ],
    "confidence": 95,
    "proposal_id": 3,
    "reasoning": "Matched 3 Medical keyword(s) in the report text.",
    "recommended_unit_id": 1,
    "severity": "Severe"
  },
  "received_at": "2026-11-02T03:32:20.158424+00:00",
  "report_id": 3,
  "reservation": null,
  "status": "created"
}
```
Nothing was dispatched for C:

```
SELECT id, status, reserved_by_proposal_id FROM units ORDER BY id
```
```json
[
  {
    "id": 1,
    "status": "assigned",
    "reserved_by_proposal_id": 1
  },
  {
    "id": 2,
    "status": "assigned",
    "reserved_by_proposal_id": 2
  }
]
```

## [0:01] Run the test suite

```
........................................................................ [ 63%]
.........................................                                [100%]
113 passed in 28.15s
```

## [0:30] What is not done

Real dispatcher login (T-7.4) and the Scenario Reader (T-3.4). The classifier is a rules-based fake model; Ollama is the planned main model and is not wired in.
