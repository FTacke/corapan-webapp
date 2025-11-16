"""Corpus routes and search endpoints."""
from __future__ import annotations

from flask import Blueprint, Response, current_app, g, jsonify, render_template, request

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
    context = _default_context()
    return render_template("pages/corpus.html", **context)


@blueprint.route("/search", methods=["GET", "POST"])
def search() -> Response:
    """Suchendpoint für Corpus-Seite (GET & POST)
    
    PUBLIC ROUTE: No authentication required.
    CSRF: Required for POST method (via JWT-CSRF).
    """
    counter_search.increment()
    
    # Parameter aus GET oder POST lesen
    data_source = request.form if request.method == "POST" else request.args
    
    # search_mode: Override hat Priorität, dann normaler Wert
    search_mode_override = data_source.get("search_mode_override", "")
    search_mode = search_mode_override if search_mode_override else data_source.get("search_mode", "text")
    
    # Handle country/region filtering
    # Compute countries list with include_regional semantics
    countries = data_source.getlist("country_code")
    include_regional = data_source.get("include_regional") == "1"
    countries = resolve_countries_for_include_regional(countries, include_regional)
    
    params = SearchParams(
        query=data_source.get("query", ""),
        search_mode=search_mode,
        sensitive=_safe_int(data_source.get("sensitive", 1), 1),
        token_ids=_parse_token_ids(),
        countries=countries if countries else None,
        speaker_types=data_source.getlist("speaker_type"),
        sexes=data_source.getlist("sex"),
        speech_modes=data_source.getlist("speech_mode"),
        discourses=data_source.getlist("discourse"),
        page=_safe_int(data_source.get("page"), 1),
        page_size=_safe_int(data_source.get("page_size"), 25),
        sort=data_source.get("sort"),
        order=data_source.get("order", "asc"),
    )
    
    # Bei Token-Suche: Validierung
    if params.search_mode == "token_ids" and not params.token_ids:
        context = _default_context()
        context["error_message"] = "Por favor ingresa al menos un Token-ID"
        context["active_tab"] = "tab-token"
        return _render_corpus(context)
    
    # Decide to use BlackLab for text/lemma search, and SQLite for direct token lookups
    use_blacklab = True
    if params.search_mode == "token_ids":
        use_blacklab = False
    service_result = None
    if use_blacklab and params.query.strip():
        # Convert params to a dict compatible with blacklab_search
        bls_params = {
            "query": params.query,
            "search_mode": params.search_mode,
            "sensitive": params.sensitive,
            "country_code": params.countries or [],
            "speaker_type": params.speaker_types or [],
            "sex": params.sexes or [],
            "speech_mode": params.speech_modes or [],
            "discourse": params.discourses or [],
            "page": params.page,
            "page_size": params.page_size,
            "include_regional": request.values.get("include_regional"),
        }
        try:
            service_result = search_blacklab(bls_params)
        except Exception as e:
            current_app.logger.error(f"BlackLab search failed: {e}")
            # Fallback to SQLite search
            service_result = search_tokens(params)
    else:
        service_result = search_tokens(params)
    context = _default_context()
    
    # Active tab bestimmen
    active_tab = "tab-simple"
    if params.search_mode == "token_ids":
        active_tab = "tab-token"
    
    context.update(
        {
            "query": params.query,
            "token_ids": ",".join(params.token_ids),
            "search_mode": params.search_mode,
            "active_tab": active_tab,
            "results": service_result["items"],
            "all_results": service_result["all_items"],
            "total_results": service_result["total"],
            "unique_countries": service_result["unique_countries"],
            "unique_filenames": service_result["unique_files"],
            "selected_countries": params.countries or ["all"],
            "selected_speaker_types": params.speaker_types or ["all"],
            "selected_sexes": params.sexes or ["all"],
            "selected_speech_modes": params.speech_modes or ["all"],
            "selected_discourses": params.discourses or ["all"],
            "current_sort": params.sort or "",
            "current_order": (params.order.lower() if params.order else "asc"),
            "page": service_result["page"],
            "page_size": service_result["page_size"],
            "total_pages": service_result["total_pages"],
            "display_pages": service_result["display_pages"],
        }
    )
    return _render_corpus(context)


