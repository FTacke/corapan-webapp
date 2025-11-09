---
title: "BlackLab Index Creation Guide"
status: active
owner: backend-team
updated: "2025-11-09"
tags: [blacklab, indexing, corpus-search, export, tsv, wpl]
links:
  - ../reference/blacklab-configuration.md
  - ../concepts/corpus-search-architecture.md
  - ../../LOKAL/01 - Add New Transcriptions/03 update DB/blacklab_index_creation.py
---

# BlackLab Index Creation Guide

Schritt-für-Schritt-Anleitung zum Exportieren von JSON v2 Annotationen nach BlackLab TSV/WPL und zum Erstellen eines BlackLab-Index.

---

## Ziel

Nach dieser Anleitung hast du:
- ✅ Export-Dateien im TSV- oder WPL-Format
- ✅ Dokument-Metadaten als JSONL
- ✅ Einen funktionierenden BlackLab-Index
- ✅ Getestete Suchabfragen mit allen Annotationen

---

## Voraussetzungen

### Erforderliches Wissen
- Grundkenntnisse: Python, Kommandozeile
- Vertrautheit mit CO.RA.PAN JSON v2 Struktur

### Benötigte Tools
- Python 3.8+
- BlackLab IndexTool (Java-basiert)
- BlackLab Server (optional für Web-Frontend)

### Systemzustand
- ✅ JSON v2 Dateien vollständig annotiert (via `annotation_json_in_media_v2.py`)
- ✅ Pflichtfelder vorhanden: `token_id`, `start_ms`, `end_ms`, `lemma`, `pos`, `norm`, `sentence_id`, `utterance_id`
- ✅ Speaker-Codes standardisiert (via `migrate_speakers_to_codes.py`)

---

## Schritte

### Schritt 1: Export vorbereiten

**Ziel:** Ausgabeverzeichnis erstellen und validieren

```powershell
# Exportverzeichnis erstellen
New-Item -ItemType Directory -Force -Path "exports\tsv"
New-Item -ItemType Directory -Force -Path "exports\wpl"

# Dry-Run zur Validierung (keine Dateien schreiben)
python "LOKAL\01 - Add New Transcriptions\03 update DB\blacklab_index_creation.py" --dry-run
```

**Erwartetes Ergebnis:**
```
📁 Found 150 JSON files in 20 countries (deterministic order)
📊 Processing 150 files...
  [DRY-RUN] Would write 5234 tokens to ARG_2023-08-10_ARG_Mitre.tsv
    Sample (first 3 rows):
      5    5    5    NUM
      de   de   de   ADP
      la   la   el   DET
  ✅ [1/150] 2023-08-10_ARG_Mitre.json - 5234 tokens
  ...
✅ Dry run complete! No files written.
```

**Falls Fehler auftreten:**
- `Missing required field: token_id` → Führe `annotation_json_in_media_v2.py` zuerst aus
- `Missing required field: speaker_code` → Führe `migrate_speakers_to_codes.py` zuerst aus

---

### Schritt 2: TSV-Export ausführen

**Ziel:** TSV-Dateien für BlackLab erstellen (empfohlenes Format)

```powershell
# TSV-Export (eine .tsv pro Transkript)
python "LOKAL\01 - Add New Transcriptions\03 update DB\blacklab_index_creation.py" `
  --root "media\transcripts" `
  --out "exports\tsv" `
  --docmeta "exports\docmeta.jsonl" `
  --format tsv
```

**Erwartetes Ergebnis:**
```
CO.RA.PAN BlackLab Export
================================================================================
Format:      TSV
Input:       media\transcripts
Output:      exports\tsv
Doc Meta:    exports\docmeta.jsonl
Dry Run:     False
================================================================================

📊 Processing 150 files...
  ✅ [1/150] 2023-08-10_ARG_Mitre.json - 5,234 tokens
  ✅ [2/150] 2023-08-12_ARG_Mitre.json - 4,891 tokens
  ⏭️  [3/150] 2023-08-16_ARG_Mitre.json - SKIPPED (unchanged)
  ...

EXPORT SUMMARY
================================================================================
Created:       148 files
Skipped:       2 files (unchanged)
Errors:        0 files
Total Tokens:  750,000
================================================================================

✅ Export complete!
   Output: exports\tsv
   Metadata: exports\docmeta.jsonl
```

