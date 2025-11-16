"""Corpus search services."""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .database import open_db
from .media_store import safe_audio_full_path, safe_transcript_path

logger = logging.getLogger(__name__)

# ============================================================================
# CANONICAL COLUMN DEFINITION - Core API Contract
# ============================================================================
# Diese Spalten garantieren stabile API-Keys, unabhängig von DB-Spaltenreihenfolge.
# Frontend erhält IMMER diese Keys in der JSON-Response.
# Bei Multi-Word-Sequenzen: Felder aus erstem und letztem Token kombiniert.
# ============================================================================
CANON_COLS = [
    "token_id",           # Eindeutige Token-ID (String)
    "filename",           # MP3-Datei (z.B. "ARG_pro_m_pre_general_001.mp3")
    "country_code",       # Land (z.B. "ARG", "MEX")
    "radio",              # Sender-Name
    "date",               # Datum
    "speaker_type",       # "pro" oder "otro"
    "sex",                # "m" oder "f"
    "mode",               # Registermodus ("pre", "lectura", "libre")
    "discourse",          # Diskurs-Typ ("general", "tiempo", "tránsito")
    "text",               # Suchresultat (ggf. Multi-Word-Sequenz: "Wort1 Wort2")
    "start",              # Start-Zeit erstes Wort (in Sekunden oder Frames)
    "end",                # End-Zeit letztes Wort (in Sekunden oder Frames)
    "context_left",       # Kontext vor dem Resultat (aus erstem Token)
    "context_right",      # Kontext nach dem Resultat (aus letztem Token)
    "context_start",      # Start-Zeit des Kontexts (erstes Token)
    "context_end",        # End-Zeit des Kontexts (letztes Token)
    "lemma",              # Lemma (nur für Suche relevant, nicht in DataTables angezeigt)
]

# Whitelist für ORDER BY Klausel (nur diese Felder erlaubt)
ALLOWED_SORT_FIELDS = set(CANON_COLS) - {"context_left", "context_right"}

# Mapping: User-Input → DB-Spalten (lokalisiert + englisch)
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


def _get_select_columns(alias: str = "t", exclude: set[str] | None = None) -> str:
    """
    Konstruiert eine Spaltenliste für SELECT mit expliziten Aliasen.
    Garantiert stabile Keys für JSON-Response, unabhängig von DB-Spaltenreihenfolge.
    
    Args:
        alias: Tabellenalias (z.B. "t1", "t2") für Multi-Word-Sequenzen
        exclude: Spalten, die ausgelassen werden sollen (z.B. {"context_left"})
    
    Returns:
        Komma-separierte SELECT-Spalten mit Aliasen: "col1 AS col1, col2 AS col2, ..."
    """
    exclude = exclude or set()
    cols = [c for c in CANON_COLS if c not in exclude]
    # Alias nutzen für Joins bei Multi-Word-Sequenzen, aber Keys bleiben konsistent
    return ", ".join(f"{alias}.{c} AS {c}" for c in cols)


def _get_db_schema(cursor) -> set[str]:
    """
    Prüft die tatsächlichen Spalten in der tokens-Tabelle.
    
    Returns:
        Set von vorhandenen Spaltennamen
    """
    cursor.execute("PRAGMA table_info(tokens)")
    return {row[1] for row in cursor.fetchall()}  # row[1] ist der Spaltenname


def _validate_db_schema(cursor, required_cols: list[str] | None = None) -> list[str]:
    """
    Validiert, dass die DB alle CANON_COLS + 'norm' hat.
    
    Args:
        cursor: DB-Cursor
        required_cols: Falls nicht gesetzt, nutze CANON_COLS
    
    Returns:
        Liste fehlender Spalten (leer = OK)
    
    Raises:
        RuntimeError: Falls kritische Spalten fehlen
    """
    required_cols = required_cols or CANON_COLS
    # Prüfe auch auf 'norm' für case/accent-insensitive Suche
    required_cols_with_norm = list(required_cols) + ["norm"]
    present = _get_db_schema(cursor)
    missing = [c for c in required_cols_with_norm if c not in present]
    
    if missing:
        msg = f"[DB SCHEMA] Missing columns {missing}. Present: {sorted(present)}"
        logger.error(msg)
        raise RuntimeError(msg)
    
    return []  # OK


