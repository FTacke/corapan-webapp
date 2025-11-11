"""
Advanced Search API Endpoints - DataTables JSON and Export.

Provides:
- GET /search/advanced/data: DataTables Server-Side endpoint
- GET /search/advanced/export: Streaming CSV/TSV export
"""
from __future__ import annotations

import csv
import io
import logging
from typing import Generator, Optional

import httpx
from flask import Blueprint, jsonify, request, Response, current_app

from .cql import build_cql, build_filters, filters_to_blacklab_query
from .cql_validator import validate_cql_pattern, validate_filter_values, CQLValidationError  # Punkt 3
from ..extensions import limiter
from ..extensions.http_client import get_http_client

logger = logging.getLogger(__name__)

bp = Blueprint("advanced_api", __name__, url_prefix="/search/advanced")

# Limits and caps
MAX_HITS_PER_PAGE = 100
GLOBAL_HITS_CAP = 50000
EXPORT_CHUNK_SIZE = 1000


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
        path: BLS endpoint path (e.g., "/corapan/hits")
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
    url = f"/bls{path}"  # Full URL from root
    
    try:
        if method.upper() == "GET":
            response = client.get(url, params=params)
        else:
            response = client.request(method.upper(), url, params=params)
        
        response.raise_for_status()
        return response
        
    except httpx.TimeoutException:
        logger.error(f"BLS timeout on {path}")
        raise
    except httpx.HTTPStatusError as e:
        logger.error(f"BLS error: {e.response.status_code} - {e.response.text[:200]}")
        raise


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
    try:
        # Extract DataTables parameters
        draw = request.args.get("draw", 1, type=int)
        start = request.args.get("start", 0, type=int)
        length = request.args.get("length", 50, type=int)
        
        # Clamp length to MAX_HITS_PER_PAGE
        length = min(length, MAX_HITS_PER_PAGE)
        
        # Build CQL
        cql_pattern = build_cql(request.args)
        
        # Punkt 3: Validierung CQL Pattern und Filter
        try:
            validate_cql_pattern(cql_pattern)
        except CQLValidationError as e:
            logger.warning(f"CQL validation failed: {e}")
            return jsonify({
                "error": "invalid_cql",
                "message": str(e),
                "draw": draw,
            }), 400
        
        # Build filters
        filters = build_filters(request.args)
        
        # Punkt 3: Validierung Filter Values
        try:
            validate_filter_values(filters)
        except CQLValidationError as e:
            logger.warning(f"Filter validation failed: {e}")
            return jsonify({
                "error": "invalid_filter",
                "message": str(e),
                "draw": draw,
            }), 400
        
        filter_query = filters_to_blacklab_query(filters)
        
        # BLS parameters
        bls_params = {
            "first": start,
            "number": length,
            "wordsaroundhit": 10,
            "listvalues": "tokid,start_ms,end_ms,country,speaker_type,sex,mode,discourse,filename,radio",
        }
        
        if filter_query:
            bls_params["filter"] = filter_query
        
        # Try CQL parameter names in order: patt, cql, cql_query
        cql_param_names = ["patt", "cql", "cql_query"]
        response = None
        last_error = None
        
        for param_name in cql_param_names:
            try:
                test_params = {**bls_params, param_name: cql_pattern}
                response = _make_bls_request("/corapan/hits", test_params)
                logger.debug(f"CQL param '{param_name}' accepted")
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
        
        # Punkt 2: Konsistenz - beide immer = numberOfHits (Server-Side Filtering)
        # Doc-Zahlen (numberOfDocs, docsRetrieved) nur für Summary-Badge nutzen
        number_of_hits = summary.get("numberOfHits", 0)
        docs_retrieved = summary.get("docsRetrieved", 0)
        number_of_docs = summary.get("numberOfDocs", 0)
        
        # Punkt 8: Logging von Trefferzahl
        logger.info(f"DataTables query: hits={number_of_hits}, docs_retrieved={docs_retrieved}, "
                   f"number_of_docs={number_of_docs}, filter={'yes' if filter_query else 'no'}")
        
        # Process hits for DataTable
        processed_hits = []
        for hit in hits:
            left = hit.get("left", {}).get("word", [])
            match = hit.get("match", {}).get("word", [])
            right = hit.get("right", {}).get("word", [])
            
            # Metadata from hit
            match_info = hit.get("match", {})
            tokid = match_info.get("tokid", [None])[0]
            start_ms = match_info.get("start_ms", [0])[0] if match_info.get("start_ms") else 0
            end_ms = match_info.get("end_ms", [0])[0] if match_info.get("end_ms") else 0
            
            # Document metadata (from listvalues)
            hit_metadata = hit.get("metadata", {})
            country = hit_metadata.get("country", "")
            speaker_type = hit_metadata.get("speaker_type", "")
            sex = hit_metadata.get("sex", "")
            mode = hit_metadata.get("mode", "")
            discourse = hit_metadata.get("discourse", "")
            filename = hit_metadata.get("filename", "")
            radio = hit_metadata.get("radio", "")
            
            row = {
                "left": " ".join(left[-10:]) if left else "",
                "match": " ".join(match),
                "right": " ".join(right[:10]) if right else "",
                "country": country,
                "speaker_type": speaker_type,
                "sex": sex,
                "mode": mode,
                "discourse": discourse,
                "filename": filename,
                "radio": radio,
                "tokid": tokid,
                "start_ms": start_ms,
                "end_ms": end_ms,
            }
            processed_hits.append([
                row["left"],
                row["match"],
                row["right"],
                row["country"],
                row["speaker_type"],
                row["sex"],
                row["mode"],
                row["discourse"],
                row["filename"],
                row["radio"],
                str(row["tokid"]),
                f"{row['start_ms']}",
                f"{row['end_ms']}",
            ])
        
        return jsonify({
            "draw": draw,
            "recordsTotal": number_of_hits,  # Punkt 2: Beide = numberOfHits
            "recordsFiltered": number_of_hits,  # Punkt 2: Server-Side Filtering (beide identisch)
            "data": processed_hits,
        })
        
    except ValueError as e:
        # CQL validation error (from build_cql)
        logger.warning(f"CQL validation: {e}")
        return jsonify({"error": "invalid_cql", "message": str(e), "draw": draw}), 400
        
    except httpx.TimeoutException:
        logger.error("BLS timeout during DataTables request")
        return jsonify({
            "error": "upstream_timeout",
            "message": "BlackLab Server did not respond in time"
        }), 504
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            # CQL syntax error
            try:
                bls_error = e.response.json().get("error", {})
                detail = bls_error.get("message", str(e))
            except:
                detail = e.response.text[:200]
            return jsonify({
                "error": "invalid_cql",
                "message": f"CQL syntax error: {detail}"
            }), 400
        else:
            logger.error(f"BLS HTTP {e.response.status_code}")
            return jsonify({
                "error": "upstream_error",
                "message": f"BlackLab Server error: {e.response.status_code}"
            }), 502
            
    except Exception as e:
        logger.exception("Unexpected error in DataTables endpoint")
        return jsonify({
            "error": "server_error",
            "message": "An unexpected error occurred"
        }), 500


