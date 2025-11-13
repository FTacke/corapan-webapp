# BlackLab Index Build: JSON → TSV → Lucene Index

> **Aktueller Status (2025-11-13):**  
> System läuft mit **BlackLab 3.0.0 (Lucene 8)**.  
> Lucene-9-Migration (BlackLab 4.x) ist vorbereitet, aber derzeit durch Upstream-Problem blockiert.

## Datenfluss-Architektur

```text
media/transcripts/           # Rohdaten (JSON) - QUELLE DER WAHRHEIT
        ↓
data/blacklab_export/tsv/    # Exportierte TSVs (temporär, jederzeit neu baubar)
data/blacklab_export/docmeta.jsonl
        ↓
data/blacklab_index/         # Lucene-Index (temporär, jederzeit neu baubar)
```

**Wichtig:**
- **Einzige Wahrheit:** `media/transcripts/` (JSON-Dateien)
- **Wegwerf-Artefakte:** `data/blacklab_export/` und `data/blacklab_index/` können gelöscht und neu erstellt werden
- **Legacy:** `data/blacklab_index.backup/` ist optional (historischer Snapshot, wird nicht mehr aktiv genutzt)

## Current State - Stand: 2025-11-13

- ✅ **JSON-Quelldaten:** 146 JSON-Dateien in `media/transcripts/` (~1.488.019 Tokens)
- ✅ **TSV-Export:** 146 TSV-Dateien in `data/blacklab_export/tsv/`
- ✅ **Metadaten:** `data/blacklab_export/docmeta.jsonl` (146 Dokumente)
- ✅ **JSON→TSV Export:** Automatisiert via `blacklab_index_creation.py`
- ✅ **Index-Build:** BlackLab 3.0.0 Docker-basiert (stabil)
- ⚠️ **BlackLab 4.x:** Vorbereitet, aber durch Reflections-Exception blockiert

## Aktueller Workflow (BlackLab 3.x / Lucene 8)

Der produktive Workflow nutzt **BlackLab 3.0.0** im Docker-Container.

### Schritt 1: JSON → TSV Export

```powershell
# Export aus JSON-Transkripten
.\LOKAL\01 - Add New Transcriptions\03b build blacklab_index\build_index.ps1
```

Dies führt `blacklab_index_creation.py` aus und erstellt:
- `data/blacklab_export/tsv/*.tsv` (146 Dateien)
- `data/blacklab_export/docmeta.jsonl`

### Schritt 2: TSV → Lucene Index (BlackLab 3.x)

```powershell
# Index mit BlackLab 3.0.0 (Docker) bauen
.\scripts\build_blacklab_index_v3.ps1
```

Dies erstellt `data/blacklab_index/` mit Lucene 8 Format.

### Schritt 3: BlackLab Server starten

```powershell
# BlackLab 3.x im Hintergrund starten
.\scripts\start_blacklab_docker_v3.ps1 -Detach

# Server-URL: http://localhost:8081/blacklab-server/
```

### Schritt 4: Advanced Search testen

```powershell
# Flask-App starten
.venv\Scripts\activate
$env:FLASK_ENV="development"
python -m src.app.main

# Browser: http://localhost:5000/search/advanced
```

### Voraussetzungen

- **Docker Desktop** installiert und gestartet
- **TSV-Dateien** in `data/blacklab_export/tsv/` (erstellt durch Schritt 1)

### Details: build_blacklab_index_v3.ps1

Das Skript führt folgende Schritte aus:

1. **Vorbedingungen prüfen:**
   - Docker ist verfügbar und läuft
   - TSV-Dateien in `data/blacklab_export/tsv/` vorhanden (146 Dateien)
   - `docmeta.jsonl` vorhanden
   - BlackLab-Konfiguration `config/blacklab/corapan-tsv.blf.yaml` existiert

2. **Docker-Image pullen:**
   - `instituutnederlandsetaal/blacklab:3.0.0` (falls noch nicht vorhanden)

3. **Vorhandenen Index sichern:**
   - Verschiebt `data/blacklab_index/` nach `data/blacklab_index.old_YYYYMMDD_HHMMSS/`
   - Optional: `--SkipBackup` überspringt Backup

