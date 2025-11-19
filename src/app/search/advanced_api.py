"""
Advanced Search API Endpoints - DataTables JSON and Export.

Provides:
- GET /search/advanced/data: DataTables Server-Side endpoint
- GET /search/advanced/export: Streaming CSV/TSV export
"""
from __future__ import annotations

import csv
import io
import json
import logging
import os
from pathlib import Path
from typing import Generator, Optional
from collections import Counter

import httpx
from flask import Blueprint, jsonify, request, Response, current_app

from ..services.collocations import get_collocations
from .cql import build_cql, build_filters, filters_to_blacklab_query, build_cql_with_speaker_filter, resolve_countries_for_include_regional
from .cql_validator import validate_cql_pattern, validate_filter_values, CQLValidationError  # Punkt 3
from .speaker_utils import map_speaker_attributes
from ..extensions import limiter
from ..extensions.http_client import get_http_client, BLS_BASE_URL
from ..services.database import open_db

logger = logging.getLogger(__name__)

bp = Blueprint("advanced_api", __name__, url_prefix="/search/advanced")

# Limits and caps
MAX_HITS_PER_PAGE = 5000  # Fetch all hits from BLS so Python can filter them properly
GLOBAL_HITS_CAP = 50000
MAX_WORDS_AROUND_HIT = 40




# Load docmeta.jsonl for metadata lookup (file_id -> metadata)
def _load_docmeta():
    """Load document metadata from docmeta.jsonl."""
    docmeta_path = Path(__file__).parent.parent.parent.parent / "data" / "blacklab_export" / "docmeta.jsonl"
    docmeta = {}
    country_codes_by_parent = {}
    
    if docmeta_path.exists():
        try:
            with open(docmeta_path, 'r', encoding='utf-8') as f:
                for line in f:
                    doc = json.loads(line)
                    file_id = doc.get("file_id")
                    if file_id:
                        # Normalize file_id keys by stripping whitespace
                        docmeta[file_id.strip()] = doc
                    
                    # Build parent -> all codes mapping
                    parent = (doc.get("country_parent_code") or doc.get("country_code") or "").upper()
                    code = (doc.get("country_code") or "").upper()
                    if parent and code:
                        country_codes_by_parent.setdefault(parent, set()).add(code)
            
            logger.info(f"Loaded {len(docmeta)} document metadata entries")
            logger.info(f"Built country codes mapping for {len(country_codes_by_parent)} parents")
        except Exception as e:
            logger.warning(f"Failed to load docmeta.jsonl: {e}")
    return docmeta, country_codes_by_parent




# Cache docmeta at module level
_DOCMETA_CACHE, COUNTRY_CODES_BY_PARENT = _load_docmeta()
EXPORT_CHUNK_SIZE = 1000

# Export streaming configuration
EXPORT_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0)
EXPORT_CHUNK_BYTES = 8192


def _build_bls_url(corpus: str = "corapan") -> str:
    """Build BlackLab Server base URL."""
    return f"/bls/{corpus}"


def _make_bls_request(
    path: str,
    params: dict,
    method: str = "GET",
    timeout_override: Optional[float] = None
) -> httpx.Response:
    """
    Make request to BlackLab Server with proper error handling.
    
    Args:
        path: BLS endpoint path (e.g., "/corpora/corapan/hits" or "corpora/corapan/hits")
        params: Query parameters
        method: HTTP method
        timeout_override: Override default timeout (seconds)
        
    Returns:
        httpx.Response
        
    Raises:
        httpx.TimeoutException: On timeout
        httpx.HTTPStatusError: On HTTP error
    """
    client = get_http_client()
    
    # Build absolute URL for BLS request
    # Ensure path is clean (remove leading /bls/ if present for legacy compatibility)
    if path.startswith("/bls/"):
        path = path[4:]  # Remove "/bls" prefix, keep "/"
    elif path.startswith("bls/"):
        path = "/" + path[4:]  # Convert "bls/..." to "/..."
    elif not path.startswith("/"):
        path = "/" + path  # Ensure leading slash
    
    # BlackLab v5 API: ensure /corpora/ prefix for corpus endpoints
    # Convert old v4 paths like /corapan/hits to /corpora/corapan/hits
    if path.startswith("/corapan/"):
        path = "/corpora" + path
    
    # Construct full URL
    full_url = f"{BLS_BASE_URL}{path}"
    
    # Always request JSON from BlackLab (v5 defaults to HTML without Accept header)
    headers = {"Accept": "application/json"}
    
    try:
        if method.upper() == "GET":
            response = client.get(full_url, params=params, headers=headers)
        else:
            response = client.request(method.upper(), full_url, params=params, headers=headers)
        
        response.raise_for_status()
        logger.debug(f"BLS {method} {path}: {response.status_code} ({len(response.content)} bytes)")
        return response

        
        
    except httpx.TimeoutException:
        logger.error(f"BLS timeout on {path}")
        raise
    except httpx.HTTPStatusError as e:
        logger.error(f"BLS error on {path}: {e.response.status_code} - {e.response.text[:200]}")
        raise
    except Exception as e:
        logger.error(f"BLS request failed on {path}: {type(e).__name__}: {str(e)}")
        raise


