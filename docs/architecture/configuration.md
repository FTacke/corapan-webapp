# Konfiguration

**Scope:** Environment Variables, Secrets, Config-Layering  
**Source-of-truth:** `src/app/config/__init__.py`, `.env` (lokal), Docker Compose

## Config-Architektur

Die Anwendung nutzt ein **3-Layer Config System**:

1. **Defaults** (in Code): `BaseConfig` / `DevConfig` in `src/app/config/__init__.py`
2. **Environment Variables**: Überschreiben Defaults via ENV-Vars
3. **Runtime Detection**: `FLASK_ENV` bestimmt Config-Klasse

### Config-Klassen

```python
# src/app/config/__init__.py

class BaseConfig:
    """Production Defaults"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    JWT_COOKIE_SECURE = True
    # ...

class DevConfig(BaseConfig):
    """Development Overrides"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    JWT_COOKIE_SECURE = False
    # ...
```

**Auswahl:** Via `FLASK_ENV` Environment Variable:
- `FLASK_ENV=production` → `BaseConfig`
- `FLASK_ENV=development` → `DevConfig`

---

## Environment Variables

### Kritische Secrets (REQUIRED)

| Variable | Required | Default | Format | Zweck |
|----------|----------|---------|--------|-------|
| `FLASK_SECRET_KEY` | **Ja** | *(fehlt)* | String (min. 32 Zeichen) | Session-Signierung, CSRF |
| `JWT_SECRET_KEY` | **Ja** | *(fällt zurück auf `FLASK_SECRET_KEY`)* | String (min. 32 Zeichen) | JWT-Token-Signierung |
| `AUTH_DATABASE_URL` | Nein | `sqlite:///data/db/auth.db` | SQLAlchemy DSN | Auth-Datenbank (PostgreSQL empfohlen) |

**Wichtig:** In Produktion **niemals** Defaults nutzen! Secrets müssen via ENV-Vars gesetzt werden.

**Generierung (PowerShell):**
```powershell
# 32-Byte zufälliger String (hex-encoded)
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### Auth & JWT

| Variable | Default | Format | Zweck | Datei |
|----------|---------|--------|-------|-------|
| `JWT_ACCESS_TOKEN_EXPIRES` | `3600` | Sekunden | Access Token Lifetime (1h) | `src/app/config/__init__.py` |
| `JWT_REFRESH_TOKEN_EXPIRES` | `604800` | Sekunden | Refresh Token Lifetime (7d) | `src/app/config/__init__.py` |
| `AUTH_HASH_ALGO` | `argon2` | `argon2` oder `bcrypt` | Password Hashing Algorithmus | `src/app/config/__init__.py` |
| `AUTH_ARGON2_TIME_COST` | `2` | Integer | Argon2 Iterations | `src/app/config/__init__.py` |
| `AUTH_ARGON2_MEMORY_COST` | `102400` | KB | Argon2 Memory (100 MB) | `src/app/config/__init__.py` |
| `AUTH_ARGON2_PARALLELISM` | `4` | Integer | Argon2 Threads | `src/app/config/__init__.py` |
| `AUTH_ACCOUNT_ANONYMIZE_AFTER_DAYS` | `30` | Tage | Soft-Delete Anonymisierung | `src/app/config/__init__.py` |

**Session/Cookie Settings:**
```python
SESSION_COOKIE_SECURE = True     # Nur HTTPS (Produktion)
SESSION_COOKIE_SAMESITE = "lax"  # CSRF-Schutz
SESSION_COOKIE_HTTPONLY = True   # JS-Access verhindern

JWT_COOKIE_SECURE = True         # Nur HTTPS (Produktion)
JWT_COOKIE_CSRF_PROTECT = True   # CSRF-Token in Cookie
JWT_COOKIE_SAMESITE = "Lax"
```

**Dev-Overrides:**
```python
# DevConfig
SESSION_COOKIE_SECURE = False  # HTTP erlauben
JWT_COOKIE_SECURE = False
JWT_COOKIE_CSRF_PROTECT = False  # vereinfacht lokales Testen
```

---

### Datenbank

| Variable | Default | Format | Zweck | Datei |
|----------|---------|--------|-------|-------|
| `AUTH_DATABASE_URL` | `sqlite:///.../data/db/auth.db` | SQLAlchemy DSN | Auth & Analytics DB | `src/app/config/__init__.py` |