4. **Index aufbauen im Docker-Container:**
   - Führt `blacklab-indexer create` im Container aus
   - Nutzt TSV-Dateien + `docmeta.jsonl` als Quelle
   - Schreibt fertigen Index nach `data/blacklab_index/`

5. **Verifizierung:**
   - Prüft, ob Lucene-Dateien (`segments_*`, `*.si`) erstellt wurden
   - Zeigt Index-Größe und Dateianzahl

**Parameter:**

- `--Force`: Keine Sicherheitsabfragen (für Skripte)
- `--SkipBackup`: Kein Backup des alten Index (Use with caution!)

**Beispiel mit Force-Modus:**

```powershell
.\scripts\build_blacklab_index_v3.ps1 -Force
```

### Quelldaten

- **JSON-Quelle:** `media/transcripts/*.json` (146 Dateien, ~1.5M Tokens)
- **TSV-Dateien:** `data/blacklab_export/tsv/*.tsv` (146 Dateien)
- **Metadaten:** `data/blacklab_export/docmeta.jsonl` (146 Dokumente)
- **Konfiguration:** `config/blacklab/corapan-tsv.blf.yaml` (17 Annotationen)

⚠️ **Wichtig:** 
- **Niemals löschen:** `media/transcripts/` (einzige Wahrheit)
- **Wegwerf-Artefakte:** `data/blacklab_export/` und `data/blacklab_index/` können jederzeit neu erstellt werden

---

## Lucene 9 Migration (geplant, derzeit blockiert)

### Problem: BlackLab 4.x / Lucene 9

Der Versuch, auf **BlackLab 4.0.0 (Lucene 9)** zu migrieren, scheitert an einer **Reflections-Library-Exception**:

```
org.reflections.ReflectionsException: Scanner TypeAnnotationsScanner was not configured
```

**Betroffene Komponenten:**
- BlackLab 4.0.0 JAR (lokal)
- BlackLab 4.0.0 Docker-Image (`instituutnederlandsetaal/blacklab:4.0.0`)

**Status:** Upstream-Bug oder Konfigurationsproblem außerhalb unserer Kontrolle.

### Warum Lucene 9?

Lucene 9 bringt:
- Verbesserte Performance
- Kleinere Index-Größe
- Moderne JVM-Optimierungen

**Aber:** Die Migration ist **nicht kritisch**. BlackLab 3.x (Lucene 8) ist stabil und erfüllt alle Anforderungen.

### Dokumentierte Versuche

1. **JAR-basierte Indexierung:** Reflections-Exception bei `IndexTool.main()`
2. **Docker-basierte Indexierung:** Identische Exception im Container
3. **Maven Central Download:** JAR ist korrupt oder unvollständig (2.5 KB statt ~80 MB)
4. **Docker-Image-Extraktion:** JAR aus Container extrahiert, gleiches Problem

**Fazit:** Problem liegt im BlackLab 4.0.0 Build selbst, nicht in unserer Konfiguration.

### Nächste Schritte (optional, keine Priorität)

Falls Lucene 9 zukünftig benötigt wird:

1. **Warten auf BlackLab 4.0.1+** mit Reflections-Fix
2. **Issue im BlackLab-Repo melden:** https://github.com/INL/BlackLab/issues
3. **BlackLab selbst bauen:** Nur als letzter Ausweg, hoher Aufwand

**Aktuell:** System läuft stabil mit BlackLab 3.x, keine dringende Notwendigkeit für Migration.

---

## Test-Checkliste

Nach dem Index-Rebuild und JAR-Setup sollten folgende Tests erfolgreich sein:

**Testumgebung einrichten**

**Voraussetzung:** Docker Desktop muss laufen.

```powershell
# Terminal 1: JSON->TSV Export und Index-Build
.\LOKAL\01 - Add New Transcriptions\03b build blacklab_index\build_index.ps1

# Terminal 2: BlackLab 3.x Server starten
.\scripts\start_blacklab_docker_v3.ps1 -Detach
```

### Test 1: Index-Build (Docker-basiert, BlackLab 3.x)

**Ziel:** Verifizieren, dass Index-Build im Docker-Container korrekt funktioniert.

```powershell
# Index neu aufbauen (BlackLab 3.x, Docker)
.\scripts\build_blacklab_index_v3.ps1
```

