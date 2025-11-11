"""Application factory for the modern CO.RA.PAN web app."""
from __future__ import annotations

import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

from .auth.loader import hydrate
from .extensions import register_extensions
from .routes import register_blueprints

# Import load_config from the config.py module (bypassing the config package)
from .config import load_config


def create_app(env_name: str | None = None) -> Flask:
    """Create and configure the Flask application instance."""
    project_root = Path(__file__).resolve().parents[2]
    template_dir = project_root / 'templates'
    static_dir = project_root / 'static'

    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
    )
    load_config(app, env_name)
    
    # Add build ID for cache busting and deployment verification
    import time
    app.config["APP_BUILD_ID"] = time.strftime("%Y%m%d%H%M%S")
    
    hydrate()
    register_extensions(app)
    register_blueprints(app)
    register_context_processors(app)
    register_auth_context(app)
    register_security_headers(app)
    register_error_handlers(app)
    setup_logging(app)
    
    # SCHEMA VALIDATION: Prüfe DB-Schema beim Start
    _validate_db_schema_on_startup(app)
    
    return app


def _validate_db_schema_on_startup(app: Flask) -> None:
    """
    Prüft beim App-Start, dass die transcription.db alle erforderlichen CANON_COLS hat.
    Erstellt fehlende Indizes bei Bedarf.
    Raises: RuntimeError wenn kritische Spalten fehlen
    """
    try:
        from .services.corpus_search import CANON_COLS, _validate_db_schema
        from .services.database import open_db
        import sqlite3
        
        app.logger.info("[STARTUP] Starting DB schema validation...")
        with open_db("transcription") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            _validate_db_schema(cursor, CANON_COLS)
        
        app.logger.info("[STARTUP] DB schema validation passed - all CANON_COLS present")
        
        # Stelle sicher, dass der Index für 'norm' existiert
        app.logger.info("[STARTUP] Creating norm index if not exists...")
        with open_db("transcription") as conn:
            cursor = conn.cursor()
            # Prüfe ob Index existiert
            cursor.execute("PRAGMA index_info('idx_tokens_norm')")
            if not cursor.fetchone():
                app.logger.info("[STARTUP] Creating idx_tokens_norm index...")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tokens_norm ON tokens(norm)")
                conn.commit()
                app.logger.info("[STARTUP] idx_tokens_norm index created successfully")
            else:
                app.logger.info("[STARTUP] idx_tokens_norm index already exists")
    except RuntimeError as e:
        app.logger.error(f"[STARTUP] DB schema validation FAILED: {e}")
        raise
    except Exception as e:
        app.logger.error(f"[STARTUP] Unexpected error during schema validation: {e}")
        raise


def register_context_processors(app: Flask) -> None:
    """Expose helpers to the template engine."""
    @app.context_processor
    def inject_utilities():  # pragma: no cover - thin wrapper
        return {
            "now": datetime.utcnow,
            "allow_public_temp_audio": app.config.get("ALLOW_PUBLIC_TEMP_AUDIO", False),
        }


def register_auth_context(app: Flask) -> None:
    """Register before_request hook and context processor for authentication state.
    
    This enables server-side rendering of Login/Logout in Navbar/Drawer.
    Every request checks JWT cookies and exposes:
    - g.user: username (string) or None
    - g.role: Role enum or None
    - is_authenticated: bool (True if valid JWT present)
    - current_user: username string or None
    """
    from flask import g
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
    from .auth import Role
    
    @app.before_request
    def _set_auth_context():
        """Load auth state into g context for all requests."""
        # Public routes - skip JWT processing entirely
        PUBLIC_PREFIXES = (
            '/static/', '/favicon', '/robots.txt', '/health',
        )
        
        path = request.path
        
        # Skip JWT processing for static assets
        if any(path.startswith(p) for p in PUBLIC_PREFIXES):
            g.user = None
            g.role = None
            return
        
        # Try to verify JWT (optional - don't fail if no token)
        try:
            verify_jwt_in_request(optional=True, locations=["cookies"])
            identity = get_jwt_identity()
            token = get_jwt() or {}
            
            g.user = identity
            role_value = token.get("role")
            try:
                g.role = Role(role_value) if role_value else None
            except (ValueError, KeyError):
                g.role = None
        except Exception:  # noqa: BLE001
            # Token error - treat as no authentication
            g.user = None
            g.role = None
    
    @app.context_processor
    def _inject_auth_context():
        """Expose auth state to templates."""
        user = getattr(g, 'user', None)
        return {
            "is_authenticated": bool(user),
            "current_user": user,
        }


