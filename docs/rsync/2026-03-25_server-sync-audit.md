# Server-Sync Audit 2026-03-25

## A. Executive Summary

Dieser Audit betrifft ausschliesslich den Bereich serverseitiger Dateisynchronisation, SSH/rsync-Uploads, grosse Runtime-Bestaende, BlackLab-Index-Publishing und die zugehoerigen Deploy-Helfer.

Kurzbefund:

- Der normale Code-Deploy ist nach dem Root-Lift fuer den Runner-Pfad konsistent: `.github/workflows/deploy.yml` ruft `bash app/scripts/deploy_prod.sh` aus `/srv/webapps/corapan/app` auf, und `app/scripts/deploy_prod.sh` modelliert `CHECKOUT_DIR=/srv/webapps/corapan/app` plus `APP_DIR=/srv/webapps/corapan/app/app` korrekt.
- Die separate Sync-Strecke fuer Daten, Medien und BlackLab lebt nicht in GitHub Actions, sondern in lokalen/operativen PowerShell-Skripten unter `app/scripts/deploy_sync/` und `maintenance_pipelines/_2_deploy/`.
- Diese Sync-Strecke hat mehrere strukturelle und sicherheitsrelevante Probleme: harte SSH-Hardcodings, flaechendeckend deaktiviertes Host-Key-Checking, inkonsistente SSH-Aufrufpfade, ein BlackLab-Publish-Upload, der den eigenen SSH-Helper im kritischen Datenpfad umgeht, und ein generelles `rsync --delete` ohne Leersourcen-Schutz.
- Es gibt mindestens einen echten Implementierungsfehler: `maintenance_pipelines/_2_deploy/deploy_data.ps1` deployed Statistik-Dateien doppelt, weil `app/scripts/deploy_sync/sync_data.ps1` sie bereits selbst deployed und der Orchestrator danach `Sync-StatisticsFiles` noch einmal direkt aufruft.
- Die Dokumentation ist in diesem Bereich deutlich inkonsistent. Besonders `docs/operations/runtime_statistics_deploy.md`, `maintenance_pipelines/_2_deploy/README_STATISTICS_DEPLOY.md`, `docs/local_runtime_layout.md` und Teile aelterer Maintenance-Doku beschreiben teils alte Pfade, alte BlackLab-Namen oder nicht mehr existierende/nie mehr erlaubte Optionen.
- Es fehlen eine knappe kanonische README fuer die gesamte rsync-/server-sync-Strecke und ein eindeutiger, dokumentierter Sicherheitsvertrag fuer `--delete`, Dry-Run, SSH host verification und Notfall-Restore.

Unsicherheit:

- Ich habe keine Live-Laeufe auf den Zielservern ausgefuehrt. Aussagen zu "aktiv benutzt" vs. "nur noch im Repo vorhanden" sind daher als Klassifikation nach Code/Doku/Referenzen zu verstehen, nicht als Live-Beobachtung.

## B. Gefundene relevante Dateien

### Aktive oder wahrscheinlich aktive Artefakte

