"""What each agent knows about the units (docs/architecture.md section 5), Milestone 11 / FR-RES-03.

Publishing happens in the database (migration 0008: a trigger on `units` writes an event and one inbox row per
other agent node), so no writer can skip it. This module reads the result:

  * `agent_view(conn, node_id)` is one agent's picture of every unit's status in its scenario run: its own
    units straight from the registry, every other unit from the latest update delivered to it (a unit it has
    heard nothing about is shown as available). An update cached for a node that was down does not appear
    until `deliver_cached` runs, which the heartbeat does when the node responds again.
  * `choices(conn, node_id)` is the unit ids that agent sees as available: a unit another agent reserved is
    not among them, which is how a reservation excludes the unit from the other agents' decisions.
"""


def _node(conn, node_id):
    node = conn.execute("SELECT scenario_run_id FROM agent_nodes WHERE id = ?", (node_id,)).fetchone()
    if node is None:
        raise LookupError(f"No agent node with id {node_id}")
    return node["scenario_run_id"]


def agent_view(conn, node_id):
    """{unit_id: status} as this agent sees it."""
    run_id = _node(conn, node_id)
    view = {}
    for unit in conn.execute("SELECT id, status, agent_node_id FROM units WHERE scenario_run_id = ? ORDER BY id", (run_id,)):
        view[unit["id"]] = unit["status"] if unit["agent_node_id"] == node_id else "available"
    for update in conn.execute(
        "SELECT e.unit_id, e.status FROM agent_inboxes i JOIN unit_events e ON e.id = i.event_id "
        "WHERE i.node_id = ? AND i.delivered_at IS NOT NULL ORDER BY e.id",
        (node_id,),
    ):
        if update["unit_id"] in view:
            view[update["unit_id"]] = update["status"]  # later events overwrite earlier ones, so the view never goes backwards
    return view


def choices(conn, node_id):
    """The unit ids this agent may propose: those it sees as available."""
    return [unit_id for unit_id, status in agent_view(conn, node_id).items() if status == "available"]


def deliver_cached(conn, node_id, stamp):
    """Deliver everything cached for a node that responds again. Returns how many updates were delivered."""
    cur = conn.execute(
        "UPDATE agent_inboxes SET delivered_at = ? WHERE node_id = ? AND delivered_at IS NULL", (stamp, node_id)
    )
    return cur.rowcount
