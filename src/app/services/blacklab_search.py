"""BlackLab search helpers.

Provides a wrapper to call BlackLab via the Flask proxy and return results
formatted like the existing `search_tokens` service (CANON_COLS format).
"""
from __future__ import annotations

import logging
import math
from typing import Any

from flask import current_app, request
from ..extensions.http_client import get_http_client
from ..search.cql import build_cql_with_speaker_filter, build_filters
from ..services.corpus_search import CANON_COLS

logger = logging.getLogger(__name__)


def _build_simple_cql(query: str, search_mode: str, sensitive: int) -> str:
    """Build a CQL string for a simple one-line query.

    This matches legacy behaviour:
    - `text` -> contains, using `word` or `norm` (regex `.*value.*`)
    - `text_exact` -> exact, `word="value"`
    - `lemma_exact` / `lemma` -> use `lemma="value"` (exact match)
    """
    from ..search.cql import tokenize_query, escape_cql

    tokens = tokenize_query(query)
    if not tokens:
        return ""

    parts = []
    for token in tokens:
        # Use regex for contains (text), equality for exact/lemma
        if search_mode == "text":
            # Simple text mode: default to exact token match (not regex)
            # TODO: Implement 'contains' semantics using regex or a suitable CQL operator
            field = "word" if sensitive == 1 else "norm"
            val = escape_cql(token)
        elif search_mode == "text_exact":
            field = "word"
            val = escape_cql(token)
        elif search_mode in ("lemma", "lemma_exact"):
            field = "lemma"
            val = escape_cql(token).lower()
        else:
            # fallback to word contains
            field = "word" if sensitive == 1 else "norm"
            val = f'.*{escape_cql(token)}.*'

        parts.append(f'[{field}="{val}"]')
    return " ".join(parts)


def _hit_to_canonical(hit: dict[str, Any]) -> dict[str, Any]:
    """Map a BlackLab hit to canonical CANON_COLS keys.

    Uses robust fallbacks if particular arrays are missing.
    """
    # Attempt to extract per-hit fields
    match = hit.get("match", {})
    # Support both BlackLab v4 (left/right) and v5 (before/after)
    left = hit.get("left", {}) or hit.get("before", {})
    right = hit.get("right", {}) or hit.get("after", {})

    def _safe_first(arr):
        return arr[0] if isinstance(arr, list) and arr else ""

    # Compose text and lemma
    text = " ".join(match.get("word", [])) if match.get("word") else _safe_first(match.get("tokid", []))
    lemma = " ".join(match.get("lemma", [])) if match.get("lemma") else ""
    pos = " ".join(match.get("pos", [])) if match.get("pos") else ""

    token_id = _safe_first(match.get("tokid", [])) or ""
    filename = _safe_first(match.get("filename", [])) or hit.get("docPid", "")
    # metadata fields may exist under match or under doc metadata
    country = _safe_first(match.get("country", [])) or hit.get("docInfo", {}).get("country", "")
    speaker_type = _safe_first(match.get("speaker_type", [])) or hit.get("docInfo", {}).get("speaker_type", "")
    sex = _safe_first(match.get("sex", [])) or ""
    mode = _safe_first(match.get("mode", [])) or ""
    discourse = _safe_first(match.get("discourse", [])) or ""

    context_left = " ".join(left.get("word", [])) if left.get("word") else ""
    context_right = " ".join(right.get("word", [])) if right.get("word") else ""

    # Start/End times: prefer start_ms/end_ms in match arrays (milliseconds),
    # fall back to top-level start/end if present (could be token offsets).
    def _get_first_int(arr_name: str, default: int = 0) -> int:
        if isinstance(match.get(arr_name), list) and match.get(arr_name):
            try:
                return int(match.get(arr_name)[0])
            except Exception:
                return default
        return int(hit.get(arr_name.replace('_ms', ''), default))

    start_ms = _get_first_int("start_ms", 0)
    end_ms = _get_first_int("end_ms", 0)

    return {
        "token_id": token_id,
        "filename": filename,
        "country_code": country.lower() if isinstance(country, str) else country,
        "radio": _safe_first(match.get("radio", [])) or "",
        "date": _safe_first(match.get("date", [])) or "",
        "speaker_type": speaker_type,
        "sex": sex,
        "mode": mode,
        "discourse": discourse,
        "text": text,
        # Provide both ms-specific fields and 'start'/'end' for backward compatibility
        "start": start_ms,
        "end": end_ms,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "context_left": context_left,
        "context_right": context_right,
        "context_start": _safe_first(left.get("start_ms", [])) or 0,
        "context_end": _safe_first(right.get("end_ms", [])) or 0,
        "lemma": lemma,
    }


