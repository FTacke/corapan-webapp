# CO.RA.PAN - Quick Start.

## Empfohlener Quickstart (Postgres + BlackLab)

Ein Befehl startet alles: Virtualenv, Dependencies, PostgreSQL + BlackLab (Docker), Auth-Migration, Dev-Server.

```powershell
# Im Repository-Root ausfuehren
.\scripts\dev-setup.ps1
```

Das Skript:
1. Richtet `.venv` + Python-Dependencies ein
2. Startet PostgreSQL + BlackLab via Docker (`docker-compose.dev-postgres.yml`)
3. Fuehrt die Postgres Auth-DB-Migration aus
4. Startet den Flask Dev-Server unter `http://localhost:8000`

**Login:** `admin` / `change-me`

---

## Nur neu starten (ohne Neuinstallation)

Wenn alles bereits eingerichtet ist:

```powershell
.\scripts\dev-start.ps1
```

Das Skript:
1. Setzt `CORAPAN_RUNTIME_ROOT` auf Standardwert (falls nicht gesetzt): `<RepoRoot>/runtime/corapan` (repo-lokal!)
2. Erstellt Runtime-Verzeichnis(se): `${CORAPAN_RUNTIME_ROOT}/data/public/statistics/`
3. Warnt, wenn Statistics noch nicht generiert wurden (mit Anleitung zum Generieren)
4. Prüft, ob Docker-Services laufen und startet sie bei Bedarf
5. Startet den Flask Dev-Server