**DSN-Formate:**
```bash
# PostgreSQL (empfohlen für Produktion)
AUTH_DATABASE_URL="postgresql://user:pass@localhost:5432/corapan_auth"

# PostgreSQL (mit psycopg2)
AUTH_DATABASE_URL="postgresql+psycopg2://user:pass@localhost/corapan_auth"

# SQLite (Dev-Fallback)
AUTH_DATABASE_URL="sqlite:///data/db/auth.db"
```

**Hinweis:** Die Anwendung nutzt **eine** Datenbank für:
- Auth (Users, Tokens)
- Analytics (Daily Aggregates)

**Corpus-Daten:** Werden **nicht** in SQL gespeichert, sondern via BlackLab Server indexiert (JSON → Lucene).

---

### Pfade & Verzeichnisse

| Variable | Default | Format | Zweck | Datei |
|----------|---------|--------|-------|-------|
| `PROJECT_ROOT` | *(auto-detected)* | Path | Repo-Root | `src/app/config/__init__.py` |
| `DB_DIR` | `{PROJECT_ROOT}/data/db` | Path | Runtime-DBs | `src/app/config/__init__.py` |
| `DB_PUBLIC_DIR` | `{PROJECT_ROOT}/data/db/public` | Path | Public DBs (falls vorhanden) | `src/app/config/__init__.py` |
| `MEDIA_DIR` | `{PROJECT_ROOT}/media` | Path | Audio & Transkripte | `src/app/config/__init__.py` |
| `TRANSCRIPTS_DIR` | `{MEDIA_DIR}/transcripts` | Path | JSON-Transkripte | `src/app/config/__init__.py` |
| `AUDIO_FULL_DIR` | `{MEDIA_DIR}/mp3-full` | Path | Vollständige Audio-Dateien | `src/app/config/__init__.py` |
| `AUDIO_SPLIT_DIR` | `{MEDIA_DIR}/mp3-split` | Path | Segmentierte Audio-Dateien | `src/app/config/__init__.py` |
| `AUDIO_TEMP_DIR` | `{MEDIA_DIR}/mp3-temp` | Path | Temp Audio-Verarbeitung | `src/app/config/__init__.py` |

**Anpassung:** Via ENV-Vars oder direkt in `BaseConfig` überschreiben.

---

### Feature Flags

| Variable | Default | Format | Zweck | Datei |
|----------|---------|--------|-------|-------|
| `ALLOW_PUBLIC_TEMP_AUDIO` | `false` | `true` / `false` | Temp-Audio ohne Auth zugänglich | `src/app/config/__init__.py` |

**Hinweis:** In Produktion sollte `ALLOW_PUBLIC_TEMP_AUDIO = false` sein (Sicherheit).

---

### Flask & Debug

| Variable | Default | Format | Zweck |
|----------|---------|--------|-------|
| `FLASK_ENV` | `production` | `production` / `development` | Config-Klasse Auswahl |
| `FLASK_DEBUG` | `0` | `0` / `1` / `true` / `false` | Debug-Modus (Dev-Server) |

**Wichtig:** In Produktion **niemals** `DEBUG = True` setzen (Security-Risiko: Stack Traces)!

---

## Config-Layering (Beispiel)

**Szenario:** PostgreSQL in Produktion, SQLite in Dev

### Development (lokal)
```powershell
# .env (nicht in Git!)
FLASK_ENV=development
FLASK_SECRET_KEY=dev-secret-change-me
JWT_SECRET_KEY=dev-jwt-secret-change-me
# AUTH_DATABASE_URL nicht gesetzt → Default: sqlite:///data/db/auth.db
```

