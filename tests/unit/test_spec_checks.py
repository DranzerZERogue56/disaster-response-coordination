"""Checks on the documents themselves (Milestone 11): the specification can be tested, and the
defect log and traceability matrix agree with the tests. These are cheap and they catch the
documents drifting away from the code."""
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import build_traceability as trace

DEFECT_LOG = (REPO / "docs" / "defect-log.md").read_text(encoding="utf-8")
TEST_FILES = sorted((REPO / "tests").rglob("test_*.py"))


@pytest.mark.defect("DEF-008")
def test_no_must_requirement_sentence_contains_a_placeholder():
    text = (REPO / "docs" / "requirements.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    bad = []
    for m in re.finditer(r"^### (FR-[A-Z]+-\d+) .*?(?=^### |^## |\Z)", text, re.DOTALL | re.MULTILINE):
        block = m.group(0)
        priority = re.search(r"\*\*Priority:\*\*\s*(\w+)", block)
        sentence = re.search(r"\*\*Requirement:\*\*(.*)", block)
        if priority and priority.group(1) == "Must" and sentence and re.search(r"\[\s*X\s*\]|\[\s*TODO", sentence.group(1)):
            bad.append(m.group(1))
    assert bad == []


def test_every_criterion_a_test_claims_to_cover_exists_in_the_requirements():
    known = {cid for _, _, criteria in trace.parse_requirements() for cid, _ in criteria}
    claimed = set()
    for path in TEST_FILES:
        for args in re.findall(r"pytest\.mark\.covers\(([^)]*)\)", path.read_text(encoding="utf-8")):
            claimed |= set(re.findall(r'"([A-Z]+-[A-Z]+-\d+-AC\d+)"', args))
    assert claimed - known == set()


def test_every_defect_id_used_in_the_tests_is_in_the_defect_log():
    logged = set(re.findall(r"^\| (DEF-\d{3}) \|", DEFECT_LOG, re.MULTILINE))
    used = set()
    for path in TEST_FILES:
        text = path.read_text(encoding="utf-8")
        for args in re.findall(r"pytest\.mark\.defect\(([^)]*)\)", text):
            used |= set(re.findall(r"DEF-\d{3}", args))
    assert used - logged == set()


def test_every_defect_marked_fixed_names_a_regression_test_that_exists():
    all_tests = "\n".join(p.read_text(encoding="utf-8") for p in TEST_FILES)
    problems = []
    for line in DEFECT_LOG.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 9 and re.fullmatch(r"DEF-\d{3}", cells[0]) and cells[6] == "Fixed":
            name = cells[8].strip("`")
            if not re.search(rf"def {re.escape(name)}\(", all_tests):
                problems.append((cells[0], name))
    assert problems == []


def test_the_defect_log_has_at_least_eight_defects_with_all_seven_fields():
    reports = re.split(r"^### (DEF-\d{3}) .*$", DEFECT_LOG, flags=re.MULTILINE)[1:]
    ids = reports[0::2]
    bodies = reports[1::2]
    assert len(ids) >= 8
    for defect_id, body in zip(ids, bodies, strict=True):
        for field in ("Environment", "Steps", "Expected vs actual", "Evidence", "Severity", "Priority", "Traceability and status"):
            assert f"**{field}" in body, (defect_id, field)
        assert re.search(r"Severity S[1-4]", body) and re.search(r"Priority P[1-4]", body), defect_id
