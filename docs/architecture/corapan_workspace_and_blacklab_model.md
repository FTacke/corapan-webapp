# CORAPAN Workspace And BlackLab Model

Datum: 2026-03-20
Geltungsbereich: Development und Repository-Struktur unter `corapan/`

## 1. Grundprinzip

Der einzige kanonische Workspace-Root ist `corapan/`.

Alle aktiven Dev-Pfade werden relativ zu diesem Root bestimmt.

`webapp/` ist kein Workspace-Root mehr, sondern der Implementierungsbereich der Webanwendung innerhalb des Gesamtprojekts.

Daraus folgen drei verbindliche Regeln:

1. Daten- und Media-Pfade werden relativ zu `corapan/` aufgeloest.
2. BlackLab-Artefakte liegen nur unter `corapan/data/blacklab/`.
3. `webapp/data` darf keine aktive BlackLab-Struktur mehr enthalten.

## 2. Kanonische Struktur

Die verbindliche Zielstruktur fuer den lokalen Dev-Betrieb lautet:

```text
corapan/
  .github/
  .venv/
  config/
    blacklab/
  data/
    blacklab/
      index/
      export/
      backups/
      quarantine/
  docs/
  media/
  scripts/
    blacklab/
  webapp/
```

Kanonische Rollen:

- `.github/`
  - gemeinsame Workspace-Instruktionen und Workflows am Root
- `.venv/`
  - einzige aktive lokale Python-Umgebung fuer den Root-basierten Dev-Workflow
- `config/blacklab/`
  - einzige aktive lokale BlackLab-Config fuer Root-Compose und Root-Skripte
- `data/blacklab/export/`
  - Export-Input fuer den lokalen BlackLab-Build
- `data/blacklab/index/`
  - aktiver lokaler BlackLab-Index
- `data/blacklab/backups/`
  - Root-basierte Build-Backups
- `data/blacklab/quarantine/`
  - Root-basierte Staging-, Log- und Fehlerpfade
- `scripts/`
  - kanonische Root-Einstiegspunkte fuer Dev und BlackLab
- `webapp/`
  - App-Code, Templates, Tests und Implementierungsdetails

## 3. BlackLab-Modell

Die einzige aktive lokale BlackLab-Struktur ist:

- `data/blacklab/index`
- `data/blacklab/export`
- `data/blacklab/backups`
- `data/blacklab/quarantine`

Der lokale Build folgt verbindlich diesem Datenfluss:

1. Transkripte aus `media/transcripts`
2. Export nach `data/blacklab/export`
3. Index-Build nach `data/blacklab/quarantine/index.build`
4. Aktivierung nach `data/blacklab/index`
5. Backup des vorherigen Index unter `data/blacklab/backups`

Der lokale BlackLab-Container mountet:

- `corapan/data/blacklab/index` nach `/data/index/corapan`
- `corapan/config/blacklab` nach `/etc/blacklab`

## 4. Anti-Patterns

Die folgenden Muster sind nicht mehr zulaessig:

### 4.1 `webapp/data` als aktive BlackLab-Quelle

Nicht erlaubt:

- `webapp/data/blacklab/...`
- `webapp/data/blacklab_index...`
- `webapp/data/blacklab_export...`

Diese Pfade gelten nur noch als Legacy- oder Fehlpfade.

### 4.2 Parallele BlackLab-Datenstrukturen

Nicht erlaubt:

- gleichzeitige aktive Nutzung von `data/blacklab/*` und `webapp/data/blacklab/*`
- flache Altpfade wie `data/blacklab_index` oder `data/blacklab_export` als aktive Defaults

### 4.3 Implizite Root-Annahmen aus Unterordnern

Nicht erlaubt:

- Annahme, dass `webapp/` der Projektroot sei
- relative Aufloesung von `media/transcripts` gegen `webapp/`
- relative Docker-Mounts gegen `webapp/data`

## 5. Dev-Workflow

Der kanonische lokale Einstieg erfolgt vom Root `corapan/` aus.

### 5.1 Taeglicher Start

```powershell
.\scripts\dev-start.ps1
```

Der Root-Wrapper ruft die Implementierung in `webapp/scripts/dev-start.ps1` auf, aber mit Root-basierter Compose-, Data-, Media- und Venv-Semantik.

### 5.2 Erst-Setup

```powershell
.\scripts\dev-setup.ps1
```

Die Root-basierte Umgebung nutzt:

- `corapan/.venv`
- `corapan/docker-compose.dev-postgres.yml`
- `corapan/data`
- `corapan/media`
- `corapan/config/blacklab`

### 5.3 BlackLab Export und Build

```powershell
python .\scripts\blacklab\run_export.py
.\scripts\blacklab\build_blacklab_index.ps1
```

### 5.4 Erwartete Pfade

- Transkripte: `corapan/media/transcripts`
- Export: `corapan/data/blacklab/export`
- Index: `corapan/data/blacklab/index`
- Config: `corapan/config/blacklab`

## 6. Aktueller Stand und bereinigtes Legacy

Im Zuge der Root-Neujustierung wurden folgende Punkte bereits umgesetzt:

- `.github` von `webapp/.github` nach `corapan/.github` verschoben
- `config/blacklab` von `webapp/config/blacklab` nach `corapan/config/blacklab` verschoben
- neue kanonische Root-Compose-Datei unter `corapan/docker-compose.dev-postgres.yml` angelegt
- neue kanonische Root-Wrapper unter `corapan/scripts/` angelegt
- neue Root-`.venv` unter `corapan/.venv` angelegt
- verschachtelte `webapp/.venv` nach `webapp/.venv_webapp_legacy_20260320` umbenannt
- relevante BlackLab-Exportdaten von `webapp/data/blacklab/export` nach `data/blacklab/export` ueberfuehrt
- falsche BlackLab-Strukturen unter `webapp/data` nach `webapp/data/_legacy_blacklab_invalid/` isoliert
- lokaler BlackLab-Index erfolgreich unter `data/blacklab/index` neu aufgebaut

Verbleibende Legacy-Pfade, die nicht mehr aktiv sind:

- `webapp/data/_legacy_blacklab_invalid/blacklab_wrong_root`
- `webapp/data/_legacy_blacklab_invalid/prior_unused_snapshot`
- `data/blacklab_export.duplicate_20260320`
- `webapp/.venv_webapp_legacy_20260320`
- historische Doku unter der frueheren `webapp/docs/`-Struktur, inzwischen bereinigt oder in kanonische Root-Dokumentation ueberfuehrt

## 7. Naechste Schritte / Roadmap

Die folgenden Punkte sind bewusst nicht Teil dieser Dev-Neujustierung, sollten aber spaeter separat behandelt werden:

1. Server-Cutover auf das analoge Zielmodell unter `/srv/webapps/corapan/`
2. Konsolidierung historischer Doku in `webapp/docs/`, die noch alte Pfade beschreibt
3. Entscheidung, ob weitere Root-Baeume wie `docs/` und `scripts/` vollstaendig aus `webapp/` herausgezogen oder dauerhaft als Wrapper-Modell gefuehrt werden
4. eventuelle spaetere Bereinigung der archivierten Legacy-Pfade nach gesonderter Freigabe

## 8. Verbindliche Merksaetze

- Workspace-Root ist `corapan/`.
- `data/blacklab/*` ist die einzige aktive lokale BlackLab-Wahrheit.
- `webapp/data` ist fuer BlackLab kein aktiver Datenpfad.
- Root-Skripte und Root-Compose sind die kanonischen Dev-Einstiegspunkte.
- Neue Pfade duerfen nicht mehr so entworfen werden, als sei `webapp/` der Projektroot.