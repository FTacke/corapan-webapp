# CORAPAN rsync-/SSH-Server-Audit

Datum: 2026-03-25

Scope:
- Ausschliesslich `/srv/webapps/corapan`
- Keine Aenderungen ausser dem Anlegen dieses Berichts
- Keine destruktiven Operationen

Methodik:
- Dateisystem-Inventar unter `/srv/webapps/corapan`
- Auswertung der laufenden Container-Mounts
- Analyse der CORAPAN-Repo-, Workflow- und Publisher-Skripte
- Pruefung von systemd, Cron, SSHD, `.ssh`-Metadaten und Runner-Spuren
- Keine Annahmen ohne Beleg; Unsicherheiten sind markiert

Wichtige Einschraenkungen dieses Audits:
- Ein echter End-to-End-Dry-Run der externen rsync-/SSH-Strecke war auf dem Server selbst nicht direkt ausfuehrbar, weil die Publisher-Skripte auf eine Windows-/PowerShell-Senderseite mit lokalem Quellbestand und lokalem SSH-Key ausgelegt sind.
- Direkte `curl`-Livechecks aus dieser Sitzung wurden durch die Ausfuehrungsrichtlinie blockiert; als Ersatz wurden reale Runner-Logs und Container-Mounts ausgewertet.
- `ps` war in dieser Sitzung ebenfalls blockiert. Der Runner-Kontext wurde daher ueber systemd-Unit, Dateibesitz und Log-Spuren belegt.

## A. Tatsaechlicher Serverzustand

### 1. Top-Level-Struktur unter `/srv/webapps/corapan`

Aktueller Top-Level-Bestand:

```text
/srv/webapps/corapan/
  app/
  config/
  data/
  docs/
  logs/
  media/
  runner/
```

Top-Level-Metadaten:

| Pfad | Zweck | Groesse | Letzte Aenderung | Owner:Group | Rechte |
|---|---|---:|---|---|---|
| `/srv/webapps/corapan` | CORAPAN-Root | 20G | 2026-03-22 19:29:15 +0100 | `root:root` | `755` |
| `/srv/webapps/corapan/app` | Git-Checkout + Doku + Deploy-Skripte | 232M | 2026-03-24 22:25:28 +0100 | `root:root` | `755` |
| `/srv/webapps/corapan/config` | externe Secrets (`passwords.env`) | 4.0K | 2025-12-02 23:40:46 +0100 | `root:root` | `755` |
| `/srv/webapps/corapan/data` | Runtime-Daten | 1.8G | 2026-03-22 19:24:17 +0100 | `root:root` | `755` |
| `/srv/webapps/corapan/docs` | serverseitige CORAPAN-Doku | 36K | 2026-03-25 12:34:11 +0100 | `root:root` | `755` |
| `/srv/webapps/corapan/logs` | App-/Build-Logs | 4.5M | 2026-03-22 18:41:31 +0100 | `hrzadmin:hrzadmin` | `755` |
| `/srv/webapps/corapan/media` | Medien-Root | 15G | 2026-03-22 18:41:30 +0100 | `root:root` | `755` |
| `/srv/webapps/corapan/runner` | Self-hosted GitHub Runner | 2.4G | 2026-03-25 12:28:20 +0100 | `uid=1001 gid=1001` | `755` |

### 2. Relevante Daten-, Medien-, BlackLab- und Log-Verzeichnisse

