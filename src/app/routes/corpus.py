"""Corpus routes and search endpoints."""
from __future__ import annotations

from flask import Blueprint, Response, current_app, g, jsonify, render_template, request, redirect, url_for

from ..services.corpus_search import SearchParams, search_tokens
from ..services.blacklab_search import search_blacklab
from ..services.counters import counter_search
from ..search.cql import resolve_countries_for_include_regional
from ..services.database import open_db

blueprint = Blueprint("corpus", __name__, url_prefix="/corpus")


def _safe_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _parse_token_ids() -> list[str]:
    # POST-Feld bevorzugen, dann GET
    raw = request.form.get("token_ids") or request.args.get("token_ids", "")
    if not raw:
        return []
    # Komma-getrennte Token-IDs parsen
    return [token.strip() for token in raw.split(",") if token.strip()]


def _default_context() -> dict[str, object]:
    return {
        "query": "",
        "token_ids": "",
        "search_mode": "text",
        "results": [],
        "all_results": [],
        "total_results": 0,
        "unique_countries": 0,
        "unique_filenames": 0,
        "selected_countries": ["all"],
        "selected_speaker_types": ["all"],
        "selected_sexes": ["all"],
        "selected_speech_modes": ["all"],
        "selected_discourses": ["all"],
        "current_sort": "",
        "current_order": "asc",
        "page": 1,
        "page_size": 20,
        "total_pages": 0,
        "display_pages": [],
        "selected_tab": request.args.get("tab", "simple"),
        "error_message": "",
        "allow_public_temp_audio": current_app.config.get("ALLOW_PUBLIC_TEMP_AUDIO", False),
        "is_authenticated": getattr(g, "user", None) is not None,
    }


def _render_corpus(context: dict[str, object]) -> Response:
    template_name = "pages/corpus.html"
    print(f"DEBUG: Rendering template: {template_name}")
    print(f"DEBUG: Template folder: {current_app.template_folder}")
    return render_template(template_name, **context)


@blueprint.get("/")
def corpus_home() -> Response:
    """Corpus-Startseite mit DataTables (neue Version)
    
    PUBLIC ROUTE: No authentication required.
    User info available via g.user (set by load_user_dimensions if logged in).
    """
    # Legacy route: redirect to advanced search for now
    return redirect(url_for('advanced_search.index'))


@blueprint.route("/search", methods=["GET", "POST"])
def search() -> Response:
    """Deprecated search endpoint - redirects to corpus home.
    
    NOTE: Simple search (SQL-based) has been removed.
    Token search now uses BlackLab via /search/advanced/token/search API endpoint.
    Advanced search uses /search/advanced UI with BlackLab.
    
    This route is kept only for backward compatibility and redirects to home.
    """
    # Just render the corpus page without results
    # All searches now happen via AJAX (DataTables) through BlackLab
    # Deprecated - redirect to advanced search UI with params preserved
    params = request.args.to_dict(flat=False)
    q = request.args.get('q') or ''
    query_str = '' if not params else ('?' + '&'.join([f"{k}={v[0]}" for k, v in params.items()]))
    return redirect(url_for('advanced_search.index') + query_str)


@blueprint.get("/search/datatables")
def search_datatables() -> Response:
    """Deprecated DataTables endpoint - was used for SQL-based simple search.
    
    NOTE: This endpoint is deprecated and should not be used.
    - Simple search (SQL-based) has been removed
    - Advanced search uses /search/advanced/data API endpoint (BlackLab)
    - Token search uses /search/advanced/token/search API endpoint (BlackLab)
    
    Returns error to inform clients to use new endpoints.
    """
    # Redirect to new advanced DataTables endpoint for compatibility
    return redirect(url_for('advanced_api.data'))


@blueprint.get("/tokens")
def token_lookup() -> Response:
    """Lookup Tokens by IDs - returns objects with CANON_COLS keys.
    
    PUBLIC ROUTE: No authentication required.
    """
    import sqlite3
    from ..services.corpus_search import CANON_COLS, _get_select_columns
    
    # Deprecated token lookup route - redirect to advanced token search endpoint
    return redirect(url_for('advanced_api.token_search'))
    token_ids = [token.strip() for token in token_ids_param.split(",") if token.strip()]
    if not token_ids:
        return jsonify([])
    
    placeholders = ",".join(["?"] * len(token_ids))
    with open_db("transcription") as connection:
        # AKTIVIERE Row-Factory
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        
        # EXPLIZITE Spaltenliste statt SELECT *
        select_cols = _get_select_columns()
        # select_cols references 't.' alias by default, so alias the tokens table
        # to 't' in the FROM clause to avoid "no such column: t.token_id" errors.
        sql = f"SELECT {select_cols} FROM tokens t WHERE token_id IN ({placeholders})"
        cursor.execute(sql, token_ids)
        rows = cursor.fetchall()
    
    # Konvertiere zu Objekten mit stabilen Keys
    payload = []
    for row in rows:
        obj = {}
        for col in CANON_COLS:
            try:
                obj[col] = row[col]
            except (IndexError, KeyError):
                obj[col] = None
        payload.append(obj)
    
    return jsonify(payload)
