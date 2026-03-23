"""Statistics aggregation service for corpus data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .database import open_db


@dataclass(slots=True)
class StatsParams:
    """Parameters for statistics aggregation, matching SearchParams."""

    query: str = ""
    search_mode: str = "text"
    token_ids: Sequence[str] = ()
    countries: Sequence[str] = ()
    speaker_types: Sequence[str] = ()
    sexes: Sequence[str] = ()
    speech_modes: Sequence[str] = ()
    discourses: Sequence[str] = ()
    country_detail: str = ""  # If set, filter all stats to this single country


def _normalise(values: Sequence[str] | None) -> list[str]:
    """Normalise filter values, removing empty strings."""
    if values is None:
        return []
    return [value.strip() for value in values if value and value.strip()]


def _append_in_clause(
    filters: list[str],
    params: list[str],
    field: str,
    values: Sequence[str] | None,
) -> None:
    """Append IN clause to filters if values are provided."""
    if not values:
        return
    selection = [value for value in _normalise(values) if value.lower() != "all"]
    if not selection:
        return
    placeholders = ",".join(["?"] * len(selection))
    filters.append(f"{field} IN ({placeholders})")
    params.extend(selection)


def _build_word_query(
    words: list[str], column: str, exact: bool
) -> tuple[str, list[str]]:
    """Build SQL query for word/lemma matching. Reused from corpus_search logic."""
    if not words:
        return "", []
    if len(words) == 1:
        word = words[0]
        if exact:
            return f"SELECT * FROM tokens t WHERE t.{column} = ?", [word]
        return f"SELECT * FROM tokens t WHERE t.{column} LIKE ?", [f"%{word}%"]

    aliases = [f"t{i + 1}" for i in range(len(words))]
    conditions: list[str] = []
    params: list[str] = []
    for alias, word in zip(aliases, words):
        comparator = "=" if exact else "LIKE"
        value = word if exact else f"%{word}%"
        conditions.append(f"{alias}.{column} {comparator} ?")
        params.append(value)

    join_parts: list[str] = []
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


def aggregate_stats(params: StatsParams) -> dict[str, object]:
    """
    Aggregate corpus statistics based on search filters.

    Returns:
        Dictionary with total count and breakdowns by country, speaker_type, sexo, modo.
        Each dimension includes absolute counts (n) and proportions (p).
    """
    filters: list[str] = []
    filter_params: list[str] = []

    # Token-ID filters
    token_ids = _normalise(params.token_ids)
    if len(token_ids) > 2000:
        token_ids = token_ids[:2000]
    if token_ids:
        placeholders = ",".join(["?"] * len(token_ids))
        filters.append(f"t.token_id IN ({placeholders})")
        filter_params.extend(token_ids)

    # Document filters (country, speaker, sex, mode, discourse)
    # NOTE: Document metadata is stored directly in tokens table, no separate docs table
    _append_in_clause(filters, filter_params, "t.country_code", params.countries)
    _append_in_clause(filters, filter_params, "t.speaker_type", params.speaker_types)
    _append_in_clause(filters, filter_params, "t.sex", params.sexes)
    _append_in_clause(filters, filter_params, "t.mode", params.speech_modes)
    _append_in_clause(filters, filter_params, "t.discourse", params.discourses)

    # Country detail filter (adds additional constraint to further narrow results)
    # This allows filtering stats to a single country while preserving other filters
    if params.country_detail:
        filters.append("t.country_code = ?")
        filter_params.append(params.country_detail)

    # Word/lemma search
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

    # Build the hits CTE
    # NOTE: No separate docs table - we query tokens directly for token-level stats
    if sql_words:
        # Word search: use word_matches CTE
        # Filters need to reference 'wm' alias (word_matches)
        wm_filters = [f.replace("t.", "wm.") for f in filters]
        hits_cte = f"""
        WITH word_matches AS ({sql_words}),
        hits AS (
            SELECT wm.country_code, wm.speaker_type, wm.sex, wm.mode, wm.discourse
            FROM word_matches wm
            WHERE 1=1
            {" AND " + " AND ".join(wm_filters) if wm_filters else ""}
        )
        """
        all_params = word_params + filter_params
    else:
        # No word search, just doc filters on tokens
        if filters:
            hits_cte = f"""
            WITH hits AS (
                SELECT t.country_code, t.speaker_type, t.sex, t.mode, t.discourse
                FROM tokens t
                WHERE {" AND ".join(filters)}
            )
            """
            all_params = filter_params
        else:
            # No filters at all - count all tokens
            hits_cte = """
            WITH hits AS (
                SELECT country_code, speaker_type, sex, mode, discourse
                FROM tokens
            )
            """
            all_params = []

    # Aggregation queries
    # Note: Count tokens (not distinct filenames)
    sql_total = f"{hits_cte} SELECT COUNT(*) AS total FROM hits"

    sql_country = f"""
    {hits_cte}
    SELECT country_code AS key, COUNT(*) AS n
    FROM hits
    GROUP BY country_code
    ORDER BY n DESC
    """

    sql_speaker = f"""
    {hits_cte}
    SELECT speaker_type AS key, COUNT(*) AS n
    FROM hits
    GROUP BY speaker_type
    ORDER BY n DESC
    """

    sql_sexo = f"""
    {hits_cte}
    SELECT sex AS key, COUNT(*) AS n
    FROM hits
    GROUP BY sex
    ORDER BY n DESC
    """

    sql_modo = f"""
    {hits_cte}
    SELECT mode AS key, COUNT(*) AS n
    FROM hits
    GROUP BY mode
    ORDER BY n DESC
    """

    sql_discourse = f"""
    {hits_cte}
    SELECT discourse AS key, COUNT(*) AS n
    FROM hits
    GROUP BY discourse
    ORDER BY n DESC
    """

    with open_db("transcription") as conn:
        cursor = conn.cursor()

        # Total count
        cursor.execute(sql_total, all_params)
        total = cursor.fetchone()["total"]

        # Country breakdown
        cursor.execute(sql_country, all_params)
        by_country = [
            {
                "key": row["key"],
                "n": row["n"],
                "p": round(row["n"] / total, 3) if total > 0 else 0,
            }
            for row in cursor.fetchall()
        ]

        # Speaker type breakdown
        cursor.execute(sql_speaker, all_params)
        by_speaker_type = [
            {
                "key": row["key"],
                "n": row["n"],
                "p": round(row["n"] / total, 3) if total > 0 else 0,
            }
            for row in cursor.fetchall()
        ]

        # Sexo breakdown
        cursor.execute(sql_sexo, all_params)
        by_sexo = [
            {
                "key": row["key"],
                "n": row["n"],
                "p": round(row["n"] / total, 3) if total > 0 else 0,
            }
            for row in cursor.fetchall()
        ]

        # Modo breakdown
        cursor.execute(sql_modo, all_params)
        by_modo = [
            {
                "key": row["key"],
                "n": row["n"],
                "p": round(row["n"] / total, 3) if total > 0 else 0,
            }
            for row in cursor.fetchall()
        ]

        # Discourse breakdown
        cursor.execute(sql_discourse, all_params)
        by_discourse = [
            {
                "key": row["key"],
                "n": row["n"],
                "p": round(row["n"] / total, 3) if total > 0 else 0,
            }
            for row in cursor.fetchall()
        ]

    return {
        "total": total,
        "by_country": by_country,
        "by_speaker_type": by_speaker_type,
        "by_sexo": by_sexo,
        "by_modo": by_modo,
        "by_discourse": by_discourse,
    }