**Ausgabestruktur:**
```
exports/
├── tsv/
│   ├── ARG_2023-08-10_ARG_Mitre.tsv
│   ├── ARG_2023-08-12_ARG_Mitre.tsv
│   ├── ...
│   ├── .hash_cache.jsonl          # Idempotenz-Cache
│   └── export_errors.jsonl        # Falls Fehler (nur bei Problemen)
└── docmeta.jsonl                  # Dokument-Metadaten
```

**TSV-Format (Beispiel):**
```tsv
word    norm    lemma   pos past_type future_type tense mood person number aspect tokid start_ms end_ms sentence_id utterance_id speaker_code
5       5       5       NUM                                                         ARGcafb6f8ac 1410 1460 ARG_2023-08-10_ARG_Mitre:0:s0 ARG_2023-08-10_ARG_Mitre:0 lib-pm
de      de      de      ADP                                                         ARG18d57b966 1460 1570 ARG_2023-08-10_ARG_Mitre:0:s0 ARG_2023-08-10_ARG_Mitre:0 lib-pm
la      la      el      DET                         Sing                           ARGa55ac777e 1570 1620 ARG_2023-08-10_ARG_Mitre:0:s0 ARG_2023-08-10_ARG_Mitre:0 lib-pm
```

---

### Schritt 3: WPL-Export (Optional)

**Ziel:** WPL-Dateien mit hierarchischen Strukturen erstellen

**Nur verwenden wenn:**
- Du `within="sentence"` oder `within="utterance"` in CQL nutzen willst
- Du strukturbasierte Kontext-Anzeigen brauchst
- Du mit BlackLab-Strukturen vertraut bist

```powershell
# WPL-Export (mit <doc>, <utt>, <s> Tags)
python "LOKAL\01 - Add New Transcriptions\03 update DB\blacklab_index_creation.py" `
  --root "media\transcripts" `
  --out "exports\wpl" `
  --docmeta "exports\docmeta.jsonl" `
  --format wpl
```

**WPL-Format (Beispiel):**
```xml
<doc id="ARG_2023-08-10_ARG_Mitre">
<utt id="ARG_2023-08-10_ARG_Mitre:0" start_ms="1410" end_ms="2640" speaker_code="lib-pm">
<s id="ARG_2023-08-10_ARG_Mitre:0:s0" start_ms="1410" end_ms="1650">
5       word="5" norm="5" lemma="5" pos="NUM" tokid="ARGcafb6f8ac" start_ms="1410" end_ms="1460" ...
de      word="de" norm="de" lemma="de" pos="ADP" tokid="ARG18d57b966" start_ms="1460" end_ms="1570" ...
</s>
<s id="ARG_2023-08-10_ARG_Mitre:0:s1" start_ms="1680" end_ms="2400">
Horacio word="Horacio" norm="horacio" lemma="horacio" pos="PROPN" ...
</s>
</utt>
</doc>
```

---

### Schritt 4: BlackLab-Index erstellen

**Ziel:** Volltextindex mit allen Annotationen erstellen

#### 4a: Index-Verzeichnis vorbereiten

```powershell
# Erstelle leeres Index-Verzeichnis
New-Item -ItemType Directory -Force -Path "data\index\corapan"
```

#### 4b: Index mit TSV-Dateien erstellen

```powershell
# BlackLab IndexTool ausführen
java -jar blacklab.jar create `
  "data\index\corapan" `
  "exports\tsv\*.tsv" `
  corapan-tsv
```

**Parameter:**
- `create` – Neuen Index erstellen
- `data\index\corapan` – Zielverzeichnis für Index
- `exports\tsv\*.tsv` – Alle TSV-Dateien
- `corapan-tsv` – Name der Format-Konfiguration (`.blf.yaml` im selben Ordner)

**Erwartetes Ergebnis:**
```
BlackLab IndexTool v4.0
Indexing format: corapan-tsv
Processing: ARG_2023-08-10_ARG_Mitre.tsv (5,234 tokens)
Processing: ARG_2023-08-12_ARG_Mitre.tsv (4,891 tokens)
...
Indexed 148 documents, 750,000 tokens
Creating forward indexes...
Optimizing...
✅ Index created successfully!
```

#### 4c: Metadaten importieren

**Falls separate Metadaten-Datei:**

Konfiguriere in `blacklab-server.yaml`:

```yaml
indices:
  corapan:
    displayName: "CO.RA.PAN Corpus"
    indexPath: "data/index/corapan"
    metadata:
      documentFormat: jsonlines
      path: "exports/docmeta.jsonl"
