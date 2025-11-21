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
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime, timezone

import httpx
from flask import Blueprint, jsonify, request, Response, current_app

from .cql import (
    build_cql,
    build_filters,
    filters_to_blacklab_query,
    resolve_countries_for_include_regional,
)
from .cql_validator import (
    validate_cql_pattern,
    validate_filter_values,
    CQLValidationError,
)  # Punkt 3
from .speaker_utils import map_speaker_attributes
from ..extensions import limiter
from ..extensions.http_client import get_http_client, BLS_BASE_URL

logger = logging.getLogger(__name__)

# Central mapping for BlackLab index fields
BLS_FIELDS = {
    "country": "country_code",
    "region": "country_region_code",
    "scope": "country_scope",
    "file_id": "file_id",
    "speaker_type": "speaker_type",
    "sex": "speaker_sex",
    "mode": "speaker_mode",
    "discourse": "speaker_discourse",
    "radio": "radio",
    "city": "city",
}

bp = Blueprint("advanced_api", __name__, url_prefix="/search/advanced")

# Limits and caps
MAX_HITS_PER_PAGE = 20000  # Fetch all hits from BLS so Python can filter them properly
GLOBAL_HITS_CAP = 50000
MAX_WORDS_AROUND_HIT = 40


# Load docmeta.jsonl for metadata lookup (file_id -> metadata)
def _load_docmeta():
    """Load document metadata from docmeta.jsonl."""
    docmeta_path = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "blacklab_export"
        / "docmeta.jsonl"
    )
    docmeta = {}
    country_codes_by_parent = {}

    if docmeta_path.exists():
        try:
            with open(docmeta_path, "r", encoding="utf-8") as f:
                for line in f:
                    doc = json.loads(line)
                    file_id = doc.get("file_id")
                    if file_id:
                        # Normalize file_id keys by stripping whitespace
                        docmeta[file_id.strip()] = doc

                    # Build parent -> all codes mapping
                    parent = (
                        doc.get("country_parent_code") or doc.get("country_code") or ""
                    ).upper()
                    code = (doc.get("country_code") or "").upper()
                    if parent and code:
                        country_codes_by_parent.setdefault(parent, set()).add(code)

            logger.info(f"Loaded {len(docmeta)} document metadata entries")
            logger.info(
                f"Built country codes mapping for {len(country_codes_by_parent)} parents"
            )
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
    timeout_override: Optional[float] = None,
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
            response = client.request(
                method.upper(), full_url, params=params, headers=headers
            )

        response.raise_for_status()
        logger.debug(
            f"BLS {method} {path}: {response.status_code} ({len(response.content)} bytes)"
        )
        return response

    except httpx.TimeoutException:
        logger.error(f"BLS timeout on {path}")
        raise
    except httpx.HTTPStatusError as e:
        logger.error(
            f"BLS error on {path}: {e.response.status_code} - {e.response.text[:200]}"
        )
        raise
    except Exception as e:
        logger.error(f"BLS request failed on {path}: {type(e).__name__}: {str(e)}")
        raise