| Pfad | Rolle | Groesse | Letzte Aenderung | Owner:Group | Rechte |
|---|---|---:|---|---|---|
| `/srv/webapps/corapan/data/blacklab` | BlackLab-Root | 1.8G | 2026-03-20 22:16:19 +0100 | `root:root` | `755` |
| `/srv/webapps/corapan/data/blacklab/index` | aktiver BlackLab-Index | 279M | 2026-03-22 18:40:12 +0100 | `root:root` | `755` |
| `/srv/webapps/corapan/data/blacklab/export` | BlackLab-Exportdaten | 1.5G | 2026-03-22 18:40:11 +0100 | `root:root` | `755` |
| `/srv/webapps/corapan/data/blacklab/backups` | Index-Backups | 0 | 2026-03-20 22:16:19 +0100 | `root:root` | `755` |
| `/srv/webapps/corapan/data/blacklab/quarantine` | Staging/Quarantaene | 0 | 2026-03-20 22:16:19 +0100 | `root:root` | `755` |
| `/srv/webapps/corapan/data/db` | DB-Root | 56K | 2026-01-18 19:48:51 +0100 | `hrzadmin:hrzadmin` | `775` |
| `/srv/webapps/corapan/data/db/public` | oeffentliche SQLite-DBs | 56K | 2026-03-24 20:08:06 +0100 | `hrzadmin:hrzadmin` | `770` |
| `/srv/webapps/corapan/data/db/restricted` | eingeschraenkte Daten | 0 | 2026-01-19 09:48:58 +0100 | `hrzadmin:hrzadmin` | `775` |
| `/srv/webapps/corapan/data/public` | oeffentliche Runtime-Daten | 7.2M | 2026-01-19 13:34:18 +0100 | `hrzadmin:hrzadmin` | `2775` |
| `/srv/webapps/corapan/data/public/metadata` | Metadaten-Downloads | 3.7M | 2026-03-22 18:41:07 +0100 | `hrzadmin:hrzadmin` | `755` |
| `/srv/webapps/corapan/data/public/statistics` | `corpus_stats.json` + `viz_*.png` | 3.6M | 2026-03-22 18:41:07 +0100 | `hrzadmin:hrzadmin` | `755` |
| `/srv/webapps/corapan/data/config` | in Container als `/app/config` gemountet | 0 | 2026-03-22 18:25:41 +0100 | `root:root` | `755` |
| `/srv/webapps/corapan/data/stats_temp` | Schreib-/Tempbereich fuer Stats | 0 | 2026-03-24 22:37:00 +0100 | `hrzadmin:hrzadmin` | `2775` |
| `/srv/webapps/corapan/data/tsv_json_test` | Test-/Hilfsdaten | 9.3M | 2025-12-02 13:03:56 +0100 | `hrzadmin:hrzadmin` | `755` |
| `/srv/webapps/corapan/media/mp3-full` | Vollaufnahmen | 6.5G | 2025-11-08 00:37:57 +0100 | `hrzadmin:hrzadmin` | `775` |
| `/srv/webapps/corapan/media/mp3-split` | Segmentierte Audios | 7.7G | 2025-11-08 03:00:18 +0100 | `hrzadmin:hrzadmin` | `775` |
| `/srv/webapps/corapan/media/mp3-temp` | temporaere Audioartefakte | 5.0M | 2026-03-24 17:16:31 +0100 | `hrzadmin:hrzadmin` | `775` |
| `/srv/webapps/corapan/media/transcripts` | Transkript-Store | 738M | 2025-11-16 14:51:20 +0100 | `hrzadmin:hrzadmin` | `775` |
| `/srv/webapps/corapan/logs` | produktive Logs | 4.5M | 2026-03-22 18:41:31 +0100 | `hrzadmin:hrzadmin` | `755` |

### 3. Alte vs. neue Struktur

Aktiver Ist-Zustand:
- Produktiv aktiv ist die kanonische Top-Level-Struktur:
  - `/srv/webapps/corapan/data`
  - `/srv/webapps/corapan/media`
  - `/srv/webapps/corapan/logs`
  - `/srv/webapps/corapan/data/config`
- Der laufende Web-Container mountet diese Pfade direkt nach `/app/*`.

Beleg:

```text
/srv/webapps/corapan/data -> /app/data
/srv/webapps/corapan/data/config -> /app/config
/srv/webapps/corapan/logs -> /app/logs
/srv/webapps/corapan/media -> /app/media
```

Dokumentierte Altstruktur:
- Im Repo ist `runtime/corapan/*` als Alt-/Uebergangsmodell dokumentiert.
- Der Code verbietet in Entwicklung sogar explizit repo-lokale `runtime/corapan`-Pfadnutzung.
- Auf dem Server selbst wurde unter `/srv/webapps/corapan` kein aktiver `runtime/corapan`-Baum gefunden.

### 4. Duplikate und ungewoehnliche Ablagen

Festgestellt wurden:
- Doppelte Code-Ablage:
  - produktives Git-Checkout: `/srv/webapps/corapan/app`
  - Runner-Workspace-Checkout: `/srv/webapps/corapan/runner/_work/corapan-webapp/corapan-webapp`
