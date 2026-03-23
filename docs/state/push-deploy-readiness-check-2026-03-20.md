# Push/Deploy Readiness Check 2026-03-20

Datum: 2026-03-20
Pruefmodus: read-only Freigabepruefung fuer das echte Git-/Deploy-Modell

## 1. Verifiziertes Git-/Deploy-Modell

Aktive Quellen:

- Git-Root: `C:\dev\corapan\webapp`
- Push-Trigger laut Repo-Workflow: `.github/workflows/deploy.yml`
- Deploy-Skript: `scripts/deploy_prod.sh`
- Produktionsziel: `/srv/webapps/corapan/app`
- Produktions-Compose: `infra/docker-compose.prod.yml`

Nachweise:

- `git rev-parse --show-toplevel` liefert `C:/dev/corapan/webapp`
- `scripts/deploy_prod.sh` setzt:
  - `BASE_DIR=/srv/webapps/corapan`
  - `APP_DIR=${BASE_DIR}/app`
  - `COMPOSE_FILE=${APP_DIR}/infra/docker-compose.prod.yml`
- `HEAD:.github/workflows/deploy.yml` fuehrt bei `push` auf `main` aus:
  - `cd /srv/webapps/corapan/app`
  - `git reset --hard "${GITHUB_SHA}"`
  - `bash scripts/deploy_prod.sh`

Bewertung:

- `webapp/` ist weiterhin das echte versionierte Repo.
- Push, CI und Auto-Deploy arbeiten im bestehenden Modell nur mit Dateien innerhalb von `webapp/`.
- Root-Dateien unter `C:\dev\corapan\...` sind in diesem Modell nicht push-wirksam.

## 2. Gepruefter Push-Stand in `webapp/`

Geprueft wurden:

- `git status --short`
- `git diff --stat`
- relevante Inhaltsdifferenzen fuer Deploy, Runtime und BlackLab

Kritische push-relevante Aenderungen innerhalb von `webapp/`:

### Blocker

- geloeschte Repo-Workflows:
  - `.github/workflows/deploy.yml`
  - `.github/workflows/ci.yml`
  - `.github/workflows/md3-lint.yml`
- geloeschte aktive BlackLab-Konfiguration im Repo:
  - `config/blacklab/blacklab-server.yaml`
  - `config/blacklab/corapan-json.blf.yaml`
  - `config/blacklab/corapan-tsv.blf.yaml`
  - `config/blacklab/corapan-wpl.blf.yaml`
  - `config/blacklab/json-metadata.blf.yaml`
- geaenderte Runtime-Pfadlogik:
  - `src/app/runtime_paths.py`
    - `get_config_root()` zeigt nicht mehr auf `CORAPAN_RUNTIME_ROOT/config`, sondern auf ein Sibling-Verzeichnis neben dem Repo

### Lokal/dev-orientiert und fuer Prod-Auto-Deploy nicht primaer

- `docker-compose.dev-postgres.yml`
- `infra/docker-compose.dev.yml`
- `scripts/dev-start.ps1`
- `scripts/dev-setup.ps1`
- `scripts/bootstrap.ps1`
- `scripts/blacklab/build_blacklab_index.ps1`
- `scripts/blacklab/build_blacklab_index.sh`
- `scripts/blacklab/start_blacklab_docker_v3.ps1`
- `scripts/blacklab/run_export.py`
- `scripts/blacklab/docmeta_to_metadata_dir.py`
- `scripts/blacklab/migrate_legacy_blacklab_dev_layout.ps1`
- `scripts/debug/build_index_test.ps1`

Diese Dateien bilden lokale Dev- und Maintenance-Workflows ab. Sie koennen Sibling-Pfade unter `C:\dev\corapan\...` verwenden, ohne den Produktions-Deploy direkt zu steuern.

## 3. Root-Aenderungen ausserhalb von `webapp/`

### `C:\dev\corapan\.github`

Klassifikation: `DANGEROUS` als Ersatz, `LOCAL_ONLY` als Workspace-Hilfe

- enthaelt Ersatz fuer Repo-Workflows und Agent-Instruktionen
- liegt ausserhalb des echten Git-Roots
- wird beim Push aus `webapp/.git` nicht mit auf den Server gebracht
- kann das geloeschte `webapp/.github` im echten Deploy-Modell nicht ersetzen

### `C:\dev\corapan\.venv`

Klassifikation: `LOCAL_ONLY`

- lokale Dev-Python-Umgebung
- nicht Teil des Server-Deploys
- unkritisch fuer Push, solange `webapp/` keine Serverlogik voraussetzt, die diese lokale venv braucht

### `C:\dev\corapan\config`

Klassifikation: `DANGEROUS` als Ersatz, `LOCAL_ONLY` fuer lokalen Dev-Betrieb

- lokal erfolgreich als Sibling-Konfiguration benutzt
- wird beim Push nicht mitdeployt
- kann die innerhalb von `webapp/` geloeschten `config/blacklab`-Dateien fuer den Server nicht ersetzen

### `C:\dev\corapan\data`

Klassifikation: `LOCAL_ONLY`

- lokaler Dev-Runtime-Datenbaum
- nicht Git-transportiert
- fuer Prod unkritisch, solange keine Repo-Datei voraussetzt, dass Server-Deploy Daten aus dem Root-Workspace nachliefert

### `C:\dev\corapan\scripts`

Klassifikation: `LOCAL_ONLY`

