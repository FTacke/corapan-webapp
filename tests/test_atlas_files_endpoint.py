from __future__ import annotations

import importlib
import json
from pathlib import Path

from flask import Flask

from src.app.extensions import cache


def _setup_env(monkeypatch, runtime_root: Path) -> None:
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("CORAPAN_RUNTIME_ROOT", str(runtime_root))


def _reload_atlas_module():
    import src.app.services.atlas as atlas

    return importlib.reload(atlas)


def _make_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test"
    cache.init_app(app)

    import src.app.routes.atlas as atlas_routes

    atlas_routes = importlib.reload(atlas_routes)
    app.register_blueprint(atlas_routes.blueprint)
    return app


def _write_sample_metadata(metadata_dir: Path) -> None:
    metadata_dir.mkdir(parents=True, exist_ok=True)
    sample = [
        {
            "file_id": "2023-08-10_ARG_Mitre",
            "filename": "2023-08-10_ARG_Mitre.mp3",
            "date": "2023-08-10",
            "country_code_alpha3": "ARG",
            "radio": "Radio Mitre",
            "duration_seconds": 5589,
            "duration_hms": "01:33:09",
            "words_transcribed": 15023,
            "revision": "YB",
        }
    ]
    (metadata_dir / "corapan_recordings.json").write_text(
        json.dumps(sample), encoding="utf-8"
    )


def test_atlas_files_endpoint_returns_200(monkeypatch, tmp_path):
    runtime_root = tmp_path / "runtime"
    metadata_dir = runtime_root / "data" / "public" / "metadata" / "latest"
    _write_sample_metadata(metadata_dir)
    _setup_env(monkeypatch, runtime_root)
    _reload_atlas_module()

    app = _make_app()
    client = app.test_client()

    response = client.get("/api/v1/atlas/files")
    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert "files" in payload
    assert isinstance(payload["files"], list)
    assert len(payload["files"]) > 0


def test_fetch_file_metadata_reads_metadata_json(monkeypatch, tmp_path):
    runtime_root = tmp_path / "runtime"
    metadata_dir = runtime_root / "data" / "public" / "metadata" / "latest"
    _write_sample_metadata(metadata_dir)
    _setup_env(monkeypatch, runtime_root)

    atlas = _reload_atlas_module()
    files = atlas.fetch_file_metadata()

    assert len(files) == 1
    assert files[0]["filename"] == "2023-08-10_ARG_Mitre.mp3"
    assert files[0]["country_code"] == "ARG"
