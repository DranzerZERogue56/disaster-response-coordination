"""tools/exe.py: find a program by its full path, never from the current directory (Windows search-path hijacking)."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import exe

NAME = "hijackme"
SUFFIX = ".exe" if sys.platform == "win32" else ""


def make_program(folder, name=NAME):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (name + SUFFIX)
    path.write_text("x", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_it_finds_a_program_in_an_absolute_path_entry_and_returns_an_absolute_path(tmp_path, monkeypatch):
    real = make_program(tmp_path / "bin")
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))
    monkeypatch.setenv("PATHEXT", ".EXE;.CMD")
    found = exe.path_of(NAME)
    assert os.path.isabs(found) and Path(found).samefile(real)


def test_a_program_that_sits_only_in_the_current_directory_is_not_found(tmp_path, monkeypatch):
    make_program(tmp_path / "work")
    monkeypatch.chdir(tmp_path / "work")
    monkeypatch.setenv("PATH", str(tmp_path / "elsewhere"))
    monkeypatch.setenv("PATHEXT", ".EXE;.CMD")
    with pytest.raises(exe.ProgramNotFound):
        exe.path_of(NAME)


def test_a_dot_or_relative_or_empty_path_entry_never_resolves_to_the_current_directory(tmp_path, monkeypatch):
    make_program(tmp_path / "work")
    monkeypatch.chdir(tmp_path / "work")
    monkeypatch.setenv("PATH", os.pathsep.join([".", "", "work", "sub/dir"]))
    monkeypatch.setenv("PATHEXT", ".EXE;.CMD")
    with pytest.raises(exe.ProgramNotFound):
        exe.path_of(NAME)


def test_even_an_absolute_entry_that_is_the_current_directory_is_skipped_and_a_later_real_one_wins(tmp_path, monkeypatch):
    make_program(tmp_path / "work")  # the hostile copy, in the current directory
    real = make_program(tmp_path / "bin")
    monkeypatch.chdir(tmp_path / "work")
    monkeypatch.setenv("PATH", os.pathsep.join([str(tmp_path / "work"), str(tmp_path / "bin")]))
    monkeypatch.setenv("PATHEXT", ".EXE;.CMD")
    assert Path(exe.path_of(NAME)).samefile(real)


def test_a_program_that_does_not_exist_raises_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(exe.ProgramNotFound, match="nothing-like-this"):
        exe.path_of("nothing-like-this")


def test_the_python_running_this_test_can_be_found_by_name():
    assert os.path.isabs(exe.path_of(Path(sys.executable).stem))
