# Verzeichnisstruktur

**Scope:** Organisation des Repositories  
**Source-of-truth:** Repo Root, `pyproject.toml`, `.gitignore`

## Top-Level Struktur

```
corapan-webapp/
├── .venv/                    # Python Virtual Environment (lokal, nicht in Git)
├── config/                   # Externe Konfiguration (Keys, BlackLab-Configs)
├── data/                     # Runtime-Datenbanken, Exporte, Counters
├── docs/                     # Dokumentation (Status quo)
├── infra/                    # Docker Compose Files (Dev/Prod)
├── logs/                     # Anwendungs-Logs (lokal/prod)
├── media/                    # Audio-Dateien, Transkripte (große Binärdaten)
├── migrations/               # SQL-Migrationen (Auth-Schema)
├── reports/                  # Automatisierte Reports (z.B. MD3-Lint)
├── scripts/                  # Hilfsskripte (Setup, Deploy, Maintenance)
├── src/                      # Hauptanwendung (Python-Code)
├── static/                   # Frontend Assets (CSS, JS, Bilder)
├── templates/                # Jinja2 Templates
├── tests/                    # Unit- und Integrationstests
├── tools/                    # Build-Tools, Utilities
├── docker-compose.yml        # Produktion Docker Compose
├── Dockerfile                # Multi-Stage Build
├── Makefile                  # Convenience-Targets
├── pyproject.toml            # Python Projekt-Metadaten
├── requirements.txt          # Python Dependencies
├── README.md                 # Projekt-Übersicht
└── startme.md                # Quick Start Guide
```

---

## `src/` — Application Code

```
src/
└── app/
    ├── __init__.py           # Application Factory (create_app)
    ├── main.py               # Entry Point (python -m src.app.main)
    ├── analytics/            # Analytics-Modul (DSGVO-konform)
    │   ├── __init__.py
    │   └── models.py         # AnalyticsDaily Model
    ├── auth/                 # Authentication & Authorization
    │   ├── __init__.py
    │   ├── decorators.py     # @require_role, @jwt_required
    │   ├── models.py         # User, RefreshToken, ResetToken
    │   └── services.py       # User Management, Login/Logout Logic
    ├── config/               # Konfiguration
    │   ├── __init__.py       # BaseConfig, DevConfig, load_config
    │   └── countries.py      # Location Data (CO.RA.PAN-spezifisch)
    ├── extensions/           # Flask Extensions Init
    │   ├── __init__.py
    │   └── sqlalchemy_ext.py # SQLAlchemy Engine, Session Management
    ├── models/               # (Leer - Models in Feature-Modulen)
    ├── routes/               # Blueprints (Route Definitions)
    │   ├── __init__.py       # register_blueprints()
    │   ├── admin.py          # Admin Dashboard
    │   ├── admin_users.py    # User Management (Admin)
    │   ├── analytics.py      # Analytics Dashboard
    │   ├── atlas.py          # Geografische Visualisierung
    │   ├── auth.py           # Login, Logout, Token Refresh
    │   ├── bls_proxy.py      # BlackLab Server Proxy
    │   ├── corpus.py         # Korpussuche (einfach + CQL)
    │   ├── editor.py         # JSON-Editor (Editor-Rolle)
    │   ├── media.py          # Audio-Datei-Serving
    │   ├── player.py         # Audio-Player
    │   ├── public.py         # Startseite, Impressum, etc.
    │   └── stats.py          # Statistiken, Charts, Export
    ├── search/               # Suchlogik (BlackLab Integration)
    │   ├── __init__.py
    │   ├── search_service.py # Search Execution
    │   └── cql_builder.py    # CQL Query Builder (Pattern Builder)
    └── services/             # Shared Services
        └── (diverse)
```

**Prinzipien:**
- **Feature-basierte Module:** Jedes Feature hat eigenes Paket (auth, search, analytics)
- **Blueprints in `routes/`:** Route-Definitionen getrennt von Logik
- **Services in Feature-Modulen:** Business Logic in `<feature>/services.py`
- **Models in Feature-Modulen:** SQLAlchemy Models in `<feature>/models.py`

---

## `templates/` — Jinja2 Templates

