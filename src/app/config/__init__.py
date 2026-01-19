"""Configuration module for CO.RA.PAN application."""

from __future__ import annotations

import os
import warnings
import logging
from pathlib import Path

# Re-export from countries module
from .countries import (
    LOCATIONS,
    Location,
    code_to_name,
    export_all_to_json,
    get_all_locations,
    get_country_name,
    get_location,
    get_locations_by_country,
    get_national_capitals,
    get_regional_capitals,
    is_national_capital,
    is_regional_capital,
    name_to_code,
    normalize_country_code,
)

logger = logging.getLogger(__name__)

# Sentinel value to detect missing SECRET_KEY
DEFAULT_SECRET_SENTINEL = "___SENTINEL_CHANGE_ME___"


def _ensure_stats_permissions(path: Path) -> None:
    """Best-effort chmod to keep statistics assets world-readable."""
    try:
        if path.is_dir():
            path.chmod(0o755)
            for child in path.iterdir():
                if child.is_file():
                    child.chmod(0o644)
        elif path.is_file():
            path.chmod(0o644)
            if path.parent.exists():
                path.parent.chmod(0o755)
    except Exception as exc:
        warnings.warn(
            f"Failed to adjust statistics permissions for {path}: {exc}",
            RuntimeWarning,
        )

# Note: passwords.env support (env-based auth) is deprecated and has been
# removed from automatic loading. Operator-managed secrets should be provided
# directly as environment variables or via the auth database.


