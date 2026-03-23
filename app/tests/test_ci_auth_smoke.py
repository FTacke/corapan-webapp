"""CI smoke tests for auth + Postgres wiring."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.skip(f"{name} not set; smoke test requires CI env")
    return value


@pytest.fixture()
def app():
    _require_env("AUTH_DATABASE_URL")
    _require_env("CORAPAN_RUNTIME_ROOT")
    from src.app import create_app

    return create_app("testing")


def test_auth_db_connection(app):
    from src.app.extensions.sqlalchemy_ext import get_engine

    engine = get_engine()
    assert engine is not None
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def test_auth_session_endpoint(app):
    with app.test_client() as client:
        resp = client.get("/auth/session")
        assert resp.status_code == 200
        payload = resp.get_json() or {}
        assert "authenticated" in payload
        assert "user" in payload
        assert "exp" in payload
