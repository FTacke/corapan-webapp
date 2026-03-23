# CO.RA.PAN Web App

> **Version 1.0.0** | Januar 2026 | Zenodo Software-Release: DOI 10.5281/zenodo.17834023

Dieses Dokument beschreibt die technische Anwendung unter `app/`. Das Repository als Ganzes ist unter `corapan/` organisiert. Systemweite Struktur, Root-Workflows, Maintenance-Pipelines und Runtime-/Deploy-Grundsaetze stehen in [../README.md](../README.md).

Die CO.RA.PAN Web App ist die zentrale Webanwendung für den Zugriff auf und die Analyse des **CO.RA.PAN — Corpus Radiofónico Panhispánico**, eines linguistischen Forschungsprojekts zur vergleichenden Untersuchung der gesprochenen Standardsprache des zeitgenössischen Spanisch.

CO.RA.PAN basiert auf einem streng kuratierten Radiokorpus, der authentische, professionell produzierte Informations- und Nachrichtensendungen aus den nationalen Rundfunkanstalten nahezu aller spanischsprachigen Länder umfasst. Der Fokus liegt auf professioneller mündlicher Normsprache, wie sie von Moderator:innen und Journalist:innen verwendet wird, und damit auf einem funktional homogenen Register, das bislang in der Korpuslinguistik nur unzureichend abgedeckt ist.

Der Korpus kombiniert Audiomaterial und Transkriptionen mit zeit- und token-alignierten linguistischen Annotationen (u. a. Lemmata, Wortarten, syntaktische Informationen) sowie einer einheitlich modellierten Metadatenstruktur. Diese Konzeption ermöglicht systematische Vergleiche panhispanischer Variation innerhalb eines klar definierten kommunikativen Rahmens.

Die Web App stellt diese Forschungsinfrastruktur in Form einer integrierten Such-, Analyse- und Explorationsumgebung bereit und dient zugleich als technisches Rückgrat für nachhaltige, reproduzierbare korpuslinguistische Forschung.

## 1. Projektübersicht

Diese Anwendung dient als Frontend und API-Layer für das CO.RA.PAN-Projekt. Sie ermöglicht Linguisten und Forschern:
- **Suche:** Detaillierte Korpus-Recherchen (Wortformen, Lemmata, POS-Tags) via BlackLab Server.
- **Analyse:** Statistische Auswertungen und Visualisierungen (Charts, Karten).
- **Exploration:** Interaktive Wiedergabe von Audio-Segmenten synchron zum Transkript.
- **Verwaltung:** Editor-Tools zur Pflege von Metadaten und Transkripten.

## 2. Features

- **Korpus-Suche:**
  - Einfache Suche und Expertensuche (CQL) mit Pattern-Builder.
  - **NEU:** Detaillierte Schritt-für-Schritt-Anleitung (Guía) für Einsteiger.
  - **NEU:** Token-Suche für präzises Wiederfinden spezifischer Belege.
  - Filterung nach Metadaten (Land, Region, Sprecher, Geschlecht, etc.).
  - KWIC-Ansicht (Key Word in Context) mit Audio-Verknüpfung.
- **Audio-Player:**
  - Segmentgenaue Wiedergabe.
  - Visuelle Hervorhebung im Transkript.
- **Visualisierung:**
  - Interaktive Karten (Leaflet) zur geografischen Verteilung.
  - Statistik-Dashboard (ECharts) für Frequenzanalysen.
- **Export:**
  - CSV/TSV-Export von Suchergebnissen (Streaming-Support für große Datenmengen).
  - CSV-Export von Statistiken (inkl. Metadaten und Filter-Infos).
- **Administration:**
  - Rollenbasiertes Zugriffssystem (User, Editor, Admin).
  - JSON-Editor für Transkripte.
- **Analytics (NEU v1.0):**
  - DSGVO-konformes, anonymes Nutzungstracking.
  - Admin-Dashboard mit Besucher-, Such- und Audio-Statistiken.
  - Keine personenbezogenen Daten, kein Consent-Banner nötig.

## 3. Tech-Stack

- **Backend:** Python 3.12, Flask (Web Framework)
- **Suchmaschine:** BlackLab Server (Lucene-basiert, via Docker)
- **Datenbank:** PostgreSQL fuer Auth und Kerndaten, SQLite nur fuer explizit getrennte Side-Datenbanken
- **Frontend:** Jinja2 Templates, Vanilla JS, Material Design 3 (CSS Tokens), ECharts, Leaflet
- **Deployment:** Gunicorn, Docker Compose

