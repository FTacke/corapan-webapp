"""Player page routes."""
from __future__ import annotations

from flask import Blueprint, abort, current_app, make_response, redirect, render_template, request, url_for
from flask_jwt_extended import jwt_required, verify_jwt_in_request

blueprint = Blueprint("player", __name__)


def is_authenticated() -> bool:
    """Check if user has valid JWT token (without raising exceptions)."""
    try:
        verify_jwt_in_request(optional=True)
        from flask_jwt_extended import get_jwt_identity
        return get_jwt_identity() is not None
    except Exception:
        return False


@blueprint.get("/player")
def player_page():
    """
    Player page - requires authentication.
    
    Gate: Check auth before rendering. If not authenticated:
    - HTMX request: 204 No Content + HX-Redirect to login_sheet with next
    - Full-page: 303 Redirect to login with next
    """
    # Gate: Require authentication
    if not is_authenticated():
        # Use path + query string (not full URL with scheme/host)
        next_url = request.full_path.rstrip('?')
        
        # HTMX request: Client-side redirect via header
        if request.headers.get("HX-Request"):
            from urllib.parse import quote
            response = make_response("", 204)
            # Double-encode next parameter to preserve query string through HTMX redirect
            # (HTMX decodes once when following HX-Redirect header)
            double_encoded_next = quote(quote(next_url, safe=''), safe='')
            redirect_url = f"/auth/login_sheet?next={double_encoded_next}"
            response.headers["HX-Redirect"] = redirect_url
            return response
        
        # Full-page request: Server-side redirect to landing page with login flag
        return redirect(url_for("public.landing_page", login=1, next=next_url), 303)
    
    # Authenticated: Render player
    transcription = request.args.get("transcription")
    audio = request.args.get("audio")
    token_id = request.args.get("token_id")
    if not transcription or not audio:
        abort(400)
    
    # Log cookie presence for debugging
    jwt_cookie_name = current_app.config.get('JWT_ACCESS_COOKIE_NAME', 'access_token_cookie')
    has_jwt = jwt_cookie_name in request.cookies
    current_app.logger.debug(
        f'[Player] Request with JWT cookie: {has_jwt} '
        f'(cookies: {list(request.cookies.keys())})'
    )
    
    # Render template
    html = render_template(
        "pages/player.html",
        transcription=transcription,
        audio=audio,
        token_id=token_id or "",
        page_name="player"
    )
    
    # Add cache control headers to prevent serving cached "logged out" page
    response = make_response(html)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Vary'] = 'Cookie'
    
    return response
