-- Migration 0003: override follow-ups become their own append-only table.
--
-- Raised as CR-002 (docs/change-requests/CR-002-append-only-override-follow-ups.md)
-- after Milestone 10 self-review finding 7.2. FR-RES-02 lets a dispatcher keep
-- adding to an override's explanation, with no time limit. Doing that by editing
-- one text column meant the log could be rewritten. Now every follow-up is a new
-- row, and neither a follow-up nor an override row can be edited afterwards.
-- (Deleting stays possible: the 24-hour purge job, NFR-PRIV-01, needs it.)

PRAGMA foreign_keys = ON;

CREATE TABLE override_follow_ups (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    override_id            INTEGER NOT NULL REFERENCES dispatcher_overrides(id),
    dispatcher_account_id  INTEGER NOT NULL REFERENCES dispatcher_accounts(id),
    text                   TEXT NOT NULL CHECK (length(trim(text)) > 0),
    added_at               TEXT NOT NULL
);

CREATE INDEX idx_override_follow_ups_override ON override_follow_ups(override_id);

CREATE TRIGGER override_follow_ups_no_edit
BEFORE UPDATE ON override_follow_ups
BEGIN
    SELECT RAISE(ABORT, 'follow-ups are append-only: add a new one instead of editing');
END;

CREATE TRIGGER dispatcher_overrides_no_edit
BEFORE UPDATE ON dispatcher_overrides
BEGIN
    SELECT RAISE(ABORT, 'the override log is append-only: record a follow-up instead of editing');
END;