```
templates/
├── base.html                 # Base Layout (NavDrawer, TopAppBar, Footer)
├── home/
│   └── index.html            # Startseite
├── pages/
│   ├── impressum.html
│   ├── privacy.html
│   └── ...
├── auth/
│   ├── login.html            # Login-Seite (mit Login-Sheet)
│   └── ...
├── admin/
│   ├── dashboard.html
│   └── users.html
├── search/
│   ├── simple.html           # Einfache Suche
│   ├── advanced.html         # CQL/Pattern Builder
│   └── results.html          # KWIC-Ansicht
├── atlas/
│   └── index.html            # Karten-Visualisierung
├── stats/
│   └── index.html            # Statistik-Dashboard
├── editor/
│   └── index.html            # JSON-Editor
├── player/
│   └── (keine Templates, nur JSON-API)
├── partials/                 # Wiederverwendbare Komponenten
│   ├── _navigation_drawer.html
│   ├── _top_app_bar.html
│   ├── _footer.html
│   ├── _login_sheet.html
│   └── ...
├── errors/
│   ├── 403.html
│   ├── 404.html
│   └── 500.html
└── _md3_skeletons/           # Template-Vorlagen für neue Seiten
```

**Konventionen:**
- **Partials:** `_` Prefix für inkludierbare Komponenten
- **Feature-Ordner:** Pro Modul ein Unterordner
- **MD3-konform:** Alle Templates nutzen Design System Tokens

---

## `static/` — Frontend Assets

```
static/
├── css/
│   ├── layout.css            # Global Layout (Grid, Container)
│   ├── app-tokens.css        # App-spezifische Token-Overrides
│   └── md3/                  # Material Design 3 System
│       ├── tokens.css        # Design Tokens (Colors, Spacing, etc.)
│       ├── typography.css    # Typografie-System
│       ├── layout.css        # Layout-Utilities
│       ├── tokens-legacy-shim.css  # Mapping alter Namen (deprecated)
│       └── components/       # UI-Komponenten
│           ├── buttons.css
│           ├── cards.css
│           ├── dialog.css
│           ├── textfields.css
│           ├── navbar.css
│           ├── navigation-drawer.css
│           ├── top-app-bar.css
│           ├── snackbar.css
│           ├── alerts.css
│           └── ...
├── js/
│   ├── theme.js              # Dark/Light Mode Toggle
│   ├── auth-setup.js         # JWT Refresh Logic
│   ├── logout.js             # Logout Handler
│   ├── navigation-drawer-init.js
│   ├── theme-toggle.js
│   └── ...
├── img/
│   ├── logo.svg
│   ├── favicon.ico
│   └── ...
├── fonts/                    # (Falls lokale Fonts)
└── vendor/
    └── htmx.min.js           # Externe Libraries (lokal gecacht)
```

**CSS-Architektur:**
1. **Tokens:** Zentrale Design-Variablen (`tokens.css`)
2. **App-Overrides:** Projekt-spezifische Anpassungen (`app-tokens.css`)
3. **Komponenten:** Wiederverwendbare UI-Elemente (`components/`)
4. **Layout:** Grid, Container, Spacing (`layout.css`)

**JavaScript:**
- **Vanilla JS:** Keine Build-Tools, kein Bundler
- **htmx:** Progressive Enhancement für AJAX
- **Modular:** Ein File pro Feature (theme, auth, drawer, etc.)

---

## `config/` — Externe Konfiguration

```
config/
├── blacklab/                 # BlackLab Server Konfiguration
│   └── blacklab-server.yaml
└── keys/                     # JWT Private Keys (nicht in Git!)
    └── jwt_private_key.pem
```

**Wichtig:** `keys/` ist in `.gitignore` und muss lokal/prod manuell erstellt werden.

---

## `data/` — Runtime-Datenbanken

```
data/
├── db/                       # SQLite/Postgres Daten (lokal)
│   ├── public/               # Öffentliche DBs (falls vorhanden)
│   └── restricted/           # Sensitive DBs (lokal/prod getrennt)
├── counters/                 # App-Counters (z.B. Export-IDs)
├── exports/                  # Generierte CSV/TSV Exporte
├── public/metadata/          # Metadaten-Cache
├── stats_temp/               # Temp-Files für Statistiken
├── blacklab_index/           # BlackLab Index (große Dateien, nicht in Git)
└── blacklab_export/          # BlackLab Export-Files
```

