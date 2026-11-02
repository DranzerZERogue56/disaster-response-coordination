#!/usr/bin/env python3
"""dbq.py - run one read-only SELECT against the project database and print
it as a small table. For demos and debugging; it cannot change anything.

    python tools/dbq.py "SELECT id, status FROM units"

Uses DB_PATH like the app does (default data/dev.sqlite).
"""
import os
import sqlite3
import sys


def main():
    if len(sys.argv) != 2 or not sys.argv[1].lstrip().lower().startswith("select"):
        sys.exit('usage: python tools/dbq.py "SELECT ..."  (SELECT statements only)')
    path = os.environ.get("DB_PATH", "data/dev.sqlite")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    cur = conn.execute(sys.argv[1])
    headers = [d[0] for d in cur.description]
    rows = [["" if v is None else str(v) for v in row] for row in cur.fetchall()]
    widths = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(headers)]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths, strict=True))
    print(line)
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(v.ljust(w) for v, w in zip(r, widths, strict=True)))
    conn.close()


if __name__ == "__main__":
    main()