def _enrich_hits_with_docmeta(items: list, hits: list, docinfos: dict, docmeta_cache: dict) -> list:
    """
    Enrich canonical items with docmeta information and speaker attribute mapping.
    - Map docPid -> file_id using docInfos if present
    - Lookup docmeta in docmeta_cache to get country_code, radio, date
    - Map speaker attributes from speaker_code if speaker metadata missing
    Returns enriched items list (mutates input list)
    """
    # Build mapping docPid -> file_id from docInfos
    pid_to_file_id = {}
    for pid, info in docinfos.items():
        md = info.get('metadata', {}) or {}
        file_id = md.get('file_id') or None
        if not file_id and md.get('fromInputFile'):
            src = md.get('fromInputFile')
            if isinstance(src, list) and src:
                src = src[0]
            # src may be an absolute path - take basename and remove extension
            base = os.path.basename(src)
            file_id = os.path.splitext(base)[0]
            if file_id:
                pid_to_file_id[str(pid)] = file_id

    def _enrich_item(item, hit):
        # Determine file_id: prefer docInfos mapping if filename is numeric docPid
        candidate = item.get('filename')
        file_id = None
        if candidate and isinstance(candidate, str):
            if candidate.isdigit():
                file_id = pid_to_file_id.get(candidate)
            elif candidate in docmeta_cache:
                file_id = candidate
            else:
                # If candidate isn't numeric and not direct file id, keep as-is
                file_id = candidate
        if not file_id:
            file_id = pid_to_file_id.get(str(hit.get('docPid')))
        # If we resolved a file_id from docInfos mapping, and the item's filename
        # was a numeric docPid, replace it with the resolved file_id so downstream
        # logic (media path resolution) uses the actual file identifier.
        if file_id:
            item['filename'] = file_id
        docmeta = docmeta_cache.get(file_id) if file_id else None
        if docmeta:
            item['country_code'] = item.get('country_code') or (docmeta.get('country_code') or '').lower()
            # Country scope may be absent in older docmeta files. Derive reasonable default:
            # If docmeta contains an explicit country_scope, use it. Otherwise infer from known regional codes.
            doc_scope = (docmeta.get('country_scope') or '').lower()
            if doc_scope:
                item['country_scope'] = item.get('country_scope') or doc_scope
            else:
                # Derive: region codes like 'ARG-CBA' indicate regional; otherwise national
                regional_codes = {'ARG-CHU', 'ARG-CBA', 'ARG-SDE', 'ESP-CAN', 'ESP-SEV'}
                code = (docmeta.get('country_code') or '').upper()
                if code in regional_codes:
                    item['country_scope'] = item.get('country_scope') or 'regional'
                else:
                    item['country_scope'] = item.get('country_scope') or 'national'
            # Only override filename from docmeta if not already set
            item['filename'] = item.get('filename') or docmeta.get('file_id')
            item['radio'] = item.get('radio') or docmeta.get('radio')
            item['date'] = item.get('date') or docmeta.get('date')
        if not item.get('speaker_type') or not item.get('sex') or not item.get('mode') or not item.get('discourse'):
            # docInfo can be list or dict - normalize to dict first
            doc_info = hit.get('docInfo') or {}
            if isinstance(doc_info, list) and doc_info:
                doc_info = doc_info[0] if isinstance(doc_info[0], dict) else {}
            spk_code = item.get('speaker_code') or hit.get('match', {}).get('speaker_code') or (doc_info.get('speaker_code') if isinstance(doc_info, dict) else None)
            if isinstance(spk_code, list) and spk_code:
                spk_code = spk_code[0]
            if spk_code:
                spk_type, sex, mode, discourse = map_speaker_attributes(spk_code)
                item['speaker_type'] = item.get('speaker_type') or spk_type
                item['sex'] = item.get('sex') or sex
                item['mode'] = item.get('mode') or mode
                item['discourse'] = item.get('discourse') or discourse
        return item

    for idx, (item, hit) in enumerate(zip(items, hits)):
        items[idx] = _enrich_item(item, hit)
    return items


def build_advanced_cql_and_filters_from_request(args):
    """
    Common helper to build CQL pattern and filters from request args.
    Used by both /data and /stats endpoints to ensure consistency.
    
    Returns:
        tuple: (cql_pattern, filter_query, filters)
    """
    # Get mode and query
    mode = args.get('mode', 'forma')
    query = args.get('q') or args.get('query', '')
    sensitive = args.get('sensitive', '0')
    
    logger.info(f"Building CQL: mode={mode}, sensitive={sensitive}, q={query}")
    
    # Resolve countries with include_regional logic
    countries = args.getlist('country_code')
    include_regional_param = args.get('include_regional')
    include_regional = include_regional_param == '1'
    countries = resolve_countries_for_include_regional(countries, include_regional)
    
    # Optimization: Clear country filter if all national countries selected
    ALL_NATIONAL_CODES = ['ARG', 'BOL', 'CHL', 'COL', 'CRI', 'CUB', 'ECU', 'ESP', 'GTM',
                          'HND', 'MEX', 'NIC', 'PAN', 'PRY', 'PER', 'DOM', 'SLV', 'URY', 'USA', 'VEN']
    
    if countries and include_regional_param is None:
        countries_set = set(countries)
        all_expected = set(ALL_NATIONAL_CODES)
        if countries_set == all_expected:
            countries = []
    
    # Build filters
    filters = build_filters(args)
    if countries:
        filters['country_code'] = countries
    
    # Build document filter
    filter_query = filters_to_blacklab_query(filters)
    
    # Build CQL pattern with speaker filter
    cql_filters = dict(filters)
    if filter_query:
        cql_filters.pop('country_code', None)
    
    cql_pattern = build_cql_with_speaker_filter(args, cql_filters)
    
    return cql_pattern, filter_query, filters