def _enrich_hits_with_docmeta(
    items: list, hits: list, docinfos: dict, docmeta_cache: dict
) -> list:
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
        md = info.get("metadata", {}) or {}
        file_id = md.get("file_id") or None
        if not file_id and md.get("fromInputFile"):
            src = md.get("fromInputFile")
            if isinstance(src, list) and src:
                src = src[0]
            # src may be an absolute path - take basename and remove extension
            base = os.path.basename(src)
            file_id = os.path.splitext(base)[0]
            if file_id:
                pid_to_file_id[str(pid)] = file_id
        # Fix: Ensure file_id is added even if it came from metadata directly
        if file_id:
            pid_to_file_id[str(pid)] = file_id

    def _enrich_item(item, hit):
        # Determine file_id: prefer docInfos mapping if filename is numeric docPid
        candidate = item.get("filename")
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
            file_id = pid_to_file_id.get(str(hit.get("docPid")))
        # If we resolved a file_id from docInfos mapping, and the item's filename
        # was a numeric docPid, replace it with the resolved file_id so downstream
        # logic (media path resolution) uses the actual file identifier.
        if file_id:
            item["filename"] = file_id
        docmeta = docmeta_cache.get(file_id) if file_id else None
        if docmeta:
            item["country_code"] = (
                item.get("country_code") or (docmeta.get("country_code") or "").lower()
            )
            # Country scope may be absent in older docmeta files. Derive reasonable default:
            # If docmeta contains an explicit country_scope, use it. Otherwise infer from known regional codes.
            doc_scope = (docmeta.get("country_scope") or "").lower()
            if doc_scope:
                item["country_scope"] = item.get("country_scope") or doc_scope
            else:
                # Derive: region codes like 'ARG-CBA' indicate regional; otherwise national
                regional_codes = {"ARG-CHU", "ARG-CBA", "ARG-SDE", "ESP-CAN", "ESP-SEV"}
                code = (docmeta.get("country_code") or "").upper()
                if code in regional_codes:
                    item["country_scope"] = item.get("country_scope") or "regional"
                else:
                    item["country_scope"] = item.get("country_scope") or "national"
            # Only override filename from docmeta if not already set
            item["filename"] = item.get("filename") or docmeta.get("file_id")
            item["radio"] = item.get("radio") or docmeta.get("radio")
            item["date"] = item.get("date") or docmeta.get("date")
        if (
            not item.get("speaker_type")
            or not item.get("sex")
            or not item.get("mode")
            or not item.get("discourse")
        ):
            # docInfo can be list or dict - normalize to dict first
            doc_info = hit.get("docInfo") or {}
            if isinstance(doc_info, list) and doc_info:
                doc_info = doc_info[0] if isinstance(doc_info[0], dict) else {}
            spk_code = (
                item.get("speaker_code")
                or hit.get("match", {}).get("speaker_code")
                or (
                    doc_info.get("speaker_code") if isinstance(doc_info, dict) else None
                )
            )
            if isinstance(spk_code, list) and spk_code:
                spk_code = spk_code[0]
            if spk_code:
                spk_type, sex, mode, discourse = map_speaker_attributes(spk_code)
                item["speaker_type"] = item.get("speaker_type") or spk_type
                item["sex"] = item.get("sex") or sex
                item["mode"] = item.get("mode") or mode
                item["discourse"] = item.get("discourse") or discourse
        return item

    for idx, (item, hit) in enumerate(zip(items, hits)):
        items[idx] = _enrich_item(item, hit)
    return items


