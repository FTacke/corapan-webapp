#!/usr/bin/env python3
"""Production database setup script for CO.RA.PAN.

This script is designed to be run inside the Docker container during deployment.
It performs the following tasks:
1. Applies database migrations (creates schema if not present)
2. Checks if an admin user exists
3. Creates an initial admin user if none exists

The script is idempotent - running it multiple times is safe and will not
create duplicate admin users or cause errors.

Usage (inside container):
    docker exec corapan-webapp python scripts/setup_prod_db.py

Environment Variables:
    DATABASE_URL or AUTH_DATABASE_URL - PostgreSQL connection string
        Example: postgresql://corapan_app:password@localhost:5432/corapan_auth
    ADMIN_EMAIL - Optional email for admin user (default: admin@example.org)
    AUTH_HASH_ALGO - Password hashing algorithm (default: argon2)

The script reads DATABASE_URL from the environment or from passwords.env if present.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Ensure repository package path is available
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_env_file(env_path: Path) -> dict[str, str]:
    """Load environment variables from a file."""
    env_vars = {}
    if not env_path.exists():
        return env_vars
    
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                # Strip quotes if present
                value = value.strip().strip("'\"")
                env_vars[key.strip()] = value
    return env_vars


def get_database_url() -> str:
    """Get database URL from environment or passwords.env file."""
    # Try environment variables first
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("AUTH_DATABASE_URL")
    if db_url:
        return db_url
    
    # Try loading from passwords.env
    passwords_env = ROOT / "passwords.env"
    if passwords_env.exists():
        env_vars = load_env_file(passwords_env)
        db_url = env_vars.get("DATABASE_URL") or env_vars.get("AUTH_DATABASE_URL")
        if db_url:
            return db_url
    
    raise RuntimeError(
        "DATABASE_URL not found. Set it in environment or in passwords.env"
    )


def apply_migrations(db_url: str) -> None:
    """Apply database migrations using the existing migration script logic."""
    print("Applying database migrations...")
    
    # Use psycopg for PostgreSQL
    try:
        import psycopg
    except ImportError:
        print("ERROR: psycopg not installed. Run: pip install psycopg[binary]", file=sys.stderr)
        sys.exit(1)
    
    # Migration files to apply (in order)
    migration_files = [
        ROOT / "migrations" / "0001_create_auth_schema_postgres.sql",
        ROOT / "migrations" / "0002_create_analytics_tables.sql",
    ]
    
    # Check all migration files exist
    for migration_file in migration_files:
        if not migration_file.exists():
            print(f"ERROR: Migration file not found: {migration_file}", file=sys.stderr)
            sys.exit(1)
    
    # Convert SQLAlchemy URL format to psycopg format
    conn_url = db_url
    if "+psycopg" in conn_url:
        conn_url = conn_url.replace("+psycopg", "")
    
    # Add connect_timeout if not present
    if "connect_timeout" not in conn_url:
        separator = "&" if "?" in conn_url else "?"
        conn_url = f"{conn_url}{separator}connect_timeout=10"
    
    try:
        with psycopg.connect(conn_url) as conn:
            for migration_file in migration_files:
                print(f"  Applying {migration_file.name}...")
                with open(migration_file, "r", encoding="utf-8") as f:
                    sql = f.read()
                # Remove explicit BEGIN/COMMIT as psycopg handles transactions
                sql = sql.replace("BEGIN;", "").replace("COMMIT;", "")
                conn.execute(sql)
                conn.commit()
                print(f"  ✓ {migration_file.name} applied")
        print("✓ All database migrations applied successfully")
    except psycopg.OperationalError as e:
        print(f"ERROR: Failed to connect to database: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Migration failed: {e}", file=sys.stderr)
        sys.exit(1)


def ensure_admin_user(db_url: str) -> None:
    """Ensure an admin user exists in the database."""
    print("Checking for admin user...")
    
    from sqlalchemy.exc import SQLAlchemyError
    from src.app.extensions.sqlalchemy_ext import init_engine, get_engine, get_session
    from src.app.auth.models import Base, User
    from src.app.auth import services
    
    # Prepare SQLAlchemy URL (ensure correct dialect)
    sa_url = db_url
    if sa_url.startswith("postgresql://") and "+psycopg" not in sa_url:
        sa_url = sa_url.replace("postgresql://", "postgresql+psycopg://")
    
    # Configuration for SQLAlchemy
    cfg = {
        "AUTH_DATABASE_URL": sa_url,
        "AUTH_HASH_ALGO": os.environ.get("AUTH_HASH_ALGO", "argon2"),
    }
    
    class AppLike:
        def __init__(self, cfg):
            self.config = cfg
    
    app = AppLike(cfg)
    
    try:
        init_engine(app)
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as e:
        print(f"ERROR: Database initialization failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create Flask app context for service helpers
    from flask import Flask
    tmp_app = Flask("setup_prod_db")
    tmp_app.config.update(cfg)
    
    admin_username = "admin"
    admin_password = "change-me"
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.org")
    
    with tmp_app.app_context():
        with get_session() as session:
            # Check if admin exists
            existing = session.query(User).filter(User.username == admin_username).first()
            
            if existing:
                print(f"✓ Admin user '{admin_username}' already exists (id: {existing.id})")
                return
            
            # Create new admin user
            import uuid
            now = datetime.now(timezone.utc)
            
            def _safe_hash(pw: str) -> str:
                try:
                    return services.hash_password(pw)
                except Exception:
                    # Fall back to bcrypt if argon2 unavailable
                    tmp_app.config["AUTH_HASH_ALGO"] = "bcrypt"
                    return services.hash_password(pw)
            
            user = User(
                id=str(uuid.uuid4()),
                username=admin_username,
                email=admin_email,
                password_hash=_safe_hash(admin_password),
                role="admin",
                is_active=True,
                must_reset_password=False,
                login_failed_count=0,
                locked_until=None,
                deleted_at=None,
                deletion_requested_at=None,
                created_at=now,
                updated_at=now,
            )
            session.add(user)
            print(f"✓ Created admin user '{admin_username}' with password 'change-me'")
            print("  ⚠️  IMPORTANT: Change the admin password immediately after first login!")


def main() -> None:
    """Main entry point for production database setup."""
    print("=" * 60)
    print("CO.RA.PAN Production Database Setup")
    print("=" * 60)
    
    try:
        db_url = get_database_url()
        # Mask password in output
        masked_url = db_url
        if "@" in db_url:
            parts = db_url.split("@")
            user_part = parts[0].rsplit(":", 1)[0]
            masked_url = f"{user_part}:***@{parts[1]}"
        print(f"Database: {masked_url}")
        print()
        
        apply_migrations(db_url)
        ensure_admin_user(db_url)
        
        print()
        print("=" * 60)
        print("✓ Database setup completed successfully")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
