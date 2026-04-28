"""Configuration module for CO.RA.PAN application."""

from __future__ import annotations

import os
import warnings
import sys
import logging
from pathlib import Path
from typing import Mapping

from ..runtime_paths import (
    get_audio_full_dir,
    get_audio_split_dir,
    get_audio_temp_dir,
    get_config_root,
    get_data_root,
    get_media_root,
    get_metadata_dir,
    get_runtime_root,
    get_stats_dir,
    get_stats_temp_dir,
    get_transcripts_dir,
    log_resolved_paths,
)

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
DEFAULT_APP_REPOSITORY_URL = "https://github.com/FTacke/corapan-webapp"

# Sentinel value to detect missing SECRET_KEY
DEFAULT_SECRET_SENTINEL = "___SENTINEL_CHANGE_ME___"


def _require_config_value(name: str, value: str | None, message: str) -> str:
    """Validate a required config value after the config object is loaded."""
    if value is None:
        raise RuntimeError(message)
    if isinstance(value, str) and not value.strip():
        raise RuntimeError(message)
    return value.strip() if isinstance(value, str) else value


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


def _normalize_app_version(value: str | None) -> str:
    """Normalize APP_VERSION to a plain semantic version string."""
    if value is None:
        return ""

    normalized = value.strip()
    if not normalized:
        return ""

    if normalized.lower().startswith("v"):
        normalized = normalized[1:].strip()

    return normalized


def _normalize_release_tag(value: str | None) -> str:
    """Normalize APP_RELEASE_TAG to the canonical v-prefixed tag format."""
    normalized_version = _normalize_app_version(value)
    if not normalized_version:
        return ""
    return f"v{normalized_version}"


def _normalize_repository_url(value: str | None) -> str:
    """Return a normalized repository URL without a trailing .git suffix."""
    normalized = (value or DEFAULT_APP_REPOSITORY_URL).strip() or DEFAULT_APP_REPOSITORY_URL
    normalized = normalized.rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    return normalized


