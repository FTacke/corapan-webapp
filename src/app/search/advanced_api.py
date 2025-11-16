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

import httpx
from flask import Blueprint, jsonify, request, Response, current_app

from .cql import build_cql, build_filters, filters_to_blacklab_query, build_cql_with_speaker_filter, resolve_countries_for_include_regional
from .cql_validator import validate_cql_pattern, validate_filter_values, CQLValidationError  # Punkt 3
from .speaker_utils import map_speaker_attributes
from ..extensions import limiter
from ..extensions.http_client import get_http_client, BLS_BASE_URL
from ..services.database import open_db

logger = logging.getLogger(__name__)

bp = Blueprint("advanced_api", __name__, url_prefix="/search/advanced")

# Limits and caps
MAX_HITS_PER_PAGE = 100
GLOBAL_HITS_CAP = 50000




# Load docmeta.jsonl for metadata lookup (file_id -> metadata)
def _load_docmeta():
    """Load document metadata from docmeta.jsonl."""
    docmeta_path = Path(__file__).parent.parent.parent.parent / "data" / "blacklab_export" / "docmeta.jsonl"
    docmeta = {}
    if docmeta_path.exists():
        try:
            with open(docmeta_path, 'r', encoding='utf-8') as f:
                for line in f:
                    doc = json.loads(line)
                    file_id = doc.get("file_id")
                    if file_id:
                        # Normalize file_id keys by stripping whitespace
                        docmeta[file_id.strip()] = doc
            logger.info(f"Loaded {len(docmeta)} document metadata entries")
        except Exception as e:
            logger.warning(f"Failed to load docmeta.jsonl: {e}")
    return docmeta




