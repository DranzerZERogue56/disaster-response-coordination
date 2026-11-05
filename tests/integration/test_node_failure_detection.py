"""Task 9: NFR-REL-01 measured with real processes: kill five nodes, time the alerts. Takes about 45 seconds."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import measure_heartbeat as mh


@pytest.mark.covers("NFR-REL-01-AC1")
def test_five_killed_node_processes_are_each_detected_within_thirty_seconds():
    results = mh.measure_detail(trials=5)

    assert len(results) == 5
    assert all(r["miss_to_alert_s"] is not None for r in results), f"a killed node was never detected: {results}"
    assert max(r["miss_to_alert_s"] for r in results) <= 30, results
    # the other agent and a human were told, once per dead node (not repeated by later polls)
    assert {r["survivor_notices"] for r in results} == {5} and {r["human_notices"] for r in results} == {5}


def test_the_report_names_the_limit_and_the_worst_case(tmp_path):
    target = tmp_path / "measurements.md"
    rows = [{"node_id": n, "miss_to_alert_s": 20.0 + n / 10, "kill_to_alert_s": 25.0 + n / 10} for n in range(2, 7)]
    mh.write_report(rows, path=target)
    text = target.read_text(encoding="utf-8")
    assert "NFR-REL-01" in text and "Worst case: 20.6 s against the 30 s limit (PASS)" in text
