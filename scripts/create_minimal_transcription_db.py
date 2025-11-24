"""Create a minimal transcription.db with the canonical tokens schema.

This helper is intentionally small: it creates `data/db/transcription.db` if
missing and ensures the `tokens` table contains all CANON_COLS + `norm` and
creates a `idx_tokens_norm` index used by the app startup check.

Usage (PowerShell):
  python scripts/create_minimal_transcription_db.py

"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def create_minimal_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_id TEXT UNIQUE,
                filename TEXT,
                country_code TEXT,
                radio TEXT,
                date TEXT,
                speaker_type TEXT,
                sex TEXT,
                mode TEXT,
                discourse TEXT,
                text TEXT,
                start REAL,
                end REAL,
                context_left TEXT,
                context_right TEXT,
                context_start REAL,
                context_end REAL,
                norm TEXT,
                lemma TEXT
            );
            """
        )
        # Create index for norm (startup validation expects this index may be present)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tokens_norm ON tokens(norm)")
        conn.commit()
        print(f"Created or validated minimal transcription DB at: {path}")
    finally:
        conn.close()


if __name__ == "__main__":
    create_minimal_db(Path("data/db/transcription.db"))
