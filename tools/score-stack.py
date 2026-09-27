#!/usr/bin/env python3
"""Rank technology options by weighted score, and refuse to let you cheat.

Reads the long-format matrix in tech-evaluation-matrix.csv. For each decision
it checks that the criterion weights sum to 1.00, that every option was scored
on every criterion, and that no score was entered without evidence. Then it
ranks the options.

    python3 score-stack.py tech-evaluation-matrix.csv
    python3 score-stack.py tech-evaluation-matrix.csv --decision data-store

Exit status is 1 if any check failed. A matrix that does not pass is a
preference wearing a table's clothes.
"""

import argparse
import csv
import sys
from collections import defaultdict

REQUIRED_COLUMNS = ["decision", "criterion", "weight", "option", "score", "evidence"]


def load_rows(path, only_decision=None):
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit("ERROR: %s is missing column(s): %s" % (path, ", ".join(missing)))
        rows = [r for r in reader
                if (r.get("decision") or "").strip()
                and not (r.get("decision") or "").lstrip().startswith("#")]
    if only_decision:
        rows = [r for r in rows if r["decision"].strip() == only_decision]
        if not rows:
            sys.exit("ERROR: no rows for decision %r" % only_decision)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv_path", help="path to the evaluation matrix")
    parser.add_argument("--decision", help="score only this decision")
    args = parser.parse_args()

    scores = defaultdict(lambda: defaultdict(dict))  # decision -> option -> criterion -> (w, s)
    weights = defaultdict(dict)                      # decision -> criterion -> weight
    problems = []

    for row in load_rows(args.csv_path, args.decision):
        decision = row["decision"].strip()
        criterion = row["criterion"].strip()
        option = row["option"].strip()
        try:
            weight = float(row["weight"])
            score = float(row["score"])
        except (TypeError, ValueError):
            problems.append("%s / %s / %s: weight and score must be numbers" % (decision, option, criterion))
            continue
        if not 0.0 <= score <= 5.0:
            problems.append("%s / %s / %s: score %g is outside 0-5" % (decision, option, criterion, score))
        seen = weights[decision].get(criterion)
        if seen is not None and abs(seen - weight) > 1e-9:
            problems.append("%s / %s: weight changes between options (%g vs %g)" % (decision, criterion, seen, weight))
        if not (row.get("evidence") or "").strip():
            problems.append("%s / %s / %s: no evidence - that is a preference, not a score"
                            % (decision, option, criterion))
        weights[decision][criterion] = weight
        scores[decision][option][criterion] = (weight, score)

    for decision in sorted(scores):
        total_weight = sum(weights[decision].values())
        print("\n=== %s ===   weights sum to %.2f" % (decision, total_weight))
        if abs(total_weight - 1.0) > 0.001:
            problems.append("%s: weights sum to %.2f, not 1.00" % (decision, total_weight))
        ranked = []
        for option, criteria in scores[decision].items():
            if set(criteria) != set(weights[decision]):
                problems.append("%s / %s: scored on %d criteria, expected %d"
                                % (decision, option, len(criteria), len(weights[decision])))
            ranked.append((sum(w * s for w, s in criteria.values()), option))
        ranked.sort(reverse=True)
        for total, option in ranked:
            print("  %5.2f  %s" % (total, option))
        if len(ranked) > 1 and ranked[0][0] - ranked[1][0] < 0.25:
            print("  note: top two are within 0.25 - this decision is a coin flip; "
                  "pick the one that is easier to reverse")

    if problems:
        print("\nPROBLEMS")
        for problem in sorted(set(problems)):
            print("  - %s" % problem)
        return 1
    print("\nOK - every decision is weighted, fully scored, and evidenced.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