- Repo-intern verschachtelte App-Struktur:
  - Checkout-Root: `/srv/webapps/corapan/app`
  - eigentliche App-Inhalte darunter in `/srv/webapps/corapan/app/app`
- Leeres, aber vorgesehenes Audit-Zielverzeichnis: `/srv/webapps/corapan/docs/rsync`
- `data/exports` wird von `sync_data.ps1` erwartet, existiert im Ist-Zustand aber nicht.

Keine Symlinks festgestellt:
- Unter `/srv/webapps/corapan` wurden bis Tiefe 3 keine Symlinks gefunden.

## B. Gefundene Sync-Mechanismen

### 1. Serverseitige automatische Mechanismen

#### 1.1 GitHub Actions Self-Hosted Runner

Mechanismus:
- systemd-Unit: `actions.runner.FTacke-corapan-webapp.corapan-prod.service`
- `ExecStart=/srv/webapps/corapan/runner/runsvc.sh`
- `WorkingDirectory=/srv/webapps/corapan/runner`
- `User=` ist in der Unit leer; systemd faellt damit effektiv auf `root` zurueck.

Trigger:
- GitHub Workflow `Deploy to Production`
- `on.push.branches: [main]`
- `workflow_dispatch`

Ausgefuehrter Befehl laut Workflow/Runner-Logs:

```bash
cd /srv/webapps/corapan/app
git fetch --prune origin
git reset --hard "${GITHUB_SHA}"
bash app/scripts/deploy_prod.sh
```

User:
- effektiv `root` auf dem Server

Arbeitsverzeichnis:
- `cd /srv/webapps/corapan/app`

Bewertung:
- Das ist ein lokaler Code-Deploy auf dem Zielserver.
- Dieser Mechanismus nutzt Git und Docker Compose, nicht rsync.

#### 1.2 systemd `rsync.service`

Feststellung:
- `rsync.service` ist systemweit als enabled sichtbar.
- Es existiert jedoch **kein** `/etc/rsyncd.conf`.

Bewertung:
- Es gibt keinen Beleg fuer einen CORAPAN-spezifischen rsync-Daemon-Export.
- Ohne `/etc/rsyncd.conf` ist der Dienst fuer konkrete Module praktisch nicht konfiguriert.

### 2. Nicht gefunden: Cron/Timer fuer CORAPAN-rsync

Geprueft wurden:
- User-Crontabs aller lokalen Benutzer
- `/etc/cron*`
- systemd-Units/Timer mit `corapan|rsync|ssh|runner`

Ergebnis:
- Keine CORAPAN-spezifischen Cronjobs fuer rsync/ssh gefunden
- Keine CORAPAN-spezifischen Timer fuer rsync/ssh gefunden
- Kein separater serverautonomer Daten-Sync ausserhalb des GitHub-Runners belegt

### 3. Manuelle/Client-seitige Publisher-Skripte im Repo

Im Repo vorhanden, aber nicht serverautonom ausgefuehrt:
- `app/app/scripts/deploy_sync/sync_media.ps1`
- `app/app/scripts/deploy_sync/sync_data.ps1`
- `app/app/scripts/deploy_sync/publish_blacklab_index.ps1`
- `app/maintenance_pipelines/_2_deploy/publish_blacklab.ps1`

Charakter:
- Diese Skripte sind fuer eine Windows-/PowerShell-Senderseite ausgelegt.
- Sie pushen Daten auf den Linux-Server via SSH/rsync/scp bzw. `tar|ssh`.
- Der Server ist Ziel und Gegenstelle, nicht die aktive Senderseite.

## C. Verwendete Zielpfade

### 1. Wo landen Medien?

Produktiv aktiv:
- `/srv/webapps/corapan/media/mp3-full`
- `/srv/webapps/corapan/media/mp3-split`
- `/srv/webapps/corapan/media/transcripts`
- temporaer: `/srv/webapps/corapan/media/mp3-temp`

Code-Beleg:

```python
get_audio_full_dir()  -> get_media_root() / "mp3-full"
get_audio_split_dir() -> get_media_root() / "mp3-split"
get_audio_temp_dir()  -> get_media_root() / "mp3-temp"
get_transcripts_dir() -> get_media_root() / "transcripts"
```

