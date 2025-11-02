"""Player page routes."""
from __future__ import annotations

from flask import Blueprint, abort, current_app, make_response, render_template, request
from flask_jwt_extended import jwt_required

blueprint = Blueprint("player", __name__)


@blueprint.get("/player")
@jwt_required()
def player_page():
    """Player page - requires authentication."""
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
    )
    
    # Add cache control headers to prevent serving cached "logged out" page
    response = make_response(html)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Vary'] = 'Cookie'
    
    return response