- duerre Wrapper auf `webapp/scripts/...`
- keine aktive Produktionsquelle
- werden nicht deployt und muessen es im bestehenden Modell auch nicht

### Root-Compose-Dateien

Klassifikation: `LOCAL_ONLY`

- lokales Dev-Compose unter `C:\dev\corapan\docker-compose.dev-postgres.yml`
- keine Produktionsquelle
- wird beim bestehenden Deploy nicht verwendet

## 4. Serverrelevante Pfadannahmen in `webapp/`

### `src/app/runtime_paths.py`

Bewertung: `BLOCKER`

- lokal liefert `get_config_root()` jetzt `C:\dev\corapan\config`
- im Produktions-Container mit `WORKDIR /app` wuerde dieselbe Logik auf ein Sibling neben `/app` zeigen, nicht auf den in `infra/docker-compose.prod.yml` gemounteten Pfad `/app/config`
- damit ist die neue Resolver-Logik nicht belastbar kompatibel mit dem bestehenden Deploy-Modell `webapp -> /srv/webapps/corapan/app`

### `config/blacklab/*`

Bewertung: `BLOCKER`

- das bestehende Repo-/Server-Modell behandelt `app/config/blacklab` weiter als produktionsrelevante Konfigurationsquelle
- `scripts/blacklab/run_bls_prod.sh` erwartet explizit `/srv/webapps/corapan/app/config/blacklab`
- ein Push mit den aktuellen Loeschungen wuerde diese Konfiguration im App-Checkout entfernen

### `.github/workflows/deploy.yml`

Bewertung: `BLOCKER`

- der bestehende Auto-Deploy ist in genau dieser Repo-Datei kodiert
- die Root-Ersatzdatei ausserhalb von `webapp/` ist fuer GitHub nicht relevant, solange `webapp/` das echte Repo bleibt
- ein Push mit geloeschter Repo-Workflow-Datei ist nicht kompatibel mit dem bestaetigten Auto-Deploy-Modell

### `scripts/dev-start.ps1`, `scripts/dev-setup.ps1`, `docker-compose.dev-postgres.yml`, `infra/docker-compose.dev.yml`

Bewertung: `LOCAL_DEV_ONLY`, kein unmittelbarer Prod-Blocker

- diese Dateien setzen bewusst den lokalen Workspace `C:\dev\corapan` als Dev-Basis voraus
- sie steuern den bestaetigten Produktions-Deploy nicht
- sie sind fuer Push nur dann problematisch, wenn sie faelschlich als Produktionsquelle missverstanden werden

## 5. Konkretes Auto-Deploy-Risiko bei aktuellem Push

### Risikoklasse 1

`JA` - lokal funktioniert ein Teil des bereinigten Dev-Zustands nur wegen Root-Dateien ausserhalb von `webapp/`.

Kritisch betroffen:

- Root-`.github` als nicht pushbarer Ersatz fuer `webapp/.github`
- Root-`config/blacklab` als nicht pushbarer Ersatz fuer `webapp/config/blacklab`

### Risikoklasse 2

`JA` - deployte Fassung erwartet Pfade, die im bestehenden Server-Modell anders sind.

Kritisch betroffen:

- `src/app/runtime_paths.py` verlagert `CONFIG_ROOT` auf ein Repo-Sibling statt auf die Runtime-/Container-Konfiguration

### Risikoklasse 3

`JA` - Deploy kann funktionierende Serverpfade mit unvollstaendiger Logik ueberschreiben.

Kritisch betroffen:

- `scripts/deploy_prod.sh` fuehrt auf dem Server `git reset --hard` im App-Checkout aus
- damit wuerden die aktuell in `webapp/` zur Loeschung markierten `config/blacklab/*`-Dateien aus `/srv/webapps/corapan/app/config/blacklab` entfernt

### Risikoklasse 4

`TEILWEISE JA`, aber nur fuer unkritische lokale Verbesserungen

- Root-`.venv`
- Root-`data`
- Root-`scripts`
- Root-Dev-Compose

Diese lokalen Hilfen muessen nicht mit auf den Server. Sie stoeren den Deploy nicht, solange keine produktionsrelevante Repo-Datei auf sie angewiesen gemacht wird.

## 6. Entscheidung

## PUSH NICHT FREIGEGEBEN

Begruendung:

1. das echte Repo `webapp/.git` enthaelt die aktive Deploy-Workflow-Datei, und diese ist zur Loeschung vorgemerkt
2. das echte Repo enthaelt die produktionsrelevante BlackLab-Konfiguration unter `config/blacklab`, und diese ist zur Loeschung vorgemerkt
3. die geaenderte App-Laufzeitlogik in `src/app/runtime_paths.py` ist nicht belastbar kompatibel mit dem bestaetigten Deploy-Modell `webapp -> /srv/webapps/corapan/app`

## 7. Exakte Restpunkte vor einem Push

1. `webapp/.github/workflows/deploy.yml` im echten Repo erhalten oder innerhalb von `webapp/` korrekt ersetzen; Root-`.github` reicht nicht
2. `webapp/config/blacklab/*` im echten Repo erhalten oder innerhalb von `webapp/` korrekt spiegeln; Root-`config/blacklab` reicht nicht
3. `src/app/runtime_paths.py` so korrigieren, dass `CONFIG_ROOT` im bestaetigten Deploy-Modell weiterhin auf die produktionsseitig gemountete Konfiguration zeigt
4. erst danach erneut `git status`, `git diff --stat` und die drei Blockerpfade pruefen