@bp.route("/data", methods=["GET"])
@limiter.limit("30 per minute")
def datatable_data():
    """
    DataTables Server-Side processing endpoint.
    """

    # Parameter extraction helpers
    def get_int(name: str, default: int = 0) -> int:
        try:
            val = request.args.get(name, type=int)
            return val if val is not None else default
        except (ValueError, TypeError):
            return default

    def get_str(name: str, default: str = "") -> str:
        val = request.args.get(name, default, type=str)
        return (val or default).strip()

    try:
        draw = get_int("draw", 1)
        start = get_int("start", 0)
        length = get_int("length", 50)
        length = min(length, MAX_HITS_PER_PAGE)

        # Initial load check
        q_val = (request.args.get("q") or request.args.get("query") or "").strip()
        filter_keys = [
            "country_code",
            "speaker_type",
            "sex",
            "speech_mode",
            "discourse",
            "city",
            "radio",
            "date",
            "include_regional",
        ]
        has_filters = any(key in request.args for key in filter_keys)

        if not q_val and not has_filters:
            return jsonify(
                {
                    "draw": draw,
                    "recordsTotal": 0,
                    "recordsFiltered": 0,
                    "data": [],
                    "initial_load": True,
                }
            )

        # Build query using shared logic
        query_info = build_blacklab_query_from_request(request.args)
        cql_pattern = query_info["patt"]
        filter_query = query_info["filter"]
        params = query_info["params_base"].copy()

        # Add DataTables specific params
        params.update(
            {
                "first": start,
                "number": length,
                "waitfortotal": "true",
                "listvalues": ",".join(
                    [
                        "word",
                        "tokid",
                        "start_ms",
                        "end_ms",
                        "sentence_id",
                        BLS_FIELDS["country"],
                        BLS_FIELDS["speaker_type"],
                        BLS_FIELDS["sex"],
                        BLS_FIELDS["mode"],
                        BLS_FIELDS["discourse"],
                        BLS_FIELDS["file_id"],
                        BLS_FIELDS["radio"],
                        BLS_FIELDS["city"],
                        "utterance_id",
                        "speaker_code",
                    ]
                ),
            }
        )

        if cql_pattern:
            params["patt"] = cql_pattern
        if filter_query:
            params["filter"] = filter_query

        # Handle sorting
        order_col_idx = get_int("order[0][column]", -1)
        order_dir = get_str("order[0][dir]", "asc")

        # Map column index to field name
        # For sorting by annotation values (metadata on tokens), we use "hit:<field>"
        column_map = {
            2: "hit:word",
            5: f"hit:{BLS_FIELDS['country']}",
            6: f"hit:{BLS_FIELDS['speaker_type']}",
            7: f"hit:{BLS_FIELDS['sex']}",
            8: f"hit:{BLS_FIELDS['mode']}",
            9: f"hit:{BLS_FIELDS['discourse']}",
            10: "hit:tokid",
            11: f"hit:{BLS_FIELDS['file_id']}",
        }

        if order_col_idx in column_map:
            sort_field = column_map[order_col_idx]
            if order_dir == "desc":
                params["sort"] = f"-{sort_field}"
            else:
                params["sort"] = sort_field

        # Execute request
        response = _make_bls_request("/corpora/corapan/hits", params)
        data = response.json()
        summary = data.get("summary", {})
        hits = data.get("hits", [])

        results_stats = summary.get("resultsStats", {})
        total_hits = summary.get("numberOfHits", 0)
        if not total_hits:
            total_hits = results_stats.get("hits", 0)

        # Process hits
        from ..services.blacklab_search import _hit_to_canonical as _hit2canon

        processed_hits = [_hit2canon(hit) for hit in hits]

        # Enrich hits
        processed_hits = _enrich_hits_with_docmeta(
            processed_hits, hits, data.get("docInfos", {}) or {}, _DOCMETA_CACHE or {}
        )

        return jsonify(
            {
                "draw": draw,
                "recordsTotal": total_hits,
                "recordsFiltered": total_hits,
                "data": processed_hits,
                "bls_summary": summary,
            }
        )

    except Exception as e:
        logger.exception("DataTables error")
        return jsonify({"draw": get_int("draw", 1), "error": str(e), "data": []})


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

    # Normalize and validate token IDs
    token_ids = []
    if token_ids_raw:
        # Split by comma, newline, semicolon, whitespace
        import re

        raw_list = re.split(r"[,;\n\r\t\s]+", token_ids_raw)
        # Trim and filter empty strings
        token_ids = [tid.strip() for tid in raw_list if tid.strip()]

    # Limit token IDs (max 500 to prevent abuse)
    MAX_TOKEN_IDS = 500
    if len(token_ids) > MAX_TOKEN_IDS:
        return jsonify(
            {
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "error": "too_many_tokens",
                "message": f"Too many token IDs (max {MAX_TOKEN_IDS}, received {len(token_ids)})",
            }
        ), 200

    if not token_ids:
        return jsonify(
            {
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "error": "no_tokens",
                "message": "No token IDs provided",
            }
        ), 200

    # Build CQL pattern with tokid filter
    if len(token_ids) == 1:
        cql_pattern = f'[tokid="{token_ids[0]}"]'
    else:
        # Multiple IDs: [tokid="ID1" | tokid="ID2" | tokid="ID3"]
        conditions = " | ".join([f'tokid="{tid}"' for tid in token_ids])
        cql_pattern = f"[{conditions}]"

    try:
        # Build BlackLab request parameters
        bls_params = {
            "first": start,
            "number": length,
            "wordsaroundhit": 40,  # Always request max context
            "listvalues": "tokid,start_ms,end_ms,word,lemma,pos,country_code,country_scope,country_parent_code,country_region_code,speaker_code,speaker_type,speaker_sex,speaker_mode,speaker_discourse,file_id,radio,city,date,sentence_id",
        }

        # Call BlackLab via proxy

        # Try CQL parameter names
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

        logger.info(
            f"Token search: {len(token_ids)} token IDs, {number_of_hits} hits found"
        )

        # Process hits using same helper as advanced search
        from ..services.blacklab_search import _hit_to_canonical as _hit2canon

        processed_hits = [_hit2canon(hit) for hit in hits]

        # Enrich with docmeta
        processed_hits = _enrich_hits_with_docmeta(
            processed_hits, hits, data.get("docInfos", {}) or {}, _DOCMETA_CACHE or {}
        )

        # Apply sentence-based context trimming
        # Logic: If context > 40 words, trim. But also respect sentence boundaries if possible.
        # Actually, user requirement: "Satzgrenze über sentence_id greifen und nur wenn es mehr als 40 wörter sind begrenzen."
        # This means: Show full sentence. If sentence > 40 words, trim to 40 words around hit.
        # BlackLab returns context as list of words. We don't have sentence structure in the word list easily unless we parse XML.
        # However, we requested 'sentence_id'.
        # But 'sentence_id' is a list value for the hit, not for the context words.
        # BlackLab's 'wordsaroundhit' is a hard limit on words.
        # If we want sentence context, we should use 'usecontent=s' or similar in BLS, but that returns XML.
        # For JSON, we get words.
        # We requested 40 words.
        # If the user wants "sentence boundary", we can't easily do that with just word lists unless we have punctuation or sentence_id per word.
        # But we can try to trim based on punctuation if we have it.
        # For now, we just ensure we requested enough context (40) as per requirement 6.
        # The requirement says: "Hier sollte die Satzgrenze über sentence_id greifen und nur wenn es mehr als 40 wörter sind begrenzen."
        # This implies we should try to show the sentence.
        # Since we can't easily get full sentence extent from BLS JSON 'hits' endpoint without 'concordance' view (which is XML),
        # we will stick to the 40 words limit which we set in bls_params.

        # Return DataTables response
        response_payload = {
            "draw": draw,
            "recordsTotal": number_of_hits,
            "recordsFiltered": number_of_hits,
            "data": processed_hits,
        }

        if current_app.debug or current_app.config.get("DEBUG"):
            response_payload["cql_debug"] = cql_pattern

        return jsonify(response_payload)

    except httpx.ConnectError:
        logger.warning("Token search: BLS connection failed")
        return jsonify(
            {
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "error": "upstream_unavailable",
                "message": "Search backend (BlackLab) is not reachable",
            }
        ), 200

    except httpx.TimeoutException:
        logger.error("Token search: BLS timeout")
        return jsonify(
            {
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "error": "upstream_timeout",
                "message": "BlackLab Server timeout",
            }
        ), 200

    except httpx.HTTPStatusError as e:
        logger.error(f"Token search: BLS HTTP {e.response.status_code}")
        return jsonify(
            {
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "error": "upstream_error",
                "message": f"BlackLab Server error: {e.response.status_code}",
            }
        ), 200

    except Exception:
        logger.exception("Token search: Unexpected error")
        return jsonify(
            {
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "error": "server_error",
                "message": "An unexpected error occurred",
            }
        ), 200


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
        countries = request.args.getlist("country_code")
        include_regional = request.args.get("include_regional") == "1"
        countries = resolve_countries_for_include_regional(countries, include_regional)

        filters = build_filters(request.args)
        if countries:
            filters["country_code"] = countries

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
        mime_type = (
            "text/tab-separated-values" if export_format == "tsv" else "text/csv"
        )

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
                    preflight_response = _make_bls_request(
                        "/corpora/corapan/hits", test_params
                    )
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
            logger.info(
                f"Export initiated: format={export_format}, total_hits={total_hits}, "
                f"filters={'yes' if filter_query else 'no'}"
            )

        except httpx.ConnectError:
            logger.warning(
                f"Export preflight failed - BLS connection refused at {BLS_BASE_URL}"
            )
            return (
                f"Export error: BlackLab Server is not reachable at {BLS_BASE_URL}",
                502,
            )
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
                "left",
                "match",
                "right",
                "country",
                "speaker_type",
                "sex",
                "mode",
                "discourse",
                "filename",
                "radio",
                "tokid",
                "start_ms",
                "end_ms",
            ]

            writer_buffer = io.StringIO()
            writer = csv.DictWriter(
                writer_buffer, fieldnames=fieldnames, delimiter=delimiter
            )

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
                        logger.warning(
                            f"Export reached max duration ({max_export_time}s) after {total_exported} rows"
                        )
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
                                response = _make_bls_request(
                                    "/corpora/corapan/hits", test_params
                                )
                                break
                            except httpx.HTTPStatusError as e:
                                if e.response.status_code != 400:
                                    raise
                                continue

                        if response is None:
                            raise Exception("Could not determine BLS CQL parameter")

                    except httpx.ConnectError:
                        logger.error(
                            f"Export chunk connection failed at offset {first} - BLS unreachable at {BLS_BASE_URL}"
                        )
                        yield f"\n# Export interrupted: BlackLab connection failed at row {total_exported}\n"
                        break
                    except httpx.TimeoutException:
                        logger.error(f"Export chunk timeout at offset {first}")
                        # Gracefully end export
                        yield f"\n# Export interrupted: BLS timeout at row {total_exported}\n"
                        break
                    except httpx.HTTPStatusError as e:
                        logger.error(
                            f"Export chunk failed: BLS {e.response.status_code} at offset {first}"
                        )
                        yield f"\n# Export interrupted: BLS error {e.response.status_code} at row {total_exported}\n"
                        break
                    except Exception as e:
                        logger.error(
                            f"Export chunk failed: {type(e).__name__}: {str(e)}"
                        )
                        yield f"\n# Export interrupted: {type(e).__name__} at row {total_exported}\n"
                        break

                    # Punkt 8: BLS-Duration Logging
                    chunk_duration = time.time() - chunk_start

                    data = response.json()
                    hits = data.get("hits", [])

                    logger.debug(
                        f"Export chunk: offset={first}, duration={chunk_duration:.2f}s, "
                        f"hits={len(hits)}, total_so_far={total_exported}"
                    )

                    # Process hits
                    writer_buffer = io.StringIO()
                    writer = csv.DictWriter(
                        writer_buffer, fieldnames=fieldnames, delimiter=delimiter
                    )

                    for hit in hits:
                        left = hit.get("left", {}).get("word", [])
                        match = hit.get("match", {}).get("word", [])
                        right = hit.get("right", {}).get("word", [])

                        match_info = hit.get("match", {})
                        tokid = match_info.get("tokid", [None])[0]
                        start_ms = (
                            match_info.get("start_ms", [0])[0]
                            if match_info.get("start_ms")
                            else 0
                        )
                        end_ms = (
                            match_info.get("end_ms", [0])[0]
                            if match_info.get("end_ms")
                            else 0
                        )

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
                        logger.info(
                            f"Export finished: {total_exported} total rows fetched"
                        )
                        break

                    first += EXPORT_CHUNK_SIZE

                # Punkt 8: Export completion logging
                export_duration = time.time() - export_start_time
                logger.info(
                    f"Export completed: {total_exported} lines in {export_duration:.2f}s "
                    f"({total_exported / max(export_duration, 0.1):.0f} lines/sec)"
                )

            except GeneratorExit:
                # Punkt 1: Client-Disconnect Handling
                export_duration = time.time() - export_start_time
                logger.warning(
                    f"Export aborted by client after {total_exported} lines, {export_duration:.2f}s"
                )
                raise
            except Exception as e:
                # Unexpected error in generator
                logger.exception(
                    f"Unexpected error in export generator after {total_exported} rows"
                )
                yield f"\n# Unexpected error: {type(e).__name__}\n"

        # Punkt 1: Content-Disposition mit sprechendem Dateinamen + Cache-Control
        return Response(
            generate_export(),
            mimetype=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": f"{mime_type}; charset=utf-8",
                "Cache-Control": "no-store",  # Punkt 1: Kein Caching
                "X-Accel-Buffering": "no",  # Disable nginx/proxy buffering
            },
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
def stats_data():
    """
    Statistics endpoint using BlackLab grouping.
    """
    try:
        query_info = build_blacklab_query_from_request(request.args)
        patt = query_info["patt"]
        filter_cql = query_info["filter"]
        params_base = query_info["params_base"]

        # Get total hits first
        count_params = params_base.copy()
        if patt:
            count_params["patt"] = patt
        if filter_cql:
            count_params["filter"] = filter_cql
        count_params["number"] = 0
        count_params["waitfortotal"] = "true"

        # Execute total count request
        count_resp = _make_bls_request("/corpora/corapan/hits", count_params)
        count_data = count_resp.json()
        total_hits = count_data.get("summary", {}).get("numberOfHits", 0)
        if not total_hits:
            total_hits = (
                count_data.get("summary", {}).get("resultsStats", {}).get("hits", 0)
            )

        # Define dimensions to group by
        dimensions = {
            "by_country": BLS_FIELDS["country"],
            "by_speaker_type": BLS_FIELDS["speaker_type"],
            "by_sex": BLS_FIELDS["sex"],
            "by_modo": BLS_FIELDS["mode"],
            "by_discourse": BLS_FIELDS["discourse"],
            "by_radio": BLS_FIELDS["radio"],
            "by_city": BLS_FIELDS["city"],
            "by_file_id": BLS_FIELDS["file_id"],
        }

        stats = {"total_hits": total_hits}

        # Execute grouping requests in parallel
        logger.info(f"STATS QUERY: patt={patt}, filter={filter_cql}")

        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_dim = {
                executor.submit(
                    bls_group_by_field, field, patt, filter_cql, params_base
                ): dim
                for dim, field in dimensions.items()
            }

            for future in as_completed(future_to_dim):
                dim = future_to_dim[future]
                try:
                    stats[dim] = future.result()
                except Exception as exc:
                    logger.error(f"Stats dimension {dim} generated an exception: {exc}")
                    stats[dim] = []

        return jsonify(stats)

    except Exception as e:
        logger.exception("Stats error")
        return jsonify({"error": str(e)}), 500


