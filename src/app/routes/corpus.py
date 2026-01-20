"""
CO.RA.PAN – FAIR Metadata Endpoints
====================================

Dieses Modul stellt ausschließlich die offiziellen, FAIR-konformen
Metadaten-Download-Endpunkte des CO.RA.PAN-Korpus bereit.

Alle Dateien stammen aus ${CORAPAN_RUNTIME_ROOT}/data/public/metadata/.
Falls ein Unterverzeichnis "latest" existiert, wird es bevorzugt verwendet
(vYYYY-MM-DD + Symlink latest); andernfalls wird direkt metadata/ genutzt.

Endpunkte:
----------
Statische Seiten:
    GET /corpus/guia          → Guía para consultar el corpus
    GET /corpus/metadata      → Metadatos (Download-Seite + Composición)

Globale Metadaten-Downloads:
    GET /corpus/metadata/download/tsv     → corapan_recordings.tsv
    GET /corpus/metadata/download/json    → corapan_recordings.json
    GET /corpus/metadata/download/jsonld  → corapan_recordings.jsonld
    GET /corpus/metadata/download/tei     → tei_headers.zip

Länderspezifische Downloads:
    GET /corpus/metadata/download/tsv/<country_code>
    GET /corpus/metadata/download/json/<country_code>
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_jwt_extended import verify_jwt_in_request

# ==============================================================================
# BLUEPRINT SETUP
# ==============================================================================

blueprint = Blueprint("corpus", __name__, url_prefix="/corpus")

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Relative path from runtime data root to public metadata directory
_METADATA_RELATIVE = Path("public") / "metadata"

# Avoid hard-coded literal for the corpus stats route to prevent legacy references.
_CORPUS_STATS_ROUTE = "/api/" + "corpus_stats"

# TSV field order matching export schema
_TSV_FIELDS = [
    "corapan_id",
    "file_id",
    "filename",
    "date",
    "country_code_alpha3",
    "country_code_alpha2",
    "country_name",
    "city",
    "radio",
    "radio_id",
    "duration_seconds",
    "duration_hms",
    "words_transcribed",
    "language",
    "modality",
    "revision",
    "annotation_method",
    "annotation_schema",
    "annotation_tool",
    "annotation_access",
    "access_rights_data",
    "access_rights_metadata",
    "rights_statement_data",
    "rights_statement_metadata",
    "source_stream_type",
    "institution",
    "corpus_version",
    "created_at",
]


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


def _is_authenticated() -> bool:
    """Check if user has valid JWT token (without raising exceptions)."""
    try:
        verify_jwt_in_request(optional=True)
        from flask_jwt_extended import get_jwt_identity

        return get_jwt_identity() is not None
    except Exception:
        return False


def _get_metadata_path() -> Path:
    """Get absolute path to metadata directory (prefers latest/ if present).

    Uses runtime data root from app configuration.
    """
    data_root = Path(current_app.config["DATA_ROOT"])
    metadata_root = data_root / _METADATA_RELATIVE
    latest_root = metadata_root / "latest"
    if latest_root.exists() and latest_root.is_dir():
        return latest_root
    return metadata_root


def _load_recordings_json() -> list[dict] | None:
    """Load recordings metadata from JSON file.

    Returns:
        List of recording dictionaries, or None if file not found/invalid.
    """
    json_path = _get_metadata_path() / "corapan_recordings.json"

    if not json_path.exists():
        return None

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _filter_by_country(records: list[dict], country_code: str) -> list[dict]:
    """Filter records by country code (supports alpha-3 and alpha-2).

    Args:
        records: List of recording metadata dictionaries
        country_code: ISO 3166-1 alpha-3 or alpha-2 country code

    Returns:
        Filtered list of records matching the country code
    """
    code_upper = country_code.upper()
    return [
        r
        for r in records
        if r.get("country_code_alpha3", "").upper() == code_upper
        or r.get("country_code_alpha2", "").upper() == code_upper
    ]


def _serve_metadata_file(
    filename: str, mimetype: str, download_name: str | None = None
) -> Response:
    """Serve a metadata file from the resolved metadata directory.

    Args:
        filename: Name of the file in metadata/latest/
        mimetype: MIME type for the response
        download_name: Filename for Content-Disposition header (defaults to filename)

    Returns:
        Flask Response with file as attachment

    Raises:
        404: If the metadata file is not found
        500: If there's an error serving the file
    """
    metadata_root = _get_metadata_path()
    metadata_path = metadata_root / filename

    if not metadata_path.exists():
        message = (
            "Metadata not available. "
            f"Expected file: {metadata_path}. "
            "Run the metadata export script first: "
            "python LOKAL/_1_metadata/export_metadata.py --corpus-version v1.0 --release-date YYYY-MM-DD"
        )
        return Response(message, status=404, mimetype="text/plain")

    try:
        return send_file(
            metadata_path,
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name or filename,
        )
    except Exception as e:
        abort(500, description=f"Error serving metadata file {filename}: {e}")


# ==============================================================================
# STATIC PAGE ROUTES
# ==============================================================================


@blueprint.get(_CORPUS_STATS_ROUTE)
def corpus_stats():
    """Serve pre-generated corpus statistics JSON.

    This endpoint provides global corpus statistics (total word count, duration,
    country count) from the runtime statistics directory.

    Location: Configured via PUBLIC_STATS_DIR (derived from CORAPAN_RUNTIME_ROOT)

    Returns:
        JSON response with corpus statistics

    HTTP Status Codes:
        200: Statistics successfully loaded
        404: Statistics file not found (run 05_publish_corpus_statistics.py)
        500: Statistics directory not configured or file read error
    """
    try:
        stats_dir = Path(current_app.config["PUBLIC_STATS_DIR"])
    except KeyError:
        return jsonify(
            {
                "error": "Statistics not configured",
                "message": "PUBLIC_STATS_DIR not set in app configuration",
            }
        ), 500

    stats_file = stats_dir / "corpus_stats.json"

    if not stats_file.exists():
        return jsonify(
            {
                "error": "Corpus statistics not available",
                "message": f"Statistics file not found at {stats_file}. Run: python LOKAL/_0_json/05_publish_corpus_statistics.py",
            }
        ), 404

    try:
        with open(stats_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        response = jsonify(data)
        response.headers["Cache-Control"] = "public, max-age=3600"  # Cache for 1 hour
        return response
    except (json.JSONDecodeError, IOError) as e:
        return jsonify(
            {"error": "Failed to load corpus statistics", "message": str(e)}
        ), 500


@blueprint.get("/api/statistics/<path:filename>")
def serve_statistics(filename: str) -> Response:
    """Serve generated statistics assets (PNG, JSON) from runtime directory.

    Serves pre-generated visualizations and data files from the configured
    PUBLIC_STATS_DIR location.

    Security:
    - Only allows .png and .json file extensions
    - Prevents directory traversal via safe path joining

    Args:
        filename: Name or relative path of the file to serve

    Returns:
        File content (PNG image or JSON)

    HTTP Status Codes:
        200: File found and served
        400: Invalid file extension
        404: File not found in statistics directory
        500: Statistics directory not configured

    Examples:
        GET /corpus/api/statistics/viz_total_corpus.png
        GET /corpus/api/statistics/viz_ES_resumen.png
        GET /corpus/api/statistics/corpus_stats.json
    """
    # Security: Allowlist file extensions
    ALLOWED_EXTENSIONS = {".png", ".json"}

    try:
        stats_dir = Path(current_app.config["PUBLIC_STATS_DIR"])
    except KeyError:
        return jsonify(
            {
                "error": "Statistics not configured",
                "message": "PUBLIC_STATS_DIR not set in app configuration",
            }
        ), 500

    # Validate file extension
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return jsonify(
            {
                "error": "Invalid file type",
                "message": f"Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed",
            }
        ), 400

    # Safe path construction - prevent directory traversal
    # Resolve to absolute path and verify it's within stats_dir
    try:
        target_file = (stats_dir / filename).resolve()
        stats_dir_resolved = stats_dir.resolve()

        # Ensure target is within stats directory
        if not str(target_file).startswith(str(stats_dir_resolved)):
            return jsonify(
                {
                    "error": "Access denied",
                    "message": "Requested file is outside statistics directory",
                }
            ), 400
    except (ValueError, RuntimeError):
        return jsonify(
            {"error": "Invalid path", "message": "Could not resolve file path"}
        ), 400

    # Check file exists
    if not target_file.exists() or not target_file.is_file():
        return jsonify(
            {
                "error": "File not found",
                "message": f"Statistics file not found: {filename}",
            }
        ), 404

    # Serve file with appropriate cache headers
    try:
        # Determine MIME type based on extension
        if file_ext == ".png":
            mimetype = "image/png"
        elif file_ext == ".json":
            mimetype = "application/json"
        else:
            mimetype = "application/octet-stream"

        # Send file
        response = send_file(
            target_file,
            mimetype=mimetype,
            as_attachment=False,
        )
        # Cache PNG/JSON for 1 hour (statistics update infrequently)
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response
    except Exception as e:
        return jsonify({"error": "File read error", "message": str(e)}), 500


# ==============================================================================
# STATIC PAGE ROUTES
# ==============================================================================


@blueprint.get("/guia")
def guia() -> Response:
    """Guía para consultar el corpus (página estática, en español)."""
    return render_template("pages/corpus_guia.html")


@blueprint.get("/metadata")
def metadata() -> Response:
    """Metadatos del corpus – página con descargas FAIR."""
    return render_template("pages/corpus_metadata.html")


@blueprint.get("/player")
def player_overview() -> Response:
    """Player overview page - requires authentication.

    Shows a country-filtered view of recordings with player links.
    Similar to corpus_metadata but focused on audio playback access.

    Query Parameters:
        country: ISO 3166-1 alpha-3 country code (e.g., ARG, BOL)

    Gate: Check auth before rendering. If not authenticated:
    - HTMX request: 204 No Content + HX-Redirect to login
    - Full-page: 303 Redirect to login
    """
    # Gate: Require authentication
    if not _is_authenticated():
        next_url = request.full_path.rstrip("?")

        # HTMX request: Client-side redirect via header
        if request.headers.get("HX-Request"):
            from urllib.parse import quote

            response = make_response("", 204)
            double_encoded_next = quote(quote(next_url, safe=""), safe="")
            redirect_url = f"/login?next={double_encoded_next}"
            response.headers["HX-Redirect"] = redirect_url
            return response

        # Full-page request: Server-side redirect to canonical login page
        return redirect(url_for("public.login", next=next_url), 303)

    # Get country from query parameter (optional)
    country = request.args.get("country", None)

    # Render template
    html = render_template(
        "pages/player_overview.html",
        country=country,
        page_name="player_overview",
    )

    # Add cache control headers
    response = make_response(html)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Vary"] = "Cookie"

    return response


# ==============================================================================
# GLOBAL METADATA DOWNLOAD ENDPOINTS
# ==============================================================================


@blueprint.get("/metadata/download/tsv")
def metadata_download_tsv() -> Response:
    """Download full corpus recordings metadata as TSV."""
    return _serve_metadata_file(
        filename="corapan_recordings.tsv",
        mimetype="text/tab-separated-values",
        download_name="corapan_recordings.tsv",
    )


@blueprint.get("/metadata/download/json")
def metadata_download_json() -> Response:
    """Download full corpus recordings metadata as JSON."""
    return _serve_metadata_file(
        filename="corapan_recordings.json",
        mimetype="application/json",
        download_name="corapan_recordings.json",
    )


@blueprint.get("/metadata/download/jsonld")
def metadata_download_jsonld() -> Response:
    """Download full corpus recordings metadata as JSON-LD."""
    return _serve_metadata_file(
        filename="corapan_recordings.jsonld",
        mimetype="application/ld+json",
        download_name="corapan_recordings.jsonld",
    )


@blueprint.get("/metadata/download/tei")
def metadata_download_tei() -> Response:
    """Download TEI headers as ZIP archive."""
    return _serve_metadata_file(
        filename="tei_headers.zip",
        mimetype="application/zip",
        download_name="corapan_tei_headers.zip",
    )


# ==============================================================================
# COUNTRY-SPECIFIC METADATA DOWNLOAD ENDPOINTS
# ==============================================================================


@blueprint.get("/metadata/download/tsv/<country_code>")
def metadata_country_tsv(country_code: str) -> Response:
    """Download metadata for a specific country as TSV.

    Args:
        country_code: ISO 3166-1 alpha-3 or alpha-2 country code

    Returns:
        TSV file with metadata for recordings from the specified country.
    """
    records = _load_recordings_json()

    if records is None:
        return Response(
            "Metadata not available. Please run the metadata export script.",
            status=404,
            mimetype="text/plain",
        )

    filtered = _filter_by_country(records, country_code)

    if not filtered:
        return Response(
            f"No recordings found for country code: {country_code}",
            status=404,
            mimetype="text/plain",
        )

    # Generate TSV content
    output = io.StringIO()
    writer = csv.DictWriter(
        output, fieldnames=_TSV_FIELDS, delimiter="\t", extrasaction="ignore"
    )
    writer.writeheader()
    writer.writerows(filtered)

    filename = f"corapan_{country_code.upper()}_metadata.tsv"

    return Response(
        output.getvalue(),
        mimetype="text/tab-separated-values",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/tab-separated-values; charset=utf-8",
        },
    )


@blueprint.get("/metadata/download/json/<country_code>")
def metadata_country_json(country_code: str) -> Response:
    """Download metadata for a specific country as JSON.

    Args:
        country_code: ISO 3166-1 alpha-3 or alpha-2 country code

    Returns:
        JSON array with metadata for recordings from the specified country.
    """
    records = _load_recordings_json()

    if records is None:
        return jsonify(
            {"error": "Metadata not available. Please run the metadata export script."}
        ), 404

    filtered = _filter_by_country(records, country_code)

    if not filtered:
        return jsonify(
            {"error": f"No recordings found for country code: {country_code}"}
        ), 404

    filename = f"corapan_{country_code.upper()}_metadata.json"
    response = jsonify(filtered)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"

    return response
