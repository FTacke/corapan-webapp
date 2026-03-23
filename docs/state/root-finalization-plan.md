# Root Finalization Plan

Datum: 2026-03-20
Umgebung: Development / lokaler Workspace
Status: funktional stabil, strukturell noch nicht vollstaendig finalisiert

## 1. Aktueller Zustand

- Workspace-Root ist `C:\dev\corapan`
- echtes Git-Root ist weiterhin `C:\dev\corapan\webapp`
- Root-BlackLab ist aufgebaut und validiert
- Root-`.venv` ist funktionsfaehig und als kanonische Dev-Umgebung vorbereitet
- `webapp/data` ist bereits weitgehend bereinigt, wird aber noch nicht vollstaendig freigegeben
- repo-lokale `runtime/corapan`-Pfade sind fuer aktive Dev-Skripte nicht mehr die kanonische Dev-Wahrheit

## 2. Bestaetigte verbleibende Blocker

### 2.1 Postgres-Blocker

Live-Nachweis:

- laufender Container: `corapan_auth_db`
- Live-Mounts:
  - `C:\dev\corapan\webapp -> /app`
  - `C:\dev\corapan\webapp\data\db\postgres_dev -> /var/lib/postgresql/data`

Bewertung:

- `webapp/data/db/postgres_dev` ist aktuell noch **aktiv belegt**
- dieser Pfad blockiert die Entfernung von `webapp/data`
- fachlicher Zielpfad fuer die finale Struktur ist `C:\dev\corapan\data\db\restricted\postgres_dev`

### 2.2 Legacy-venv-Blocker

Live-Nachweis:

- laufender Prozess:
  - PID `30072`
  - Executable: `C:\dev\corapan\webapp\.venv\Scripts\python.exe`
  - CommandLine: `"C:\dev\corapan\webapp\.venv\Scripts\python.exe" -m src.app.main`

Bewertung:

- die alte webapp-venv ist nicht nur historisch vorhanden, sondern aktuell noch live genutzt
- solange dieser Prozess nicht beendet ist, darf die Legacy-venv nicht geloescht werden

### 2.3 Git-Blocker

Live-Nachweis:

- `C:\dev\corapan` enthaelt kein `.git`
- Git-Top-Level ist weiterhin `C:\dev\corapan\webapp`
- derzeit ausserhalb des Git-Roots liegende relevante Root-Pfade:
  - `C:\dev\corapan\.github`
  - `C:\dev\corapan\.venv`
  - `C:\dev\corapan\scripts`
  - `C:\dev\corapan\config`
  - `C:\dev\corapan\data`
  - `C:\dev\corapan\docker-compose.dev-postgres.yml`
  - `C:\dev\corapan\.gitignore`
  - `C:\dev\corapan\.python-version`

Bewertung:

- das Zielmodell `CORAPAN/` als echte Root-Struktur ist noch nicht durch Git abgesichert
- Root-Dateien sind operativ relevant, aber derzeit nicht Teil des versionierten Repos

## 3. Was bereits final sauber ist

- Root-BlackLab-Index ist live korrekt unter `C:\dev\corapan\data\blacklab\index`
- aktive Dev-Skripte `dev-start.ps1` und `dev-setup.ps1` verwenden das Workspace-Root als kanonische Runtime-Basis
- Root-`.github` wurde auf Workspace-Root-Logik vorbereitet
- `webapp/data/exports` wurde inhaltlich nach `C:\dev\corapan\data\exports` ueberfuehrt
- `webapp/data/_legacy_blacklab_invalid` wurde nach `C:\dev\corapan\data\blacklab\quarantine\webapp_legacy_blacklab_invalid_20260320` ueberfuehrt
- `webapp/.github` als leerer Doppelrest wurde entfernt

## 4. Was noch nicht entfernt werden darf

### `webapp/data`

Der Ordner darf noch nicht entfernt werden, weil darin weiterhin der live gemountete Postgres-Pfad liegt:

- `webapp/data/db/postgres_dev`

Aktueller Restinhalt von `webapp/data`:

- `.gitkeep`
- `db/`
- `exports/` als leerer Restordner
- `README.md`

### `webapp/.venv_webapp_legacy_20260320`

Noch nicht freigeben, solange der laufende Prozess aus der alten webapp-venv nicht beendet wurde.

### `webapp/runtime/corapan/media`

Noch nicht loeschen. Der Pfad ist lokal nicht als aktiver Verbraucher belegt, aber die alternative Datei `webapp/infra/docker-compose.dev.yml` referenziert weiterhin repo-lokale Runtime-Media-Fallbacks.

## 5. Konkreter Plan

### 5.1 Postgres-Pfad-Migration

Ziel:

