"""Atlas metadata services."""

from __future__ import annotations

import logging
import sqlite3
from typing import Iterable

from flask import current_app, has_app_context

from .database import open_db


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
            "country_name": code_to_name(
                row["country_code"], fallback=row["country_code"]
            ),
            "total_word_count": row["total_word_count"],
            "total_duration": row["total_duration_country"],
        }
        for row in rows
    ]


def _table_has_columns(
    cursor: sqlite3.Cursor, table_name: str, required_columns: Iterable[str]
) -> bool:
    try:
        rows = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    except sqlite3.Error:
        return False
    existing = {row["name"] if isinstance(row, sqlite3.Row) else row[1] for row in rows}
    return set(required_columns).issubset(existing)


def _resolve_metadata_table(cursor: sqlite3.Cursor) -> str | None:
    required_columns = {
        "filename",
        "country_code",
        "radio",
        "date",
        "revision",
        "word_count",
        "duration",
    }
    tables = [
        row["name"] if isinstance(row, sqlite3.Row) else row[0]
        for row in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    ]
    if "metadata" in tables and _table_has_columns(cursor, "metadata", required_columns):
        return "metadata"
    for table in tables:
        if _table_has_columns(cursor, table, required_columns):
            return table
    return None


def fetch_file_metadata() -> list[dict[str, object]]:
    with open_db("stats_files") as connection:
        cursor = connection.cursor()
        table_name = _resolve_metadata_table(cursor)
        if not table_name:
            logger = current_app.logger if has_app_context() else logging.getLogger(__name__)
            logger.warning(
                "Atlas metadata table missing in stats_files.db; returning empty files list."
            )
            return []
        try:
            rows = cursor.execute(
                f"""
                SELECT filename, country_code, radio, date, revision, word_count, duration
                FROM {table_name}
                ORDER BY date DESC
                """
            ).fetchall()
        except sqlite3.Error as exc:
            logger = current_app.logger if has_app_context() else logging.getLogger(__name__)
            logger.warning(
                "Atlas metadata query failed for table '%s': %s",
                table_name,
                exc,
            )
            return []
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
