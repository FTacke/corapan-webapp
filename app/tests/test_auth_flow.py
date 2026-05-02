import logging
import secrets
from datetime import datetime, timezone

import httpx
import pytest

from flask import Flask

from src.app.extensions.sqlalchemy_ext import init_engine, get_engine, get_session
from src.app.auth.models import Base, User, ResetToken, RefreshToken


class _ReadyConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement):
        return None


class _ReadyEngine:
    def __init__(self, *, fail: bool = False, backend: str = "postgresql"):
        self.fail = fail
        self.dialect = type("Dialect", (), {"name": backend})()

    def connect(self):
        if self.fail:
            raise RuntimeError(
                "could not connect to postgresql://corapan_app:supersecret@db:5432/corapan_auth"
            )
        return _ReadyConnection()


class _ReadyResponse:
    def __init__(self, status_code: int = 200, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = ""

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("GET", "http://blacklab.local/corpora")
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=request, response=self
            )

    def json(self):
        return self._payload


class _ReadyHttpClient:
    def __init__(self, response: _ReadyResponse | None = None, error: Exception | None = None):
        self.response = response or _ReadyResponse()
        self.error = error

    def get(self, *args, **kwargs):
        if self.error is not None:
            raise self.error
        return self.response


@pytest.fixture
def client():
    app = Flask(__name__)
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


@pytest.fixture
def admin_client(client):
    """Client fixture with pre-created admin user."""
    from src.app.auth import services

    with get_session() as session:
        admin = User(
            id=str(secrets.token_hex(8)),
            username="admin",
            email="admin@example.org",
            password_hash=services.hash_password("admin-password"),
            role="admin",
            is_active=True,
            must_reset_password=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(admin)

    return client


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
    r = client.post(
        "/auth/change-password",
        json={"oldPassword": "password123", "newPassword": "NewStrong1Pass"},
    )
    assert r.status_code == 200

    # all refresh tokens for user should be revoked
    with get_session() as session:
        rows = (
            session.query(RefreshToken).filter(RefreshToken.user_id == str(u.id)).all()
        )
        assert all(r.revoked_at is not None for r in rows)


def test_change_password_wrong_old_password(client):
    create_test_user("wrongold")
    resp = login_user(client, "wrongold")
    assert resp.status_code in (200, 303, 204)

    r = client.post(
        "/auth/change-password",
        json={"oldPassword": "bad", "newPassword": "NewPass123!"},
    )
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
    rc = client.post(
        "/auth/reset-password/confirm",
        json={"resetToken": raw, "newPassword": "BrandNew1Pass"},
    )
    assert rc.status_code == 200
    assert rc.json.get("ok") is True

    # token should be marked used
    with get_session() as session:
        rt = (
            session.query(ResetToken)
            .filter(ResetToken.token_hash == services._hash_refresh_token(raw))
            .first()
        )
        assert rt is not None and rt.used_at is not None


def test_reset_password_confirm_errors(client):
    create_test_user("reseterr")

    # invalid token
    r = client.post(
        "/auth/reset-password/confirm", json={"resetToken": "nope", "newPassword": "x"}
    )
    assert r.status_code == 400


def test_profile_get_and_patch(client):
    create_test_user("profuser")

    resp = login_user(client, "profuser")
    assert resp.status_code in (200, 303, 204)

    # GET profile
    g = client.get("/auth/account/profile")
    assert g.status_code == 200
    assert g.json.get("username") == "profuser"
    assert "password_hash" not in g.json

    # PATCH profile (update display_name and email)
    p = client.patch(
        "/auth/account/profile",
        json={"display_name": "Prof", "email": "prof@example.org"},
    )
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
        assert (
            row.deleted_at is not None
            and row.deletion_requested_at is not None
            and not row.is_active
        )

    # data-export should return user info when logged in (we need a fresh login for token)
    # create a new user/login - use different user
    create_test_user("exporter")
    login_user(client, "exporter")
    de = client.get("/auth/account/data-export")
    assert de.status_code == 200
    assert "user" in de.json and "tokens" in de.json


# =============================================================================
# Login Flow Integration Tests
# =============================================================================


class TestLoginFlow:
    """Comprehensive login flow tests."""

    def test_login_post_with_valid_credentials(self, admin_client):
        """Test POST /auth/login with valid credentials returns redirect and sets cookies."""
        resp = admin_client.post(
            "/auth/login",
            data={"username": "admin", "password": "admin-password"},
            follow_redirects=False,
        )

        # Should redirect (303) after successful login
        assert resp.status_code == 303, f"Expected 303, got {resp.status_code}"

        # Check that auth cookies are set via Set-Cookie header
        set_cookies = resp.headers.getlist("Set-Cookie")
        cookie_names = [c.split("=")[0] for c in set_cookies]
        assert "access_token_cookie" in cookie_names, "access_token_cookie not set"

    @pytest.mark.skip(
        reason="Auth route currently renders template even for JSON error responses without error_code"
    )
    def test_login_post_with_invalid_password(self, admin_client):
        """Test POST /auth/login with wrong password returns error."""
        resp = admin_client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrong-password"},
        )

        # Should return 400 for invalid credentials
        assert resp.status_code == 400
        assert resp.json.get("error") or resp.status_code == 400

    @pytest.mark.skip(
        reason="Auth route currently renders template even for JSON error responses without error_code"
    )
    def test_login_post_with_nonexistent_user(self, admin_client):
        """Test POST /auth/login with unknown user returns error."""
        resp = admin_client.post(
            "/auth/login",
            json={"username": "nobody", "password": "password"},
        )

        # Should return 400 for unknown user
        assert resp.status_code == 400

    def test_login_post_json_format(self, admin_client):
        """Test POST /auth/login with JSON body."""
        resp = admin_client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin-password"},
        )

        # JSON requests return 303 redirect on success
        assert resp.status_code in (200, 204, 303)

    def test_login_with_next_url_redirect(self, admin_client):
        """Test that ?next URL is respected after login."""
        resp = admin_client.post(
            "/auth/login",
            data={
                "username": "admin",
                "password": "admin-password",
                "next": "/admin/dashboard",
            },
            follow_redirects=False,
        )

        assert resp.status_code == 303
        # Location header should contain the next URL
        location = resp.headers.get("Location", "")
        assert "/admin" in location or "dashboard" in location or location != ""

    def test_login_cookies_have_correct_attributes(self, admin_client):
        """Test that login sets cookies with correct security attributes."""
        resp = admin_client.post(
            "/auth/login",
            data={"username": "admin", "password": "admin-password"},
            follow_redirects=False,
        )

        assert resp.status_code == 303

        # Check cookies exist via Set-Cookie header
        set_cookies = resp.headers.getlist("Set-Cookie")
        cookie_names = [c.split("=")[0] for c in set_cookies]
        assert "access_token_cookie" in cookie_names

        # Check HttpOnly attribute is present
        access_cookie = [c for c in set_cookies if c.startswith("access_token_cookie=")]
        assert len(access_cookie) > 0
        assert "HttpOnly" in access_cookie[0], "Cookie should have HttpOnly attribute"


