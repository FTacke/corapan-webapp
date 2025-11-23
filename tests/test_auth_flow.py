import secrets
from datetime import datetime, timezone

import pytest

from flask import Flask

from src.app.extensions.sqlalchemy_ext import init_engine, get_engine, get_session
from src.app.auth.models import Base, User, ResetToken, RefreshToken


@pytest.fixture
def client():
    app = Flask(__name__)
    app.config["AUTH_BACKEND"] = "db"
    app.config["AUTH_DATABASE_URL"] = "sqlite:///:memory:"
    app.config["AUTH_HASH_ALGO"] = "bcrypt"
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = False
    app.config["TESTING"] = True
    # disable cookie CSRF protections for tests (we set cookies manually)
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config["SECRET_KEY"] = "test-secret"

    from src.app.extensions import register_extensions
    from src.app.routes import register_blueprints

    register_extensions(app)
    init_engine(app)
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    register_blueprints(app)

    ctx = app.app_context()
    ctx.push()
    client = app.test_client()
    yield client
    ctx.pop()


def create_test_user(username: str = "alice") -> User:
    from src.app.auth import services

    with get_session() as session:
        u = User(
            id=str(secrets.token_hex(8)),
            username=username,
            email=f"{username}@example.org",
            password_hash=services.hash_password("password123"),
            role="user",
            is_active=True,
            must_reset_password=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(u)
    return u


def login_user(client, username="alice", password="password123"):
    # login and ensure cookies are set on the client so subsequent jwt_required calls work
    resp = client.post("/auth/login", json={"username": username, "password": password})
    # parse any Set-Cookie headers and set cookies into the test client
    for s in resp.headers.getlist("Set-Cookie"):
        try:
            name = s.split("=", 1)[0]
            val = s.split("=", 1)[1].split(";", 1)[0]
            # default path for refresh token is /auth/refresh but we set for full app path
            client.set_cookie(name, val, path="/")
        except Exception:
            continue
    # Ensure access token cookie exists on client (some test environments don't persist it)
    try:
        from src.app.auth import services

        user = services.find_user_by_username_or_email(username)
        if user:
            token = services.create_access_token_for_user(user)
            client.set_cookie("access_token_cookie", token, path="/")
    except Exception:
        pass
    return resp


def test_change_password_success_and_invalidate(client):
    u = create_test_user("changeuser")

    # login to set cookies
    resp = login_user(client, "changeuser")
    assert resp.status_code in (200, 303, 204)

    # ensure there is a refresh token present
    cookies = resp.headers.getlist("Set-Cookie")
    raw = None
    for s in cookies:
        if "refreshToken=" in s:
            raw = s.split("refreshToken=", 1)[1].split(";", 1)[0]
            break
    assert raw

    # create an extra refresh token for the user (simulate another session)
    from src.app.auth import services

    extra_raw, extra_row = services.create_refresh_token_for_user(u)

    # call change-password with correct old password
    r = client.post("/auth/change-password", json={"oldPassword": "password123", "newPassword": "new-strong-pass"})
    assert r.status_code == 200

    # all refresh tokens for user should be revoked
    with get_session() as session:
        rows = session.query(RefreshToken).filter(RefreshToken.user_id == str(u.id)).all()
        assert all(r.revoked_at is not None for r in rows)


def test_change_password_wrong_old_password(client):
    create_test_user("wrongold")
    resp = login_user(client, "wrongold")
    assert resp.status_code in (200, 303, 204)

    r = client.post("/auth/change-password", json={"oldPassword": "bad", "newPassword": "newpass"})
    assert r.status_code == 401


def test_reset_password_request_and_confirm(client):
    from src.app.auth import services

    u = create_test_user("resetme")

    # request reset should always return ok
    r = client.post("/auth/reset-password/request", json={"email": u.email})
    assert r.status_code == 200
    assert r.json.get("ok") is True

    # create token directly and confirm flow
    raw, row = services.create_reset_token_for_user(u)
    assert raw and row

    # confirm using route
    rc = client.post("/auth/reset-password/confirm", json={"resetToken": raw, "newPassword": "brand-new-pass"})
    assert rc.status_code == 200
    assert rc.json.get("ok") is True

    # token should be marked used
    with get_session() as session:
        rt = session.query(ResetToken).filter(ResetToken.token_hash == services._hash_refresh_token(raw)).first()
        assert rt is not None and rt.used_at is not None


def test_reset_password_confirm_errors(client):
    create_test_user("reseterr")

    # invalid token
    r = client.post("/auth/reset-password/confirm", json={"resetToken": "nope", "newPassword": "x"})
    assert r.status_code == 400


def test_profile_get_and_patch(client):
    from src.app.auth import services

    u = create_test_user("profuser")

    resp = login_user(client, "profuser")
    assert resp.status_code in (200, 303, 204)

    # GET profile
    g = client.get("/auth/account/profile")
    assert g.status_code == 200
    assert g.json.get("username") == "profuser"
    assert "password_hash" not in g.json

    # PATCH profile (update display_name and email)
    p = client.patch("/auth/account/profile", json={"display_name": "Prof", "email": "prof@example.org"})
    assert p.status_code == 200

    # verify DB updated
    with get_session() as session:
        row = session.query(User).filter(User.username == "profuser").first()
        assert getattr(row, "display_name", None) == "Prof"
        assert row.email == "prof@example.org"


def test_account_delete_and_data_export(client):
    from src.app.auth import services

    u = create_test_user("deleteme")
    # create refresh token to be revoked
    raw, rt = services.create_refresh_token_for_user(u)

    # login (to set access cookie)
    login_user(client, "deleteme")

    # attempt delete with wrong password
    r = client.post("/auth/account/delete", json={"password": "nope"})
    assert r.status_code == 401

    # delete with correct password
    r2 = client.post("/auth/account/delete", json={"password": "password123"})
    assert r2.status_code == 202

    # user should be soft-deleted and inactive
    with get_session() as session:
        row = session.query(User).filter(User.username == "deleteme").first()
        assert row.deleted_at is not None and row.deletion_requested_at is not None and not row.is_active

    # data-export should return user info when logged in (we need a fresh login for token)
    # create a new user/login - use different user
    uu = create_test_user("exporter")
    login_user(client, "exporter")
    de = client.get("/auth/account/data-export")
    assert de.status_code == 200
    assert "user" in de.json and "tokens" in de.json
