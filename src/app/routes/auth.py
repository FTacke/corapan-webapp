"""Authentication endpoints."""
from __future__ import annotations

from dataclasses import dataclass

from flask import Blueprint, Response, current_app, flash, g, jsonify, make_response, redirect, request, session, url_for
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
        verify_jwt_in_request(optional=True)
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


@blueprint.get("/ready")
def auth_ready() -> Response:
    """
    Authentication ready page - polls /auth/session until cookies are confirmed.
    This is a deterministic intermediate page that ensures cookies are set
    before redirecting to the target page (typically /player).
    
    Uses 303 redirect from POST /auth/login to ensure proper cookie handling.
    """
    next_url = request.args.get("next", url_for("public.landing_page"))
    
    # Security: validate next_url is relative (no external redirects)
    if next_url.startswith('http://') or next_url.startswith('https://'):
        from urllib.parse import urlparse
        parsed = urlparse(next_url)
        # Only allow same host
        if parsed.netloc and parsed.netloc != request.host:
            current_app.logger.warning(f'Blocked external redirect attempt: {next_url}')
            next_url = url_for("public.landing_page")
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="cache-control" content="no-store">
    <title>Autenticando...</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: #f5f5f5;
        }}
        .loader {{
            text-align: center;
        }}
        .spinner {{
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="loader">
        <div class="spinner"></div>
        <p>Autenticando...</p>
    </div>
    <script>
    (async () => {{
        console.log('[Auth Ready] Starting session verification...');
        
        for (let i = 0; i < 10; i++) {{
            try {{
                const response = await fetch('/auth/session', {{
                    credentials: 'same-origin',
                    cache: 'no-store'
                }});
                
                console.log('[Auth Ready] Session check attempt', i + 1, '- Status:', response.status);
                
                if (response.ok) {{
                    const data = await response.json();
                    if (data.authenticated) {{
                        console.log('[Auth Ready] Session confirmed for user:', data.user);
                        console.log('[Auth Ready] Redirecting to:', {repr(next_url)});
                        location.replace({repr(next_url)});
                        return;
                    }}
                }}
            }} catch (error) {{
                console.error('[Auth Ready] Session check failed:', error);
            }}
            
            await new Promise(resolve => setTimeout(resolve, 150));
        }}
        
        console.error('[Auth Ready] Session verification failed after 10 attempts');
        location.href = '/?showlogin=1&e=auth';
    }})();
    </script>
    <noscript>JavaScript wird benötigt, um fortzufahren.</noscript>
</body>
</html>"""
    
    response = Response(html, 200, content_type='text/html; charset=utf-8')
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Vary'] = 'Cookie'
    
    return response


def redirect_to_login(message: str | None = None) -> Response:
    """
    Redirect to login page/dialog with optional message.
    Saves current URL for post-login redirect.
    """
    save_return_url()
    
    # Try to redirect to referrer with login dialog hint
    referrer = request.referrer or url_for("public.landing_page")
    
    if message:
        flash(message, "info")
    
    # Add query parameter to open login dialog (avoids scroll-to-anchor)
    separator = '&' if '?' in referrer else '?'
    return redirect(f"{referrer}{separator}showlogin=1")


@dataclass(slots=True)
class Credential:
    role: Role
    password_hash: str


CREDENTIALS: dict[str, Credential] = {}


@blueprint.post("/login")
@limiter.limit("5 per minute")
def login() -> Response:
    """Login endpoint with rate limiting (max 5 attempts per minute)."""
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")
    
    # Check for stored return URL (from protected routes or save-redirect API)
    return_url = session.pop(RETURN_URL_SESSION_KEY, None)
    
    # Fallback to form referrer or request referrer or landing page
    if not return_url:
        return_url = request.form.get("referrer") or request.referrer or url_for("public.landing_page")
    
    if not username or username not in CREDENTIALS:
        current_app.logger.warning(f'Failed login attempt - unknown user: {username} from {request.remote_addr}')
        flash("Unknown account.", "error")
        # Restore return URL for next login attempt
        if return_url and return_url != url_for("public.landing_page"):
            session[RETURN_URL_SESSION_KEY] = return_url
        # Strip ?showlogin=1 if present, but keep other query parameters
        redirect_url = return_url
        if redirect_url and '?showlogin=1' in redirect_url:
            redirect_url = redirect_url.replace('?showlogin=1', '?').replace('&showlogin=1', '').rstrip('?')
        return redirect(redirect_url)
    
    credential = CREDENTIALS[username]
    if not check_password_hash(credential.password_hash, password):
        current_app.logger.warning(f'Failed login attempt - wrong password: {username} from {request.remote_addr}')
        flash("Invalid credentials.", "error")
        # Restore return URL for next login attempt
        if return_url and return_url != url_for("public.landing_page"):
            session[RETURN_URL_SESSION_KEY] = return_url
        # Strip ?showlogin=1 if present, but keep other query parameters
        redirect_url = return_url
        if redirect_url and '?showlogin=1' in redirect_url:
            redirect_url = redirect_url.replace('?showlogin=1', '?').replace('&showlogin=1', '').rstrip('?')
        return redirect(redirect_url)
    
    # Create access token (1h) and refresh token (7 days)
    access_token = issue_token(username, credential.role)
    refresh_token = create_refresh_token(
        identity=username,
        additional_claims={"role": credential.role.value}
    )
    
    # Use 303 See Other redirect to /auth/ready with next URL
    # The ready page will poll /auth/session to confirm cookies are set
    ready_url = url_for("auth.auth_ready", next=return_url)
    response = make_response(redirect(ready_url, 303))
    
    # Set both cookies
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    
    # Prevent caching of login response
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    
    counter_access.increment(username, credential.role.value)
    current_app.logger.info(f'Successful login: {username} from {request.remote_addr} -> ready page -> {return_url}')
    return response


@blueprint.post("/logout")
@jwt_required(optional=True)
def logout() -> Response:
    """Logout endpoint - clears JWT cookies and redirects with reload trigger."""
    # Get referrer to determine redirect target
    referrer = request.referrer or url_for("public.landing_page")
    
    # Check if referrer is a protected route that requires auth
    # If so, redirect to landing page instead to avoid redirect loop
    protected_paths = ['/player', '/editor', '/admin']
    redirect_to = referrer
    
    # Check if referrer contains any protected path
    for protected_path in protected_paths:
        if protected_path in referrer:
            redirect_to = url_for("public.landing_page")
            break
    
    # Clear JWT cookies
    response = make_response(redirect(redirect_to, 303))
    unset_jwt_cookies(response)
    
    # CRITICAL: Force browser to reload page after redirect
    # This ensures data-auth attribute is updated from server
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    flash("Has cerrado sesión correctamente.", "success")
    current_app.logger.info(f'User logged out from {request.remote_addr} -> redirecting to {redirect_to}')
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
    
    CRITICAL FIX for optional auth routes:
    Flask-JWT-Extended calls error callbacks even for optional=True routes
    when expired tokens are present. To prevent this, we manually decode
    the JWT with SIGNATURE VERIFICATION but allow_expired=True for optional routes.
    
    This prevents expired_token_loader from being called while still validating
    token integrity (preventing manipulated cookies).
    """
    from flask_jwt_extended.utils import decode_token
    from flask_jwt_extended.config import config as jwt_config
    from jwt.exceptions import InvalidTokenError
    from datetime import datetime, timezone
    
    # List of routes that use @jwt_required(optional=True)
    OPTIONAL_AUTH_ROUTES = [
        '/corpus/', '/media/', '/auth/session', '/auth/logout'
    ]
    
    path = request.path
    is_optional_route = any(path.startswith(route) for route in OPTIONAL_AUTH_ROUTES)
    
    # For optional routes: check if access token is expired (but valid signature)
    if is_optional_route:
        access_cookie = request.cookies.get(jwt_config.access_cookie_name)
        if access_cookie:
            try:
                # Decode WITH signature verification, but allow expired
                decoded = decode_token(access_cookie, allow_expired=True)
                exp = decoded.get('exp')
                
                # Check if token is expired
                if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                    # Expired but valid signature - treat as anonymous for optional route
                    g.user = None
                    g.role = None
                    return
                    
                # Token is valid and not expired - set user info
                g.user = decoded.get("sub")
                role_value = decoded.get("role")
                try:
                    g.role = Role(role_value) if role_value else None
                except ValueError:
                    g.role = None
                return
                
            except InvalidTokenError:
                # Invalid token (bad signature, malformed, etc.) - treat as anonymous
                g.user = None
                g.role = None
                return
            except Exception:  # noqa: BLE001
                # Any other error - treat as anonymous
                g.user = None
                g.role = None
                return
    
    # Standard path for non-optional routes or optional routes without cookie
    try:
        verify_jwt_in_request(optional=True)
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