| Dateipfad | Klassifikation | Zweck | Wann / wodurch aufgerufen | Quell- und Zielpfade | Env / Voraussetzungen | Logging | Dry-Run | Delete / Prune |
|---|---|---|---|---|---|---|---|---|
| `.github/workflows/deploy.yml` | aktiv | normaler Produktionsdeploy per self-hosted runner, kein rsync | bei Push auf `main` oder `workflow_dispatch` | `cd /srv/webapps/corapan/app`; `bash app/scripts/deploy_prod.sh` | self-hosted runner, Docker, Checkout unter `/srv/webapps/corapan/app` | ja, Workflow-Logs | nein | kein rsync-delete |
| `app/scripts/deploy_prod.sh` | aktiv | Code-Deploy und Compose-Restart auf dem Server | durch `.github/workflows/deploy.yml` | Host: `/srv/webapps/corapan/{data,media,logs,config}`; App-Subtree: `/srv/webapps/corapan/app/app` | `passwords.env`, Docker Compose V2, Health-URL | ja, strukturierte `log_info`-Ausgaben | nein | kein rsync-delete |
| `app/infra/docker-compose.prod.yml` | aktiv | kanonischer Produktions-Stack | durch `app/scripts/deploy_prod.sh` | Host mounts: `/srv/webapps/corapan/data -> /app/data`, `/srv/webapps/corapan/media -> /app/media`, `/srv/webapps/corapan/logs -> /app/logs`, `/srv/webapps/corapan/data/config -> /app/config` | `POSTGRES_PASSWORD`, `FLASK_SECRET_KEY`, `JWT_SECRET_KEY`, `BLS_*`, Runtime-Variablen | Docker/Compose-Logs | n/a | n/a |
| `app/passwords.env.template` | aktiv als Template | dokumentiert benoetigte Prod-Variablen | manuell vom Operator | Container-Runtime, keine Transferpfade | `AUTH_DATABASE_URL`, `BLS_BASE_URL`, `BLS_CORPUS`, `CORAPAN_RUNTIME_ROOT`, `CORAPAN_MEDIA_ROOT` etc. | n/a | n/a | n/a |
| `app/scripts/deploy_sync/_lib/ssh.ps1` | aktiv | SSH/SCP-Konfig und Helper | von `publish_blacklab_index.ps1`, indirekt von `sync_core.ps1` geladen | Default-Remote: `/srv/webapps/corapan`, `/srv/webapps/corapan/data`, `/srv/webapps/corapan/media`, `/srv/webapps/corapan/data/blacklab` | `ssh.exe`, Key-Datei `$env:USERPROFILE\.ssh\marele`; harter 8.3-Keypfad `C:\Users\FELIXT~1\.ssh\marele` | ja, Host-Ausgaben und Dry-Run-Ausgaben | ja | kein rsync-delete |
| `app/scripts/deploy_sync/sync_core.ps1` | aktiv | gemeinsame Transferlogik fuer Data/Media, rsync/tar-Upload, Manifeste, Ownership | von `sync_data.ps1` und `sync_media.ps1` | lokal: `CORAPAN_RUNTIME_ROOT\{data,media}`; remote: `/srv/webapps/corapan/{data,media}` | `CORAPAN_RUNTIME_ROOT`, cwRsync oder `tar`/`python`, SSH-Key | ja, aber begrenzt; nicht dateigenau | kein offizieller globaler Dry-Run, nur Aufrufer | `rsync --delete` fuer Verzeichnis-Syncs |
| `app/scripts/deploy_sync/sync_data.ps1` | aktiv | Sync von `data/db/public`, `data/public/metadata`, `data/exports`, Stats-DBs und Statistik-Dateien | direkt oder via `maintenance_pipelines/_2_deploy/deploy_data.ps1` | lokal: `$env:CORAPAN_RUNTIME_ROOT\data`; remote: `/srv/webapps/corapan/data`; stats nach `/srv/webapps/corapan/data/public/statistics` | `CORAPAN_RUNTIME_ROOT`; fuer Stats optional `PUBLIC_STATS_DIR`; rsync/ssh | ja, aber Stats-rsync-Output wird unterdrueckt | ja, fuer Hauptlauf und Stats | Verzeichnis-Sync ueber `sync_core.ps1` mit `--delete`; Stats explizit ohne delete |
| `app/scripts/deploy_sync/sync_media.ps1` | aktiv | Sync von `media/transcripts`, `media/mp3-full`, `media/mp3-split` | direkt oder via `maintenance_pipelines/_2_deploy/deploy_media.ps1` | lokal: `$env:CORAPAN_RUNTIME_ROOT\media`; remote: `/srv/webapps/corapan/media` | `CORAPAN_RUNTIME_ROOT`; rsync/ssh | ja, aber keine eindeutige Aenderungsliste | ja | Verzeichnis-Sync ueber `sync_core.ps1` mit `--delete` |
| `app/scripts/deploy_sync/publish_blacklab_index.ps1` | aktiv | Upload eines lokal gebauten BlackLab-Index nach `/srv/webapps/corapan/data/blacklab`, Remote-Validierung und atomischer Swap | direkt oder via `maintenance_pipelines/_2_deploy/publish_blacklab.ps1` | lokal: `data/blacklab/quarantine/index.build`; remote staging: `/srv/webapps/corapan/data/blacklab/quarantine/index.upload_<timestamp>`; aktiv: `/srv/webapps/corapan/data/blacklab/index`; Backup: `/srv/webapps/corapan/data/blacklab/backups/index_<timestamp>` | `ssh`, `tar` oder `scp`, Docker und curl auf dem Zielhost; optional `KeepBackups` | ja, gute Schrittlogs | ja | kein rsync-delete; Backup-Retention separat, standardmaessig report-only |
| `app/scripts/blacklab/retain_blacklab_backups_prod.sh` | aktiv als Hilfsskript | Backup-Retention fuer BlackLab-Backups | durch `publish_blacklab_index.ps1` Step 8 | Backup-Root `/srv/webapps/corapan/data/blacklab/backups` | `BLACKLAB_ROOT`, `BLACKLAB_KEEP_BACKUPS`, optional `BLACKLAB_RETENTION_DELETE`, `BLACKLAB_RETENTION_OLDER_THAN_DAYS` | ja, Logfile unter `backups/logs/` | kein Dry-Run-Flag, aber Default report-only | loescht nur bei `BLACKLAB_RETENTION_DELETE=1` |
| `maintenance_pipelines/_2_deploy/deploy_data.ps1` | aktiv/wahrscheinlich aktiv | user-facing Orchestrator fuer Data-Sync | manuell vom Operator | ruft `app/scripts/deploy_sync/sync_data.ps1` auf; deployed danach Stats erneut nach hartem `/srv/webapps/corapan` | `AppRepoPath`, `Force`, `SkipStatistics` | ja, `_logs/deploy_data_<timestamp>.log` | kein pass-through zu underlying `-DryRun` | kein eigenes delete, aber underlying sync nutzt `--delete` |
| `maintenance_pipelines/_2_deploy/deploy_media.ps1` | aktiv/wahrscheinlich aktiv | user-facing Orchestrator fuer Media-Sync | manuell vom Operator | ruft `app/scripts/deploy_sync/sync_media.ps1` auf | `AppRepoPath`, `Force`, `ForceMP3` | ja, `_logs/deploy_media_<timestamp>.log` | kein pass-through zu underlying `-DryRun` | kein eigenes delete, aber underlying sync nutzt `--delete` |
| `maintenance_pipelines/_2_deploy/publish_blacklab.ps1` | aktiv/wahrscheinlich aktiv | Orchestrator fuer Export -> Build -> Publish von BlackLab | manuell vom Operator | lokal: Export und Build im Workspace/App-Repo; remote: `/srv/webapps/corapan/app`, `/srv/webapps/corapan/data/blacklab` | Python, App-Repo, optionale Flags `-DryRun`, `-KeepBackups` | ja, Transcript-Log | ja | kein delete, ausser optional serverseitige Retention |
| `app/scripts/pre_deploy_check.sh` | sekundar / aktiv als Helper | lokaler Smoke-Test per `app/infra/docker-compose.dev.yml` | manuell | `COMPOSE_FILE="infra/docker-compose.dev.yml"` | Docker Compose, lokale App-Root-Ausfuehrung | ja | Quick-Modus, aber kein Dry-Run | `docker compose down --volumes` im Cleanup |
| `app/scripts/pre_deploy_check.ps1` | sekundar / aktiv als Helper | dito fuer PowerShell | manuell | Default `ComposeFile = "infra/docker-compose.dev.yml"` | Docker Compose, lokale App-Root-Ausfuehrung | ja | Quick-Modus, aber kein Dry-Run | `docker compose down --volumes` im Cleanup |
| `docs/operations/runtime_statistics_deploy.md` | aktiv, aber inkonsistent | Doku fuer Statistik-Deployment | manuell gelesen | beschreibt `/srv/webapps/corapan/data/public/statistics/` | nennt SSH-Key, Host und cwRsync | n/a | beschreibt keinen echten Orchestrator-Dry-Run | beschreibt bewusst kein delete |
| `maintenance_pipelines/_2_deploy/README.md` | aktiv | Doku fuer Orchestratoren | manuell gelesen | beschreibt `maintenance_pipelines/_2_deploy/*` -> `app/scripts/deploy_sync/*` | keine Secrets, aber Verweise auf Sync-Layer | n/a | sagt fuer data/media kein Dry-Run | erwaehnt Delta-Sync, nicht klar genug zu `--delete` |

