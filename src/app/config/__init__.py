"""Configuration module for CO.RA.PAN application."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

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

# Sentinel value to detect missing SECRET_KEY
DEFAULT_SECRET_SENTINEL = "___SENTINEL_CHANGE_ME___"

# Note: passwords.env support (env-based auth) is deprecated and has been
# removed from automatic loading. Operator-managed secrets should be provided
# directly as environment variables or via the auth database.


class BaseConfig:
    """Base configuration (Production defaults)."""

    # Project paths
    PROJECT_ROOT = Path(__file__).resolve().parents[3]

    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", DEFAULT_SECRET_SENTINEL)
    SESSION_COOKIE_SECURE = os.getenv("FLASK_SESSION_SECURE", "true").lower() == "true"
    SESSION_COOKIE_SAMESITE = os.getenv("FLASK_SESSION_SAMESITE", "lax")
    SESSION_COOKIE_HTTPONLY = True

    # JWT
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET", os.getenv("FLASK_SECRET_KEY", DEFAULT_SECRET_SENTINEL)
    )
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SECURE = SESSION_COOKIE_SECURE
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_COOKIE_SAMESITE = "Lax"  # Allows cookies in redirects
    # Token lifetimes (seconds)
    ACCESS_TOKEN_EXP = int(os.getenv("ACCESS_TOKEN_EXP", os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600")))
    REFRESH_TOKEN_EXP = int(os.getenv("REFRESH_TOKEN_EXP", os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "604800")))
    # Ensure cookies are sent with all requests (not just /auth)
    JWT_ACCESS_COOKIE_PATH = "/"
    JWT_REFRESH_COOKIE_PATH = "/"
    JWT_ACCESS_CSRF_COOKIE_PATH = "/"
    JWT_REFRESH_CSRF_COOKIE_PATH = "/"

    # Database paths
    # NOTE: This directory contains runtime DBs such as auth.db and stats DBs.
    # Historically `transcription.db` lived under this directory; the corpus/sqlite
    # transcription DB is deprecated in the modern pipeline (BlackLab + indexes)
    # and should not be required for Variant A (dev) runs. Use EXPECT_TRANSCRIPTION_DB
    # config to opt-in/opt-out of expecting a transcription DB at startup.
    DB_DIR = PROJECT_ROOT / "data" / "db"
    DB_PUBLIC_DIR = PROJECT_ROOT / "data" / "db_public"

    # Media paths
    MEDIA_DIR = PROJECT_ROOT / "media"
    TRANSCRIPTS_DIR = MEDIA_DIR / "transcripts"
    AUDIO_FULL_DIR = MEDIA_DIR / "mp3-full"
    AUDIO_SPLIT_DIR = MEDIA_DIR / "mp3-split"
    AUDIO_TEMP_DIR = MEDIA_DIR / "mp3-temp"

    # Feature flags
    ALLOW_PUBLIC_TEMP_AUDIO = (
        os.getenv("ALLOW_PUBLIC_TEMP_AUDIO", "false").lower() == "true"
    )

    # Whether the app should expect a pre-built transcription DB (data/db/transcription.db)
    # Production and most deployments will keep this True. Development Variant A (fast local)
    # can use DevConfig to set this to False so the app won't require the transcription DB.
    EXPECT_TRANSCRIPTION_DB = True


    # Auth DB (used only when AUTH_BACKEND=db) - DSN or fallback to sqlite file
    AUTH_DATABASE_URL = os.getenv(
        "AUTH_DATABASE_URL", f"sqlite:///{(Path(PROJECT_ROOT) / 'data' / 'db' / 'auth.db').as_posix()}"
    )

    # Hashing (argon2 or bcrypt)
    AUTH_HASH_ALGO = os.getenv("AUTH_HASH_ALGO", "argon2")
    # Argon2 defaults - these may be tuned for infra but sensible defaults applied
    AUTH_ARGON2_TIME_COST = int(os.getenv("AUTH_ARGON2_TIME_COST", "2"))
    AUTH_ARGON2_MEMORY_COST = int(os.getenv("AUTH_ARGON2_MEMORY_COST", "102400"))
    AUTH_ARGON2_PARALLELISM = int(os.getenv("AUTH_ARGON2_PARALLELISM", "4"))

    # Account deletion/anonymization retention (days)
    # Users marked as deleted will be anonymized after this many days.
    AUTH_ACCOUNT_ANONYMIZE_AFTER_DAYS = int(os.getenv("AUTH_ACCOUNT_ANONYMIZE_AFTER_DAYS", "30"))

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

    # For local development Variant A — we don't require the heavyweight transcription DB
    EXPECT_TRANSCRIPTION_DB = False


CONFIG_MAPPING = {
    "development": DevConfig,
    "production": BaseConfig,
}


def load_config(app, env_name: str | None) -> None:
    """Load a configuration object based on the environment name."""
    env = env_name or os.getenv("FLASK_ENV", "production").lower()
    config_obj = CONFIG_MAPPING.get(env, BaseConfig)
    app.config.from_object(config_obj)

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