@bp.route("/data", methods=["GET"])
@limiter.limit("30 per minute")
def datatable_data():
    """
    DataTables Server-Side processing endpoint.
    
    Query parameters (from DataTables):
        - draw: Request sequence number
        - start: Pagination offset (0-based)
        - length: Rows per page (capped at MAX_HITS_PER_PAGE)
        - q or query: Search query
        - mode: 'forma_exacta' | 'forma' | 'lemma' | 'cql'
        - sensitive: '1' (sensitive) | '0' (insensitive)
        - country_code[]: List of countries
        - speaker_type[]: List of speaker types
        - sex[]: List of sexes
        - speech_mode[]: List of modes
        - discourse[]: List of discourse types
        - include_regional: '0' | '1'
        
    Returns:
        JSON: {draw, recordsTotal, recordsFiltered, data: [...]}
    """
    # Parameter extraction helpers (safe, handle missing/invalid values)
    def get_str(name: str, default: str = "") -> str:
        """Safely extract string parameter."""
        val = request.args.get(name, default, type=str)
        return (val or default).strip()
    
    def get_int(name: str, default: int = 0) -> int:
        """Safely extract integer parameter with fallback."""
        try:
            val = request.args.get(name, type=int)
            return val if val is not None else default
        except (ValueError, TypeError):
            return default
    
    def get_bool(name: str, default: bool = False) -> bool:
        """Safely extract boolean parameter (checks for '1', 'true', 'on', 'yes')."""
        val = request.args.get(name, "").lower()
        return val in ("1", "true", "on", "yes") if val else default
    
    def get_list(name: str) -> list:
        """Safely extract list parameter (handles both param[] and comma-separated)."""
        vals = request.args.getlist(name)
        return [v.strip() for v in vals if v and v.strip()]
    
    try:
        # Extract DataTables parameters with safe helpers
        draw = get_int("draw", 1)
        start = get_int("start", 0)
        length = get_int("length", 50)
        
        # Clamp length to MAX_HITS_PER_PAGE
        length = min(length, MAX_HITS_PER_PAGE)
        
        # If it's an initial load with no query and no filters, return empty.
        q_val = (request.args.get('q') or request.args.get('query') or '').strip()
        has_query = bool(q_val)
        
        # Check if any filter parameters were actually passed in the request
        filter_keys = ['country_code', 'speaker_type', 'sex', 'speech_mode', 'mode', 'discourse', 'city', 'radio', 'date', 'include_regional']
        has_filters = any(key in request.args for key in filter_keys)

        if not has_query and not has_filters:
            logger.info("Initial load detected (no query, no filters). Returning empty result set with initial_load flag.")
            return jsonify({
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "initial_load": True
            })

        # Use shared CQL builder (same as /stats)
        cql_pattern, filter_query, filters = build_advanced_cql_and_filters_from_request(request.args)
        logger.info(f"DATA CQL: patt={cql_pattern}, filter_query={filter_query}, filters={filters}")
        
        # Validate filters
        try:
            validate_filter_values(filters)
        except CQLValidationError as e:
            logger.warning(f"Filter validation failed: {e}")
            return jsonify({
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "error": "invalid_filter",
                "message": str(e)
            }), 200
        
        # BLS parameters
        bls_params = {
            "first": 0,
            "number": MAX_HITS_PER_PAGE,
            "wordsaroundhit": MAX_WORDS_AROUND_HIT,
            "listvalues": "word,tokid,start_ms,end_ms,sentence_id,file_id,filename,country,country_code,speaker_type,speaker_sex,speaker_mode,speaker_discourse,radio,utterance_id,speaker_code",
        }
        
        if filter_query:
            bls_params["filter"] = filter_query

        # Validate CQL pattern if we have one
        if cql_pattern is not None:
            try:
                validate_cql_pattern(cql_pattern)
            except CQLValidationError as e:
                logger.warning(f"CQL validation failed: {e}")
                return jsonify({
                    "draw": draw,
                    "recordsTotal": 0,
                    "recordsFiltered": 0,
                    "data": [],
                    "error": "invalid_cql",
                    "message": str(e)
                }), 200  # Return 200 for DataTables compatibility

        # If we have a CQL pattern, try the parameter names (patt, cql, cql_query)
        cql_param_names = ["patt", "cql", "cql_query"]
        response = None
        last_error = None
        if cql_pattern:
            for param_name in cql_param_names:
                try:
                    test_params = {**bls_params, param_name: cql_pattern}
                    response = _make_bls_request("/corpora/corapan/hits", test_params)
                    logger.debug(f"CQL param '{param_name}' accepted")
                    logger.debug(f"BL request params: {test_params}")
                    break
                except httpx.HTTPStatusError as e:
                    last_error = e
                    if e.response and e.response.status_code == 400:
                        continue  # Try next param name
                    else:
                        raise
            
            if response is None:
                raise last_error or Exception("Could not determine BLS CQL parameter")

        else: # No CQL pattern, make request with filters only
            response = _make_bls_request("/corpora/corapan/hits", bls_params)
        
        # Parse response
        data = response.json()
        summary = data.get("summary", {})
        hits = data.get("hits", [])
        # Temporary debug: log BL summary and counts for troubleshooting
        try:
            logger.debug(f"BLS summary keys: {list(summary.keys())}")
            logger.debug(f"BLS resultsStats: {summary.get('resultsStats')}")
            logger.debug(f"BLS numberOfHits: {summary.get('numberOfHits')}")
            logger.debug(f"BLS hits count (len): {len(hits)}")
        except Exception:
            logger.exception("Error logging BLS summary for debug")
        
        # DEBUG: Log first hit structure
        if hits:
            logger.debug(f"First hit structure: {json.dumps(hits[0], indent=2)[:500]}")
        
        # Punkt 2: Konsistenz - beide immer = numberOfHits (Server-Side Filtering)
        # Doc-Zahlen (numberOfDocs, docsRetrieved) nur für Summary-Badge nutzen
        # BlackLab v5: resultsStats.hits (nicht numberOfHits)
        results_stats = summary.get("resultsStats", {})
        number_of_hits = results_stats.get("hits", 0)
        docs_retrieved = results_stats.get("documents", 0)  # v5: documents statt docsRetrieved
        number_of_docs = results_stats.get("documents", 0)
        
        # Punkt 8: Logging von Trefferzahl
        logger.info(f"DataTables query: hits={number_of_hits}, docs_retrieved={docs_retrieved}, "
                   f"number_of_docs={number_of_docs}, filter={'yes' if filter_query else 'no'}")
        
        # Process hits for DataTable: map to canonical keys via blacklab_search helper
        from ..services.blacklab_search import _hit_to_canonical as _hit2canon
        processed_hits = [_hit2canon(hit) for hit in hits]

        # Enrich processed hits using helper
        processed_hits = _enrich_hits_with_docmeta(processed_hits, hits, data.get('docInfos', {}) or {}, _DOCMETA_CACHE or {})
        if current_app.debug or current_app.config.get('DEBUG'):
            try:
                sample = processed_hits[:5]
                logger.debug(f"Sample processed hits after enrichment: {json.dumps(sample, default=str)[:1000]}")
            except Exception:
                logger.exception("Error logging sample processed hits")
        
        # Apply country filter (post-processing since metadata is document-level)
        def _matches_country_filter(item, filters):
            """Ultra-simple 3-case country filter: checkbox OR exact whitelist."""
            include_regional = filters.get("include_regional", False)
            selected_codes = [c.upper() for c in filters.get("country_code", [])]
            
            code = (item.get("country_code") or "").upper()
            scope = (item.get("country_scope") or "").lower()  # "national" / "regional" / ""
            
            # Reject documents without country_code
            if not code:
                return False
            
            # CASE 3: País-Dropdown has selections → exact whitelist (checkbox irrelevant)
            if selected_codes:
                selected_set = set(selected_codes)
                return code in selected_set
            
            # CASE 1+2: No país selection → checkbox controls behavior
            
            # Checkbox off: only national documents
            if not include_regional:
                return scope == "national"
            
            # Checkbox on: national + regional (all documents)
            return True
        
        # Apply filter
        filtered_hits = [h for h in processed_hits if _matches_country_filter(h, filters)]
        
        # Apply pagination to filtered hits
        paginated_hits = filtered_hits[start:start + length]
        
        # Simple count logic: backend filter is the only filter
        records_total = len(filtered_hits)
        records_filtered = len(filtered_hits)
        
        response_payload = {
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": paginated_hits,
        }
        # Debug helper: include CQL when running in debug mode
        # Prefer Flask app.debug flag; ENV config may be missing in some configurations
        if current_app.debug or current_app.config.get('DEBUG'):
            response_payload['cql_debug'] = cql_pattern
            response_payload['filter_debug'] = filter_query or ''
            # Include a small sample of processed hits for debugging
            response_payload['hit_sample'] = processed_hits[:5]
        # Temporary debug: include BLS summary and hit counts to inspect responses
        response_payload['bls_summary'] = summary
        response_payload['bls_hits_len'] = len(hits)

        return jsonify(response_payload)
        
    except ValueError as e:
        # CQL validation error (from build_cql)
        logger.warning(f"CQL validation: {e}")
        return jsonify({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "invalid_cql",
            "message": str(e)
        }), 200  # Return 200 with error in JSON for DataTables compatibility
        
    except httpx.ConnectError:
        # Connection refused, DNS lookup failed, or BlackLab unreachable
        # This is a clear, actionable error for the user
        logger.warning(f"BLS connection failed (server not reachable at {BLS_BASE_URL})")
        return jsonify({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "upstream_unavailable",
            "message": f"Search backend (BlackLab) is currently not reachable. Please check that the BlackLab server is running at {BLS_BASE_URL}."
        }), 200  # Return 200 with error in JSON for DataTables compatibility
        
    except httpx.TimeoutException:
        logger.error("BLS timeout during DataTables request")
        return jsonify({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "upstream_timeout",
            "message": "BlackLab Server did not respond in time. Please try again later."
        }), 200  # Return 200 with error in JSON for DataTables compatibility
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            # CQL syntax error
            try:
                bls_error = e.response.json().get("error", {})
                detail = bls_error.get("message", str(e))
            except:
                detail = e.response.text[:200]
            logger.warning(f"BLS CQL error: {detail}")
            return jsonify({
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "error": "invalid_cql",
                "message": f"CQL syntax error: {detail}"
            }), 200  # Return 200 with error in JSON for DataTables compatibility
        else:
            logger.error(f"BLS HTTP {e.response.status_code}: {e.response.text[:200]}")
            return jsonify({
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "error": "upstream_error",
                "message": f"BlackLab Server error: {e.response.status_code}"
            }), 200  # Return 200 with error in JSON for DataTables compatibility
            
    except Exception as e:
        logger.exception("Unexpected error in DataTables endpoint")
        msg = str(e)
        # include small debug payload for troubleshooting
        debug_payload = {}
        try:
            debug_payload['request_args'] = dict(request.args)
            if 'cql_pattern' in locals():
                debug_payload['cql_pattern'] = cql_pattern
            if 'filter_query' in locals():
                debug_payload['filter_query'] = filter_query
            if 'bls_params' in locals():
                debug_payload['bls_params'] = bls_params
        except Exception:
            pass
        payload = {
            "draw": draw if 'draw' in locals() else 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "server_error",
            "message": "An unexpected error occurred",
        }
        # Include error details and debug payload only when debug is enabled
        if current_app.debug or current_app.config.get('DEBUG'):
            payload['error_details'] = msg
            payload['debug'] = debug_payload
        return jsonify(payload), 200  # Return 200 with error in JSON for DataTables compatibility