# Cache docmeta at module level
_DOCMETA_CACHE = _load_docmeta()
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
        docmeta = docmeta_cache.get(file_id) if file_id else None
        if docmeta:
            item['country_code'] = item.get('country_code') or (docmeta.get('country_code') or '').lower()
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
        
        # Build filters first (needed for speaker-based CQL construction)
        # But first compute include_regional-adjusted country list similar to corpus routes
        # Compute country list using centralized logic
        countries = request.args.getlist('country_code')
        include_regional_param = request.args.get('include_regional')  # Can be None, '0', or '1'
        include_regional = include_regional_param == '1'
        countries = resolve_countries_for_include_regional(countries, include_regional)
        
        # OPTIMIZATION: If ALL countries are selected (default case when no params sent),
        # clear the country filter to avoid building inefficient CQL regex with 20-25 alternatives.
        # This allows queries to match all documents without unnecessary country_code constraints.
        # 
        # IMPORTANT: Only apply this optimization when user has NOT explicitly set include_regional.
        # If include_regional is explicitly set, we must keep the filter to exclude regional codes.
        ALL_NATIONAL_CODES = ['ARG', 'BOL', 'CHL', 'COL', 'CRI', 'CUB', 'ECU', 'ESP', 'GTM', 
                              'HND', 'MEX', 'NIC', 'PAN', 'PRY', 'PER', 'DOM', 'SLV', 'URY', 'USA', 'VEN']
        ALL_REGIONAL_CODES = ['ARG-CHU', 'ARG-CBA', 'ARG-SDE', 'ESP-CAN', 'ESP-SEV']
        
        # Only optimize when include_regional param is NOT explicitly set
        if countries and include_regional_param is None:
            countries_set = set(countries)
            all_expected = set(ALL_NATIONAL_CODES)  # When no param, defaults to national only
            if countries_set == all_expected:
                # All national countries selected and no explicit include_regional → no need to filter
                countries = []

        # Build filters from request.args and then override the country list computed above
        filters = build_filters(request.args)
        # Build_filters populates country_code as list if present; override it with our computed list
        if countries:
            filters['country_code'] = countries
        
        # Punkt 3: Validierung Filter Values
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
            }), 200  # Return 200 for DataTables compatibility
        
        # Build the initial BlackLab document filter from token-level filters
        # (country, radio, city, date). We'll try to expand country_code filters
        # into a doc-level file_id filter using document metadata when available.
        filter_query = filters_to_blacklab_query(filters)
        logger.info(f"BlackLab document filter (initial): {filter_query}")
        
        # CQL Pattern validation is performed after the pattern is built.
        
        logger.info(f"All filters: {filters}")
        
        # BLS parameters
        # Note: listvalues must include 'word' for KWIC display in BlackLab v5
        # Include 'speaker_code' for speaker attribute mapping
        bls_params = {
            "first": start,
            "number": length,
            "wordsaroundhit": 10,
            # Include all token-level metadata needed for canonical mapping
            "listvalues": "word,tokid,start_ms,end_ms,file_id,filename,country,country_code,speaker_type,sex,mode,discourse,radio,utterance_id,speaker_code",
        }
        
        # IMPORTANT: Do NOT build file_id filter when all countries are selected.
        # file_id is NOT indexed as document-level metadata (only as token annotation).
        # Instead, rely on token-level country_code metadata (already built by filters_to_blacklab_query).
        # 
        # Skip file_id filter building entirely - it causes 0 results because file_id
        # doesn't exist as doc-level metadata field in the BlackLab index.

        if filter_query:
            bls_params = {
                "first": start,
                "number": length,
                "wordsaroundhit": 10,
                # Include all token-level metadata needed for canonical mapping
                "listvalues": "word,tokid,start_ms,end_ms,file_id,filename,country,country_code,speaker_type,sex,mode,discourse,radio,utterance_id,speaker_code",
            }
            bls_params["filter"] = filter_query
        else:
            bls_params = {
                "first": start,
                "number": length,
                "wordsaroundhit": 10,
                # Include all token-level metadata needed for canonical mapping
                "listvalues": "word,tokid,start_ms,end_ms,file_id,filename,country,country_code,speaker_type,sex,mode,discourse,radio,utterance_id,speaker_code",
            }

        # Build CQL with speaker filter integrated
        # Important: pass filters with computed country_code and include_regional semantics
        # If we build a doc-level BLS filter (file_id list), avoid adding token-level
        # country_code constraints into the CQL (they can be redundant and cause mismatches).
        cql_filters = dict(filters)  # copy to avoid mutating original
        if filter_query:  # doc-level filter present
            cql_filters.pop('country_code', None)
        cql_pattern = build_cql_with_speaker_filter(request.args, cql_filters)
        logger.info(f"Built CQL pattern: {cql_pattern} (mode={request.args.get('mode')}, q={request.args.get('q')})")

        # Validate CQL pattern
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

        # Try CQL parameter names in order: patt, cql, cql_query
        cql_param_names = ["patt", "cql", "cql_query"]
        response = None
        last_error = None
        
        for param_name in cql_param_names:
            try:
                test_params = {**bls_params, param_name: cql_pattern}
                response = _make_bls_request("/corpora/corapan/hits", test_params)
                logger.debug(f"CQL param '{param_name}' accepted")
                logger.debug(f"BL request params: {test_params}")
                break
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 400:
                    continue  # Try next param name
                else:
                    raise
        
        if response is None:
            raise last_error or Exception("Could not determine BLS CQL parameter")
        
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
        
        # BlackLab is Single Source of Truth for counts
        # Both recordsTotal and recordsFiltered come from BlackLab
        response_payload = {
            "draw": draw,
            "recordsTotal": number_of_hits,
            "recordsFiltered": number_of_hits,
            "data": processed_hits,
        }
        # Debug helper: include CQL when running in debug mode
        # Prefer Flask app.debug flag; ENV config may be missing in some configurations
        if current_app.debug or current_app.config.get('DEBUG'):
            response_payload['cql_debug'] = cql_pattern
            response_payload['filter_debug'] = filter_query or ''
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
