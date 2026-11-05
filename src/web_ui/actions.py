"""What a dispatcher can do, in one place, so the JSON routes and the HTML console cannot drift apart.

Both callers pass the stand-in dispatcher's id (real login, FR-AUTH-01, is not built); errors propagate as
DecideError, RegistryError and OverrideError for the caller to turn into a status code or a message.
"""
from src.decide_proposal.service import decide_human
from src.negotiation.service import contest
from src.notify_responder.service import (
    NotifyError,
    notify_for_decision,
    notify_responder,
)
from src.override_assignment.service import override_assignment
from src.unit_registry.service import RegistryError, reserve_for_proposal


def try_notify(conn, decision):
    """Notify after an approval. A failed notification never undoes the
    decision; it is reported next to it so a person can see it."""
    try:
        return notify_for_decision(conn, decision)
    except NotifyError as exc:
        return {"error": {"code": exc.code, "message": str(exc)}}


def decide_with_retry(conn, proposal_id, decision, dispatcher_id, modified_unit_id=None):
    """Approve, modify or reject, then tell the unit that now holds the job."""
    try:
        result = decide_human(conn, proposal_id, decision, dispatcher_id, modified_unit_id=modified_unit_id)
    except RegistryError as exc:
        if exc.code != "UNIT_NO_LONGER_AVAILABLE" or decision != "approve":
            raise
        # FR-RES-01-AC2: the held unit was lost before the dispatcher decided. Give the
        # incident a second path to a responder (the proposal's alternatives) and approve
        # that; only if no unit can be had does the dispatcher get the error.
        reserve_for_proposal(conn, proposal_id, on_conflict=contest)
        result = decide_human(conn, proposal_id, "approve", dispatcher_id)
        result["retried_after_unit_loss"] = True
    result["notification"] = try_notify(conn, result)
    return result


def override_with_notice(conn, proposal_id, new_unit_id, reason, dispatcher_id):
    """Move an assignment to another unit, with a reason, and tell the unit that now holds it."""
    result = override_assignment(conn, proposal_id, new_unit_id, reason, dispatcher_id)
    try:
        result["notification"] = notify_responder(conn, proposal_id, result["new_unit_id"])
    except NotifyError as exc:
        result["notification"] = {"error": {"code": exc.code, "message": str(exc)}}
    return result