@bp.route("/token/search", methods=["POST"])
@limiter.limit("30 per minute")
def token_search():
    """
    Token search endpoint - searches by token IDs using BlackLab.
    
    JSON parameters:
        - draw: DataTables request sequence number
        - start: Pagination offset
        - length: Rows per page
        - token_ids_raw: Comma/newline-separated token IDs
        - context_size: Context words (default: 5)
        
    Returns:
        JSON: {draw, recordsTotal, recordsFiltered, data: [...]}
    """
    # Extract parameters
    draw = request.json.get("draw", 1) if request.json else 1
    start = request.json.get("start", 0) if request.json else 0
    length = request.json.get("length", 25) if request.json else 25
    token_ids_raw = request.json.get("token_ids_raw", "") if request.json else ""
    context_size = request.json.get("context_size", 5) if request.json else 5
    
    # Normalize and validate token IDs
    token_ids = []
    if token_ids_raw:
        # Split by comma, newline, semicolon, whitespace
        import re
        raw_list = re.split(r'[,;\n\r\t\s]+', token_ids_raw)
        # Trim and filter empty strings
        token_ids = [tid.strip() for tid in raw_list if tid.strip()]
    
    # Limit token IDs (max 500 to prevent abuse)
    MAX_TOKEN_IDS = 500
    if len(token_ids) > MAX_TOKEN_IDS:
        return jsonify({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "too_many_tokens",
            "message": f"Too many token IDs (max {MAX_TOKEN_IDS}, received {len(token_ids)})"
        }), 200
    
    if not token_ids:
        return jsonify({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "no_tokens",
            "message": "No token IDs provided"
        }), 200
    
    # Build CQL pattern with tokid filter
    if len(token_ids) == 1:
        cql_pattern = f'[tokid="{token_ids[0]}"]'
    else:
        # Multiple IDs: [tokid="ID1" | tokid="ID2" | tokid="ID3"]
        conditions = ' | '.join([f'tokid="{tid}"' for tid in token_ids])
        cql_pattern = f'[{conditions}]'
    
    try:
        # Build BlackLab request parameters
        bls_params = {
            "first": start,
            "number": length,
            "wordsaroundhit": context_size,
            "listvalues": "tokid,start_ms,end_ms,word,lemma,pos,country_code,country_scope,country_parent_code,country_region_code,speaker_code,speaker_type,speaker_sex,speaker_mode,speaker_discourse,file_id,radio,city,date",
        }
        
        # Call BlackLab via proxy
        bls_url = f"/bls/corpora/corapan/hits"
        
        # Try CQL parameter names
        http_client = get_http_client()
        response = None
        for param_name in ["patt", "cql", "cql_query"]:
            try:
                test_params = {**bls_params, param_name: cql_pattern}
                response = _make_bls_request("/corpora/corapan/hits", test_params)
                break
            except httpx.HTTPStatusError as e:
                if e.response.status_code != 400:
                    raise
                continue
        
        if response is None:
            raise Exception("Could not determine BLS CQL parameter")
        
        data = response.json()
        summary = data.get("summary", {})
        hits = data.get("hits", [])
        
        # Get hit counts
        results_stats = summary.get("resultsStats", {})
        number_of_hits = results_stats.get("hits", 0)
        
        logger.info(f"Token search: {len(token_ids)} token IDs, {number_of_hits} hits found")
        
        # Process hits using same helper as advanced search
        from ..services.blacklab_search import _hit_to_canonical as _hit2canon
        processed_hits = [_hit2canon(hit) for hit in hits]
        
        # Enrich with docmeta
        processed_hits = _enrich_hits_with_docmeta(processed_hits, hits, data.get('docInfos', {}) or {}, _DOCMETA_CACHE or {})
        
        # Return DataTables response
        response_payload = {
            "draw": draw,
            "recordsTotal": number_of_hits,
            "recordsFiltered": number_of_hits,
            "data": processed_hits,
        }
        
        if current_app.debug or current_app.config.get('DEBUG'):
            response_payload['cql_debug'] = cql_pattern
        
        return jsonify(response_payload)
        
    except httpx.ConnectError:
        logger.warning(f"Token search: BLS connection failed")
        return jsonify({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "upstream_unavailable",
            "message": f"Search backend (BlackLab) is not reachable"
        }), 200
        
    except httpx.TimeoutException:
        logger.error("Token search: BLS timeout")
        return jsonify({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "upstream_timeout",
            "message": "BlackLab Server timeout"
        }), 200
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Token search: BLS HTTP {e.response.status_code}")
        return jsonify({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "upstream_error",
            "message": f"BlackLab Server error: {e.response.status_code}"
        }), 200
        
    except Exception as e:
        logger.exception("Token search: Unexpected error")
        return jsonify({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "server_error",
            "message": "An unexpected error occurred"
        }), 200