### Wahrscheinlich veraltete, tote oder nur historisch relevante Artefakte

| Dateipfad | Klassifikation | Befund |
|---|---|---|
| `app/scripts/deploy_sync/legacy/20260116_211115/deploy_full_prod.ps1` | tot / legacy | verwendet altes Deploy-Kommando `cd /srv/webapps/corapan/app && bash scripts/deploy_prod.sh --rebuild-index --skip-git`; das ist nach Root-Lift falsch und durch aktiven Workflow ersetzt |
| `app/scripts/deploy_sync/legacy/20260116_211115/update_data_media.ps1` | tot / legacy | beschreibt alte Inhalte wie `blacklab_export` und kombinierten Maintenance-Runner; nicht mehr kanonisch |
| `app/scripts/deploy_sync/legacy/20260116_211115/PUBLISH_BLACKLAB_INDEX.md` | tot / legacy | beschreibt alte Pfade `data/blacklab_index` statt `data/blacklab/index` |
| `app/scripts/backup.sh` | wahrscheinlich veraltet / potentiell gefaehrlich | benutzt `~/corapan/{data,media,backups}` statt `/srv/webapps/corapan/...`, kein Root-Lift-/Runtime-Contract, kein Dry-Run |
| `docs/local_runtime_layout.md` | grossenteils veraltet / gefaehrlich als Referenz | beschreibt alte Namen `data/blacklab_export`, `data/blacklab_index`, `corapan-webapp/` und alte Fallback-Modelle |
| `maintenance_pipelines/README.md` | teils veraltet | beschreibt alte Pipeline-Outputs wie `static/img/statistics/` fuer Schritt 05; passt nicht mehr zur Runtime-Statistik-Story |
| `maintenance_pipelines/_1_metadata/README.md` | teils veraltet | spricht von `data/metadata/latest/`, waehrend Runtime und Sync `data/public/metadata/latest/` verwenden |

