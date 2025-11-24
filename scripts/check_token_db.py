#!/usr/bin/env python3
import sqlite3
from pathlib import Path

repo = Path(r"c:\dev\corapan-webapp")
DB = repo / "data" / "db" / "transcription.db"
print("DB path", DB)
if not DB.exists():
    print("transcription.db not found. This repository no longer requires data/db/transcription.db for Variant A (auth-only dev).")
    print("To inspect a real corpus DB, create it with the full JSON->DB pipeline or use BlackLab. For quick local tests you can use scripts/create_minimal_transcription_db.py")
    raise SystemExit(1)

con = sqlite3.connect(DB)
cur = con.cursor()

token = "ven2252d1579"  # from user
# Try exact + uppercase
for t in [token, token.upper(), token.lower(), token.capitalize()]:
    cur.execute("SELECT filename, token_id FROM tokens WHERE token_id = ?", (t,))
    row = cur.fetchone()
    print("Try", t, "->", row)

# Search for token id substring
cur.execute(
    "SELECT filename, token_id FROM tokens WHERE token_id LIKE ?", ("%2252d1579%",)
)
rows = cur.fetchall()
print("Substring matches:", len(rows))
for r in rows[:20]:
    print(r)

con.close()
print("Done")
