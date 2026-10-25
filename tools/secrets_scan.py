#!/usr/bin/env python3
"""CI secrets check (Milestone 9 Medium tier: "automate the boring check").

Scans every tracked file for the same secret-shape patterns used in the
one-time full-history audit (docs/skeleton-trace.md). Fails the build if
a tracked file matches — this is the check that never gets tired.
"""
import re
import subprocess
import sys

PATTERN = re.compile(
    r"(api[_-]?key|secret[_-]?key|password\s*=|AKIA[0-9A-Z]{16}"
    r"|-----BEGIN (RSA|OPENSSH|PGP) PRIVATE KEY-----"
    r"|token\s*=\s*['\"][A-Za-z0-9_\-]{10,}"
    r"|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,})",
    re.IGNORECASE,
)

# Known-safe matches: column names, not secrets.
ALLOWLIST = ("password_hash", "password_salt")


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    )
    return [line for line in out.stdout.splitlines() if line]


def main():
    hits = []
    for path in tracked_files():
        if path == "tools/secrets_scan.py":
            continue  # this file necessarily contains the pattern itself
        try:
            with open(path, encoding="utf-8") as f:
                for lineno, line in enumerate(f, start=1):
                    if any(allowed in line for allowed in ALLOWLIST):
                        continue
                    if PATTERN.search(line):
                        hits.append(f"{path}:{lineno}: {line.strip()}")
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue

    if hits:
        print("SECRETS CHECK FAILED:")
        for hit in hits:
            print(" ", hit)
        sys.exit(1)

    print("secrets check: 0 matches across %d tracked files" % len(tracked_files()))


if __name__ == "__main__":
    main()
