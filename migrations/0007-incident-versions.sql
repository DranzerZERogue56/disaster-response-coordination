-- Migration 0007: versions of an incident, and the reconciliation log.
--
-- Raised as CR-007 (docs/change-requests/CR-007-incident-versions.md), Milestone 11 work plan Task 6
-- (FR-COORD-02). Two agents can hold different, differently-timestamped pictures of the same incident.
-- The newer picture becomes the active record and the older one is kept as history, never deleted;
-- a human can override the automatic choice, and the override is logged like an Override Assignment:
-- who, when, why, and what the original automatic decision was.

PRAGMA foreign_keys = ON;

CREATE TABLE incident_versions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id        INTEGER NOT NULL REFERENCES incident_reports(id),
    agent_node_id    INTEGER NOT NULL REFERENCES agent_nodes(id),
    data             TEXT NOT NULL,
    data_timestamp   TEXT NOT NULL,
    active           INTEGER NOT NULL DEFAULT 0 CHECK (active IN (0, 1)),
    recorded_at      TEXT NOT NULL,
    superseded_at    TEXT
);

CREATE INDEX idx_incident_versions_report ON incident_versions(report_id);
-- at most one active version per incident
CREATE UNIQUE INDEX one_active_version_per_report ON incident_versions(report_id) WHERE active = 1;

-- What a version says cannot be rewritten; record a newer one instead. (Only active and superseded_at
-- change, when reconciliation runs. Rows are deleted only by the 24-hour retention purge.)
CREATE TRIGGER incident_versions_data_is_final
BEFORE UPDATE OF report_id, agent_node_id, data, data_timestamp, recorded_at ON incident_versions
BEGIN
    SELECT RAISE(ABORT, 'a recorded incident version cannot be changed; record a newer one');
END;

CREATE TABLE reconciliation_log (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id             INTEGER NOT NULL REFERENCES incident_reports(id),
    kind                  TEXT NOT NULL CHECK (kind IN ('automatic', 'override')),
    original_version_id   INTEGER NOT NULL REFERENCES incident_versions(id),
    chosen_version_id     INTEGER NOT NULL REFERENCES incident_versions(id),
    decided_by            INTEGER REFERENCES dispatcher_accounts(id),
    reason                TEXT,
    decided_at            TEXT NOT NULL,
    CHECK ((kind = 'override') = (decided_by IS NOT NULL)),
    CHECK (kind != 'override' OR length(trim(coalesce(reason, ''))) > 0)
);

CREATE INDEX idx_reconciliation_log_report ON reconciliation_log(report_id);

CREATE TRIGGER reconciliation_log_no_edit
BEFORE UPDATE ON reconciliation_log
BEGIN
    SELECT RAISE(ABORT, 'the reconciliation log is append-only');
END;
