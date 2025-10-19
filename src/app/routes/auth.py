"""Authentication endpoints."""
from __future__ import annotations

from dataclasses import dataclass

from flask import Blueprint, Response, current_app, flash, g, jsonify, redirect, request, session, url_for
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
    
    # Check for stored return URL (from protected routes)
    return_url = session.pop(RETURN_URL_SESSION_KEY, None)
    
    # Fallback to form referrer or request referrer
    if not return_url:
        return_url = request.form.get("referrer") or request.referrer or url_for("public.landing_page")
    
    if not username or username not in CREDENTIALS:
        current_app.logger.warning(f'Failed login attempt - unknown user: {username} from {request.remote_addr}')
        flash("Unknown account.", "error")
        # Restore return URL for next login attempt
        if return_url and return_url != url_for("public.landing_page"):
            session[RETURN_URL_SESSION_KEY] = return_url
        return redirect(return_url if not return_url or "?" not in return_url else return_url.split("?")[0])
    
    credential = CREDENTIALS[username]
    if not check_password_hash(credential.password_hash, password):
        current_app.logger.warning(f'Failed login attempt - wrong password: {username} from {request.remote_addr}')
        flash("Invalid credentials.", "error")
        # Restore return URL for next login attempt
        if return_url and return_url != url_for("public.landing_page"):
            session[RETURN_URL_SESSION_KEY] = return_url
        return redirect(return_url if not return_url or "?" not in return_url else return_url.split("?")[0])
    
    # Create access token (30 min) and refresh token (7 days)
    access_token = issue_token(username, credential.role)
    refresh_token = create_refresh_token(
        identity=username,
        additional_claims={"role": credential.role.value}
    )
    
    response = redirect(return_url)
    
    # Set both cookies
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    
    counter_access.increment(username, credential.role.value)
    current_app.logger.info(f'Successful login: {username} from {request.remote_addr} -> redirecting to {return_url}')
    return response


@blueprint.post("/logout")
@jwt_required(optional=True)
def logout() -> Response:
    referrer = request.form.get("referrer") or request.referrer or url_for("public.landing_page")
    response = redirect(referrer)
    unset_jwt_cookies(response)
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
    try:
        verify_jwt_in_request(optional=True)
    except Exception:  # noqa: BLE001
        g.user = None
        g.role = None
        return
    token = get_jwt() or {}
    g.user = token.get("sub")
    role_value = token.get("role")
    try:
        g.role = Role(role_value) if role_value else None
    except ValueError:
        g.role = None