class BaseConfig:
    """Base configuration (Production defaults)."""

    # Project paths
    PROJECT_ROOT = Path(__file__).resolve().parents[3]

    # Environment
    _env_name = (os.getenv("FLASK_ENV") or os.getenv("APP_ENV") or "production").lower()
    _is_dev = _env_name in ("development", "dev")
    _runtime_root = os.getenv("CORAPAN_RUNTIME_ROOT")

    # BlackLab configuration
    BLS_BASE_URL = os.getenv(
        "BLS_BASE_URL", "http://localhost:8081/blacklab-server"
    ).rstrip("/")
    BLS_CORPUS = (os.getenv("BLS_CORPUS", "index") or "index").strip() or "index"

    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", DEFAULT_SECRET_SENTINEL)
    SESSION_COOKIE_SECURE = os.getenv("FLASK_SESSION_SECURE", "true").lower() == "true"
    SESSION_COOKIE_SAMESITE = os.getenv("FLASK_SESSION_SAMESITE", "lax")
    SESSION_COOKIE_HTTPONLY = True

    # JWT
    # Prefer JWT_SECRET_KEY; fallback to legacy JWT_SECRET for backwards compatibility
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        os.getenv("JWT_SECRET", os.getenv("FLASK_SECRET_KEY", DEFAULT_SECRET_SENTINEL)),
    )
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SECURE = SESSION_COOKIE_SECURE
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_COOKIE_SAMESITE = "Lax"  # Allows cookies in redirects
    # Token lifetimes (seconds)
    ACCESS_TOKEN_EXP = int(
        os.getenv("ACCESS_TOKEN_EXP", os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))
    )
    REFRESH_TOKEN_EXP = int(
        os.getenv("REFRESH_TOKEN_EXP", os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "604800"))
    )
    # Ensure cookies are sent with all requests (not just /auth)
    JWT_ACCESS_COOKIE_PATH = "/"
    JWT_REFRESH_COOKIE_PATH = "/"
    JWT_ACCESS_CSRF_COOKIE_PATH = "/"
    JWT_REFRESH_CSRF_COOKIE_PATH = "/"

    # Runtime data root (non-BlackLab)
    if _runtime_root:
        DATA_ROOT = Path(_runtime_root) / "data"
    elif _is_dev:
        DATA_ROOT = PROJECT_ROOT / "runtime" / "corapan" / "data"
        warnings.warn(
            "CORAPAN_RUNTIME_ROOT not configured. Defaulting to repo-local runtime path for development: "
            f"{DATA_ROOT}",
            RuntimeWarning,
        )
    else:
        raise RuntimeError(
            "CORAPAN_RUNTIME_ROOT environment variable not configured.\n"
            "Runtime data is required for database and metadata paths.\n\n"
            "Options:\n"
            "  1. Set CORAPAN_RUNTIME_ROOT (preferred):\n"
            "     export CORAPAN_RUNTIME_ROOT=/runtime/path\n"
            "     # Then data paths resolve to ${CORAPAN_RUNTIME_ROOT}/data\n"
        )

    # Database paths
    # NOTE: This directory contains runtime DBs such as stats DBs.
    # Corpus data is served via BlackLab indexes (no transcription.db).
    DB_DIR = DATA_ROOT / "db"
    PUBLIC_DB_DIR = DATA_ROOT / "db" / "public"

    # Dev Postgres data directory (host path for docker volume)
    _explicit_postgres_dev_dir = os.getenv("POSTGRES_DEV_DATA_DIR")
    if _explicit_postgres_dev_dir:
        POSTGRES_DEV_DATA_DIR = Path(_explicit_postgres_dev_dir)
    else:
        POSTGRES_DEV_DATA_DIR = DATA_ROOT / "db" / "restricted" / "postgres_dev"

    # Media paths (runtime-configured, REQUIRED - no repo fallbacks)
    _explicit_media_root = os.getenv("CORAPAN_MEDIA_ROOT")
    
    if not _explicit_media_root:
        raise RuntimeError(
            "CORAPAN_MEDIA_ROOT environment variable is required.\n"
            "Media storage is mandatory for audio/transcripts paths.\n\n"
            "Setup:\n"
            "  - Dev: Run via scripts/dev-start.ps1 (auto-sets CORAPAN_MEDIA_ROOT)\n"
            "  - Production: export CORAPAN_MEDIA_ROOT=/path/to/runtime/media\n\n"
            "No fallbacks to repo media paths are supported."
        )
    
    MEDIA_ROOT = Path(_explicit_media_root)

    TRANSCRIPTS_DIR = MEDIA_ROOT / "transcripts"
    AUDIO_FULL_DIR = MEDIA_ROOT / "mp3-full"
    AUDIO_SPLIT_DIR = MEDIA_ROOT / "mp3-split"
    AUDIO_TEMP_DIR = MEDIA_ROOT / "mp3-temp"

    # Public statistics directory (RUNTIME-ONLY)
    # Statistics are runtime data generated by 05_publish_corpus_statistics.py
    # Must be explicitly configured via environment variables
    _explicit_stats_dir = os.getenv("PUBLIC_STATS_DIR")

    if _explicit_stats_dir:
        # Explicit path takes priority
        PUBLIC_STATS_DIR = Path(_explicit_stats_dir)
    elif _runtime_root:
        # Derive from runtime root
        PUBLIC_STATS_DIR = Path(_runtime_root) / "data" / "public" / "statistics"
    elif _is_dev:
        # Dev fallback: repo-local runtime
        PUBLIC_STATS_DIR = (
            PROJECT_ROOT / "runtime" / "corapan" / "data" / "public" / "statistics"
        )
        warnings.warn(
            "PUBLIC_STATS_DIR not configured. Defaulting to repo-local runtime path for development: "
            f"{PUBLIC_STATS_DIR}",
            RuntimeWarning,
        )
    else:
        # Neither env var set - fall back to repo-local runtime (non-fatal)
        PUBLIC_STATS_DIR = (
            PROJECT_ROOT / "runtime" / "corapan" / "data" / "public" / "statistics"
        )
        logger.warning(
            "PUBLIC_STATS_DIR not configured. Falling back to repo-local runtime path: %s",
            PUBLIC_STATS_DIR,
        )

    _explicit_stats_temp_dir = os.getenv("STATS_TEMP_DIR")
    if _explicit_stats_temp_dir:
        STATS_TEMP_DIR = Path(_explicit_stats_temp_dir)
    elif _runtime_root:
        STATS_TEMP_DIR = Path(_runtime_root) / "data" / "stats_temp"
    elif _is_dev:
        STATS_TEMP_DIR = PROJECT_ROOT / "runtime" / "corapan" / "data" / "stats_temp"
    else:
        STATS_TEMP_DIR = PROJECT_ROOT / "runtime" / "corapan" / "data" / "stats_temp"
        logger.warning(
            "STATS_TEMP_DIR not configured. Falling back to repo-local runtime path: %s",
            STATS_TEMP_DIR,
        )

    try:
        PUBLIC_STATS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        logger.warning("Failed to create PUBLIC_STATS_DIR at %s: %s", PUBLIC_STATS_DIR, exc)

    try:
        STATS_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        logger.warning("Failed to create STATS_TEMP_DIR at %s: %s", STATS_TEMP_DIR, exc)

    _stats_file = PUBLIC_STATS_DIR / "corpus_stats.json"
    if not _stats_file.exists():
        warnings.warn(
            "Statistics not generated yet; stats endpoints will return 404 until corpus_stats.json exists. "
            f"Expected: {_stats_file}",
            RuntimeWarning,
        )

    _ensure_stats_permissions(PUBLIC_STATS_DIR)

    # Feature flags
    ALLOW_PUBLIC_TEMP_AUDIO = (
        os.getenv("ALLOW_PUBLIC_TEMP_AUDIO", "false").lower() == "true"
    )
    ALLOW_PUBLIC_FULL_AUDIO = (
        os.getenv("ALLOW_PUBLIC_FULL_AUDIO", "false").lower() == "true"
    )
    ALLOW_PUBLIC_TRANSCRIPTS = (
        os.getenv("ALLOW_PUBLIC_TRANSCRIPTS", "false").lower() == "true"
    )

