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


def build_sentence_context(hit: dict[str, Any]) -> dict[str, Any] | None:
    """
    Build sentence-based context for a BlackLab hit.

    Returns a dictionary with sentence-based context, or None if it fails.
    """
    try:
        match = hit.get("match", {})
        left = hit.get("left", {}) or hit.get("before", {})
        right = hit.get("right", {}) or hit.get("after", {})

        def arr(side, key):
            if isinstance(side, dict):
                return side.get(key, []) or []
            return []

        left_words, left_sent_ids, left_start, left_end = arr(left, "word"), arr(left, "sentence_id"), arr(left, "start_ms"), arr(left, "end_ms")
        match_words, match_sent_ids, match_start, match_end = arr(match, "word"), arr(match, "sentence_id"), arr(match, "start_ms"), arr(match, "end_ms")
        right_words, right_sent_ids, right_start, right_end = arr(right, "word"), arr(right, "sentence_id"), arr(right, "start_ms"), arr(right, "end_ms")

        if not match_words or not match_sent_ids:
            return None

        sent_id = match_sent_ids[0]
        if not sent_id:
            return None

        tokens = []
        for i, w in enumerate(left_words):
            tokens.append({
                "zone": "left", "word": w,
                "sentence_id": left_sent_ids[i] if i < len(left_sent_ids) else None,
                "start_ms": int(left_start[i]) if i < len(left_start) and left_start[i] is not None else None,
                "end_ms": int(left_end[i]) if i < len(left_end) and left_end[i] is not None else None,
            })
        for i, w in enumerate(match_words):
            tokens.append({
                "zone": "match", "word": w,
                "sentence_id": match_sent_ids[i] if i < len(match_sent_ids) else None,
                "start_ms": int(match_start[i]) if i < len(match_start) and match_start[i] is not None else None,
                "end_ms": int(match_end[i]) if i < len(match_end) and match_end[i] is not None else None,
            })
        for i, w in enumerate(right_words):
            tokens.append({
                "zone": "right", "word": w,
                "sentence_id": right_sent_ids[i] if i < len(right_sent_ids) else None,
                "start_ms": int(right_start[i]) if i < len(right_start) and right_start[i] is not None else None,
                "end_ms": int(right_end[i]) if i < len(right_end) and right_end[i] is not None else None,
            })

        sentence_tokens = [t for t in tokens if t["sentence_id"] == sent_id]
        if not sentence_tokens:
            return None

        match_indices = [i for i, t in enumerate(sentence_tokens) if t["zone"] == "match"]
        if not match_indices:
            return None

        first_match_idx = min(match_indices)
        last_match_idx = max(match_indices)

        left_tokens = sentence_tokens[:first_match_idx]
        right_tokens = sentence_tokens[last_match_idx + 1:]

        context_left = " ".join(t["word"] for t in left_tokens)
        context_right = " ".join(t["word"] for t in right_tokens)

        hit_start_ms = int(match_start[0]) if match_start and match_start[0] is not None else 0
        hit_end_ms = int(match_end[-1]) if match_end and match_end[-1] is not None else hit_start_ms

        context_start = min((t["start_ms"] for t in sentence_tokens if t["start_ms"] is not None), default=hit_start_ms)
        context_end = max((t["end_ms"] for t in sentence_tokens if t["end_ms"] is not None), default=hit_end_ms)

        return {
            "context_left": context_left,
            "context_right": context_right,
            "hit_start_ms": hit_start_ms,
            "hit_end_ms": hit_end_ms,
            "context_start": context_start,
            "context_end": context_end,
        }
    except Exception as e:
        logger.error(f"Error in build_sentence_context: {e}")
        return None


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
    # Match text may come as word array or fallback to tokid
    if match.get("word"):
        text = " ".join(match.get("word", []))
    else:
        # tokid may be present as list of ids or strings
        text = _safe_first(match.get("tokid", [])) if match.get("tokid") else _safe_first(match.get("word", []))
    lemma = " ".join(match.get("lemma", [])) if match.get("lemma") else ""
    pos = " ".join(match.get("pos", [])) if match.get("pos") else ""

    token_id = _safe_first(match.get("tokid", [])) or ""
    filename = _safe_first(match.get("filename", [])) or hit.get("docPid", "")
    # metadata fields may exist under match or under doc metadata
    # BL v5 may return 'country' or 'country_code' keys; support both
    # docInfo may be a dict or a list of dicts (v4 vs v5 shapes); handle both
    def _safe_doc_field(field_name: str) -> str:
        doc_info = hit.get("docInfo") or hit.get("docInfos") or {}
        if isinstance(doc_info, list):
            # take first dict element
            if doc_info and isinstance(doc_info[0], dict):
                return doc_info[0].get(field_name, "") or ""
            return ""
        if isinstance(doc_info, dict):
            return doc_info.get(field_name, "") or ""
        return ""

    country = _safe_first(match.get("country", [])) or _safe_first(match.get("country_code", [])) or _safe_doc_field("country") or _safe_doc_field("country_code")
    speaker_type = _safe_first(match.get("speaker_type", [])) or _safe_doc_field("speaker_type")
    speaker_sex = _safe_first(match.get("speaker_sex", [])) or _safe_first(match.get("sex", [])) or ""
    speaker_mode = _safe_first(match.get("speaker_mode", [])) or _safe_first(match.get("mode", [])) or ""
    speaker_discourse = _safe_first(match.get("speaker_discourse", [])) or _safe_first(match.get("discourse", [])) or ""

    # New sentence-based context logic
    sentence_context = build_sentence_context(hit)

    if sentence_context:
        context_left = sentence_context["context_left"]
        context_right = sentence_context["context_right"]
        start_ms = sentence_context["hit_start_ms"]
        end_ms = sentence_context["hit_end_ms"]
        context_start = sentence_context["context_start"]
        context_end = sentence_context["context_end"]
    else:
        # Fallback to legacy N-word-window logic
        def _extract_context(side):
            if not side:
                return ""
            if isinstance(side, dict) and side.get("word"):
                return " ".join(side.get("word", []))
            if isinstance(side, list) and all(isinstance(x, str) for x in side):
                return " ".join(side)
            if isinstance(side, list) and side and isinstance(side[0], dict) and side[0].get("word"):
                words = []
                for elem in side:
                    w = elem.get("word")
                    if isinstance(w, list):
                        words.extend(w)
                    elif isinstance(w, str):
                        words.append(w)
                return " ".join(words)
            return ""

        context_left = _extract_context(left)
        context_right = _extract_context(right)

        def _get_first_int(arr_name: str, default: int = 0) -> int:
            if isinstance(match.get(arr_name), list) and match.get(arr_name):
                try:
                    return int(match.get(arr_name)[0])
                except Exception:
                    return default
            return int(hit.get(arr_name.replace('_ms', ''), default))

        start_ms = _get_first_int("start_ms", 0)
        end_ms = _get_first_int("end_ms", 0)

        def _to_int(val, default=0):
            try:
                return int(val)
            except Exception:
                return default

        def _safe_last(arr):
            return arr[-1] if isinstance(arr, list) and arr else ""

        def _get_context_start(side) -> int:
            try:
                if isinstance(side, dict) and side.get("start_ms"):
                    return _to_int(_safe_first(side.get("start_ms", [])))
                if isinstance(side, list) and side and isinstance(side[0], dict):
                    return _to_int(_safe_first(side[0].get("start_ms", [])))
                if isinstance(side, dict) and side.get("end_ms"):
                    return _to_int(_safe_first(side.get("end_ms", [])))
            except Exception:
                pass
            return 0

        def _get_context_end(side) -> int:
            try:
                if isinstance(side, dict) and side.get("end_ms"):
                    return _to_int(_safe_last(side.get("end_ms", [])))
                if isinstance(side, list) and side and isinstance(side[-1], dict) and side[-1].get("end_ms"):
                    return _to_int(_safe_last(side[-1].get("end_ms", [])))
                if isinstance(side, dict) and side.get("start_ms"):
                    return _to_int(_safe_last(side.get("start_ms", [])))
                if isinstance(side, list) and side and isinstance(side[-1], dict) and side[-1].get("start_ms"):
                    return _to_int(_safe_last(side[-1].get("start_ms", [])))
            except Exception:
                pass
            return 0
        
        context_start = _get_context_start(left)
        context_end = _get_context_end(right)

    return {
        "token_id": token_id,
        "filename": filename,
        "country_code": country.lower() if isinstance(country, str) else country,
        "radio": _safe_first(match.get("radio", [])) or "",
        "date": _safe_first(match.get("date", [])) or "",
        "speaker_type": speaker_type,
        "speaker_sex": speaker_sex,
        "speaker_mode": speaker_mode,
        "speaker_discourse": speaker_discourse,
        # Legacy fields for backward compatibility
        "sex": speaker_sex,
        "mode": speaker_mode,
        "discourse": speaker_discourse,
        "text": text,
        # Provide both ms-specific fields and 'start'/'end' for backward compatibility
        "start": start_ms,
        "end": end_ms,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "context_left": context_left,
        "context_right": context_right,
        "context_start": context_start,
        "context_end": context_end,
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
        "listvalues": "tokid,start_ms,end_ms,word,lemma,pos,country_code,country_scope,country_parent_code,country_region_code,speaker_code,speaker_type,speaker_sex,speaker_mode,speaker_discourse,filename,radio,city,date",
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
