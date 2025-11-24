"""SQLite database utilities for the CO.RA.PAN web app."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DATA_ROOT = Path(__file__).resolve().parents[3] / "data"
PRIVATE_DB_ROOT = DATA_ROOT / "db"
PUBLIC_DB_ROOT = DATA_ROOT / "db_public"

DATABASES = {
    "transcription": PRIVATE_DB_ROOT / "transcription.db",
    "stats_files": PRIVATE_DB_ROOT / "stats_files.db",
    "stats_country": PRIVATE_DB_ROOT / "stats_country.db",
    "stats_all": PUBLIC_DB_ROOT / "stats_all.db",
}


def get_connection(name: str) -> sqlite3.Connection:
    """Return a sqlite3 connection with row factory enabled."""
    path = DATABASES.get(name)
    if path is None:
        raise KeyError(f"Unknown database identifier: {name}")
    # If caller requests transcription DB, make sure the app didn't explicitly
    # disable that (EXPECT_TRANSCRIPTION_DB=False). When running with a Flask
    # app context we prefer to fail fast with a helpful message rather than
    # silently creating an empty DB file.
    if name == "transcription":
        try:
            # If app context is available, check the flag
            from flask import current_app

            expect = current_app.config.get("EXPECT_TRANSCRIPTION_DB", True)
        except Exception:
            # No app context — don't enforce the flag (legacy scripts/tests may need access)
            expect = True

        if not expect:
            raise RuntimeError(
                "transcription DB disabled (EXPECT_TRANSCRIPTION_DB=False). "
                "Corpus/search features require a prebuilt transcription DB or BlackLab index."
            )
    connection = sqlite3.connect(str(path), detect_types=sqlite3.PARSE_DECLTYPES)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def open_db(name: str) -> Iterator[sqlite3.Connection]:
    """Context manager that closes the connection automatically."""
    connection = get_connection(name)
    try:
        yield connection
    finally:
        connection.close()
