"""SQLite database utilities for the CO.RA.PAN web app."""

from __future__ import annotations

import os
import sqlite3
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def _resolve_data_root() -> Path:
    """Resolve runtime data root from CORAPAN_RUNTIME_ROOT (dev fallback supported)."""
    env_name = (os.getenv("FLASK_ENV") or os.getenv("APP_ENV") or "production").lower()
    is_dev = env_name in ("development", "dev")
    runtime_root = os.getenv("CORAPAN_RUNTIME_ROOT")

    if runtime_root:
        return Path(runtime_root) / "data"
    if is_dev:
        data_root = Path(__file__).resolve().parents[3] / "runtime" / "corapan" / "data"
        warnings.warn(
            "CORAPAN_RUNTIME_ROOT not configured. Defaulting to repo-local runtime path for development: "
            f"{data_root}",
            RuntimeWarning,
        )
        return data_root
    raise RuntimeError(
        "CORAPAN_RUNTIME_ROOT environment variable not configured.\n"
        "Runtime data is required for stats databases.\n\n"
        "Options:\n"
        "  1. Set CORAPAN_RUNTIME_ROOT (preferred):\n"
        "     export CORAPAN_RUNTIME_ROOT=/runtime/path\n"
        "     # Then data paths resolve to ${CORAPAN_RUNTIME_ROOT}/data\n"
    )


DATA_ROOT = _resolve_data_root()
PUBLIC_DB_ROOT = DATA_ROOT / "db" / "public"

DATABASES = {
    "stats_files": PUBLIC_DB_ROOT / "stats_files.db",
    "stats_country": PUBLIC_DB_ROOT / "stats_country.db",
}


def get_connection(name: str) -> sqlite3.Connection:
    """Return a sqlite3 connection with row factory enabled."""
    path = DATABASES.get(name)
    if path is None:
        raise KeyError(f"Unknown database identifier: {name}")
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
