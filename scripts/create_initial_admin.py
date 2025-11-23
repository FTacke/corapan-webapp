"""Create or update an initial admin user in the AUTH database.

This helper supports both a local sqlite DB file (default) and any SQLAlchemy
URL provided via the `AUTH_DATABASE_URL` environment variable.

Usage (PowerShell):
  $env:START_ADMIN_USERNAME='admin'; $env:START_ADMIN_PASSWORD='change-me'; python scripts/create_initial_admin.py

Or explicit DB file (sqlite):
  python scripts/create_initial_admin.py --db data/db/auth.db --username admin --password mypass

This script is intentionally small and non-destructive: it will create the
database tables if missing and either create a new admin user or update an
existing user with the same username (setting role=admin, is_active=True).
"""
from __future__ import annotations

import os
from pathlib import Path
import argparse
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", help="Path to sqlite DB file (defaults data/db/auth.db)", default="data/db/auth.db")
    parser.add_argument("--username", default=os.environ.get("START_ADMIN_USERNAME", "admin"))
    parser.add_argument("--password", default=os.environ.get("START_ADMIN_PASSWORD", "change-me"))
    args = parser.parse_args()

    # Setup a minimal app-like config for the SQLAlchemy helpers
    # config must behave like a mapping with .get() for the SQLAlchemy helper
    cfg = {
        "AUTH_DATABASE_URL": os.environ.get("AUTH_DATABASE_URL", f"sqlite:///{Path(args.db).as_posix()}")
    }
    # allow optional override for the hashing algorithm used by services
    cfg["AUTH_HASH_ALGO"] = os.environ.get("AUTH_HASH_ALGO", "argon2")

    # initialize auth engine and create tables
    import sys

    # ensure repository package path is available when running the script directly
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from src.app.extensions.sqlalchemy_ext import init_engine, get_engine, get_session
    from src.app.auth.models import Base, User
    from src.app.auth import services

    class AppLike:
        def __init__(self, cfg):
            # mimic Flask app.config API (mapping-like get)
            self.config = cfg

    app = AppLike(cfg)
    init_engine(app)
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    # We need a Flask app context for service helpers that read current_app.config
    from flask import Flask

    tmp_app = Flask("create_initial_admin")
    tmp_app.config.update(cfg)

    with tmp_app.app_context():
        with get_session() as session:
            # Check if username exists
            existing = session.query(User).filter(User.username == args.username).first()
            now = datetime.now(timezone.utc)
            def _safe_hash(pw: str) -> str:
                # try configured hashing algorithm first, fall back to bcrypt if unavailable
                try:
                    return services.hash_password(pw)
                except Exception as e:
                    # fall back to bcrypt
                    tmp_app.logger.debug("hashing fallback (bcrypt) due to: %s", e)
                    tmp_app.config["AUTH_HASH_ALGO"] = "bcrypt"
                    return services.hash_password(pw)

            if existing:
                existing.role = "admin"
                existing.is_active = True
                existing.must_reset_password = True
                existing.password_hash = _safe_hash(args.password)
                existing.updated_at = now
                print(f"Updated existing user '{args.username}' as admin (must_reset_password=True)")
            else:
                # create a new admin user
                import secrets

                u = User(
                    id=str(secrets.token_hex(8)),
                    username=args.username,
                    email=f"{args.username}@example.org",
                    password_hash=_safe_hash(args.password),
                    role="admin",
                    is_active=True,
                    must_reset_password=True,
                    created_at=now,
                    updated_at=now,
                )
                session.add(u)
                print(f"Created admin user '{args.username}' (must_reset_password=True)")


if __name__ == "__main__":
    main()
