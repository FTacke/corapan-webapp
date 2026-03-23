# JSON-Pipeline für CO.RA.PAN

Vollständige Pipeline zur Verarbeitung von JSON-Transkripten: Preprocessing → Annotation → Statistik-Datenbanken → Statistik-Generierung → Web-Publikation.

---

## Übersicht

Die Pipeline besteht aus **fünf Skripten** plus einem **QA-Skript**, die nacheinander ausgeführt werden:

| # | Skript | Aufgabe | Input | Output |
|---|--------|---------|-------|--------|
| 01 | `01_preprocess_transcripts.py` | Bereinigung & Speaker-Migration | `json-pre/*.json` | `json-ready/*.json` |
| 02 | `02_annotate_transcripts_v3.py` | spaCy-Annotation & Token-IDs | `media/transcripts/<country>/*.json` | (in-place) |
| 03 | `03_build_metadata_stats.py` | Statistik-Datenbanken | `media/transcripts/<country>/*.json` | `data/db/*.db` |
| 04 | `04_internal_country_statistics.py` | Corpus-Statistiken (CSV) | `media/transcripts/<country>/*.json` | `results/*.csv` |
| 05 | `05_publish_corpus_statistics.py` | Web-Visualisierungen | `results/*.csv` | `static/img/statistics/` |
| 99 | `99_check_pipeline_json.py` | QA/Regression-Tests | alle Outputs | Report (Console + JSON) |

### Pipeline-Diagramm

```
json-pre/*.json
      │
      ▼ [01 preprocess]
json-ready/*.json
      │
      ▼ (manuell kopieren)
media/transcripts/<country>/*.json
      │
      ├──▶ [02 annotate] ──▶ (in-place annotation)
      │
      ├──▶ [03 metadata] ──▶ data/db/*.db
      │
      └──▶ [04 statistics] ──▶ results/*.csv
                                    │
                                    ▼ [05 publish]
                          static/img/statistics/
                                    │
                                    ▼ [99 QA check]
                          99_check_pipeline_report.json
```

### Wichtige Änderungen (v3)

- ✅ **Zeiten in Millisekunden**: `start_ms`, `end_ms` (int) statt `start`, `end` (float)
- ✅ **Englische Tense-Labels**: `morph.PastType`, `morph.FutureType`
- ✅ **Deterministische Token-IDs**: MD5-Hash-basiert
- ✅ **Schema-Version**: `corapan-ann/v3`
- ✅ **JSON-basierte Statistiken**: Direkt aus JSON, keine `transcription.db`
- ❌ **Keine `transcription.db`**: Token-Suche erfolgt über BlackLab

---

## Schritt-für-Schritt Workflow

### 1. Preprocessing (01)

**Zweck**: Bereinigte, standardisierte JSONs für die Annotation vorbereiten.

#### Vorbereitung

```bash
# Roh-JSONs in json-pre/ ablegen
LOKAL/_1_json/json-pre/
├── 2023-08-10_ARG_Mitre.json
├── 2023-08-12_ARG_Mitre.json
└── ...
```

#### Ausführung

```bash
cd LOKAL/_1_json
python 01_preprocess_transcripts.py
```

**Optionen:**

| Flag | Beschreibung |
|------|--------------|
| `--limit N` | Nur N Dateien verarbeiten |
| `--strict` | Abbruch bei Validierungsfehlern |
| `--input DIR` | Alternatives Eingabeverzeichnis |
| `--output DIR` | Alternatives Ausgabeverzeichnis |
| `--verbose` | Ausführliche Ausgabe |

#### Was passiert?

1. **Felder entfernen**: `duration`, `conf`, `pristine`
2. **Self-Corrections bereinigen**: `-,` und `-.` → `-`
3. **Fremdwörter markieren**: `(foreign)` → `foreign="1"`
4. **Speaker-Migration**: `speakers[]` + `segment.speaker` → `segment.speaker_code`

#### Ausgabe

```bash
LOKAL/_1_json/json-ready/
├── 2023-08-10_ARG_Mitre.json
├── 2023-08-12_ARG_Mitre.json
└── ...
```

---

### 2. Dateien übertragen

