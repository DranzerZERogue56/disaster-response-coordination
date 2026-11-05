"""Play a scenario file against the running app: python tools/play_scenario.py FILE --speed 10

This is an operator tool, not app code: it lives in tools/ because src/ must import no network client
(tests/acceptance, NFR-SEC-01).

Each report is POSTed to the app's /reports route. A reply from the app, even a refusal, is printed and the
play continues (a refusal is part of what a scenario can show). If the app cannot be reached the play stops
with that error. The exit code is 0 only if every report was delivered.
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.scenario.reader import ScenarioFileInvalid, play_scenario


def post_report(base_url, payload):
    """POST one report; returns the HTTP status. Raises URLError if the app cannot be reached."""
    request = urllib.request.Request(
        base_url.rstrip("/") + "/reports",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


def main(argv=None):
    parser = argparse.ArgumentParser(description="Replay a prewritten scenario at a controlled pace.")
    parser.add_argument("file", help="scenario JSON file, e.g. seed/scenarios/demo-scenario.json")
    parser.add_argument("--speed", type=float, default=1.0, help="2 means twice as fast as the scenario's own gaps")
    parser.add_argument("--url", default="http://127.0.0.1:8080", help="where the app is listening")
    args = parser.parse_args(argv)

    sent = []

    def submit(payload):
        status = post_report(args.url, payload)
        sent.append(status)
        print(f"report {len(sent)}: {payload.get('location', '?')} -> HTTP {status}", flush=True)

    try:
        result = play_scenario(args.file, args.speed, submit)
    except (ScenarioFileInvalid, ValueError) as exc:
        print(f"cannot play: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"stopped after {len(sent)} report(s): {exc}", file=sys.stderr)
        return 1
    print(f"scenario run {result['run_id']} finished: {result['reports_queued']} reports at speed {args.speed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
