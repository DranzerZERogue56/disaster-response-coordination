-- Migration 0004: a proposal records the input data the agent used.
--
-- Raised as CR-004 (docs/change-requests/CR-004-proposal-input-data.md) after the Milestone 11
-- acceptance test for FR-AUDIT-01-AC1 failed (defect DEF-014): the proposal log held the agent's
-- confidence and reasoning but not the data it had been given, only a pointer (report_id) to a row
-- that can be purged after 24 hours (NFR-PRIV-01). Ben's criterion: "It should include input data."
--
-- input_data is a JSON snapshot of the report fields the agent read, written at the moment the
-- proposal is generated. It is nullable only so proposals logged before this migration stay valid.
-- Once written it cannot be changed: a log that can be edited afterwards does not show the agent's
-- actual reasoning (FR-AUDIT-01).

PRAGMA foreign_keys = ON;

ALTER TABLE agent_proposals ADD COLUMN input_data TEXT;

CREATE TRIGGER agent_proposals_input_data_is_final
BEFORE UPDATE OF input_data ON agent_proposals
WHEN OLD.input_data IS NOT NULL AND NEW.input_data IS NOT OLD.input_data
BEGIN
    SELECT RAISE(ABORT, 'the logged input data of a proposal cannot be changed');
END;
