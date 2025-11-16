"""
Advanced search Blueprint for CO.RA.PAN.

Provides BlackLab-powered corpus search via Flask proxy.
"""
from flask import Blueprint, render_template, request, jsonify, current_app
import httpx
from urllib.parse import urlencode

from .cql import build_cql, build_filters, filters_to_blacklab_query
from ..extensions import limiter
from ..extensions.http_client import get_http_client

bp = Blueprint("advanced_search", __name__, url_prefix="/search/advanced")


@bp.route("", methods=["GET"])
def index():
    """
    Render advanced search form.
    
    Returns:
        HTML template with MD3 form + empty results container
    """
    return render_template("search/advanced.html")


@bp.route("/results", methods=["GET"])
@limiter.limit("30 per minute")
def results():
    """
    Execute BlackLab search and return KWIC results fragment.
    
    Query parameters:
        - q: Query string
        - mode: 'forma_exacta' | 'forma' | 'lemma'
        - ci: Case insensitive (bool)
        - da: Diacritics insensitive (bool)
        - pos: POS tags (comma-separated)
        - country_code: ISO country code
        - radio: Radio station
        - speaker_code: Speaker ID
        - date_from: Start date (YYYY-MM-DD)
        - date_to: End date (YYYY-MM-DD)
        - hitstart: Pagination offset (default: 0)
        - maxhits: Max results per page (default: 50)
        
    Returns:
        HTML fragment with KWIC results + pagination
    """
    try:
        # Build document filters
        filters = build_filters(request.args)
        
        # Build CQL pattern with integrated speaker and metadata filters
        from .cql import build_cql_with_speaker_filter
        cql_pattern = build_cql_with_speaker_filter(request.args, filters)
        
        # Legacy filter query (deprecated, now integrated in CQL)
        filter_query = filters_to_blacklab_query(filters)
        
        # Pagination
        hitstart = int(request.args.get("hitstart", 0))
        maxhits = int(request.args.get("maxhits", 50))
        
        # BlackLab parameters - try multiple CQL parameter names for compatibility
        # Auto-detect which parameter BlackLab accepts (patt, cql, or cql_query)
        bls_params = {
            "first": hitstart,
            "number": maxhits,
            "wordsaroundhit": 10,  # Context words (left/right)
            "listvalues": "tokid,start_ms,end_ms,word,lemma,pos,country_code,country_scope,country_parent_code,country_region_code,speaker_code,speaker_type,speaker_sex,speaker_mode,speaker_discourse,filename,radio,city,date",
        }
        
        # Add filter if present
        if filter_query:
            bls_params["filter"] = filter_query
        
        # Call BlackLab via Flask proxy (use v5 API path)
        bls_url = f"{request.url_root}bls/corpora/corapan/hits"
        
        # Try CQL parameter names in order: patt (standard), cql, cql_query
        cql_param_names = ["patt", "cql", "cql_query"]
        response = None
        last_error = None
        
        # Use centrally configured HTTP client (proper timeout configuration)
        http_client = get_http_client()
        
        for param_name in cql_param_names:
            try:
                test_params = {**bls_params, param_name: cql_pattern}
                response = http_client.get(bls_url, params=test_params)
                response.raise_for_status()
                # Success - use this parameter name
                # Log only on first successful detection (debug level to avoid spam)
                current_app.logger.debug(f"BlackLab CQL parameter accepted: {param_name}")
                break
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 400:
                    # Bad request - try next parameter name
                    current_app.logger.debug(f"CQL parameter '{param_name}' not accepted, trying next")
                    continue
                else:
                    # Other error - re-raise
                    raise
        
        if response is None:
            # All parameter names failed
            raise last_error or Exception("Could not determine BlackLab CQL parameter name")
        
        # Parse JSON response
        data = response.json()
        
        # Extract hits
        hits = data.get("hits", [])
        summary = data.get("summary", {})
        
        # Serverfilter detection: if filter was applied and docsRetrieved < numberOfDocs
        # then server-side filtering is active
        server_filtered = False
        if filter_query:
            docs_retrieved = summary.get("docsRetrieved", 0)
            number_of_docs = summary.get("numberOfDocs", 0)
            server_filtered = docs_retrieved < number_of_docs
        
        # Process hits for template
        processed_hits = []
        for hit in hits:
            # Extract context
            left = hit.get("left", {}).get("word", [])
            match = hit.get("match", {}).get("word", [])
            right = hit.get("right", {}).get("word", [])
            
            # Extract metadata
            doc_pid = hit.get("docPid", "")
            start = hit.get("start", 0)
            end = hit.get("end", 0)
            
            # Extract additional fields (if available)
            match_info = hit.get("match", {})
            lemma = match_info.get("lemma", [])
            pos = match_info.get("pos", [])
            tokid = match_info.get("tokid", [])
            start_ms = match_info.get("start_ms", [])
            end_ms = match_info.get("end_ms", [])
            
            processed_hit = {
                "left": " ".join(left[-10:]) if left else "",  # Last 10 words
                "match": " ".join(match),
                "right": " ".join(right[:10]) if right else "",  # First 10 words
                "doc_pid": doc_pid,
                "start": start,
                "end": end,
                "lemma": " ".join(lemma) if lemma else "",
                "pos": " ".join(pos) if pos else "",
                "tokid": tokid[0] if tokid else "",
                "start_ms": start_ms[0] if start_ms else 0,
                "end_ms": end_ms[0] if end_ms else 0,
            }
            processed_hits.append(processed_hit)
        
        # Pagination info
        total_hits = summary.get("numberOfHits", 0)
        has_prev = hitstart > 0
        has_next = (hitstart + maxhits) < total_hits
        
        prev_start = max(0, hitstart - maxhits)
        next_start = hitstart + maxhits
        
        # Build pagination URLs
        current_params = dict(request.args)
        
        prev_params = {**current_params, "hitstart": prev_start}
        next_params = {**current_params, "hitstart": next_start}
        
        prev_url = f"/search/advanced/results?{urlencode(prev_params)}" if has_prev else None
        next_url = f"/search/advanced/results?{urlencode(next_params)}" if has_next else None
        
        return render_template(
            "search/_results.html",
            hits=processed_hits,
            total=total_hits,
            hitstart=hitstart,
            maxhits=maxhits,
            has_prev=has_prev,
            has_next=has_next,
            prev_url=prev_url,
            next_url=next_url,
            cql_pattern=cql_pattern,
            filters=filters,
            server_filtered=server_filtered,  # Server-side filter detection
            docs_retrieved=summary.get("docsRetrieved", 0),
            number_of_docs=summary.get("numberOfDocs", 0),
        )
    
    except ValueError as e:
        # Validation error (empty query, etc.)
        return render_template(
            "search/_results.html",
            error=str(e),
            hits=[],
            total=0,
        ), 400
    
    except httpx.HTTPStatusError as e:
        # BlackLab server error
        current_app.logger.error(f"BlackLab error: {e.response.status_code} - {e.response.text}")
        return render_template(
            "search/_results.html",
            error=f"BlackLab server error: {e.response.status_code}",
            hits=[],
            total=0,
        ), 502
    
    except httpx.TimeoutException:
        # Timeout
        current_app.logger.error("BlackLab request timeout")
        return render_template(
            "search/_results.html",
            error="Search timed out. Please try a more specific query.",
            hits=[],
            total=0,
        ), 504
    
    except Exception as e:
        # Unknown error
        current_app.logger.exception("Unexpected error in advanced search")
        return render_template(
            "search/_results.html",
            error="An unexpected error occurred. Please try again.",
            hits=[],
            total=0,
        ), 500
