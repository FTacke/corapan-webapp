"""Register Flask extensions."""
from __future__ import annotations

from flask import Flask
from flask_caching import Cache
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "200 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

# Cache configuration
# TODO: For production, use Redis: CACHE_TYPE='RedisCache', CACHE_REDIS_URL='redis://localhost:6379/0'
cache = Cache(config={
    'CACHE_TYPE': 'SimpleCache',  # In-memory cache (dev/testing)
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes default
})


def register_extensions(app: Flask) -> None:
    """Attach Flask extensions to the app."""
    jwt.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)