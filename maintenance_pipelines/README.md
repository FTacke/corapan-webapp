# CO.RA.PAN-Tools Übersicht

Dieses Repository enthält Tools zur Datenverarbeitung und Analyse des CO.RA.PAN-Korpus.
Die bearbeiteten Daten sind Transkriptionen gesprochener Sprache in Form von JSON-Dateien, die eine detaillierte Segmentierung in Sprechersegmente und Wörter mit linguistischen Annotationen (POS, Lemma, Morphologie) aufweisen. JSON als Format ermöglicht eine flexible, hierarchische und erweiterbare Struktur, die sich besonders gut eignet, um sprachliche Daten mit vielfältigen Informationen anzureichern und maschinell auszuwerten.
Das Repository umfasst ausschließlich Python-Skripte, die für die Aufbereitung, Verarbeitung und Auswertung der sprachlichen Daten entwickelt wurden.

## Inhalt

Python-Skripte zur Datenverarbeitung, Annotation, Datenbankverwaltung und Analyse.
Keine Rohdaten oder Analyseergebnisse (CSV, PNG, DOCX) sind im Repository enthalten, diese werden separat verwaltet.

## CO.RA.PAN-Korpora

Das CO.RA.PAN-Projekt umfasst zwei Korpora:

### Full Corpus (Restricted)
Vollständiges Korpus mit Audio- und Transkriptionsdaten. Zugriff nur auf Anfrage.
DOI: https://doi.org/10.5281/zenodo.15360942

### Sample Corpus (Public)
Öffentliches Beispielkorpus mit ausgewählten Audios und JSON-Daten.
DOI: https://doi.org/10.5281/zenodo.15378479

Das Full Corpus wird von der CO.RA.PAN-Webapp genutzt und ist nicht Teil dieses Repository.

## Ziel

Die Tools dienen der Vorbereitung, Analyse und Auswertung des CO.RA.PAN-Korpus, um linguistische Fragestellungen zu untersuchen.
Das Repository ist als Ergänzung zur CO.RA.PAN-Webapp konzipiert, die die Daten visualisiert und zugänglich macht.

## Projektstruktur

```
01 - Add New Transcriptions/
├── NEW JSON INTEGRATION_CHECKLIST.md
├── 01 preprocess JSON/
│   ├── preprocess_json.py          # Vorverarbeitung von JSON-Dateien (Bereinigung, Backup)
│   ├── json-backup/                # Automatische Backups
│   └── json-pre/                   # Verarbeitete JSON-Dateien
├── 02 annotate JSON/
│   └── annotation_json_in_media.py # Linguistische Annotation mit spaCy
├── 03 update DB/
│   ├── database_creation_v2.py     # Erstellung/Update von SQLite-Datenbanken
│   └── __pycache__/
├── 04 update full corpus in Zenodo-Repo/
│   ├── zenodo_corpus_zip.py        # ZIP-Erstellung für Zenodo-Upload
│   ├── zenodo_description_README.md
│   └── ZIPs/                       # Erstellte ZIP-Dateien
├── 05 update internal_country_statistics/
│   ├── internal_country_statistics.py # Korpus-Statistiken pro Land
│   └── results/                    # CSV-Ergebnisse und Berichte
└── 06 publish corpus statistics/
    ├── publish_corpus_statistics.py # Öffentliche Statistiken und Visualisierungen
    └── static/
        └── img/                    # Statische Bilder

02 - Add New Users (Security)/
├── hash_passwords_v2.py            # Passwort-Hashing für Benutzerkonten
└── README.md

03 - Analysis Scripts (tense)/
├── analysis_tenses.py              # Analyse von Zeitformen (Futur/Pasado)
├── analysis_tenses_make_tidy.py    # Kombination der Analyseergebnisse
├── tenses_tidy.csv                 # Tidy CSV mit kombinierten Ergebnissen
├── alte Ergebnisse/                # Archivierte Analyseergebnisse
├── alte Scripte/                   # Archivierte Skripte
└── [weitere CSV-Dateien]           # Analyseergebnisse pro Modus

records/ 
├── ⚠️ AUFGELÖST (2025-11-08)
├── Alle 97 Dokumentationen nach docs/ migriert
├── Struktur: docs/{design,reference,troubleshooting,archived}/
└── Verzeichnis gelöscht ✓
```
# CO.RA.PAN — LOKAL tools (processing & exports)

Dieses Git-Repository enthält die lokaleren Tools zur Datenvorverarbeitung, Annotation, Metadaten-Export,
Audio-Pipelines, Statistik-Generierung und Zenodo-Release-Tools für das CO.RA.PAN-Projekt.

Wichtig: Dieses Unter-Repository stellt nur die Verarbeitungs-Tools bereit — Rohdaten
(Audio/JSON) sowie die erzeugten Artefakte (CSV, PNG, ZIP) liegen außerhalb des Git-Tracking (oder werden
nur als Release-/Zenodo-Artefakte abgelegt).

## Kurzübersicht (aktuelle Organisation)

Top-level (LOKAL/) enthält mehrere funktionale Bereiche:

- `_0_mp3/` — MP3-Vorverarbeitung & Splitting (ffmpeg required)
- `_0_json/` — Vollständige JSON-Processing-Pipeline (01–05) + QA (99)
- `_1_blacklab/` — Hilfs-Runner für BlackLab-Export (ruft intern src.scripts)
- `_1_metadata/` — Metadaten-Export (TSV, JSON-LD, TEI headers)
- `_1_zenodo-repos/` — Tools zum Packaging / ZIP-Erstellung für Zenodo-Releases
- `_3_analysis_on_json/` — Explorative / research-spezifische Analysen (nicht Teil der Webapp-pipeline)

## Wichtige Skripte (kurze Beschreibung)

LOKAL/_0_json — die neue, JSON-basierte Pipeline (vollständig überarbeitet):

| Nr | Skript | Aufgabe |
|----|--------|---------|
| 01 | `01_preprocess_transcripts.py` | Bereinigung / Standardisierung der Roh-JSONs (json-pre → json-ready)
| 02 | `02_annotate_transcripts_v3.py` | spaCy Annotation, Token-IDs, v3-Schema (in-place, media/transcripts/<country>)
| 03 | `03_build_metadata_stats.py` | Erzeugt Metadaten DBs (data/db/public/stats_country.db, data/db/public/stats_files.db)
| 04 | `04_internal_country_statistics.py` | Berechnet detaillierte Statistiken pro Land, CSVs & lokale Viz (results/)
| 05 | `05_publish_corpus_statistics.py` | Publiziert Web-Grafiken & `corpus_stats.json` (static/img/statistics/)
| 99 | `99_check_pipeline_json.py` | QA/Regression: Führe Steps 01–05 durch (oder prüfe vorhandene Outputs)

Der Pipeline-Workflow ist dokumentiert im Datei: `_0_json/README-pipeline_json.md` — bitte dort für Detail-Anweisungen zu Flags, Dateipfaden und Troubleshooting nachsehen.

### Weitere Bereiche

_0_mp3 — Audio bereinigen / normalisieren / splitten
 - `mp3_prepare_and_split.py` — CBR-Konvertierung, LUFS-Normalisierung, Segmentierung in 4-minütige Chunks
 - Anforderungen: `pydub`, `eyed3`, und system-weites `ffmpeg` installiert.

_1_blacklab — BlackLab export runner
 - `blacklab_export.py` — ruft das interne Modul `src.scripts.blacklab_index_creation` auf und erzeugt TSVs / docmeta für Indexing

_1_metadata — Metadaten export
 - `export_metadata.py` — Erzeugt TSV/JSON/JSON-LD/TEI Dateien für Zenodo-Releases und Metadaten-Pakete

_1_zenodo-repos — Paketierung für Zenodo
 - `zenodo_full-corpus.py`, `zenodo_metadata.py` — ZIP-Erstellung, Kopieren aktueller Metadaten ins Release-Verzeichnis

_3_analysis_on_json — Explorative Analysen (nicht verändert bei der Umstrukturierung)

## Anforderungen (LOKAL-spezifisch)

Siehe `requirements-lokal.txt` in diesem Ordner — diese Datei enthält nur die Python-Pakete, die von den Tools in LOKAL benötigt werden.

Wichtige Systemanforderungen:
- `ffmpeg` (für pydub-gestützte Audioverarbeitung) — muss systemweit installiert sein und in PATH liegen.
- spaCy-Modelle (z.B. `es_dep_news_trf`) müssen separat installiert werden (siehe `requirements-lokal.txt` für das empfohlene Modell-wheel).

## Schnellstart - typische Reihenfolge zur Erzeugung veröffentlichter Artefakte

1. (Optional) Roh-Audio vorbereiten: `_0_mp3/mp3_prepare_and_split.py`
2. JSON Preprocessing: `_0_json/01_preprocess_transcripts.py` → `json-ready/`
3. Manuell: `json-ready/*.json` → `media/transcripts/<country>/`
4. Annotation: `_0_json/02_annotate_transcripts_v3.py` (oder mit `--country`/`--force`)
5. Metadaten-Datenbanken: `_0_json/03_build_metadata_stats.py --rebuild`
6. Interne Statistiken (CSV + local visuals): `_0_json/04_internal_country_statistics.py`
7. Web-Publikation: `_0_json/05_publish_corpus_statistics.py` → `static/img/statistics/` + `corpus_stats.json`
8. QA / Regression: `_0_json/99_check_pipeline_json.py` (prüft alle Outputs, generiert JSON-Report)

## Hinweise zur Pflege

- Alle Skripte in LOKAL sind Python3-Module mit CLI-Flags; kommentierte Usage-Abschnitte befinden sich oben in jedem Skript.
- Analysen, Notebooks und experimentelle Werkzeuge sind in `_3_analysis_on_json/` isoliert und verändern Produktionsdaten nicht direkt.

## Kontakt / Support

Bei Fragen zur Pipeline, Modellen oder Fehlerbehebung: siehe [CONTRIBUTING.md](/CONTRIBUTING.md) und das Projekt-README im Repository-Root.

## Lizenz

Diese Tools stehen unter der MIT-Lizenz. Details siehe `LICENSE` im Projekt-Root.