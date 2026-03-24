# Failing Jobs

Hinweis:
- echte GitHub-Run-Metadaten waren lokal nicht verfuegbar, weil `gh` fehlt
- die Angaben unten stammen aus Workflow-Analyse und lokaler Reproduktion

## `test (3.12, bcrypt)`

- Jobname: historischer Matrix-Zweig aus `ci.yml`
- Exakter Fehler:
  - fachlich inkonsistent: der aktuelle Workflow fuehrte gar kein `pytest` aus, sondern nur `echo "Pytest disabled in CI"`
  - bei lokaler ehrlicher Reproduktion der Suite traten zuerst Importzeit-Abbrueche durch harte Konfigurationsvalidierung auf
- Erster relevanter Logabschnitt:
  - `RuntimeError: BLS_CORPUS environment variable is required. For the canonical dev stack, set BLS_CORPUS=corapan.`
- Reproduzierbarkeit lokal: `ja`
- Vermutete Ursache:
  - Tests wurden im Workflow faktisch deaktiviert, weil die Suite wegen Importzeit- und SQLAlchemy-Problemen nicht stabil war

## `test (3.12, argon2)`

- Jobname: historischer Matrix-Zweig aus `ci.yml`
- Exakter Fehler:
  - derselbe strukturelle Fehler wie oben; zusaetzlich war die Matrix fachlich ueberbreit fuer den realen Support-Scope
- Erster relevanter Logabschnitt:
  - identisch zum `bcrypt`-Zweig vor Fix
- Reproduzierbarkeit lokal: `ja`
- Vermutete Ursache:
  - Hash-Algorithmus-Matrix war kein Root Cause; die eigentlichen Defekte lagen in Konfigurationsimporten und ORM-Filtern

## `migration-postgres`

- Jobname: `migration-postgres`
- Exakter Fehler:
  - Workflow setzte vor dem Fix `BLS_CORPUS` nicht fuer den Testschritt
  - `create_app("testing")` fiel deshalb bereits vor eigentlichem Smoke-Test um
- Erster relevanter Logabschnitt:
  - `RuntimeError: BLS_CORPUS environment variable is required. For the canonical dev stack, set BLS_CORPUS=corapan.`
- Reproduzierbarkeit lokal: `teilweise`
- Vermutete Ursache:
  - fehlende Pflichtvariablen im Workflow und fehlende `testing`-Config
  - volle Postgres-Verifikation lokal blockiert durch fehlenden Docker-Daemon

## `playwright-e2e`

- Jobname: `playwright-e2e`
- Exakter Fehler:
  - Workflow startete die App mit SQLite-Auth und ohne `BLS_CORPUS`
  - der Serverstart brach noch vor Playwright ab
- Erster relevanter Logabschnitt:
  - `RuntimeError: BLS_CORPUS environment variable is required. For the canonical dev stack, set BLS_CORPUS=corapan.`
- Reproduzierbarkeit lokal: `ja`
- Vermutete Ursache:
  - nicht-kanonischer SQLite-E2E-Pfad in der CI
  - fehlende Pflichtvariablen fuer den App-Start

## Action-Warnings

- Betroffen:
  - `actions/checkout@v4`
  - `actions/setup-python@v5`
  - Node-Runtime-Hinweise
- Ursache:
  - veraltete Action-Majors
- Status:
  - auf `checkout@v6`, `setup-python@v6`, `setup-node@v6` angehoben
