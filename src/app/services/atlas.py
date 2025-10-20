"""Atlas metadata services."""
from __future__ import annotations

from .database import open_db


def fetch_overview() -> dict[str, object]:
    with open_db("stats_all") as connection:
        cursor = connection.cursor()
        row = cursor.execute("SELECT total_word_count, total_duration_all FROM stats LIMIT 1").fetchone()
    if row is None:
        return {"total_word_count": 0, "total_duration_all": "0"}
    return {"total_word_count": row["total_word_count"], "total_duration_all": row["total_duration_all"]}


def fetch_country_stats() -> list[dict[str, object]]:
    from ..config.countries import code_to_name
    
    with open_db("stats_country") as connection:
        cursor = connection.cursor()
        rows = cursor.execute(
            "SELECT country_code, total_word_count, total_duration_country FROM stats_country ORDER BY country_code"
        ).fetchall()
    return [
        {
            "country_code": row["country_code"],
            "country_name": code_to_name(row["country_code"], fallback=row["country_code"]),
            "total_word_count": row["total_word_count"],
            "total_duration": row["total_duration_country"],
        }
        for row in rows
    ]


def fetch_file_metadata() -> list[dict[str, object]]:
    with open_db("stats_files") as connection:
        cursor = connection.cursor()
        rows = cursor.execute(
            """
            SELECT filename, country_code, radio, date, revision, word_count, duration
            FROM metadata
            ORDER BY date DESC
            """
        ).fetchall()
    return [
        {
            "filename": row["filename"],
            "country_code": row["country_code"],
            "radio": row["radio"],
            "date": row["date"],
            "revision": row["revision"],
            "word_count": row["word_count"],
            "duration": row["duration"],
        }
        for row in rows
    ]