```

---

### Schritt 5: Index-Validierung

**Ziel:** Prüfen ob alle Annotationen und Metadaten korrekt indiziert wurden

#### 5a: Annotations prüfen

```bash
# Liste alle Annotationen
curl "http://localhost:8080/blacklab-server/corapan/fields/contents"
```

**Erwartetes Ergebnis:**
```json
{
  "annotations": [
    {"name": "word", "sensitivity": "sensitive"},
    {"name": "norm", "sensitivity": "insensitive"},
    {"name": "lemma", "sensitivity": "sensitive"},
    {"name": "pos"},
    {"name": "tense"},
    {"name": "mood"},
    {"name": "tokid"},
    ...
  ]
}
```

#### 5b: Metadaten prüfen

```bash
# Liste alle Metadaten-Felder
curl "http://localhost:8080/blacklab-server/corapan/metadata"
```

**Erwartetes Ergebnis:**
```json
{
  "fields": [
    {"name": "file_id", "type": "text"},
    {"name": "country_code", "type": "text"},
    {"name": "date", "type": "text"},
    {"name": "radio", "type": "text"},
    ...
  ]
}
```

#### 5c: Stichproben-Suche

```bash
# Einfache Wortsuche (sensitiv)
curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[word=\"México\"]&number=5"

# Lemma-Suche mit POS-Filter
curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[lemma=\"cantar\" & pos=\"VERB\"]&number=5"

# Norm-Suche (indifferent)
curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[norm=\"mexico\"]&number=5"

# Morphologie-Suche (Verb in Präsens, Indikativ)
curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[pos=\"VERB\" & tense=\"Pres\" & mood=\"Ind\"]&number=5"
```

---

### Schritt 6: Quick-Tests

**Ziel:** Funktionalität aller Annotationen testen

#### Test 1: Sensitiv vs. Insensitiv

```bash
# SENSITIV (word): findet nur exakte Schreibung
curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[word=\"México\"]"
# → Trefferanzahl: z.B. 450

# INSENSITIV (norm): findet alle Varianten
curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[norm=\"mexico\"]"
# → Trefferanzahl: z.B. 520 (inkl. "méxico", "Mexico", "MÉXICO")
```

#### Test 2: Morphologie

```bash
# Verben im Perfecto Compuesto (past_type)
curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[past_type=\"PerfectoCompuesto\"]&number=10"

# Verben im Präsens Subjunktiv (morph)
curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[pos=\"VERB\" & tense=\"Pres\" & mood=\"Sub\"]&number=10"
```

#### Test 3: Kontext und Timing

```bash
# Treffer mit Token-IDs und Zeiten
curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[lemma=\"hablar\"]&listvalues=tokid,start_ms,end_ms&number=5"
```

**Erwartetes Ergebnis:**
```json
{
  "hits": [
    {
      "docPid": "ARG_2023-08-10_ARG_Mitre",
      "start": 123,
      "end": 124,
      "match": {"word": ["habla"]},
      "tokid": "ARGabc123def",
      "start_ms": 15430,
      "end_ms": 15680
    },
    ...
  ]
}
```

#### Test 4: Metadaten-Filter

```bash
# Nur Argentinien
curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[lemma=\"gobierno\"]&filter=country_code:ARG"

# Nur 2023
curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[lemma=\"gobierno\"]&filter=date:2023-*"

# Nur lib-pm Speaker (libre, politician, masculino)
curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[speaker_code=\"lib-pm\"]"
```

---

## Inkrementelle Updates

**Ziel:** Nur geänderte Dateien re-exportieren und re-indizieren

### Schritt 1: Export mit Hash-Cache

```powershell
# Export erneut ausführen (nutzt .hash_cache.jsonl)
python "LOKAL\01 - Add New Transcriptions\03 update DB\blacklab_index_creation.py" `
  --root "media\transcripts" `
  --out "exports\tsv"
```

**Erwartetes Ergebnis:**
```
📊 Processing 150 files...
  ⏭️  [1/150] 2023-08-10_ARG_Mitre.json - SKIPPED (unchanged)
  ⏭️  [2/150] 2023-08-12_ARG_Mitre.json - SKIPPED (unchanged)
  ✅ [3/150] 2023-08-16_ARG_Mitre.json - 4,567 tokens  # GEÄNDERT
  ✅ [4/150] 2025-11-09_ARG_Mitre.json - 5,123 tokens  # NEU
  ...

EXPORT SUMMARY
================================================================================
Created:       2 files
Skipped:       148 files (unchanged)
Errors:        0 files
================================================================================
```

### Schritt 2: Index aktualisieren

```powershell
# Geänderte Dokumente ersetzen (delete + add)
# Zuerst: alte Version löschen
java -jar blacklab.jar delete `
  "data\index\corapan" `
  "file_id:ARG_2023-08-16_ARG_Mitre"

# Dann: neue Version hinzufügen
java -jar blacklab.jar add `
  "data\index\corapan" `
  "exports\tsv\ARG_2023-08-16_ARG_Mitre.tsv" `
  corapan-tsv

# Neue Dateien direkt hinzufügen
java -jar blacklab.jar add `
  "data\index\corapan" `
  "exports\tsv\ARG_2025-11-09_ARG_Mitre.tsv" `
  corapan-tsv
```

---

## Validierung

**Wie prüft man, dass alles funktioniert hat?**

### Check 1: Dateianzahl

```powershell
# TSV-Dateien zählen
(Get-ChildItem "exports\tsv\*.tsv").Count
# Erwartung: 148 (=Anzahl JSON-Dateien)

# Index-Dokumente zählen
curl "http://localhost:8080/blacklab-server/corapan/docs?number=0" | jq '.summary.numberOfDocs'
# Erwartung: 148
```

### Check 2: Token-Anzahl

```powershell
# Token in Export
Get-Content "exports\tsv\ARG_2023-08-10_ARG_Mitre.tsv" | Measure-Object -Line
# Erwartung: 5235 (Header + 5234 Tokens)

# Token in Index
curl "http://localhost:8080/blacklab-server/corapan/" | jq '.tokenCount'
# Erwartung: ~750,000
```

### Check 3: Annotation-Coverage

```bash
# Teste ob alle Annotationen befüllt sind
curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[norm=\".*\"]&number=100" | jq '.summary.numberOfHits'
# Erwartung: >0 (norm ist nie leer bei validen Tokens)

curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[lemma=\".*\"]&number=100" | jq '.summary.numberOfHits'
# Erwartung: >0
```

### Check 4: Stichprobe (manuell)

1. Öffne `exports/tsv/ARG_2023-08-10_ARG_Mitre.tsv` in Excel/LibreOffice
2. Prüfe Zeile 10:
   - Sind alle Spalten befüllt? (außer morph bei PUNCT/NUM)
   - Ist `tokid` eindeutig?
   - Ist `start_ms` < `end_ms`?
3. Suche in BlackLab nach diesem Token:
   ```bash
   curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[tokid=\"<TOKEN_ID>\"]"
   ```
4. Vergleiche Annotationen: JSON ↔ TSV ↔ BlackLab

---

## Rollback

**Wie macht man es rückgängig?**

### Export rückgängig

```powershell
# Export-Verzeichnis löschen
Remove-Item -Recurse -Force "exports\tsv"

# Hash-Cache löschen (für kompletten Re-Export)
Remove-Item -Force "exports\tsv\.hash_cache.jsonl"
```

### Index rückgängig

```powershell
# Index komplett löschen
Remove-Item -Recurse -Force "data\index\corapan"

# Oder: einzelne Dokumente entfernen
java -jar blacklab.jar delete `
  "data\index\corapan" `
  "file_id:ARG_2023-08-10_ARG_Mitre"
```

---

## Troubleshooting

### Problem 1: `Missing required field: token_id`

**Symptom:**
```
❌ [5/150] 2023-08-10_ARG_Mitre.json - INVALID: Missing required field: token_id
```

**Ursache:** JSON nicht mit `annotation_json_in_media_v2.py` annotiert

**Lösung:**
```powershell
python "LOKAL\01 - Add New Transcriptions\01 annotation\annotation_json_in_media_v2.py" safe
```

---

### Problem 2: `Missing required field: speaker_code`

**Symptom:**
```
❌ [8/150] 2023-08-12_ARG_Mitre.json - INVALID: Missing required field: speaker_code
```

**Ursache:** Alte JSON-Struktur mit `speakers[]` Array

**Lösung:**
```powershell
python "LOKAL\01 - Add New Transcriptions\02 preprocessing\migrate_speakers_to_codes.py"
```

---

### Problem 3: BlackLab findet keine Treffer

**Symptom:**
```bash
curl "http://localhost:8080/blacklab-server/corapan/hits?patt=[lemma=\"hablar\"]"
# → "numberOfHits": 0
```

**Diagnose:**

1. Prüfe ob Annotation existiert:
   ```bash
   curl "http://localhost:8080/blacklab-server/corapan/fields/contents"
   # Ist "lemma" in der Liste?
   ```

2. Prüfe TSV-Datei:
   ```powershell
   Get-Content "exports\tsv\ARG_2023-08-10_ARG_Mitre.tsv" | Select-Object -First 5
   # Ist "lemma" Spalte befüllt?
   ```

3. Prüfe Format-Config:
   ```yaml
   # corapan-tsv.blf.yaml
   - name: lemma
     valuePath: lemma  # MUSS mit TSV-Spaltenname übereinstimmen
   ```

**Lösung:**
- Format-Config korrigieren und Index neu erstellen

---

### Problem 4: Index extrem langsam

**Symptom:** Indizierung dauert >10 Minuten für 150 Dateien

**Ursachen:**
- Zu wenig RAM
- Forward-Indexes nicht konfiguriert
- Disk-IO-Probleme

**Lösung:**

1. Mehr RAM für Java:
   ```powershell
   java -Xmx4G -jar blacklab.jar create ...
   ```

2. Forward-Indexes prüfen (in `.blf.yaml`):
   ```yaml
   annotations:
     - name: lemma
       forwardIndex: true  # MUSS true sein für Aggregationen
   ```

3. SSD verwenden statt HDD

---

### Problem 5: Metadaten fehlen in BlackLab

**Symptom:**
```bash
curl "http://localhost:8080/blacklab-server/corapan/docs/ARG_2023-08-10_ARG_Mitre"
# → "country_code": null
```

**Ursache:** `docmeta.jsonl` nicht importiert

**Lösung:**

1. Prüfe `blacklab-server.yaml`:
   ```yaml
   indices:
     corapan:
       metadata:
         documentFormat: jsonlines
         path: "exports/docmeta.jsonl"  # Pfad korrekt?
   ```

2. Prüfe `docmeta.jsonl`:
   ```powershell
   Get-Content "exports\docmeta.jsonl" | Select-Object -First 3
   ```

3. BlackLab-Server neu starten

---

## Performance-Tipps

### Tip 1: Parallel-Export (zukünftig)

```powershell
# Mit --workers Flag (noch nicht implementiert)
python blacklab_index_creation.py --workers 4
```

### Tip 2: Partielle Exports

```powershell
# Nur ein Land exportieren (manuell)
python blacklab_index_creation.py --root "media\transcripts\ARG" --out "exports\tsv_arg"
```

### Tip 3: Index-Optimierung

```powershell
# Nach großen Updates: Index optimieren
java -jar blacklab.jar optimize "data\index\corapan"
```

---

## Siehe auch

- [BlackLab Configuration Reference](../reference/blacklab-configuration.md) - Detaillierte `.blf.yaml` Optionen
- [Corpus Search Architecture](../concepts/corpus-search-architecture.md) - Gesamtarchitektur
- [JSON Annotation v2 Guide](../../JSON_ANNOTATION_V2_DOCUMENTATION_INDEX.md) - JSON-Format-Spezifikation
- [BlackLab Official Docs](https://inl.github.io/BlackLab/) - Externe BlackLab-Dokumentation
