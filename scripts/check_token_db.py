#!/usr/bin/env python3
import sqlite3
from pathlib import Path

repo = Path(r"c:\dev\corapan-webapp")
DB = repo / 'data' / 'db' / 'transcription.db'
print('DB path', DB)
con = sqlite3.connect(DB)
cur = con.cursor()

token = 'ven2252d1579'  # from user
# Try exact + uppercase
for t in [token, token.upper(), token.lower(), token.capitalize()]:
    cur.execute('SELECT filename, token_id FROM tokens WHERE token_id = ?', (t,))
    row = cur.fetchone()
    print('Try', t, '->', row)

# Search for token id substring
cur.execute('SELECT filename, token_id FROM tokens WHERE token_id LIKE ?', ('%2252d1579%',))
rows = cur.fetchall()
print('Substring matches:', len(rows))
for r in rows[:20]:
    print(r)

con.close()
print('Done')
