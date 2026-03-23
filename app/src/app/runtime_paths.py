"""Central runtime path getters for canonical CO.RA.PAN environments."""

from __future__ import annotations

import logging
import os
from pathlib import Path


logger = logging.getLogger(__name__)


def is_dev_environment() -> bool:
    env_name = (os.getenv("FLASK_ENV") or os.getenv("APP_ENV") or "production").lower()
    return env_name in ("development", "dev")


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def legacy_dev_runtime_root() -> Path:
    return project_root() / "runtime" / "corapan"


def _same_path(left: Path, right: Path) -> bool:
    return left.resolve() == right.resolve()


def get_runtime_root() -> Path:
    runtime_root = os.getenv("CORAPAN_RUNTIME_ROOT")
    if not runtime_root or not runtime_root.strip():
        raise RuntimeError(
            "CORAPAN_RUNTIME_ROOT environment variable is required.\n"
            "Dev must use the canonical sibling workspace root so data resolves to <workspace>/data.\n"
            "Repo-local runtime/corapan is inactive in development."
        )

    resolved = Path(runtime_root).expanduser()
    if is_dev_environment() and _same_path(resolved, legacy_dev_runtime_root()):
        raise RuntimeError(
            "Repo-local runtime/corapan is inactive in development.\n"
            "Use the canonical sibling workspace root that contains data/ and media/."
        )
    return resolved


def get_data_root() -> Path:
    return get_runtime_root() / "data"


def get_media_root() -> Path:
    media_root = os.getenv("CORAPAN_MEDIA_ROOT")
    if not media_root or not media_root.strip():
        raise RuntimeError(
            "CORAPAN_MEDIA_ROOT environment variable is required.\n"
            "Dev must use the canonical sibling media path <workspace>/media.\n"
            "No repo-local runtime/corapan media fallback is supported."
        )

    resolved = Path(media_root).expanduser()
    legacy_media_root = legacy_dev_runtime_root() / "media"
    if is_dev_environment() and _same_path(resolved, legacy_media_root):
        raise RuntimeError(
            "Repo-local runtime/corapan/media is inactive in development.\n"
            "Use the canonical sibling media directory instead."
        )
    return resolved


def get_config_root() -> Path:
    return get_data_root() / "config"


def get_logs_dir() -> Path:
    return get_runtime_root() / "logs"


def get_stats_dir(runtime_root: Path | None = None) -> Path:
    explicit = os.getenv("PUBLIC_STATS_DIR")
    if explicit and explicit.strip():
        return Path(explicit).expanduser()
    resolved_runtime_root = runtime_root or get_runtime_root()
    return resolved_runtime_root / "data" / "public" / "statistics"


def get_stats_temp_dir(runtime_root: Path | None = None) -> Path:
    explicit = os.getenv("STATS_TEMP_DIR")
    if explicit and explicit.strip():
        return Path(explicit).expanduser()
    resolved_runtime_root = runtime_root or get_runtime_root()
    return resolved_runtime_root / "data" / "stats_temp"


def get_metadata_dir(runtime_root: Path | None = None) -> Path:
    resolved_runtime_root = runtime_root or get_runtime_root()
    return resolved_runtime_root / "data" / "public" / "metadata" / "latest"


def get_audio_full_dir() -> Path:
    return get_media_root() / "mp3-full"


def get_audio_split_dir() -> Path:
    return get_media_root() / "mp3-split"


def get_audio_temp_dir() -> Path:
    return get_media_root() / "mp3-temp"


def get_transcripts_dir() -> Path:
    return get_media_root() / "transcripts"


def get_docmeta_path(runtime_root: Path | None = None) -> Path:
    explicit = os.getenv("CORAPAN_BLACKLAB_DOCMETA_PATH")
    if explicit and explicit.strip():
        return Path(explicit).expanduser()

    resolved_runtime_root = runtime_root or get_runtime_root()
    return resolved_runtime_root / "data" / "blacklab" / "export" / "docmeta.jsonl"


def log_resolved_paths(log: logging.Logger | None = None) -> None:
    active_logger = log or logger
    runtime_root = get_runtime_root()
    active_logger.info("Resolved runtime paths: RUNTIME_ROOT=%s", runtime_root)
    active_logger.info(
        "Resolved runtime paths: DATA_ROOT=%s MEDIA_ROOT=%s CONFIG_ROOT=%s LOGS_DIR=%s METADATA_DIR=%s STATS_DIR=%s STATS_TEMP_DIR=%s DOCMETA_PATH=%s",
        get_data_root(),
        get_media_root(),
        get_config_root(),
        get_logs_dir(),
        get_metadata_dir(runtime_root),
        get_stats_dir(runtime_root),
        get_stats_temp_dir(runtime_root),
        get_docmeta_path(runtime_root),
    )


def resolve_runtime_root() -> Path:
    return get_runtime_root()


def resolve_data_root() -> Path:
    return get_data_root()


def resolve_media_root() -> Path:
    return get_media_root()


def resolve_public_stats_dir(runtime_root: Path | None = None) -> Path:
    return get_stats_dir(runtime_root)


def resolve_stats_temp_dir(runtime_root: Path | None = None) -> Path:
    return get_stats_temp_dir(runtime_root)