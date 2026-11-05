-- Migration 0006: the tiebreak log and the human-escalation queue.
--
-- Raised as CR-006 (docs/change-requests/CR-006-tiebreak-log-and-escalations.md), Milestone 11 work plan
-- Task 5. FR-COORD-01 requires that a tiebreak resolution is "logged as having followed the correct
-- protocol"; the log records both richness scores so a stranger can recompute the result (ADR 0007).
-- human_escalations is where an incident lands when the system cannot place it and a person must: nothing
-- is allowed to disappear silently. Task 10 (the model fallback chain) writes to it too.

PRAGMA foreign_keys = ON;

CREATE TABLE tiebreak_log (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    winner_proposal_id  INTEGER NOT NULL REFERENCES agent_proposals(id),
    loser_proposal_id   INTEGER NOT NULL REFERENCES agent_proposals(id),
    pair_low            INTEGER NOT NULL,
    pair_high           INTEGER NOT NULL,
    reason              TEXT NOT NULL CHECK (reason IN ('severity', 'richness', 'reported-first', 'true-tie')),
    winner_richness     INTEGER NOT NULL,
    loser_richness      INTEGER NOT NULL,
    protocol_followed   INTEGER NOT NULL CHECK (protocol_followed IN (0, 1)),
    resolved_at         TEXT NOT NULL,
    UNIQUE (pair_low, pair_high),
    CHECK (winner_proposal_id != loser_proposal_id)
);

CREATE INDEX idx_tiebreak_log_winner ON tiebreak_log(winner_proposal_id);
CREATE INDEX idx_tiebreak_log_loser ON tiebreak_log(loser_proposal_id);

-- Resolving the same pair again returns the logged answer; the log is never edited.
CREATE TRIGGER tiebreak_log_no_edit
BEFORE UPDATE ON tiebreak_log
BEGIN
    SELECT RAISE(ABORT, 'the tiebreak log is append-only');
END;

CREATE TABLE human_escalations (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id      INTEGER NOT NULL REFERENCES incident_reports(id),
    proposal_id    INTEGER REFERENCES agent_proposals(id),
    reason         TEXT NOT NULL,
    created_at     TEXT NOT NULL,
    resolved_at    TEXT,
    resolved_by    INTEGER REFERENCES dispatcher_accounts(id),
    CHECK ((resolved_at IS NULL) = (resolved_by IS NULL))
);

CREATE INDEX idx_human_escalations_report ON human_escalations(report_id);
