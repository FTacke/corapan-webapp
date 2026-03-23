# Root Finalization Completed

Datum: 2026-03-20
Umgebung: Development / lokaler Workspace

## 1. Kurzfazit

Die verbleibenden operativen Legacy-Blocker der Dev-Struktur wurden kontrolliert aufgeloest. Aktive Dev-Daten liegen nicht mehr unter `webapp/data`, aktive Runtime-Media liegen nicht mehr unter `webapp/runtime`, und es gibt keinen laufenden Prozess mehr aus der alten webapp-venv.

Die einzige bewusst verbleibende strukturelle Einschraenkung ist das weiterhin unter `webapp/.git` liegende Git-Root.

## 2. Durchgefuehrte Migrationen

### Postgres

- App-Prozesse wurden beendet
- `corapan_auth_db` wurde gestoppt
- Lock-Pruefung fuer den alten Pfad `webapp/data/db/postgres_dev` wurde erfolgreich durch Pfadprobe bestanden
- alter Live-Datenbaum wurde nach `data/db/restricted/postgres_dev` ueberfuehrt
- der bisherige Root-Zielbaum wurde vorab als Snapshot gesichert unter:
  - `data/db/restricted/postgres_dev.pre_migration_20260320_legacy_snapshot`
- Root-Compose wurde auf den finalen Mount korrigiert
- `corapan_auth_db` wurde neu erstellt und mountet jetzt live:
  - `C:\dev\corapan\data\db\restricted\postgres_dev -> /var/lib/postgresql/data`

### venv

- alle laufenden App-Prozesse aus der alten webapp-venv wurden beendet
- ein zusaetzlicher nicht-kanonischer App-Prozess wurde entfernt, bevor die App sauber neu gestartet wurde
- `webapp/.venv_webapp_legacy_20260320` wurde physisch entfernt
- es gibt keinen laufenden Prozess mehr mit `ExecutablePath` unter `webapp/.venv*`

### Runtime

- `webapp/infra/docker-compose.dev.yml` wurde von repo-lokalem `runtime/corapan/media` auf Root-`media` umgestellt
- repo-lokaler Runtime-Baum `webapp/runtime/corapan` wurde entfernt
- der nun leere Parent `webapp/runtime` wurde ebenfalls entfernt

## 3. Entfernte Pfade

- `data/blacklab_export.duplicate_20260320`
- `webapp/data`
- `webapp/runtime/corapan`
- `webapp/runtime`
- `webapp/.venv_webapp_legacy_20260320`

## 4. Finaler Zustand

### Aktive Datenpfade

- Postgres: `C:\dev\corapan\data\db\restricted\postgres_dev`
- BlackLab Index: `C:\dev\corapan\data\blacklab\index`
- BlackLab Export: `C:\dev\corapan\data\blacklab\export`
- Quarantaene / Archiv: `C:\dev\corapan\data\blacklab\quarantine`

### Aktive Media-Pfade

- Root-Media: `C:\dev\corapan\media`
- keine aktive Dev-Referenz mehr auf `webapp/runtime/corapan/media`

### Aktive venv

- kanonische Dev-Umgebung: `C:\dev\corapan\.venv`
- keine aktive Nutzung mehr von `webapp/.venv`

### Aktiver Git-Root

- weiterhin `C:\dev\corapan\webapp\.git`

Bewertung:

- Laufzeit- und Pfadmodell sind dev-seitig bereinigt
- Versionskontroll-Root ist noch nicht auf `CORAPAN/` gehoben

## 5. Validierungsergebnisse

### Postgres

- Live-Container `corapan_auth_db` mountet:
  - `C:\dev\corapan\data\db\restricted\postgres_dev`
- Container wurde gesund (`healthy`)

### App

- `GET /health` -> `200`
- `GET /health/auth` -> `200`

### BlackLab

- `GET /health/bls` -> `200`
- BlackLab blieb waehrend der Finalisierung erreichbar

### Aktive Referenzen

- keine aktive technische Referenz mehr auf `webapp/data`
- keine aktive technische Referenz mehr auf repo-lokales `runtime/corapan/media`
- verbleibender Treffer auf `runtime/corapan/...` in `README.md` ist Produktionsdokumentation, keine aktive Dev-Referenz

## 6. Verbleibende Restpunkte

- Git-Root ist weiterhin `webapp/.git`
- Root-`.github`, Root-`.venv`, Root-`config`, Root-`scripts`, Root-`data` und Root-Compose sind damit operativ kanonisch, aber noch nicht als echtes Git-Root versioniert
- fuer eine vollstaendige strukturelle Finalisierung fehlt noch die separate Git-Root-Migration von `webapp/` nach `CORAPAN/`