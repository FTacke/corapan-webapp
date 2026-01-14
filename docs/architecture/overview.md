# Architektur-Überblick

**Scope:** High-Level Architektur der CO.RA.PAN Webapp  
**Source-of-truth:** `src/app/__init__.py`, `src/app/main.py`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`

## Tech Stack

### Backend
- **Framework:** Flask 3.x (Python 3.12+)
- **WSGI Server:** Gunicorn (Production)
- **Datenbank:** PostgreSQL (Produktion), SQLite (Dev-Fallback)
- **ORM:** SQLAlchemy 2.x (für Auth & Analytics)
- **Auth:** Flask-JWT-Extended (JWT-basiert, Cookie + Header)
- **Password Hashing:** Argon2 (via passlib), Fallback: bcrypt

### Frontend
- **Template Engine:** Jinja2
- **CSS Framework:** Custom Material Design 3 (Token-basiert)
- **JavaScript:** Vanilla JS, htmx (progressive enhancement)
- **Charts:** ECharts (Apache ECharts)
- **Maps:** Leaflet + OpenStreetMap
- **Icons:** Font Awesome 6.7.1, Bootstrap Icons

### Infrastruktur
- **Container:** Docker + Docker Compose
- **Reverse Proxy:** Nginx (HTTPS-Termination, Static Serving)
- **Suchmaschine:** BlackLab Server (Lucene-basiert, Docker)
- **Logging:** Python logging (RotatingFileHandler)

## Application Factory Pattern

Die Anwendung nutzt das Factory Pattern (`create_app()` in `src/app/__init__.py`):

```python
app = create_app(env_name)  # env_name: "development" oder "production"
```

**Initialisierung:**
1. Config laden (`src/app/config/__init__.py`)
2. Auth-DB Engine initialisieren (SQLAlchemy)
3. Extensions registrieren (JWT, etc.)
4. Blueprints registrieren (Routes)
5. Context Processors, Error Handlers, Logging einrichten

## Module-Landkarte

Die Anwendung ist in folgende Feature-Module unterteilt (Blueprints):

| Modul | Blueprint | Zweck | Routes Beispiel |
|-------|-----------|-------|-----------------|
| **Public** | `public_bp` | Startseite, statische Seiten | `/`, `/impressum`, `/privacy` |
| **Auth** | `auth_bp` | Login, Logout, Token Refresh | `/auth/login`, `/auth/logout` |
| **Admin** | `admin_bp` | User Management (nur Admin) | `/admin/users`, `/admin/logs` |
| **Search** | `corpus_bp` | Korpussuche (einfach + CQL) | `/search`, `/search/advanced` |
| **Player** | `player_bp` | Audio-Wiedergabe | `/audio/<doc>/<seg>` |
| **Atlas** | `atlas_bp` | Geografische Visualisierung | `/atlas` |
| **Stats** | `stats_bp` | Statistiken, Charts, Export | `/stats`, `/stats/export` |
| **Editor** | `editor_bp` | JSON-Transkript-Editor (Editor-Rolle) | `/editor` |
| **Media** | `media_bp` | Audio-Datei-Serving | `/media/audio/<path>` |
| **Analytics** | `analytics_bp` | DSGVO-konformes Tracking (Admin-only) | `/analytics/dashboard` |
| **BLS Proxy** | `bls_proxy_bp` | BlackLab Server Proxy | `/api/blacklab/*` |

**Blueprint-Registrierung:** `src/app/routes/__init__.py`

## High-Level Architektur

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (User)                                             │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTPS
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Nginx Reverse Proxy                                        │
│  - HTTPS Termination (Let's Encrypt)                        │
│  - Static File Serving (/static/*)                          │
│  - Proxy Pass → Gunicorn (Port 6000)                        │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Gunicorn WSGI Server (Docker Container)                    │
│  - Workers: 4                                               │
│  - Bind: 0.0.0.0:8000 (intern)                              │
│  - Exposed: 6000:8000 (Docker Port Mapping)                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Flask Application (src/app/)                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Request Lifecycle:                                      ││
│  │ 1. ProxyFix (X-Forwarded-* Headers)                     ││
│  │ 2. before_request: JWT Auth Context (g.user, g.role)    ││
│  │ 3. Route Handler (Blueprint)                            ││
│  │ 4. Service Layer (Business Logic)                       ││
│  │ 5. Data Layer (DB/BlackLab/Files)                       ││
│  │ 6. Template Rendering / JSON Response                   ││
│  └─────────────────────────────────────────────────────────┘│
└──────────┬──────────────┬──────────────┬────────────────────┘
           │              │              │
           ▼              ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌─────────────────┐
│ PostgreSQL   │  │ BlackLab     │  │ Filesystem      │
│ (Auth, Stats)│  │ Server       │  │ (Audio, JSON)   │
│ Port: 5432   │  │ Port: 8080   │  │ Volumes/Bind    │
└──────────────┘  └──────────────┘  └─────────────────┘
```

## Data Flow Layers

1. **Presentation Layer:** Templates (`templates/`), Static Assets (`static/`)
2. **Route Layer:** Blueprints (`src/app/routes/`)
3. **Service Layer:** Business Logic (`src/app/services/`, `src/app/search/`, `src/app/auth/`)
4. **Data Layer:** SQLAlchemy Models (`src/app/auth/models.py`, `src/app/analytics/models.py`), BlackLab API, Filesystem

## Deployment-Architektur

**Entwicklung:**
- Docker Compose: `docker-compose.dev-postgres.yml`
- PostgreSQL + BlackLab in Containern
- Flask Dev-Server (Hot Reload)
- Port 8000 (lokal)

**Produktion:**
- Docker Compose: `docker-compose.yml`
- Gunicorn (4 Workers)
- Nginx (HTTPS, Port 443 → 6000 → 8000)
- PostgreSQL (externer Managed Service möglich)
- BlackLab (Docker, separates Netzwerk)
- Volumes für Logs, Daten, Media (Read-Only wo möglich)

## Extension Points

**Neue Features hinzufügen:**
1. Blueprint erstellen in `src/app/routes/`
2. Service-Logik in `src/app/services/` oder eigenem Modul
3. Templates in `templates/<feature>/`
4. CSS (falls nötig) in `static/css/` (MD3-konform)
5. Blueprint registrieren in `src/app/routes/__init__.py`

**Bestehende Features anpassen:**
- Siehe jeweilige Modul-Dokumentation unter `docs/modules/`

## Projekt-spezifische Annahmen

- **BlackLab Server:** Wird für Korpussuche vorausgesetzt (Docker-basiert)
- **PostgreSQL:** Empfohlen für Produktion (SQLite nur Dev-Fallback)
- **Audio-Dateien:** Liegen auf Filesystem (`media/mp3-split/`, `media/mp3-full/`)
- **Transkripte:** JSON-Dateien in `media/transcripts/`
- **Multi-Sprache:** Aktuell nur Deutsch/Spanisch in UI-Texten (keine i18n-Library)
- **DSGVO:** Analytics-Modul ist opt-in, speichert keine personenbezogenen Daten
