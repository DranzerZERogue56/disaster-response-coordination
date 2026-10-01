#!/usr/bin/env python3
"""migrate.py - apply numbered SQL migrations to the project's SQLite database.

    python3 tools/migrate.py <db-path>

Reads every migrations/NNNN-*.sql file, applies any whose number isn't
already recorded in schema_migrations, in order, each inside one
transaction. Forward-only: there is no "down" migration. See
docs/architecture.md §6 "Migrations" for why this project uses a plain
runner instead of a migration library.
"""
import re
import sqlite3
import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
FILENAME_RE = re.compile(r"^(\d{4})-.*\.sql$")


def find_migrations():
    found = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        m = FILENAME_RE.match(path.name)
        if not m:
            sys.exit("migrate.py: %s doesn't match NNNN-name.sql" % path.name)
        found.append((int(m.group(1)), path))
    return found


def applied_versions(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    return {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: migrate.py <db-path>")
    db_path = sys.argv[1]

    migrations = find_migrations()
    if not migrations:
        sys.exit("migrate.py: no migrations found in %s" % MIGRATIONS_DIR)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    already = applied_versions(conn)

    applied_count = 0
    for version, path in migrations:
        if version in already:
            print("  skip  %04d  %s (already applied)" % (version, path.name))
            continue
        sql = path.read_text(encoding="utf-8")
        print("  apply %04d  %s" % (version, path.name))
        with conn:
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, datetime('now'))",
                (version,),
            )
        applied_count += 1

    print("migrate.py: %d migration(s) applied, database at %s" % (applied_count, db_path))


if __name__ == "__main__":
    main()
