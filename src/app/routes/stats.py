"""Statistics API endpoints."""

from __future__ import annotations

import hashlib
import json
import os
import warnings
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, Response, current_app, jsonify, request

from ..extensions import limiter
from ..services.stats_aggregator import StatsParams, aggregate_stats

blueprint = Blueprint("stats", __name__, url_prefix="/api")


def _resolve_data_root() -> Path:
    """Resolve runtime data root from CORAPAN_RUNTIME_ROOT (dev fallback supported)."""
    env_name = (os.getenv("FLASK_ENV") or os.getenv("APP_ENV") or "production").lower()
    is_dev = env_name in ("development", "dev")
    runtime_root = os.getenv("CORAPAN_RUNTIME_ROOT")

    if runtime_root:
        return Path(runtime_root) / "data"
    if is_dev:
        data_root = Path(__file__).resolve().parents[3] / "runtime" / "corapan" / "data"
        warnings.warn(
            "CORAPAN_RUNTIME_ROOT not configured. Defaulting to repo-local runtime path for development: "
            f"{data_root}",
            RuntimeWarning,
        )
        return data_root
    raise RuntimeError(
        "CORAPAN_RUNTIME_ROOT environment variable not configured.\n"
        "Runtime data is required for stats cache.\n\n"
        "Options:\n"
        "  1. Set CORAPAN_RUNTIME_ROOT (preferred):\n"
        "     export CORAPAN_RUNTIME_ROOT=/runtime/path\n"
        "     # Then data paths resolve to ${CORAPAN_RUNTIME_ROOT}/data\n"
    )


# Cache directory for stats responses (runtime data)
STATS_CACHE_DIR = _resolve_data_root() / "stats_temp"
CACHE_TTL_SECONDS = 120  # 2 minutes


def _ensure_cache_dir() -> None:
    """Ensure cache directory exists."""
    STATS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _normalize_params(args: dict) -> dict:
    """Normalize query parameters for consistent caching."""
    # Regional codes that should be excluded by default
    regional_codes = ["ARG-CHU", "ARG-CBA", "ARG-SDE", "ESP-CAN", "ESP-SEV"]
    national_codes = [
        "ARG",
        "BOL",
        "CHL",
        "COL",
        "CRI",
        "CUB",
        "ECU",
        "ESP",
        "GTM",
        "HND",
        "MEX",
        "NIC",
        "PAN",
        "PRY",
        "PER",
        "DOM",
        "SLV",
        "URY",
        "USA",
        "VEN",
    ]

    countries = args.getlist("pais") if "pais" in args else []
    include_regional = args.get("include_regional") == "1"

    # Apply same logic as in corpus.search()
    if not countries:
        if include_regional:
            countries = national_codes + regional_codes
        else:
            countries = national_codes
    elif not include_regional:
        # If user selected countries but checkbox is off, exclude any regional codes
        countries = [c for c in countries if c not in regional_codes]

    normalized = {
        "query": args.get("q", "").strip(),
        "search_mode": args.get("mode", "text"),
        "token_ids": sorted(args.getlist("token_ids")) if "token_ids" in args else [],
        "countries": sorted(countries),  # Apply regional filter logic
        "include_regional": include_regional,  # Store for cache key
        "speaker_types": sorted(args.getlist("speaker")) if "speaker" in args else [],
        "sexes": sorted(args.getlist("sexo")) if "sexo" in args else [],
        "speech_modes": sorted(args.getlist("modo")) if "modo" in args else [],
        "discourses": sorted(args.getlist("discourse")) if "discourse" in args else [],
        "country_detail": args.get(
            "country_detail", ""
        ).strip(),  # For per-country filtering
    }
    return normalized


def _compute_cache_key(params: dict) -> str:
    """Compute stable cache key from normalized parameters."""
    param_json = json.dumps(params, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(param_json.encode("utf-8")).hexdigest()[:16]


def _get_cached_response(cache_key: str) -> tuple[dict | None, str | None]:
    """
    Retrieve cached response if still valid.

    Returns:
        Tuple of (cached_data, etag) or (None, None) if cache miss/expired.
    """
    cache_file = STATS_CACHE_DIR / f"{cache_key}.json"

    if not cache_file.exists():
        return None, None

    # Check TTL
    mtime = cache_file.stat().st_mtime
    age = datetime.now(timezone.utc).timestamp() - mtime

    if age > CACHE_TTL_SECONDS:
        # Expired - delete and return miss
        try:
            cache_file.unlink()
        except OSError:
            pass
        return None, None

    # Valid cache - load and return
    try:
        with open(cache_file, encoding="utf-8") as f:
            data = json.load(f)
        etag = f'W/"{cache_key}"'
        return data, etag
    except (OSError, json.JSONDecodeError):
        return None, None


def _save_cached_response(cache_key: str, data: dict) -> None:
    """Save response to cache."""
    _ensure_cache_dir()
    cache_file = STATS_CACHE_DIR / f"{cache_key}.json"

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except OSError as e:
        current_app.logger.warning(f"Failed to cache stats response: {e}")


@blueprint.get("/stats")
@limiter.limit("60 per minute")
def get_stats() -> Response:
    """
    Aggregate corpus statistics based on search filters.

    Query Parameters:
        q: Search query string
        mode: Search mode (text, text_exact, lemma, lemma_exact)
        pais: Country code(s) - can be repeated
        speaker: Speaker type(s) - can be repeated
        sexo: Sex filter(s) - can be repeated
        modo: Speech mode(s) - can be repeated
        discourse: Discourse type(s) - can be repeated
        token_ids: Token ID(s) - can be repeated

    Returns:
        JSON with total count and breakdowns by dimension.
        Each dimension includes:
        - key: category identifier
        - n: absolute count
        - p: proportion (0-1)

    Headers:
        ETag: Weak entity tag for caching
        Cache-Control: public, max-age=60

    Rate Limit:
        60 requests per minute per IP
    """
    # Normalize parameters
    normalized = _normalize_params(request.args)
    cache_key = _compute_cache_key(normalized)

    # Check cache
    cached_data, etag = _get_cached_response(cache_key)

    # ETag conditional request support
    if etag and request.headers.get("If-None-Match") == etag:
        return Response(status=304)

    if cached_data:
        response = jsonify(cached_data)
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=60"
        return response

    # Cache miss - compute stats
    params = StatsParams(
        query=normalized["query"],
        search_mode=normalized["search_mode"],
        token_ids=normalized["token_ids"],
        countries=normalized["countries"],
        speaker_types=normalized["speaker_types"],
        sexes=normalized["sexes"],
        speech_modes=normalized["speech_modes"],
        discourses=normalized["discourses"],
        country_detail=normalized["country_detail"],
    )

    try:
        stats = aggregate_stats(params)

        # Add metadata
        result = {
            **stats,
            "meta": {
                "query": normalized,
                "generatedAt": datetime.now(timezone.utc).isoformat(),
            },
        }

        # Cache result
        _save_cached_response(cache_key, result)

        # Build response
        etag = f'W/"{cache_key}"'
        response = jsonify(result)
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=60"

        return response

    except Exception as e:
        current_app.logger.error(f"Stats aggregation error: {e}", exc_info=True)
        return jsonify(
            {"error": "internal_error", "message": "Failed to compute statistics"}
        ), 500


# Ensure cache directory exists on import
try:
    _ensure_cache_dir()
except Exception as e:
    # Log but don't crash app startup
    import logging

    logging.warning(f"Failed to create stats cache directory: {e}")
