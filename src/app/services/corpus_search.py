"""Corpus search services."""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .database import open_db
from .media_store import safe_audio_full_path, safe_transcript_path

SUPPORTED_SORTS = {
    # Support both Spanish UI names and English DB column names
    "palabra": "text",
    "text": "text",
    "modo": "mode",
    "mode": "mode",
    "discurso": "discourse",
    "discourse": "discourse",
    "hablante": "speaker_type",
    "speaker_type": "speaker_type",
    "sexo": "sex",
    "sex": "sex",
    "pais": "country_code",
    "country_code": "country_code",
    "archivo": "filename",
    "filename": "filename",
    "token_id": "token_id",
}
SUPPORTED_ORDERS = {"asc", "desc"}
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass(slots=True)
class SearchParams:
    query: str
    search_mode: str = "text"
    token_ids: Sequence[str] = ()
    countries: Sequence[str] = ()
    speaker_types: Sequence[str] = ()
    sexes: Sequence[str] = ()
    speech_modes: Sequence[str] = ()
    discourses: Sequence[str] = ()
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE
    sort: str | None = None
    order: str = "asc"
    table_search: str = ""  # DataTables search within results


def _normalise(values: Iterable[str] | None) -> list[str]:
    if values is None:
        return []
    return [value.strip() for value in values if value and value.strip()]


def _append_in_clause(
    filters: list[str],
    params: list[str],
    field: str,
    values: Sequence[str] | None,
) -> None:
    if not values:
        return
    selection = [value for value in _normalise(values) if value.lower() != "all"]
    if not selection:
        return
    placeholders = ",".join(["?"] * len(selection))
    filters.append(f"{field} IN ({placeholders})")
    params.extend(selection)


def _coerce_page(value: int) -> int:
    return max(1, value)


def _coerce_page_size(value: int) -> int:
    return min(max(1, value), MAX_PAGE_SIZE)


def _build_word_query(words: list[str], column: str, exact: bool) -> tuple[str, list[str]]:
    if not words:
        return "", []
    if len(words) == 1:
        word = words[0]
        if exact:
            return f"SELECT * FROM tokens t WHERE t.{column} = ?", [word]
        return f"SELECT * FROM tokens t WHERE t.{column} LIKE ?", [f"%{word}%"]

    aliases = [f"t{i + 1}" for i in range(len(words))]
    join_parts: list[str] = []
    conditions: list[str] = []
    params: list[str] = []
    for alias, word in zip(aliases, words):
        comparator = "=" if exact else "LIKE"
        value = word if exact else f"%{word}%"
        conditions.append(f"{alias}.{column} {comparator} ?")
        params.append(value)
    for left, right in zip(aliases, aliases[1:]):
        join_parts.append(
            f"JOIN tokens {right} ON {right}.filename = {left}.filename AND {right}.id = {left}.id + 1"
        )
    from_clause = f"FROM tokens {aliases[0]}"
    sql = (
        f"SELECT {aliases[0]}.* {from_clause} {' '.join(join_parts)} "
        f"WHERE {' AND '.join(conditions)}"
    )
    return sql, params


def _compute_display_pages(current: int, total: int) -> list[int | str]:
    if total <= 9:
        return list(range(1, total + 1))
    pages: list[int | str] = []
    if current > 4:
        pages.extend([1, "..."])
    start = max(1, current - 2)
    end = min(total, current + 2)
    pages.extend(range(start, end + 1))
    if end < total - 1:
        pages.extend(["...", total])
    elif end == total - 1:
        pages.append(total)
    return pages


