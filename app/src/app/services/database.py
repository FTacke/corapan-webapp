"""SQLite database utilities for the CO.RA.PAN web app."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from ..runtime_paths import get_data_root


def get_public_db_root() -> Path:
    return get_data_root() / "db" / "public"

DATABASES = {
    "stats_files": lambda: get_public_db_root() / "stats_files.db",
    "stats_country": lambda: get_public_db_root() / "stats_country.db",
}


def get_connection(name: str) -> sqlite3.Connection:
    """Return a sqlite3 connection with row factory enabled."""
    path_factory = DATABASES.get(name)
    if path_factory is None:
        raise KeyError(f"Unknown database identifier: {name}")
    path = path_factory()
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
