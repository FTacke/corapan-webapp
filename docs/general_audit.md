# General Audit — Repo, Runtime, Ops, LOKAL

**Datum:** 2026-01-20  
**Rolle:** Repo-Maintainer / Lead Engineer (Ops + App)  
**Ziel:** Bestandsaufnahme + konkrete Empfehlungen.  
**Scope:** Nur Fakten aus dem Repo, keine Code-Änderungen außer dieser Datei.

---

## 1) Repo-Inventar (harte Fakten)

### 1.1 Top-Level-Struktur (Depth 2)

**Ordner (Top-Level):**

| Ordner | Kurzbeschreibung | Evidence |
|---|---|---|
| .github | GitHub Actions Workflows | [.github/workflows/](.github/workflows/) |
| config | BlackLab-Konfig + Keys-Verzeichnis (Keys sind extern) | [config/](config/) |
| data | Runtime/Build-Daten (BlackLab Index, Exports etc.) | [data/](data/) |
| docs | Projekt- und Ops-Dokumentation | [docs/](docs/) |
| infra | Docker-Compose (dev/prod) | [infra/](infra/) |
| logs | Laufzeit-Logs (lokal) | [logs/](logs/) |
| LOKAL | Gitignored Admin/Pipeline-Repo (separates Repo) | [LOKAL/](LOKAL/) |
| migrations | SQL-Schemata für Auth/Analytics | [migrations/](migrations/) |
| reports | Lint-/Audit-Reports | [reports/](reports/) |
| runtime | Repo-lokale Runtime (dev; gitignored) | [runtime/](runtime/) |
| scripts | Ops/Build/Debug/Dev/Deploy-Skripte | [scripts/](scripts/) |
| src | App-Code (Flask) + interne Scripts | [src/](src/) |
| static | Frontend Assets | [static/](static/) |
| templates | Jinja-Templates | [templates/](templates/) |
| tests | Pytest + E2E | [tests/](tests/) |
| tools | Dritt-Tools (cwRsync) | [tools/](tools/) |

**Lokale Artefakte (nicht Teil der App-Logik):**