**Manueller Schritt**: Bereinigte JSONs ins Transkript-Verzeichnis kopieren.

```bash
# Beispiel für Argentinien
cp LOKAL/_1_json/json-ready/*.json media/transcripts/ARG/
```

**Verzeichnisstruktur:**

```
media/transcripts/
├── ARG/
│   ├── 2023-08-10_ARG_Mitre.json
│   └── ...
├── CHL/
├── ESP/
└── ...
```

> **Wichtig**: Der Ordnername muss dem Ländercode entsprechen (z.B. `ARG`, `ESP`, `CHL`).

---

### 3. Annotation (02)

**Zweck**: Vollständige linguistische Annotation mit spaCy und Token-ID-Generierung.

#### Ausführung

```bash
cd LOKAL/_1_json

# Alle Dateien annotieren
python 02_annotate_transcripts_v3.py

# Nur ein Land
python 02_annotate_transcripts_v3.py --country ARG

# Force-Modus (alles neu)
python 02_annotate_transcripts_v3.py --force

# Dry-Run (nur Simulation)
python 02_annotate_transcripts_v3.py --dry-run --limit 5
```

**Optionen:**

| Flag | Beschreibung |
|------|--------------|
| `--country XX` | Nur Land XX verarbeiten |
| `--force` | Alle Dateien neu annotieren (ignoriere Idempotenz) |
| `--dry-run` | Keine Änderungen schreiben |
| `--limit N` | Nur N Dateien annotieren |
| `--skip-token-ids` | Token-ID-Generierung überspringen |
| `--verbose` | Ausführliche Ausgabe |

#### Was passiert?

1. **Token-ID-Generierung** (deterministisch, MD5-basiert)
2. **Zeitkonvertierung**: `start`/`end` (float) → `start_ms`/`end_ms` (int)
3. **Normalisierung**: `norm` für akzent-/case-indifferente Suche
4. **spaCy-Annotation**: `pos`, `lemma`, `dep`, `head_text`, `morph`
5. **Zeitformen-Erkennung**: `morph.PastType`, `morph.FutureType`
6. **Satz-/Utterance-IDs**: `sentence_id`, `utterance_id`
7. **Metadaten**: `ann_meta.version`, `ann_meta.text_hash`, etc.

#### Idempotenz

Das Skript ist **idempotent** im Safe-Modus:

- Prüft `ann_meta.version` und `ann_meta.text_hash`
- Überspringt bereits annotierte Dateien
- Mit `--force` werden alle Dateien neu annotiert

---

### 4. Statistik-Datenbanken (03)

**Zweck**: Metadaten-Datenbanken für die Webapp erstellen.

#### Ausführung

```bash
cd LOKAL/_1_json

# Alle Datenbanken neu erstellen
python 03_build_metadata_stats.py --rebuild

# Nur ein Land
python 03_build_metadata_stats.py --country ARG

# Nur verifizieren
python 03_build_metadata_stats.py --verify-only
```

**Optionen:**

| Flag | Beschreibung |
|------|--------------|
| `--rebuild` | Datenbanken neu erstellen (Standard) |
| `--country XX` | Nur Land XX verarbeiten |
| `--verify-only` | Nur Datenbanken prüfen |
| `--verbose` | Ausführliche Ausgabe |

#### Ausgabedateien

| Datei | Inhalt |
|-------|--------|
| `data/db/public/stats_country.db` | Statistiken pro Land |
| `data/db/public/stats_files.db` | Metadaten pro Datei |

> **Hinweis**: `transcription.db` wird **nicht mehr erstellt**!
> Die Token-Suche erfolgt über BlackLab direkt aus den JSONs.

---

### 5. Interne Statistiken (04)

**Zweck**: Detaillierte Corpus-Statistiken als CSV-Dateien generieren.

#### Ausführung

```bash
cd LOKAL/_1_json

# Alle Länder verarbeiten
python 04_internal_country_statistics.py

# Nur bestimmte Länder
python 04_internal_country_statistics.py --country ARG,ESP,MEX

# Mit Limit (für Tests)
python 04_internal_country_statistics.py --country ARG --limit 5
```

**Optionen:**