## C. Konkrete Risiken / Fehler

### 1. BlackLab-Publish umgeht im eigentlichen Upload den eigenen SSH-Helper

Betroffene Datei:

- `app/scripts/deploy_sync/publish_blacklab_index.ps1`

Konkrete Zeilen / Verhalten:

- Der SSH-Helper wird fuer Connectivity-Pruefung benutzt.
- Der eigentliche tar-Upload baut aber ein nacktes Kommando: `tar -cf - -C "$localNew" . | ssh $sshTarget "$remoteCmd"`.

Risiko:

- Der Datenpfad verwendet nicht dieselben SSH-Parameter wie `_lib/ssh.ps1`.
- Kein explizites `-i <key>`.
- Kein explizites `StrictHostKeyChecking`.
- Kein konsistentes `ssh.exe`-Binary.
- Verhalten haengt von lokaler Nutzerkonfiguration und `ssh` in `PATH` ab.

Bewertung:

- Hoch. Das ist genau im kritischen Upload-Schritt inkonsistent und kann auf anderen Operator-Maschinen oder neuen Workstations brechen oder auf das falsche SSH-Setup fallen.

### 2. SSH Host-Key-Pruefung ist praktisch ueberall deaktiviert

Betroffene Dateien:

- `app/scripts/deploy_sync/_lib/ssh.ps1`
- `app/scripts/deploy_sync/sync_core.ps1`
- `app/scripts/deploy_sync/sync_data.ps1`

Konkrete Shell-Zeilen / Muster:

- `-o StrictHostKeyChecking=no`
- in `_lib/ssh.ps1` fuer `ssh` und `scp`
- in `sync_core.ps1` fuer rsync-SSH und direkte SSH-Aufrufe
- in `sync_data.ps1` fuer Statistik-rsync

Risiko:

- Keine Host-Pinning- oder `known_hosts`-Pruefung.
- Erhoehtes MITM-Risiko.
- Der Audit findet keine kanonische Behandlung von `UserKnownHostsFile`, `known_hosts` oder Fingerprint-Pinning.

Bewertung:

- Hoch. Fuer Produktionsdaten- und Medien-Sync ueber Root-SSH ist das unnoetig unsicher.

### 3. Allgemeines `rsync --delete` ohne Leersource-Schutz

Betroffene Datei:

- `app/scripts/deploy_sync/sync_core.ps1`

Konkrete Zeile / Verhalten:

- `Sync-DirectoryWithRsync` baut standardmaessig `rsync -avz --partial --progress --delete ...`.

Risiko:

- Wenn eine lokale Quelle existiert, aber versehentlich leer ist, kann der Lauf das Remote-Ziel leeren.
- Es gibt keinen Schutz wie:
  - Mindestdateizahl
  - Sentinel-Datei
  - explizite Bestaetigung fuer delete
  - `--dry-run` Pflicht vor delete-Laeufen

Betroffene Syncs:

- `data/db/public`
- `data/public/metadata`
- `data/exports`
- `media/transcripts`
- `media/mp3-full`
- `media/mp3-split`

Bewertung:

- Hoch. Fuer grosse Bestandsdaten ist `--delete` ohne Empty-Source-Guard der groesste operative Risikofaktor im Data-/Media-Sync.

### 4. `deploy_data.ps1` deployt Statistik-Dateien doppelt

Betroffene Dateien:

- `app/scripts/deploy_sync/sync_data.ps1`
- `maintenance_pipelines/_2_deploy/deploy_data.ps1`

Konkretes Verhalten:

- `sync_data.ps1` ruft am Ende selbst `Sync-StatisticsFiles` auf.
- `deploy_data.ps1` ruft nach dem erfolgreichen `sync_data.ps1` dieselbe Funktion noch einmal direkt auf.

Risiko:

- doppelte Uebertragung derselben Statistik-Dateien
- uneindeutige Logs
- mehr Laufzeit und mehr SSH/rsync-Rauschen
- zweite Ausfuehrung nutzt hart kodiert `"/srv/webapps/corapan"` statt `Get-RemotePaths()`

Bewertung:

- Mittel bis hoch. Kein Datenverlust, aber echter Implementierungsfehler und Root-of-truth-Bruch.

### 5. BlackLab-Validierung prueft nur Corpora-Endpoints, keine echte Hits-Query

Betroffene Datei:

- `app/scripts/deploy_sync/publish_blacklab_index.ps1`

Konkretes Verhalten:

- Step 5 prueft `http://127.0.0.1:<port>/blacklab-server/corpora/?outputformat=json`.
- Step 7 prueft erneut nur den Corpora-Endpoint auf dem Produktiv-Port.

Risiko:

- Das verletzt die im Repo selbst festgelegten BlackLab-Sicherheitsregeln.
- Ein Index kann auf Root-/Corpora-Ebene antworten, aber bei realen Hits fehlschlagen.

Bewertung:

- Hoch. Fuer den Publish-Gate fehlt genau der geforderte Nachweis eines realen Suchpfads.

### 6. SSH-Konfiguration ist workstation-spezifisch und nicht minimal

Betroffene Datei:

- `app/scripts/deploy_sync/_lib/ssh.ps1`

Konkrete Hardcodings:

- `Hostname = "marele.online.uni-marburg.de"`
- `User = "root"`
- `SSHKeyPath = "$env:USERPROFILE\.ssh\marele"`
- `SSHKeyPathShort = "C:\Users\FELIXT~1\.ssh\marele"`

Risiko:

- Harte Bindung an einen konkreten Windows-Benutzernamen / 8.3-Pfad.
- Default-Nutzer ist `root`.
- Kein Secrets-/Config-Layer fuer andere Operatoren.
- Die README behauptet "single source of truth", praktisch existieren aber mehrere SSH-Aufrufpfade.

Bewertung:

- Hoch. Portabilitaet und Sicherheit sind beides schwach.

### 7. `_lib/ssh.ps1` ist nicht wirklich die einzige Wahrheit, weil `sync_core.ps1` SSH neu implementiert

Betroffene Dateien:

- `app/scripts/deploy_sync/_lib/ssh.ps1`
- `app/scripts/deploy_sync/sync_core.ps1`

Konkretes Problem:

- `sync_core.ps1` sourct `_lib/ssh.ps1`, definiert spaeter aber erneut `Invoke-SSHCommand` und baut eigene rsync-SSH-Kommandos.

Risiko:

- Doppelte Logik fuer SSH.
- Docs sagen "single source of truth", Code ist es nicht.
- Aenderungen an `_lib/ssh.ps1` greifen nicht automatisch ueberall.

Bewertung:

- Mittel. Architekturproblem mit realen Folgefehlern.

### 8. Observability der Syncs ist fuer echte Dateiaenderungen zu schwach

Betroffene Dateien:

- `app/scripts/deploy_sync/sync_core.ps1`
- `app/scripts/deploy_sync/sync_data.ps1`
- `app/scripts/deploy_sync/sync_media.ps1`
- `maintenance_pipelines/_2_deploy/deploy_data.ps1`
- `maintenance_pipelines/_2_deploy/deploy_media.ps1`

Konkretes Verhalten:

- Nicht-verbose rsync-Output wird intern geparst, aber nicht als belastbare Aenderungsliste protokolliert.
- Statistik-rsync laeuft mit `| Out-Null` und zeigt keine uebertragenen Dateinamen.
- Nach einem "erfolgreichen" Lauf ist nur begrenzt sichtbar:
  - was tatsaechlich neu war
  - was geloescht wurde
  - ob gar nichts geaendert wurde

Bewertung:

- Mittel. Fuer grosse Bestaende und Incident-Analyse ist das zu schwach.

### 9. User-facing Doku widerspricht dem Ist-Zustand mehrfach

Beispiele:

- `maintenance_pipelines/_2_deploy/deploy_data.ps1` schreibt `data/metadata/`, der Code synced `data/public/metadata`.
- `docs/operations/runtime_statistics_deploy.md` und `maintenance_pipelines/_2_deploy/README_STATISTICS_DEPLOY.md` nennen `blacklab_export` im Data-Sync, obwohl `sync_data.ps1` BlackLab explizit ausschliesst.
- `README_STATISTICS_DEPLOY.md` dokumentiert Notfall-Flags `-IncludeCounters`, `-IncludeAuthDb`, `-IUnderstandThisWillOverwriteProductionState`; der Orchestrator bietet diese Flags nicht, und `sync_data.ps1` blockiert `IncludeAuthDb` hart.
- `docs/local_runtime_layout.md` dokumentiert alte BlackLab-Namen `data/blacklab_export` und `data/blacklab_index`, die laut Repo-Regeln nicht mehr als aktiv behandelt werden duerfen.

Bewertung:

- Mittel. Operativ gefaehrlich, weil Maintainer veraltete Pfade oder nicht existente Optionen lernen.

### 10. Pre-Deploy-Helper zeigen weiter auf `app/infra/docker-compose.dev.yml`

Betroffene Dateien:

- `app/scripts/pre_deploy_check.sh`
- `app/scripts/pre_deploy_check.ps1`

Konkrete Zeilen:

- `COMPOSE_FILE="infra/docker-compose.dev.yml"`
- `ComposeFile = "infra/docker-compose.dev.yml"`

Risiko:

- Das ist nicht der kanonische Root-Dev-Pfad `docker-compose.dev-postgres.yml`.
- Als sekundarer App-Repo-Helper ist das vertretbar, aber die Klassifikation fehlt klar in der Doku.

Bewertung:

- Mittel. Kein direkter Datenverlust, aber klares Root-Lift-/Source-of-truth-Problem.

### 11. `backup.sh` und Cron-Doku passen nicht zur aktuellen Serverstruktur

Betroffene Dateien:

- `app/scripts/backup.sh`
- `docs/operations/production.md`
- `docs/architecture/deployment-runtime.md`

Konkretes Verhalten:

- Script nutzt `~/corapan/backups`, `~/corapan/data`, `~/corapan/media`.
- Doku verweist als Cron-Beispiel auf `scripts/backup.sh`.
- Das weicht vom kanonischen Ziel `/srv/webapps/corapan/...` ab.

Risiko:

- Wahrscheinlich stale.
- Falls jemand es wirklich benutzt, sichert es den falschen Baum oder gar nichts.
- Kein Dry-Run, keine Pfadvalidierung, kein Root-Lift-Modell.

Bewertung:

- Mittel bis hoch. Als Backup-Skript ist ein falscher Pfad schlimmer als gar kein Skript.

## D. Wahrscheinlich veraltete oder tote Artefakte

Beibehalten, aber klar markieren oder entfernen:

1. `app/scripts/deploy_sync/legacy/20260116_211115/deploy_full_prod.ps1`
   - entfernen oder mindestens deutlich als tot markieren
   - Grund: falscher Root-Lift-Pfad `bash scripts/deploy_prod.sh`

2. `app/scripts/deploy_sync/legacy/20260116_211115/update_data_media.ps1`
   - entfernen oder deutlich als archival-only markieren
   - Grund: alte Sync-Inhalte, alter Combined-Runner

3. `app/scripts/deploy_sync/legacy/20260116_211115/PUBLISH_BLACKLAB_INDEX.md`
   - archivieren oder aus aktivem Suchraum entfernen
   - Grund: alte `blacklab_index`-Pfade

4. `app/scripts/backup.sh`
   - als legacy markieren oder ersetzen
   - Grund: `~/corapan` statt `/srv/webapps/corapan`

5. `docs/local_runtime_layout.md`
   - entweder hart aktualisieren oder klar als historische Uebergangsdoku markieren
   - Grund: mehrere alte BlackLab- und Repo-Namen

6. `maintenance_pipelines/_2_deploy/README_STATISTICS_DEPLOY.md`
   - nicht tot, aber in Teilen faktisch veraltet
   - Grund: beschreibt Features/Flags/Pfade, die nicht mehr zum Code passen

## E. Sofort noetige Korrekturen

1. `publish_blacklab_index.ps1` Upload-Schritt auf den zentralen SSH-Helper vereinheitlichen.
   - Kein nacktes `ssh` im tar-Pipeline-Pfad mehr.
   - Gleiche Key-, Port-, Host- und Host-Key-Policy wie im Rest.

2. Host-Key-Handling kanonisieren.
   - `StrictHostKeyChecking=no` entfernen.
   - festen `known_hosts`-Pfad oder Fingerprint-Pinning einfuehren.

3. `sync_core.ps1` gegen leere Quellen absichern, bevor `rsync --delete` laeuft.
   - Mindestdateizahl oder expliziter `AllowEmptySource`-Schalter.
   - Default muss sicher sein.

4. Doppelte Statistik-Ausfuehrung in `maintenance_pipelines/_2_deploy/deploy_data.ps1` entfernen.
   - Entweder Stats nur in `sync_data.ps1` belassen oder nur im Orchestrator, nicht in beiden.

5. BlackLab-Publish um echte Hits-Query erweitern.
   - Validierung darf nicht bei `/corpora` enden.

6. `pre_deploy_check.{sh,ps1}` explizit als sekundare App-Repo-Helper klassifizieren oder auf den Root-Dev-Pfad umstellen.

7. `backup.sh` entweder korrigieren auf `/srv/webapps/corapan/...` oder als veraltet aus der aktiven Produktionsdoku entfernen.

## F. Empfohlene Zielstruktur

### Kanonische operative Schichten

1. Normaler Code-Deploy
   - `.github/workflows/deploy.yml`
   - `app/scripts/deploy_prod.sh`
   - `app/infra/docker-compose.prod.yml`

2. Separater Runtime-Sync fuer grosse Bestaende
   - `app/scripts/deploy_sync/_lib/ssh.ps1`
   - `app/scripts/deploy_sync/sync_core.ps1`
   - `app/scripts/deploy_sync/sync_data.ps1`
   - `app/scripts/deploy_sync/sync_media.ps1`
   - `app/scripts/deploy_sync/publish_blacklab_index.ps1`

