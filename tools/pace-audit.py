#!/usr/bin/env python3
"""pace-audit.py - the Week 8 halfway audit for a 240-hour capstone.

Reads the hours log you started in Week 1 and tells you, without flattery,
where you are against the budget: 16 weeks, 15 hours a week, 240 hours.

It reads the log exactly as you created it in Week 1 -- same columns, no
editing, no second format:

    date,start,end,hours,phase,hat,task,estimate_hours,blocked_hours,notes
    2026-09-07,19:00,21:15,2.25,inception,project-manager,scaffold repo,1.50,0.00,

Only three of those columns matter here: date, hours, and phase. Course weeks
are counted from the Monday of the week that holds your earliest logged date,
so you never number weeks by hand. Pass --start to pin Week 1 to a specific
Monday, and if your log happens to carry a week column, that column wins.

Usage:
    python3 pace-audit.py docs/hours-log.csv
    python3 pace-audit.py --demo
    python3 pace-audit.py docs/hours-log.csv --through 8
    python3 pace-audit.py docs/hours-log.csv --through 8 --start 2026-09-07
"""
import argparse
import csv
import io
import sys
from collections import defaultdict
from datetime import date, timedelta

WEEKS = 16
PER_WEEK = 15.0
TOTAL = WEEKS * PER_WEEK

DEMO = """date,start,end,hours,phase,hat,task,estimate_hours,blocked_hours,notes
2026-09-07,19:00,21:15,2.25,inception,project-manager,create repo + scaffold docs/ tree,1.50,0.00,underestimated .gitignore research
2026-09-09,17:30,20:30,3.00,inception,project-manager,draft charter: purpose + constraints,2.00,0.50,blocked 30m on institution GitHub SSO
2026-09-12,13:00,16:15,3.25,inception,project-manager,charter non-goals + risks; rewrote purpose,2.00,0.00,rework: first purpose statement was unverifiable
2026-09-15,18:00,21:00,3.00,inception,product-owner,idea screen: twelve problems down to three,2.00,0.00,
2026-09-17,19:00,21:30,2.50,inception,product-owner,feasibility screen on three candidates,2.00,0.00,
2026-09-19,14:00,17:30,3.50,inception,product-owner,scoping decision memo; killed two on purpose,3.00,0.00,
2026-09-22,18:00,22:00,4.00,requirements,business-analyst,personas + user stories for three roles,3.00,0.00,
2026-09-24,17:00,21:30,4.50,requirements,business-analyst,FR-01 through FR-14 with acceptance criteria,4.00,0.00,
2026-09-26,13:00,17:30,4.50,requirements,business-analyst,rewrote eight vague requirements after self-review,2.00,0.00,rework: "user friendly" is not testable
2026-09-29,18:30,22:00,3.50,requirements,business-analyst,NFR-01 to NFR-09 with metric + threshold + method,3.00,0.00,
2026-10-01,19:00,22:00,3.00,requirements,business-analyst,constraints + definition of done,2.50,0.00,
2026-10-03,10:00,14:30,4.50,requirements,business-analyst,MoSCoW pass + explicit out-of-scope list,3.00,1.00,blocked an hour waiting on the stakeholder
2026-10-06,18:00,21:30,3.50,design,architect,stack evaluation matrix: three options scored,3.00,0.00,
2026-10-08,19:00,22:00,3.00,design,architect,ADR-0001 database choice,2.00,0.00,
2026-10-10,12:00,15:30,3.50,design,architect,ADR-0002 auth + spike to prove the SDK works,2.00,1.25,blocked: SDK docs are v2 and pip installs v3
2026-10-13,19:30,22:00,2.50,design,architect,component diagram + interface list,2.50,0.00,
2026-10-15,19:00,21:30,2.50,design,architect,data model + technical specification draft,3.00,0.00,
2026-10-17,14:00,16:30,2.50,design,architect,traceability: every FR mapped to a component,1.50,0.00,found two requirements with nowhere to live
2026-10-20,20:00,22:30,2.50,planning,project-manager,WBS down to work packages under 8 hours,3.00,0.00,
2026-10-22,19:00,21:00,2.00,planning,project-manager,schedule for weeks 9-16 against the hours left,2.00,0.00,
2026-10-24,15:00,16:30,1.50,planning,project-manager,risk register: eight risks with triggers,2.00,0.00,short week: OS midterm
2026-10-27,19:00,21:00,2.00,review,project-manager,design review prep: assembled the packet,2.00,0.00,
2026-10-29,19:30,21:30,2.00,review,project-manager,walkthrough of the spec + defect log entries,2.00,0.00,
"""


def normalize(raw):
    """Lower-case the headers and strip the cells, so a log edited in a
    spreadsheet still reads. Any unnamed overflow column is dropped."""
    return {(key or "").strip().lower(): (value or "").strip()
            for key, value in raw.items() if key}


