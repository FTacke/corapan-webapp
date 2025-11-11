"""Media-serving endpoints with public toggle."""
from __future__ import annotations

from pathlib import Path

from flask import Blueprint, abort, current_app, g, jsonify, request, send_file
import json

from ..config import code_to_name
from flask_jwt_extended import jwt_required

from ..auth import Role
from ..auth.decorators import require_role
from ..services import audio_snippets, media_store

blueprint = Blueprint("media", __name__, url_prefix="/media")


def _secure_path(base: Path, filename: str) -> Path:
    candidate = (base / filename).resolve()
    media_store.ensure_within(base, candidate)
    if not candidate.exists():
        abort(404)
    return candidate


def _temp_access_allowed() -> bool:
    return current_app.config.get("ALLOW_PUBLIC_TEMP_AUDIO", False) or getattr(g, "user", None) is not None


@blueprint.get("/full/<path:filename>")
def download_full(filename: str):
    """
    Serve full MP3 files with intelligent country subfolder detection.
    
    PUBLIC ROUTE (conditionally): No decorator needed.
    - For authenticated users: Always allowed
    - For unauthenticated: Only if public access is enabled
    """
    # Check if user is authenticated or public access is allowed
    if not (getattr(g, "user", None) or current_app.config.get("ALLOW_PUBLIC_FULL_AUDIO", False)):
        abort(401, "Authentication required to access full audio files")
    
    # Use intelligent path resolution with country subfolder detection
    path = media_store.safe_audio_full_path(filename)
    if path is None:
        abort(404, f"Audio file not found: {filename}")
    
    # Determine if download or streaming based on query parameter
    download_flag = request.args.get("download")
    as_attachment = download_flag is not None
    
    return send_file(
        path, 
        mimetype="audio/mpeg",
        as_attachment=as_attachment,
        download_name=path.name if as_attachment else None
    )


@blueprint.get("/split/<path:filename>")
@jwt_required()
def download_split(filename: str):
    path = _secure_path(media_store.MP3_SPLIT_DIR, filename)
    return send_file(path, mimetype="audio/mpeg", as_attachment=False)


@blueprint.get("/temp/<path:filename>")
def download_temp(filename: str):
    """PUBLIC ROUTE (conditionally): Access controlled by ALLOW_PUBLIC_TEMP_AUDIO config."""
    if not _temp_access_allowed():
        abort(401)
    path = _secure_path(media_store.MP3_TEMP_DIR, filename)
    return send_file(path, mimetype="audio/mpeg", as_attachment=False)


@blueprint.post("/snippet")
def create_snippet():
    """PUBLIC ROUTE (conditionally): Access controlled by ALLOW_PUBLIC_TEMP_AUDIO config.
    
    CSRF: Required for POST (via JWT-CSRF if user logged in).
    """
    if not _temp_access_allowed():
        abort(401)
    payload = request.get_json(silent=True) or {}
    filename = payload.get("filename")
    start = payload.get("start")
    end = payload.get("end")
    try:
        start_val = float(start)
        end_val = float(end)
    except (TypeError, ValueError):
        abort(400, "Invalid start/end values")
    if not filename:
        abort(400, "Filename required")
    try:
        snippet_path = audio_snippets.build_snippet(filename, start_val, end_val)
    except FileNotFoundError:
        abort(404, "Audio source not found")
    except ValueError as exc:
        abort(400, str(exc))
    download_name = snippet_path.name
    return send_file(snippet_path, mimetype="audio/mpeg", as_attachment=False, download_name=download_name)


@blueprint.get("/transcripts/<path:filename>")
def fetch_transcript(filename: str):
    """
    Serve transcript JSON files.
    
    PUBLIC ROUTE (conditionally): No decorator needed.
    - For authenticated users: Always allowed
    - For unauthenticated: Only if public access is enabled
    """
    # Check if user is authenticated or public access is allowed
    if not (getattr(g, "user", None) or current_app.config.get("ALLOW_PUBLIC_TRANSCRIPTS", False)):
        abort(401, "Authentication required to access transcripts")
    
    transcript = media_store.safe_transcript_path(filename)
    if transcript is None:
        abort(404)

    # Load and augment transcript JSON with a human-readable country display.
    try:
        with open(transcript, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    except Exception:
        # Fall back to sending raw file if we cannot parse it
        return send_file(transcript, mimetype="application/json", as_attachment=False)

    # Look for several possible country fields and compute display name
    raw_country = (
        data.get('country') or
        data.get('country_code') or
        data.get('countryCode') or
        data.get('country_name') or
        data.get('countryName') or
        data.get('location') or
        data.get('location_code') or
        data.get('locationCode') or
        ''
    )

    if raw_country:
        # code_to_name will normalize legacy codes and return a readable name
        try:
            display = code_to_name(str(raw_country), fallback=str(raw_country))
        except Exception:
            display = str(raw_country)
        data['country_display'] = display

    return jsonify(data)


@blueprint.post("/toggle/temp")
@jwt_required()
@require_role(Role.ADMIN)
def toggle_temp_access():
    current = current_app.config.get("ALLOW_PUBLIC_TEMP_AUDIO", False)
    current_app.config["ALLOW_PUBLIC_TEMP_AUDIO"] = not current
    return jsonify({"allow_public_temp_audio": current_app.config["ALLOW_PUBLIC_TEMP_AUDIO"]})




@blueprint.get("/play_audio/<path:filename>")
def play_audio(filename: str):
    """PUBLIC ROUTE (conditionally): Access controlled by ALLOW_PUBLIC_TEMP_AUDIO config.
    
    Legacy endpoint for audio playback with snippet generation.
    """
    start = request.args.get("start", type=float)
    end = request.args.get("end", type=float)
    token_id = request.args.get("token_id")
    snippet_type = request.args.get("type")  # 'pal' or 'ctx'
    
    if start is None or end is None:
        abort(400, "Missing start/end parameters")
    if end <= start:
        abort(400, "End time must be greater than start time")
    if not _temp_access_allowed():
        abort(401)
    try:
        snippet_path = audio_snippets.build_snippet(filename, start, end, token_id, snippet_type)
    except FileNotFoundError:
        abort(404, "Audio source not found")
    except ValueError as exc:
        abort(400, str(exc))
    download_flag = request.args.get("download")
    as_attachment = download_flag is not None
    return send_file(
        snippet_path,
        mimetype="audio/mpeg",
        as_attachment=as_attachment,
        download_name=snippet_path.name if as_attachment else None,
    )
