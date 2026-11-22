"""tools/m13_capture.py: the recorded output must never contain a one-time password or phone key."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import m13_capture


def test_lines_with_a_password_or_phone_key_are_redacted():
    text = "Account ready: demo (dispatcher)\n  Password (shown once): hunter2hunter2\n  Phone setup key: ABCDEF\nThen start the app"
    shown = m13_capture.tail(text)
    assert "hunter2" not in shown and "ABCDEF" not in shown
    assert "Account ready" in shown and "Then start the app" in shown


def test_only_the_last_lines_are_kept_and_empty_output_is_said_plainly():
    assert m13_capture.tail("\n".join(str(n) for n in range(100))).splitlines()[-1] == "99"
    assert len(m13_capture.tail("\n".join(str(n) for n in range(100))).splitlines()) == m13_capture.TAIL_LINES
    assert m13_capture.tail("") == "(no output)"
