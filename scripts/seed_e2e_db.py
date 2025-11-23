"""Seed a test DB with an E2E user account.

Usage:
  python scripts/seed_e2e_db.py --db data/db/auth_e2e.db --user e2e_user --password password123

This is intentionally simple: it configures the auth engine and creates the tables
and a single user for browser E2E smoke tests.
"""
from pathlib import Path
import argparse
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/db/auth_e2e.db")
    parser.add_argument("--user", default="e2e_user")
    parser.add_argument("--password", default="password123")
    args = parser.parse_args()

    # ensure parent folder exists
    p = Path(args.db)
    p.parent.mkdir(parents=True, exist_ok=True)

    # minimal Flask-like config object for init_engine
    class C:
        pass

    cfg = C()
    cfg.AUTH_DATABASE_URL = f"sqlite:///{p.as_posix()}"
    cfg.AUTH_HASH_ALGO = "bcrypt"

    # initialize auth engine and create tables
    from src.app.extensions.sqlalchemy_ext import init_engine, get_engine, get_session
    from src.app.auth.models import Base, User
    from src.app.auth import services

    # use a tiny fake app container since init_engine expects an app with config
    class AppLike:
        def __init__(self, cfg):
            self.config = cfg

    app = AppLike(cfg)
    init_engine(app)
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    # seed user (id, username, email, hash, role)
    import secrets

    with get_session() as session:
        if session.query(User).filter(User.username == args.user).first():
            print("User already present — skipping")
            return

        u = User(
            id=str(secrets.token_hex(8)),
            username=args.user,
            email=f"{args.user}@example.org",
            password_hash=services.hash_password(args.password),
            role="user",
            is_active=True,
            must_reset_password=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(u)

    print(f"Seeded {args.user} in {p}")


if __name__ == "__main__":
    main()
