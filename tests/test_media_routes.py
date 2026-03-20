from __future__ import annotations

import importlib
import json
from pathlib import Path

from flask import Flask


def _setup_env(monkeypatch, runtime_root: Path, media_root: Path) -> None:
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("CORAPAN_RUNTIME_ROOT", str(runtime_root))
    monkeypatch.setenv("CORAPAN_MEDIA_ROOT", str(media_root))
    monkeypatch.setenv("BLS_BASE_URL", "http://localhost:8081/blacklab-server")
    monkeypatch.setenv("BLS_CORPUS", "corapan")


def _write_sample_media(media_root: Path) -> tuple[str, bytes, dict[str, object]]:
    audio_filename = "2023-08-10_ARG_Mitre.mp3"
    transcript_filename = "2023-08-10_ARG_Mitre.json"
    audio_bytes = b"ID3test-audio"
    transcript_payload = {"country": "ARG", "segments": [{"text": "hola"}]}

    audio_path = media_root / "mp3-full" / "ARG" / audio_filename
    transcript_path = media_root / "transcripts" / "ARG" / transcript_filename
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    transcript_path.parent.mkdir(parents=True, exist_ok=True)

    audio_path.write_bytes(audio_bytes)
    transcript_path.write_text(json.dumps(transcript_payload), encoding="utf-8")

    return audio_filename, audio_bytes, transcript_payload


def _make_app(media_root: Path) -> Flask:
    import src.app.routes.media as media_routes

    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY="test",
        ALLOW_PUBLIC_FULL_AUDIO=True,
        ALLOW_PUBLIC_TRANSCRIPTS=True,
        MEDIA_ROOT=media_root,
        AUDIO_FULL_DIR=media_root / "mp3-full",
        AUDIO_SPLIT_DIR=media_root / "mp3-split",
        AUDIO_TEMP_DIR=media_root / "mp3-temp",
        TRANSCRIPTS_DIR=media_root / "transcripts",
    )

    media_routes = importlib.reload(media_routes)
    app.register_blueprint(media_routes.blueprint)
    return app


def test_media_full_route_resolves_flat_and_nested_paths(monkeypatch, tmp_path):
    runtime_root = tmp_path / "workspace"
    media_root = runtime_root / "media"
    _setup_env(monkeypatch, runtime_root, media_root)
    audio_filename, audio_bytes, _ = _write_sample_media(media_root)

    app = _make_app(media_root)
    client = app.test_client()

    for url in (
        f"/media/full/{audio_filename}",
        f"/media/full/ARG/{audio_filename}",
    ):
        response = client.get(url)
        assert response.status_code == 200
        assert response.data == audio_bytes
        assert response.mimetype == "audio/mpeg"


def test_transcript_route_resolves_flat_and_nested_paths(monkeypatch, tmp_path):
    runtime_root = tmp_path / "workspace"
    media_root = runtime_root / "media"
    _setup_env(monkeypatch, runtime_root, media_root)
    audio_filename, _, transcript_payload = _write_sample_media(media_root)
    transcript_filename = audio_filename.replace(".mp3", ".json")

    app = _make_app(media_root)
    client = app.test_client()

    for url in (
        f"/media/transcripts/{transcript_filename}",
        f"/media/transcripts/ARG/{transcript_filename}",
    ):
        response = client.get(url)
        assert response.status_code == 200
        assert response.mimetype == "application/json"
        payload = response.get_json()
        assert payload["country"] == transcript_payload["country"]
        assert payload["segments"] == transcript_payload["segments"]
        assert payload["country_display"]