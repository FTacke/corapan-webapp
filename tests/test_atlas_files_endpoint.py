from __future__ import annotations

import importlib
import sqlite3
from pathlib import Path

from flask import Flask

from src.app.extensions import cache


def _setup_env(monkeypatch) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    runtime_root = repo_root / "runtime" / "corapan"
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("CORAPAN_RUNTIME_ROOT", str(runtime_root))
    return runtime_root


def _reload_atlas_modules():
    import src.app.services.database as database
    import src.app.services.atlas as atlas

    database = importlib.reload(database)
    atlas = importlib.reload(atlas)
    return atlas, database


def _make_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test"
    cache.init_app(app)

    import src.app.routes.atlas as atlas_routes

    atlas_routes = importlib.reload(atlas_routes)
    app.register_blueprint(atlas_routes.blueprint)
    return app


def test_atlas_files_endpoint_returns_200(monkeypatch):
    _setup_env(monkeypatch)
    _reload_atlas_modules()

    app = _make_app()
    client = app.test_client()

    response = client.get("/api/v1/atlas/files")
    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert "files" in payload
    assert isinstance(payload["files"], list)


def test_fetch_file_metadata_missing_table_returns_empty(monkeypatch, tmp_path):
    _setup_env(monkeypatch)
    atlas, database = _reload_atlas_modules()

    temp_db = tmp_path / "stats_files.db"
    conn = sqlite3.connect(temp_db)
    conn.execute("CREATE TABLE other_table (id INTEGER)")
    conn.commit()
    conn.close()

    original_databases = dict(database.DATABASES)
    try:
        database.DATABASES["stats_files"] = temp_db
        files = atlas.fetch_file_metadata()
    finally:
        database.DATABASES.clear()
        database.DATABASES.update(original_databases)

    assert files == []
