"""Player page routes."""
from __future__ import annotations

from flask import Blueprint, abort, g, redirect, render_template, request, url_for
from flask_jwt_extended import jwt_required

blueprint = Blueprint("player", __name__)


@blueprint.get("/player")
@jwt_required(optional=True)
def player_page():
    """Player page - requires authentication."""
    # Check if user is authenticated
    if not getattr(g, "user", None):
        # Redirect to referrer or home with query param to open login (avoids scroll)
        referrer = request.referrer or url_for("public.landing_page")
        separator = '&' if '?' in referrer else '?'
        return redirect(f"{referrer}{separator}showlogin=1")
    
    transcription = request.args.get("transcription")
    audio = request.args.get("audio")
    token_id = request.args.get("token_id")
    if not transcription or not audio:
        abort(400)
    return render_template(
        "pages/player.html",
        transcription=transcription,
        audio=audio,
        token_id=token_id or "",
    )
