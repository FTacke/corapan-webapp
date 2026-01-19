"""Trace runtime data paths without secrets.

Usage:
  python scripts/trace_runtime_paths.py

The script prints resolved runtime paths based on environment variables and
repo-local fallbacks used in code. It does not print credentials.
"""

from __future__ import annotations

import os
from pathlib import Path


def _env(name: str) -> str | None:
    value = os.getenv(name)
    return value if value else None


def _is_dev() -> bool:
    env = (os.getenv("FLASK_ENV") or os.getenv("APP_ENV") or "production").lower()
    return env in ("development", "dev")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_runtime_root() -> Path | None:
    runtime_root = _env("CORAPAN_RUNTIME_ROOT")
    if runtime_root:
        return Path(runtime_root)
    if _is_dev():
        return _repo_root() / "runtime" / "corapan"
    return None


def _resolve_public_stats_dir(runtime_root: Path | None) -> Path | None:
    explicit = _env("PUBLIC_STATS_DIR")
    if explicit:
        return Path(explicit)
    if runtime_root:
        return runtime_root / "data" / "public" / "statistics"
    if _is_dev():
        return _repo_root() / "runtime" / "corapan" / "data" / "public" / "statistics"
    return None


def _print_path(label: str, path: Path | None, public: bool | None = None) -> None:
    if path is None:
        print(f"- {label}: <missing>")
        return
    flag = ""
    if public is True:
        flag = " (public)"
    elif public is False:
        flag = " (restricted)"
    exists = "OK" if path.exists() else "MISSING"
    print(f"- {label}:{flag} {path} [{exists}]")


def main() -> None:
    print("Runtime path trace (no secrets)")
    print(f"- FLASK_ENV/APP_ENV: {os.getenv('FLASK_ENV') or os.getenv('APP_ENV') or 'production'}")

    runtime_root = _resolve_runtime_root()
    media_root = _env("CORAPAN_MEDIA_ROOT")

    _print_path("CORAPAN_RUNTIME_ROOT", runtime_root)
    _print_path("CORAPAN_MEDIA_ROOT", Path(media_root) if media_root else None, public=False)

    if runtime_root:
        data_root = runtime_root / "data"
        _print_path("DATA_ROOT", data_root)
        _print_path("PUBLIC_DB_DIR", data_root / "db" / "public", public=True)
        _print_path("DB_RESTRICTED_DIR", data_root / "db" / "restricted", public=False)
        _print_path("PUBLIC_METADATA_ROOT", data_root / "public" / "metadata", public=True)
        _print_path("PUBLIC_METADATA_LATEST", data_root / "public" / "metadata" / "latest", public=True)
        _print_path("PUBLIC_STATS_DIR", _resolve_public_stats_dir(runtime_root), public=True)
        _print_path("STATS_FILES_DB", data_root / "db" / "public" / "stats_files.db", public=True)
        _print_path("STATS_COUNTRY_DB", data_root / "db" / "public" / "stats_country.db", public=True)
        _print_path("POSTGRES_DEV_DATA_DIR", Path(_env("POSTGRES_DEV_DATA_DIR")) if _env("POSTGRES_DEV_DATA_DIR") else data_root / "db" / "restricted" / "postgres_dev", public=False)

    if media_root:
        media_root_path = Path(media_root)
        _print_path("MEDIA_ROOT", media_root_path, public=False)
        _print_path("TRANSCRIPTS_DIR", media_root_path / "transcripts", public=False)
        _print_path("AUDIO_FULL_DIR", media_root_path / "mp3-full", public=False)
        _print_path("AUDIO_SPLIT_DIR", media_root_path / "mp3-split", public=False)
        _print_path("AUDIO_TEMP_DIR", media_root_path / "mp3-temp", public=False)

    print("- AUTH_DATABASE_URL: <redacted>" if _env("AUTH_DATABASE_URL") else "- AUTH_DATABASE_URL: <missing>")


if __name__ == "__main__":
    main()
