"""Data access for units: the one place that writes SQL about the `units` table (pilot data-access layer).

The services (src/unit_registry/service.py and the modules that use it) ask this class questions in the language of the
domain ("try to reserve unit 3 for proposal 7") and get plain Python values back, never database rows or cursors. Nothing
above it knows which database is underneath, so a later move to PostgreSQL means writing a second class with the same
methods and no change to the business rules (docs/superpowers/plans/2026-11-18-database-options.md).

Rules kept here:
  * Every value travels as a bound parameter; no SQL text is built from variables (enforced by
    tests/unit/test_architecture_boundaries.py).
  * It never commits: the caller owns the transaction, so approving a proposal and assigning its unit stay atomic.
  * The check-and-change statements are single UPDATEs with the condition in the WHERE clause, so two callers can never
    both win a unit; the methods report whether they did (`True` or `False`).
"""


class UnitRepository:
    def __init__(self, conn):
        self._conn = conn

    def all_units(self):
        rows = self._conn.execute("SELECT id, unit_type, status, released_expected_by FROM units ORDER BY id").fetchall()
        return [{"id": r[0], "unit_type": r[1], "status": r[2], "released_expected_by": r[3]} for r in rows]

    def status_of(self, unit_id):
        row = self._conn.execute("SELECT status FROM units WHERE id = ?", (unit_id,)).fetchone()
        return row[0] if row else None

    def try_reserve(self, unit_id, proposal_id, reserved_at, until):
        cur = self._conn.execute(
            "UPDATE units SET status = 'reserved', reserved_by_proposal_id = ?, "
            "reserved_at = ?, released_expected_by = ? WHERE id = ? AND status = 'available'",
            (proposal_id, reserved_at, until, unit_id),
        )
        return cur.rowcount == 1

    def free_reserved(self, unit_id):
        cur = self._conn.execute(
            "UPDATE units SET status = 'available', reserved_by_proposal_id = NULL, "
            "reserved_at = NULL, released_expected_by = NULL WHERE id = ? AND status = 'reserved'",
            (unit_id,),
        )
        return cur.rowcount == 1

    def reserved_by(self, proposal_id):
        rows = self._conn.execute(
            "SELECT id FROM units WHERE status = 'reserved' AND reserved_by_proposal_id = ?", (proposal_id,)
        ).fetchall()
        return [r[0] for r in rows]

    def expired_reservations(self, stamp):
        rows = self._conn.execute(
            "SELECT id, reserved_by_proposal_id FROM units WHERE status = 'reserved' AND released_expected_by <= ?", (stamp,)
        ).fetchall()
        return [(r[0], r[1]) for r in rows]

    def try_assign(self, unit_id, proposal_id):
        cur = self._conn.execute(
            "UPDATE units SET status = 'assigned', released_expected_by = NULL "
            "WHERE id = ? AND status = 'reserved' AND reserved_by_proposal_id = ?",
            (unit_id, proposal_id),
        )
        return cur.rowcount == 1

    def assigned_unit_of(self, proposal_id):
        row = self._conn.execute(
            "SELECT id FROM units WHERE reserved_by_proposal_id = ? AND status = 'assigned'", (proposal_id,)
        ).fetchone()
        return row[0] if row else None

    def release_assigned(self, unit_id):
        cur = self._conn.execute(
            "UPDATE units SET status = 'available', reserved_by_proposal_id = NULL, "
            "reserved_at = NULL, released_expected_by = NULL WHERE id = ? AND status = 'assigned'",
            (unit_id,),
        )
        return cur.rowcount == 1

    def try_assign_available(self, unit_id, proposal_id, at):
        cur = self._conn.execute(
            "UPDATE units SET status = 'assigned', reserved_by_proposal_id = ?, reserved_at = ?, "
            "released_expected_by = NULL WHERE id = ? AND status = 'available'",
            (proposal_id, at, unit_id),
        )
        return cur.rowcount == 1

    def undecided_holder(self, unit_id):
        """The proposal holding this unit as a reservation that nobody has decided yet, or None."""
        row = self._conn.execute(
            "SELECT u.reserved_by_proposal_id FROM units u JOIN agent_proposals p ON p.id = u.reserved_by_proposal_id "
            "WHERE u.id = ? AND u.status = 'reserved' AND p.final_status IS NULL",
            (unit_id,),
        ).fetchone()
        return row[0] if row else None
