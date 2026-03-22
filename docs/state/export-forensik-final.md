# Export-Forensik Final 2026-03-20

Datum: 2026-03-20
Modus: read-only, gezielte Abschlussverifikation
Zielpfad: `/srv/webapps/corapan/data/blacklab_export`

## 1. Container-Mounts

Geprüft wurde `docker inspect` für alle aktuell vorhandenen Container.

Befund:

- Kein Container mountet `/srv/webapps/corapan/data/blacklab_export`.
- `corapan-web-prod` mountet nur `/srv/webapps/corapan/runtime/corapan/data` nach `/app/data`.
- `corapan-blacklab` mountet `/srv/webapps/corapan/data/blacklab_index` nach `/data/index/corapan`.

Bewertung:

- kein belegter Container-Leser
- kein belegter Container-Schreiber

## 2. Aktive Host-Prozesse

Geprüft wurde nur:

- `lsof /srv/webapps/corapan/data/blacklab_export`

Befund:

- keine Ausgabe
- Exit-Code 1

Bewertung:

- es ist aktuell kein offener Dateihandle auf genau diesem Pfad belegt

## 3. Bekannte Deploy-/Ops-Pfade

Gezielt geprüft wurden:

- `app/scripts/deploy_sync/**`
- `app/scripts/blacklab/**`
- `app/scripts/deploy_prod.sh`
- `runner/.service`
- `runner/runsvc.sh`

Befund:

- In `app/scripts/**` gibt es keinen expliziten Treffer auf `/srv/webapps/corapan/data/blacklab_export`.
- `deploy_sync/sync_data.ps1` referenziert nur `blacklab_export` als Runtime-Deploy-Verzeichnis, nicht den Top-Level-Pfad.
- `blacklab/build_blacklab_index.ps1` referenziert nur relatives `blacklab_export` unter einem aus Umgebung oder Repo abgeleiteten Datenroot, nicht den expliziten Top-Level-Pfad.
- `runner/.service` zeigt nur auf den GitHub-Runner-Service `actions.runner.FTacke-corapan-webapp.corapan-prod.service`.
- `runner/runsvc.sh` startet nur `RunnerService.js` und enthält keinen Bezug auf `blacklab_export`.

Bewertung:

- kein expliziter Ops-/Deploy-Pfad mit `/srv/webapps/corapan/data/blacklab_export` belegt

## 4. systemd / cron

Gezielt geprüft wurden:

- `actions.runner.FTacke-corapan-webapp.corapan-prod.service`
- `docker.service`
- `docker.socket`
- Root-Crontab
- `hrzadmin`-Crontab

Befund:

- Der bekannte CORAPAN-Runner-Service ist `active`, aber seine Unit startet nur `/srv/webapps/corapan/runner/runsvc.sh`.
- In der Unit selbst steht kein Verweis auf `/srv/webapps/corapan/data/blacklab_export`.
- `docker.service` und `docker.socket` enthalten keinen Verweis auf den Zielpfad.
- Root-Crontab enthält nur:
  - `/usr/bin/docker system prune -af --volumes`
  - `/usr/local/bin/disk-check.sh`
- Für `hrzadmin` existiert keine Crontab.

Bewertung:

- kein belegter systemd-/cron-Zugriff auf `/srv/webapps/corapan/data/blacklab_export`

## 5. Zugriffstimestamps

`stat /srv/webapps/corapan/data/blacklab_export` ergab:

- Access: `2025-12-02 16:54:26.185208560 +0100`
- Modify: `2025-11-23 10:58:53.962764600 +0100`
- Change: `2026-01-19 09:57:59.880704860 +0100`

Bewertung:

- letzter Access-Zeitstempel ist alt
- letzter Modify-Zeitstempel ist alt
- `Change` belegt nur eine Metadatenänderung, nicht inhaltliche Nutzung

## 6. Klassifikation

Klassifikation für `/srv/webapps/corapan/data/blacklab_export`:

- `UNUSED`

Begründung ausschließlich aus belegten Fakten:

- kein Container-Mount auf diesen Pfad
- kein offener Host-Prozess auf diesen Pfad
- kein expliziter Treffer in den gezielt geprüften bekannten Ops-/Deploy-Pfaden
- kein belegter systemd-/cron-Zugriff
- alter Access-/Modify-Timestamp

## 7. Abschlussentscheidung

Klare Aussage:

- `Löschung jetzt sicher`

Diese Aussage stützt sich ausschließlich auf die in dieser finalen Verifikation belegten Fakten zum aktuellen Zustand.