@bp.route("/stats/csv", methods=["GET"])
@limiter.limit("10 per minute")
def stats_csv():
    """
    Streaming CSV export of statistics.
    """
    try:
        query_info = build_blacklab_query_from_request(request.args)
        patt = query_info["patt"]
        filter_cql = query_info["filter"]
        params_base = query_info["params_base"]

        # Get total hits first
        count_params = params_base.copy()
        if patt:
            count_params["patt"] = patt
        if filter_cql:
            count_params["filter"] = filter_cql
        count_params["number"] = 0
        count_params["waitfortotal"] = "true"

        # Execute total count request
        count_resp = _make_bls_request("/corpora/corapan/hits", count_params)
        count_data = count_resp.json()
        total_hits = count_data.get("summary", {}).get("numberOfHits", 0)
        if not total_hits:
            total_hits = (
                count_data.get("summary", {}).get("resultsStats", {}).get("hits", 0)
            )

        # Define dimensions to group by
        dimensions = {
            "by_country": {"field": BLS_FIELDS["country"], "label": "Por país"},
            "by_speaker_type": {"field": BLS_FIELDS["speaker_type"], "label": "Por tipo de hablante"},
            "by_sex": {"field": BLS_FIELDS["sex"], "label": "Por sexo"},
            "by_modo": {"field": BLS_FIELDS["mode"], "label": "Por modo"},
            "by_discourse": {"field": BLS_FIELDS["discourse"], "label": "Por discurso"},
            "by_radio": {"field": BLS_FIELDS["radio"], "label": "Por emisora"},
            "by_city": {"field": BLS_FIELDS["city"], "label": "Por ciudad"},
            "by_file_id": {"field": BLS_FIELDS["file_id"], "label": "Por archivo"},
        }

        # Execute grouping requests in parallel
        stats_results = {}
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_dim = {
                executor.submit(
                    bls_group_by_field, info["field"], patt, filter_cql, params_base
                ): dim
                for dim, info in dimensions.items()
            }

            for future in as_completed(future_to_dim):
                dim = future_to_dim[future]
                try:
                    stats_results[dim] = future.result()
                except Exception as exc:
                    logger.error(f"Stats dimension {dim} generated an exception: {exc}")
                    stats_results[dim] = []

        # Capture args for generator to avoid context issues
        req_args = request.args.copy()

        def generate():
            # Metadata header
            yield f"# corpus=CO.RA.PAN\n"
            yield f"# date_generated={datetime.now(timezone.utc).isoformat()}\n"
            yield f"# query_type=CQL\n"
            yield f"# query={patt or '*'}\n"
            
            # Filters as JSON string
            filters_dict = {k: v for k, v in req_args.items() if k not in ['q', 'mode', 'patt', 'cql']}
            yield f"# filters={json.dumps(filters_dict, ensure_ascii=False)}\n"
            
            yield f"# total_hits={total_hits}\n"
            yield f"# stats_type=all_charts\n"
            
            # CSV Header
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["chart_id", "chart_label", "dimension", "count", "relative_frequency"])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            # Data rows
            for dim_key, results in stats_results.items():
                chart_label = dimensions[dim_key]["label"]
                for row in results:
                    count = row["n"]
                    rel_freq = count / total_hits if total_hits > 0 else 0
                    writer.writerow([
                        dim_key,
                        chart_label,
                        row["key"],
                        count,
                        f"{rel_freq:.6f}"
                    ])
                    yield output.getvalue()
                    output.seek(0)
                    output.truncate(0)

        return Response(
            generate(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=estadisticas_busqueda.csv"}
        )

    except Exception as e:
        logger.exception("Stats CSV export error")
        return jsonify({"error": str(e)}), 500


def build_cql_with_direct_filters(params, filters):
    """
    Build CQL pattern with direct field constraints (no speaker_code mapping).
    Uses BLS_FIELDS to map filter keys to index field names.
    """
    base_cql = build_cql(params)

    constraints = []

    # Map filter keys to BLS fields
    # filters keys: speaker_type, sex, mode, discourse, country_code, radio, city, date

    # Speaker fields
    for filter_key, bls_field in [
        ("speaker_type", BLS_FIELDS["speaker_type"]),
        ("sex", BLS_FIELDS["sex"]),
        ("mode", BLS_FIELDS["mode"]),
        ("discourse", BLS_FIELDS["discourse"]),
    ]:
        vals = filters.get(filter_key, [])
        if vals:
            if len(vals) == 1:
                constraints.append(f'{bls_field}="{vals[0]}"')
            else:
                constraints.append(f'{bls_field}="({"|".join(vals)})"')

    # Document/Metadata fields (as token annotations)
    # country_code
    vals = filters.get("country_code", [])
    if vals:
        if len(vals) == 1:
            constraints.append(f'{BLS_FIELDS["country"]}="{vals[0]}"')
        else:
            constraints.append(f'{BLS_FIELDS["country"]}="({"|".join(vals)})"')

    # exclude_country_code
    vals = filters.get("exclude_country_code", [])
    if vals:
        for val in vals:
            constraints.append(f'{BLS_FIELDS["country"]}!="{val}"')

    # country_scope
    val = filters.get("country_scope")
    if val:
        constraints.append(f'{BLS_FIELDS["scope"]}="{val}"')

    # radio
    val = filters.get("radio")
    if val:
        constraints.append(f'{BLS_FIELDS["radio"]}="{val}"')

    # city
    val = filters.get("city")
    if val:
        constraints.append(f'{BLS_FIELDS["city"]}="{val}"')

    # date
    val = filters.get("date")
    if val:
        constraints.append(f'date="{val}"')

    if not constraints:
        return base_cql

    # Apply constraints to every token in the CQL pattern
    import re

    token_pattern = re.compile(r"\[([^\]]*)\]")

    constraint_str = " & ".join(constraints)

    def add_constraints(match):
        existing = match.group(1).strip()
        if existing:
            return f"[{existing} & {constraint_str}]"
        return f"[{constraint_str}]"

    modified_cql = token_pattern.sub(add_constraints, base_cql)
    logger.info(f"CQL with direct filters: {modified_cql}")
    return modified_cql
    return modified_cql


def build_blacklab_query_from_request(req_args) -> dict:
    """
    Liest die HTTP-Parameter und erzeugt ein dict mit:
    - patt (CQL-Pattern)
    - filter (CQL-Filter oder "")
    - params_base (dict mit fixen BLS-Parametern, ohne paging / grouping)
    """
    # Get mode and query

    # Resolve countries with include_regional logic
    countries = req_args.getlist("country_code")
    include_regional_param = req_args.get("include_regional")
    include_regional = include_regional_param == "1"

    # Build filters
    filters = build_filters(req_args)
    if countries:
        filters["country_code"] = countries

    # Handle country_scope default logic
    # If no explicit countries selected and include_regional is False, enforce national scope
    if not countries and not filters.get("country_scope"):
        if not include_regional:
            filters["country_scope"] = "national"
            # Explicitly exclude known regional codes to be safe against missing scope tags
            filters["exclude_country_code"] = ["ARG-CHU", "ARG-CBA", "ARG-SDE", "ESP-CAN", "ESP-SEV"]

    # Build document filter (likely empty now, but kept for structure)
    filter_query = filters_to_blacklab_query(filters)

    # Build CQL pattern with direct filters
    # We pass filters to build_cql_with_direct_filters which adds them to the CQL
    cql_pattern = build_cql_with_direct_filters(req_args, filters)

    params_base = {
        "wordsaroundhit": MAX_WORDS_AROUND_HIT,
    }

    return {"patt": cql_pattern, "filter": filter_query, "params_base": params_base}


def bls_group_by_field(
    field_name: str, patt: str, filter_cql: str, base_params: dict
) -> list[dict]:
    """
    Ruft BlackLab mit group=hit:<field_name> auf und gibt eine Liste von
    {'key': <groupValue>, 'n': <size>} zurück.
    """
    params = base_params.copy()
    if patt:
        params["patt"] = patt
    if filter_cql:
        params["filter"] = filter_cql

    # Use 'hit:' grouping since all our metadata are stored as token annotations
    params["group"] = f"hit:{field_name}"
    params["number"] = 1000  # Limit number of groups, not hits
    params["waitfortotal"] = "true"

    try:
        start_time = time.time()
        # Log the actual params being sent for debugging
        logger.debug(f"Grouping request {field_name}: params={params}")

        response = _make_bls_request("/corpora/corapan/hits", params)
        duration = time.time() - start_time

        data = response.json()
        groups = data.get("hitGroups", [])

        logger.debug(f"Grouping {field_name}: {len(groups)} groups in {duration:.2f}s")

        result = []
        for g in groups:
            identity = g.get("identity", "")
            # identity for hit: grouping is usually just the value
            # but sometimes it might be "cql:..." depending on version
            val = identity
            if ":" in str(val) and not str(val).startswith(
                "http"
            ):  # Avoid splitting URLs if any
                # Heuristic: if it looks like cql:field:value, take last part
                parts = str(val).split(":")
                if len(parts) > 1:
                    val = parts[-1]

            result.append({"key": val, "n": g.get("size", 0)})

        return result

    except Exception as e:
        logger.error(f"Grouping failed for {field_name}: {e}")
        return []