def search_tokens(params: SearchParams) -> dict[str, object]:
    filters: list[str] = []
    filter_params: list[str] = []

    token_ids = _normalise(params.token_ids)
    # Token-Limit enforcement
    if len(token_ids) > 2000:
        token_ids = token_ids[:2000]
    
    # Direct Token-ID Matching (case-sensitive for index usage)
    # Note: Token-IDs in DB are case-sensitive, so we search as-is
    if token_ids:
        placeholders = ",".join(["?"] * len(token_ids))
        filters.append(f"token_id IN ({placeholders})")
        filter_params.extend(token_ids)

    _append_in_clause(filters, filter_params, "country_code", params.countries)
    _append_in_clause(filters, filter_params, "speaker_type", params.speaker_types)
    _append_in_clause(filters, filter_params, "sex", params.sexes)
    _append_in_clause(filters, filter_params, "mode", params.speech_modes)
    _append_in_clause(filters, filter_params, "discourse", params.discourses)
    
    # DataTables table search (search within all visible columns)
    if params.table_search:
        search_term = f"%{params.table_search}%"
        table_search_conditions = [
            "text LIKE ?",
            "context_left LIKE ?",
            "context_right LIKE ?",
            "country_code LIKE ?",
            "speaker_type LIKE ?",
            "sex LIKE ?",
            "mode LIKE ?",
            "discourse LIKE ?",
            "token_id LIKE ?",
            "filename LIKE ?",
        ]
        filters.append(f"({' OR '.join(table_search_conditions)})")
        filter_params.extend([search_term] * len(table_search_conditions))

    filter_clause = " AND ".join(filters)
    if filter_clause:
        filter_clause = " AND " + filter_clause

    words = params.query.split()
    column = "text"
    exact = False
    if params.search_mode == "text_exact":
        column, exact = "text", True
    elif params.search_mode == "lemma":
        column, exact = "lemma", False
    elif params.search_mode == "lemma_exact":
        column, exact = "lemma", True

    sql_words, word_params = ("", [])
    if params.query.strip():
        sql_words, word_params = _build_word_query(words, column, exact)

    # ORDER BY Logik: Token-IDs mit CASE für Input-Reihenfolge
    if token_ids:
        case_clauses = []
        case_params = []
        for i, tid in enumerate(token_ids):
            case_clauses.append(f"WHEN token_id = ? THEN {i}")
            case_params.append(tid)
        order_by_case = f"CASE {' '.join(case_clauses)} ELSE 999999 END"
        order_sql_full = f"{order_by_case}, start ASC"
    else:
        sort_column = SUPPORTED_SORTS.get((params.sort or "").lower(), column)
        order = params.order.lower() if params.order.lower() in SUPPORTED_ORDERS else "asc"
        order_sql_dir = "DESC" if order == "desc" else "ASC"
        order_sql_full = f"{sort_column} {order_sql_dir}"

    page = _coerce_page(params.page)
    page_size = _coerce_page_size(params.page_size)
    offset = (page - 1) * page_size

    # Bindings: word_params + filter_params + case_params (falls Token-Suche)
    bindings_for_count = word_params + filter_params
    if token_ids:
        bindings_for_data = bindings_for_count + case_params + [page_size, offset]
        bindings_for_all = bindings_for_count + case_params
    else:
        bindings_for_data = bindings_for_count + [page_size, offset]
        bindings_for_all = bindings_for_count

    with open_db("transcription") as connection:
        connection.row_factory = None
        cursor = connection.cursor()
        if sql_words:
            count_sql = f"SELECT COUNT(*) FROM ({sql_words}) AS base WHERE 1=1{filter_clause}"
            cursor.execute(count_sql, bindings_for_count)
            total_results = cursor.fetchone()[0]

            data_sql = (
                "SELECT * FROM (" + sql_words + ") AS base "
                f"WHERE 1=1{filter_clause} ORDER BY {order_sql_full} LIMIT ? OFFSET ?"
            )
            cursor.execute(data_sql, bindings_for_data)
            rows = cursor.fetchall()
        else:
            base_sql = f"SELECT * FROM tokens WHERE 1=1{filter_clause}"
            count_sql = f"SELECT COUNT(*) FROM ({base_sql})"
            cursor.execute(count_sql, filter_params)
            total_results = cursor.fetchone()[0]

            data_sql = (
                f"{base_sql} ORDER BY {order_sql_full} LIMIT ? OFFSET ?"
            )
            cursor.execute(data_sql, bindings_for_data)
            rows = cursor.fetchall()

    def _row_to_dict(row_tuple: tuple[object, ...]) -> dict[str, object]:
        (
            row_id,
            token_id,
            filename,
            country_code,
            radio,
            date,
            speaker_type,
            sex,
            mode,
            discourse,
            text,
            start,
            end,
            context_left,
            context_right,
            context_start,
            context_end,
            lemma,
        ) = row_tuple
        stem = Path(str(filename)).stem
        transcript_name = f"{stem}.json"
        return {
            "id": row_id,
            "token_id": token_id,
            "filename": filename,
            "country_code": country_code,
            "radio": radio,
            "date": date,
            "speaker_type": speaker_type,
            "sex": sex,
            "mode": mode,
            "discourse": discourse,
            "text": text,
            "start": start,
            "end": end,
            "context_left": context_left,
            "context_right": context_right,
            "context_start": context_start,
            "context_end": context_end,
            "lemma": lemma,
            "audio_available": safe_audio_full_path(str(filename)) is not None,
            "transcript_available": safe_transcript_path(transcript_name) is not None,
            "transcript_name": transcript_name,
        }

    row_dicts = [_row_to_dict(tuple(row)) for row in rows]

    total_pages = math.ceil(total_results / page_size) if page_size else 1
    display_pages = _compute_display_pages(page, total_pages)

    # Note: unique_countries/files now based on current page only (not all results)
    # For true totals, use server-side DataTables endpoint
    unique_countries = len({row["country_code"] for row in row_dicts})
    unique_files = len({row["filename"] for row in row_dicts})

    return {
        "items": row_dicts,
        "all_items": row_dicts,  # Now same as items (no ALL RESULTS loading)
        "total": total_results,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "display_pages": display_pages,
        "unique_countries": unique_countries,
        "unique_files": unique_files,
    }