def load(handle):
    """Return [(day, week, hours, phase)] from a Week 1 hours log.

    A row needs hours, and a date (or a week column, if yours has one).
    The split is by phase; category, then hat, stand in when phase is blank,
    and a row carrying none of them lands in "unlabeled" -- which is
    itself a finding worth reading.
    """
    rows = []
    for raw in csv.DictReader(handle):
        row = normalize(raw)
        try:
            hours = float(row["hours"])
        except (KeyError, ValueError):
            print("skipping row with no usable hours: %r" % raw, file=sys.stderr)
            continue
        day = None
        if row.get("date"):
            try:
                day = date.fromisoformat(row["date"])
            except ValueError:
                print("skipping row with an unreadable date (want YYYY-MM-DD): %r"
                      % raw, file=sys.stderr)
                continue
        week = None
        if row.get("week"):
            try:
                week = int(float(row["week"]))
            except ValueError:
                week = None
        if day is None and week is None:
            print("skipping row with no date and no week: %r" % raw, file=sys.stderr)
            continue
        phase = row.get("phase") or row.get("category") or row.get("hat") or "unlabeled"
        rows.append((day, week, hours, phase))
    return rows


def week_one_monday(rows, start):
    """Monday of Week 1: the one you passed in, or the Monday of the week
    holding your earliest logged session."""
    if start is not None:
        anchor = start
    else:
        days = [day for day, _, _, _ in rows if day is not None]
        if not days:
            return None
        anchor = min(days)
    return anchor - timedelta(days=anchor.weekday())


def tally(rows, monday, through):
    """Fold the rows into hours-per-week and hours-per-phase for weeks 1..through."""
    by_week = defaultdict(float)
    by_phase = defaultdict(float)
    outside = 0.0
    for day, week, hours, phase in rows:
        if week is None:
            if monday is None or day is None:
                continue
            week = (day - monday).days // 7 + 1
        if week < 1 or week > through:
            outside += hours
            continue
        by_week[week] += hours
        by_phase[phase] += hours
    return by_week, by_phase, outside


def report(by_week, by_phase, through, monday=None, outside=0.0):
    if monday is not None:
        print("Week 1 starts Monday %s. Wrong? Pass --start YYYY-MM-DD.\n"
              % monday.isoformat())
    print("WEEKLY PACE (budget %.0f h/week)\n" % PER_WEEK)
    print("%-6s %8s %10s %10s %10s" % ("week", "logged", "cumul.", "budget", "variance"))
    running = 0.0
    silent = []
    for week in range(1, through + 1):
        logged = by_week.get(week, 0.0)
        running += logged
        budget = PER_WEEK * week
        if logged == 0.0:
            silent.append(week)
        print("%-6d %8.1f %10.1f %10.1f %+10.1f" % (week, logged, running, budget, running - budget))

    budget = PER_WEEK * through
    variance = running - budget
    avg = running / through if through else 0.0
    print("\nPHASE SPLIT")
    for name, hours in sorted(by_phase.items(), key=lambda kv: -kv[1]):
        share = (100.0 * hours / running) if running else 0.0
        print("  %-16s %7.1f h  %5.1f%%" % (name, hours, share))

    print("\nVERDICT")
    print("  logged through week %d : %.1f h" % (through, running))
    print("  budgeted              : %.1f h  (variance %+.1f h)" % (budget, variance))
    print("  average per week      : %.1f h" % avg)
    remaining_weeks = WEEKS - through
    print("  at this average you finish the course with %.0f h of the %.0f-hour budget"
          % (running + avg * remaining_weeks, TOTAL))
    if outside:
        print("  %.1f h fall outside weeks 1-%d and are not counted above" % (outside, through))
    if silent:
        print("  SILENT WEEKS (nothing logged): %s" % ", ".join(str(w) for w in silent))
    if variance < -PER_WEEK:
        print("  BEHIND by more than a full week. Cut scope now, while nothing is built.")
    elif variance > PER_WEEK:
        print("  AHEAD. Bank it as buffer; do not spend it by adding requirements.")
    else:
        print("  On pace. Keep the log honest and re-run this in Week 12.")
    print("\n  A number is not a plan. Write the paragraph that says what you will change.")


def main():
    parser = argparse.ArgumentParser(description="Audit capstone hours against the 240-hour budget.")
    parser.add_argument("logfile", nargs="?", help="path to the hours log CSV")
    parser.add_argument("--demo", action="store_true", help="run against built-in sample data")
    parser.add_argument("--through", type=int, default=8, help="audit through this week (default 8)")
    parser.add_argument("--start", help="date of Week 1 (YYYY-MM-DD); default: your earliest entry")
    args = parser.parse_args()

    start = None
    if args.start:
        try:
            start = date.fromisoformat(args.start)
        except ValueError:
            sys.exit("--start wants a date like 2026-09-07")

    if args.demo:
        handle = io.StringIO(DEMO)
    elif args.logfile:
        try:
            handle = open(args.logfile, newline="", encoding="utf-8-sig")
        except OSError as err:
            sys.exit("cannot open %s: %s" % (args.logfile, err))
    else:
        sys.exit("give a log file path, or pass --demo")

    with handle:
        rows = load(handle)
    if not rows:
        sys.exit("no readable rows. Check the header line: it should be the one you "
                 "created in Week 1, starting date,start,end,hours,phase,...")

    through = max(1, min(args.through, WEEKS))
    monday = week_one_monday(rows, start)
    by_week, by_phase, outside = tally(rows, monday, through)
    report(by_week, by_phase, through, monday, outside)


if __name__ == "__main__":
    main()
