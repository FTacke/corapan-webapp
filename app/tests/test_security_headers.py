import os
from pathlib import Path

import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("CORAPAN_RUNTIME_ROOT", str(WORKSPACE_ROOT))
os.environ.setdefault("CORAPAN_MEDIA_ROOT", str(WORKSPACE_ROOT / "media"))
os.environ.setdefault("BLS_CORPUS", "corapan")


@pytest.fixture
def client():
    from flask import Flask

    project_root = Path(__file__).resolve().parents[1]
    template_dir = project_root / "templates"
    static_dir = project_root / "static"

    app = Flask(
        __name__, template_folder=str(template_dir), static_folder=str(static_dir)
    )
    app.config["AUTH_DATABASE_URL"] = "sqlite:///:memory:"
    app.config["AUTH_HASH_ALGO"] = "bcrypt"
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config["JWT_COOKIE_SECURE"] = False
    app.config["TESTING"] = True

    from src.app.extensions.sqlalchemy_ext import init_engine as init_auth, get_engine
    from src.app.auth.models import Base
    from src.app.extensions import register_extensions
    from src.app.routes import register_blueprints

    register_extensions(app)
    init_auth(app)
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    register_blueprints(app)

    # register global context processors and security headers used by create_app
    from src.app import register_context_processors, register_security_headers

    register_context_processors(app)
    register_security_headers(app)

    # ensure template helpers are available (already registered above)

    ctx = app.app_context()
    ctx.push()
    client = app.test_client()
    yield client
    ctx.pop()


def test_csp_script_src_no_unsafe_inline(client):
    r = client.get("/")
    assert "Content-Security-Policy" in r.headers
    csp = r.headers["Content-Security-Policy"]
    # Ensure 'unsafe-inline' was removed for scripts (styles still need it until jQuery migration)
    assert "script-src" in csp
    assert "'unsafe-inline'" not in csp.split("script-src", 1)[1].split(";", 1)[0]
    assert "style-src" in csp
    # NOTE: style-src still contains 'unsafe-inline' due to jQuery/DataTables dependency
    # This will be removed after jQuery migration (see TODO in src/app/__init__.py:213)
    # For now, we only verify that script-src doesn't have unsafe-inline


def test_goatcounter_disabled_by_default(client):
    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-goatcounter=' not in html
    assert 'https://gc.zgo.at/count.js' not in html
    assert 'js/modules/core/entry.js' in html
    assert "Content-Security-Policy" in response.headers
    csp = response.headers["Content-Security-Policy"]
    assert "https://gc.zgo.at" not in csp


def test_goatcounter_enabled_renders_once_and_updates_csp(client):
    client.application.config["GOATCOUNTER_URL"] = "https://corapan.goatcounter.com/count"

    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert html.count('data-goatcounter="https://corapan.goatcounter.com/count"') == 1
    assert html.count('src="https://gc.zgo.at/count.js"') == 1
    assert 'js/modules/core/entry.js' in html

    csp = response.headers["Content-Security-Policy"]
    assert "https://gc.zgo.at" in csp
    assert "connect-src 'self' https://corapan.goatcounter.com;" in csp
