"""Corpus routes and search endpoints."""
from __future__ import annotations

from flask import Blueprint, Response, current_app, g, jsonify, render_template, request
from flask_jwt_extended import jwt_required

from ..services.corpus_search import SearchParams, search_tokens
from ..services.counters import counter_search
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
@jwt_required(optional=True)
def corpus_home() -> Response:
    """Corpus-Startseite mit DataTables (neue Version)"""
    context = _default_context()
    return render_template("pages/corpus.html", **context)


@blueprint.route("/search", methods=["GET", "POST"])
@jwt_required(optional=True)
def search() -> Response:
    """Suchendpoint für Corpus-Seite (GET & POST)"""
    counter_search.increment()
    
    # Parameter aus GET oder POST lesen
    data_source = request.form if request.method == "POST" else request.args
    
    # search_mode: Override hat Priorität, dann normaler Wert
    search_mode_override = data_source.get("search_mode_override", "")
    search_mode = search_mode_override if search_mode_override else data_source.get("search_mode", "text")
    
    # Handle country/region filtering
    # Regional codes that should be excluded by default
    regional_codes = ['ARG-CHU', 'ARG-CBA', 'ARG-SDE', 'ESP-CAN', 'ESP-SEV']
    national_codes = ['ARG', 'BOL', 'CHL', 'COL', 'CRI', 'CUB', 'ECU', 'ESP', 'GTM', 
                      'HND', 'MEX', 'NIC', 'PAN', 'PRY', 'PER', 'DOM', 'SLV', 'URY', 'VEN']
    
    countries = data_source.getlist("country_code")
    include_regional = data_source.get("include_regional") == "1"
    
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
    
    params = SearchParams(
        query=data_source.get("query", ""),
        search_mode=search_mode,
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
@jwt_required(optional=True)
def search_datatables() -> Response:
    """Server-side DataTables endpoint for corpus search.
    
    Handles DataTables AJAX requests with server-side processing.
    Expects DataTables parameters: start, length, search, order, etc.
    """
    # DataTables parameters
    draw = _safe_int(request.args.get("draw"), 1)
    start = _safe_int(request.args.get("start"), 0)
    length = _safe_int(request.args.get("length"), 25)
    
    # Search parameters (from original search)
    query = request.args.get("query", "").strip()
    search_mode = request.args.get("search_mode", "text")
    token_ids = _parse_token_ids()
    
    # Filter parameters
    # Regional codes that should be excluded by default
    regional_codes = ['ARG-CHU', 'ARG-CBA', 'ARG-SDE', 'ESP-CAN', 'ESP-SEV']
    national_codes = ['ARG', 'BOL', 'CHL', 'COL', 'CRI', 'CUB', 'ECU', 'ESP', 'GTM', 
                      'HND', 'MEX', 'NIC', 'PAN', 'PRY', 'PER', 'DOM', 'SLV', 'URY', 'VEN']
    
    countries = request.args.getlist("country_code")
    include_regional = request.args.get("include_regional") == "1"
    speaker_types = request.args.getlist("speaker_type")
    sexes = request.args.getlist("sex")
    speech_modes = request.args.getlist("speech_mode")
    discourses = request.args.getlist("discourse")
    
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
    
    # DataTables ordering
    order_col_index = _safe_int(request.args.get("order[0][column]"), 0)
    order_dir = request.args.get("order[0][dir]", "asc")
    
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
    
    # Calculate page number
    page = (start // length) + 1 if length > 0 else 1
    
    # Build search params
    params = SearchParams(
        query=query,
        search_mode=search_mode,
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
    )
    
    # Execute search
    counter_search.increment()
    service_result = search_tokens(params)
    
    # Format for DataTables
    # Order must match HTML table columns: #, Ctx.←, Palabra, Ctx.→, Audio, País, Hablante, Sexo, Modo, Discurso, Token-ID, Arch., Emis.
    data = []
    for idx, item in enumerate(service_result["items"], start=start + 1):
        data.append([
            idx,                                    # 0: Row number (#)
            item.get("context_left", ""),           # 1: Ctx.← 
            item.get("text", ""),                   # 2: Palabra
            item.get("context_right", ""),          # 3: Ctx.→
            item.get("audio_available", False),     # 4: Audio (boolean for rendering)
            item.get("country_code", ""),           # 5: País
            item.get("speaker_type", ""),           # 6: Hablante
            item.get("sex", ""),                    # 7: Sexo
            item.get("mode", ""),                   # 8: Modo
            item.get("discourse", ""),              # 9: Discurso
            item.get("token_id", ""),               # 10: Token-ID
            item.get("filename", ""),               # 11: Arch. (filename for icon)
            # Hidden fields for audio/player functionality:
            item.get("start", 0),                   # 12: word start time
            item.get("end", 0),                     # 13: word end time
            item.get("context_start", 0),           # 14: context start time
            item.get("context_end", 0),             # 15: context end time
        ])
    
    return jsonify({
        "draw": draw,
        "recordsTotal": service_result["total"],
        "recordsFiltered": service_result["total"],
        "data": data,
    })


@blueprint.get("/tokens")
@jwt_required(optional=True)
def token_lookup() -> Response:
    token_ids_param = request.args.get("token_ids", "")
    token_ids = [token.strip() for token in token_ids_param.split(",") if token.strip()]
    if not token_ids:
        return jsonify([])
    placeholders = ",".join(["?"] * len(token_ids))
    with open_db("transcription") as connection:
        cursor = connection.cursor()
        cursor.execute(
            f"SELECT * FROM tokens WHERE token_id IN ({placeholders})",
            token_ids,
        )
        rows = cursor.fetchall()
    payload = []
    for row in rows:
        payload.append(
            {
                "token_id": row[1],
                "filename": row[2],
                "country": row[3],
                "sex": row[7],
                "speaker": row[6],
                "mode": row[8],
                "word": row[10],
                "context_left": row[13],
                "context_right": row[14],
                "start": row[15],
                "end": row[16],
            }
        )
    return jsonify(payload)
