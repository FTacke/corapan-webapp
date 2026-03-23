from __future__ import annotations

import importlib
import subprocess
from pathlib import Path

import imageio_ffmpeg
from flask import Flask


def _set_required_env(monkeypatch, runtime_root: Path, media_root: Path) -> None:
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("CORAPAN_RUNTIME_ROOT", str(runtime_root))
    monkeypatch.setenv("CORAPAN_MEDIA_ROOT", str(media_root))
    monkeypatch.setenv("BLS_BASE_URL", "http://localhost:8081/blacklab-server")
    monkeypatch.setenv("BLS_CORPUS", "corapan")
    monkeypatch.setenv(
        "AUTH_DATABASE_URL",
        "postgresql+psycopg2://corapan_auth:corapan_auth@127.0.0.1:54320/corapan_auth",
    )


def _create_sample_mp3(target_path: Path, duration_seconds: float = 12.0) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        imageio_ffmpeg.get_ffmpeg_exe(),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={duration_seconds}",
        "-q:a",
        "4",
        str(target_path),
    ]
    subprocess.run(command, capture_output=True, text=True, check=True)


def _prepare_audio_tree(media_root: Path) -> str:
    filename = "2025-11-17_DOM_Test.mp3"
    _create_sample_mp3(media_root / "mp3-full" / "DOM" / filename)
    _create_sample_mp3(media_root / "mp3-split" / "DOM" / "2025-11-17_DOM_Test_01.mp3")
    (media_root / "mp3-temp").mkdir(parents=True, exist_ok=True)
    return filename


def _make_app(monkeypatch, tmp_path: Path) -> tuple[Flask, Path, object, object]:
    runtime_root = tmp_path / "workspace"
    media_root = runtime_root / "media"
    _set_required_env(monkeypatch, runtime_root, media_root)

    import src.app.services.audio_snippets as audio_snippets
    import src.app.services.media_store as media_store
    import src.app.routes.media as media_routes

    audio_snippets = importlib.reload(audio_snippets)
    media_store = importlib.reload(media_store)
    media_routes = importlib.reload(media_routes)

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
    app.register_blueprint(media_routes.blueprint)
    return app, media_root, audio_snippets, media_routes


def test_build_snippet_supports_nested_country_paths(monkeypatch, tmp_path):
    app, media_root, audio_snippets, _ = _make_app(monkeypatch, tmp_path)
    filename = _prepare_audio_tree(media_root)

    original_which = audio_snippets.shutil.which
    audio_snippets._resolve_ffmpeg_executable.cache_clear()
    monkeypatch.setattr(audio_snippets.shutil, "which", lambda _: None)

    with app.app_context():
        snippet_path = audio_snippets.build_snippet(
            f"DOM/{filename}",
            2.0,
            3.5,
            token_id="dom_demo",
            snippet_type="ctx",
        )

    audio_snippets._resolve_ffmpeg_executable.cache_clear()
    monkeypatch.setattr(audio_snippets.shutil, "which", original_which)

    assert snippet_path.exists()
    assert snippet_path.name == "corapan_dom_demo_ctx.mp3"
    assert snippet_path.parent == media_root / "mp3-temp"
    assert snippet_path.stat().st_size > 0


def test_play_audio_route_returns_audio_for_nested_country_path(monkeypatch, tmp_path):
    app, media_root, audio_snippets, _ = _make_app(monkeypatch, tmp_path)
    filename = _prepare_audio_tree(media_root)

    original_which = audio_snippets.shutil.which
    audio_snippets._resolve_ffmpeg_executable.cache_clear()
    monkeypatch.setattr(audio_snippets.shutil, "which", lambda _: None)

    client = app.test_client()
    response = client.get(
        f"/media/play_audio/DOM/{filename}?start=2.0&end=3.5&token_id=dom_demo&type=ctx"
    )

    audio_snippets._resolve_ffmpeg_executable.cache_clear()
    monkeypatch.setattr(audio_snippets.shutil, "which", original_which)

    assert response.status_code == 200
    assert response.mimetype == "audio/mpeg"
    assert (media_root / "mp3-temp" / "corapan_dom_demo_ctx.mp3").exists()


def test_play_audio_route_returns_503_when_ffmpeg_backend_missing(monkeypatch, tmp_path):
    app, media_root, audio_snippets, _ = _make_app(monkeypatch, tmp_path)
    filename = _prepare_audio_tree(media_root)

    audio_snippets._resolve_ffmpeg_executable.cache_clear()
    monkeypatch.setattr(audio_snippets, "_resolve_ffmpeg_executable", lambda: None)

    client = app.test_client()
    response = client.get(
        f"/media/play_audio/DOM/{filename}?start=2.0&end=3.5&token_id=dom_demo&type=ctx"
    )

    assert response.status_code == 503
    assert b"Audio snippet backend unavailable" in response.data
