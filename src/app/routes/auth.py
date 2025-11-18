"""Authentication endpoints."""
from __future__ import annotations

from dataclasses import dataclass

from flask import Blueprint, Response, current_app, flash, g, jsonify, make_response, redirect, render_template, request, session, url_for
from flask_jwt_extended import (
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
    verify_jwt_in_request,
)
from werkzeug.security import check_password_hash

from ..auth import Role
from ..auth.jwt import issue_token
from ..extensions import limiter
from ..services.counters import counter_access

blueprint = Blueprint("auth", __name__, url_prefix="/auth")

# Session key for storing intended destination after login
RETURN_URL_SESSION_KEY = "_return_url_after_login"


def save_return_url(url: str | None = None) -> None:
    """
    Save the current or specified URL for redirect after login.
    Called by protected routes when authentication is required.
    """
    if url is None:
        url = request.url
    
    # Don't save login/logout URLs or static assets
    if url and not any(x in url for x in ['/auth/', '/static/', '/health']):
        session[RETURN_URL_SESSION_KEY] = url
        current_app.logger.debug(f'Saved return URL: {url}')


@blueprint.post("/save-redirect")
def save_redirect() -> Response:
    """
    API endpoint to save player redirect URL in server session.
    Called by JavaScript before opening login dialog.
    """
    data = request.get_json() or {}
    redirect_url = data.get("url", "").strip()
    
    if redirect_url and not any(x in redirect_url for x in ['/auth/', '/static/', '/health']):
        session[RETURN_URL_SESSION_KEY] = redirect_url
        current_app.logger.debug(f'Saved redirect URL via API: {redirect_url}')
        return jsonify({"success": True}), 200
    
    return jsonify({"success": False, "error": "Invalid URL"}), 400


@blueprint.get("/session")
def check_session() -> Response:
    """
    Check if user has valid auth session.
    Used by player to ensure cookies are set before loading data.
    Also returns token expiration for proactive refresh on client-side.
    
    ALWAYS returns 200 with JSON, regardless of token state.
    This is an "optional auth" endpoint that reports state without failing.
    
    Contract:
    - authenticated: bool (True if valid token present)
    - user: str|None (username if authenticated)
    - exp: int|None (Unix timestamp of token expiration)
    
    Response is always 200 OK, even if not authenticated.
    This prevents JWT error handlers from interfering and ensures
    consistent JSON responses (no HTML redirects).
    """
    try:
        # Manual token verification without decorator to avoid error handlers
        # Ensure we check cookies explicitly so fetch('/auth/session') inherits cookies
        verify_jwt_in_request(optional=True, locations=["cookies"])
        token = get_jwt() or {}
        sub = token.get("sub")
        exp = token.get("exp")
        
        resp = jsonify({
            "authenticated": bool(sub),
            "user": sub if sub else None,
            "exp": exp
        })
    except Exception as e:
        # Fallback for any token errors (expired, invalid, etc.)
        # Still return 200 with authenticated: false
        current_app.logger.debug(f'Session check fallback: {e}')
        resp = jsonify({
            "authenticated": False,
            "user": None,
            "exp": None
        })
    
    # Cache-Control headers as documented in auth-flow.md
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Vary"] = "Cookie"
    
    return resp, 200



@dataclass(slots=True)
class Credential:
    role: Role
    password_hash: str


CREDENTIALS: dict[str, Credential] = {}


def _safe_next(raw: str | None) -> str | None:
    """
    Validate and sanitize redirect URL to prevent open redirect vulnerabilities.
    
    Args:
        raw: URL from form, query param, or referrer (may be double-encoded)
        
    Returns:
        Safe path+query if valid, None otherwise
        
    Security rules:
    - Must be same origin (empty netloc or matches request.host)
    - Must not redirect to auth endpoints (login/logout)
    - Only path and query preserved, no scheme/netloc/fragment
    
    Note: Handles double-encoded URLs (used to preserve query strings through HTMX redirects).
    """
    from urllib.parse import urlparse, unquote
    
    if not raw:
        return None
    
    # Decode once (in case it's double-encoded from HTMX flow)
    decoded = unquote(raw)
    parsed = urlparse(decoded)
    
    # External origin → reject
    if parsed.netloc and parsed.netloc != request.host:
        return None
    
    # Auth endpoints → reject (prevent redirect loops)
    if parsed.path.startswith(("/auth/login", "/auth/logout")):
        return None
    
    # Build safe path+query
    safe_url = parsed.path
    if parsed.query:
        safe_url += f"?{parsed.query}"
    
    return safe_url if safe_url else None


@blueprint.get("/login_sheet")
def login_sheet() -> Response:
    """
    Render login sheet partial (HTMX fragment).
    
    Returns only the sheet HTML (no full page layout).
    Used by navbar, drawer, and on-page auth prompts.
    
    Template: templates/auth/_login_sheet.html
    """
    from flask import render_template
    
    # Get next URL from query param or referrer
    next_url = _safe_next(request.args.get("next") or request.referrer)
    
    response = make_response(render_template("auth/_login_sheet.html", next=next_url or ""))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Vary"] = "Cookie"
    return response, 200


