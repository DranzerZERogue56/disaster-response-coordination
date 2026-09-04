#!/usr/bin/env python3
"""Offline twin of the 240-Hour Scope Sizer (Chapter 2).

Standard library only. Reads candidate-scorecard.csv (same directory by default)
and prints an hour range, a verdict, and the two cuts that move the number most.

    python3 size_check.py
    python3 size_check.py my-candidates.csv

The model is a heuristic, not an oracle. Estimate by hand too, then reconcile.
"""
import csv
import os
import sys

PLAN, CEILING, FLOOR = 60.0, 75.0, 30.0          # construction-hour budget
DATA = {"simple": 1.0, "moderate": 1.1, "complex": 1.25}
COST = {"feature": 6.0, "integration": 10.0, "auth": 12.0,
        "persistence": 6.0, "deploy": 8.0}


def truthy(value):
    return str(value).strip().lower() in ("yes", "y", "true", "1")


def estimate(row):
    """Return (point, low, high, multiplier) for one candidate row."""
    base = (COST["feature"] * int(row["features"])
            + COST["integration"] * int(row["integrations"])
            + (COST["auth"] if truthy(row["auth"]) else 0.0)
            + (COST["persistence"] if truthy(row["persistence"]) else 0.0)
            + (COST["deploy"] if truthy(row["deploy"]) else 0.0))
    mult = (DATA.get(row["data"].strip().lower(), 1.1)
            * (1.0 + 0.15 * int(row["new_tech"])))
    point = base * mult
    return point, point * 0.8, point * 1.5, mult


def verdict(point):
    if point < FLOOR:
        return "TOO SMALL TO DEFEND"
    if point > CEILING:
        return "YOU WILL NOT FINISH THIS"
    if point > PLAN:
        return "RIGHT-SIZED (no slack)"
    return "RIGHT-SIZED"


def cuts(row, point, mult):
    """The levers, largest saving first."""
    options = []
    if int(row["integrations"]) > 0:
        options.append(("drop one external integration",
                        COST["integration"] * mult))
    if truthy(row["auth"]):
        options.append(("replace accounts with a shared join code",
                        COST["auth"] * mult))
    if int(row["new_tech"]) > 0:
        options.append(("swap one new technology for one you know",
                        point - point / (1.0 + 0.15) if mult else 0.0))
    if int(row["features"]) > 3:
        options.append(("cut two features", 2 * COST["feature"] * mult))
    options.sort(key=lambda pair: pair[1], reverse=True)
    return options[:2]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        here, "candidate-scorecard.csv")
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            point, low, high, mult = estimate(row)
            print("\n%s" % row["candidate"])
            print("  estimate : %.0f h   (range %.0f-%.0f h)" % (point, low, high))
            print("  budget   : plan %.0f h, ceiling %.0f h" % (PLAN, CEILING))
            print("  verdict  : %s" % verdict(point))
            for label, saved in cuts(row, point, mult):
                print("  cut      : %-45s saves ~%.0f h" % (label, saved))
    print("\nHeuristic only. Estimate by hand as well; if the two disagree by more")
    print("than a factor of two, find out which is wrong before Week 5.")


if __name__ == "__main__":
    main()
