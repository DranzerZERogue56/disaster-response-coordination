#!/usr/bin/env python3
"""plan-check.py - turn a work breakdown into an honest answer.

Reads a WBS CSV (see wbs-sample.csv), computes PERT expected effort per task,
calibrates it against tasks you have already finished, lays the total against
your remaining weekly capacity, and reports the first week the plan goes over.

Usage:
  python3 plan-check.py wbs-sample.csv
  python3 plan-check.py wbs-sample.csv --buffer 0.25 --exclude WP-5,WP-3
  python3 plan-check.py my-wbs.csv --capacity 4,11,12,12,12,12,12,6,5 --start-week 8

Nothing here is magic. Read it, change the numbers, argue with the verdict.
"""
import argparse
import csv
import sys
from collections import OrderedDict

DEFAULT_CAPACITY = "4,12,12,12,12,12,12,6,5"  # project hours per week, Weeks 8-16


def pert(o, m, p):
    """PERT expected effort and standard deviation."""
    return (o + 4 * m + p) / 6.0, (p - o) / 6.0


def load(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if not r.get("task_id"):
                continue
            o, m, p = (float(r[k]) for k in ("optimistic", "likely", "pessimistic"))
            if not (o <= m <= p):
                sys.exit("Bad estimate on %s: need optimistic <= likely <= pessimistic" % r["task_id"])
            r["exp"], r["sd"] = pert(o, m, p)
            r["actual"] = float(r["actual_hours"]) if r.get("actual_hours") else None
            rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wbs")
    ap.add_argument("--capacity", default=DEFAULT_CAPACITY)
    ap.add_argument("--start-week", type=int, default=8)
    ap.add_argument("--buffer", type=float, default=0.25)
    ap.add_argument("--exclude", default="", help="comma-separated work-package OR task ids to cut")
    a = ap.parse_args()

    rows = load(a.wbs)
    cut = {s.strip() for s in a.exclude.split(",") if s.strip()}
    cap = [float(x) for x in a.capacity.split(",")]

    done = [r for r in rows if r["status"].strip().lower() == "done"]
    de, da = sum(r["exp"] for r in done), sum(r["actual"] or 0 for r in done)
    factor = (da / de) if de else 1.0

    print("\nCALIBRATION")
    print("  completed tasks         %d" % len(done))
    print("  expected (PERT)         %.1f h" % de)
    print("  actually logged         %.1f h" % da)
    print("  your factor             %.2fx%s" % (factor, "   (thin sample - trust it loosely)" if len(done) < 8 else ""))

    packs = OrderedDict()
    for r in rows:
        if r["status"].strip().lower() == "done":
            continue
        packs.setdefault(r["wp_id"], {"name": r["wp_name"], "n": 0, "raw": 0.0, "var": 0.0})
        if r["wp_id"] in cut or r["task_id"] in cut:
            continue
        packs[r["wp_id"]]["n"] += 1
        packs[r["wp_id"]]["raw"] += r["exp"]
        packs[r["wp_id"]]["var"] += r["sd"] ** 2

    print("\nREMAINING WORK")
    total = var = 0.0
    for wp, d in packs.items():
        mark = "  [CUT]" if wp in cut else ""
        print("  %-6s %-28s %2d tasks  %6.1f h raw  %6.1f h calibrated%s"
              % (wp, d["name"][:28], d["n"], d["raw"], d["raw"] * factor, mark))
        total += d["raw"] * factor
        var += d["var"] * factor ** 2
    sd = var ** 0.5
    print("  %-6s %-28s           %6.1f h raw  %6.1f h calibrated" % ("TOTAL", "", total / factor, total))
    print("  rough P80 (calibrated + 0.84 sd)                     %6.1f h" % (total + 0.84 * sd))

    raw_cap = sum(cap)
    plannable = raw_cap * (1 - a.buffer)
    print("\nCAPACITY  (weeks %d-%d)" % (a.start_week, a.start_week + len(cap) - 1))
    print("  raw capacity            %.1f h" % raw_cap)
    print("  project buffer (%d%%)     %.1f h" % (round(a.buffer * 100), raw_cap - plannable))
    print("  plannable               %.1f h" % plannable)

    gap = total - plannable
    print("\n  VERDICT: %s" % ("OVER BUDGET by %.1f h - cut, defer, or re-estimate" % gap if gap > 0
                               else "fits, with %.1f h to spare" % -gap))

    print("\nBURN-DOWN   (negative projected = slack; your buffer, still untouched)")
    print("  week  capacity   ideal   projected")
    rem, ideal, first_over = total, plannable, None
    for i, c in enumerate(cap):
        wk = a.start_week + i
        if first_over is None and rem > sum(cap[i:]):
            first_over = wk
        print("  %4d  %8.1f  %6.1f  %10.1f" % (wk, c, ideal, rem))
        rem, ideal = rem - c, max(0.0, ideal - c * (1 - a.buffer))
    print("  end   %8s  %6.1f  %10.1f" % ("-", 0.0, rem))
    if rem > 0:
        print("\n  Runs out of weeks with %.1f h still on the board." % rem)
    if first_over:
        print("  Plan first exceeds remaining capacity in week %d." % first_over)


if __name__ == "__main__":
    main()
