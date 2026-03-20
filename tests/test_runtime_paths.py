from __future__ import annotations

from pathlib import Path

from src.app import runtime_paths


def test_central_runtime_getters_resolve_canonical_paths(monkeypatch, tmp_path):
    runtime_root = tmp_path / "workspace"
    media_root = runtime_root / "media"

    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("CORAPAN_RUNTIME_ROOT", str(runtime_root))
    monkeypatch.setenv("CORAPAN_MEDIA_ROOT", str(media_root))
    monkeypatch.delenv("PUBLIC_STATS_DIR", raising=False)
    monkeypatch.delenv("STATS_TEMP_DIR", raising=False)

    assert runtime_paths.get_runtime_root() == runtime_root
    assert runtime_paths.get_data_root() == runtime_root / "data"
    assert runtime_paths.get_media_root() == media_root
    assert runtime_paths.get_config_root() == runtime_root / "config"
    assert runtime_paths.get_stats_dir() == runtime_root / "data" / "public" / "statistics"
    assert runtime_paths.get_stats_temp_dir() == runtime_root / "data" / "stats_temp"
    assert runtime_paths.get_metadata_dir() == runtime_root / "data" / "public" / "metadata" / "latest"
    assert runtime_paths.get_docmeta_path() == runtime_root / "data" / "blacklab_export" / "docmeta.jsonl"


def test_explicit_stats_env_overrides_still_use_single_source(monkeypatch, tmp_path):
    runtime_root = tmp_path / "workspace"
    media_root = runtime_root / "media"
    stats_dir = tmp_path / "stats-out"
    stats_temp_dir = tmp_path / "stats-temp"

    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("CORAPAN_RUNTIME_ROOT", str(runtime_root))
    monkeypatch.setenv("CORAPAN_MEDIA_ROOT", str(media_root))
    monkeypatch.setenv("PUBLIC_STATS_DIR", str(stats_dir))
    monkeypatch.setenv("STATS_TEMP_DIR", str(stats_temp_dir))

    assert runtime_paths.get_stats_dir() == stats_dir
    assert runtime_paths.get_stats_temp_dir() == stats_temp_dir