# Auth DB - Must be explicitly configured via AUTH_DATABASE_URL env var
    # No fallback to SQLite - dev must use Postgres from docker-compose.dev-postgres.yml
    # Production sets this via environment/secrets
    AUTH_DATABASE_URL = os.getenv("AUTH_DATABASE_URL")
    if not AUTH_DATABASE_URL:
        raise RuntimeError(
            "AUTH_DATABASE_URL environment variable is required.\n"
            "For development: Start Postgres with 'docker compose -f docker-compose.dev-postgres.yml up -d'\n"
            "Then set: AUTH_DATABASE_URL=postgresql+psycopg2://corapan_auth:corapan_auth@localhost:54320/corapan_auth"
        )

    # Hashing (argon2 or bcrypt)
    AUTH_HASH_ALGO = os.getenv("AUTH_HASH_ALGO", "argon2")
    # Argon2 defaults - these may be tuned for infra but sensible defaults applied
    AUTH_ARGON2_TIME_COST = int(os.getenv("AUTH_ARGON2_TIME_COST", "2"))
    AUTH_ARGON2_MEMORY_COST = int(os.getenv("AUTH_ARGON2_MEMORY_COST", "102400"))
    AUTH_ARGON2_PARALLELISM = int(os.getenv("AUTH_ARGON2_PARALLELISM", "4"))

    # Account deletion/anonymization retention (days)
    # Users marked as deleted will be anonymized after this many days.
    AUTH_ACCOUNT_ANONYMIZE_AFTER_DAYS = int(
        os.getenv("AUTH_ACCOUNT_ANONYMIZE_AFTER_DAYS", "30")
    )

    # Debug
    DEBUG = False
    TESTING = False


class DevConfig(BaseConfig):
    """Development configuration."""

    DEBUG = True
    SESSION_COOKIE_SECURE = False
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False

    # Template auto-reload for development
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0


CONFIG_MAPPING = {
    "development": DevConfig,
    "production": BaseConfig,
}


def load_config(app, env_name: str | None) -> None:
    """Load a configuration object based on the environment name."""
    env = env_name or os.getenv("FLASK_ENV", "production").lower()
    config_obj = CONFIG_MAPPING.get(env, BaseConfig)
    app.config.from_object(config_obj)

    app.logger.info(
        "Media config: CORAPAN_MEDIA_ROOT=%s MEDIA_ROOT=%s AUDIO_FULL_DIR=%s AUDIO_SPLIT_DIR=%s AUDIO_TEMP_DIR=%s TRANSCRIPTS_DIR=%s",
        os.getenv("CORAPAN_MEDIA_ROOT"),
        app.config.get("MEDIA_ROOT"),
        app.config.get("AUDIO_FULL_DIR"),
        app.config.get("AUDIO_SPLIT_DIR"),
        app.config.get("AUDIO_TEMP_DIR"),
        app.config.get("TRANSCRIPTS_DIR"),
    )

    app.logger.info(
        "BlackLab config: BLS_BASE_URL=%s BLS_CORPUS=%s",
        app.config.get("BLS_BASE_URL"),
        app.config.get("BLS_CORPUS"),
    )

    # We now assume the auth system is DB-backed. Legacy env-based auth (passwords.env)
    # support is deprecated and not automatically enabled by configuration.

    if app.config["SECRET_KEY"] == DEFAULT_SECRET_SENTINEL:
        raise RuntimeError(
            "FLASK_SECRET_KEY must be provided via environment variable."
        )


__all__ = [
    "load_config",
    "BaseConfig",
    "DevConfig",
    "Location",
    "LOCATIONS",
    "normalize_country_code",
    "get_location",
    "code_to_name",
    "name_to_code",
    "get_all_locations",
    "get_national_capitals",
    "get_regional_capitals",
    "get_locations_by_country",
    "get_country_name",
    "is_national_capital",
    "is_regional_capital",
    "export_all_to_json",
]