**Hinweis:** `data/` wird lokal ignoriert, in Produktion via Volumes gemountet.

---

## `media/` — Audio & Transkripte

```
media/
├── mp3-full/                 # Vollständige Audio-Dateien (ein File pro Gespräch)
├── mp3-split/                # Segmentierte Audio-Dateien (ein File pro Segment)
├── mp3-temp/                 # Temporäre Audio-Verarbeitung
└── transcripts/              # JSON-Transkripte (ein File pro Gespräch)
```

**Wichtig:** Diese Dateien sind **sehr groß** (mehrere GB) und nicht im Git-Repo. In Produktion via Docker Volumes (Read-Only) gemountet.

---

## `migrations/` — Datenbank-Migrationen

```
migrations/
├── 0001_create_auth_schema_postgres.sql
├── 0001_create_auth_schema_sqlite.sql
└── 0002_create_analytics_tables.sql
```

**Manuell ausgeführt:** Kein Alembic, bewusste Entscheidung für einfache Struktur.

---

## `scripts/` — Automation & Maintenance

```
scripts/
├── dev-setup.ps1             # Einmaliges Setup (venv, Docker, DB)
├── dev-start.ps1             # Dev-Server starten
├── deploy_prod.sh            # Production Deployment
├── create_initial_admin.py   # Admin-User anlegen
├── anonymize_old_users.py    # DSGVO-Compliance (Soft-Delete)
├── backup.sh                 # Datenbank-Backup
└── ...
```

**Wichtig:** PowerShell-Skripte für Windows, Bash-Skripte für Linux.

---

## `tests/` — Tests

```
tests/
├── conftest.py               # Pytest Fixtures
├── test_auth.py
├── test_search.py
└── ...
```

**Test-Runner:** `pytest` (siehe `pyproject.toml`)

---

## Spezielle Verzeichnisse

### `LOKAL/` (Nicht Teil der Webapp)

**Hinweis:** `LOKAL/` ist ein **separates Repo** mit schweren NLP-Tools (JSON→BlackLab Pipeline). Wird in `.gitignore`, `.dockerignore` und CI explizit ausgeschlossen.

Für neue Projekte (Template-Nutzung) ist `LOKAL/` **nicht relevant**.

---

## "Was gehört wohin"-Regeln

| Dateityp | Zielort | Beispiel |
|----------|---------|----------|
| Python-Code | `src/app/` | `src/app/auth/services.py` |
| Templates | `templates/<feature>/` | `templates/auth/login.html` |
| CSS | `static/css/` | `static/css/md3/components/buttons.css` |
| JavaScript | `static/js/` | `static/js/theme.js` |
| Bilder | `static/img/` | `static/img/logo.svg` |
| Config | `config/` oder ENV-Vars | `config/keys/jwt_private_key.pem` |
| Datenbanken | `data/db/` | `data/db/auth.db` |
| Audio | `media/mp3-split/` | `media/mp3-split/es-bog-001_001.mp3` |
| Transkripte | `media/transcripts/` | `media/transcripts/es-bog-001.json` |
| Migrations | `migrations/` | `migrations/0001_create_auth_schema_postgres.sql` |
| Tests | `tests/` | `tests/test_auth.py` |
| Doku | `docs/` | `docs/architecture/overview.md` |
| Scripts | `scripts/` | `scripts/dev-setup.ps1` |

---

## Anpassung für neue Projekte

Wenn du das Repo als Template nutzt:

1. **`src/app/config/countries.py`**: CO.RA.PAN-spezifische Location-Daten entfernen (falls nicht benötigt)
2. **`media/`**: Audio/Transkripte sind projekt-spezifisch (löschen oder eigene Daten verwenden)
3. **`data/blacklab_index/`**: BlackLab-Index neu erstellen oder Modul entfernen
4. **`templates/`**: Seiten in `templates/home/`, `templates/pages/` anpassen
5. **`static/img/`**: Logo, Favicon ersetzen
6. **`static/css/app-tokens.css`**: Farben/Branding anpassen