SUPPORTED_ORDERS = {"asc", "desc"}
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass(slots=True)
class SearchParams:
    query: str
    search_mode: str = "text"
    sensitive: int = 1  # 1=sensitive (default), 0=case/accent-indifferent
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


def _normalize_for_search(text: str) -> str:
    """
    Normalisiert Text für case/accent-insensitive Suche (sensitive=0).
    Konvertiert zu lowercase und entfernt Akzente.
    
    Args:
        text: Input-Text
    
    Returns:
        Normalisierter Text
    """
    import unicodedata
    # Zu lowercase
    text = text.lower()
    # Akzente/Diakritika entfernen mittels NFD
    # NFD = Normalisierungsform decomposed
    nfkd = unicodedata.normalize('NFD', text)
    # Nur die Basis-Zeichen behalten (ohne combining marks)
    return ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')


def _build_word_query(words: list[str], column: str, exact: bool, sensitive: int = 1) -> tuple[str, list[str]]:
    """
    Konstruiert SQL für Word-Suche (single oder multi-word).
    Nutzt EXPLIZITE Spaltenlisten, nicht SELECT *.
    
    Args:
        words: Liste von Suchbegriffen
        column: Spaltenname (text, lemma) für sensitive=1, oder 'norm' für sensitive=0
        exact: Exakte Match oder LIKE?
        sensitive: 1=case/accent-sensitive (column=text/lemma), 0=indifferent (column=norm)
    
    Returns:
        (SQL_string, params_list)
    """
    if not words:
        return "", []
    
    # Bei sensitive=0: Nutze 'norm' statt 'text'/'lemma'
    # Normalisiere auch die Suchbegriffe
    if sensitive == 0:
        column = "norm"
        # Normalisiere Suchbegriffe: lowercase, strip accents
        words = [_normalize_for_search(w) for w in words]
    
    if len(words) == 1:
        word = words[0]
        select_cols = _get_select_columns()
        if exact:
            return f"SELECT {select_cols}, 1 as word_count FROM tokens t WHERE t.{column} = ?", [word]
        return f"SELECT {select_cols}, 1 as word_count FROM tokens t WHERE t.{column} LIKE ?", [f"%{word}%"]

    # Multi-word sequence: JOIN nachfolgende Tokens und sammle alle Texte
    aliases = [f"t{i + 1}" for i in range(len(words))]
    join_parts: list[str] = []
    conditions: list[str] = []
    params: list[str] = []
    
    # Sammle alle Texte für die Sequenz (t1.text || ' ' || t2.text || ...)
    text_parts = [f"{alias}.text" for alias in aliases]
    combined_text = " || ' ' || ".join(text_parts)
    
    # Sammle start von t1 und end von tn
    first_alias = aliases[0]
    last_alias = aliases[-1]
    
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
    
    # EXPLIZITE SPALTENLISTE: Nicht SELECT *, sondern alle CANON_COLS einzeln
    # Nutze first_alias für die meisten Felder, last_alias für context_right und end
    explicit_cols = []
    for col in CANON_COLS:
        if col == "text":
            # Kombinierte Sequenz
            explicit_cols.append(f"({combined_text}) as {col}")
        elif col == "end":
            # End vom letzten Wort
            explicit_cols.append(f"{last_alias}.{col} as {col}")
        elif col == "context_right":
            # Context-Right vom letzten Wort
            explicit_cols.append(f"{last_alias}.{col} as {col}")
        elif col == "context_end":
            # Context-End vom letzten Wort
            explicit_cols.append(f"{last_alias}.{col} as {col}")
        else:
            # Alle anderen vom first_alias
            explicit_cols.append(f"{first_alias}.{col} as {col}")
    
    select_list = ", ".join(explicit_cols)
    
    sql = (
        f"SELECT "
        f"{select_list}, "
        f"{len(words)} as word_count "
        f"{from_clause} {' '.join(join_parts)} "
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
        sql_words, word_params = _build_word_query(words, column, exact, sensitive=params.sensitive)

    # ORDER BY Logik mit Whitelist
    if token_ids:
        case_clauses = []
        case_params = []
        for i, tid in enumerate(token_ids):
            case_clauses.append(f"WHEN token_id = ? THEN {i}")
            case_params.append(tid)
        order_by_case = f"CASE {' '.join(case_clauses)} ELSE 999999 END"
        order_sql_full = f"{order_by_case}, start ASC"
    else:
        # WHITELIST: Nur ALLOWED_SORT_FIELDS erlauben
        sort_column_raw = (params.sort or "").lower()
        sort_column = SUPPORTED_SORTS.get(sort_column_raw, column)
        
        # Zusätzliche Validierung: Ist das Feld in CANON_COLS?
        if sort_column not in ALLOWED_SORT_FIELDS:
            logger.warning(f"Sort field '{sort_column}' not in whitelist, falling back to '{column}'")
            sort_column = column
        
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
        # AKTIVIERE Row-Factory für objekt-basierte Rückgabe
        import sqlite3
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        
        # SCHEMA VALIDIERUNG beim Start
        try:
            _validate_db_schema(cursor)
        except RuntimeError as e:
            logger.error(f"Schema validation failed: {e}")
            raise
        
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
            select_cols = _get_select_columns()
            # NOTE: _get_select_columns() uses alias 't' by default (e.g. "t.token_id"
            # as token_id). We must therefore alias the tokens table as 't' in the FROM
            # clause. Forgetting the alias caused: sqlite3.OperationalError: no such
            # column: t.token_id when the query was executed.
            base_sql = f"SELECT {select_cols}, 1 as word_count FROM tokens t WHERE 1=1{filter_clause}"
            count_sql = f"SELECT COUNT(*) FROM ({base_sql})"
            cursor.execute(count_sql, filter_params)
            total_results = cursor.fetchone()[0]

            data_sql = (
                f"{base_sql} ORDER BY {order_sql_full} LIMIT ? OFFSET ?"
            )
            cursor.execute(data_sql, bindings_for_data)
            rows = cursor.fetchall()

        def _row_to_dict(row: sqlite3.Row) -> dict[str, object]:
            """
            Konvertiert sqlite3.Row (Dict-like) zu normalem Dict mit allen CANON_COLS Keys.
            Row-Factory macht die Arbeit: row['fieldname'] funktioniert direkt.
            
            Garantiert:
            - Genau die Keys aus CANON_COLS in der Ausgabe
            - Stabil gegenüber DB-Spaltenreihenfolge-Änderungen
            - Zusätzliche Helper-Felder (audio_available, etc.)
            """
            # DB enthält jetzt MP3-Filenames (aus JSON-Metadaten)
            filename_from_db = str(row["filename"])
            stem = Path(filename_from_db).stem
            transcript_name = f"{stem}.json"
            
            # Extrahiere nur CANON_COLS aus Row, ignoriere Rest
            result = {}
            for col in CANON_COLS:
                try:
                    result[col] = row[col]
                except (IndexError, KeyError):
                    # Fallback falls Spalte nicht existiert
                    result[col] = None
            
            # Zusätzliche Helper-Felder (nicht in CANON_COLS)
            try:
                result["word_count"] = row["word_count"]
            except (IndexError, KeyError):
                result["word_count"] = 1
            
            # DB enthält jetzt MP3-Filenames direkt (aus JSON-Metadaten)
            # Kein Conversion mehr nötig!
            result["audio_available"] = safe_audio_full_path(filename_from_db) is not None
            result["transcript_available"] = safe_transcript_path(transcript_name) is not None
            result["transcript_name"] = transcript_name
            
            return result

        # Konvertiere Rows zu Dicts mit Objektkeys (nicht Tupel-Indizes)
        row_dicts = [_row_to_dict(row) for row in rows]

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
