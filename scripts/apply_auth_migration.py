"""Apply auth database migrations for SQLite or PostgreSQL.

Usage:
  # SQLite (default)
  python scripts/apply_auth_migration.py --db data/db/auth.db

  # PostgreSQL (uses AUTH_DATABASE_URL or connection args)
  python scripts/apply_auth_migration.py --engine postgres

  # Reset and recreate
  python scripts/apply_auth_migration.py --engine postgres --reset
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
SQLITE_SQL_FILE = ROOT / "migrations" / "0001_create_auth_schema_sqlite.sql"
POSTGRES_SQL_FILE = ROOT / "migrations" / "0001_create_auth_schema_postgres.sql"
ANALYTICS_SQL_FILE = ROOT / "migrations" / "0002_create_analytics_tables.sql"
DEFAULT_DB = ROOT / "data" / "db" / "auth.db"


def apply_sqlite_migration(db_file: Path, reset: bool = False) -> None:
    """Apply SQLite migration."""
    if not SQLITE_SQL_FILE.exists():
        raise FileNotFoundError(f"Migration SQL not found: {SQLITE_SQL_FILE}")

    if reset and db_file.exists():
        try:
            db_file.unlink()
            print(f"Deleted existing DB file: {db_file}")
        except OSError as e:
            print(f"Warning: failed to delete DB file {db_file}: {e}")

    db_file.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(db_file)) as conn:
        with open(SQLITE_SQL_FILE, "r", encoding="utf-8") as f:
            sql = f.read()
        try:
            conn.executescript(sql)
            print(f"SQLite migration applied to {db_file}")
        except sqlite3.DatabaseError as e:
            print(f"Failed to apply migration: {e}")
            raise


def apply_postgres_migration(reset: bool = False) -> None:
    """Apply PostgreSQL migration using AUTH_DATABASE_URL."""
    import sys

    try:
        import psycopg
    except ImportError:
        print(
            "ERROR: psycopg not installed. Run: pip install psycopg[binary]",
            file=sys.stderr,
        )
        sys.exit(1)

    if not POSTGRES_SQL_FILE.exists():
        print(f"ERROR: Migration SQL not found: {POSTGRES_SQL_FILE}", file=sys.stderr)
        sys.exit(1)

    db_url = os.getenv("AUTH_DATABASE_URL", "")
    if not db_url or not db_url.startswith("postgresql"):
        # Default to local dev Postgres
        db_url = "postgresql://corapan_auth:corapan_auth@localhost:54320/corapan_auth"
        print(f"Using default dev Postgres URL: {db_url}")

    # Convert SQLAlchemy URL to psycopg format
    # postgresql+psycopg://... -> postgresql://...
    if "+psycopg" in db_url:
        db_url = db_url.replace("+psycopg", "")

    # Add connect_timeout if not present
    if "connect_timeout" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{separator}connect_timeout=10"

    with open(POSTGRES_SQL_FILE, "r", encoding="utf-8") as f:
        sql = f.read()

    # Remove explicit BEGIN/COMMIT from SQL as psycopg handles transactions
    # This prevents nested transaction issues
    sql = sql.replace("BEGIN;", "").replace("COMMIT;", "")

    conn = None
    try:
        print("Connecting to PostgreSQL...")
        conn = psycopg.connect(db_url)
        print("Connected successfully.")

        with conn.cursor() as cur:
            if reset:
                # Drop existing tables (in reverse order of dependencies)
                print("Dropping existing auth tables...")
                cur.execute("DROP TABLE IF EXISTS analytics_daily CASCADE")
                cur.execute("DROP TABLE IF EXISTS reset_tokens CASCADE")
                cur.execute("DROP TABLE IF EXISTS refresh_tokens CASCADE")
                cur.execute("DROP TABLE IF EXISTS users CASCADE")
                cur.execute("DROP TYPE IF EXISTS user_role CASCADE")
                conn.commit()
                print("Existing tables dropped.")

            # Apply migration
            print("Executing auth migration SQL...")
            cur.execute(sql)
            conn.commit()
            print("PostgreSQL auth migration applied successfully.")

            # Apply analytics migration (0002)
            if ANALYTICS_SQL_FILE.exists():
                print("Executing analytics migration SQL...")
                with open(ANALYTICS_SQL_FILE, "r", encoding="utf-8") as f:
                    analytics_sql = f.read()
                analytics_sql = analytics_sql.replace("BEGIN;", "").replace(
                    "COMMIT;", ""
                )
                cur.execute(analytics_sql)
                conn.commit()
                print("PostgreSQL analytics migration applied successfully.")
            else:
                print(f"Warning: Analytics migration not found: {ANALYTICS_SQL_FILE}")

    except psycopg.OperationalError as e:
        print(f"ERROR: Database connection failed: {e}", file=sys.stderr)
        sys.exit(1)
    except psycopg.Error as e:
        print(f"ERROR: Migration failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply auth database migrations")
    parser.add_argument("--db", help="Path to SQLite DB file", default=str(DEFAULT_DB))
    parser.add_argument(
        "--engine",
        choices=["sqlite", "postgres"],
        default="sqlite",
        help="Database engine to use (default: sqlite)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="DROP existing tables before applying migration (dev-only).",
    )
    args = parser.parse_args()

    if args.engine == "postgres":
        print(f"Applying PostgreSQL migration (reset={args.reset})...")
        apply_postgres_migration(reset=args.reset)
    else:
        db_file = Path(args.db)
        print(f"Applying SQLite migration to: {db_file} (reset={args.reset})")
        apply_sqlite_migration(db_file, reset=args.reset)