**Hinweis zu Statistics:** Beim ersten Start werden wahrscheinlich noch keine Statistics vorhanden sein. Das ist normal! Die API gibt dann 404 zurück. Um Statistics zu generieren, siehe [Statistiken generieren](#statistiken-generieren).

### Runtime-Verzeichnis (Repo-lokal)

Die Runtime liegt jetzt **vollständig im Repo**:
- Pfad: `RepoRoot/runtime/corapan`
- Nicht versioniert (`.gitignore`)
- Wird automatisch angelegt beim ersten Start
- Enthält: Statistics, Cache, temporäre Daten

**Keine manuelle Vorbereitung nötig!** Einfach `dev-start.ps1` ausführen.

### Custom Runtime-Pfad (optional)

Falls du eine Custom Runtime an anderem Ort brauchst, setze `CORAPAN_RUNTIME_ROOT` vor dem Start:

```powershell
# Einmalig
$env:CORAPAN_RUNTIME_ROOT = "D:\my-custom-runtime"
.\scripts\dev-start.ps1

# Oder persistent im PowerShell-Profil:
# notepad $PROFILE
# Dann: $env:CORAPAN_RUNTIME_ROOT = "D:\my-custom-runtime"
```

---

## Statistiken generieren

Statistics (PNG-Visualisierungen und JSON-Daten) werden in die Runtime-Directory geschrieben und vom App-API-Endpoint serviert.

**Vorbedingung:** `CORAPAN_RUNTIME_ROOT` wird von `dev-start.ps1` automatisch gesetzt (repo-lokal, falls nicht überschrieben).

```powershell
# Schritt 1: Input-CSVs generieren (falls noch nicht vorhanden)
python .\LOKAL\_0_json\04_internal_country_statistics.py

# Schritt 2: Statistics generieren und nach Runtime schreiben
python .\LOKAL\_0_json\05_publish_corpus_statistics.py

# Schritt 3: Prüfen, dass Dateien erstellt wurden
ls $env:CORAPAN_RUNTIME_ROOT\data\public\statistics\

# Schritt 4: App starten (oder neustarten)
.\scripts\dev-start.ps1
```

**Hinweis:** Diese Schritte sind nur nötig, wenn du mit Corpus-Daten arbeitest oder die Statistik-UI testen willst. Für einfache API-Tests ist das nicht erforderlich.

---

## Voraussetzungen

- **Docker Desktop** muss laufen (fuer Postgres + BlackLab)
- **Python 3.12+** (empfohlen: in `.venv` aktiviert)
- **PowerShell** (Version 5.1 oder 7+)

---

## Script-Optionen

### dev-setup.ps1 (Erst-Setup / Vollstaendige Installation)

| Parameter | Beschreibung |
|-----------|-------------|
| `-SkipInstall` | Ueberspringt pip install |
| `-SkipBlackLab` | Ueberspringt BlackLab-Start |
| `-SkipDevServer` | Ueberspringt Dev-Server-Start |
| `-ResetAuth` | Auth-DB zuruecksetzen + Admin neu anlegen |
| `-StartAdminPassword` | Initiales Admin-Passwort (Default: `change-me`) |

### dev-start.ps1 (Taegliches Starten)

| Parameter | Beschreibung |
|-----------|-------------|
| `-SkipBlackLab` | BlackLab nicht starten |

---

## Environment-Variablen

Die Dev-Skripte setzen automatisch:

| Variable | Dev-Wert | Beschreibung |
|----------|----------|-------------|
| `AUTH_DATABASE_URL` | `postgresql+psycopg://corapan_auth:corapan_auth@localhost:54320/corapan_auth` | Auth-DB Connection |
| `JWT_SECRET_KEY` | `dev-jwt-secret-change-me` | JWT-Signing-Key |
| `FLASK_SECRET_KEY` | `dev-secret-change-me` | Flask Session-Encryption |
| `BLACKLAB_BASE_URL` | `http://localhost:8081/blacklab-server` | Corpus-Search-Service |
| `CORAPAN_RUNTIME_ROOT` | `C:\dev\runtime\corapan` (Default) | Runtime Data Directory |
| `PUBLIC_STATS_DIR` | `${CORAPAN_RUNTIME_ROOT}\data\public\statistics` (Auto) | Statistics Output Location |

---

## Docker-Services

Der Dev-Stack verwendet `docker-compose.dev-postgres.yml`:

| Service | Container | Port | Beschreibung |
|---------|-----------|------|-------------|
| PostgreSQL | `corapan_auth_db` | `54320` | Auth-Datenbank |
| BlackLab | `blacklab-server-v3` | `8081` | Corpus-Suchserver |

### Manuelles Starten/Stoppen

```powershell
# Starten
docker compose -f docker-compose.dev-postgres.yml up -d

# Stoppen
docker compose -f docker-compose.dev-postgres.yml down

# Status pruefen
docker compose -f docker-compose.dev-postgres.yml ps

# Logs ansehen
docker compose -f docker-compose.dev-postgres.yml logs -f
```

---

## BlackLab-Index aufbauen

Nur beim ersten Setup oder nach Daten-Reset:

```powershell
# Schritt 1: JSON -> TSV Export
python "scripts/blacklab/run_export.py"

# Schritt 2: TSV -> Lucene Index
.\scripts\build_blacklab_index.ps1
```

Mehr Details: `docs/troubleshooting/blacklab-issues.md`

---

## Health Checks

```powershell
# App Health
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing

# Auth DB Health
Invoke-WebRequest -Uri "http://localhost:8000/health/auth" -UseBasicParsing

# BlackLab Health
Invoke-WebRequest -Uri "http://localhost:8000/health/bls" -UseBasicParsing
```

---

## Troubleshooting

### Docker-Container laeuft nicht

```powershell
docker ps --filter name=corapan
docker logs corapan_auth_db
docker logs blacklab-server-v3
```

### PostgreSQL-Verbindung schlaegt fehl

```powershell
# Healthcheck pruefen
docker inspect --format='{{.State.Health.Status}}' corapan_auth_db

# Container neu starten
docker compose -f docker-compose.dev-postgres.yml restart corapan_auth_db
```

### Auth-DB zuruecksetzen

```powershell
.\scripts\dev-setup.ps1 -ResetAuth -StartAdminPassword "neues-passwort"
```

### Browser lädt endlos (Infinite Loading)

Symptom: Server läuft, aber Anfragen (z.B. `http://localhost:8000/`) laden ewig ohne Antwort.

Ursache: Python/Flask Console-Output-Buffer voll oder blockiert (Windows Pipeline Issue).

Diagnose:
```powershell
# 1. Laufende Prozesse stoppen
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# 2. Server direkt starten (ohne Pipeline!)
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-start.ps1

# 3. Check (in neuer Konsole)
curl.exe --max-time 3 -v http://127.0.0.1:8000/
```
Wenn `curl` Connected aber Timeout (oder Server hängt), ist der Fix bereits aktiv in `dev-start.ps1` (nutzt nun `Start-Process` und Log-Files).

---

## Weiterfuehrende Dokumentation

- [Development Setup](docs/operations/development-setup.md) - Detaillierte Setup-Anleitung
- [Deployment Guide](docs/operations/deployment.md) - Production-Deployment
- [Production Hardening](docs/operations/production_hardening.md) - Security & Tests
- [Project Structure](docs/reference/project_structure.md) - Codebase-Uebersicht