Publisher-Beleg:
- `sync_media.ps1` synchronisiert genau `transcripts`, `mp3-full`, `mp3-split`
- `mp3-temp` ist explizit ausgeschlossen

### 2. Wo liegen BlackLab-Daten?

Aktiv:
- `/srv/webapps/corapan/data/blacklab/index`
- `/srv/webapps/corapan/data/blacklab/export`
- `/srv/webapps/corapan/data/blacklab/backups`
- `/srv/webapps/corapan/data/blacklab/quarantine`

Live-Container-Beleg:

```text
/srv/webapps/corapan/data/blacklab/index -> /data/index/corapan
/srv/webapps/corapan/app/config/blacklab -> /etc/blacklab
```

Wichtig:
- BlackLab-Konfiguration liegt **im Code-Checkout** unter `/srv/webapps/corapan/app/config/blacklab`.
- Der Index selbst liegt ausserhalb des Checkouts unter `/srv/webapps/corapan/data/blacklab/index`.

### 3. Wo landen Uploads?

Im Code nachweisbar:
- Editor-Speicherungen landen in `media/transcripts/<land>/<datei>.json`
- Backups landen in `media/transcripts/<land>/backup/`
- Edit-Historie landet in `media/transcripts/edit_log.jsonl`
- temporaere Audioartefakte landen in `media/mp3-temp`

Beleg aus `editor.py`:

```python
full_path = _transcripts_dir() / file_path
backup_dir = full_path.parent / "backup"
edit_log = _ensure_edit_log()
```

Ergebnis:
- Es wurde kein separater Upload-Root ausserhalb von `media/transcripts` bzw. `media/mp3-temp` gefunden.

### 4. Typische rsync-Zielpfade vs. Realitaet

Aus den Publisher-Skripten abgeleitete Zielpfade:
- `/srv/webapps/corapan/data`
- `/srv/webapps/corapan/media`
- `/srv/webapps/corapan/data/blacklab`
- `/srv/webapps/corapan/data/public/statistics`
- `/srv/webapps/corapan/data/db/public`

Ist-Zustand:
- Diese Pfade existieren alle, **ausser** `data/exports`
- `data/exports` ist im Script vorgesehen, aber auf dem Server derzeit nicht vorhanden

### 5. Pfade, die vom Code-Deploy ueberschrieben werden koennten

Sicher vom Git-Deploy betroffen:
- alles unter `/srv/webapps/corapan/app`
- insbesondere durch `git reset --hard "${GITHUB_SHA}"`

Nicht vom Git-Deploy betroffen:
- `/srv/webapps/corapan/data`
- `/srv/webapps/corapan/media`
- `/srv/webapps/corapan/logs`
- `/srv/webapps/corapan/config`

Kritischer Sonderfall:
- `/srv/webapps/corapan/app/config/blacklab` liegt **im Checkout** und wird vom BlackLab-Container direkt genutzt
- damit existiert hier eine echte Kollision zwischen Code-Deploy und produktiver BlackLab-Konfiguration

## D. Logging-Bewertung

### 1. Tatsae chliche Log-Orte

Gefunden wurden:
- App-/Build-Logs unter `/srv/webapps/corapan/logs`
- Runner-Diagnoselogs unter `/srv/webapps/corapan/runner/_diag`
- Runner-Workspace-Spuren unter `/srv/webapps/corapan/runner/_work`

Wichtige vorhandene Logdateien:
- `/srv/webapps/corapan/logs/corapan.log`
- `/srv/webapps/corapan/logs/blacklab_build_*.log`
- `/srv/webapps/corapan/logs/rebuild_*.log`
- `/srv/webapps/corapan/runner/_diag/Runner_*.log`
- `/srv/webapps/corapan/runner/_diag/Worker_*.log`

### 2. Bewertung der rsync-/Deploy-Transparenz

Positiv:
- GitHub-Runner-Logs belegen den ausgelosten Deploy-Befehl
- `.sync_state/*_manifest.json` belegen, dass Sync-Laeufe fuer Medien und Daten existiert haben
- `publish_blacklab.ps1` sieht auf der Senderseite PowerShell-Transcript-Logs vor

