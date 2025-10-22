"""Atlas routes - API v1."""
from __future__ import annotations

from flask import Blueprint, jsonify, redirect, url_for

from ..extensions import cache
from ..services.atlas import fetch_country_stats, fetch_file_metadata, fetch_overview

# New versioned blueprint
blueprint = Blueprint("atlas_api", __name__, url_prefix="/api/v1/atlas")

# Legacy blueprint for backwards compatibility (redirects to v1)
legacy_blueprint = Blueprint("atlas_api_legacy", __name__, url_prefix="/atlas")


@blueprint.get("/overview")
@cache.cached(timeout=3600)  # Cache for 1 hour
def overview():
    """Get corpus overview statistics (cached for 1 hour)."""
    return jsonify(fetch_overview())


@blueprint.get("/countries")
@cache.cached(timeout=3600)  # Cache for 1 hour
def countries():
    """Get country-specific statistics (cached for 1 hour)."""
    return jsonify({"countries": fetch_country_stats()})


@blueprint.get("/files")
@cache.cached(timeout=3600)  # Cache for 1 hour
def files():
    """Get file metadata (cached for 1 hour)."""
    return jsonify({"files": fetch_file_metadata()})


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

@legacy_blueprint.get("/overview")
def legacy_overview():
    """Redirect to versioned API."""
    return redirect(url_for("atlas_api.overview"), code=301)


@legacy_blueprint.get("/countries")
def legacy_countries():
    """Redirect to versioned API."""
    return redirect(url_for("atlas_api.countries"), code=301)


@legacy_blueprint.get("/files")
def legacy_files():
    """Redirect to versioned API."""
    return redirect(url_for("atlas_api.files"), code=301)
