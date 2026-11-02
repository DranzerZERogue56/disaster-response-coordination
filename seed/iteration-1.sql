-- Seed data for the Milestone 10 demo (docs/demo/iteration-1-script.md).
-- Apply to a FRESH database, after migrations/0001-initial.sql:
--     sqlite3 data/dev.sqlite < seed/iteration-1.sql
-- Creates one interactive scenario run, one Medical agent node, and exactly
-- two Medical units, so the demo's failure-path beat can run them out.
--
-- MODEL: the demo runs on the FAKE model for now (CLASSIFY_MODEL defaults to
-- "fake", see src/classify_propose/model.py), so nothing below needs to
-- change. When Ollama exists, switch by setting CLASSIFY_MODEL, not by
-- editing this file.
--
-- The three demo reports are submitted live (POST /reports), not seeded.
-- Copy-paste payloads:
--
--   Report A, happy path (fake model: Serious, confidence 90+):
--     {"location":"4th & Main St",
--      "severity_raw":"person fell, visible leg injury, conscious and talking",
--      "timestamp_reported":"2026-11-01T12:00:00+00:00","reporting_unit":"field-unit-7"}
--
--   Report B, escalation path (fake model: confidence 40, under the 75 line):
--     {"location":"near the old warehouse on 2nd",
--      "severity_raw":"something happened, not sure how bad, no one's answering",
--      "timestamp_reported":"2026-11-01T12:05:00+00:00","reporting_unit":"field-unit-7"}
--
--   Report C, failure path (A and B already hold both Medical units, so C gets the 409):
--     {"location":"900 Elm Ave",
--      "severity_raw":"man collapsed, chest pain, not breathing well",
--      "timestamp_reported":"2026-11-01T12:10:00+00:00","reporting_unit":"field-unit-3"}

PRAGMA foreign_keys = ON;

INSERT INTO scenario_runs (mode, scenario_file, team_size_config, started_at)
VALUES ('interactive', 'iteration-1-demo', '{}', '2026-11-01T12:00:00+00:00');

INSERT INTO agent_nodes (scenario_run_id, role_type, status, last_heartbeat_at)
VALUES (1, 'Medical', 'alive', '2026-11-01T12:00:00+00:00');

INSERT INTO units (scenario_run_id, unit_type, agent_node_id, status)
VALUES (1, 'Medical', 1, 'available'),
       (1, 'Medical', 1, 'available');

-- The stand-in dispatcher for the escalation path (slice 4). Fictional, and
-- the hash/salt are placeholders: there is no login yet (FR-AUTH-01 is
-- deferred), so nothing ever checks them.
INSERT INTO dispatcher_accounts
    (username, password_hash, password_salt, role, is_fictional_test_account, created_at)
VALUES ('demo-dispatcher', 'not-a-real-hash', 'not-a-real-salt', 'dispatcher', 1,
        '2026-11-01T12:00:00+00:00');
