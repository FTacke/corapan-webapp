# Workflows Inventory

## `.github/workflows/ci.yml`

Trigger:
- `push` auf `main`, `prod_prep`
- `pull_request` gegen `main`
- `workflow_dispatch`

Jobs:
- `fast-checks`
  - Zweck: schneller Pflichtcheck fuer Struktur, Ruff und servicefreie Pytest-Suite
  - Runner: `ubuntu-latest`
  - Dependencies: keine
  - Cache: pip ueber `actions/setup-python`
  - Services/Container: keine
- `auth-hash-compat`
  - Zweck: fokussierte Kompatibilitaetspruefung fuer `argon2` und `bcrypt` ohne Vollsuite-Matrix
  - Runner: `ubuntu-latest`
  - Dependencies: keine
  - Cache: pip
  - Services/Container: keine
- `migration-postgres`
  - Zweck: kanonischer Auth-/App-Start-Smoke gegen PostgreSQL; fuehrt Migration aus und startet Full App Context fuer zielgerichtete Tests
  - Runner: `ubuntu-latest`
  - Dependencies: keine
  - Cache: pip
  - Services/Container: `postgres:15`
- `playwright-e2e`
  - Zweck: manueller Browser-Smoke gegen kanonisches PostgreSQL statt SQLite
  - Runner: `ubuntu-latest`
  - Dependencies: `needs: fast-checks`
  - Trigger-Einschraenkung: nur `workflow_dispatch`
  - Cache: pip und npm
  - Services/Container: `postgres:15`

Historische Vereinfachung:
- alte Vollsuite-Matrix `python-version x auth-hash-algo` entfernt
- alter `Skip tests (CI minimal)`-Schritt entfernt
- SQLite-E2E-Seeding aus der CI entfernt

## `.github/workflows/md3-lint.yml`

Trigger:
- `pull_request` gegen `main` mit `paths` auf `app/templates/**`, `app/static/css/md3/components/**`, `app/scripts/**`
- `workflow_dispatch`

Jobs:
- `md3-lint`
  - Zweck: spezialisierter UI-/Template-Regelcheck fuer MD3
  - Runner: `ubuntu-latest`
  - Dependencies: keine
  - Cache: pip
  - Services/Container: keine

## `.github/workflows/deploy.yml`

Trigger:
- `push` auf `main`
- `workflow_dispatch`

Jobs:
- `deploy`
  - Zweck: Produktionsdeployment auf Self-Hosted Runner
  - Runner: `self-hosted`
  - Dependencies: keine
  - Cache: keine
  - Services/Container: nutzt Server-Docker direkt, aber kein CI-Service-Container

Einordnung:
- `deploy` ist operativ wichtig, aber kein eigentlicher Produktqualitaets-Job.
- `fast-checks` und `migration-postgres` sind die zentralen Qualitaetsgates.
- `playwright-e2e` ist wertvoll, aber wegen Kosten und Laufzeit sinnvoll als manueller schwerer Check.