- `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `node_modules/`, `__pycache__/` (lokal/auto-generiert)

**Top-Level-Dateien (Auswahl):**

- App/Build/Deploy: [Dockerfile](Dockerfile), [docker-compose.yml](docker-compose.yml), [docker-compose.dev-postgres.yml](docker-compose.dev-postgres.yml), [infra/docker-compose.dev.yml](infra/docker-compose.dev.yml), [infra/docker-compose.prod.yml](infra/docker-compose.prod.yml)
- Setup/Docs: [README.md](README.md), [startme.md](startme.md), [CONTRIBUTING.md](CONTRIBUTING.md)
- Python: [requirements.txt](requirements.txt), [pyproject.toml](pyproject.toml)
- Node/E2E: [package.json](package.json), [playwright.config.js](playwright.config.js)
- Env/Secrets (lokal): [.env](.env), [.env.example](.env.example), [passwords.env](passwords.env), [passwords.env.template](passwords.env.template)

---

### 1.2 App-Entry (Start lokal / prod)

**Python Entry:**

- `python -m src.app.main` initialisiert `create_app()` und startet dev server.  
  Evidence: [src/app/main.py](src/app/main.py), [src/app/__init__.py](src/app/__init__.py)

**Lokaler Start (empfohlen):**

- Quickstart: [startme.md](startme.md)
- Täglicher Start: [scripts/dev-start.ps1](scripts/dev-start.ps1)
- Full Setup: [scripts/dev-setup.ps1](scripts/dev-setup.ps1)

**Production Start:**

- Dockerfile (Gunicorn, Port 5000): [Dockerfile](Dockerfile)
- Prod Compose: [infra/docker-compose.prod.yml](infra/docker-compose.prod.yml)
- Deploy Script: [scripts/deploy_prod.sh](scripts/deploy_prod.sh)
- GitHub Deploy Workflow: [.github/workflows/deploy.yml](.github/workflows/deploy.yml)

---

### 1.3 Runtime / Data / Media / Logs (Source of Truth)

**Canonical Runtime-Layout:**

- Contract: [docs/runtime_data_contract.md](docs/runtime_data_contract.md)
- Audit / Path-Matrix: [docs/runtime_data_audit.md](docs/runtime_data_audit.md), [docs/state/path_usage_matrix.md](docs/state/path_usage_matrix.md)

**Wesentliche Wurzeln:**

- `CORAPAN_RUNTIME_ROOT` → `data/` (mandatory in prod; dev fallback vorhanden)  
  Evidence: [src/app/config/__init__.py](src/app/config/__init__.py)
- `CORAPAN_MEDIA_ROOT` → `media/` (mandatory; **kein fallback**)  
  Evidence: [src/app/config/__init__.py](src/app/config/__init__.py)
- `PUBLIC_STATS_DIR` (optional override)  
  Evidence: [src/app/config/__init__.py](src/app/config/__init__.py)

**Runtime First (Prod):**

- Mount-Contract `/app/data`, `/app/media`, `/app/logs`, `/app/config`  
  Evidence: [infra/docker-compose.prod.yml](infra/docker-compose.prod.yml), [scripts/deploy_prod.sh](scripts/deploy_prod.sh), [scripts/deploy_sync/README.md](scripts/deploy_sync/README.md)

---

### 1.4 Konfiguration (ENV / config/)

**Templates/Beispiele:**

- [.env.example](.env.example)
- [docs/architecture/configuration.md](docs/architecture/configuration.md)

**Pflichtvariablen (prod; aus Code abgeleitet):**

- `FLASK_SECRET_KEY` (required)  
- `JWT_SECRET_KEY` (required)  
- `AUTH_DATABASE_URL` (required)  
- `CORAPAN_MEDIA_ROOT` (required, **no fallback**)  
- `CORAPAN_RUNTIME_ROOT` (required in prod; dev fallback möglich)  
  Evidence: [src/app/config/__init__.py](src/app/config/__init__.py)

**Wichtige optionale Variablen:**

- `BLS_BASE_URL`, `BLS_CORPUS` (BlackLab)  
- `PUBLIC_STATS_DIR`, `STATS_TEMP_DIR`  
- `ALLOW_PUBLIC_TEMP_AUDIO`, `ALLOW_PUBLIC_FULL_AUDIO`, `ALLOW_PUBLIC_TRANSCRIPTS`  
- `FLASK_SESSION_SECURE`, `FLASK_SESSION_SAMESITE`, `JWT_COOKIE_SECURE`  
  Evidence: [src/app/config/__init__.py](src/app/config/__init__.py)

**Config Files:**

- BlackLab config: [config/blacklab/](config/blacklab/)
- Keys path (extern gemountet): [config/keys/](config/keys/)

---

### 1.5 CI / Workflows

| Workflow | Zweck | Evidence |
|---|---|---|
| CI | Lint + minimaler Runtime-Setup, Tests sind deaktiviert | [.github/workflows/ci.yml](.github/workflows/ci.yml) |
| Deploy | Self-hosted Prod-Deploy via [scripts/deploy_prod.sh](scripts/deploy_prod.sh) | [.github/workflows/deploy.yml](.github/workflows/deploy.yml) |
| MD3 Lint | UI-Guard/Lint für Templates & MD3 CSS | [.github/workflows/md3-lint.yml](.github/workflows/md3-lint.yml) |

---

### 1.6 Deploy (Canonical vs Doppelungen)

**Canonical (Prod):**

- Compose: [infra/docker-compose.prod.yml](infra/docker-compose.prod.yml)
- Deploy Script: [scripts/deploy_prod.sh](scripts/deploy_prod.sh)

**Dev (zwei Varianten):**

- [docker-compose.dev-postgres.yml](docker-compose.dev-postgres.yml) (DB + BlackLab)  
- [infra/docker-compose.dev.yml](infra/docker-compose.dev.yml) (App + DB + BlackLab)  
  Evidence: [docker-compose.dev-postgres.yml](docker-compose.dev-postgres.yml), [infra/docker-compose.dev.yml](infra/docker-compose.dev.yml)

**Legacy/Alternate:**

- [docker-compose.yml](docker-compose.yml) (root) weicht in Ports/Bindings vom Dockerfile ab (siehe Findings).

---

### 1.7 Tests / Lint

**Pytest:**

- Tests: [tests/](tests/)
- Markers & Defaults: [pyproject.toml](pyproject.toml)
- Test-Doc: [tests/README.md](tests/README.md)

**E2E:**

- Playwright: [package.json](package.json), [playwright.config.js](playwright.config.js)

**CI-Status:**

- CI lint läuft, Tests werden aktuell übersprungen.  
  Evidence: [.github/workflows/ci.yml](.github/workflows/ci.yml)

---

### 1.8 Dependencies (Python/Node)

**Runtime Dependencies (Python):**

- [requirements.txt](requirements.txt) (Pins, teils `>=` bei `psycopg2-binary`, `argon2-cffi`)

**Dev Dependencies (Python):**

- [pyproject.toml](pyproject.toml) (pytest, ruff, mypy)

**Node:**

- [package.json](package.json) (nur Playwright für E2E)

---

### 1.9 Docs Inventory

**Top-Level Docs:**

- [docs/index.md](docs/index.md)  
- [docs/checkup.md](docs/checkup.md)  
- [docs/local_runtime_layout.md](docs/local_runtime_layout.md)  
- [docs/runtime_data_contract.md](docs/runtime_data_contract.md)  
- [docs/runtime_data_audit.md](docs/runtime_data_audit.md)

**Docs-Unterordner (Auswahl):**

- Architektur: [docs/architecture/](docs/architecture/)  
- Operations: [docs/operations/](docs/operations/)  
- Modules: [docs/modules/](docs/modules/)  
- State/Audit: [docs/state/](docs/state/)  
- BlackLab: [docs/blacklab/](docs/blacklab/)  
- UI Conventions: [docs/ui_conventions/](docs/ui_conventions/)  
- Data Cleanup: [docs/data_cleanup/](docs/data_cleanup/)

**Hinweis:** [docs/index.md](docs/index.md) verweist auf mehrere Pfade, die aktuell im Repo nicht existieren (z.B. docs/how-to, docs/reference, docs/analytics, docs/ui/design-system.md). Siehe Findings.

---

## 2) Konsistenz-Checks (Findings)

**Tabelle:** Bereich | Befund | Risiko | Empfehlung | Aufwand (S/M/L)

| Bereich | Befund | Risiko | Empfehlung | Aufwand |
|---|---|---|---|---|
| Pfad-/Runtime-Konzept | `CORAPAN_MEDIA_ROOT` ist **required** in Code, aber in [.env.example](.env.example) nicht enthalten. | Runtime-Bruch bei manueller .env-Nutzung | `.env.example` und Doku ergänzen, klare Pflichtliste. | S |
| Pfad-/Runtime-Konzept | `PUBLIC_STATS_DIR` ist standardmäßig `/app/data/public/statistics` im Template, aber dev scripts nutzen repo-lokales Runtime-Root. | Verwirrung / falsche Pfade | Doku: klarer Dev vs Prod Pfad + Beispiel in [startme.md](startme.md). | S |
| Docker/Compose | [docker-compose.yml](docker-compose.yml) mapped `6000:8000`, Dockerfile bindet `5000`. | Container startet ohne Traffic / Healthcheck mismatch | Datei als legacy markieren oder Port/Healthcheck anpassen. | S |
| Docker/Compose | Zwei Dev-Stacks: [docker-compose.dev-postgres.yml](docker-compose.dev-postgres.yml) und [infra/docker-compose.dev.yml](infra/docker-compose.dev.yml). | Doppelte Wahrheiten (Ports, ENV, Volumes) | Einen Stack als „canonical dev“ kennzeichnen, anderen als legacy. | M |
| Docker/Compose | [docs/operations/local-dev.md](docs/operations/local-dev.md) nennt Ports 5432/8080, Dev-Compose nutzt 54320/8081. | Setup-Fehler | Docs korrigieren oder Port-Map angleichen. | S |
| Config/ENV | Unterschiedliche Namen: `BLS_BASE_URL` (Code) vs `BLACKLAB_BASE_URL` (Scripts) vs README. | Falsche BlackLab-URL in Env | Vereinheitlichen in Doku und Scripts (Alias dokumentieren). | S |
| CI Gate | Lint wird mit `ruff check ... || true` nicht als Gate genutzt; Tests werden im CI explizit übersprungen. | Qualitäts-Gate inaktiv | CI-Plan definieren: welche Tests sollen blocken? | M |
| Secrets | Dateien [.env](.env) und [passwords.env](passwords.env) liegen im Repo-Root (lokal sichtbar). | Secrets-Leak (wenn committed) | Sicherstellen, dass sie gitignored bleiben + auf Template verweisen. | S |
| Logging | `logs/` enthält reale Logfiles im Repo-Root. | Risiko, versehentlich zu committen | `.gitignore` prüfen; ggf. Log-Dir nur runtime. | S |
| Docs | [docs/index.md](docs/index.md) referenziert Pfade, die fehlen; README verlinkt nicht existente Dokus. | Onboarding-Verwirrung | Doku-Index bereinigen oder fehlende Files erstellen. | M |
| Scripts-Organisation | Drei Orte: [scripts/](scripts/), [src/scripts/](src/scripts/), [LOKAL/](LOKAL/). | kognitive Last, unklare Ownership | Konvention klar definieren (App-intern vs Ops vs Pipeline). | M |
| Security Basics | Dev-Skripte setzen `ALLOW_PUBLIC_FULL_AUDIO`/`ALLOW_PUBLIC_TRANSCRIPTS` auf `true`. | Potenziell zu offen, wenn in prod übernommen | Klarer „dev-only“ Hinweis in Doku/Script. | S |
| Dead code / Legacy | `scripts/dev-start.ps1.broken`, legacy compose, passwords.env (deprecated). | Technische Schulden | Deprecation-Policy dokumentieren + cleanup-Liste. | S |

---

## 3) LOKAL Pipeline Integration

### 3.1 Was ist LOKAL wahrscheinlich?

**Beobachtete Kategorien (aus Verzeichnisstruktur):**

- **JSON/Preprocess Pipeline:** [LOKAL/_0_json/](LOKAL/_0_json/)
- **MP3 Processing:** [LOKAL/_0_mp3/](LOKAL/_0_mp3/)
- **BlackLab Export/Index:** [LOKAL/_1_blacklab/](LOKAL/_1_blacklab/)
- **Metadata Export:** [LOKAL/_1_metadata/](LOKAL/_1_metadata/)
- **Zenodo Repos:** [LOKAL/_1_zenodo-repos/](LOKAL/_1_zenodo-repos/)
- **Deploy Orchestrators:** [LOKAL/_2_deploy/](LOKAL/_2_deploy/)
- **Analysis/Results:** [LOKAL/_3_analysis_on_json/](LOKAL/_3_analysis_on_json/)
- **Dependencies:** [LOKAL/requirements-lokal.txt](LOKAL/requirements-lokal.txt)
- **Meta:** [LOKAL/README.md](LOKAL/README.md)

**Warum gitignored/separates Repo? (wahrscheinliche Gründe):**

- Große Daten/Artefakte (Audio, Exports, Outputs)
- Environment- oder Host-spezifische Pfade
- Risiko von Secrets/Keys in Ops-Skripten
- Separates Release/Access Control

---

### 3.2 Kriterien für Integration ins Hauptrepo

**Darf rein (Hauptrepo):**

- Skriptbarer Code ohne Secrets/PII
- Reproduzierbare Tools/CLI
- Admin-Tools, die nur auf runtime paths arbeiten

**Darf NICHT rein:**

- Personenbezogene Daten, Audio/Transkript-Originale
- Private Keys / SSH Configs
- Host-spezifische Pfade oder Credentials

**Grenzfälle:**

- Config Templates statt echter Configs  
- Platzhalter/Docs statt realer Outputs

---

### 3.3 Integrations-Optionen (Bewertung)

| Option | Vorteile | Nachteile | Risiken (Secrets/PII/Host coupling) | Aufwand | Empfehlung |
|---|---|---|---|---|---|
| A) Hauptrepo als `admin/` oder `ops/` | Sichtbarkeit, CI-fähig, einfache Nutzung | Repo wächst, klare Grenzen nötig | Mittel: Muss strikt templatisiert werden | M | **Go** (wenn klare Regeln) |
| B) Git-Submodule | Access-Control, getrennte Historie | Submodule-Friktion, CI komplizierter | Niedrig | M | **No-Go** (Alltagskosten hoch) |
| C) Separates Repo + Release-Artefakte | Saubere Trennung, minimaler Risiko | Doku/Version Drift | Niedrig | S | **Go** (kurzfristig ok) |
| D) Private Package/CLI | Versioniert, sauber deploybar | Packaging-Aufwand | Niedrig | L | **Maybe** (mittel/langfristig) |

---

### 3.4 Konkreter Vorschlag: „Wenn wir integrieren, dann so“

**Zielstruktur (Vorschlag):**

```
admin/
  README.md
  pipeline/
    sync_data.ps1
    sync_media.ps1
    build_blacklab_index.sh
    export_stats.py
  templates/
    env.admin.example
    runtime.layout.md
  runbooks/
    prod_deploy.md
    data_sync.md
