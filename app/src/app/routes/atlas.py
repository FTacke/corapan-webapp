"""Atlas routes - API v1."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, redirect, url_for

from ..extensions import cache
from ..services.atlas import fetch_country_stats, fetch_file_metadata

# New versioned blueprint
blueprint = Blueprint("atlas_api", __name__, url_prefix="/api/v1/atlas")

# Legacy blueprint for backwards compatibility (redirects to v1)
legacy_blueprint = Blueprint("atlas_api_legacy", __name__, url_prefix="/atlas")


@blueprint.get("/countries")
@cache.cached(timeout=3600)  # Cache for 1 hour
def countries():
    """Get country-specific statistics (cached for 1 hour)."""
    return jsonify({"countries": fetch_country_stats()})


@blueprint.get("/files")
def files():
    """Get file metadata.

    In development, avoid persisting empty responses because path fixes and
    metadata refreshes should become visible immediately.
    """
    cache_key = "atlas_files_v2"

    if not current_app.debug and not current_app.testing:
        cached = cache.get(cache_key)
        if cached is not None:
            return jsonify({"files": cached})

    files_payload = fetch_file_metadata()

    if current_app.debug or current_app.testing:
        cache.delete(cache_key)
    elif files_payload:
        cache.set(cache_key, files_payload, timeout=3600)
    else:
        cache.delete(cache_key)

    return jsonify({"files": files_payload})


@blueprint.get("/locations")
@cache.cached(timeout=3600)
def locations():
    """Return list of known locations (countries + regional capitals).

    Uses the config.export_all_to_json helper to provide a compact
    JSON-serializable representation suitable for client-side lookups.
    """
    from ..config import export_all_to_json

    return jsonify({"locations": export_all_to_json()})


# ========================================
# Legacy Routes (Backwards Compatibility)
# ========================================
# Redirect old /atlas/* endpoints to /api/v1/atlas/*


@legacy_blueprint.get("/countries")
def legacy_countries():
    """Redirect to versioned API."""
    return redirect(url_for("atlas_api.countries"), code=301)


@legacy_blueprint.get("/files")
def legacy_files():
    """Redirect to versioned API."""
    return redirect(url_for("atlas_api.files"), code=301)
