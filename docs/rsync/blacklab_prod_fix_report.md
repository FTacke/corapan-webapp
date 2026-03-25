# BlackLab Prod Fix Report

Datum: 2026-03-25

## A. Executive Summary

Die produktive BlackLab/Search-Stoerung war ein Config-Mount-Drift, nicht ein Index- oder Query-Problem.

DEV lief mit einer befuellten Konfiguration unter `/etc/blacklab` und einer funktionierenden Hits-Query. PROD lief mit demselben Image und demselben Index-Mount, aber mit einem leeren `/etc/blacklab`, weil der laufende `corapan-blacklab`-Container und die zugehoerigen Prod-Skripte noch den veralteten Hostpfad `/srv/webapps/corapan/app/config/blacklab` verwendeten. Nach dem Root-Lift liegt die echte versionierte BlackLab-Konfiguration jedoch unter `/srv/webapps/corapan/app/app/config/blacklab`.

Die kleinste saubere Reparatur ist daher:

- produktiven BlackLab-Container mit korrekt gemounteter Config neu starten
- Prod-Skripte auf den echten Checkout-Pfad korrigieren
- Recovery mit echter Hits-Query nachweisen

## B. DEV-vs-PROD Vergleich

### Containerzustand

DEV:

- Container: `blacklab-server-v3`
- Image: `instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7`
- Status: `Up ... (healthy)`
- Cmd: `catalina.sh run`
- Env relevant:
  - `JAVA_OPTS=-Xmx2g -Xms512m`
  - `BLACKLAB_CONFIG_DIR=/etc/blacklab`
- echte Hits-Query gegen `corapan` lieferte ein regulaeres BlackLab-XML-Payload mit `<summary>`

PROD:

- Container: `corapan-blacklab`
- Image: `instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7`
- Status vor Fix: `Up ...`
- Cmd: `catalina.sh run`
- Env relevant vor Fix:
  - `JAVA_TOOL_OPTIONS=-Xmx2g -Xms512m`
  - kein explizites `BLACKLAB_CONFIG_DIR`

### Mounts

| Bereich | DEV | PROD vor Fix | Bewertung |
| --- | --- | --- | --- |
| `/data/index/corapan` | `C:\dev\corapan\data\blacklab\index` | `/srv/webapps/corapan/data/blacklab/index` | aktiv und konsistent |
| `/etc/blacklab` | `C:\dev\corapan\app\config\blacklab` | `/srv/webapps/corapan/app/config/blacklab` | PROD driftet |

### Host-Dateisystem

DEV:

- aktiv: `C:\dev\corapan\app\config\blacklab`
- Dateien:
  - `blacklab-server.yaml`
  - `corapan-json.blf.yaml`
  - `corapan-tsv.blf.yaml`
  - `corapan-wpl.blf.yaml`
  - `json-metadata.blf.yaml`

PROD:

- `/srv/webapps/corapan/app/config/blacklab`: vorhanden, aber leer
- `/srv/webapps/corapan/app/app/config/blacklab`: vorhanden und mit denselben fünf Dateien befuellt
- `/srv/webapps/corapan/config/blacklab`: fehlt
- `/srv/webapps/corapan/data/config/blacklab`: fehlt

### Container-Dateisystem

DEV im laufenden Container:

- `/etc/blacklab` enthaelt die erwarteten fuenf Config-Dateien
- `/data/index/corapan` enthaelt einen gefuellten Index

PROD im laufenden Container vor Fix:

- `/etc/blacklab` war leer
- `/data/index/corapan` war gefuellt

### Compose-/Deploy-Vertrag

Belastbare Quellen:

- DEV canonical compose: `docker-compose.dev-postgres.yml`
- DEV Start-Guard: `app/scripts/dev-start.ps1`
- PROD Web deploy: `app/scripts/deploy_prod.sh`
- PROD BlackLab start: `app/scripts/blacklab/run_bls_prod.sh`

Wesentliche Vertragslage:

- DEV mountet korrekt nach `/etc/blacklab`
- `app/scripts/deploy_prod.sh` beschreibt den root-gelifteten Checkout unter `/srv/webapps/corapan/app` mit Application-Subtree `/srv/webapps/corapan/app/app`
- `run_bls_prod.sh` und `build_blacklab_index_prod.sh` verwendeten trotzdem noch den alten aeusseren Pfad `/srv/webapps/corapan/app/config/blacklab`

## C. Tatsaechlicher PROD-Fehlerzustand

Vor Fix lieferte die produktive Hits-Query:

- `http://127.0.0.1:8081/blacklab-server/corpora/corapan/hits?patt=%5Bword%3D%22casa%22%5D&number=1`
- HTTP `500`

Fehlerinhalt und Logs zeigten:

- `Couldn't find blacklab-server.(json|yaml) in BlackLab config dir /etc/blacklab`

Das ist staerker als generische Readiness, weil:

- der Container lief
- der Index war gemountet
- aber die produktiv relevante Hits-Operation scheiterte unmittelbar an fehlender Config im aktiven Container

## D. Root Cause

Primaerer Root Cause:

- Nach dem Root-Lift der Produktions-Checkout-Struktur blieb die BlackLab-Prod-Logik auf dem veralteten Hostpfad `/srv/webapps/corapan/app/config/blacklab` stehen.
- Die echte versionierte BlackLab-Konfiguration liegt jetzt unter `/srv/webapps/corapan/app/app/config/blacklab`.
- Der laufende Container mountete deshalb einen existierenden, aber leeren Hostordner nach `/etc/blacklab`.

Einordnung zur Verursachung:

- Der Fehler wurde nicht durch den rsync-Refactor erzeugt.
- Es handelt sich um einen bereits vorhandenen Produktionsdrift aus der root-gelifteten Checkout-Struktur, der durch die verschaerfte Hits-Query-Validierung jetzt belastbar sichtbar wurde.

Sekundaere Faktoren:

- `run_bls_prod.sh` kodierte weiterhin den stale Pfad
- `build_blacklab_index_prod.sh` dokumentierte und referenzierte denselben stale Pfad
- produktive Readiness ohne echte Hits-Query haette den Fehler nicht sicher erkannt

Klassifikation:

- Failure class: `config/BLF` und `mount/runtime`
- nicht primaer: Index-Korruption
- nicht primaer: App/CQL-Logik

## E. Konkrete Reparatur

Durchgefuehrte Reparatur in PROD:

- `corapan-blacklab` mit identischem Image, identischem Index-Mount und identischem Port/Netzwerk neu gestartet
- Config-Mount umgestellt von:
  - `/srv/webapps/corapan/app/config/blacklab:/etc/blacklab:ro`
- auf:
  - `/srv/webapps/corapan/app/app/config/blacklab:/etc/blacklab:ro`
- zusaetzlich `BLACKLAB_CONFIG_DIR=/etc/blacklab` explizit gesetzt
- Live-Reparatur wurde direkt auf dem Produktionshost ausgefuehrt, ohne Web-Deploy oder Sync-Strecke umzubauen

Dauerhafte Repo-Reparatur:

- `app/scripts/blacklab/run_bls_prod.sh`
- `app/scripts/blacklab/build_blacklab_index_prod.sh`

wurden auf den realen Produktions-Checkout-Pfad angepasst.

## F. Nachweis nach Fix

Belegt nach dem Live-Fix:

- BlackLab-Container laeuft:
  - `corapan-blacklab   instituutnederlandsetaal/blacklab   Up ...   0.0.0.0:8081->8080/tcp`
- aktive PROD-Mounts:
  - `/srv/webapps/corapan/data/blacklab/index -> /data/index/corapan`
  - `/srv/webapps/corapan/app/app/config/blacklab -> /etc/blacklab`
- aktive Env im Container:
  - `JAVA_TOOL_OPTIONS=-Xmx2g -Xms512m`
  - `BLACKLAB_CONFIG_DIR=/etc/blacklab`
- `/etc/blacklab` ist im laufenden PROD-Container wieder befuellt mit:
  - `blacklab-server.yaml`
  - `corapan-json.blf.yaml`
  - `corapan-tsv.blf.yaml`
  - `corapan-wpl.blf.yaml`
  - `json-metadata.blf.yaml`
- echte Hits-Query gegen `corapan` funktioniert wieder:
  - Ergebnisnachweis: `BLACKLAB_HITS_OK`
  - Response enthaelt wieder BlackLab-Payload mit `<summary>` statt HTTP 500
- Logs zeigen keine offensichtlichen Folgefehler, sondern regulaeren Start und Query-Verarbeitung:
  - `Index found: corapan (/data/index/corapan)`
  - `GET /corpora/corapan/hits?...`
  - `Total search time is: ... ms`

Damit ist Search in PROD wieder funktionsfaehig.

## G. Nebenbefund Data-Statistik-Pfad

Der echte Data-Lauf zeigte den Fehler:

- `Es wurde kein Positionsparameter gefunden, der das Argument ".../corpus_stats.json .../viz_*.png 2>/dev/null || true'" akzeptiert.`

Kurzdiagnose:

- Root Cause ist ein PowerShell-Quoting-Fehler im `chmod`-Nachgangspfad von `Sync-StatisticsFiles`
- der Befehl wurde mit Bash-Quoting gebaut, aber mit PowerShell-String-Escaping (`\"`) zusammengesetzt, was den Remote-Command inkonsistent machte

Mitbehebung:

- kleiner, risikoarmer Fix in `app/scripts/deploy_sync/sync_data.ps1`
- der Remote-`chmod`-Aufruf wird jetzt ueber einen sauberen interpolierten Here-String aufgebaut

## H. Auswirkungen auf Deploy-/Config-Vertrag

Belastbarer Vertrag nach diesem Befund:

- DEV config mount: `CORAPAN/app/config/blacklab -> /etc/blacklab`
- PROD config mount bei root-geliftetem Checkout: `/srv/webapps/corapan/app/app/config/blacklab -> /etc/blacklab`
- PROD stale/dangerous path: `/srv/webapps/corapan/app/config/blacklab`

Wichtig:

- funktionierende DEV-Search entlastet nicht von PROD-Mount-Pruefung
- identisches Image reicht nicht; Config-Mount und Container-Inhalt muessen live verglichen werden
- BlackLab-Validierung bleibt hits-query-basiert, nicht nur root-ready

## I. Skill-/Governance-Folgerungen

Neu verankert:

- BlackLab ist separat produktionskritisch
- wenn DEV funktioniert und PROD scheitert, ist ein Live-DEV-vs-PROD-Abgleich von Image, Env, Cmd, Mounts und `/etc/blacklab` Pflicht
- die produktive Config-Lage fuer den aktuellen Root-Lift ist explizit dokumentiert
- `/srv/webapps/corapan/app/config/blacklab` ist als stale/dangerous klassifiziert, bis er spaeter bewusst aufgeraeumt wird

## J. Offene Restpunkte

- pruefen, ob es noch weitere operative Hilfsskripte oder Dokumente mit dem stale Prod-BlackLab-Pfad gibt
- den Data-Statistik-Fix separat praktisch bestaetigen, falls ein weiterer Data-Lauf ohnehin ansteht
- den leeren stale Hostpfad nicht jetzt implizit loeschen; erst nach bewusstem Legacy-Abbau