@bp.route("/export", methods=["GET"])
@limiter.limit("6 per minute")  # Export rate limit: 6/min (separate from /data)
def export_data():
    """
    Stream full search results as CSV or TSV.
    
    Hardening (2025-11-10):
    - Punkt 1: Content-Disposition mit sprechendem Dateinamen, Cache-Control: no-store
    - Punkt 8: Logging von Export-Zeilen, BLS-Duration, Client-Disconnect
    
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
            return jsonify({
                "error": "invalid_cql",
                "message": str(e),
            }), 400
        
        # Build filters
        filters = build_filters(request.args)
        
        # Punkt 3: Validierung Filter Values
        try:
            validate_filter_values(filters)
        except CQLValidationError as e:
            logger.warning(f"Export filter validation failed: {e}")
            return jsonify({
                "error": "invalid_filter",
                "message": str(e),
            }), 400
        
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
        
        # Streaming generator function
        def generate_export() -> Generator[str, None, None]:
            """Stream CSV rows, fetching from BLS in chunks."""
            
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
            
            # Stream hits in chunks
            total_exported = 0
            first = 0
            export_start_time = time.time()
            
            try:
                while total_exported < GLOBAL_HITS_CAP:
                    chunk_start = time.time()
                    
                    # Fetch chunk
                    bls_params = {
                        "first": first,
                        "number": EXPORT_CHUNK_SIZE,  # Punkt 1: Chunk-Size 1000 bestätigt
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
                            response = _make_bls_request("/corapan/hits", test_params)
                            break
                        except httpx.HTTPStatusError as e:
                            if e.response.status_code != 400:
                                raise
                            continue
                    
                    if response is None:
                        raise Exception("Could not determine BLS CQL parameter")
                    
                    # Punkt 8: BLS-Duration Logging
                    chunk_duration = time.time() - chunk_start
                    
                    data = response.json()
                    hits = data.get("hits", [])
                    summary = data.get("summary", {})
                    number_of_hits = summary.get("numberOfHits", 0)
                    
                    # Punkt 8: Log BLS-Anfrage Dauer und Trefferzahl
                    if first == 0:
                        logger.info(f"Export started: format={export_format}, total_hits={number_of_hits}, "
                                  f"filters={'yes' if filter_query else 'no'}")
                    
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
                    if total_exported >= number_of_hits:
                        break
                    
                    first += EXPORT_CHUNK_SIZE
                
                # Punkt 8: Export completion logging
                export_duration = time.time() - export_start_time
                logger.info(f"Export completed: {total_exported} lines in {export_duration:.2f}s "
                          f"({total_exported/export_duration:.0f} lines/sec)")
                
            except GeneratorExit:
                # Punkt 1: Client-Disconnect Handling
                export_duration = time.time() - export_start_time
                logger.warning(f"Export aborted by client after {total_exported} lines, {export_duration:.2f}s")
                raise
        
        # Punkt 1: Content-Disposition mit sprechendem Dateinamen + Cache-Control
        return Response(
            generate_export(),
            mimetype=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": f"{mime_type}; charset=utf-8",
                "Cache-Control": "no-store",  # Punkt 1: Kein Caching
            }
        )
        
    except ValueError as e:
        logger.warning(f"Export CQL validation: {e}")
        return jsonify({"error": "invalid_cql", "message": str(e)}), 400
        
    except httpx.TimeoutException:
        logger.error("BLS timeout during export")
        return jsonify({
            "error": "upstream_timeout",
            "message": "BlackLab Server did not respond in time"
        }), 504
        
    except httpx.HTTPStatusError as e:
        logger.error(f"BLS HTTP {e.response.status_code} during export")
        return jsonify({
            "error": "upstream_error",
            "message": f"BlackLab Server error: {e.response.status_code}"
        }), 502
        
    except Exception as e:
        logger.exception("Unexpected error in export endpoint")
        return jsonify({
            "error": "server_error",
            "message": "An unexpected error occurred during export"
        }), 500
