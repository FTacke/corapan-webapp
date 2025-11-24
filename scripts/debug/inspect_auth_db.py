import sqlite3
from pathlib import Path
p=Path('data/db/auth.db')
print('exists', p.exists())
conn=sqlite3.connect(str(p))
cur=conn.cursor()
cur.execute("PRAGMA table_info(users)")
cols = cur.fetchall()
print('columns:')
for c in cols:
    print(' ', c)

col_names = [c[1] for c in cols]
cur.execute('SELECT * FROM users')
rows = cur.fetchall()
print('rows:', len(rows))
for r in rows:
    # print as dict
    print({name: val for name, val in zip(col_names, r)})
conn.close()