**Erfolgskriterien:**
- ✅ Skript findet Docker und Daemon läuft
- ✅ Docker-Image `instituutnederlandsetaal/blacklab:3.0.0` vorhanden oder wird gepullt
- ✅ 146 TSV-Dateien gefunden in `data/blacklab_export/tsv/`
- ✅ Alte Index-Version wird automatisch gesichert (`data/blacklab_index.old_TIMESTAMP/`)
- ✅ blacklab-indexer läuft erfolgreich durch (Exit Code 0)
- ✅ Neue Index-Dateien vorhanden: `segments_*`, `*.si`, `*.cfs`
- ✅ Index-Größe > 0 MB
- ✅ Keine Exceptions im Docker-Output

**Debug bei Fehlern:**
```powershell
# Docker prüfen
docker version

# TSV-Dateien prüfen
(Get-ChildItem "data\blacklab_export\tsv\*.tsv" | Measure-Object).Count

# Index-Verzeichnis prüfen
Get-ChildItem "data\blacklab_index" -Recurse | Measure-Object
```

### Test 2: BlackLab-Server (mit Docker, BlackLab 3.x)

**Ziel:** Verifizieren, dass BlackLab-Server den neu aufgebauten Index laden kann.

```powershell
# BlackLab 3.x starten
.\scripts\start_blacklab_docker_v3.ps1 -Detach

# API-Root testen
Invoke-WebRequest -Uri "http://localhost:8081/blacklab-server/" -UseBasicParsing | Select-Object StatusCode, Content
```

**Erfolgskriterien:**
- ✅ HTTP 200 (kein 500!)
- ✅ JSON-Response mit BlackLab-Versionsinformationen (3.0.0)
- ✅ Container-Status: `Up` (nicht `Restarting` oder `Exited`)
- ✅ Keine Lucene-Exceptions im Container-Log
- ✅ Index erfolgreich geladen

**Container-Logs prüfen:**
```powershell
docker logs blacklab-server-v3 --tail 50
```

### Test 3: Advanced Search – End-to-End

**Ziel:** Verifizieren, dass Flask-App erfolgreich mit BlackLab kommuniziert und Suchergebnisse anzeigt.

```powershell
# Flask starten (separates Terminal)
.venv\Scripts\activate
$env:FLASK_ENV="development"
python -m src.app.main

# Browser öffnen
# http://localhost:8000/search/advanced
```

**Testsuche:** Token `casa` (oder andere häufige Wörter)

**Erfolgskriterien:**
- ✅ Trefferliste wird angezeigt
- ✅ Kein `upstream_error` im JSON
- ✅ Kein HTTP 500, keine Tracebacks
- ✅ Audio-Links funktionieren (sofern MP3-Dateien vorhanden)
- ✅ DataTables zeigt mindestens 1 Treffer
- ✅ Pagination funktioniert (falls > 20 Treffer)
- ✅ Metadaten-Filter funktionieren (Land, Datum, etc.)

### Test 4: Fehlerbehandlung – BlackLab Offline

**Ziel:** Verifizieren, dass die App sauber mit BlackLab-Ausfall umgeht.

```powershell
# BlackLab stoppen
.\scripts\stop_blacklab_docker.ps1

# Advanced Search erneut ausführen (gleiche Suche)
```

**Erfolgskriterien:**
- ✅ Sauberer Fehler mit `upstream_unavailable` im JSON
- ✅ MD3-Error-Banner im Frontend: "BlackLab Server nicht erreichbar"
- ✅ Keine 500-Fehler, keine Stacktraces
- ✅ Anwendung bleibt stabil
- ✅ Andere Seiten (z.B. Home, Corpus) funktionieren weiterhin

### Test 5: CQL-Syntaxfehler (Error-Handling)

**Ziel:** Verifizieren, dass ungültige CQL-Queries sauber behandelt werden.

```powershell
# BlackLab läuft, Flask läuft
# Advanced Search: ungültige CQL-Query eingeben, z.B. "[pos="VERB" AND"
```

**Erfolgskriterien:**
- ✅ JSON enthält `"error_code": "invalid_cql"`
- ✅ Frontend zeigt Error-Banner mit CQL-Syntaxfehler
- ✅ Keine 500-Fehler
- ✅ Detaillierte Fehlermeldung (z.B. "Unexpected token at position X")

