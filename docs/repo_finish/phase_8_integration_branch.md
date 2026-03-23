# Phase 8 - Integration Branch

Datum: 2026-03-23
Workspace: `C:\dev\corapan`
Modus: lokaler Integrations-Branch auf Basis von `origin/main`, ohne Push nach `main`, ohne Deploy

## 1. Kurzurteil

Der Integrations-Branch `root-lift-integration` wurde erfolgreich **direkt auf Basis von `origin/main`** erstellt und der publizierte Zielbaum von `origin/root-lift-review` wurde **kontrolliert als neue Projektstruktur uebernommen**, ohne Merge, ohne `--allow-unrelated-histories` und ohne Cherry-Pick.

Der resultierende Stand ist lokal technisch plausibel:

- Root-Struktur entspricht dem Root-Lift-Zielbild
- `webapp/` ist nicht mehr vorhanden
- `CONFIG_ROOT` bleibt korrekt auf `data/config`
- `docker compose config` rendert sauber
- `create_app('development')` startet mit den kanonischen Dev-Variablen erfolgreich

Damit lautet das Urteil fuer den Integrations-Branch selbst:

### GO ALS GRUNDLAGE FUER EINEN SPAETEREN PR

nicht aber fuer einen sofortigen Merge nach `main`, solange Review, CI-Pruefung und Freigabe noch ausstehen.

## 2. Branch-Erstellung

Ausgangspunkt war ausdruecklich `origin/main`.

Geprueft und umgesetzt wurde:

- `origin/main = 9c819e6`
- `origin/root-lift-review = 07f5b6e`
- neuer lokaler Branch: `root-lift-integration`
- Branch-Start direkt von `origin/main`

Wichtig:

- der Branch wurde **nicht** von `root-lift-review` abgezweigt
- es wurde keine Historienverknuepfung zwischen beiden Linien erzeugt
- die Integration erfolgte als bewusste Baumuebernahme auf einem Branch, dessen Historie bei `origin/main` beginnt

## 3. Baumuebernahme

Die Uebernahme erfolgte bewusst ohne Git-Merge-Mechanik:

1. Branch `root-lift-integration` auf `origin/main` erstellt
2. bestehenden Arbeitsbaum dieses Branchs vollstaendig aus dem Index entfernt
3. Inhalt von `origin/root-lift-review` gezielt in den Arbeitsbaum uebernommen
4. Ergebnis erneut vollstaendig gestaged

Wichtig:

- kein `merge`
- kein `--allow-unrelated-histories`
- kein `cherry-pick`
- keine Rebase-Mechanik

Damit ist die technische Form der Uebernahme genau der zuvor empfohlenen Bridge-/Integrations-Strategie gefolgt.

## 4. Strukturpruefung

Geprueft wurden insbesondere:

- `app/`
- `docs/`
- `maintenance_pipelines/`
- `scripts/`
- `.github/`
- Abwesenheit von `webapp/`
- Root-/App-README-Rollen
- `CONFIG_ROOT`

Ergebnis:

- vorhanden und plausibel:
  - `app/`
  - `docs/`
  - `maintenance_pipelines/`
  - `scripts/`
  - `.github/`
- `webapp/`: nicht vorhanden
- Root-README bleibt die Repository-/Workspace-README
- `app/README.md` bleibt die technische App-README
- `app/src/app/runtime_paths.py` verwendet weiterhin:

```text
get_config_root() = get_data_root() / "config"
```

Klassifikation der relevanten Pfade im Integrationsstand:

- `C:\dev\corapan\data\config`: **active**
- `C:\dev\corapan\app\config\blacklab`: **active** fuer versionierte BlackLab-Konfiguration
- `C:\dev\corapan\webapp`: **nicht vorhanden / nicht aktiv**
- repo-lokale Altpfade unter `app/runtime` oder `app/data`: **legacy/dangerous** fuer lokale Runtime-Annahmen

## 5. Dev-Check

### Compose-Check

Geprueft wurde:

```powershell
docker compose -f docker-compose.dev-postgres.yml config
```

Ergebnis:

- die Root-Compose-Datei rendert erfolgreich
- die Dev-Topologie bleibt damit im Integrations-Branch formal konsistent

### Minimaler App-Factory-Check

