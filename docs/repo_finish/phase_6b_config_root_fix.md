# Phase 6b - CONFIG_ROOT Fix

Datum: 2026-03-23
Workspace: `C:\dev\corapan`
Modus: lokaler Runtime-Config-Fix ohne Push, ohne Deploy

## 1. Problem

Im Phase-6-Run wurde ein echter Architekturwiderspruch festgestellt:

- die Zielarchitektur und die Root-Lift-Dokumentation klassifizieren `C:\dev\corapan\data\config` als kanonischen Runtime-Config-Pfad
- die aktive Dev-Laufzeit loeste `CONFIG_ROOT` aber zu `C:\dev\corapan\config` auf
- dieser Root-Pfad existiert nicht mehr im Arbeitsbaum und ist nicht mehr kanonisch

Damit standen Dokumentation, Struktur und aktiver Runtime-Code im Widerspruch.

## 2. Analyse des alten Verhaltens

### Beteiligte Dateien

- `app/src/app/runtime_paths.py`
- `app/src/app/config/__init__.py`
- `app/scripts/dev-start.ps1`
- `scripts/dev-start.ps1`

### Alte Pfadauflosung

Alte Kette:

1. `app/scripts/dev-start.ps1` setzt `CORAPAN_RUNTIME_ROOT` im Dev-Fall auf den Workspace-Root `C:\dev\corapan`
2. `get_runtime_root()` liest genau diesen Wert
3. `get_config_root()` leitete daraus bisher `CORAPAN_RUNTIME_ROOT / "config"` ab
4. `BaseConfig.CONFIG_ROOT` in `app/src/app/config/__init__.py` uebernahm das Ergebnis unveraendert

Konkretes altes Ergebnis im Dev-Check:

- `RUNTIME_ROOT = C:\dev\corapan`
- `CONFIG_ROOT = C:\dev\corapan\config`

### Aktive Zugriffe

Die aktive Definition bzw. Nutzung von `CONFIG_ROOT` lief ueber:

- `get_config_root()` in `app/src/app/runtime_paths.py`
- `CONFIG_ROOT = get_config_root()` in `app/src/app/config/__init__.py`
- Runtime-Logging in `log_resolved_paths()` und `load_config()`

Eine breite aktive Call-Site-Landschaft gab es nicht. Der Widerspruch sass zentral in der Resolver-Funktion.

## 3. Zielarchitektur

Kanonisch gilt jetzt eindeutig:

```text
CONFIG_ROOT = CORAPAN_RUNTIME_ROOT / data / config
```

Das bedeutet fuer den lokalen Dev-Fall mit `CORAPAN_RUNTIME_ROOT = C:\dev\corapan`:

```text
CONFIG_ROOT = C:\dev\corapan\data\config
```

Wichtige Konsequenzen:

- kein Fallback auf `C:\dev\corapan\config`
- keine parallele zweite Runtime-Config-Logik
- `CORAPAN_RUNTIME_ROOT` bleibt weiterhin der Workspace-Root
- nur die Config-Ableitung wird auf den kanonischen Runtime-Datenbaum ausgerichtet

## 4. Code-Anpassungen

Umgesetzt wurde:

1. `app/src/app/runtime_paths.py`
   - `get_config_root()` liefert jetzt `get_data_root() / "config"`

Keine Aenderung war noetig an:

- `scripts/dev-start.ps1`
- `app/scripts/dev-start.ps1`
- `app/src/app/config/__init__.py`

Begruendung:

- die Dev-Startskripte setzen `CORAPAN_RUNTIME_ROOT` bereits korrekt auf den Workspace-Root
- `config/__init__.py` uebernimmt `CONFIG_ROOT` korrekt aus dem Resolver
- der Fehler lag ausschliesslich in der alten Ableitung `runtime_root/config`

## 5. Dev-Check

Nach dem Fix wurde erneut ein minimaler Laufzeit-Check mit `create_app('development')` ausgefuehrt.

Gesetzte Kernvariablen:

- `FLASK_ENV=development`
- `CORAPAN_RUNTIME_ROOT=C:\dev\corapan`
- `CORAPAN_MEDIA_ROOT=C:\dev\corapan\media`
- `AUTH_DATABASE_URL=postgresql+psycopg2://corapan_auth:corapan_auth@127.0.0.1:54320/corapan_auth`
- `BLS_BASE_URL=http://localhost:8081/blacklab-server`
- `BLS_CORPUS=corapan`

Erwartetes Pruefziel:

- `CONFIG_ROOT = C:\dev\corapan\data\config`
- keine Fehler beim App-Factory-Start
- Auth-DB weiterhin erreichbar

Tatsaechliches Ergebnis:

- `create_app('development')` lief erfolgreich an
- Auth-DB-Verbindung wurde weiterhin erfolgreich verifiziert
- die aktive Aufloesung laut Runtime-Log und App-Config ist jetzt:
   - `RUNTIME_ROOT = C:\dev\corapan`
   - `DATA_ROOT = C:\dev\corapan\data`
   - `CONFIG_ROOT = C:\dev\corapan\data\config`
   - `MEDIA_ROOT = C:\dev\corapan\media`
- es traten keine neuen Fehler auf

## 6. Entfernte Altpfade

Aktiv entfernt wurde der falsche Altpfad aus der Resolver-Logik:

- vorher: `CORAPAN_RUNTIME_ROOT/config`
- jetzt: `CORAPAN_RUNTIME_ROOT/data/config`

Klassifikation der konkurrierenden Pfade nach dem Fix:

- `C:\dev\corapan\data\config`: **active**
- `C:\dev\corapan\config`: **legacy/dangerous**, nicht mehr kanonisch und nicht mehr Zielpfad der aktiven Resolver-Logik

Historische Dokumente, die den frueheren Konflikt oder alte Zwischenstaende beschreiben, bleiben als Forensik bestehen. Sie sind nicht mehr die operative Wahrheit.

## 7. Go / No-Go fuer Review-Branch-Push

Der Laufzeit-Check hat den erwarteten Pfad `C:\dev\corapan\data\config` bestaetigt. Der spezifische `CONFIG_ROOT`-Blocker ist damit behoben.

Damit gilt fuer diesen Teilaspekt:

### GO FUER REVIEW-BRANCH-PUSH

unter der Voraussetzung, dass der Arbeitsbaum danach noch bewusst in einen commit-bereiten Zustand gebracht wird.