### Production (Docker Compose)
```yaml
# docker-compose.yml
services:
  web:
    environment:
      - FLASK_ENV=production
      - FLASK_SECRET_KEY=${FLASK_SECRET_KEY}  # Aus Host-ENV oder .env
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - AUTH_DATABASE_URL=postgresql://corapan:${DB_PASSWORD}@postgres:5432/corapan_auth
```

**Host `.env` (nicht in Git!):**
```bash
FLASK_SECRET_KEY=prod-secret-64-chars-hex...
JWT_SECRET_KEY=prod-jwt-secret-64-chars-hex...
DB_PASSWORD=secure-postgres-password
```

---

## Zugriff auf Config im Code

### In Routes/Services
```python
from flask import current_app

def my_function():
    secret_key = current_app.config["SECRET_KEY"]
    db_url = current_app.config["AUTH_DATABASE_URL"]
    allow_temp_audio = current_app.config.get("ALLOW_PUBLIC_TEMP_AUDIO", False)
```

### In Templates
```jinja2
{# Config-Werte via Context Processor verfügbar #}
{% if allow_public_temp_audio %}
  <a href="/media/audio/temp/...">Download</a>
{% endif %}
```

---

## Sicherheits-Checkliste

### Vor Production-Deployment

- [ ] `FLASK_SECRET_KEY` auf **zufälligen** 64-Char Hex-String gesetzt
- [ ] `JWT_SECRET_KEY` auf **separaten** 64-Char Hex-String gesetzt (nicht identisch mit `FLASK_SECRET_KEY`)
- [ ] `AUTH_DATABASE_URL` auf PostgreSQL DSN gesetzt (nicht SQLite)
- [ ] `FLASK_ENV=production` gesetzt
- [ ] `FLASK_DEBUG=0` (oder nicht gesetzt)
- [ ] `SESSION_COOKIE_SECURE=true` (HTTPS erforderlich)
- [ ] `JWT_COOKIE_SECURE=true` (HTTPS erforderlich)
- [ ] Keine Secrets in `docker-compose.yml` oder Code hardcoded
- [ ] `.env` in `.gitignore` (niemals committen!)
- [ ] Secrets via ENV-Vars oder Secrets-Manager (z.B. Docker Secrets, Vault)

---

## Legacy: passwords.env (DEPRECATED)

**Hinweis:** Die Anwendung nutzte früher `passwords.env` für env-basierte Auth (plain-text User/Pass). Dies ist **deprecated** und wurde durch DB-backed Auth ersetzt.

**Migration:** Siehe `migrations/0001_create_auth_schema_postgres.sql` und `scripts/create_initial_admin.py`.

**Rollback (nur für Notfall):**
```python
# passwords.env wird NICHT automatisch geladen
# Manuelle Integration erforderlich (nicht empfohlen)
```

---

## Projekt-spezifische Config

### CO.RA.PAN-spezifisch

**Location Data:**
```python
# src/app/config/countries.py
LOCATIONS = {
    "es-arg-bue": Location(code="es-arg-bue", name="Buenos Aires", ...),
    # ...
}
```

**Verwendung:**
```python
from ..config import get_location

location = get_location("es-arg-bue")
print(location.country_name)  # "Argentina"
```

**Anpassung für neue Projekte:**
- Falls keine Location-Daten benötigt: `countries.py` entfernen oder anpassen
- Falls eigene Metadaten-Struktur: Neue Module in `src/app/config/` anlegen

---

## Extension Points

**Neue Config-Optionen hinzufügen:**
1. ENV-Variable in `BaseConfig` / `DevConfig` hinzufügen
2. `os.getenv()` für Defaults nutzen
3. Typ-Konvertierung (int, bool) via `int()` / `.lower() == "true"`
4. Dokumentation hier aktualisieren
5. `.env.example` Datei anlegen (Template für User)

**Best Practices:**
- **Defaults für Dev:** Sollten "funktionieren" (z.B. SQLite)
- **Defaults für Prod:** Sollten "sicher" sein (z.B. `SECURE=true`)
- **Keine Secrets in Code:** Immer via ENV-Vars
- **Dokumentation:** Jede neue Variable hier dokumentieren