Der Laufzeitcheck wurde mit den kanonischen Dev-Werten aus `scripts/dev-start.ps1` ausgefuehrt:

- `FLASK_ENV=development`
- `CORAPAN_RUNTIME_ROOT=C:\dev\corapan`
- `CORAPAN_MEDIA_ROOT=C:\dev\corapan\media`
- `PUBLIC_STATS_DIR=C:\dev\corapan\data\public\statistics`
- `POSTGRES_DEV_DATA_DIR=C:\dev\corapan\data\db\restricted\postgres_dev`
- `AUTH_DATABASE_URL=postgresql+psycopg2://corapan_auth:corapan_auth@127.0.0.1:54320/corapan_auth`
- `FLASK_SECRET_KEY=dev-secret-change-me`
- `JWT_SECRET_KEY=dev-jwt-secret-change-me`
- `BLS_BASE_URL=http://localhost:8081/blacklab-server`
- `BLACKLAB_BASE_URL=http://localhost:8081/blacklab-server`
- `BLS_CORPUS=corapan`

Ergebnis von `create_app('development')`:

- erfolgreich
- Auth-DB-Verbindung erfolgreich verifiziert
- keine offensichtlichen Runtime-Fehler im minimalen Startup

Zur Laufzeit wurden bestaetigt:

- `RUNTIME_ROOT = C:\dev\corapan`
- `DATA_ROOT = C:\dev\corapan\data`
- `CONFIG_ROOT = C:\dev\corapan\data\config`
- `MEDIA_ROOT = C:\dev\corapan\media`
- `PUBLIC_STATS_DIR = C:\dev\corapan\data\public\statistics`
- `BLS_BASE_URL = http://localhost:8081/blacklab-server`
- `BLS_CORPUS = corapan`

## 6. Diff-Bewertung

Diff gegen `origin/main` im gestageten Integrationsstand:

- `661 files changed`
- `54259 insertions`
- `2455 deletions`

Wesentliche Beobachtungen:

- die Diff-Form ist fuer einen Root-Lift-Inhaltstransfer nachvollziehbar
- sehr viele Veraenderungen werden als saubere Renames erkannt, insbesondere:
  - Root-Dateien nach `app/`
  - `config/blacklab/... -> app/config/blacklab/...`
  - `infra/... -> app/infra/...`
  - `scripts/... -> app/scripts/...`
  - `src/... -> app/src/...`
  - `static/... -> app/static/...`
  - `templates/... -> app/templates/...`
  - `tests/... -> app/tests/...`

Plausibel neu am Repo-Root sind insbesondere:

- `.github/agents/...`
- `.github/instructions/...`
- `.github/skills/...`
- `.github/workflows/README.md`
- Root-Wrapper und Root-Dokumentation

Bewertung der Loeschungen:

- die grossen Loeschbilder auf `origin/main` entsprechen ueberwiegend der beabsichtigten Verlagerung in den `app/`-Unterbaum
- es wurden in der Stichprobe keine offensichtlichen unerwarteten Massenverluste ausserhalb des Root-Lift-Ziels festgestellt

Rest-Risiko:

- wegen des Umfangs bleibt vor einem spaeteren PR eine CI-Auswertung und eine gezielte Review der Root-Workflows sinnvoll

## 7. Commit

Fuer den Integrationsstand wurde der folgende Commit angelegt:

```text
Integrate root-lift structure: migrate to app/ layout and canonical runtime paths
```

Dieser Commit repraesentiert den kontrollierten Integrationsstand auf `root-lift-integration` als Grundlage fuer einen spaeteren normalen PR nach `main`.

## 8. Go / No-Go fuer PR

### GO

Fuer:

- lokalen Integrations-Branch `root-lift-integration`
- spaetere PR-Vorbereitung auf Basis dieses Branchs
- technische Review der Diff- und Workflow-Aenderungen

### NO-GO

Fuer:

- Push auf `main`
- produktiven Deploy
- Ueberspringen der spaeteren CI- und Review-Phase

Kurzurteil:

### DER INTEGRATIONS-BRANCH IST SAUBER GENUG ALS PR-GRUNDLAGE. DER NAECHSTE SCHRITT IST REVIEW UND CI, NICHT DER DIREKTE MERGE NACH `main`.