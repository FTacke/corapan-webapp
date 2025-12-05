import sqlite3
from pathlib import Path

p = Path("data/db/auth.db")
conn = sqlite3.connect(str(p))
cur = conn.cursor()
cur.execute(
    "UPDATE users SET must_reset_password=0, login_failed_count=0, locked_until=NULL WHERE username='admin'"
)
conn.commit()
cur.execute(
    "SELECT username, must_reset_password, login_failed_count, locked_until FROM users WHERE username='admin'"
)
print(cur.fetchone())
conn.close()
