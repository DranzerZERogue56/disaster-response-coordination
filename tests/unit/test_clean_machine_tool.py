"""Task 1: the clean-machine test follows the README, times it, and fails honestly (NFR-MNT-01)."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import clean_machine_test as cm

README = (REPO / "README.md").read_text(encoding="utf-8")


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_the_steps_are_the_readme_steps():
    assert cm.readme_steps(README) == ["./script/setup", "./script/start"]


def test_it_passes_when_setup_is_fast_and_the_app_answers():
    clock = Clock()

    def run_command(step, cwd):
        clock.now += 90  # setup takes 90 seconds
        return True

    result = cm.run(README, "x", run_command, lambda step, cwd: object(), lambda: True, clock)
    assert result["ok"] is True and result["seconds"] == 90 and result["steps"] == ["./script/setup", "./script/start"]


def test_it_fails_when_setup_takes_five_minutes():
    clock = Clock()

    def run_command(step, cwd):
        clock.now += 300  # exactly at the limit is not "under 5 minutes"
        return True

    result = cm.run(README, "x", run_command, lambda step, cwd: object(), lambda: True, clock)
    assert result["ok"] is False and result["seconds"] == 300


def test_it_fails_when_healthz_never_answers():
    result = cm.run(README, "x", lambda step, cwd: True, lambda step, cwd: object(), lambda: False, Clock())
    assert result["ok"] is False and result["failed_step"] == "healthz never answered"


def test_it_fails_and_names_the_step_when_a_readme_command_fails():
    result = cm.run(README, "x", lambda step, cwd: False, lambda step, cwd: object(), lambda: True, Clock())
    assert result["ok"] is False and result["failed_step"] == "./script/setup"
    assert result["steps"] == ["./script/setup"]  # it stops at the first failure


def test_the_app_it_started_is_stopped():
    stopped = []

    class App:
        def terminate(self):
            stopped.append(True)

    cm.run(README, "x", lambda step, cwd: True, lambda step, cwd: App(), lambda: True, Clock())
    assert stopped == [True]