def search_blacklab(params: Any) -> dict[str, Any]:
    """Execute a BlackLab hits query and return results in canonical format.

    Args:
        params: Should contain keys similar to SearchParams/dataclass.
    Returns:
        Dict with keys: items, all_items, total, page, page_size, total_pages, display_pages
    """
    http = get_http_client()
    # Map pagination
    page = int(params.get("page", 1)) if isinstance(params.get("page", (1)), int) or str(params.get("page", "1")) else 1
    page = max(1, int(page))
    page_size = int(params.get("page_size", params.get("pageSize", 25))) if params else 25
    first = (page - 1) * page_size

    # Build CQL
    # Map old search_mode to CQL style
    search_mode = params.get("search_mode") or params.get("search_type") or "text"
    if search_mode == "text":
        mode = "text"
    elif search_mode == "text_exact":
        mode = "text_exact"
    elif search_mode in ("lemma", "lemma_exact", "lemma_exact"):
        mode = "lemma"
    else:
        mode = search_mode

    sensitive = int(params.get("sensitive", params.get("sensitive", 1)))

    query = params.get("query") or params.get("q") or ""

    # Use cql builder when advanced 'cql' mode in params
    if params.get("mode") == "cql" or params.get("q", "").startswith("["):
        cql = params.get("q")
    else:
        # Build simple cql manually
        cql = _build_simple_cql(query, search_mode, sensitive)

    # Build filters and integrate into CQL
    filter_params = build_filters(params)
    merged = build_cql_with_speaker_filter({"q": query, "mode": mode, "sensitive": sensitive}, filter_params)
    if merged:
        cql = merged

    # Use 'corpora' path segment for BlackLab v5 API via proxy
    bls_url = f"{request.url_root}bls/corpora/corapan/hits"

    bls_params = {
        "first": first,
        "number": page_size,
        "wordsaroundhit": 10,
        # Ensure we request the fields we need for canonical mapping
        "listvalues": "tokid,start_ms,end_ms,word,lemma,pos,country,speaker_type,sex,mode,discourse,filename,radio",
    }

    # Add CQL param as patt/cql/cql_query fallback handled by upper layer
    bls_params["patt"] = cql

    # Add filter param if present (deprecated), use filter only if build filters returned any
    # Not needed: blacklab filter doc-level maybe included in CQL

    response = http.get(bls_url, params=bls_params)
    response.raise_for_status()
    data = response.json()

    summary = data.get("summary") or data.get("resultsStats", {})
    total = summary.get("hits") or summary.get("numberOfHits") or 0
    hits = data.get("hits", [])

    items = []
    for h in hits:
        items.append(_hit_to_canonical(h))

    total_pages = math.ceil(total / page_size) if page_size else 1
    # compute display pages similar to corpus_search._compute_display_pages
    from .corpus_search import _compute_display_pages as _dp
    display_pages = _dp(page, total_pages)

    unique_countries = len({it.get("country_code") for it in items if it.get("country_code")})
    unique_files = len({it.get("filename") for it in items if it.get("filename")})

    return {
        "items": items,
        "all_items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "display_pages": display_pages,
        "unique_countries": unique_countries,
        "unique_files": unique_files,
    }
