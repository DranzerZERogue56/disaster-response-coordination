"""Two architecture rules, enforced by the build (docs/superpowers/plans/2026-11-18-database-options.md).

1. The unit registry's service no longer touches the `units` table: that is the repository's job (the pilot data-access layer).
2. No SQL anywhere in `src/` is built from variables (f-strings, concatenation, % or .format), except the one reviewed line in
   the purge job. Values always travel as bound parameters, which is what stops SQL injection.
"""
import ast
import re
from pathlib import Path

SRC = Path("src")
SQL_METHODS = {"execute", "executemany", "executescript"}
# (file, enclosing function): reviewed. The purge job's table name and condition come from constants in the same function.
REVIEWED = {("src/purge/job.py", "purge")}


def _builds_text_from_variables(node):
    if isinstance(node, ast.JoinedStr):
        return any(isinstance(v, ast.FormattedValue) for v in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        return any(isinstance(side, (ast.Constant, ast.JoinedStr)) and not isinstance(getattr(side, "value", ""), (int, float)) for side in (node.left, node.right))
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format" and isinstance(node.func.value, ast.Constant)


def sql_built_from_variables():
    found = set()
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for function in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))] + [tree]:
            name = getattr(function, "name", "<module>")
            for node in ast.walk(function):
                is_sql_call = isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in SQL_METHODS and node.args
                if is_sql_call and _builds_text_from_variables(node.args[0]):
                    found.add((path.as_posix(), name))
    # a call inside a nested function is also seen from its parent; keep the innermost name only
    return {item for item in found if not any(other[0] == item[0] and other != item and item[1] == "<module>" for other in found)}


def test_no_sql_in_src_is_built_from_variables_except_the_reviewed_purge_line():
    assert sql_built_from_variables() <= REVIEWED, f"SQL built from variables outside the reviewed list: {sql_built_from_variables() - REVIEWED}"


def test_the_reviewed_list_cannot_go_stale():
    assert REVIEWED <= sql_built_from_variables(), "a reviewed exception no longer exists: remove it from REVIEWED"


def test_the_scanner_really_catches_the_forms_of_unsafe_sql(tmp_path):
    for bad in ('conn.execute(f"SELECT * FROM t WHERE a = {x}")', 'conn.execute("SELECT " + x)', 'conn.execute("SELECT %s" % x)', 'conn.execute("SELECT {}".format(x))'):
        node = ast.parse(bad).body[0].value.args[0]
        assert _builds_text_from_variables(node), bad
    for good in ('conn.execute("SELECT * FROM t WHERE a = ?", (x,))', 'conn.execute("SELECT * FROM t " "WHERE a = ?", (x,))'):
        node = ast.parse(good).body[0].value.args[0]
        assert not _builds_text_from_variables(node), good


def test_the_unit_registry_service_has_no_sql_on_the_units_table():
    text = Path("src/unit_registry/service.py").read_text(encoding="utf-8")
    touches_units = re.findall(r"\b(?:FROM|UPDATE|INTO|JOIN)\s+units\b", text)
    assert touches_units == [], f"unit_registry/service.py still touches the units table directly: {touches_units}"


def test_no_security_or_validation_check_in_src_relies_on_assert():
    """`python -O` removes assert statements, so a check written as an assert would silently vanish. The running app
    (src/) must use none: validation raises real exceptions instead."""
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Assert):
                offenders.append(f"{path.as_posix()}:{node.lineno}")
    assert offenders == [], f"assert statements in the running app: {offenders}"

