#!/usr/bin/env python3
"""Check database structure."""

import sqlite3
from pathlib import Path

db_path = Path("data/db/transcription.db")
if not db_path.exists():
    print("transcription.db not found at data/db/transcription.db — this DB is deprecated in the current layout.")
    print("If you need search/corpus DB locally, either create it via the full JSON->DB pipeline, use BlackLab, or run scripts/create_minimal_transcription_db.py for a tiny placeholder.")
    raise SystemExit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=== TABLES ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]
for table in tables:
    print(f"  - {table}")

if "tokens" in tables:
    print("\n=== tokens TABLE SCHEMA ===")
    cursor.execute("PRAGMA table_info(tokens)")
    for row in cursor.fetchall():
        print(f"  {row[1]:20} {row[2]:15} (nullable={row[3] == 0})")

    cursor.execute("SELECT COUNT(*) FROM tokens")
    print(f"\nTotal rows: {cursor.fetchone()[0]:,}")

    # Sample row
    cursor.execute("SELECT * FROM tokens LIMIT 1")
    sample = cursor.fetchone()
    if sample:
        print("\n=== SAMPLE ROW ===")
        cursor.execute("PRAGMA table_info(tokens)")
        col_names = [row[1] for row in cursor.fetchall()]
        for col, val in zip(col_names, sample):
            print(f"  {col:20} = {val}")

conn.close()
