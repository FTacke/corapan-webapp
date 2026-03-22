# Root Consistency Audit 2026-03-20

Datum: 2026-03-20
Umgebung: Development / lokaler Workspace
Scope: Git-Root, Workspace-Root, `.venv`, `.github`, `.gitignore`, `webapp/data`, repo-lokale Runtime-/Media-Pfade

## 1. Geprueft wurde

- echte Git-Grenze und versionierte Top-Level-Pfade
- aktive Python-Interpreter und virtuelle Umgebungen
- Root-`.github` versus leeres `webapp/.github`
- Root- und `webapp`-`.gitignore`
- Live-Docker-Mounts fuer Postgres und BlackLab
- `webapp/data` inklusive `db`, `exports`, `_legacy_blacklab_invalid`
- repo-lokale `webapp/runtime/corapan/*`-Pfade
- repo-weite aktive Referenzen in Skripten, Config und Hilfsdateien

## 2. Git-/Workspace-Realitaet

- Workspace-Root ist `C:\dev\corapan`
- echtes Git-Root ist weiterhin `C:\dev\corapan\webapp`
- `C:\dev\corapan` hat kein `.git`
- Root-Dateien wie `.github/`, `.venv/`, `config/`, `scripts/` und `docker-compose.dev-postgres.yml` liegen damit ausserhalb des aktuell versionierten Repos

Bewertung:

- `CORAPAN/` ist aktuell operativer Workspace, aber noch nicht Git-Root
- das ist weiterhin ein echter Widerspruch zwischen Zielmodell und Versionskontrollrealitaet

## 3. `.venv`-Pruefung

### Nachweis

- konfigurierte Python-Umgebung fuer den Workspace: `C:\dev\corapan\.venv`
- Root-`.venv` ist funktionsfaehig und mit Projektpaketen installiert
- laufende Python-Prozesse:
  - `C:\dev\corapan\.venv\Scripts\python.exe -m src.app.main`
  - `C:\dev\corapan\webapp\.venv\Scripts\python.exe -m src.app.main`
  - zusaetzlich weitere nicht-kanonische Interpreter-Prozesse

### Bewertung

- Root-`.venv` ist die beabsichtigte kanonische Dev-Umgebung
- `webapp/.venv_webapp_legacy_20260320` ist **nicht** vollstaendig erledigt, weil aktuell noch mindestens ein laufender Python-Prozess aus dem alten `webapp/.venv` stammt
- die Legacy-venv darf daher in diesem Zustand **nicht** endgueltig geloescht werden

## 4. `.github`-Pruefung

### Nachweis

- Root-`.github` enthaelt Instructions, Skills und Workflows
- `webapp/.github` wurde als leerer Doppelrest entfernt
- Root-Instruction-Dateien hatten vor diesem Run noch `applyTo`-Patterns wie `src/**` und `scripts/**`, die nicht zur Workspace-Root-Logik passten
- Root-Workflows waren am Workspace-Root vorhanden, sind aber nicht aktiv, solange das Git-Root unter `webapp/` liegt

### Bewertung

- massgebliche Customization-Fassung im Workspace ist Root-`.github`
- `webapp/.github` ist nur noch ein leerer Restordner
- Root-Workflows bleiben bis zu einer Git-Root-Migration faktisch inaktiv
- der produktive Deploy-Workflow wurde bewusst nicht angepasst, da er prod-spezifisch und ausserhalb dieses Cleanup-Scope ist

## 5. `.gitignore`-Pruefung

- aktive Repo-`.gitignore` ist `webapp/.gitignore`, weil `webapp/` das Git-Root ist
- Root-`.gitignore` ist fuer das aktuelle Git nicht wirksam, beschreibt aber das beabsichtigte kuenftige Root-Modell
- fuer das aktuelle Git-Root deckt `webapp/.gitignore` die lokale repo-venv ab, nicht aber Root-`.venv` als Git-Objekt; das ist unkritisch, weil Root-`.venv` ausserhalb des Git-Repos liegt

