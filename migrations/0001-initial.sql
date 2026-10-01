-- Migration 0001 — initial schema
-- Disaster Response Coordination
-- See docs/architecture.md §6 for the full entity descriptions, invariants,
-- and the reasoning behind each design choice (node granularity, key style,
-- the no-separate-assignments-table decision, the 24h purge exception for
-- scenario_runs).

PRAGMA foreign_keys = ON;

CREATE TABLE scenario_runs (
    id                               INTEGER PRIMARY KEY AUTOINCREMENT,
    mode                             TEXT NOT NULL CHECK (mode IN ('batch', 'interactive')),
    scenario_file                    TEXT NOT NULL,
    team_size_config                 TEXT NOT NULL,
    started_at                       TEXT NOT NULL,
    finished_at                      TEXT,
    score                            REAL,
    unresolved_would_escalate_count  INTEGER NOT NULL DEFAULT 0,
    CHECK ( (finished_at IS NULL) OR (score IS NOT NULL) )
);

CREATE TABLE dispatcher_accounts (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    username                    TEXT NOT NULL UNIQUE,
    password_hash               TEXT NOT NULL,
    password_salt               TEXT NOT NULL,
    role                        TEXT NOT NULL CHECK (role IN ('admin', 'dispatcher', 'observer')),
    is_fictional_test_account   INTEGER NOT NULL DEFAULT 1 CHECK (is_fictional_test_account IN (0, 1)),
    created_at                  TEXT NOT NULL
);

CREATE TABLE agent_nodes (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_run_id         INTEGER NOT NULL REFERENCES scenario_runs(id),
    role_type               TEXT NOT NULL CHECK (role_type IN ('Medical', 'Fire', 'Shelter', 'Security', 'IncidentCommand')),
    status                  TEXT NOT NULL CHECK (status IN ('alive', 'not_responding', 'recovered')),
    last_heartbeat_at       TEXT NOT NULL,
    recovered_confirmed_by  INTEGER REFERENCES dispatcher_accounts(id),
    CHECK ( (status != 'recovered') OR (recovered_confirmed_by IS NOT NULL) )
);

CREATE TABLE units (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_run_id           INTEGER NOT NULL REFERENCES scenario_runs(id),
    unit_type                 TEXT NOT NULL CHECK (unit_type IN ('Medical', 'Fire', 'Shelter', 'Security')),
    agent_node_id             INTEGER NOT NULL REFERENCES agent_nodes(id),
    status                    TEXT NOT NULL CHECK (status IN ('available', 'reserved', 'assigned', 'out_of_service')),
    reserved_by_proposal_id   INTEGER REFERENCES agent_proposals(id),  -- forward reference: SQLite resolves FKs at write time, not at CREATE TABLE time, so this is valid even though agent_proposals is defined below
    reserved_at               TEXT,
    released_expected_by      TEXT,
    CHECK ( (status != 'available') OR (reserved_by_proposal_id IS NULL) ),
    CHECK ( (status NOT IN ('reserved', 'assigned')) OR (reserved_by_proposal_id IS NOT NULL) )
);

CREATE TABLE incident_reports (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_run_id      INTEGER NOT NULL REFERENCES scenario_runs(id),
    location             TEXT NOT NULL,
    severity_raw         TEXT NOT NULL,
    severity             TEXT CHECK (severity IN ('Minor', 'Moderate', 'Serious', 'Severe', 'Critical')),
    timestamp_reported   TEXT NOT NULL,
    reporting_unit       TEXT NOT NULL,
    description          TEXT,
    status               TEXT NOT NULL CHECK (status IN ('queued', 'created', 'classified', 'duplicate_merged')),
    duplicate_of_id      INTEGER REFERENCES incident_reports(id),
    received_at          TEXT NOT NULL,
    CHECK ( (status IN ('queued', 'created')) OR (severity IS NOT NULL) OR (status = 'duplicate_merged') ),
    CHECK ( (status != 'duplicate_merged') OR (duplicate_of_id IS NOT NULL) )
);

CREATE TABLE agent_proposals (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id               INTEGER NOT NULL REFERENCES incident_reports(id),
    agent_node_id           INTEGER NOT NULL REFERENCES agent_nodes(id),
    confidence              INTEGER NOT NULL CHECK (confidence BETWEEN 0 AND 100),
    recommended_unit_id     INTEGER NOT NULL REFERENCES units(id),
    reasoning               TEXT NOT NULL,
    alternatives            TEXT NOT NULL,  -- JSON array of unit ids
    model_identifier        TEXT NOT NULL,
    model_version           TEXT NOT NULL,
    decided_by              TEXT,
    final_status            TEXT CHECK (final_status IN ('approved', 'modified', 'rejected', 'unresolved_would_escalate')),
    generated_at            TEXT NOT NULL,
    decided_at              TEXT,
    CHECK ( (decided_at IS NULL) = (final_status IS NULL) )
);

CREATE TABLE dispatcher_overrides (
    id                               INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id                    INTEGER NOT NULL REFERENCES agent_proposals(id),
    dispatcher_account_id            INTEGER NOT NULL REFERENCES dispatcher_accounts(id),
    new_unit_id                      INTEGER NOT NULL REFERENCES units(id),
    original_agent_choice_unit_id    INTEGER NOT NULL REFERENCES units(id),
    reason                           TEXT NOT NULL CHECK (length(trim(reason)) > 0),
    follow_up_explanation            TEXT,
    ai_escalated_at                  TEXT,
    overridden_at                    TEXT NOT NULL,
    CHECK ( (ai_escalated_at IS NULL) OR (ai_escalated_at <= overridden_at) )
);

CREATE TABLE notifications (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id      INTEGER NOT NULL REFERENCES agent_proposals(id),
    unit_id            INTEGER NOT NULL REFERENCES units(id),
    sent_at            TEXT NOT NULL,
    acknowledged_at    TEXT  -- reserved for FR-ALERT-02, not populated by v0.1 logic
);

-- Indexes on the columns every purge job and every lookup in §5's
-- interfaces actually filters or joins on.
CREATE INDEX idx_incident_reports_run ON incident_reports(scenario_run_id);
CREATE INDEX idx_incident_reports_received_at ON incident_reports(received_at);
CREATE INDEX idx_agent_proposals_report ON agent_proposals(report_id);
CREATE INDEX idx_units_run ON units(scenario_run_id);
CREATE INDEX idx_units_reserved_by ON units(reserved_by_proposal_id);
CREATE INDEX idx_agent_nodes_run ON agent_nodes(scenario_run_id);
