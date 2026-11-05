-- Migration 0005: node-failure alerts and the notices that go with them.
--
-- Raised as CR-008 (docs/change-requests/CR-008-heartbeat-alerts.md), Milestone 11 work plan Task 8
-- (FR-DEGRADE-01). A node that misses its heartbeat for 30 seconds (10 s x 3) is flagged
-- 'not_responding'; one alert row records the episode, and one notice row goes to each other agent that
-- is still alive plus one to a human. If the node resumes, the alert is marked as a late recovery and the
-- earlier notices are updated to say so, but the node's status becomes 'recovered' only after a human
-- confirms (agent_nodes already has CHECK status != 'recovered' OR recovered_confirmed_by IS NOT NULL).
--
-- Numbered 0005 because that number was left free; the runner applies by version, and these tables depend
-- on nothing in 0006 or 0007.
--
-- These tables hold node health, not incident data, so the 24-hour purge does not touch them.

PRAGMA foreign_keys = ON;

CREATE TABLE node_alerts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id        INTEGER NOT NULL REFERENCES agent_nodes(id),
    raised_at      TEXT NOT NULL,
    silent_seconds REAL NOT NULL,
    recovered_at   TEXT,
    confirmed_at   TEXT,
    confirmed_by   INTEGER REFERENCES dispatcher_accounts(id),
    CHECK ((confirmed_at IS NULL) = (confirmed_by IS NULL)),
    CHECK (confirmed_at IS NULL OR recovered_at IS NOT NULL)
);

CREATE INDEX idx_node_alerts_node ON node_alerts(node_id);

CREATE TABLE node_notices (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id      INTEGER NOT NULL REFERENCES node_alerts(id),
    audience      TEXT NOT NULL CHECK (audience IN ('agent', 'human')),
    to_node_id    INTEGER REFERENCES agent_nodes(id),
    message       TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    updated_at    TEXT,
    late_recovery INTEGER NOT NULL DEFAULT 0 CHECK (late_recovery IN (0, 1)),
    CHECK ((audience = 'agent') = (to_node_id IS NOT NULL))
);

CREATE INDEX idx_node_notices_alert ON node_notices(alert_id);