Bewertung:

- Ignore-Logik ist derzeit nur relativ zum aktuellen Git-Root konsistent
- fuer das Zielmodell `CORAPAN/` als Git-Root besteht weiterhin ein struktureller Mismatch

## 6. `webapp/data`-Pruefung

### `webapp/data/db/postgres_dev`

- Live-Nutzung belegt
- laufender Container `corapan_auth_db` mountet `C:\dev\corapan\webapp\data\db\postgres_dev -> /var/lib/postgresql/data`
- fachlich gehoert dieser Pfad kuenftig **nicht** unter `webapp/data`, sondern unter Root-`data/db/restricted/postgres_dev`
- konnte in diesem Run **nicht** entfernt werden, weil er aktuell live benutzt wird

### `webapp/data/exports`

- kein aktiver Verbraucher im App-/Dev-Startpfad belegt
- verbleibender Codebezug war nur ein Debug-Helfer
- fachlich gehoert der Pfad unter Root-`data/exports`
- Inhalt wurde nach Root-`data/exports` ueberfuehrt
- der bisherige Ordner unter `webapp/data/exports` ist jetzt leerer Rest

### `webapp/data/_legacy_blacklab_invalid`

- kein aktiver Verbraucher belegt
- rein historische Quarantaene fuer falsch gerootete BlackLab-Artefakte
- fachlich gehoert dieser Inhalt unter Root-`data/blacklab/quarantine`
- Inhalt wurde nach `data/blacklab/quarantine/webapp_legacy_blacklab_invalid_20260320` ueberfuehrt

### Gesamtbewertung `webapp/data`

- `webapp/data` konnte **nicht** vollstaendig entfernt werden
- blocker ist der live genutzte Postgres-Pfad `webapp/data/db/postgres_dev`
- zusaetzlich blieb ein leerer Restordner `webapp/data/exports` physisch stehen, obwohl der Inhalt bereits migriert ist

## 7. Repo-lokale Runtime-/Media-Pfade

### Nachweis

- `webapp/runtime/corapan/media/*` ist lokal leer
- `webapp/runtime/corapan/data/*` ist lokal praktisch leer bzw. nur als Reststruktur vorhanden
- laufende Dev-Skripte und `runtime_paths.py` verbieten repo-lokales `runtime/corapan` in Development
- verbleibende aktive Legacy-Referenz: `webapp/infra/docker-compose.dev.yml` mit Fallback auf `runtime/corapan/media`

### Bewertung

- repo-lokale Runtime-/Media-Pfade sind lokal derzeit nicht live belegt
- vollstaendig loeschbar sind sie aber erst, wenn die alternative Dev-Compose-Datei entweder stillgelegt oder explizit umgestellt wird

## 8. Live-Container-Realitaet

- `corapan_auth_db` live mountet weiterhin:
  - `C:\dev\corapan\webapp\data\db\postgres_dev`
  - `C:\dev\corapan\webapp`
- `blacklab-server-v3` live mountet weiterhin:
  - `C:\dev\corapan\data\blacklab\index`
  - `C:\dev\corapan\webapp\config\blacklab`

Bewertung:

- die laufende Dev-Realitaet ist noch gemischt
- Root-Index ist bereits live
- Postgres-Datenpfad und BlackLab-Config-Pfad laufen noch ueber alte `webapp`-Muster

## 9. Entscheidungslage nach diesem Run

- `webapp/data` darf noch **nicht** komplett weg
- `webapp/.venv_webapp_legacy_20260320` darf noch **nicht** geloescht werden, solange ein Altprozess laeuft
- repo-lokales `webapp/runtime/corapan/media` ist lokal leer und nicht live belegt, bleibt aber wegen der alternativen Dev-Compose-Datei vorerst als Restpfad bestehen
- Root-Struktur ist nur **teilweise** konsistent: fuers Zielmodell ja, fuer Git-Root und laufende Container noch nein