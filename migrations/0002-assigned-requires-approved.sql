-- Migration 0002: a unit is "assigned" only while its proposal is approved.
--
-- Raised as CR-001 (docs/change-requests/CR-001-assigned-requires-approved.md)
-- after the Milestone 10 self-review (finding 3.2). The application already
-- approves and assigns in one transaction; these triggers make the rule hold
-- for every writer, including a hand-typed UPDATE, a future module, or a bug.
--
-- "Approved" here means final_status is 'approved' (agent or dispatcher said
-- yes) or 'modified' (a dispatcher said yes with a different unit, see
-- Override Assignment). 'rejected' and NULL (undecided) never allow it.

PRAGMA foreign_keys = ON;

-- 1. A unit cannot be inserted as assigned unless its proposal is approved.
CREATE TRIGGER units_assigned_requires_approved_on_insert
BEFORE INSERT ON units
WHEN NEW.status = 'assigned'
 AND COALESCE((SELECT final_status FROM agent_proposals WHERE id = NEW.reserved_by_proposal_id), 'none')
     NOT IN ('approved', 'modified')
BEGIN
    SELECT RAISE(ABORT, 'a unit can only be assigned while its proposal is approved');
END;

-- 2. A unit cannot become assigned unless its proposal is approved.
CREATE TRIGGER units_assigned_requires_approved_on_update
BEFORE UPDATE ON units
WHEN NEW.status = 'assigned'
 AND COALESCE((SELECT final_status FROM agent_proposals WHERE id = NEW.reserved_by_proposal_id), 'none')
     NOT IN ('approved', 'modified')
BEGIN
    SELECT RAISE(ABORT, 'a unit can only be assigned while its proposal is approved');
END;

-- 3. The other direction: an approved proposal cannot be un-approved
--    (rejected, or set back to undecided) while a unit is still assigned to it.
CREATE TRIGGER proposals_stay_approved_while_unit_assigned
BEFORE UPDATE OF final_status ON agent_proposals
WHEN OLD.final_status IN ('approved', 'modified')
 AND NEW.final_status IS NOT 'approved'
 AND NEW.final_status IS NOT 'modified'
 AND EXISTS (SELECT 1 FROM units WHERE reserved_by_proposal_id = OLD.id AND status = 'assigned')
BEGIN
    SELECT RAISE(ABORT, 'a proposal cannot stop being approved while a unit is assigned to it');
END;
