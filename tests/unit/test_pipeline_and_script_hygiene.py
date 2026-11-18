"""CI workflow and shell-script hygiene (docs/pipeline-security-audit.md). Plain-text checks: no YAML library is needed."""
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
SCRIPTS = sorted(p for p in (ROOT / "script").iterdir() if p.is_file() and p.name != "common.sh")
UNTRUSTED = re.compile(r"\$\{\{\s*(github\.event\.|github\.head_ref|github\.ref_name|inputs\.|steps\.[\w-]+\.outputs)")


def text(path):
    return path.read_text(encoding="utf-8")


def test_there_is_a_workflow_to_check():
    assert WORKFLOWS


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_every_action_is_pinned_to_a_full_commit_hash(workflow):
    uses = re.findall(r"^\s*-?\s*uses:\s*(\S+)", text(workflow), re.M)
    assert uses
    for ref in uses:
        assert re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", ref), f"{ref} is not pinned to a 40-character commit hash"


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_the_privileged_pull_request_trigger_is_never_used(workflow):
    assert "pull_request_target" not in text(workflow)
    assert "workflow_run" not in text(workflow)


@pytest.mark.defect("DEF-041")
@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_the_token_is_limited_to_reading_the_repository(workflow):
    body = text(workflow)
    top = re.search(r"^permissions:\s*\n((?:[ \t]+.*\n)+)", body, re.M)
    assert top, "the workflow has no top-level permissions block, so the token gets the repository default"
    assert re.findall(r"^\s+([\w-]+):\s*(\w+)", top.group(1), re.M) == [("contents", "read")]


@pytest.mark.defect("DEF-041")
@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_checkout_does_not_leave_the_token_in_the_git_config(workflow):
    body = text(workflow)
    for block in re.split(r"(?=^\s*-\s*uses:\s*actions/checkout)", body, flags=re.M)[1:]:
        assert re.search(r"persist-credentials:\s*false", block.split("\n      - ")[0])


@pytest.mark.defect("DEF-041")
@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_every_job_has_a_time_limit(workflow):
    assert "timeout-minutes:" in text(workflow)


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_no_run_step_places_untrusted_text_into_a_shell_command(workflow):
    runs = re.findall(r"^\s*run:\s*(?:\|\s*\n((?:[ \t]+.*\n)+)|(.*)\n)", text(workflow), re.M)
    for block, line in runs:
        assert not UNTRUSTED.search(block or line)


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_every_script_stops_on_the_first_error_and_never_traces_commands(script):
    body = text(script)
    assert re.search(r"^set -euo pipefail$", body, re.M), "a failing command must stop the script"
    assert not re.search(r"^\s*set\s+-\w*x|\bxtrace\b", body, re.M), "tracing would print secrets into the log"


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_no_script_evaluates_text_or_downloads_and_runs_code(script):
    body = text(script)
    assert not re.search(r"\beval\b|\bcurl\b|\bwget\b|\bsh -c\b|\bbash -c\b", body)


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_shell_variables_that_hold_paths_are_quoted(script):
    for number, line in enumerate(text(script).splitlines(), 1):
        code = line.split("#")[0]
        for match in re.finditer(r"(?<![\"\w{])\$(DB_PATH|PYTHON|PY)\b(?!\")", code):
            raise AssertionError(f"{script.name}:{number}: unquoted ${match.group(1)}")


@pytest.mark.parametrize("script", SCRIPTS + [ROOT / "script" / "common.sh"], ids=lambda p: p.name)
def test_every_script_parses(script):
    assert subprocess.run(["bash", "-n", str(script)], capture_output=True, check=False).returncode == 0  # noqa: S607
