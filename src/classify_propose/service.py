"""Classify & Propose (docs/architecture.md §5) — Milestone 10, slice 1.

Serves FR-AGENT-01 (tag a created report with a severity) and
FR-AGENT-02 (write a proposal: recommended unit, confidence, reasoning,
alternatives). The model is passed in, so tests use a fake and the real
one can be swapped in without touching this file (see model.py).

Not here yet, on purpose: reserving the unit (slice 2) and deciding or
escalating the proposal by confidence (slices 3-4).
"""
import json
from datetime import UTC, datetime

from src.classify_propose.model import SEVERITIES, UNIT_TYPES

# The report fields the agent is given; recorded with the proposal (FR-AUDIT-01, CR-004).
INPUT_FIELDS = ("location", "severity_raw", "description", "timestamp_reported", "reporting_unit")


class ClassifyError(Exception):
    """The report could not be classified; a human has to handle it."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def _validate(output):
    """A model's answer is only trusted if it has exactly the shape we need: both labels in their
    allowed sets, a confidence that is a real whole number from 0 to 100 (not a boolean, a float or
    text), and a reasoning that is non-empty text (DEF-015: it used to accept None, numbers and lists)."""
    try:
        ok = (
            isinstance(output["severity"], str)
            and output["severity"] in SEVERITIES
            and isinstance(output["unit_type"], str)
            and output["unit_type"] in UNIT_TYPES
            and type(output["confidence"]) is int
            and 0 <= output["confidence"] <= 100
            and isinstance(output["reasoning"], str)
            and output["reasoning"].strip() != ""
        )
    except (KeyError, TypeError):
        ok = False
    if not ok:
        raise ClassifyError("MODEL_OUTPUT_INVALID", f"Model output failed validation: {output!r}")


def classify_and_propose(conn, report_id, model):
    report = conn.execute(
        "SELECT * FROM incident_reports WHERE id = ?", (report_id,)
    ).fetchone()
    if report is None:
        raise ClassifyError("REPORT_NOT_FOUND", f"No report with id {report_id}")

    if report["status"] != "created":
        raise ClassifyError(
            "ALREADY_CLASSIFIED", f"Report {report_id} is already {report['status']}"
        )

    output = model.classify(dict(report))
    _validate(output)

    # Prefer free units; if none are free, still propose the best of the
    # rest rather than nothing (FR-AGENT-02 acceptance criterion 2).
    units = conn.execute(
        """
        SELECT id, agent_node_id FROM units
        WHERE scenario_run_id = ? AND unit_type = ? AND status != 'out_of_service'
        ORDER BY (status = 'available') DESC, id
        """,
        (report["scenario_run_id"], output["unit_type"]),
    ).fetchall()
    if not units:
        raise ClassifyError(
            "NO_UNIT_OF_TYPE", f"No {output['unit_type']} unit exists for this scenario run"
        )

    best, others = units[0], units[1:]
    now = datetime.now(UTC).isoformat()
    cur = conn.execute(
        """
        INSERT INTO agent_proposals
            (report_id, agent_node_id, confidence, recommended_unit_id, reasoning,
             alternatives, model_identifier, model_version, generated_at, input_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_id,
            best["agent_node_id"],
            output["confidence"],
            best["id"],
            output["reasoning"],
            json.dumps([u["id"] for u in others]),
            model.identifier,
            model.version,
            now,
            json.dumps(
                {k: report[k] for k in INPUT_FIELDS},
                sort_keys=True,
            ),
        ),
    )
    conn.execute(
        "UPDATE incident_reports SET severity = ?, status = 'classified' WHERE id = ?",
        (output["severity"], report_id),
    )
    conn.commit()
    return {
        "proposal_id": cur.lastrowid,
        "severity": output["severity"],
        "confidence": output["confidence"],
        "recommended_unit_id": best["id"],
        "alternatives": [u["id"] for u in others],
        "reasoning": output["reasoning"],
    }
