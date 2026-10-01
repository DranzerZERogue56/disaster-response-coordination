#!/usr/bin/env python3
"""spec-check.py - a lint pass for a technical specification.

    python3 spec-check.py docs/architecture.md [--requirements docs/requirements.md]

Checks four things a human reviewer should never have to check by hand:
  1. every load-bearing section exists,
  2. no vague words that mean "I have not decided",
  3. no unresolved markers left in the document,
  4. every requirement identifier is traced (needs --requirements).

Identifiers are read in either style Chapter 3 allows - area-scoped
(FR-INV-01, NFR-PERF-02) or flat (FR-014, NFR-01) - and the traceability
line reports how many it found, so a file it cannot parse is never mistaken
for a file with nothing wrong in it.

Exits 0 when clean, 1 when it finds something, so it drops into CI in Week 9.
It cannot tell you whether your design is good. It can tell you whether your
document decided anything.
"""
import argparse
import re
import sys

REQUIRED = ["purpose", "context", "container", "component", "interface",
            "data model", "sequence", "error", "traceability", "open question"]

VAGUE = ["user-friendly", "user friendly", "appropriately", "as appropriate",
         "as needed", "as necessary", "fast", "quickly", "robust", "scalable",
         "efficient", "seamless", "intuitive", "handle errors", "and so on",
         "etc.", "somehow", "various", "flexible"]

MARKERS = ["TBD", "TODO", "FIXME", "XXX", "???", "<insert"]

# Both identifier styles from Chapter 3:
#   area-scoped  FR-INV-01, NFR-PERF-02   (recommended there)
#   flat         FR-014, NFR-01           (used by several worked examples)
ID_RE = re.compile(r"\b((?:FR|NFR)-(?:[A-Z][A-Z0-9]*-)?\d{2,3})\b")


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        sys.exit("cannot read %s: %s" % (path, exc))


def missing_sections(text):
    heads = " || ".join(line.lstrip("#").strip().lower()
                        for line in text.splitlines() if line.startswith("#"))
    return [name for name in REQUIRED if name not in heads]


def term_hits(text, terms, ignore_case=True):
    hits = []
    for number, line in enumerate(text.splitlines(), 1):
        hay = line.lower() if ignore_case else line
        for term in terms:
            needle = term.lower() if ignore_case else term
            pattern = r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(needle)
            if re.search(pattern, hay):
                hits.append((number, term, line.strip()[:64]))
    return hits


def identifiers(text):
    """Every requirement identifier in the text, deduplicated and ordered."""
    def key(identifier):
        parts = identifier.split("-")
        # FR-INV-01 -> ("FR", "INV", 1); FR-014 -> ("FR", "", 14)
        return (parts[0], "-".join(parts[1:-1]), int(parts[-1]))
    return sorted(set(ID_RE.findall(text)), key=key)


def untraced(spec_text, req_text):
    present = set(identifiers(spec_text))
    return [i for i in identifiers(req_text) if i not in present]


def report(title, rows):
    if not rows:
        print("  OK   %s" % title)
        return 0
    print("  FAIL %s (%d)" % (title, len(rows)))
    for row in rows:
        print("       %s" % row)
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description="Lint a technical specification.")
    ap.add_argument("spec", help="path to the specification")
    ap.add_argument("--requirements", help="path to the requirements document")
    args = ap.parse_args()

    spec = read(args.spec)
    print("spec-check: %s" % args.spec)
    found = 0
    found += report("required sections present",
                    ["missing section: %s" % s for s in missing_sections(spec)])
    found += report("no vague words",
                    ["line %d: '%s' -> %s" % h for h in term_hits(spec, VAGUE)])
    found += report("no unresolved markers",
                    ["line %d: '%s' -> %s" % h
                     for h in term_hits(spec, MARKERS, ignore_case=False)])
    if args.requirements:
        req = read(args.requirements)
        wanted = identifiers(req)
        if not wanted:
            found += report(
                "every requirement traced",
                ["no requirement identifiers found in %s" % args.requirements,
                 "expected FR-INV-01 / NFR-PERF-02 or FR-014 / NFR-01 style",
                 "this check verified nothing - fix the identifiers first"])
        else:
            found += report("every requirement traced, %d read" % len(wanted),
                            ["never mentioned in the spec: %s" % g
                             for g in untraced(spec, req)])
    else:
        print("  SKIP traceability (pass --requirements to enable)")

    print("spec-check: %d finding(s)" % found)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
