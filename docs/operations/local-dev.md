# Lokale Entwicklung

**Scope:** Setup und Development Workflow  
**Source-of-truth:** `startme.md`, `scripts/dev-setup.ps1`, `scripts/dev-start.ps1`

## Quick Start

**Ein Befehl startet alles:**

```powershell
.\scripts\dev-setup.ps1
```

Das Skript:
1. Richtet `.venv` + Dependencies ein
2. Startet PostgreSQL + BlackLab via Docker
3. Führt Auth-DB-Migration aus
4. Startet Flask Dev-Server unter `http://localhost:8000`

**Login:** `admin` / `change-me`

---

## Voraussetzungen

- **Python 3.12+**
- **Docker Desktop** (muss laufen)
- **PowerShell 5.1+** (Windows) oder Bash (Linux/Mac)
- **Git**

---

## Manuelles Setup (Schritt für Schritt)

### 1. Repository klonen

```bash
git clone <repo-url>
cd corapan-webapp
```

### 2. Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # PowerShell
# oder: source .venv/bin/activate  # Bash
```

### 3. Dependencies installieren

```powershell
pip install -r requirements.txt
```

### 4. Docker Services starten

```powershell
docker-compose -f docker-compose.dev-postgres.yml up -d
```

**Services:**
- PostgreSQL (Port 5432)
- BlackLab Server (Port 8080)

### 5. Datenbank migrieren

```powershell
# PowerShell
$env:AUTH_DATABASE_URL = "postgresql://corapan:corapan@localhost:5432/corapan_auth"
python -c "from src.app.extensions.sqlalchemy_ext import init_engine; from src.app.config import load_config; from flask import Flask; app = Flask(__name__); load_config(app, 'development'); init_engine(app); from src.app.auth.models import Base; Base.metadata.create_all(app.config['AUTH_DATABASE_URL'])"
```

**Oder manuell:**
```bash
psql -U corapan -h localhost -d corapan_auth -f migrations/0001_create_auth_schema_postgres.sql
psql -U corapan -h localhost -d corapan_auth -f migrations/0002_create_analytics_tables.sql
```

### 6. Initial Admin erstellen

```powershell
python scripts/create_initial_admin.py
```

**Credentials:** `admin` / `change-me`

### 7. Dev-Server starten

```powershell
python -m src.app.main
```

**URL:** `http://localhost:8000`

---

## Nur neu starten (nach Setup)

```powershell
.\scripts\dev-start.ps1
```

Prüft ob Docker-Services laufen und startet sie bei Bedarf.

---

## Environment Variables (Dev)

**Empfohlen:** `.env` Datei im Root (nicht in Git!)

```bash
# .env
FLASK_ENV=development
FLASK_SECRET_KEY=dev-secret-change-me
JWT_SECRET_KEY=dev-jwt-secret-change-me
AUTH_DATABASE_URL=postgresql://corapan:corapan@localhost:5432/corapan_auth
ALLOW_PUBLIC_TEMP_AUDIO=true
```

**Laden via python-dotenv (automatisch in Flask):**
```python
# Wird automatisch geladen wenn .env vorhanden
```

---

## Port-Übersicht (Dev)

| Port | Service | URL |
|------|---------|-----|
| 8000 | Flask Dev-Server | `http://localhost:8000` |
| 5432 | PostgreSQL | `postgresql://localhost:5432` |
| 8080 | BlackLab Server | `http://localhost:8080/blacklab-server` |

---

## Runtime-Verzeichnis (Repo-lokal)

**Lage:** `RepoRoot/runtime/corapan`

Die Runtime ist **vollständig innerhalb des Repos** und wird **nicht versioniert** (`.gitignore`):

```
runtime/
├── data/
│   ├── public/
│   │   └── statistics/       ← Generierte Statistik-Daten (JSON + PNG)
│   └── ...                   ← Sonstige Runtime-Daten
└── ...
```

### Auto-Setup beim Start

`scripts/dev-start.ps1` erstellt das Runtime-Verzeichnis automatisch:
- Setzt `CORAPAN_RUNTIME_ROOT` auf `<RepoRoot>\runtime\corapan` (falls nicht überschrieben)
- Erstellt alle notwendigen Subdirectories
- **Keine manuelle Vorbereitung erforderlich**

### Custom Runtime-Pfad

Falls du die Runtime an einem anderen Ort brauchst (z.B. auf schnellerem Drive), überschreibe vor dem Start:

```powershell
$env:CORAPAN_RUNTIME_ROOT = "D:\custom-runtime\corapan"
.\scripts\dev-start.ps1
```

Oder persistent im PowerShell-Profil (`notepad $PROFILE`):
```powershell
$env:CORAPAN_RUNTIME_ROOT = "D:\custom-runtime\corapan"
```

### Statistics-Generierung

Statistics (JSON + PNG-Visualisierungen) werden in `$CORAPAN_RUNTIME_ROOT\data\public\statistics\` geschrieben:

```powershell
# CSV-Input generieren (einmalig)
python .\LOKAL\_0_json\04_internal_country_statistics.py

# Statistics generieren und schreiben
python .\LOKAL\_0_json\05_publish_corpus_statistics.py

# Verifikation
ls $env:CORAPAN_RUNTIME_ROOT\data\public\statistics\
```

Der API-Endpoint `/api/statistics` serviert diese Dateien.

---

## Hot Reload

**Flask Dev-Server:**
```python
# src/app/main.py
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
```

**Wichtig:** In `create_app()` ist `use_reloader=False` gesetzt (Stabilitätsgründe). Kann überschrieben werden.

---

## Tests ausführen

```powershell
pytest
```

**Config:** `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
norecursedirs = ["LOKAL", "data", "media", "static", "templates"]
```

---

## Docker Services verwalten

### Starten
```powershell
docker-compose -f docker-compose.dev-postgres.yml up -d
```

### Stoppen
```powershell
docker-compose -f docker-compose.dev-postgres.yml down
```

### Logs anzeigen
```powershell
docker-compose -f docker-compose.dev-postgres.yml logs -f
```

### DB-Shell öffnen
```powershell
docker exec -it corapan-postgres psql -U corapan -d corapan_auth
```

---

## Troubleshooting

### Port bereits belegt
```powershell
# Port 8000 prüfen
netstat -ano | findstr :8000

# Prozess beenden
taskkill /PID <PID> /F
```

### Docker startet nicht
```powershell
# Docker Desktop Status prüfen
docker ps

# Services neu starten
docker-compose -f docker-compose.dev-postgres.yml restart
```

### DB-Migration schlägt fehl
```powershell
# DB löschen und neu erstellen
docker-compose -f docker-compose.dev-postgres.yml down -v
docker-compose -f docker-compose.dev-postgres.yml up -d
# Migration erneut ausführen
```

### Import-Fehler
```powershell
# Virtual Environment aktiviert?
.\.venv\Scripts\Activate.ps1

# Dependencies neu installieren
pip install -r requirements.txt --force-reinstall
```

---

## Extension Points

**Neue Dependencies hinzufügen:**
1. In `requirements.txt` eintragen
2. `pip install -r requirements.txt`
3. Für andere Entwickler committen

**Neue Umgebungsvariablen:**
1. In `.env` (lokal) hinzufügen
2. In `src/app/config/__init__.py` als `os.getenv()` definieren
3. Dokumentation in `docs/architecture/configuration.md` aktualisieren
