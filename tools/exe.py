"""exe.py - find a program by its full path before running it.

On Windows a program started by its bare name (`git`, `powershell`, `ffmpeg`) can be resolved from the CURRENT
DIRECTORY before the system folders, so a hostile `git.exe` sitting in a folder you happen to run a tool from would be
run instead of the real one. `shutil.which` has the same habit on Python 3.11 (it always looks in the current directory
first on Windows), so it is not a fix. `path_of` looks only in absolute PATH entries, skips any entry that is the current
directory, and returns an absolute path, which is then what the tool passes to `subprocess`.

    from exe import path_of
    subprocess.run([path_of("git"), "status"])
"""
import os
import sys


class ProgramNotFound(RuntimeError):
    """The named program is on no trusted PATH entry."""


def _extensions(name):
    if sys.platform != "win32" or os.path.splitext(name)[1]:
        return [""]
    return [""] + [e for e in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").lower().split(";") if e]


def path_of(name):
    here = os.path.normcase(os.path.realpath(os.getcwd()))
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if not entry or not os.path.isabs(entry):
            continue  # an empty or relative entry means "the current directory"
        if os.path.normcase(os.path.realpath(entry)) == here:
            continue
        for extension in _extensions(name):
            candidate = os.path.join(entry, name + extension)
            if os.path.isfile(candidate) and (sys.platform == "win32" or os.access(candidate, os.X_OK)):
                return os.path.abspath(candidate)
    raise ProgramNotFound(f"{name!r} was not found in any absolute PATH entry (the current directory is never searched)")


def find(name):
    """Like path_of, but None when the program is not found (for "is it installed?" checks)."""
    try:
        return path_of(name)
    except ProgramNotFound:
        return None