@bp.route("/export", methods=["GET"])
@limiter.limit("6 per minute")  # Export rate limit: 6/min (separate from /data)
def export_data():
    """
    Stream full search results as CSV or TSV.
    
    Hardening (2025-11-10):
    - Punkt 1: Content-Disposition mit sprechendem Dateinamen, Cache-Control: no-store
    - Punkt 8: Logging von Export-Zeilen, BLS-Duration, Client-Disconnect
    - V2: Timeout-Safe Streaming mit deterministic error responses
    
    Query parameters:
        - q or query: Search query
        - mode: 'forma_exacta' | 'forma' | 'lemma' | 'cql'
        - sensitive: '1' | '0'
        - country_code[]: List of countries
        - speaker_type[]: List of speaker types
        - sex[]: List of sexes
        - speech_mode[]: List of modes
        - discourse[]: List of discourse types
        - include_regional: '0' | '1'
        - format: 'csv' (default) | 'tsv'
        
    Returns:
        Streaming text/csv or text/tab-separated-values with Content-Disposition
        On error: text/plain 504 (timeout) or 502 (upstream error)
    """
    import time
    
    try:
        # Build CQL
        cql_pattern = build_cql(request.args)
        
        # Punkt 3: Validierung CQL Pattern
        try:
            validate_cql_pattern(cql_pattern)
        except CQLValidationError as e:
            logger.warning(f"Export CQL validation failed: {e}")
            # Return as plain text error (not JSON, so it doesn't break downloads)
            return f"CQL validation error: {str(e)}", 400
        
        # Build filters - compute include_regional-adjusted countries
        countries = request.args.getlist('country_code')
        include_regional = request.args.get('include_regional') == '1'
        countries = resolve_countries_for_include_regional(countries, include_regional)

        filters = build_filters(request.args)
        if countries:
            filters['country_code'] = countries
        
        # Punkt 3: Validierung Filter Values
        try:
            validate_filter_values(filters)
        except CQLValidationError as e:
            logger.warning(f"Export filter validation failed: {e}")
            # Return as plain text error
            return f"Filter validation error: {str(e)}", 400
        
        filter_query = filters_to_blacklab_query(filters)
        
        # Output format
        export_format = request.args.get("format", "csv").lower()
        if export_format not in ("csv", "tsv"):
            export_format = "csv"
        
        delimiter = "\t" if export_format == "tsv" else ","
        mime_type = "text/tab-separated-values" if export_format == "tsv" else "text/csv"
        
        # Punkt 1: Sprechender Dateiname mit Timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"corapan-export_{timestamp}.{export_format}"
        
        # Pre-flight: Try to fetch first chunk to validate BLS is reachable
        # This prevents streaming starting but failing mid-stream
        logger.debug("Export: Pre-flight BLS call to validate upstream...")
        try:
            preflight_params = {
                "first": 0,
                "number": 1,  # Just 1 hit to check connectivity
                "wordsaroundhit": 10,
                "listvalues": "tokid,start_ms,end_ms,country,speaker_type,sex,mode,discourse,filename,radio",
            }
            if filter_query:
                preflight_params["filter"] = filter_query
            
            # Try CQL parameter names
            preflight_response = None
            for param_name in ["patt", "cql", "cql_query"]:
                try:
                    test_params = {**preflight_params, param_name: cql_pattern}
                    preflight_response = _make_bls_request("/corpora/corapan/hits", test_params)
                    logger.debug(f"Export preflight: CQL param '{param_name}' accepted")
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code != 400:
                        raise
                    continue
            
            if preflight_response is None:
                raise Exception("Could not determine BLS CQL parameter")
            
            preflight_data = preflight_response.json()
            total_hits = preflight_data.get("summary", {}).get("numberOfHits", 0)
            logger.info(f"Export initiated: format={export_format}, total_hits={total_hits}, "
                       f"filters={'yes' if filter_query else 'no'}")
            
        except httpx.ConnectError:
            logger.warning(f"Export preflight failed - BLS connection refused at {BLS_BASE_URL}")
            return f"Export error: BlackLab Server is not reachable at {BLS_BASE_URL}", 502
        except httpx.TimeoutException:
            logger.error("Export preflight timeout - BLS not responding")
            return "Export error: BlackLab Server timeout", 504
        except httpx.HTTPStatusError as e:
            logger.error(f"Export preflight failed: BLS {e.response.status_code}")
            return f"Export error: BlackLab Server error {e.response.status_code}", 502
        except Exception as e:
            logger.error(f"Export preflight failed: {type(e).__name__}: {str(e)}")
            return f"Export error: {str(e)}", 502
        
        # Streaming generator function
        def generate_export() -> Generator[str, None, None]:
            """Stream CSV rows, fetching from BLS in chunks with timeout protection."""
            
            # CSV header with UTF-8 BOM (optional, für Excel-Kompatibilität)
            fieldnames = [
                "left", "match", "right",
                "country", "speaker_type", "sex", "mode", "discourse",
                "filename", "radio", "tokid", "start_ms", "end_ms"
            ]
            
            writer_buffer = io.StringIO()
            writer = csv.DictWriter(writer_buffer, fieldnames=fieldnames, delimiter=delimiter)
            
            # Punkt 1: UTF-8 BOM nur für CSV (Excel-Kompatibilität)
            if export_format == "csv":
                yield "\ufeff"  # UTF-8 BOM
            
            writer.writeheader()
            yield writer_buffer.getvalue()
            
            # Stream hits in chunks with timeout protection
            total_exported = 0
            first = 0
            export_start_time = time.time()
            max_export_time = 300  # 5 minutes absolute max
            
            try:
                while total_exported < GLOBAL_HITS_CAP:
                    # Check if we've exceeded absolute time limit
                    elapsed = time.time() - export_start_time
                    if elapsed > max_export_time:
                        logger.warning(f"Export reached max duration ({max_export_time}s) after {total_exported} rows")
                        break
                    
                    chunk_start = time.time()
                    
                    # Fetch chunk with explicit timeout
                    try:
                        bls_params = {
                            "first": first,
                            "number": EXPORT_CHUNK_SIZE,
                            "wordsaroundhit": 10,
                            "listvalues": "tokid,start_ms,end_ms,country,speaker_type,sex,mode,discourse,filename,radio",
                        }
                        
                        if filter_query:
                            bls_params["filter"] = filter_query
                        
                        # Try CQL param names
                        response = None
                        for param_name in ["patt", "cql", "cql_query"]:
                            try:
                                test_params = {**bls_params, param_name: cql_pattern}
                                response = _make_bls_request("/corpora/corapan/hits", test_params)
                                break
                            except httpx.HTTPStatusError as e:
                                if e.response.status_code != 400:
                                    raise
                                continue
                        
                        if response is None:
                            raise Exception("Could not determine BLS CQL parameter")
                        
                    except httpx.ConnectError:
                        logger.error(f"Export chunk connection failed at offset {first} - BLS unreachable at {BLS_BASE_URL}")
                        yield f"\n# Export interrupted: BlackLab connection failed at row {total_exported}\n"
                        break
                    except httpx.TimeoutException:
                        logger.error(f"Export chunk timeout at offset {first}")
                        # Gracefully end export
                        yield f"\n# Export interrupted: BLS timeout at row {total_exported}\n"
                        break
                    except httpx.HTTPStatusError as e:
                        logger.error(f"Export chunk failed: BLS {e.response.status_code} at offset {first}")
                        yield f"\n# Export interrupted: BLS error {e.response.status_code} at row {total_exported}\n"
                        break
                    except Exception as e:
                        logger.error(f"Export chunk failed: {type(e).__name__}: {str(e)}")
                        yield f"\n# Export interrupted: {type(e).__name__} at row {total_exported}\n"
                        break
                    
                    # Punkt 8: BLS-Duration Logging
                    chunk_duration = time.time() - chunk_start
                    
                    data = response.json()
                    hits = data.get("hits", [])
                    
                    logger.debug(f"Export chunk: offset={first}, duration={chunk_duration:.2f}s, "
                               f"hits={len(hits)}, total_so_far={total_exported}")
                    
                    # Process hits
                    writer_buffer = io.StringIO()
                    writer = csv.DictWriter(writer_buffer, fieldnames=fieldnames, delimiter=delimiter)
                    
                    for hit in hits:
                        left = hit.get("left", {}).get("word", [])
                        match = hit.get("match", {}).get("word", [])
                        right = hit.get("right", {}).get("word", [])
                        
                        match_info = hit.get("match", {})
                        tokid = match_info.get("tokid", [None])[0]
                        start_ms = match_info.get("start_ms", [0])[0] if match_info.get("start_ms") else 0
                        end_ms = match_info.get("end_ms", [0])[0] if match_info.get("end_ms") else 0
                        
                        # Metadata
                        hit_metadata = hit.get("metadata", {})
                        
                        row = {
                            "left": " ".join(left[-10:]) if left else "",
                            "match": " ".join(match),
                            "right": " ".join(right[:10]) if right else "",
                            "country": hit_metadata.get("country", ""),
                            "speaker_type": hit_metadata.get("speaker_type", ""),
                            "sex": hit_metadata.get("sex", ""),
                            "mode": hit_metadata.get("mode", ""),
                            "discourse": hit_metadata.get("discourse", ""),
                            "filename": hit_metadata.get("filename", ""),
                            "radio": hit_metadata.get("radio", ""),
                            "tokid": tokid or "",
                            "start_ms": start_ms or "",
                            "end_ms": end_ms or "",
                        }
                        writer.writerow(row)
                    
                    chunk_output = writer_buffer.getvalue()
                    if chunk_output:
                        yield chunk_output
                    
                    total_exported += len(hits)
                    
                    # Check if we've got all hits
                    if len(hits) < EXPORT_CHUNK_SIZE:
                        logger.info(f"Export finished: {total_exported} total rows fetched")
                        break
                    
                    first += EXPORT_CHUNK_SIZE
                
                # Punkt 8: Export completion logging
                export_duration = time.time() - export_start_time
                logger.info(f"Export completed: {total_exported} lines in {export_duration:.2f}s "
                          f"({total_exported/max(export_duration, 0.1):.0f} lines/sec)")
                
            except GeneratorExit:
                # Punkt 1: Client-Disconnect Handling
                export_duration = time.time() - export_start_time
                logger.warning(f"Export aborted by client after {total_exported} lines, {export_duration:.2f}s")
                raise
            except Exception as e:
                # Unexpected error in generator
                logger.exception(f"Unexpected error in export generator after {total_exported} rows")
                yield f"\n# Unexpected error: {type(e).__name__}\n"
        
        # Punkt 1: Content-Disposition mit sprechendem Dateinamen + Cache-Control
        return Response(
            generate_export(),
            mimetype=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": f"{mime_type}; charset=utf-8",
                "Cache-Control": "no-store",  # Punkt 1: Kein Caching
                "X-Accel-Buffering": "no",     # Disable nginx/proxy buffering
            }
        )
        
    except ValueError as e:
        logger.warning(f"Export CQL validation: {e}")
        return f"Export error: CQL validation failed - {str(e)}", 400
        
    except httpx.ConnectError:
        logger.error(f"Export connection failed - BLS unreachable at {BLS_BASE_URL}")
        return f"Export error: BlackLab Server is not reachable at {BLS_BASE_URL}", 502
        
    except httpx.TimeoutException:
        logger.error("BLS timeout during export")
        return "Export error: BlackLab Server timeout", 504
        
    except httpx.HTTPStatusError as e:
        logger.error(f"BLS HTTP {e.response.status_code} during export")
        return f"Export error: BlackLab Server error {e.response.status_code}", 502
        
    except Exception as e:
        logger.exception("Unexpected error in export endpoint")
        return f"Export error: {type(e).__name__} - {str(e)}", 500