| Flag | Beschreibung |
|------|--------------|
| `--country XX,YY` | Komma-separierte Ländercodes (default: alle) |
| `--limit N` | Nur N Dateien pro Land verarbeiten |

#### Was passiert?

1. **JSON-Dateien laden** aus `media/transcripts/<country>/`
2. **Tokens aggregieren** nach Speaker-Typ, Geschlecht, Modus
3. **Statistiken berechnen**: Wortanzahl, Dauer pro Kategorie
4. **CSV-Dateien generieren**:
   - `corpus_statistics.csv` - Pro Land, pro Kategorie
   - `corpus_statistics_across_countries.csv` - Länderübergreifend
   - `gender_gap_analysis.csv` - Gender-Analyse
5. **Visualisierungen erstellen**:
   - `viz_<COUNTRY>_pro_modes.png` - Pro Land
   - `viz_ALL_COUNTRIES_pro_modes.png` - Gesamt
   - `viz_gender_gap_*.png` - Gender-Gap-Analysen

#### Ausgabedateien

| Datei | Inhalt |
|-------|--------|
| `results/corpus_statistics.csv` | Statistiken pro Land/Kategorie |
| `results/corpus_statistics_across_countries.csv` | Aggregierte Statistiken |
| `results/gender_gap_analysis.csv` | Gender-Gap pro Land |
| `results/viz_*.png` | Visualisierungen |
| `results/summary_report.txt` | Zusammenfassung |

---

### 6. Web-Publikation (05)

**Zweck**: Visualisierungen und JSON-Daten für die Webapp generieren.

#### Ausführung

```bash
cd LOKAL/_1_json

# Web-Statistiken publizieren
python 05_publish_corpus_statistics.py
```

**Keine Optionen** - das Skript verwendet fest definierte Pfade.

#### Was passiert?

1. **CSV-Dateien laden** aus `results/`
2. **Statistiken aggregieren** für Web-Darstellung
3. **Visualisierungen erstellen**:
   - `viz_total_corpus.png` - Gesamtübersicht
   - `viz_genero_profesionales.png` - Gender-Verteilung
   - `viz_modo_genero_profesionales.png` - Modus × Gender
   - `viz_<COUNTRY>_resumen.png` - Länder-Zusammenfassungen
4. **JSON exportieren**: `corpus_stats.json`

#### Ausgabedateien

| Datei | Inhalt |
|-------|--------|
| `static/img/statistics/viz_total_corpus.png` | Corpus-Gesamt |
| `static/img/statistics/viz_genero_profesionales.png` | Gender-Verteilung |
| `static/img/statistics/viz_modo_genero_profesionales.png` | Modus × Gender |
| `static/img/statistics/viz_<COUNTRY>_resumen.png` | Länder-Übersichten |
| `static/img/statistics/corpus_stats.json` | JSON-API für Web |

---

### 7. QA-Tests (99)

**Zweck**: Automatisierte Regression-Tests für die gesamte Pipeline.

#### Ausführung

```bash
cd LOKAL/_1_json

# Vollständiger Test (alle Steps ausführen)
python 99_check_pipeline_json.py --country ARG --limit 2

# Nur Checks ausführen (ohne Pipeline-Steps)
python 99_check_pipeline_json.py --skip-steps

# Bestimmte Steps überspringen
python 99_check_pipeline_json.py --skip-step 01 --skip-step 02 --continue-on-error

# Mit Fehlertoleranz
python 99_check_pipeline_json.py --continue-on-error
```

**Optionen:**

| Flag | Beschreibung |
|------|--------------|
| `--country XX` | Land für Tests (default: auto-detect) |
| `--limit N` | Anzahl Dateien pro Step (default: 2) |
| `--skip-steps` | Keine Pipeline-Steps ausführen, nur Checks |
| `--skip-step NN` | Bestimmten Step überspringen (z.B. `--skip-step 01`) |
| `--continue-on-error` | Bei Fehlern weitermachen |

#### Durchgeführte Checks

| Check | Beschreibung |
|-------|--------------|
| **JSON Structure** | v3-Schema-Validierung (start_ms, speaker, etc.) |
| **DB vs JSON** | Wortanzahl-Konsistenz zwischen DB und JSON |
| **CSV Consistency** | TOTAL_ALL_COUNTRIES vs Summe der TOTALs |
| **Published Outputs** | Existenz und Konsistenz der Web-Outputs |

