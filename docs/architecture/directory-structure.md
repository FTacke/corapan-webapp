# Directory Structure

This document reflects the current repository layout after the cleanup pass.

## Root

```text
corapan/
    .github/                    active governance and workflows
    app/                        versioned application and deploy implementation
    docs/                       canonical maintainer documentation
    scripts/                    root dev entry points
    data/                       runtime state, not versioned
    media/                      runtime media, not versioned
    maintenance_pipelines/      separate operational subtree
    docker-compose.dev-postgres.yml
    README.md
    AGENTS.md
```

## App

```text
app/
    src/app/                    Flask backend and shared services
    templates/                  Jinja templates
    static/                     CSS, JS, images
    migrations/                 SQL migrations
    scripts/                    app-level helpers and deploy scripts
    infra/                      production compose and secondary full-stack helper
    requirements*.in|txt        Python dependency sources and compiled locks
    package.json                Playwright-only Node manifest
    pyproject.toml              Python project metadata and tool config
```

## Key Ownership Rules

- root `scripts/` and root `docker-compose.dev-postgres.yml` define the canonical local dev path
- `app/infra/docker-compose.prod.yml` defines the canonical production compose path
- runtime data and media are outside the versioned app tree
- `.github/` is the active governance layer for the whole repository

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