3. User-facing Orchestratoren
   - `maintenance_pipelines/_2_deploy/deploy_data.ps1`
   - `maintenance_pipelines/_2_deploy/deploy_media.ps1`
   - `maintenance_pipelines/_2_deploy/publish_blacklab.ps1`

4. Kanonische Doku fuer diese Strecke
   - neue `docs/rsync/README.md`
   - plus kurze Verweise aus `docs/operations/production.md` und `maintenance_pipelines/_2_deploy/README.md`

### Kanonische Server-Zielstruktur

- Code-Checkout: `/srv/webapps/corapan/app`
- versionierter App-Subtree: `/srv/webapps/corapan/app/app`
- Runtime data: `/srv/webapps/corapan/data`
- Runtime media: `/srv/webapps/corapan/media`
- Runtime logs: `/srv/webapps/corapan/logs`
- Runtime config fuer Container-Mount: `/srv/webapps/corapan/data/config`
- BlackLab mutable runtime state: `/srv/webapps/corapan/data/blacklab/{index,export,backups,quarantine}`

### Prinzipien fuer den Sync-Layer

- keine harten User-spezifischen Key-Pfade im Repo
- ein SSH-Helper, kein zweiter paralleler Pfad
- `--delete` nur mit sicherem Empty-Source-Guard
- Dry-Run fuer alle user-facing Orchestratoren
- Logging muss Aenderungen, Deletes und No-Op-Laeufe sichtbar machen
- Doku muss pro Lane explizit sagen:
  - was synced wird
  - was nie synced wird
  - ob delete aktiv ist
  - wie man einen Dry-Run macht

## G. Konkreter Patch-Plan in sinnvoller Reihenfolge

1. SSH-Layer haerten
   - `_lib/ssh.ps1`: Host-Key-Policy, optional `KnownHostsPath`, keine operator-spezifische 8.3-Vorgabe als Default
   - `sync_core.ps1`: direkte SSH-Reimplementierung abbauen oder auf `_lib/ssh.ps1` konsolidieren
   - `publish_blacklab_index.ps1`: Upload-Pipeline auf denselben SSH-Layer umstellen

2. Data-/Media-Sync sicher machen
   - `sync_core.ps1`: Empty-Source-Guard vor `rsync --delete`
   - eindeutiges Logging fuer:
     - uebertragene Dateien
     - geloeschte Dateien
     - no changes

3. Doppelten Statistik-Deploy entfernen
   - `maintenance_pipelines/_2_deploy/deploy_data.ps1`: zweiten `Sync-StatisticsFiles`-Aufruf entfernen oder per explizitem Flag exklusiv machen

4. BlackLab-Gate reparieren
   - `publish_blacklab_index.ps1`: echte Hits-Query gegen den Validierungscontainer und gegen den Produktionsport
   - Fehlerfall mit klarer Ausgabe von Query, HTTP-Code und ggf. Logs

5. Pre-Deploy-Helper klassifizieren
   - `pre_deploy_check.{sh,ps1}` entweder:
     - auf Root-Compose umstellen, oder
     - im Header und in der Doku als "sekundaerer app-only helper" markieren

6. Backup-Strecke bereinigen
   - `backup.sh` und Produktionsdoku angleichen
   - wenn nicht mehr genutzt: aus aktiver Doku entfernen und als legacy markieren

7. Doku konsolidieren
   - `docs/operations/runtime_statistics_deploy.md` korrigieren
   - `maintenance_pipelines/_2_deploy/README_STATISTICS_DEPLOY.md` korrigieren
   - `docs/local_runtime_layout.md` hart auf kanonische `data/blacklab/...`-Struktur bringen oder archival markieren
   - neue `docs/rsync/README.md` als Einstieg

## H. Testplan fuer Dry-Run und echten Lauf

### 1. Dry-Run Data Sync

Direkt auf Entry-Point-Ebene:

```powershell
$env:CORAPAN_RUNTIME_ROOT = "C:\dev\corapan"
.\app\scripts\deploy_sync\sync_data.ps1 -DryRun
```

Pruefen:

- zeigt lokale Quelle und Remote-Ziele
- zeigt explizit, dass `data/db` nicht als Ganzes gesynct wird
- zeigt Statistik-Dateien nur als geplante Datei-Liste
- fuehrt keinen SSH-Upload aus

### 2. Dry-Run Media Sync

```powershell
$env:CORAPAN_RUNTIME_ROOT = "C:\dev\corapan"
.\app\scripts\deploy_sync\sync_media.ps1 -DryRun
```

Pruefen:

- listet `transcripts`, `mp3-full`, `mp3-split`
- sagt klar, ob delete spaeter aktiv waere

### 3. Dry-Run BlackLab Publish

```powershell
.\maintenance_pipelines\_2_deploy\publish_blacklab.ps1 -AppRepoPath .\app -DryRun
```

Pruefen:

- lokales Staging `data/blacklab/quarantine/index.build` wird validiert
- Remote-Pfade und Swap-Ziele werden nur angezeigt
- keine echten Uploads, keine Retention-Loeschung

### 4. Sicherheits-Test fuer leere Quelle

Vor Patch:

- in isolierter Testumgebung mit leerem Testverzeichnis pruefen, dass aktueller Code remote loeschen wuerde

Nach Patch:

- derselbe Lauf muss mit klarer Fehlermeldung abbrechen
  - Beispiel erwartete Meldung: `REFUSED: source directory is empty; refusing rsync --delete`

### 5. Echte Data-Sync-Probe auf kleinem Testsegment

Voraussetzungen:

- Host-Key-Pinning eingerichtet
- Testlauf nur mit kleinem, bekannten Delta

Lauf:

```powershell
.\maintenance_pipelines\_2_deploy\deploy_data.ps1
```

Pruefen:

- genau eine Statistik-Ausfuehrung
- Logfile benennt uebertragene Dateien
- Logfile zeigt explizit "no changes" oder konkrete Deltas
- kein unerwarteter Delete

### 6. Echte Media-Sync-Probe mit einer gezielten Aenderung

Vorgehen:

- eine kleine Testdatei in `media/transcripts` oder ein kleines Test-Audio aendern
- Sync laufen lassen

Pruefen:

- nur erwartete Datei wird uebertragen
- Delete-Verhalten ist sichtbar und nachvollziehbar
- Resume-Verhalten fuer grosse Dateien bleibt intakt

### 7. Echte BlackLab-Publish-Probe

Vorgehen:

- neuen Index lokal bauen
- Publish laufen lassen

Pruefen:

- Upload nutzt denselben SSH-Pfad wie Preflight
- Validierungscontainer beantwortet eine echte Hits-Query
- Produktionsport beantwortet dieselbe oder eine aequivalente Hits-Query
- Backup-Retention bleibt report-only, solange nicht explizit auf Delete gestellt

## I. Vorschlag fuer minimale kanonische Dokumentation

Empfohlene neue Datei:

- `docs/rsync/README.md`

Minimalinhalt:

1. Zweck und Scope
   - "Diese Strecke deployed keine App-Releases. Sie synced nur grosse Runtime-Bestaende und BlackLab-Indexe."

2. Drei getrennte Lanes
   - Data Sync
   - Media Sync
   - BlackLab Publish

3. Kanonische Entry-Points
   - `maintenance_pipelines/_2_deploy/deploy_data.ps1`
   - `maintenance_pipelines/_2_deploy/deploy_media.ps1`
   - `maintenance_pipelines/_2_deploy/publish_blacklab.ps1`

4. Kanonische Remote-Ziele
   - `/srv/webapps/corapan/data`
   - `/srv/webapps/corapan/media`
   - `/srv/webapps/corapan/data/blacklab`

5. Was niemals per normalem Sync ueberschrieben wird
   - `data/db/auth.db`
   - sonstige produktive DB-State-Pfade
   - aktive App-Code-Pfade unter `/srv/webapps/corapan/app`

6. SSH-Vertrag
   - Host
   - User
   - Port
   - Key-Quelle
   - `known_hosts`-Pfad
   - keine Nutzung von `StrictHostKeyChecking=no`

7. Delete-Vertrag
   - welche Syncs `--delete` verwenden
   - welche Guards davor greifen
   - wie ein Dry-Run vor jedem echten Lauf aussieht

8. Observability-Vertrag
   - wo Logs landen
   - wie "no changes" aussieht
   - wie geloeschte und uebertragene Dateien ausgewiesen werden

9. BlackLab-spezifischer Vertrag
   - lokales Staging unter `data/blacklab/quarantine/index.build`
   - Remote staging unter `.../quarantine/index.upload_<timestamp>`
   - echte Hits-Query als Gate
   - Backup-Retention standardmaessig report-only

10. Kurzer Restore-/Rollback-Block
   - Data/Media: manueller SSH/rsync-Restore
   - BlackLab: `mv <active> <failed>; mv <backup> <active>`

Empfohlene Querverweise aus bestehender Doku:

- `docs/operations/production.md` -> kurzer Link auf `docs/rsync/README.md`
- `maintenance_pipelines/_2_deploy/README.md` -> kurzer Link auf `docs/rsync/README.md`
- `docs/operations/runtime_statistics_deploy.md` -> auf diese neue kanonische Seite reduzieren und nur statistik-spezifische Details behalten