@blueprint.get("/login", endpoint="login")
def login_form() -> Response:
    """
    GET /auth/login - Router für direktes Aufrufen.
    
    HTMX-Requests: 204 No Content + HX-Redirect zu login_sheet
    Full-Page: 303 zu Inicio mit ?login=1&next=...
    
    Zweck: Verhindert Full-Page-Login; triggert Sheet stattdessen.
    """
    next_url = _safe_next(request.args.get("next") or request.referrer)
    
    # HTMX request: redirect via header
    if request.headers.get("HX-Request"):
        response = make_response("", 204)
        response.headers["HX-Redirect"] = url_for("auth.login_sheet", next=next_url) if next_url else url_for("auth.login_sheet")
        return response
    
    # Full-page request: redirect to inicio with login flag
    # Inicio-Template wird das Sheet via JS laden
    target = url_for("public.landing_page", login=1, next=next_url) if next_url else url_for("public.landing_page", login=1)
    return redirect(target, 303)


@blueprint.post("/login", endpoint="login_post")
@limiter.limit("5 per minute")
def login_post() -> Response:
    """
    Login endpoint (POST) - supports both HTMX and full-page.
    
    Rate limit ist deaktiviert in debug mode (siehe extensions.py DevFriendlyLimiter).
    
    Flow:
    1. POST /auth/login mit username+password+next
    2. Wenn erfolgreich:
       - HTMX: 204 No Content + HX-Redirect zum intended target
       - Full-page: 303 Redirect zum intended target
    3. Wenn fehler: 400 Bad Request + Sheet mit Fehler anzeigen
    """
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")
    
    # Get next URL from form, query param, or referrer
    next_raw = request.form.get("next") or request.args.get("next") or request.headers.get("Referer")
    # Fallback: if the previous step saved a redirect in session, use it
    if not next_raw and RETURN_URL_SESSION_KEY in session:
        next_raw = session.pop(RETURN_URL_SESSION_KEY, None)
        current_app.logger.debug(f'Login POST using session RETURN_URL_SESSION_KEY: {next_raw}')
    next_url = _safe_next(next_raw)
    
    # Validierung: Username existiert?
    if not username or username not in CREDENTIALS:
        current_app.logger.warning(f'Failed login attempt - unknown user: {username} from {request.remote_addr}')
        flash("Unknown account.", "error")
        # Return sheet with error
        return render_template("auth/_login_sheet.html", next=next_url or ""), 400
    
    # Validierung: Password korrekt?
    credential = CREDENTIALS[username]
    if not check_password_hash(credential.password_hash, password):
        current_app.logger.warning(f'Failed login attempt - wrong password: {username} from {request.remote_addr}')
        flash("Invalid credentials.", "error")
        # Return sheet with error
        return render_template("auth/_login_sheet.html", next=next_url or ""), 400
    
    # Erfolgreich: Tokens erstellen
    access_token = issue_token(username, credential.role)
    refresh_token = create_refresh_token(
        identity=username,
        additional_claims={"role": credential.role.value}
    )
    
    counter_access.increment(username, credential.role.value)
    
    # Redirect target
    target = next_url or url_for("public.landing_page")
    
    # HTMX request: Header-based redirect (no HTML body)
    if request.headers.get("HX-Request"):
        response = make_response("", 204)
        response.headers["HX-Redirect"] = target
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        current_app.logger.info(f'Successful login (HTMX): {username} from {request.remote_addr} -> {target}')
        return response
    
    # Full-page request: Standard 303 redirect
    response = make_response(redirect(target, 303))
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    current_app.logger.info(f'Successful login: {username} from {request.remote_addr} -> {target}')
    return response


def _next_url_after_logout() -> str:
    """Determine redirect target after logout.
    
    Logic:
    - Protected routes (/player, /editor, /admin) → Redirect to Inicio (/)
    - Public routes (/corpus, /search, /) → Stay on same page
    - External/invalid referrer → Fallback to Inicio
    
    Returns:
        Redirect URL (absolute or relative)
    """
    from urllib.parse import urlparse
    
    # Protected route prefixes
    PROTECTED_PATHS = ('/player', '/editor', '/admin')
    
    # Public route prefixes (can stay on page after logout)
    PUBLIC_PATHS = ('/corpus', '/search', '/proyecto', '/atlas', '/stats', '/impressum', '/privacy', '/')
    
    # Get referrer from query param (explicit) or header (implicit)
    referrer = request.args.get('next') or request.headers.get('Referer')
    
    # No referrer or external origin → fallback to inicio
    if not referrer:
        return url_for('public.landing_page')
    
    # Parse referrer to check same-origin
    parsed = urlparse(referrer)
    if parsed.netloc and parsed.netloc != request.host:
        # External referrer → fallback to inicio
        return url_for('public.landing_page')
    
    # Extract path from referrer
    path = parsed.path
    
    # Protected route → redirect to inicio
    if any(path.startswith(p) for p in PROTECTED_PATHS):
        return url_for('public.landing_page')
    
    # Public route → stay on same page
    if any(path.startswith(p) for p in PUBLIC_PATHS):
        return referrer
    
    # Unknown route → fallback to inicio
    return url_for('public.landing_page')


