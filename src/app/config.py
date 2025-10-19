"""Configuration management for the CO.RA.PAN web app."""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv


DEFAULT_SECRET_SENTINEL = "__CHANGE_ME__"

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / 'passwords.env'
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


class BaseConfig:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", DEFAULT_SECRET_SENTINEL)
    JWT_PUBLIC_KEY_PATH = os.getenv("JWT_PUBLIC_KEY_PATH")
    JWT_PRIVATE_KEY_PATH = os.getenv("JWT_PRIVATE_KEY_PATH")
    ALLOW_PUBLIC_TEMP_AUDIO = os.getenv("ALLOW_PUBLIC_TEMP_AUDIO", "true").lower() == "true"
    SESSION_COOKIE_SECURE = os.getenv("FLASK_SESSION_SECURE", "true").lower() == "true"
    SESSION_COOKIE_SAMESITE = os.getenv("FLASK_SESSION_SAMESITE", "lax")
    SESSION_COOKIE_HTTPONLY = True
    
    # JWT Configuration - Refresh Token Support
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = SESSION_COOKIE_SECURE
    JWT_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_SECRET_KEY = SECRET_KEY
    
    # Access Token: 30 minutes (short-lived for security)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    
    # Refresh Token: 7 days (long-lived for convenience)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # Separate cookie names for access and refresh tokens
    JWT_ACCESS_COOKIE_NAME = "corapan_access_token"
    JWT_REFRESH_COOKIE_NAME = "corapan_refresh_token"
    
    # Refresh cookie only sent to /auth/refresh endpoint
    JWT_REFRESH_COOKIE_PATH = "/auth/refresh"
    
    JWT_CSRF_CHECK_FORM = True


class DevConfig(BaseConfig):
    SESSION_COOKIE_SECURE = False
    JWT_COOKIE_SECURE = False


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




