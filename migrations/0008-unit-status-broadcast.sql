-- Migration 0008: every unit status change is published to every other agent.
--
-- Raised as CR-010 (docs/change-requests/CR-010-unit-status-broadcast.md), Milestone 11 work plan Task 14
-- (FR-RES-03, acceptance criteria 1-3). When a unit's status changes (reserved, assigned, released, taken out
-- of service) every other agent node must see the change; if a node cannot receive it, the update is cached
-- for that node and a warning goes to the other agents; a reservation is timestamped and visible to the others
-- so their decisions exclude that unit.
--
-- Done as a trigger on units, in the same spirit as the other database rules (0002, 0006, 0007): the registry,
-- the decide module, the override, the tiebreak and the purge all write units.status, and a rule that held
-- only for the callers who remembered it would not be a rule. The publishing cannot be skipped.
--
-- unit_events is the history of status changes. agent_inboxes is one row per (event, receiving node):
-- delivered at once to a node that is alive or recovered, cached (delivered_at NULL) for a node that is
-- not_responding until the node responds again (src/heartbeat/service.py delivers them in event order). The
-- unit's own agent node is the source of its changes, so it gets no inbox row for them.
--
-- `at` is the reservation timestamp when the unit has one (the moment the proposal reserved it), otherwise the
-- real clock; `recorded_at` is always the real clock. proposal_id is not a foreign key: it is history, and the
-- 24-hour purge deletes events for purged proposals.

PRAGMA foreign_keys = ON;

CREATE TABLE unit_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id     INTEGER NOT NULL REFERENCES units(id),
    status      TEXT NOT NULL,
    proposal_id INTEGER,
    at          TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE INDEX idx_unit_events_unit ON unit_events(unit_id);

CREATE TABLE agent_inboxes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id     INTEGER NOT NULL REFERENCES unit_events(id),
    node_id      INTEGER NOT NULL REFERENCES agent_nodes(id),
    delivered_at TEXT,
    cached       INTEGER NOT NULL DEFAULT 0 CHECK (cached IN (0, 1)),
    CHECK ((cached = 1) OR (delivered_at IS NOT NULL))
);

CREATE INDEX idx_agent_inboxes_node ON agent_inboxes(node_id, event_id);

CREATE TRIGGER units_status_published
AFTER UPDATE OF status ON units
WHEN OLD.status != NEW.status
BEGIN
    INSERT INTO unit_events (unit_id, status, proposal_id, at, recorded_at)
    VALUES (
        NEW.id,
        NEW.status,
        NEW.reserved_by_proposal_id,
        COALESCE(NEW.reserved_at, strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now')),
        strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now')
    );

    INSERT INTO agent_inboxes (event_id, node_id, delivered_at, cached)
    SELECT last_insert_rowid(),
           n.id,
           CASE WHEN n.status = 'not_responding' THEN NULL ELSE strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now') END,
           CASE WHEN n.status = 'not_responding' THEN 1 ELSE 0 END
    FROM agent_nodes n
    WHERE n.id != NEW.agent_node_id AND n.scenario_run_id = NEW.scenario_run_id;

    -- a warning to the agents that can still be reached, for every node the update could not be delivered to
    INSERT INTO node_notices (alert_id, audience, to_node_id, message, created_at)
    SELECT (SELECT MAX(a.id) FROM node_alerts a WHERE a.node_id = down.id),
           'agent',
           up.id,
           'Status update for unit ' || NEW.id || ' (' || NEW.status || ') could not be delivered to node ' || down.id || ' and was cached.',
           strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now')
    FROM agent_nodes down, agent_nodes up
    WHERE down.status = 'not_responding'
      AND down.id != NEW.agent_node_id
      AND down.scenario_run_id = NEW.scenario_run_id
      AND up.status != 'not_responding'
      AND up.id != down.id
      AND up.id != NEW.agent_node_id
      AND up.scenario_run_id = NEW.scenario_run_id
      AND EXISTS (SELECT 1 FROM node_alerts a WHERE a.node_id = down.id);
END;