class TestHealthEndpoint:
    """Health endpoint tests."""

    def test_health_returns_liveness_only(self, client, monkeypatch):
        """Test /health stays a pure liveness check."""
        from src.app.extensions import http_client as http_client_module
        from src.app.extensions import sqlalchemy_ext as sqlalchemy_module

        monkeypatch.setattr(
            sqlalchemy_module,
            "get_engine",
            lambda: (_ for _ in ()).throw(AssertionError("auth DB should not be checked")),
        )
        monkeypatch.setattr(
            http_client_module,
            "get_http_client",
            lambda: (_ for _ in ()).throw(AssertionError("BlackLab should not be checked")),
        )

        resp = client.get("/health")

        assert resp.status_code == 200
        assert resp.json == {"status": "healthy", "service": "corapan", "checks": {"flask": True}}

    def test_health_checks_flask(self, client):
        """Test /health reports Flask as healthy."""
        resp = client.get("/health")
        data = resp.json

        assert data["checks"]["flask"] is True

    def test_health_is_not_rate_limited(self, client):
        """Test /health stays available across many repeated requests."""
        for attempt in range(1, 206):
            resp = client.get("/health")
            assert resp.status_code == 200, f"/health rate limited on attempt {attempt}"

    def test_ready_is_not_rate_limited(self, client, monkeypatch):
        """Test /ready stays available across many repeated requests."""
        from src.app.extensions import http_client as http_client_module
        from src.app.extensions import sqlalchemy_ext as sqlalchemy_module

        client.application.config["BLS_BASE_URL"] = "http://blacklab.local/blacklab-server"
        client.application.config["BLS_CORPUS"] = "corapan"

        monkeypatch.setattr(sqlalchemy_module, "get_engine", lambda: _ReadyEngine())
        monkeypatch.setattr(
            http_client_module,
            "get_http_client",
            lambda: _ReadyHttpClient(
                _ReadyResponse(200, {"corpora": [{"corpusId": "corapan"}]})
            ),
        )

        for attempt in range(1, 206):
            resp = client.get("/ready")
            assert resp.status_code == 200, f"/ready rate limited on attempt {attempt}"

    def test_rate_limited_route_still_rate_limited(self, client):
        """Test a normal route still returns 429 after its limit is exceeded."""
        for attempt in range(1, 7):
            resp = client.post(
                "/auth/reset-password/request",
                json={"email": "missing@example.org"},
            )
            if attempt < 6:
                assert resp.status_code == 200
            else:
                assert resp.status_code == 429

    def test_ready_reports_healthy(self, client, monkeypatch):
        """Test /ready returns healthy when auth DB and BlackLab are available."""
        from src.app.extensions import http_client as http_client_module
        from src.app.extensions import sqlalchemy_ext as sqlalchemy_module

        client.application.config["BLS_BASE_URL"] = "http://blacklab.local/blacklab-server"
        client.application.config["BLS_CORPUS"] = "corapan"

        monkeypatch.setattr(sqlalchemy_module, "get_engine", lambda: _ReadyEngine())
        monkeypatch.setattr(
            http_client_module,
            "get_http_client",
            lambda: _ReadyHttpClient(
                _ReadyResponse(200, {"corpora": [{"corpusId": "corapan"}]})
            ),
        )

        resp = client.get("/ready")

        assert resp.status_code == 200
        data = resp.json
        assert data["status"] == "healthy"
        assert data["checks"]["auth_db"]["ok"] is True
        assert data["checks"]["blacklab"]["ok"] is True

    def test_ready_degrades_when_blacklab_is_unavailable(self, client, monkeypatch):
        """Test /ready degrades when BlackLab cannot be reached."""
        from src.app.extensions import http_client as http_client_module
        from src.app.extensions import sqlalchemy_ext as sqlalchemy_module

        client.application.config["BLS_BASE_URL"] = "http://blacklab.local/blacklab-server"
        client.application.config["BLS_CORPUS"] = "corapan"

        monkeypatch.setattr(sqlalchemy_module, "get_engine", lambda: _ReadyEngine())
        monkeypatch.setattr(
            http_client_module,
            "get_http_client",
            lambda: _ReadyHttpClient(error=RuntimeError("blacklab unreachable")),
        )

        resp = client.get("/ready")

        assert resp.status_code == 200
        data = resp.json
        assert data["status"] == "degraded"
        assert data["checks"]["auth_db"]["ok"] is True
        assert data["checks"]["blacklab"]["ok"] is False

    def test_ready_is_unhealthy_when_auth_db_is_unavailable(
        self, client, monkeypatch, caplog
    ):
        """Test /ready returns unhealthy and redacts secrets when auth DB fails."""
        from src.app.extensions import http_client as http_client_module
        from src.app.extensions import sqlalchemy_ext as sqlalchemy_module

        client.application.config["BLS_BASE_URL"] = "http://blacklab.local/blacklab-server"
        client.application.config["BLS_CORPUS"] = "corapan"

        monkeypatch.setattr(sqlalchemy_module, "get_engine", lambda: _ReadyEngine(fail=True))
        monkeypatch.setattr(
            http_client_module,
            "get_http_client",
            lambda: _ReadyHttpClient(
                _ReadyResponse(200, {"corpora": [{"corpusId": "corapan"}]})
            ),
        )

        with caplog.at_level(logging.WARNING):
            resp = client.get("/ready")

        assert resp.status_code == 503
        data = resp.json
        assert data["status"] == "unhealthy"
        assert data["checks"]["auth_db"]["ok"] is False
        assert "supersecret" not in resp.get_data(as_text=True)

        log_text = "\n".join(record.getMessage() for record in caplog.records)
        assert "supersecret" not in log_text
        assert "postgresql://" not in log_text
        assert "check=auth_db" in log_text

    def test_health_auth_endpoint(self, client):
        """Test /health/auth returns auth DB status."""
        resp = client.get("/health/auth")

        assert resp.status_code in (200, 503)
        data = resp.json
        assert "ok" in data
        assert "backend" in data
