# Doc-Metadaten-Integration: Abschlussbericht (15.11.2025)

## Zusammenfassung

Die Integration von `docmeta.jsonl` in den BlackLab-Index wurde versucht, ist aber **noch nicht funktionsfähig**. Die Filter-Architektur ist korrekt implementiert, aber BlackLab 5.x lädt die externen Metadaten nicht wie erwartet.

## Was funktioniert ✅

1. **Filter-Architektur (vollständig repariert)**
   - Doc-Metadaten-Filter (`country_code`, `radio`, `city`, `date`) werden als BlackLab-`filter`-Parameter übergeben
   - Speaker-Filter laufen über CQL-Constraints mit `speaker_code`
   - Keine Python-Nachfilterung mehr
   - `recordsTotal` = `recordsFiltered` = BlackLab's `numberOfHits`

2. **Grundlegende Suchen**
   - Lemma/Forma-Suche: 761 Treffer für "casa"
   - POS-Mode: 150.866 Treffer für "VERB"
   - Speaker-Filter: 284 Treffer für "casa" + sex=f
   - Pagination funktioniert korrekt

3. **Metadaten-Infrastruktur**
   - `docmeta.jsonl` existiert mit 146 Dokumenten
   - Felder: `file_id`, `country_code`, `date`, `radio`, `city`, `audio_path`
   - `file_id` entspricht TSV-Dateinamen (z.B. `2023-08-10_ARG_Mitre`)

## Was nicht funktioniert ❌

**Externe Metadaten-Import in BlackLab 5.x**

Versuchte Ansätze:

### 1. `blacklab-server.yaml` Konfiguration
```yaml
corpora:
  corapan:
    metadata:
      documentFormat: jsonlines
      path: /data/export/docmeta.jsonl
      idField: file_id
```
**Ergebnis**: HTTP 500 Error beim Server-Start

### 2. `linkedDocuments` in BLF
```yaml
linkedDocuments:
  inputFile:
    name: docmeta.jsonl
  ...
```
**Ergebnis**: `InvalidInputFormatConfig: Unknown key ...` bei verschiedenen Syntaxvarianten

### 3. `valuePath` in Metadatenfeldern
```yaml
metadata:
  fields:
    - name: country_code
      valuePath: country_code
```
**Ergebnis**: Index baut erfolgreich, aber Server liefert HTTP 400/500 Errors

## Diagnose

**Problem**: BlackLab 5.x unterstützt entweder:
- Externe Metadaten-Import nicht (oder anders als dokumentiert)
- Die Syntax ist in BlackLab 5.0.0-SNAPSHOT anders als in der Dokumentation
- `--linked-file-dir` Parameter funktioniert nicht wie erwartet

**Beobachtungen**:
- Index-Build mit `--linked-file-dir /data/export` läuft durch
- Keine Warnungen über fehlende `docmeta.jsonl`
- Aber: Server kann Korpus nicht laden oder liefert Fehler

## Aktueller Status

**Index**: Wiederhergestellt auf Stand vor Metadaten-Experiment
- 146 Dokumente, 1.5M Tokens
- Token-Annotationen funktionieren
- Metadatenfelder definiert, aber leer

**Test-Ergebnisse** (mit altem Index):
```
✓ PASS   Health Check
✓ PASS   Simple Search        (761 hits)
✗ FAIL   Country Filter       (0 hits - Metadaten nicht im Index)
✓ PASS   Speaker Filters      (284 hits - sex=f)
✓ PASS   POS Mode             (150866 hits - q=VERB)
```

## Geänderte Dateien (diese Runde)

1. **`scripts/start_blacklab_docker_v3.ps1`**
   - Mount für `/data/export` hinzugefügt (funktioniert)
   - Path-Escaping-Bug gefixt (`\\` → `\`)

2. **`config/blacklab/blacklab-server.yaml`**
   - Versuchte Metadaten-Konfiguration wieder auskommentiert

3. **`config/blacklab/corapan-tsv.blf.yaml`**
   - Kommentar hinzugefügt: Externe Metadaten nicht funktionsfähig
   - Metadatenfelder bleiben definiert (Schema), aber ohne `valuePath`

4. **`test_docmeta_integration.ps1`**
   - Erstellt (noch nicht getestet, da Metadaten fehlen)

## Empfohlene Lösungsansätze

### Option A: Metadaten in TSV integrieren (bevorzugt)

**Vorteil**: Alles in einem Format, garantiert funktionstüchtig

1. `LOKAL/.../blacklab_index_creation.py` erweitern:
   - Doc-Metadaten aus `docmeta.jsonl` einlesen
   - Als zusätzliche TSV-Spalten pro Token wiederholen: `country_code`, `radio`, `city`, `date`

2. `corapan-tsv.blf.yaml` anpassen:
   - Metadatenfelder mit `valuePath` auf TSV-Spalten mappen

**Nachteil**: TSV-Dateien werden größer (4 zusätzliche Spalten × 1.5M Tokens)

### Option B: BlackLab 4.x downgrade

Falls BlackLab 4.x externe Metadaten besser unterstützt.

**Risiko**: Laut Notizen wurde BlackLab 4.x wegen Reflections-Bibliotheksproblemen übersprungen.

### Option C: BlackLab-Community kontaktieren

GitHub Issues bei `INL/BlackLab` mit Frage zur korrekten Syntax für externe JSON-Metadaten in v5.x.

## Commit-Message (für diese Runde)

```
feat(blacklab): attempt docmeta.jsonl integration (not yet working)

- Add /data/export mount in Docker script for metadata access
- Fix path escaping bug in start_blacklab_docker_v3.ps1
- Try various linkedDocuments/valuePath configurations  
- Document that external metadata import doesn't work in BL 5.x yet

Filter architecture is correct, but metadata fields remain empty.
Recommend integrating metadata into TSV export as next step.
```

## Nächste Schritte

**Kurzfristig** (um Doc-Metadaten-Filter zum Laufen zu bringen):
1. Option A implementieren: Metadaten in TSV integrieren
2. `blacklab_index_creation.py` erweitern
3. Index neu bauen
4. Tests validieren

**Langfristig** (sauberere Lösung):
- BlackLab-Dokumentation/Community konsultieren
- Externes Metadaten-Feature richtig verstehen
- Sobald funktionstüchtig: Zurück zu Option B (externe JSONL)
