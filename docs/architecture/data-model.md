# Datenmodell

**Scope:** Datenbank-Schema (Auth, Analytics)  
**Source-of-truth:** `src/app/auth/models.py`, `src/app/analytics/models.py`, `migrations/*.sql`

## Übersicht

Die Anwendung nutzt **eine PostgreSQL-Datenbank** (oder SQLite im Dev) für:
- **Authentication:** Users, Tokens
- **Analytics:** Aggregierte Nutzungsstatistiken (DSGVO-konform)

**Corpus-Daten** (Transkripte, Annotationen) werden **nicht** in SQL gespeichert, sondern via BlackLab Server indexiert (JSON → Lucene).

---

## Auth-Schema

### users

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `user_id` | TEXT (UUID) | Primary Key |
| `username` | TEXT | Unique, Nicht-Null |
| `email` | TEXT | Optional, Unique |
| `password_hash` | TEXT | Argon2/bcrypt Hash |
| `role` | TEXT | "user", "editor", "admin" |
| `is_active` | BOOLEAN | Account aktiv? |
| `must_reset_password` | BOOLEAN | Password-Reset erzwingen |
| `created_at` | TIMESTAMP | Erstellungsdatum |
| `updated_at` | TIMESTAMP | Letzte Änderung |
| `last_login_at` | TIMESTAMP | Letzter Login |
| `access_expires_at` | TIMESTAMP | Temporäre Zugriffsbeschränkung |
| `valid_from` | TIMESTAMP | Account gültig ab |
| `login_failed_count` | INTEGER | Fehlgeschlagene Login-Versuche |
| `locked_until` | TIMESTAMP | Account-Sperre bis |
| `deleted_at` | TIMESTAMP | Soft-Delete Zeitpunkt |
| `deletion_requested_at` | TIMESTAMP | Löschanfrage Zeitpunkt |
| `display_name` | TEXT | Anzeigename (UI) |

**Indizes:**
- `idx_users_username` (lower(username))
- `idx_users_email` (lower(email))
- `idx_users_is_active`
- `idx_users_deleted_at`

**Datei:** `src/app/auth/models.py`, `migrations/0001_create_auth_schema_postgres.sql`

---

### refresh_tokens

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `token_id` | TEXT (UUID) | Primary Key |
| `user_id` | TEXT | Foreign Key → users.user_id |
| `token_hash` | TEXT | SHA-256 Hash des Tokens |
| `created_at` | TIMESTAMP | Erstellung |
| `expires_at` | TIMESTAMP | Ablaufdatum |
| `last_used_at` | TIMESTAMP | Letzte Nutzung |
| `revoked_at` | TIMESTAMP | Manuell revoked? |
| `user_agent` | TEXT | Browser/Client |
| `ip_address` | TEXT | IP bei Erstellung |
| `replaced_by` | TEXT | Token Rotation (neues Token-ID) |

**Foreign Key:** `ON DELETE CASCADE` (bei User-Löschung werden Tokens mitgelöscht)

**Datei:** `src/app/auth/models.py`

---

### reset_tokens (Placeholder)

Aktuell nicht aktiv genutzt, aber Schema vorhanden für zukünftiges Password-Reset Feature.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `token_id` | TEXT (UUID) | Primary Key |
| `user_id` | TEXT | Foreign Key → users.user_id |
| `token_hash` | TEXT | SHA-256 Hash |
| `created_at` | TIMESTAMP | Erstellung |
| `expires_at` | TIMESTAMP | Ablauf (z.B. 1h) |
| `used_at` | TIMESTAMP | Wurde eingelöst? |

---

## Analytics-Schema

### analytics_daily

**Variante 3a:** Nur aggregierte Zähler, **keine** personenbezogenen Daten, **keine** Suchinhalte.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `date` | DATE | Primary Key (Tag) |
| `visitors` | INTEGER | Anzahl Unique Besucher (Session-basiert) |
| `mobile` | INTEGER | Mobile Geräte |
| `desktop` | INTEGER | Desktop Geräte |
| `searches` | INTEGER | Anzahl Suchvorgänge |
| `audio_plays` | INTEGER | Audio-Segment-Wiedergaben |
| `errors` | INTEGER | 4xx/5xx Fehler |
| `created_at` | TIMESTAMP | Erste Erfassung |
| `updated_at` | TIMESTAMP | Letzte Aktualisierung |

**DSGVO-Konformität:**
- Keine IPs gespeichert
- Keine User-IDs (außer anonyme Session-Hashes)
- Keine Suchinhalte
- Keine personenbezogenen Daten

**Datei:** `src/app/analytics/models.py`, `migrations/0002_create_analytics_tables.sql`

---

## Corpus-Daten (nicht in SQL!)

**Wichtig:** Transkripte und Annotationen werden **nicht** in dieser Datenbank gespeichert.

**Speicherorte:**
- **JSON-Transkripte:** `media/transcripts/*.json`
- **BlackLab Index:** `data/blacklab_index/` (Lucene-basiert)

**Zugriff:**
- **Suche:** Via BlackLab Server REST API (`http://blacklab:8080/blacklab-server/`)
- **Audio:** Direkt vom Filesystem (`media/mp3-split/`)

---

## Beziehungen

```
users
  │
  ├── 1:N → refresh_tokens (Cascade Delete)
  └── 1:N → reset_tokens (Cascade Delete)

analytics_daily (standalone, keine Beziehungen)
```

---

## Migration

### Initial Setup

**PostgreSQL:**
```bash
psql -U corapan -d corapan_auth -f migrations/0001_create_auth_schema_postgres.sql
psql -U corapan -d corapan_auth -f migrations/0002_create_analytics_tables.sql
```

**SQLite (Dev):**
```bash
sqlite3 data/db/auth.db < migrations/0001_create_auth_schema_sqlite.sql
sqlite3 data/db/auth.db < migrations/0002_create_analytics_tables.sql
```

**Automatisiert (PowerShell):**
```powershell
.\scripts\dev-setup.ps1  # führt Migrationen automatisch aus
```

---

## SQLAlchemy Session Management

**Datei:** `src/app/extensions/sqlalchemy_ext.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

_engine = None
_SessionLocal = None

def init_engine(app):
    global _engine, _SessionLocal
    _engine = create_engine(app.config["AUTH_DATABASE_URL"])
    _SessionLocal = sessionmaker(bind=_engine)

@contextmanager
def get_session() -> Session:
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

**Verwendung:**
```python
from ..extensions.sqlalchemy_ext import get_session
from .models import User

with get_session() as session:
    user = session.query(User).filter_by(username="admin").first()
    print(user.role)
```

---

## Backup & Restore

### PostgreSQL

**Backup:**
```bash
pg_dump -U corapan -d corapan_auth > backup_$(date +%Y%m%d).sql
```

**Restore:**
```bash
psql -U corapan -d corapan_auth < backup_20260114.sql
```

### SQLite

**Backup:**
```bash
cp data/db/auth.db data/db/auth.db.backup
```

**Restore:**
```bash
cp data/db/auth.db.backup data/db/auth.db
```

---

## Extension Points

**Neue Tabellen hinzufügen:**
1. Model in `src/app/<modul>/models.py` definieren
2. Migration in `migrations/` erstellen
3. Auf Produktion anwenden (manuell oder via Alembic)

**Beispiel: Audit Logs**
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: str = mapped_column(String(36), primary_key=True)
    user_id: str
    action: str
    timestamp: datetime
```