- finaler Datenpfad: `C:\dev\corapan\data\db\restricted\postgres_dev`

Betroffene Dateien / Quellen:

- kanonisch: `C:\dev\corapan\docker-compose.dev-postgres.yml`
- vorbereitend korrigiert: `C:\dev\corapan\webapp\docker-compose.dev-postgres.yml`
- Dev-Skripte setzen bereits `POSTGRES_DEV_DATA_DIR` auf `data/db/restricted/postgres_dev`
- Config-Default in `src/app/config/__init__.py` erwartet bereits `DATA_ROOT / db / restricted / postgres_dev`

Sauberer spaeterer Switch:

1. laufenden Dev-App-Prozess geordnet beenden
2. `corapan_auth_db` kontrolliert stoppen
3. validieren, dass keine Datei-Locks auf `webapp/data/db/postgres_dev` mehr bestehen
4. Datenbestand von `webapp/data/db/postgres_dev` nach `data/db/restricted/postgres_dev` angleichen oder einmalig final ueberfuehren
5. kanonischen Root-Compose verwenden: `docker compose -f C:\dev\corapan\docker-compose.dev-postgres.yml up -d`
6. per `docker inspect corapan_auth_db` bestaetigen, dass der Host-Mount jetzt auf `C:\dev\corapan\data\db\restricted\postgres_dev` zeigt
7. danach erst `webapp/data/db/postgres_dev` als loeschbar klassifizieren

### 5.2 venv-Bereinigung

Ziel:

- einzige aktive Dev-venv: `C:\dev\corapan\.venv`

Bedingung fuer Entfernung der Legacy-venv:

- Prozess PID `30072` oder jeder Nachfolgeprozess mit `ExecutablePath = C:\dev\corapan\webapp\.venv\Scripts\python.exe` muss beendet sein

Saubere Abfolge:

1. laufende App-Prozesse inventarisieren
2. Altprozess aus `webapp/.venv` gezielt beenden
3. sicherstellen, dass neue Starts nur noch Root-`.venv` verwenden
4. erneut Prozessliste pruefen
5. erst dann `webapp/.venv_webapp_legacy_20260320` final entfernen

### 5.3 Runtime-Cleanup

Aktueller Status:

- `webapp/runtime/corapan/media` ist lokal nicht als aktiver Live-Pfad belegt
- die alternative Dev-Compose-Datei `webapp/infra/docker-compose.dev.yml` traegt aber noch Fallbacks auf `./runtime/corapan/media`

Saubere Abfolge:

1. entscheiden, ob `webapp/infra/docker-compose.dev.yml` stillgelegt oder auf Root-Logik umgestellt wird
2. danach repo-weiten aktiven Referenzcheck auf `runtime/corapan/media` wiederholen
3. wenn keine aktive Referenz mehr uebrig ist, `webapp/runtime/corapan/media` als entfernbar freigeben
4. erst danach physisch loeschen

### 5.4 Git-Root-Migration

Ziel:

- echtes Git-Root von `C:\dev\corapan\webapp` auf `C:\dev\corapan` heben

Warum das der wichtigste Abschluss-Schritt ist:

- nur so werden Root-`.github`, Root-Compose, Root-`.gitignore`, Root-`.python-version`, Root-`config`, Root-`scripts` und Root-`data` Teil der versionierten Wahrheit

Sichere Migrationsabfolge:

1. kompletten aktuellen Status von `webapp/.git` sichern
2. Root-Dateien und Root-Verzeichnisse gegen den gewuenschten Sollzustand final inventarisieren
3. entscheiden, welche doppelt vorhandenen Top-Level-Pfade unter `webapp/` als Legacy bleiben und welche in die Root-Wahrheit uebergehen
4. neues Git-Root auf `C:\dev\corapan` etablieren
5. Root-`.gitignore` und Root-`.github` als alleinige massgebliche Fassungen verifizieren
6. `git status` am Root gegen die gesamte Workspace-Struktur pruefen
7. danach erst verbleibende Doppelpfade unter `webapp/` kontrolliert abbauen

## 6. Minimaler Abschlusszustand nach diesen vier Schritten

Der Workspace gilt erst dann als strukturell finalisiert, wenn alle folgenden Punkte wahr sind:

- Postgres mountet nicht mehr `webapp/data/db/postgres_dev`, sondern Root-`data/db/restricted/postgres_dev`
- kein laufender Python-Prozess nutzt mehr `webapp/.venv`
- `webapp/runtime/corapan/media` hat keine aktive Referenz mehr
- `CORAPAN/` ist echtes Git-Root
- Root-`.github`, Root-`.venv`, Root-`config`, Root-`scripts`, Root-`data` und Root-Compose sind nicht nur operativ, sondern auch versioniert kanonisch