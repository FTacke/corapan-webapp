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

# Load environment variables from passwords.env file
# This must happen before any config classes are instantiated
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_PASSWORDS_ENV_PATH = _PROJECT_ROOT / "passwords.env"
if _PASSWORDS_ENV_PATH.exists():
    load_dotenv(_PASSWORDS_ENV_PATH)


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
    JWT_SECRET_KEY = os.getenv("JWT_SECRET", os.getenv("FLASK_SECRET_KEY", DEFAULT_SECRET_SENTINEL))
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SECURE = SESSION_COOKIE_SECURE
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_COOKIE_SAMESITE = "Lax"  # Allows cookies in redirects
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7 days
    # Ensure cookies are sent with all requests (not just /auth)
    JWT_ACCESS_COOKIE_PATH = "/"
    JWT_REFRESH_COOKIE_PATH = "/"
    JWT_ACCESS_CSRF_COOKIE_PATH = "/"
    JWT_REFRESH_CSRF_COOKIE_PATH = "/"
    
    # Database paths
    DB_DIR = PROJECT_ROOT / "data" / "db"
    DB_PUBLIC_DIR = PROJECT_ROOT / "data" / "db_public"
    
    # Media paths
    MEDIA_DIR = PROJECT_ROOT / "media"
    TRANSCRIPTS_DIR = MEDIA_DIR / "transcripts"
    AUDIO_FULL_DIR = MEDIA_DIR / "mp3-full"
    AUDIO_SPLIT_DIR = MEDIA_DIR / "mp3-split"
    AUDIO_TEMP_DIR = MEDIA_DIR / "mp3-temp"
    
    # Feature flags
    ALLOW_PUBLIC_TEMP_AUDIO = os.getenv("ALLOW_PUBLIC_TEMP_AUDIO", "false").lower() == "true"
    
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
    
    if app.config["SECRET_KEY"] == DEFAULT_SECRET_SENTINEL:
        raise RuntimeError("FLASK_SECRET_KEY must be provided via environment variable.")


__all__ = [
    'load_config',
    'BaseConfig',
    'DevConfig',
    'Location',
    'LOCATIONS',
    'normalize_country_code',
    'get_location',
    'code_to_name',
    'name_to_code',
    'get_all_locations',
    'get_national_capitals',
    'get_regional_capitals',
    'get_locations_by_country',
    'get_country_name',
    'is_national_capital',
    'is_regional_capital',
    'export_all_to_json',
]