@blueprint.route("/logout", methods=["GET", "POST"])
def logout_any() -> Response:
    """Logout endpoint (GET + POST) - clears JWT cookies and redirects.
    
    CRITICAL FIX (2025-11-11): Unified GET+POST endpoint, NO @jwt_required, NO CSRF.
    
    WHY NO CSRF?
    - Logout is idempotent (just clears cookies)
    - No sensitive data modified
    - No state change that could harm user
    - CSRF attack on logout = annoying, not dangerous
    
    WHY NO @jwt_required?
    - Must work even with expired/invalid tokens
    - Public endpoint that clears cookies unconditionally
    - Prevents JWT error handlers from intercepting
    
    Redirect logic: Smart (public → stay, protected → inicio)
    Cookies cleared: access_token_cookie, refresh_token_cookie
    """
    redirect_to = _next_url_after_logout()
    
    # Clear JWT cookies
    response = make_response(redirect(redirect_to, 303))
    unset_jwt_cookies(response)
    
    # Force browser to reload page after redirect
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    method = request.method
    flash("Has cerrado sesión correctamente.", "success")
    current_app.logger.info(f'User logged out via {method} from {request.remote_addr} -> {redirect_to}')
    return response


@blueprint.post("/refresh")
@jwt_required(refresh=True)
def refresh() -> Response:
    """
    Refresh endpoint - issues new access token from valid refresh token.
    Called automatically by frontend when access token expires.
    No user interaction required.
    """
    # Get user identity from refresh token
    current_user = get_jwt_identity()
    current_role_value = get_jwt().get("role")
    
    # Validate role
    try:
        role = Role(current_role_value) if current_role_value else None
        if not role:
            current_app.logger.warning(f'Token refresh failed - invalid role for user: {current_user}')
            return jsonify({"error": "Invalid role"}), 401
    except ValueError:
        current_app.logger.warning(f'Token refresh failed - unknown role for user: {current_user}')
        return jsonify({"error": "Invalid role"}), 401
    
    # Issue new access token
    new_access_token = issue_token(current_user, role)
    
    response = jsonify({"msg": "Token refreshed successfully"})
    set_access_cookies(response, new_access_token)
    
    current_app.logger.info(f'Token refreshed for user: {current_user}')
    return response


@blueprint.before_app_request
def load_user_dimensions():
    """Load user info from JWT into flask.g context.
    
    CRITICAL FIX (2025-11-11): Public routes bypass JWT processing entirely.
    
    Problem:
    - Global verify_jwt_in_request() triggered expired_token_loader even for public routes
    - Caused 401/302 redirects on /corpus/, /search/advanced when expired tokens present
    
    Solution:
    - Public routes (corpus, search, bls, atlas, static) skip JWT processing completely
    - Only protected routes (/player, /editor, /admin) perform JWT verification
    - Prevents error handlers from blocking public access
    """
    # Public route prefixes - NO JWT processing
    # Only minimal infra/static routes bypass JWT entirely. Routes such as
    # /corpus, /search/advanced, /atlas and /media/* are "optional auth" and
    # should run `verify_jwt_in_request(optional=True)` so that `g.user` is
    # populated when a valid token is present.
    PUBLIC_PREFIXES = (
        '/static/', '/favicon', '/robots.txt', '/health', '/media/play_audio',
    )
    
    path = request.path
    current_app.logger.debug(f'[Auth.load_user_dimensions] Path: {path}; Public prefixes: {PUBLIC_PREFIXES}')
    
    # Early return for public routes - skip JWT entirely
    if path.startswith(PUBLIC_PREFIXES):
        g.user = None
        g.role = None
        return
    
    # Protected routes: Standard JWT processing - verify JWT in cookies
    try:
        # Use cookie location explicitly to avoid header-only tokens in API tests
        verify_jwt_in_request(optional=True, locations=["cookies"])
        token = get_jwt() or {}
        g.user = token.get("sub")
        role_value = token.get("role")
        try:
            g.role = Role(role_value) if role_value else None
        except ValueError:
            g.role = None
    except Exception:  # noqa: BLE001
        # Silently ignore - treat as no token
        g.user = None
        g.role = None
        current_app.logger.debug(f'[Auth.load_user_dimensions] Token invalid or missing - g.user set to None for path {path}')
    else:
        current_app.logger.debug(f'[Auth.load_user_dimensions] g.user set to {g.user} for path {path}')