#### Ausgabedateien

| Datei | Inhalt |
|-------|--------|
| `99_check_pipeline_report.json` | Detaillierter JSON-Report |
| Console | `[OK]/[FAIL]` Status pro Check |

#### Exit Codes

| Code | Bedeutung |
|------|-----------|
| `0` | Alle Checks bestanden |
| `1` | Mindestens ein Check fehlgeschlagen |

---

## Schnellstart: Komplette Pipeline

```bash
cd LOKAL/_1_json

# 1. Preprocessing (wenn neue Roh-JSONs)
python 01_preprocess_transcripts.py

# 2. Manuell: json-ready → media/transcripts/<country>/

# 3. Annotation
python 02_annotate_transcripts_v3.py

# 4. Metadaten-Datenbanken
python 03_build_metadata_stats.py --rebuild

# 5. Interne Statistiken
python 04_internal_country_statistics.py

# 6. Web-Publikation
python 05_publish_corpus_statistics.py

# 7. QA-Check (optional)
python 99_check_pipeline_json.py --skip-steps
```

---

## BlackLab-Integration

Nach der Annotation können die JSONs direkt von BlackLab indiziert werden:

```bash
# BlackLab-Indexierung (separate Dokumentation)
# Die annotierten JSONs im v3-Format sind BlackLab-kompatibel
```

---

## v3-Schema Referenz

### Token-Felder (Pflicht)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `token_id` | string | Eindeutige ID (z.B. `ARG12345abcd`) |
| `sentence_id` | string | Satz-ID (z.B. `ARG_2023-08-10:0:s0`) |
| `utterance_id` | string | Utterance-ID (z.B. `ARG_2023-08-10:0`) |
| `start_ms` | int | Startzeit in Millisekunden |
| `end_ms` | int | Endzeit in Millisekunden |
| `text` | string | Original-Text |
| `lemma` | string | Lemma |
| `pos` | string | Part-of-Speech |
| `dep` | string | Dependency-Relation |
| `morph` | object | Morphologische Features |
| `norm` | string | Normalisierte Suchform |

### Segment-Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `speaker_code` | string | Speaker-Code (z.B. `lib-pm`) |
| `utt_start_ms` | int | Utterance-Startzeit in ms |
| `utt_end_ms` | int | Utterance-Endzeit in ms |

### Tense-Labels (morph)

**PastType:**
- `simplePast` - Perfecto Simple
- `presentPerfect` - Perfecto Compuesto
- `pastPerfect` - Pluscuamperfecto
- `futurePerfect` - Futuro Perfecto
- `conditionalPerfect` - Condicional Perfecto
- `otherCompoundPast` - Andere zusammengesetzte Form
- `otherPast` - Andere Vergangenheitsform

**FutureType:**
- `periphrasticFuture` - "ir a + Inf" (Präsens)
- `periphrasticFuturePast` - "ir a + Inf" (Imperfekt)

### ann_meta

```json
{
  "ann_meta": {
    "version": "corapan-ann/v3",
    "spacy_model": "es_dep_news_trf",
    "text_hash": "abc123...",
    "timestamp": "2025-12-09T10:30:00+00:00",
    "required": ["token_id", "sentence_id", ...],
    "speaker_code_migrated": true,
    "speaker_migration_timestamp": "2025-12-09T10:00:00+00:00"
  }
}
```

---

## Erlaubte Speaker-Codes

| Code | Typ | Geschlecht | Modus | Diskurs |
|------|-----|------------|-------|---------|
| `lib-pm` | pro | m | libre | general |
| `lib-pf` | pro | f | libre | general |
| `lib-om` | otro | m | libre | general |
| `lib-of` | otro | f | libre | general |
| `lec-pm` | pro | m | lectura | general |
| `lec-pf` | pro | f | lectura | general |
| `lec-om` | otro | m | lectura | general |
| `lec-of` | otro | f | lectura | general |
| `pre-pm` | pro | m | pre | general |
| `pre-pf` | pro | f | pre | general |
| `tie-pm` | pro | m | n/a | tiempo |
| `tie-pf` | pro | f | n/a | tiempo |
| `traf-pm` | pro | m | n/a | tránsito |
| `traf-pf` | pro | f | n/a | tránsito |
| `foreign` | n/a | n/a | n/a | foreign |
| `none` | - | - | - | - |