@bp.route("/stats", methods=["GET"])
@limiter.limit("30 per minute")
def advanced_stats():
    """
    Comprehensive BlackLab-native statistics aggregation endpoint.
    
    Aggregates hit-level metadata from BlackLab search results using the exact same
    search query as the DataTables endpoint to ensure consistency.
    
    Query Parameters:
        All parameters from /search/advanced/data are supported:
        - q, mode, sensitive: Search query parameters
        - country_code[], speaker_type[], sex[], speech_mode[], discourse[]: Filters
        - include_regional: Include regional broadcasts
        - country_detail: Optional post-filter by specific country (for drill-down)
    
    Returns:
        JSON: {
            "total_hits": int,
            "by_country": [{key, n, p}, ...],
            "by_country_region": [{key, n, p}, ...],
            "by_speaker_type": [{key, n, p}, ...],
            "by_sexo": [{key, n, p}, ...],
            "by_modo": [{key, n, p}, ...],
            "by_discourse": [{key, n, p}, ...],
            "by_radio": [{key, n, p}, ...],
            "by_city": [{key, n, p}, ...],
            "by_file_id": [{key, n, p}, ...]
        }
        where:
            key: Category value (e.g., "ARG", "m", "libre")
            n: Absolute count of hits
            p: Proportion (0.0-1.0)
    
    Implementation:
        1. Builds identical CQL + filters as /data endpoint
        2. Fetches up to MAX_STATS_HITS hits from BlackLab (no pagination)
        3. Aggregates token-level annotations from hit.match field
        4. Returns sorted statistics (descending by count, then ascending by key)
    
    Note:
        - All aggregated fields are token annotations (in corapan-tsv.blf.yaml)
        - BlackLab doesn't provide native grouping API, so we aggregate manually
        - For queries with >MAX_STATS_HITS results, statistics are based on sample
    """
    # Maximum hits to fetch for statistics (balance between accuracy and performance)
    MAX_STATS_HITS = 50000
    
    try:
        # Build CQL and filters using same logic as /data endpoint
        cql_pattern, filter_query, filters = build_advanced_cql_and_filters_from_request(request.args)
        logger.info(f"STATS CQL: patt={cql_pattern}, filter={filter_query}")
        
        # BlackLab parameters for stats aggregation
        bls_params = {
            "first": 0,
            "number": MAX_STATS_HITS,  # Fetch large sample for accurate statistics
            "wordsaroundhit": 0,  # No context needed for stats
            # Request all token annotations needed for aggregation
            # NOTE: Field names match BlackLab index: speaker_sex, speaker_mode, speaker_discourse
            "listvalues": "country_code,country_region_code,speaker_type,speaker_sex,speaker_mode,speaker_discourse,radio,city,file_id",
            "waitfortotal": "true"  # Ensure we get accurate total count
        }
        
        if filter_query:
            bls_params["filter"] = filter_query
        
        # Try CQL parameter names (same fallback logic as /data)
        cql_param_names = ["patt", "cql", "cql_query"]
        response = None
        last_error = None
        
        for param_name in cql_param_names:
            try:
                test_params = {**bls_params, param_name: cql_pattern}
                response = _make_bls_request("/corpora/corapan/hits", test_params)
                logger.debug(f"Stats: CQL param '{param_name}' accepted")
                break
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response and e.response.status_code == 400:
                    continue  # Try next param name
                else:
                    raise
        
        if response is None:
            raise last_error or Exception("Could not determine BLS CQL parameter")
        
        # Parse BlackLab response
        data = response.json()
        summary = data.get("summary", {})
        results_stats = summary.get("resultsStats", {})
        
        # Get total hit count from resultsStats (BlackLab v5)
        total_hits = results_stats.get("hits", 0)
        
        # Get hits for aggregation
        hits = data.get("hits", [])
        
        logger.info(f"Stats: Retrieved {len(hits)} of {total_hits} total hits from BlackLab")
        
        # DEBUG: Log first hit structure to identify field names
        if hits:
            first_hit = hits[0]
            match_data = first_hit.get("match", {})
            logger.info(f"Stats DEBUG: First hit match fields: {list(match_data.keys())}")
            logger.debug(f"Stats DEBUG: First hit match values: {match_data}")
        
        # Log sampling warning if we hit the limit
        if len(hits) >= MAX_STATS_HITS and total_hits > MAX_STATS_HITS:
            logger.warning(f"Stats: Sampled {len(hits)} of {total_hits} hits for aggregation")
        
        # Apply country_detail filter if specified (for drill-down by country)
        country_detail = request.args.get('country_detail', '').strip().upper()
        
        if country_detail:
            filtered_hits = []
            for hit in hits:
                match = hit.get("match", {})
                country_code = match.get("country_code")
                
                # Extract first value if list
                if isinstance(country_code, list):
                    country_code = country_code[0] if country_code else None
                
                if country_code and country_code.upper() == country_detail:
                    filtered_hits.append(hit)
            
            hits = filtered_hits
            total_hits = len(hits)
            logger.info(f"Stats: Filtered to {total_hits} hits for country {country_detail}")
        
        # Aggregation function
        def aggregate_dimension(dimension_key: str, fallback_key: str = None) -> list:
            """
            Aggregate hits by a token annotation field.
            
            Args:
                dimension_key: Primary field name from hit.match (token annotation)
                fallback_key: Alternative field name to try if primary is not found
            
            Returns:
                List of {key, n, p} dicts sorted by count (desc) then key (asc)
            """
            counts = Counter()
            
            def is_empty_value(val):
                """Check if value is None, empty list, empty string, or list containing only empty strings."""
                if val is None or val == "" or val == []:
                    return True
                if isinstance(val, list):
                    # Check if all elements are empty strings
                    return all(v == "" or v is None for v in val)
                return False
            
            for hit in hits:
                # Extract value from hit.match (token-level annotation)
                match = hit.get("match", {})
                value = match.get(dimension_key)
                
                # Try fallback if primary key has no value
                if is_empty_value(value) and fallback_key:
                    value = match.get(fallback_key)
                
                # Skip empty values
                if is_empty_value(value):
                    continue
                
                # Handle list values (BlackLab returns token annotations as lists)
                # Take FIRST non-empty value only (one count per hit!)
                if isinstance(value, list):
                    for v in value:
                        if v is not None and str(v).strip():
                            counts[str(v)] += 1
                            break  # Only count once per hit
                else:
                    if value and str(value).strip():
                        counts[str(value)] += 1
            
            # Calculate proportions
            total = sum(counts.values())
            
            # Build sorted result
            result = [
                {
                    "key": key,
                    "n": count,
                    "p": round(count / total, 3) if total > 0 else 0
                }
                for key, count in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
            ]
            
            return result
        
        # DEBUG: Log first 3 hits to see field structure
        if hits and len(hits) > 0:
            logger.info(f"Stats DEBUG: Inspecting first 3 hits...")
            for i, hit in enumerate(hits[:3]):
                match = hit.get("match", {})
                logger.info(f"  Hit {i+1} match keys: {list(match.keys())}")
                logger.info(f"  Hit {i+1} speaker_sex={match.get('speaker_sex')}, sex={match.get('sex')}")
                logger.info(f"  Hit {i+1} speaker_mode={match.get('speaker_mode')}, mode={match.get('mode')}")
                logger.info(f"  Hit {i+1} country_code={match.get('country_code')}")
        
        # Aggregate all dimensions
        # NOTE: Using fallback keys for backward compatibility (some indices may use "sex" instead of "speaker_sex")
        by_country = aggregate_dimension("country_code", "country")
        by_country_region = aggregate_dimension("country_region_code")
        by_speaker_type = aggregate_dimension("speaker_type")
        by_sex = aggregate_dimension("speaker_sex", "sex")  # Try speaker_sex first, fallback to sex
        by_mode = aggregate_dimension("speaker_mode", "mode")  # Try speaker_mode first, fallback to mode
        by_discourse = aggregate_dimension("speaker_discourse", "discourse")  # Try speaker_discourse first, fallback to discourse
        by_radio = aggregate_dimension("radio")
        by_city = aggregate_dimension("city")
        by_file_id = aggregate_dimension("file_id")
        
        # Build response
        result = {
            "total_hits": total_hits,
            "by_country": by_country,
            "by_country_region": by_country_region,
            "by_speaker_type": by_speaker_type,
            "by_sexo": by_sex,  # Frontend expects "by_sexo"
            "by_modo": by_mode,  # Frontend expects "by_modo"
            "by_discourse": by_discourse,
            "by_radio": by_radio,
            "by_city": by_city,
            "by_file_id": by_file_id,
        }
        
        logger.info(
            f"Stats: Aggregated {len(hits)} hits - "
            f"{len(by_country)} countries, "
            f"{len(by_country_region)} regions, "
            f"{len(by_speaker_type)} speaker types, "
            f"{len(by_sex)} sexes, "
            f"{len(by_mode)} modes, "
            f"{len(by_discourse)} discourse types, "
            f"{len(by_radio)} radios, "
            f"{len(by_city)} cities, "
            f"{len(by_file_id)} files"
        )
        
        return jsonify(result), 200
        
    except httpx.ConnectError:
        logger.error("Stats: BLS connection failed")
        return jsonify({
            "error": "connection_error",
            "message": "BlackLab Server is not reachable"
        }), 502
        
    except httpx.TimeoutException:
        logger.error("Stats: BLS timeout")
        return jsonify({
            "error": "timeout",
            "message": "BlackLab Server request timeout"
        }), 504
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Stats: BLS HTTP error {e.response.status_code}")
        return jsonify({
            "error": "bls_error",
            "message": f"BlackLab Server returned error {e.response.status_code}"
        }), 502
        
    except CQLValidationError as e:
        logger.warning(f"Stats: CQL validation error - {e}")
        return jsonify({
            "error": "invalid_query",
            "message": str(e)
        }), 400
        
    except Exception as e:
        logger.exception("Stats: Unexpected error")
        return jsonify({
            "error": "server_error",
            "message": "An unexpected error occurred"
        }), 500
