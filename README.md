# CO.RA.PAN Web App

Eine moderne Webplattform für die Analyse und Exploration des CO.RA.PAN-Korpus (Corpus Oral de Referencia del Español Actual).

## 1. Projektübersicht

Diese Anwendung dient als Frontend und API-Layer für das CO.RA.PAN-Projekt. Sie ermöglicht Linguisten und Forschern:
- **Suche:** Detaillierte Korpus-Recherchen (Wortformen, Lemmata, POS-Tags) via BlackLab Server.
- **Analyse:** Statistische Auswertungen und Visualisierungen (Charts, Karten).
- **Exploration:** Interaktive Wiedergabe von Audio-Segmenten synchron zum Transkript.
- **Verwaltung:** Editor-Tools zur Pflege von Metadaten und Transkripten.

## 2. Features

- **Korpus-Suche:**
  - Einfache Suche und Expertensuche (CQL).
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
- **Administration:**
  - Rollenbasiertes Zugriffssystem (User, Editor, Admin).
  - JSON-Editor für Transkripte.

## 3. Tech-Stack

- **Backend:** Python 3.12, Flask (Web Framework)
- **Suchmaschine:** BlackLab Server (Lucene-basiert, via Docker)
- **Datenbank:** SQLite (für User-Daten und App-Status)
- **Frontend:** Jinja2 Templates, Vanilla JS, CSS (Bootstrap-basiert), ECharts, Leaflet
- **Deployment:** Gunicorn, Docker Compose

## 4. Voraussetzungen

- **Python:** Version 3.12 oder höher
- **Docker Desktop:** Für den Betrieb des BlackLab Servers
- **PowerShell:** (Windows) für Hilfsskripte (empfohlen Version 5.1 oder 7+)

## 5. Installation & Setup

### 1. Repository klonen
```bash
git clone <repo-url>
cd corapan-webapp
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

### 4. Konfiguration
Erstellen Sie eine `.env` Datei basierend auf der Vorlage:
```powershell
cp .env.example .env
```
Passen Sie die Werte in `.env` an (insbesondere `FLASK_SECRET_KEY` und Pfade).

### 5. BlackLab Index (Optional/Initial)
Falls noch kein Index vorhanden ist, muss dieser erstellt werden. Siehe dazu `docs/how-to/quickstart-windows.md` oder nutzen Sie das Skript:
```powershell
.\scripts\build_blacklab_index.ps1
```

## 6. Entwicklung & Start

### BlackLab Server starten
Der Such-Server muss im Hintergrund laufen:
```powershell
.\scripts\start_blacklab_docker_v3.ps1 -Detach
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

## 7. Tests & Qualitätssicherung

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

## 8. Dokumentation

Die detaillierte Dokumentation befindet sich im `docs/` Ordner:

- **[Konzepte](docs/concepts/)**: Architektur, Authentifizierung.
- **[Anleitungen](docs/how-to/)**: Schritt-für-Schritt Guides (z.B. Quickstart).
- **[Betrieb](docs/operations/)**: Deployment, Security.
- **[Referenz](docs/reference/)**: API-Doku, Datenbank-Schema.

## 9. Deployment

Für den produktiven Betrieb wird empfohlen:
- Einsatz eines WSGI-Servers (z.B. Gunicorn).
- Reverse Proxy (Nginx/Apache) für SSL-Terminierung.
- Setzen der Environment-Variable `FLASK_ENV=production`.
- Siehe `docs/operations/deployment.md` für Details.

## 10. Lizenz

(Hier Lizenzinformationen einfügen, z.B. MIT oder Proprietär)

- **Public Access Mode**: Configurable public/private audio snippet access
- **Security Features**: Rate limiting, CQL injection prevention, input validation

## Technology Stack

### Backend
- **Flask 3.x** with application factory pattern
- **SQLite** databases for corpus data and statistics
- **BlackLab Server** for advanced corpus search (Java-based)
- **FFmpeg** and **libsndfile** for audio processing
- **JWT** for authentication with cookie-based tokens

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
```

**Run**:
```bash
set FLASK_SECRET_KEY=your-secret-key
python -m src.app.main
```

**Environment Variables**:
- `FLASK_SECRET_KEY` - Flask session secret
- `JWT_SECRET` - JWT signing key
- `ALLOW_PUBLIC_TEMP_AUDIO` - Allow anonymous audio snippet access (default: false)

## Current Status (November 2025)

### ✅ Production-Ready Features
- **Basic Corpus Search**: Fully operational with token-based queries
- **Advanced Search**: BlackLab integration complete (Stage 1-3), UI deployed
- **Authentication System**: JWT-based auth with GET/POST logout support
- **Audio Player**: Full playback with transcript synchronization
- **Atlas**: Interactive map with country/region data
- **Statistics**: ECharts-based visualization dashboard
- **Editor**: JSON transcript editing interface for authorized roles
- **Security**: CSRF protection, rate limiting, CQL injection prevention

### 🔧 Configuration
- **Database**: SQLite (`data/transcription.db`, `data/stats_all.db`)
- **Media Files**: Organized by country in `media/` directory
- **BlackLab Index**: 146 documents, 1.49M tokens, 15.89 MB index
- **Access Control**: Public access configurable via `ALLOW_PUBLIC_TEMP_AUDIO`

### 📊 System Metrics
- **Corpus Size**: 146 JSON documents across 20+ countries/regions
- **Total Tokens**: ~1.5 million indexed tokens
- **Search Performance**: <100ms for basic queries, <1s for complex CQL
- **Export Capability**: Up to 50,000 rows with streaming
