"""Small helper to apply the SQLite auth migration SQL to a specified SQLite DB file.

Usage (PowerShell):
  $env:DB_FILE="C:\dev\corapan-webapp\data\db\auth.db"; python scripts/apply_auth_migration.py

If DB_FILE is not provided, defaults to data/db/auth.db and creates directory if needed.
This script is intentionally simple and safe: it reads the SQL file migrations/0001_create_auth_schema_sqlite.sql
and executes it within a transaction using sqlite3.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
SQL_FILE = ROOT / "migrations" / "0001_create_auth_schema_sqlite.sql"
DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "db" / "auth.db"


def apply_sqlite_migration(db_file: Path) -> None:
    if not SQL_FILE.exists():
        raise FileNotFoundError(f"Migration SQL not found: {SQL_FILE}")

    db_file.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(db_file)) as conn:
        with open(SQL_FILE, "r", encoding="utf-8") as f:
            sql = f.read()
        try:
            conn.executescript(sql)
            print(f"Migration applied to {db_file}")
        except sqlite3.DatabaseError as e:
            print(f"Failed to apply migration: {e}")
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", help="Path to sqlite DB file", default=str(DEFAULT_DB))
    args = parser.parse_args()
    apply_sqlite_migration(Path(args.db))