Negativ:
- Keine dedizierten serverseitigen rsync-Logdateien unter `/srv/webapps/corapan/logs`
- `sync_data.ps1` und DB-/Stats-Uebertragungen leiten rsync-Output weitgehend nach `Out-Null`
- `sync_core.ps1` parst rsync-Output fuer Progress, speichert aber serverseitig keinen vollstaendigen Audit-Log
- Erfolgs-/Fehlschlag sichtbar nur begrenzt ueber Exitcodes auf der Senderseite, nicht als dauerhafter Server-Audit-Trail
- No-Change-Laeufe sind serverseitig nicht eindeutig erkennbar
- Datei-fuer-Datei-Aenderungen sind im Regelfall nicht nachvollziehbar

### 3. Fazit Logging

Die Logging-Qualitaet fuer rsync-/SSH-Syncs ist fuer einen dauerhaften Server-Audit-Trail **unzureichend**.

Konkret unzureichend, weil:
- keine eigene serverseitige Sync-Logdatei pro Lauf
- keine persistierten Exitcodes auf dem Server
- keine klare Trennung zwischen `changed`, `unchanged`, `failed`
- keine durchgehende Korrelation zwischen Senderlauf, Zielpfad und Ergebnis

Konkrete Verbesserungen:
1. Alle Publisher-Skripte muessen pro Lauf ein serverseitig persistiertes Log unter `/srv/webapps/corapan/logs/sync/` schreiben.
2. rsync muss mit `--itemize-changes --out-format='%t %i %n%L'` laufen und in Logdateien geschrieben werden.
3. Jeder Lauf braucht eine maschinenlesbare Summary-Datei mit:
   - Startzeit
   - Endzeit
   - Sender
   - Zielpfad
   - Exitcode
   - Anzahl geaenderter Dateien
   - Dry-run ja/nein
4. No-Change-Laeufe muessen explizit als `changed=0` protokolliert werden.
5. Der GitHub-Runner sollte fuer Deploy-Laeufe zusaetzlich ein kompaktes Server-Deploy-Log unter `/srv/webapps/corapan/logs/deploy/` ablegen.

## E. Ergebnis Dry-Run/Test

### 1. Gewuenschter Test

Vorgesehen waere ein echter Dry-Run ueber die vorhandenen Publisher-Skripte gewesen, zum Beispiel:

```powershell
.\scripts\deploy_sync\sync_media.ps1 -DryRun
.\scripts\deploy_sync\sync_data.ps1 -DryRun
.\scripts\deploy_sync\publish_blacklab_index.ps1 -DryRun
```

### 2. Warum das auf dem Server nicht moeglich war

Begruendung:
- Auf dem Server ist **kein** `pwsh`/`powershell` vorhanden (`NO_POWERSHELL`).
- Die Publisher-Skripte sind auf eine Windows-Senderseite ausgelegt.
- Sie erwarten lokale Quellpfade und einen lokalen SSH-Key (`$env:USERPROFILE\.ssh\marele`).
- Der Server ist die Gegenstelle, nicht die produktive Senderumgebung.

### 3. Real ausgefuehrte, nicht-destruktive Verifikation

Es wurden statt eines nicht verfuegbaren Sender-Dry-Runs folgende Live-Belege genutzt:

```bash
docker inspect corapan-web-prod --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}' | sort
docker inspect corapan-blacklab --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}' | sort
docker inspect corapan-web-prod --format '{{.Config.User}}|{{.State.Status}}|{{.State.Health.Status}}'
docker inspect corapan-blacklab --format '{{.Config.User}}|{{.State.Status}}'
```

Ergebnis:
- `corapan-web-prod` laeuft und ist `healthy`
- Container-User im Web-Container: `corapan`
- `corapan-blacklab` laeuft
- Die aktiven Mounts entsprechen der kanonischen Top-Level-Struktur

Zusatzbeleg aus Runner-Logs:
- Die Runner-Worker-Logs enthalten die produktiven Deploy-Befehle und die Health-/Mount-Pruefungen des Workflows.

### 4. Bewertung

Ein echter End-to-End-rsync-Dry-Run mit produktiver Senderkonfiguration war in diesem Audit **nicht moeglich**.