```

**Kandidaten (Kategorien, keine inhaltlichen Annahmen):**

- Pipeline: JSON/MP3/BlackLab/Metadata/Deploy-Orchestrierung  
  Evidence: [LOKAL/_0_json/](LOKAL/_0_json/), [LOKAL/_0_mp3/](LOKAL/_0_mp3/), [LOKAL/_1_blacklab/](LOKAL/_1_blacklab/), [LOKAL/_1_metadata/](LOKAL/_1_metadata/), [LOKAL/_2_deploy/](LOKAL/_2_deploy/)

**Zwingend umzubauen:**

- Secrets raus → Env vars / Templates
- Pfade parametrieren (keine Host-Hardcodes)
- Logging vereinheitlichen (runtime/logs)

**Als Template statt 1:1:**

- Beispiel-ENV und PowerShell Templates (keine echten Secrets)  
- Runbooks mit Safety-Checklist

---

## 4) Minimum Next Steps (1–2 Sessions)

**Priorisierte TODOs (mit Owner / Aufwand / Impact):**

1) **Port-Mismatch fixen (compose vs Dockerfile)** — Owner: Ops — Aufwand: S — Impact: High  
2) **Dev-Docs Ports angleichen** — Owner: Maintainer — Aufwand: S — Impact: Medium  
3) **ENV Pflichtliste + `CORAPAN_MEDIA_ROOT` in Templates** — Owner: Maintainer — Aufwand: S — Impact: High  
4) **Doku-Index bereinigen (fehlende Pfade)** — Owner: Docs — Aufwand: M — Impact: Medium  
5) **CI Gate definieren (Ruff/Test Strategy)** — Owner: QA/Eng — Aufwand: M — Impact: High  
6) **Dev-Stack „canonical“ markieren** — Owner: Ops — Aufwand: S — Impact: Medium  
7) **Legacy-Label für [docker-compose.yml](docker-compose.yml) + [scripts/dev-start.ps1.broken](scripts/dev-start.ps1.broken)** — Owner: Maintainer — Aufwand: S — Impact: Medium  
8) **LOKAL Integration Decision (A vs C)** — Owner: Maintainer/Ops — Aufwand: M — Impact: Medium  
9) **Secrets Hygiene Check (gitignore + pre-commit)** — Owner: Security/Ops — Aufwand: S — Impact: High  
10) **Logging-Rotation/Retention klar dokumentieren** — Owner: Ops — Aufwand: S — Impact: Medium

---

## Anhang: Quick Links

- Start lokal: [startme.md](startme.md)  
- Prod Deploy: [scripts/deploy_prod.sh](scripts/deploy_prod.sh)  
- Runtime Contract: [docs/runtime_data_contract.md](docs/runtime_data_contract.md)  
- Config: [docs/architecture/configuration.md](docs/architecture/configuration.md)