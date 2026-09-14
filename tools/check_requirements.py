#!/usr/bin/env python3
"""A blunt first-pass linter for a requirements document.

Usage:  python3 check_requirements.py [path]        (default: docs/requirements.md)

It reads a Markdown requirements file written in the house shape:

    ### FR-<AREA>-<nn> — <name>       (or the flat form: ### FR-<nnn> — <name>)
    **Priority:** Must | Should | Could | Won't
    **Requirement:** <Actor> shall ...
    **Rationale:** ...
    **Acceptance criteria:**
    - Given ..., when ..., then ...

It cannot tell you whether a requirement is *right*. It can tell you that one is
unmeasurable, compound, solution-biased, unprioritised, or untestable. Every
finding is a prompt to think, not a verdict. Exit code 1 if any ERROR is found.
"""
import re
import sys
from collections import Counter

WEASEL = ["user-friendly", "user friendly", "easy to use", "intuitive", "seamless",
          "robust", "efficient", "efficiently", "fast", "quickly", "quick",
          "as appropriate", "appropriate", "adequate", "as needed", "if possible",
          "state-of-the-art", "modern", "simple", "flexible", "scalable",
          "several", "various", "etc.", "tbd", "to be determined"]

# These five are vague only as VERBS. "The system shall support export" hides a
# feature; "the browser process is terminated" and "a supported format" are exact.
# Matching them as bare words fired on nouns and adjectives and cost more trust
# than it bought, so they are matched as the requirement's verb instead.
VAGUE_VERB = re.compile(
    r"\bshall\s+(?:be\s+able\s+to\s+)?(support|handle|manage|process|deal\s+with)\b", re.I)
BIASED = ["button", "dropdown", "drop-down", "checkbox", "radio button", "modal",
          "database table", "api endpoint", "microservice", "docker", "kubernetes",
          "react", "angular", "vue", "postgres", "postgresql", "mysql", "mongodb",
          "sqlite", "redis", "rest api", "graphql", "javascript", "typescript"]
COMPOUND = [" and/or ", " as well as ", " and also ", "; and ", ", and shall "]
PRIORITIES = {"must", "should", "could", "won't", "wont", "will not"}
# Two identifier styles are legal in this course, and the linter accepts both:
#   area-scoped  FR-INV-04   (recommended — the area tells you where it lives)
#   flat         FR-014      (used by most of the book's worked examples)
# Pick one in Week 3 and stay consistent; mixing them is what breaks traceability,
# not the style itself. The linter reports a mix as an error below.
ID_RE = re.compile(r"^###\s+(FR-(?:[A-Z][A-Z0-9]*-)?\d{2,3})\b")


def id_style(rid):
    """'area' for FR-INV-04, 'flat' for FR-014."""
    return "flat" if re.fullmatch(r"FR-\d{2,3}", rid) else "area"
FIELD_RE = re.compile(r"^\*\*(Priority|Requirement|Rationale|Source|Acceptance criteria)"
                      r":?\*\*:?\s*(.*)$", re.I)


def parse(lines):
    """Split the document into requirement blocks keyed by identifier."""
    blocks, current = [], None
    for raw in lines:
        line = raw.rstrip("\n")
        m = ID_RE.match(line)
        if m:
            current = {"id": m.group(1), "fields": {}, "criteria": [], "last": None}
            blocks.append(current)
            continue
        if current is None:
            continue
        if line.startswith("### ") or line.startswith("## "):
            current = None
            continue
        f = FIELD_RE.match(line)
        if f:
            key = f.group(1).lower()
            current["fields"][key] = f.group(2).strip()
            current["last"] = key
            continue
        if line.startswith("- ") and current["last"] == "acceptance criteria":
            current["criteria"].append(line[2:].strip())
    return blocks


def hits(text, needles):
    low = text.lower()
    return sorted({n for n in needles if re.search(r"(?<![\w-])" + re.escape(n), low)})


def check(block, errors, warnings):
    rid, f = block["id"], block["fields"]
    req, prio = f.get("requirement", ""), f.get("priority", "").lower()
    body = " ".join([req] + block["criteria"])
    if not req:
        errors.append(f"{rid}: no **Requirement:** sentence.")
    elif " shall " not in f" {req.lower()} ":
        warnings.append(f"{rid}: requirement sentence does not say 'shall'.")
    if not prio:
        errors.append(f"{rid}: no **Priority:** — every requirement gets a MoSCoW value.")
    elif not any(p in prio for p in PRIORITIES):
        errors.append(f"{rid}: priority '{f['priority']}' is not Must/Should/Could/Won't.")
    if ("must" in prio or "should" in prio) and not block["criteria"]:
        errors.append(f"{rid}: {f['priority']} requirement with no acceptance criteria.")
    for c in block["criteria"]:
        if not re.search(r"\bgiven\b.*\bwhen\b.*\bthen\b", c, re.I):
            warnings.append(f"{rid}: criterion is not in Given/When/Then form: '{c[:60]}...'")
    for w in hits(body, WEASEL):
        errors.append(f"{rid}: unmeasurable or vague word '{w}'.")
    for vm in VAGUE_VERB.finditer(req):
        errors.append(f"{rid}: 'shall {vm.group(1).lower()}' hides the behavior — say what it does.")
    for b in hits(req, BIASED):
        warnings.append(f"{rid}: names an implementation ('{b}') — that belongs in the design.")
    for c in hits(req, COMPOUND):
        errors.append(f"{rid}: looks compound ('{c.strip()}') — split it.")
    if req.lower().count(" and ") >= 3:
        warnings.append(f"{rid}: three or more 'and's — probably more than one requirement.")
    if not f.get("rationale"):
        warnings.append(f"{rid}: no **Rationale:** — say which persona asked for this.")
    if not f.get("source"):
        warnings.append(f"{rid}: no **Source:** — say where this came from.")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/requirements.md"
    try:
        with open(path, encoding="utf-8") as fh:
            blocks = parse(fh.readlines())
    except OSError as exc:
        print(f"cannot read {path}: {exc}")
        return 2
    errors, warnings = [], []
    dupes = [i for i, n in Counter(b["id"] for b in blocks).items() if n > 1]
    for d in dupes:
        errors.append(f"{d}: identifier used more than once. Identifiers are never reused.")
    styles = {id_style(b["id"]) for b in blocks}
    if len(styles) > 1:
        errors.append("mixed identifier styles (FR-INV-04 and FR-014 both present) — "
                      "pick one and use it for every requirement.")
    for b in blocks:
        check(b, errors, warnings)
    print(f"{path}: {len(blocks)} requirement(s) parsed.")
    for e in errors:
        print(f"  ERROR   {e}")
    for w in warnings:
        print(f"  warning {w}")
    if not blocks:
        print("  ERROR   no '### FR-<AREA>-<nn>' (or '### FR-<nnn>') headings found "
              "— check the file shape.")
        return 1
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
