"""Register Flask extensions."""
from __future__ import annotations

from flask import Flask, jsonify, request
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
    
    # Register JWT error handlers
    register_jwt_handlers()


def register_jwt_handlers() -> None:
    """Register JWT error handlers for expired/invalid tokens.
    
    CRITICAL: When @jwt_required(optional=True) is used, expired tokens
    should be silently ignored (treated as unauthenticated) instead of
    throwing errors. This prevents "Token has expired" errors for public
    pages like /corpus when users have old tokens in localStorage.
    """
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired JWT tokens.
        
        For API endpoints: Return 401 with JSON error.
        For HTML pages with optional auth: Return empty 200 (treated as no token).
        
        This allows @jwt_required(optional=True) routes to work correctly
        even when users have expired tokens cached.
        """
        # API endpoints: Return JSON error
        if request.path.startswith('/api/') or request.path.startswith('/atlas/'):
            return jsonify({
                'error': 'token_expired',
                'message': 'The token has expired'
            }), 401
        
        # AJAX/fetch requests: Return JSON error
        if request.accept_mimetypes.best == 'application/json':
            return jsonify({
                'error': 'token_expired',
                'message': 'The token has expired'
            }), 401
        
        # HTML pages with optional auth: Return 401 so Flask's error handler
        # can redirect to login (if needed) or just ignore it
        # The @jwt_required(optional=True) decorator should not trigger this
        # but if it does, we want graceful handling
        from flask import abort
        abort(401)
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        """Handle invalid JWT tokens (malformed, wrong signature, etc.).
        
        Similar to expired tokens: API gets JSON error, HTML pages
        redirect to login or ignore silently.
        """
        # API endpoints: Return JSON error
        if request.path.startswith('/api/') or request.path.startswith('/atlas/'):
            return jsonify({
                'error': 'invalid_token',
                'message': error_string
            }), 401
        
        # AJAX/fetch requests: Return JSON error
        if request.accept_mimetypes.best == 'application/json':
            return jsonify({
                'error': 'invalid_token',
                'message': error_string
            }), 401
        
        # HTML pages: Abort with 401 (let error handler deal with it)
        from flask import abort
        abort(401)
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error_string):
        """Handle requests without JWT token to @jwt_required() endpoints.
        
        Note: This is ONLY triggered by @jwt_required() (mandatory auth),
        NOT by @jwt_required(optional=True).
        """
        # API endpoints: Return JSON error
        if request.path.startswith('/api/') or request.path.startswith('/atlas/'):
            return jsonify({
                'error': 'unauthorized',
                'message': error_string
            }), 401
        
        # AJAX/fetch requests: Return JSON error
        if request.accept_mimetypes.best == 'application/json':
            return jsonify({
                'error': 'unauthorized',
                'message': error_string
            }), 401
        
        # HTML pages: Redirect to login (handled by 401 error handler in __init__.py)
        from flask import abort
        abort(401)