---

## Technischer Hintergrund

### Lucene-Versionskompatibilität

- Lucene 8.x → 9.x ist ein **Major-Upgrade** mit Breaking Changes
- Index-Format (`codecs`) ist inkompatibel
- Kein automatisches Migration-Tool verfügbar
- Einzige Lösung: Index von Grund auf neu erstellen

### BlackLab-Indexierung

CO.RA.PAN nutzt:
- **Format:** TSV (Tab-Separated Values)
- **Annotationen:** 17 Spalten (word, norm, lemma, pos, tokid, start_ms, end_ms, ...)
- **Metadaten:** `docmeta.jsonl` (147 Dokumente mit country_code, date, radio, city, audio_path)
- **Config:** `config/blacklab/corapan-tsv.blf.yaml`

Der Indexer liest:
1. TSV-Dateien (Token-Annotationen)
2. `docmeta.jsonl` (Dokument-Metadaten via `--linked-file-path`)
3. `.blf.yaml` (Schema-Definition)

Und schreibt einen Lucene-Index nach `data/blacklab_index/`.



## Referenzen

- **Lucene 9 Migration Guide:** https://lucene.apache.org/core/9_0_0/core/org/apache/lucene/codecs/lucene90/package-summary.html
- **BlackLab Indexing Docs:** https://blacklab.ivdnt.org/blacklab-server/indexing.html
- **CO.RA.PAN Index-Schema:** `config/blacklab/corapan-tsv.blf.yaml`
- **Dev-Setup-Anleitung:** `docs/how-to/advanced-search-dev-setup.md`

## Troubleshooting

### Problem: Skript findet Docker nicht

```powershell
✗ FEHLER: Docker ist nicht verfügbar oder läuft nicht.
```

**Lösung:** Docker Desktop starten und warten, bis der Daemon läuft.

### Problem: TSV-Dateien nicht gefunden

```powershell
✗ FEHLER: Keine TSV-Dateien in data\blacklab_index.backup\tsv\ gefunden.
```

**Lösung:** Prüfe, ob `data/blacklab_index.backup/` vollständig ist. Falls nicht, aus Backup wiederherstellen.

### Problem: Docker-Exit-Code ≠ 0

```powershell
✗ FEHLER: Indexierung fehlgeschlagen (Exit Code: 1)
```

**Mögliche Ursachen:**

1. **BLF-Config ungültig:** Prüfe YAML-Syntax in `config/blacklab/corapan-tsv.blf.yaml`
2. **TSV-Dateien defekt:** Öffne eine TSV-Datei und prüfe auf Header-Zeile + Tab-getrennte Werte
3. **Keine Schreibrechte:** Prüfe Berechtigungen für `data/blacklab_index/`

**Debug-Modus:** Führe den Docker-Befehl manuell aus:

```powershell
docker run --rm `
  -v "$PWD\data\blacklab_index.backup:/data:ro" `
  -v "$PWD\data\blacklab_index:/data/index:rw" `
  -v "$PWD\config\blacklab:/etc/blacklab:ro" `
  instituutnederlandsetaal/blacklab:latest `
  blacklab-indexer create /data/index "/data/tsv/*.tsv" /etc/blacklab/corapan-tsv.blf.yaml --docmeta /data/docmeta.jsonl
```

### Problem: Index erstellt, aber BlackLab liefert trotzdem 500

**Prüfe:**

1. **Index nicht leer:**
   ```powershell
   Get-ChildItem data\blacklab_index -Recurse | Measure-Object
   ```
   Sollte > 0 Dateien haben.

2. **BlackLab läuft mit neuem Index:**
   ```powershell
   .\scripts\stop_blacklab_docker.ps1
   .\scripts\start_blacklab_docker.ps1
   ```

3. **Logs prüfen:**
   ```powershell
   docker logs corapan-blacklab-dev --tail 100
   ```

4. **Volume-Mounts korrekt:**
   ```powershell
   docker inspect corapan-blacklab-dev | Select-String "Mounts" -Context 10
   ```
   Sollte zeigen: `data/blacklab_index -> /data/index`

