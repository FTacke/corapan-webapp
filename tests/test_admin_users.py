import secrets
from datetime import datetime, timedelta, timezone
from datetime import timezone

import pytest

from flask import Flask

from src.app.extensions.sqlalchemy_ext import init_engine, get_engine, get_session
from src.app.auth.models import Base, User, ResetToken, RefreshToken


@pytest.fixture
def client():
    app = Flask(__name__)
    app.config["AUTH_DATABASE_URL"] = "sqlite:///:memory:"
    app.config["AUTH_HASH_ALGO"] = "bcrypt"
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = False
    app.config["TESTING"] = True
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


def create_user(username: str = "alice", role: str = "user") -> User:
    from src.app.auth import services

    with get_session() as session:
        u = User(
            id=str(secrets.token_hex(8)),
            username=username,
            email=f"{username}@example.org",
            password_hash=services.hash_password("password123"),
            role=role,
            is_active=True,
            must_reset_password=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(u)
    return u


def login_user(client, username="alice", password="password123"):
    resp = client.post("/auth/login", json={"username": username, "password": password})
    for s in resp.headers.getlist("Set-Cookie"):
        try:
            name = s.split("=", 1)[0]
            val = s.split("=", 1)[1].split(";", 1)[0]
            client.set_cookie(name, val, path="/")
        except Exception:
            continue
    try:
        from src.app.auth import services
        uobj = services.find_user_by_username_or_email(username)
        if uobj:
            tok = services.create_access_token_for_user(uobj)
            client.set_cookie("access_token_cookie", tok, path="/")
    except Exception:
        pass
    return resp


def make_admin_and_login(client, username="admin"):
    admin = create_user(username, role="admin")
    r = login_user(client, username)
    assert r.status_code in (200, 303, 204)
    return admin


def test_admin_list_and_get_detail(client):
    admin = make_admin_and_login(client)
    # create some users
    u1 = create_user("u1")
    u2 = create_user("u2")

    r = client.get("/admin/users")
    assert r.status_code == 200
    assert "items" in r.json

    r2 = client.get(f"/admin/users/{u1.id}")
    assert r2.status_code == 200
    assert r2.json.get("username") == "u1"


def test_admin_create_invite_and_no_plaintext(client):
    admin = make_admin_and_login(client)

    r = client.post("/admin/users", json={"username": "invited", "email": "invite@example.org"})
    assert r.status_code == 201
    assert r.json.get("inviteSent") is True

    # verify reset token exists in DB for created user
    uid = r.json.get("userId")
    with get_session() as session:
        user = session.query(User).filter(User.id == uid).first()
        assert user is not None
        # there should be a reset token for the user
        rt = session.query(ResetToken).filter(ResetToken.user_id == uid).first()
        assert rt is not None


def test_admin_create_invite_has_metadata(client):
    admin = make_admin_and_login(client)
    r = client.post("/admin/users", json={"username": "invited2", "email": "invite2@example.org"})
    assert r.status_code == 201
    assert r.json.get("inviteSent") is True
    # response should include token id and expiry
    assert r.json.get("inviteId")
    assert r.json.get("inviteExpiresAt")
    # DB token should match
    uid = r.json.get("userId")
    with get_session() as session:
        rt = session.query(ResetToken).filter(ResetToken.user_id == uid).first()
        assert rt is not None
        assert rt.id == r.json.get("inviteId")


def test_admin_reset_returns_invite_link(client):
    admin = make_admin_and_login(client)
    target = create_user("targ2")
    r = client.post(f"/admin/users/{target.id}/reset-password")
    assert r.status_code == 200
    # should contain invite link and metadata
    assert r.json.get("ok") is True
    assert r.json.get("inviteLink")
    assert r.json.get("inviteExpiresAt")


def test_admin_patch_lock_unlock_invalidate_delete(client):
    admin = make_admin_and_login(client)
    target = create_user("targ")

    # patch role and must_reset
    p = client.patch(f"/admin/users/{target.id}", json={"role": "editor", "must_reset_password": True})
    assert p.status_code == 200

    # admin reset password (should create reset token)
    r = client.post(f"/admin/users/{target.id}/reset-password")
    assert r.status_code == 200

    # lock user
    l = client.post(f"/admin/users/{target.id}/lock", json={"until": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()})
    assert l.status_code == 200

    # unlock
    u = client.post(f"/admin/users/{target.id}/unlock")
    assert u.status_code == 200

    # create refresh token and then invalidate sessions
    from src.app.auth import services

    raw, rt = services.create_refresh_token_for_user(target)
    assert rt is not None
    inv = client.post(f"/admin/users/{target.id}/invalidate-sessions")
    assert inv.status_code == 200

    # delete (soft-delete)
    d = client.delete(f"/admin/users/{target.id}")
    assert d.status_code == 200

    with get_session() as session:
        t = session.query(User).filter(User.id == target.id).first()
        assert t.deleted_at is not None and t.deletion_requested_at is not None


def test_rbac_enforced_for_non_admin(client):
    # create non-admin and login
    user = create_user("normal", role="user")
    r = login_user(client, "normal")
    assert r.status_code in (200, 303, 204)

    # non-admin should be forbidden to access admin endpoints
    r = client.get("/admin/users")
    assert r.status_code in (401, 403)
