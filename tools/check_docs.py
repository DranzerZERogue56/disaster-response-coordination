#!/usr/bin/env python3
"""check_docs.py - mechanical checks on the documentation set, run in CI (Milestone 13, Medium extras).

    python tools/check_docs.py          exit 1 and print every problem if anything below fails

Correctness (does the documentation point at things that exist?):
  * README.md has the eleven numbered sections;
  * every `./script/...` command written in README.md, the runbook and the onboarding guide is an executable file;
  * every repository path written in backticks in those documents exists (URLs, placeholders and globs are skipped);
  * every relative Markdown link in the documentation set resolves;
  * the ADR index lists every ADR file.
Accessibility (can a screen reader and a keyboard reader use it?):
  * exactly one level-1 heading, and heading levels never skip a level;
  * no link text such as "here" or "click here"; images have alt text;
  * every diagram in a mermaid block is followed by a text version of it.
It checks form, not truth: it cannot tell you that an expected output is still what the program prints.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ["README.md", "docs/runbook.md", "docs/onboarding.md", "docs/adr/README.md", "docs/clean-machine-test.md", "docs/ci-pipeline.md", "docs/architecture.md", "docs/accessibility-pass.md"]
PATH_TOKEN = re.compile(r"`([A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)+/?)`")
SCRIPT_TOKEN = re.compile(r"\./script/([a-z0-9-]+)")
LINK = re.compile(r"(?<!\!)\[([^\]]*)\]\(([^)\s]+)\)")
IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
BAD_LINK_TEXT = {"here", "click here", "link", "this link", "more", "read more"}
GENERATED = ("data/", ".venv/", "docs/evidence/", "tests/manual/evidence/")  # created by running things, not committed


def strip_fences(text):
    return re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)


def headings(text):
    out, fenced = [], False
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#{1,6} ", line):
            out.append((number, len(line) - len(line.lstrip("#")), line.lstrip("#").strip()))
    return out


def check_accessibility(name, text):
    problems = []
    found = headings(text)
    if sum(1 for _, level, _ in found if level == 1) != 1:
        problems.append(f"{name}: needs exactly one level-1 heading")
    previous = 0
    for number, level, title in found:
        if previous and level > previous + 1:
            problems.append(f"{name}:{number}: heading '{title}' jumps from level {previous} to {level}")
        previous = level
    prose = strip_fences(text)
    for label, _ in LINK.findall(prose):
        if label.strip().lower() in BAD_LINK_TEXT:
            problems.append(f"{name}: link text '{label}' says nothing out of context")
    for alt, target in IMAGE.findall(prose):
        if not alt.strip():
            problems.append(f"{name}: image {target} has no alt text")
    for match in re.finditer(r"```mermaid\n.*?```\n(.*)", text, flags=re.S):
        following = match.group(1).lstrip("\n")[:400].lower()
        if "text version" not in following:
            problems.append(f"{name}: a mermaid diagram is not followed by a 'Text version' paragraph")
    return problems


def check_paths(name, text, root):
    problems = []
    prose = strip_fences(text)
    for token in set(PATH_TOKEN.findall(prose)):
        if token.startswith(GENERATED) or "*" in token or "..." in token or token.startswith(("http", "docs/img/")):  # "..." is a placeholder (Windows even resolves it as a path)
            continue
        if not (root / token).exists():
            problems.append(f"{name}: `{token}` does not exist in the repository")
    for command in set(SCRIPT_TOKEN.findall(text)):
        path = root / "script" / command
        if not path.is_file():
            problems.append(f"{name}: ./script/{command} does not exist")
    for _, target in LINK.findall(prose):
        if target.startswith(("http", "#", "mailto:")):
            continue
        base = (root / name).parent
        if not (base / target.split("#")[0]).exists():
            problems.append(f"{name}: link target {target} does not exist")
    return problems


def check_readme_sections(text):
    numbers = [int(m.group(1)) for m in re.finditer(r"^## (\d+)\. ", text, re.M)]
    return [] if numbers == list(range(1, 12)) else [f"README.md: needs sections 1 to 11 in order, found {numbers}"]


def check_adr_index(root):
    index = (root / "docs" / "adr" / "README.md").read_text(encoding="utf-8")
    return [f"docs/adr/README.md: {f.name} is not listed" for f in sorted((root / "docs" / "adr").glob("0*.md")) if f.name not in index]


def check_all(root=ROOT):
    problems = []
    for name in CORE:
        path = root / name
        if not path.is_file():
            problems.append(f"{name}: missing")
            continue
        text = path.read_text(encoding="utf-8")
        problems += check_accessibility(name, text)
        if name in ("README.md", "docs/runbook.md", "docs/onboarding.md", "docs/adr/README.md"):
            problems += check_paths(name, text, root)
    if (root / "README.md").is_file():
        problems += check_readme_sections((root / "README.md").read_text(encoding="utf-8"))
    if (root / "docs" / "adr" / "README.md").is_file():
        problems += check_adr_index(root)
    return problems


if __name__ == "__main__":
    found = check_all()
    for problem in found:
        print(problem)
    print(f"check_docs: {len(found)} problem(s) in {len(CORE)} documents")
    sys.exit(1 if found else 0)