**Auth:** DB-backed JWT-Authentication (Argon2 Password Hashing).

**Hinweis:** `passwords.env` bleibt eine operator-managed Produktions-Secret-Datei ausserhalb von Git. Details stehen in [../docs/operations/production.md](../docs/operations/production.md).

## 4. Voraussetzungen

- **Python:** Version 3.12 oder höher
- **Docker Desktop:** Für den Betrieb des BlackLab Servers
- **PowerShell:** (Windows) für Hilfsskripte (empfohlen Version 5.1 oder 7+)

### Reproduzierbare Python-Basis (zu bestätigen)

- **Python-Standard für lokales Dev-Setup:** `3.12.10` (siehe `.python-version`)
- **Package Tooling:** `uv`
- **Virtuelle Umgebung:** `.venv/` im Repo-Root (nicht versioniert)

Quellenlage für Python-Version:

- Autoritativ: Docker und CI pinnen den Minor-Stand `3.12` (kein Patch):
  - `Dockerfile` (`FROM python:3.12-slim`)
  - `.github/workflows/ci.yml` (`python-version: "3.12"`)
- Lokaler Hinweis (nicht autoritativ): `.venv/pyvenv.cfg` kann ein konkretes Patchlevel zeigen.

Entscheidung:

- Docker/CI bleiben auf Minor-Pin `3.12` (latest Patchlevel pro Environment).
- `.python-version` ist bewusst ein konkreter **Local Dev Pin**: `3.12.10`.

