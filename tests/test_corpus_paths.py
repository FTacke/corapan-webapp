from __future__ import annotations

import importlib
import json
from pathlib import Path
from unittest.mock import patch

from flask import Flask


def _setup_env(monkeypatch, runtime_root: Path, media_root: Path) -> None:
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("CORAPAN_RUNTIME_ROOT", str(runtime_root))
    monkeypatch.setenv("CORAPAN_MEDIA_ROOT", str(media_root))
    monkeypatch.setenv("BLS_BASE_URL", "http://localhost:8081/blacklab-server")
    monkeypatch.setenv("BLS_CORPUS", "corapan")
    monkeypatch.delenv("PUBLIC_STATS_DIR", raising=False)
    monkeypatch.delenv("STATS_TEMP_DIR", raising=False)


def _make_app() -> Flask:
    import src.app.routes.corpus as corpus_routes

    template_dir = Path(__file__).resolve().parents[1] / "templates"
    app = Flask(__name__, template_folder=str(template_dir))
    app.config.update(TESTING=True, SECRET_KEY="test")

    corpus_routes = importlib.reload(corpus_routes)
    app.register_blueprint(corpus_routes.blueprint)
    return app


def _write_metadata(runtime_root: Path) -> None:
    metadata_dir = runtime_root / "data" / "public" / "metadata" / "latest"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "file_id": "2023-08-10_ARG_Mitre",
            "filename": "2023-08-10_ARG_Mitre.mp3",
            "country_code_alpha3": "ARG",
        }
    ]
    (metadata_dir / "corapan_recordings.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _write_stats(runtime_root: Path) -> None:
    stats_dir = runtime_root / "data" / "public" / "statistics"
    stats_dir.mkdir(parents=True, exist_ok=True)
    (stats_dir / "corpus_stats.json").write_text(
        json.dumps({"total_word_count": 123}), encoding="utf-8"
    )


def test_metadata_page_renders(monkeypatch, tmp_path):
    runtime_root = tmp_path / "workspace"
    media_root = runtime_root / "media"
    _setup_env(monkeypatch, runtime_root, media_root)

    app = _make_app()
    client = app.test_client()

    with patch("src.app.routes.corpus.render_template", return_value="ok"):
        response = client.get("/corpus/metadata")
    assert response.status_code == 200


def test_metadata_download_uses_canonical_latest_dir(monkeypatch, tmp_path):
    runtime_root = tmp_path / "workspace"
    media_root = runtime_root / "media"
    _setup_env(monkeypatch, runtime_root, media_root)
    _write_metadata(runtime_root)

    app = _make_app()
    client = app.test_client()

    response = client.get("/corpus/metadata/download/json")
    assert response.status_code == 200
    assert response.get_json()[0]["file_id"] == "2023-08-10_ARG_Mitre"


def test_statistics_route_uses_canonical_stats_dir(monkeypatch, tmp_path):
    runtime_root = tmp_path / "workspace"
    media_root = runtime_root / "media"
    _setup_env(monkeypatch, runtime_root, media_root)
    _write_stats(runtime_root)

    app = _make_app()
    client = app.test_client()

    response = client.get("/corpus/api/statistics/corpus_stats.json")
    assert response.status_code == 200
    payload = response.get_data(as_text=True)
    assert '"total_word_count"' in payload
    assert "123" in payload