Diese Einschraenkung ist sachlich begruendet und kein Indikator fuer einen Serverfehler, sondern fuer die Architektur der Publisher-Strecke.

## F. Konkrete Risiken / Fehlkonfigurationen

1. **BlackLab-Produktivkonfiguration liegt im Git-Checkout**
   - Pfad: `/srv/webapps/corapan/app/config/blacklab`
   - Risiko: `git reset --hard` und Repo-Deploy koennen produktive BlackLab-Konfiguration direkt aendern oder ueberschreiben.

2. **SSH-Publisher arbeiten standardmaessig als `root`**
   - Beleg: `_lib/ssh.ps1` default `User = "root"`
   - SSHD erlaubt `root` per Public Key (`permitrootlogin without-password`, `allowusers root`)
   - Risiko: hoher Blast Radius bei kompromittiertem Key oder Fehlskript.

3. **`StrictHostKeyChecking=no` in allen SSH/rsync/scp-Pfaden**
   - Risiko: Host-Key-Pruefung deaktiviert, MITM-Schutz praktisch abgeschaltet.

4. **`--delete` im generischen Directory-rsync**
   - Beleg: `sync_core.ps1`
   - Risiko: falscher Quellpfad oder falscher Trailing Slash kann Zielinhalte loeschen.

5. **`data/exports` laut Script vorgesehen, serverseitig aber nicht vorhanden**
   - Risiko: stiller Konfigurationsdrift oder nie fertig migrierter Teilpfad.

6. **Keine serverseitig belastbare rsync-Auditspur**
   - Risiko: im Incident-Fall unklare Frage, welche Dateien wann wirklich uebertragen wurden.

7. **Runner-Verzeichnis mit orphaned UID/GID 1001**
   - Risiko: unklare Besitzverhaeltnisse; spaetere Rechteprobleme oder unklare Betriebsverantwortung.

8. **`authorized_keys` fuer root ohne erkennbare Restriktionsoptionen**
   - Beleg: 15 Zeilen, keine Treffer fuer `command=`, `from=`, `restrict`, `no-port-forwarding`, `no-pty` etc.
   - Risiko: jeder eingetragene Key hat vollen root-Shell-Zugriff im Rahmen der SSHD-Policy.

9. **Mischung `root` vs. `hrzadmin` in Runtime-Pfaden**
   - Daten-/Medienroot gehoeren `root:root`, Unterverzeichnisse oft `hrzadmin:hrzadmin`
   - Funktioniert derzeit, ist aber ohne klares Ownership-Konzept stoeranfaelliger.

## G. Sofort notwendige Korrekturen

1. BlackLab-Konfiguration aus `/srv/webapps/corapan/app/config/blacklab` herausziehen in einen nicht deploybaren Runtime-Pfad, z. B. `/srv/webapps/corapan/config/blacklab` oder `/srv/webapps/corapan/data/config/blacklab`.
2. SSH-Key-Nutzung fuer Publisher haerten:
   - Host-Key-Pinning aktivieren
   - `StrictHostKeyChecking=yes`
   - `known_hosts` sauber pflegen
3. Root-SSH fuer Publisher reduzieren:
   - wenn moeglich dedizierten Deploy-User verwenden
   - falls root unvermeidbar, Keys in `authorized_keys` mit Restriktionen versehen
4. Serverseitiges Sync-Logging einfuehren.
5. `data/exports` explizit entscheiden:
   - entweder sauber migrieren/anlegen
   - oder aus `sync_data.ps1` entfernen

## H. Aufraeum-/Strukturmassnahmen

1. Runner-Besitzverhaeltnisse dokumentieren und orphaned UID/GID 1001 bereinigen.
2. Doppelte Repo-Ablagen klar dokumentieren:
   - produktives Checkout
   - Runner-Workspace-Checkout
3. Alte Doku-Referenzen auf `runtime/corapan/*` konsequent bereinigen, wenn der Live-Zielzustand dauerhaft Top-Level bleibt.
4. Leeres Audit-/Sync-Dokuverzeichnis `/srv/webapps/corapan/docs/rsync` weiter nutzen und verbindlich pflegen.
5. Ownership-Modell fuer Runtime-Pfade vereinheitlichen und schriftlich festlegen.