---

## Fehlerbehebung

### Problem: "Keine JSON-Dateien gefunden"

**Ursache**: Falscher Pfad oder leeres Verzeichnis.

**Lösung**:
```bash
# Prüfe json-pre/
ls LOKAL/_1_json/json-pre/

# Prüfe media/transcripts/
ls media/transcripts/ARG/
```

### Problem: "spaCy-Modell nicht gefunden"

**Ursache**: `es_dep_news_trf` nicht installiert.

**Lösung**:
```bash
python -m spacy download es_dep_news_trf
```

### Problem: "Hash prefix exceeded 16 hex characters"

**Ursache**: Token-ID-Kollision (sehr unwahrscheinlich).

**Lösung**: Kontaktiere Support, dies sollte nicht passieren.

### Problem: "Unbekannte Speaker-Codes"

**Symptom**: Warnung "Nicht erlaubte Speaker-Codes → auf 'none' gesetzt"

**Lösung**: Speaker-Codes im Quell-JSON anpassen oder `ALLOWED_SPEAKER_CODES` erweitern.

### Problem: "NaN values in CSV"

**Ursache**: Fehlende Kategorien in den Quelldaten.

**Lösung**: Die Skripte behandeln NaN-Werte automatisch. Bei persistenten Problemen: QA-Skript ausführen.

---

## Dateistruktur

```
LOKAL/_1_json/
├── 01_preprocess_transcripts.py    # [01] Preprocessing
├── 02_annotate_transcripts_v3.py   # [02] Annotation
├── 03_build_metadata_stats.py      # [03] Statistik-DBs
├── 04_internal_country_statistics.py # [04] Interne Statistiken
├── 05_publish_corpus_statistics.py # [05] Web-Publikation
├── 99_check_pipeline_json.py       # [99] QA-Tests
├── README-pipeline_json.md         # Diese Dokumentation
│
├── json-pre/                       # Input: Roh-JSONs
│   └── *.json
├── json-ready/                     # Output Step 01: Bereinigte JSONs
│   └── *.json
├── results/                        # Output Step 04: Statistiken
│   ├── corpus_statistics.csv
│   ├── corpus_statistics_across_countries.csv
│   ├── gender_gap_analysis.csv
│   ├── viz_*.png
│   └── summary_report.txt
│
# Ausgaben außerhalb von LOKAL/_1_json:
# ├── media/transcripts/<country>/  # Annotierte JSONs
# ├── data/db/*.db                  # Statistik-Datenbanken
# └── static/img/statistics/        # Web-Visualisierungen
│
# Alte Skripte (nicht mehr verwenden):
├── preprocess_json.py              # ❌ DEPRECATED
├── annotation_json_in_media_v3.py  # ❌ DEPRECATED
└── database_creation_v3.py         # ❌ DEPRECATED
```

---

## Anforderungen

- **Python**: >= 3.10
- **spaCy**: mit Modell `es_dep_news_trf`
- **pandas**: für CSV-Verarbeitung und Statistiken
- **matplotlib**: für Visualisierungen
- **Pakete**: `argparse`, `json`, `hashlib`, `unicodedata`, `sqlite3` (stdlib)

### Installation

```bash
# Virtual Environment aktivieren
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\Activate.ps1  # Windows

# Abhängigkeiten installieren
pip install pandas matplotlib

# spaCy-Modell installieren
python -m spacy download es_dep_news_trf
```

---

## Aktuelle Corpus-Statistiken

Stand: Dezember 2025

| Metrik | Wert |
|--------|------|
| **Länder** | 25 |
| **JSON-Dateien** | 146 |
| **Tokens (gesamt)** | 1.488.019 |
| **Tokens (ohne Punkt.)** | 1.464.768 |
| **Gesamtdauer** | ~134 Stunden |

---

## Kontakt

Bei Fragen oder Problemen: siehe [CONTRIBUTING.md](../../CONTRIBUTING.md)