def register_security_headers(app: Flask) -> None:
    """Add security headers to all responses."""
    @app.after_request
    def set_security_headers(response):
        """Set security headers on every response."""
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # XSS Protection (legacy browsers)
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HSTS - only in production
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        # Note: 'unsafe-inline' needed for current jQuery/DataTables implementation
        # TODO: Remove 'unsafe-inline' after jQuery migration
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://code.jquery.com https://cdn.jsdelivr.net "
            "https://cdn.datatables.net https://cdnjs.cloudflare.com https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.datatables.net "
            "https://cdnjs.cloudflare.com https://unpkg.com https://fonts.googleapis.com; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net "
            "https://fonts.googleapis.com https://fonts.gstatic.com; "
            "connect-src 'self'; "
            "media-src 'self' blob:; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # Auth-specific caching rules for htmx compatibility
        if request.path.startswith("/auth/"):
            # Prevent caching of auth endpoints (login sheet, session check, etc.)
            response.headers["Cache-Control"] = "no-store, private"
            response.headers["Vary"] = "Cookie"
        
        return response


def register_error_handlers(app: Flask) -> None:
    """Register custom error handlers for common HTTP errors."""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        app.logger.warning(f'Bad request: {error}')
        if request.path.startswith('/api/') or request.path.startswith('/atlas/'):
            return jsonify({'error': 'Bad request', 'message': str(error)}), 400
        return render_template('errors/400.html', error=error), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors - redirect to login for HTML requests."""
        app.logger.warning(f'Unauthorized access attempt: {request.path} from {request.remote_addr}')
        
        # API requests get JSON response
        if request.path.startswith('/api/') or request.path.startswith('/atlas/'):
            return jsonify({'error': 'Unauthorized', 'message': str(error)}), 401
        
        # AJAX/fetch requests get JSON response (check Accept header)
        if request.accept_mimetypes.best == 'application/json':
            return jsonify({'error': 'Unauthorized', 'message': str(error)}), 401
        
        # HTML requests: save return URL and redirect to login
        from .routes.auth import save_return_url
        save_return_url()
        
        # Redirect to referrer (or home) with login dialog query parameter
        # Using query param instead of hash to avoid automatic scroll-to-anchor
        referrer = request.referrer or url_for("public.landing_page")
        flash("Por favor inicia sesión para acceder a este contenido.", "info")
        
        # Add ?showlogin=1 to URL (preserves scroll position)
        separator = '&' if '?' in referrer else '?'
        return redirect(f"{referrer}{separator}showlogin=1")
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        app.logger.warning(f'Forbidden access attempt: {request.path} from {request.remote_addr}')
        if request.path.startswith('/api/') or request.path.startswith('/atlas/'):
            return jsonify({'error': 'Forbidden', 'message': str(error)}), 403
        return render_template('errors/403.html', error=error), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        if request.path.startswith('/api/') or request.path.startswith('/atlas/'):
            return jsonify({'error': 'Not found', 'message': str(error)}), 404
        return render_template('errors/404.html', error=error), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        app.logger.error(f'Server Error: {error}', exc_info=True)
        if request.path.startswith('/api/') or request.path.startswith('/atlas/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500


def setup_logging(app: Flask) -> None:
    """Configure application logging."""
    if not app.debug:
        # Create logs directory
        log_dir = Path(__file__).resolve().parents[2] / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # Setup rotating file handler
        file_handler = RotatingFileHandler(
            log_dir / 'corapan.log',
            maxBytes=10_000_000,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        file_handler.setLevel(logging.INFO)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('CO.RA.PAN application startup')