## I. Empfohlene Zielstruktur

Empfohlene Zielstruktur fuer Produktion:

```text
/srv/webapps/corapan/
  app/                      # nur Code/Repo/Build-Artefakte
  config/
    passwords.env
    blacklab/               # produktive BlackLab-Konfiguration
    ssh-known-hosts/        # optional, fuer gepinnte SSH-Hosts
  data/
    blacklab/
      index/
      export/
      backups/
      quarantine/
    config/                 # nur falls App-Config bewusst hierhin soll
    db/
      public/
      restricted/
    public/
      metadata/
      statistics/
    stats_temp/
    exports/                # nur wenn fachlich wirklich benoetigt
  media/
    transcripts/
    mp3-full/
    mp3-split/
    mp3-temp/
  logs/
    app/
    deploy/
    sync/
    blacklab/
  runner/
```

Grundsaetze:
- Code nie mit produktiver Konfiguration mischen
- produktive Daten nie im Checkout
- pro Funktionsbereich eigener Log-Ort
- Deploy und Daten-Sync strikt trennen

## J. SSH Server Setup & Gegenstelle

### 1. Beteiligte User

Festgestellt:

```text
root:x:0:0:root:/root:/bin/bash
hrzadmin:x:1000:1000:HRZ Admin,,,:/home/hrzadmin:/bin/bash
```

Serverseitige Rollen:
- `root`: SSH-Gegenstelle fuer Publisher und GitHub-Runner-nahe Operationen
- `hrzadmin`: Besitzer vieler Runtime-Unterverzeichnisse unter `data/`, `media/`, `logs/`

### 2. Home-Verzeichnisse und `.ssh`

Festgestellt:
- `/root/.ssh` existiert, `700`, `root:root`
- `/root/.ssh/authorized_keys` existiert, `600`, `root:root`, 15 Zeilen
- `/home/hrzadmin/.ssh` wurde nicht gefunden

Bewertung:
- Produktive SSH-Gegenstelle ist faktisch `root`
- `hrzadmin` ist Datenbesitzer, aber nicht als aktive SSH-Publisher-Gegenstelle belegt

### 3. Effektive SSHD-Konfiguration

Beleg:

```text
permitrootlogin without-password
pubkeyauthentication yes
passwordauthentication no
permitemptypasswords no
authorizedkeysfile .ssh/authorized_keys .ssh/authorized_keys2
allowusers root
```

Bewertung:
- Passt technisch zu den Publisher-Skripten, die `root` + Public-Key voraussetzen.
- Sicherheitsseitig ist das nur tragbar, wenn die verwendeten Keys stark kontrolliert und eingeschraenkt sind.

### 4. Bewertung `authorized_keys`

Festgestellt:
- keine sichtbaren Key-Restriktionsoptionen gefunden (`NO_KEY_RESTRICTIONS_FOUND`)

Bewertung:
- Das ist fuer einen root-only-Zugang zu breit.
- Empfohlen sind mindestens `from=`, `restrict`, `no-port-forwarding`, `no-agent-forwarding`, `no-pty` oder besser ein dedizierter Deploy-User.

## K. Abgleich mit GitHub Actions (konkret!)

### 1. Was GitHub Actions tatsaechlich liefert

Produktiver Code-Deploy laut Workflow:
- laeuft auf Self-Hosted Runner **direkt auf dem Zielserver**
- benoetigt **keinen** SSH-Hop von GitHub zum Server
- nutzt lokales Checkout unter `/srv/webapps/corapan/app`
- setzt Zustand hart auf `${GITHUB_SHA}` via `git reset --hard`

Was dafuer serverseitig vorhanden sein muss:
- laufender Runner-Service unter `/srv/webapps/corapan/runner`
- Git-Checkout unter `/srv/webapps/corapan/app`
- Docker + Compose V2
- `passwords.env` unter `/srv/webapps/corapan/config/passwords.env`
- laufende Zielpfade:
  - `/srv/webapps/corapan/data`
  - `/srv/webapps/corapan/media`
  - `/srv/webapps/corapan/logs`
  - `/srv/webapps/corapan/data/config`

### 2. Was fuer die externe rsync-/SSH-Strecke erwartet werden muss