`uv` installieren (Windows PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 5. Setup (Windows)

Der kanonische lokale Einstieg erfolgt vom Repository-Root `corapan/` aus. Fuer normale lokale Entwicklung sind die Root-Wrapper vorzuziehen.

```powershell
git clone <repo-url> corapan
cd corapan

powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
.\scripts\dev-setup.ps1

# optional:
# .\scripts\dev-start.ps1

# nur falls lokal benötigt:
# Copy-Item .\app\.env.example .\app\.env

# App-spezifische Details siehe unten.
```

## 6. Dependency-Workflow (requirements.in + lock)

- Runtime-Quelle: `requirements.in`
- Runtime-Lock: `requirements.txt`
- Dev-Quelle: `requirements-dev.in`
- Dev-Lock: `requirements-dev.txt`

Lockfiles aktualisieren (aus `app/`):

```powershell
.\scripts\refresh-lockfiles.ps1
```

## 7. Data / Media (nicht im Git)

- Laufzeitdaten und Medien werden nicht versioniert (`data/`, `media/`, `logs/`).
- Für neuen PC manuell migrieren oder aus Quellen neu erzeugen.
- Details und Größenabschätzung: siehe `MIGRATION.md`.
- Empfohlene Auslagerung (Windows): `D:\data\corapan\...`

## 8. Secrets / Environment

Lege lokal `.env` aus `.env.example` an. Niemals `.env` oder Schlüsseldateien committen.

Benötigte Variablen (Minimal-Startsatz):

- `FLASK_SECRET_KEY` – Secret für Flask Session-Signing
- `JWT_SECRET_KEY` – Secret für JWT-Signing
- `AUTH_DATABASE_URL` – Verbindung zur Auth-Datenbank
- `CORAPAN_MEDIA_ROOT` – Root-Pfad der Laufzeit-Medien

Weitere häufig benötigte Variablen:

- `FLASK_ENV` – Laufzeitmodus (`development`/`production`)
- `FLASK_DEBUG` – Debug-Flag für lokale Entwicklung
- `AUTH_HASH_ALGO` – Hashing-Algorithmus (`argon2`/`bcrypt`)
- `BLS_BASE_URL` – URL des BlackLab-Servers
- `BLS_CORPUS` – BlackLab-Korpusname/Indexname
- `CORAPAN_RUNTIME_ROOT` – Runtime-Root für Datenpfade
- `PUBLIC_STATS_DIR` – Zielpfad veröffentlichter Statistikdateien
- `STATS_TEMP_DIR` – Temp-Pfad für Statistik-Erzeugung
- `ALLOW_PUBLIC_TEMP_AUDIO` – öffentlicher Zugriff auf Audio-Snippets

Bezugsquelle für Werte:

- Lokal/Dev: Team-Passwortmanager (z. B. 1Password/Bitwarden) oder lokal gepflegte Dev-Secrets.
- Team/Prod: zentrales Secret-Management (z. B. Vault/KeyVault/Secrets Manager).
- Niemals echte Secret-Werte in Git committen.

## 9. Installation & Setup (Legacy/Manuell)

### 1. Repository klonen
```bash
git clone <repo-url> corapan
cd corapan/app
```

### 2. Virtuelles Environment erstellen
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Abhängigkeiten installieren
```powershell
pip install -r requirements.txt
pip install -e .
```

Note: Heavy corpus processing and maintenance pipeline dependencies are maintained
separately from the app runtime environment.
If you need the JSON→TSV→indexing pipeline, use the workspace maintenance toolchain
instead of installing the large NLP/audio packages into the app environment.

### 4. Konfiguration
Erstellen Sie eine `.env` Datei basierend auf der Vorlage:
```powershell
cp .env.example .env
```
Passen Sie die Werte in `.env` an (insbesondere `FLASK_SECRET_KEY` und `JWT_SECRET_KEY`).

### 5. Datenbank initialisieren
Erstellen Sie die Auth-Datenbank und den initialen Admin-Account:
```powershell
# PostgreSQL (canonical dev / production / staging)
# AUTH_DATABASE_URL must be set explicitly.
python scripts/apply_auth_migration.py --engine postgres --reset

# Or apply the SQL files manually
# Apply migrations/0001_create_auth_schema_postgres.sql via psql

# Initialen Admin erstellen
python scripts/create_initial_admin.py --username admin --password change-me
```

### 6. BlackLab Index (Optional/Initial)
Falls noch kein Index vorhanden ist, muss dieser erstellt werden. Siehe dazu `docs/how-to/quickstart-windows.md` oder nutzen Sie das Skript:
```powershell
.\scripts\blacklab\build_blacklab_index.ps1
```

**Hinweis:** Für ein minimales Template ohne Korpus-Suchfunktion kann dieser Schritt übersprungen werden.

## 10. Entwicklung & Start

### BlackLab Server starten
Der Such-Server muss im Hintergrund laufen:
```powershell
.\scripts\blacklab\start_blacklab_docker_v3.ps1 -Detach
```
URL: http://localhost:8081/blacklab-server

### Flask App starten
```powershell
# Environment aktivieren
.venv\Scripts\Activate.ps1

# Server starten (Development Mode)
$env:FLASK_ENV="development"; python -m src.app.main
```
URL: http://localhost:8000

## 11. Tests & Qualitätssicherung

### Tests ausführen
Das Projekt nutzt `pytest`. Alle Tests (Unit & Integration) können wie folgt gestartet werden:
```powershell
pytest
```

### Code-Qualität
Wir nutzen `ruff` für Linting und Formatierung:
```powershell
# Check
ruff check .

# Formatierung anwenden
ruff format .
```

### CI/CD
Eine GitHub Actions Pipeline (`.github/workflows/ci.yml`) prüft bei jedem Push automatisch Tests und Linter-Regeln.

## 12. Dokumentation

Die detaillierte Dokumentation liegt auf Root-Ebene unter `../docs/`:

- **[Architektur](../docs/architecture/)**
- **[Betrieb](../docs/operations/)**
- **[Aenderungen](../docs/changes/)**
- **[Repo-Finalisierung](../docs/repo_finish/)**
- **[Changelog](CHANGELOG.md)**

## 13. Deployment

Für den produktiven Betrieb wird empfohlen:
- Einsatz eines WSGI-Servers (z.B. Gunicorn).
- Reverse Proxy (Nginx/Apache) für SSL-Terminierung.
- Setzen der Environment-Variable `FLASK_ENV=production`.
- Siehe [../docs/operations/production.md](../docs/operations/production.md) fuer Details.

### Deployment (Production)

Die Produktion laeuft auf einer VM am HRZ der Philipps-Universitaet Marburg und wird ueber einen **self-hosted GitHub Runner** automatisiert. Ein `push` auf den `main`-Branch fuehrt `scripts/deploy_prod.sh` aus, welches im App-Checkout unter `/srv/webapps/corapan/app` deployt. Grosse Daten- und Medienbestaende kommen **nicht** ueber Git, sondern werden getrennt unter `/srv/webapps/corapan/data` und `/srv/webapps/corapan/media` bereitgestellt.

> **Secrets:** Die Datei `passwords.env` liegt serverseitig unter `/srv/webapps/corapan/config/passwords.env` und wird per `--env-file` in den Deploy-Prozess eingebunden. Die App erwartet Werte wie `AUTH_DATABASE_URL`, `FLASK_SECRET_KEY`, `BLS_BASE_URL` und `BLS_CORPUS` als Umgebungsvariablen.

→ Vollstaendige Dokumentation: [../docs/operations/production.md](../docs/operations/production.md)

## 14. Lizenz / Licensing

The CO.RA.PAN Web Application is released under the MIT License.  
This applies to the software code only.

The CO.RA.PAN corpus data (audio, transcripts, annotations, metadata, and any
derived structured data) is **not** covered by this license and remains
restricted due to copyright and broadcasting rights.  
These materials may not be redistributed or reused outside the scope explicitly
permitted by the project’s legal framework and cannot be considered open data.

## 15. Versionierung & Zitation

- **Aktuelle Version:** 1.0.0 (Januar 2026)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Zitation:** Siehe [CITATION.cff](CITATION.cff)
- **Zenodo (Software):** DOI 10.5281/zenodo.17834023

## CO.RA.PAN References and Related Resources

The CO.RA.PAN project consists of multiple, clearly separated components with distinct citation records.  
Please refer to the appropriate DOI depending on whether you cite the software, metadata, or corpus data.

**CO.RA.PAN Full Corpus (Restricted)**  
DOI: https://doi.org/10.5281/zenodo.15360942  
*Audio data and full JSON transcripts; access restricted due to copyright and broadcasting constraints.*

**CO.RA.PAN Sample Corpus (Public)**  
DOI: https://doi.org/10.5281/zenodo.15378479  
*Public sample dataset for demonstration, testing, and teaching purposes.*

**CO.RA.PAN Metadata (Public)**  
DOI: https://doi.org/10.5281/zenodo.17843469  
*Complete metadata inventory describing the CO.RA.PAN corpus.*

**CO.RA.PAN Web Application**  
DOI: https://doi.org/10.5281/zenodo.17834023  
*Software release of the CO.RA.PAN Web Application (this repository).*


## Current Status (January 2026)

### Frontend
- **Vite** for asset bundling and build process
- **Material Design 3** principles with custom CSS architecture
- **DataTables** for interactive result tables
- **ECharts** for data visualization
- **Leaflet** for geolinguistic mapping
- **HTMX** for dynamic UI interactions

### Styling
- Material Design 3 design system with custom tokens
- BEM naming convention for CSS classes
- Design tokens in `static/css/md3/tokens.css`
- Responsive, mobile-first layouts
- WCAG 2.1 AA accessibility compliance

## Development

**Requirements**: Python 3.12+, FFmpeg, libsndfile

**Setup**:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
````

**Run**:

```bash
set FLASK_SECRET_KEY=your-secret-key
python -m src.app.main
```

**Environment Variables**:

* `FLASK_SECRET_KEY` - Flask session secret
* `JWT_SECRET_KEY` - JWT signing key (legacy: `JWT_SECRET`)
* `AUTH_DATABASE_URL` - Auth database URL (PostgreSQL required for auth/core)
* `BLS_BASE_URL` - BlackLab server URL
* `BLS_CORPUS` - Explicit BlackLab corpus name (canonical dev value: `corapan`)
* `ALLOW_PUBLIC_TEMP_AUDIO` - Allow anonymous audio snippet access (default: false)

## Current Status (January 2026)

### ✅ Production-Ready Features

* **Basic Corpus Search**: Fully operational with token-based queries
* **Advanced Search**: BlackLab integration complete (Stage 1-3), UI deployed
* **Authentication System**: JWT-based auth with GET/POST logout support
* **Audio Player**: Full playback with transcript synchronization
* **Atlas**: Interactive map with marker tooltips showing country statistics and deep-links
* **Corpus Metadata**: Country-tabbed dashboard with file tables and deep-link support
* **Statistics**: ECharts-based visualization dashboard with country deep-links
* **Editor**: JSON transcript editing interface for authorized roles
* **Security**: CSRF protection, rate limiting, CQL injection prevention

### 🔧 Configuration

* **Database**: PostgreSQL (production/dev default), SQLite (fallback)
* **Media Files**: Organized by country in `media/` directory
* **BlackLab Index**: 146 documents, 1.49M tokens, 15.89 MB index
* **Access Control**: Public access configurable via `ALLOW_PUBLIC_TEMP_AUDIO`

### 📊 System Metrics

* **Corpus Size**: 146 JSON documents across 20+ countries/regions
* **Total Tokens**: ~1.5 million indexed tokens
* **Search Performance**: <100ms for basic queries, <1s for complex CQL
* **Export Capability**: Up to 50,000 rows with streaming