def resolve_app_release_metadata(
    env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Resolve normalized release metadata from environment."""
    source = env or os.environ
    repository_url = _normalize_repository_url(source.get("APP_REPOSITORY_URL"))
    app_release_tag = _normalize_release_tag(
        source.get("APP_RELEASE_TAG") or source.get("APP_VERSION")
    )
    app_version = _normalize_app_version(source.get("APP_VERSION") or app_release_tag)
    app_release_url = (source.get("APP_RELEASE_URL") or "").strip()
    if app_release_tag:
        app_release_url = f"{repository_url}/releases/tag/{app_release_tag}"

    return {
        "app_version": app_version,
        "app_repository_url": repository_url,
        "app_release_tag": app_release_tag,
        "app_release_url": app_release_url,
    }


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
    _is_testing = _env_name in ("testing", "test")
    _runtime_root = get_runtime_root()

    # BlackLab configuration
    BLS_BASE_URL = os.getenv(
        "BLS_BASE_URL", "http://localhost:8081/blacklab-server"
    ).rstrip("/")
    BLS_CORPUS = os.getenv("BLS_CORPUS", "")

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
    RUNTIME_ROOT = _runtime_root
    DATA_ROOT = get_data_root()
    CONFIG_ROOT = get_config_root()
    METADATA_DIR = get_metadata_dir(_runtime_root)

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
    MEDIA_ROOT = get_media_root()

    TRANSCRIPTS_DIR = get_transcripts_dir()
    AUDIO_FULL_DIR = get_audio_full_dir()
    AUDIO_SPLIT_DIR = get_audio_split_dir()
    AUDIO_TEMP_DIR = get_audio_temp_dir()

    # Public statistics directory (RUNTIME-ONLY)
    # Statistics are runtime data generated by 05_publish_corpus_statistics.py
    # Must be explicitly configured via environment variables
    _explicit_stats_dir = os.getenv("PUBLIC_STATS_DIR")

    if _explicit_stats_dir:
        PUBLIC_STATS_DIR = Path(_explicit_stats_dir)
    else:
        PUBLIC_STATS_DIR = get_stats_dir(_runtime_root)

    _explicit_stats_temp_dir = os.getenv("STATS_TEMP_DIR")
    if _explicit_stats_temp_dir:
        STATS_TEMP_DIR = Path(_explicit_stats_temp_dir)
    else:
        STATS_TEMP_DIR = get_stats_temp_dir(_runtime_root)

    try:
        PUBLIC_STATS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        logger.warning(
            "Failed to create PUBLIC_STATS_DIR at %s: %s", PUBLIC_STATS_DIR, exc
        )

    try:
        STATS_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        logger.warning("Failed to create STATS_TEMP_DIR at %s: %s", STATS_TEMP_DIR, exc)

    _stats_file = PUBLIC_STATS_DIR / "corpus_stats.json"
    if not _is_testing and "pytest" not in sys.modules and not _stats_file.exists():
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

    # Optional third-party pageview tracking. Disabled by default in dev/test
    # unless explicitly configured via environment.
    GOATCOUNTER_URL = (os.getenv("GOATCOUNTER_URL") or "").strip()

    # Auth DB - Must be explicitly configured via AUTH_DATABASE_URL env var
    # No fallback to SQLite - dev must use Postgres from docker-compose.dev-postgres.yml
    # Production sets this via environment/secrets
    AUTH_DATABASE_URL = os.getenv("AUTH_DATABASE_URL", "")

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


class TestingConfig(DevConfig):
    """Testing configuration used by CI smoke tests and app factory tests."""

    TESTING = True
    SESSION_COOKIE_SECURE = False
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False


CONFIG_MAPPING = {
    "development": DevConfig,
    "testing": TestingConfig,
    "production": BaseConfig,
}


def load_config(app, env_name: str | None) -> None:
    """Load a configuration object based on the environment name."""
    env = env_name or os.getenv("FLASK_ENV", "production").lower()
    config_obj = CONFIG_MAPPING.get(env, BaseConfig)
    app.config.from_object(config_obj)

    release_metadata = resolve_app_release_metadata()
    app.config["APP_VERSION"] = release_metadata["app_version"]
    app.config["APP_REPOSITORY_URL"] = release_metadata["app_repository_url"]
    app.config["APP_RELEASE_TAG"] = release_metadata["app_release_tag"]
    app.config["APP_RELEASE_URL"] = release_metadata["app_release_url"]

    app.config["BLS_CORPUS"] = _require_config_value(
        "BLS_CORPUS",
        app.config.get("BLS_CORPUS"),
        "BLS_CORPUS environment variable is required. "
        "For the canonical dev stack, set BLS_CORPUS=corapan.",
    )
    app.config["AUTH_DATABASE_URL"] = _require_config_value(
        "AUTH_DATABASE_URL",
        app.config.get("AUTH_DATABASE_URL"),
        "AUTH_DATABASE_URL environment variable is required.\n"
        "For development: Start Postgres with 'docker compose -f docker-compose.dev-postgres.yml up -d'\n"
        "Then set: AUTH_DATABASE_URL=postgresql+psycopg2://corapan_auth:corapan_auth@localhost:54320/corapan_auth",
    )

    log_resolved_paths(app.logger)

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
        "Data config: DATA_ROOT=%s CONFIG_ROOT=%s METADATA_DIR=%s PUBLIC_STATS_DIR=%s STATS_TEMP_DIR=%s",
        app.config.get("DATA_ROOT"),
        app.config.get("CONFIG_ROOT"),
        app.config.get("METADATA_DIR"),
        app.config.get("PUBLIC_STATS_DIR"),
        app.config.get("STATS_TEMP_DIR"),
    )

    app.logger.info(
        "BlackLab config: BLS_BASE_URL=%s BLS_CORPUS=%s",
        app.config.get("BLS_BASE_URL"),
        app.config.get("BLS_CORPUS"),
    )

    app.logger.info(
        "Release config: APP_VERSION=%s APP_RELEASE_URL=%s",
        app.config.get("APP_VERSION") or "<unset>",
        app.config.get("APP_RELEASE_URL") or "<unset>",
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
    "resolve_app_release_metadata",
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