Die externen Publisher-Skripte erwarten serverseitig:
- SSH-Ziel: `root@marele.online.uni-marburg.de:22`
- Public-Key-Login fuer `root`
- Zielpfade:
  - `/srv/webapps/corapan/data`
  - `/srv/webapps/corapan/media`
  - `/srv/webapps/corapan/data/blacklab`
- Schreibrechte auf diesen Pfaden
- BlackLab-Zusatzvoraussetzungen fuer Publish:
  - Docker
  - `curl`
  - `tar`
  - BlackLab-Konfiguration unter `/srv/webapps/corapan/app/config/blacklab`

### 3. Konsistenzbewertung Server vs. Repo/GitHub

Konsistent:
- Web-Container nutzt die im aktuellen Repo dokumentierte kanonische Top-Level-Mount-Struktur
- Runner-Logs belegen den aktuellen Deploy-Pfad `app/scripts/deploy_prod.sh`
- SSHD erlaubt genau das Modell, das die PowerShell-Publisher erwarten: `root` per Key
- BlackLab-Zielpfad `/srv/webapps/corapan/data/blacklab` ist vorhanden und aktiv

Abweichungen / Drift:
1. `data/exports` ist in `sync_data.ps1` vorgesehen, serverseitig aber nicht vorhanden.
2. Ein Teil der Doku und alte Workspace-Kopien referenzieren noch `runtime-first` bzw. fruehere Pfadlagen.
3. BlackLab-Konfiguration liegt in einem deploybaren Checkout-Pfad und nicht in einem stabilen Runtime-Config-Pfad.
4. Der Runner-Ordner gehoert einer nicht aufloesbaren UID/GID 1001, waehrend der Service effektiv als root laeuft.

Implizite Annahmen im aktuellen Setup:
- root-SSH ist auf Dauer akzeptiert
- Host-Key-Pruefung darf abgeschaltet sein
- BlackLab-Config darf im Git-Checkout liegen
- Senderseitige Transcript-/PowerShell-Logs reichen als Sync-Audit aus

Potenzielle Fehlerquellen:
- falscher oder leerer Senderpfad in Kombination mit `--delete`
- Checkout-Deploy aendert BlackLab-Konfiguration unbeabsichtigt mit
- inkonsistente `app/scripts/...` vs. `scripts/...` Aufrufpfade in aelteren Runner-Artefakten
- fehlende serverseitige Sync-Logs erschweren Fehleranalyse und Rollback

## Anhang: Wesentliche Befehle dieses Audits

```bash
find /srv/webapps/corapan -maxdepth 3 -printf '%y %p -> %l\n' | sort
find /srv/webapps/corapan/data /srv/webapps/corapan/media -maxdepth 3 -type d -name '.sync_state' -printf '%p|%TY-%Tm-%Td %TH:%TM:%TS|%u|%g|%M\n' | sort
docker inspect corapan-web-prod --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}' | sort
docker inspect corapan-blacklab --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}' | sort
systemctl cat actions.runner.FTacke-corapan-webapp.corapan-prod.service
systemctl list-unit-files --no-pager | grep -Ei 'corapan|runner|rsync|ssh'
sshd -T | grep -Ei 'permitrootlogin|passwordauthentication|pubkeyauthentication|authorizedkeysfile|allowusers'
rg -n -i 'rsync|scp|ssh|sync_state|deploy_prod|runtime/corapan|/srv/webapps/corapan' /srv/webapps/corapan/app
```

## Kurzfazit

Der produktive CORAPAN-Server nutzt aktuell **keine eigenstaendig servergetriebene rsync-Automation** fuer Daten. Die rsync-/SSH-Strecke ist in erster Linie als **externe Publisher-Strecke** im Repo angelegt, waehrend der eigentliche Code-Deploy lokal ueber den Self-Hosted GitHub Runner, Git und Docker Compose erfolgt.

Die Live-Zielpfade sind konsistent mit der neuen Top-Level-Struktur. Kritisch bleiben jedoch:
- root-basierte SSH-Publisher mit deaktivierter Host-Key-Pruefung
- fehlende serverseitige rsync-Auditlogs
- BlackLab-Konfiguration im Git-Checkout
- kleiner, aber realer Strukturdrift (`data/exports`, Alt-Doku, orphaned Runner-UID)