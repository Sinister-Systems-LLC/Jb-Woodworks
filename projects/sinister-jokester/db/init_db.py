"""Initialise (idempotent) the Sinister Jokester intake DB.

Author: RKOJ-ELENO :: 2026-05-26
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "db" / "schema.sql"
DEFAULT_DB_PATH = REPO_ROOT / "vault" / "db" / "intake.sqlite"


def init_db(db_path: Path = DEFAULT_DB_PATH, schema_path: Path = SCHEMA_PATH) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = schema_path.read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()
    return db_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Initialise Sinister Jokester intake DB.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="DB path")
    parser.add_argument(
        "--ensure",
        action="store_true",
        help="Idempotent: create if missing, no-op if present (default behaviour).",
    )
    args = parser.parse_args(argv)
    path = init_db(args.db)
    print(f"ok db={path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