@blueprint.get("/search/datatables")
def search_datatables() -> Response:
    """Server-side DataTables endpoint for corpus search.
    
    PUBLIC ROUTE: No authentication required.
    
    Handles DataTables AJAX requests with server-side processing.
    Expects DataTables parameters: start, length, search, order, etc.
    """
    # DataTables parameters
    draw = _safe_int(request.args.get("draw"), 1)
    start = _safe_int(request.args.get("start"), 0)
    length = _safe_int(request.args.get("length"), 25)
    
    # DataTables search parameter (search within results)
    dt_search = request.args.get("search[value]", "").strip()
    
    # Search parameters (from original search)
    query = request.args.get("query", "").strip()
    search_mode = request.args.get("search_mode", "text")
    token_ids = _parse_token_ids()
    
    # Filter parameters
    # Regional codes that should be excluded by default
    regional_codes = ['ARG-CHU', 'ARG-CBA', 'ARG-SDE', 'ESP-CAN', 'ESP-SEV']
    national_codes = ['ARG', 'BOL', 'CHL', 'COL', 'CRI', 'CUB', 'ECU', 'ESP', 'GTM', 
                      'HND', 'MEX', 'NIC', 'PAN', 'PRY', 'PER', 'DOM', 'SLV', 'URY', 'USA', 'VEN']
    
    countries = request.args.getlist("country_code")
    include_regional = request.args.get("include_regional") == "1"
    countries = resolve_countries_for_include_regional(countries, include_regional)
    speaker_types = request.args.getlist("speaker_type")
    sexes = request.args.getlist("sex")
    speech_modes = request.args.getlist("speech_mode")
    discourses = request.args.getlist("discourse")
    
    # DEBUG: Log received filters
    print(f"DEBUG DataTables - Received filters:")
    print(f"  countries: {countries}")
    print(f"  include_regional: {include_regional}")
    print(f"  speaker_types: {speaker_types}")
    print(f"  sexes: {sexes}")
    print(f"  speech_modes: {speech_modes}")
    print(f"  discourses: {discourses}")
    
    # If nothing selected, use defaults based on include_regional
    if not countries:
        if include_regional:
            # Include all: 19 national + 5 regional
            countries = national_codes + regional_codes
        else:
            # Only national capitals
            countries = national_codes
    elif not include_regional:
        # If user selected countries but checkbox is off, exclude any regional codes
        countries = [c for c in countries if c not in regional_codes]
    
    # DEBUG: Log processed countries
    print(f"DEBUG DataTables - Processed countries: {countries}")
    
    # DataTables ordering
    order_col_index = _safe_int(request.args.get("order[0][column]"), 0)
    order_dir = request.args.get("order[0][dir]", "asc")
    
    # DEBUG: Log ordering
    print(f"DEBUG DataTables - Ordering: column={order_col_index}, dir={order_dir}")
    
    # Map DataTables column index to sort field
    # Order: #, Ctx.←, Palabra, Ctx.→, Audio, País, Hablante, Sexo, Modo, Discurso, Token-ID, Archivo
    column_map = {
        0: "",                  # Row number (no sort)
        1: "",                  # Ctx.← (no sort)
        2: "text",              # Palabra
        3: "",                  # Ctx.→ (no sort)
        4: "",                  # Audio (no sort)
        5: "country_code",      # País
        6: "speaker_type",      # Hablante
        7: "sex",               # Sexo
        8: "mode",              # Modo
        9: "discourse",         # Discurso
        10: "token_id",         # Token-ID
        11: "filename",         # Archivo (combined icon + player)
    }
    sort_field = column_map.get(order_col_index, "")
    
    # DEBUG: Log sort field
    print(f"DEBUG DataTables - Sort field: {sort_field} (from column {order_col_index})")
    
    # Calculate page number
    page = (start // length) + 1 if length > 0 else 1
    
    # Build search params
    params = SearchParams(
        query=query,
        search_mode=search_mode,
        sensitive=_safe_int(request.args.get("sensitive", 1), 1),
        token_ids=token_ids,
        countries=countries if countries else None,
        speaker_types=speaker_types if speaker_types else None,
        sexes=sexes if sexes else None,
        speech_modes=speech_modes if speech_modes else None,
        discourses=discourses if discourses else None,
        sort=sort_field,
        order=order_dir,
        page=page,
        page_size=length,
        table_search=dt_search,  # Pass DataTables search
    )
    
    # Execute search
    counter_search.increment()
    # Use BlackLab for text/lemma searches; fallback to SQLite for token_ids
    use_blacklab = True
    if params.search_mode == "token_ids":
        use_blacklab = False
    if use_blacklab and params.query.strip():
        bls_params = {
            "query": params.query,
            "search_mode": params.search_mode,
            "sensitive": params.sensitive,
            "country_code": params.countries or [],
            "speaker_type": params.speaker_types or [],
            "sex": params.sexes or [],
            "speech_mode": params.speech_modes or [],
            "discourse": params.discourses or [],
            "page": page,
            "page_size": length,
            "include_regional": request.args.get("include_regional"),
            "table_search": dt_search,
        }
        try:
            service_result = search_blacklab(bls_params)
        except Exception as e:
            current_app.logger.error(f"BlackLab datatables search failed: {e}")
            service_result = search_tokens(params)
    else:
        service_result = search_tokens(params)
    
    # Format for DataTables - NOW WITH OBJECT MODE
    # DataTables kann sowohl Arrays als auch Objekte verarbeiten.
    # Objekt-Mode ist robuster gegen Spaltenreihenfolge-Änderungen.
    from ..services.corpus_search import CANON_COLS
    
    data = []
    for idx, item in enumerate(service_result["items"], start=start + 1):
        # Nutze die stabilen Keys aus CANON_COLS + zusätzliche Helper-Felder
        row_obj = {
            # Aus CANON_COLS
            "row_number": idx,                      # Helper: Zeilennummer
            "token_id": item.get("token_id", ""),
            "filename": item.get("filename", ""),
            "country_code": item.get("country_code", ""),
            "radio": item.get("radio", ""),
            "date": item.get("date", ""),
            "speaker_type": item.get("speaker_type", ""),
            "sex": item.get("sex", ""),
            "mode": item.get("mode", ""),
            "discourse": item.get("discourse", ""),
            "text": item.get("text", ""),            # Suchresultat (evt. Multi-Word)
            "start": item.get("start", 0),
            "end": item.get("end", 0),
            "context_left": item.get("context_left", ""),
            "context_right": item.get("context_right", ""),
            "context_start": item.get("context_start", 0),
            "context_end": item.get("context_end", 0),
            "lemma": item.get("lemma", ""),
            # Zusätzliche Helper-Felder
            "audio_available": item.get("audio_available", False),
            "word_count": item.get("word_count", 1),
        }
        data.append(row_obj)
    
    return jsonify({
        "draw": draw,
        "recordsTotal": service_result["total"],
        "recordsFiltered": service_result["total"],
        "data": data,
    })


@blueprint.get("/tokens")
def token_lookup() -> Response:
    """Lookup Tokens by IDs - returns objects with CANON_COLS keys.
    
    PUBLIC ROUTE: No authentication required.
    """
    import sqlite3
    from ..services.corpus_search import CANON_COLS, _get_select_columns
    
    token_ids_param = request.args.get("token_ids", "")
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
