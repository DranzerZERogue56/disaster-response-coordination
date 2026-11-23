"""tools/check_docs.py: the documentation set is checked for form on every run (Milestone 13, Medium extras)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import check_docs


def test_the_real_documentation_set_has_no_problems():
    assert check_docs.check_all() == []


def test_a_skipped_heading_level_is_reported():
    problems = check_docs.check_accessibility("x.md", "# Title\n\n### Jumped\n")
    assert any("jumps from level 1 to 3" in p for p in problems)


def test_two_level_one_headings_are_reported():
    assert check_docs.check_accessibility("x.md", "# A\n\n# B\n")


def test_link_text_that_says_nothing_and_missing_alt_text_are_reported():
    problems = check_docs.check_accessibility("x.md", "# T\n\nSee [here](a.md) and ![](pic.png)\n")
    assert any("'here'" in p for p in problems) and any("no alt text" in p for p in problems)


def test_a_diagram_without_a_text_version_is_reported_and_one_with_it_is_not():
    bare = "# T\n\n```mermaid\nflowchart LR\n A-->B\n```\n\nNothing else.\n"
    described = bare.replace("Nothing else.", "**Text version of the diagram:** A leads to B.")
    assert check_docs.check_accessibility("x.md", bare)
    assert check_docs.check_accessibility("x.md", described) == []


def test_a_path_or_script_that_does_not_exist_is_reported(tmp_path):
    (tmp_path / "script").mkdir()
    text = "# T\n\nSee `docs/nothing.md` and run ./script/ghost.\n"
    problems = check_docs.check_paths("README.md", text, tmp_path)
    assert any("docs/nothing.md" in p for p in problems) and any("./script/ghost" in p for p in problems)


def test_the_readme_must_have_eleven_numbered_sections():
    assert check_docs.check_readme_sections("## 1. A\n## 2. B\n") != []
    assert check_docs.check_readme_sections("".join(f"## {n}. S\n" for n in range(1, 12))) == []


def test_a_placeholder_with_three_dots_is_not_treated_as_a_path(tmp_path):
    text = "# T\n\nRun the `./script/...` commands.\n"
    assert check_docs.check_paths("README.md", text, tmp_path) == []
