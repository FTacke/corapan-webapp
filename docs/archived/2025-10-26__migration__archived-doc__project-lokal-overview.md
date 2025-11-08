# Projektübersicht LOKAL

Dieser Ordner enthält Skripte zur Datenverarbeitung der Sprachaufnahmen im Ordner `grabaciones`. Die Verarbeitung gliedert sich in drei Hauptbereiche:

---

## 1. Datenbankerstellung (`database`)

**Skript:** `database_creation.py`

- Liest alle JSON-Dateien im Ordner `grabaciones`.
- Erstellt und aktualisiert mehrere SQLite-Datenbanken:
  - `db_public/stats_all.db`: Gesamtwortzahl und Gesamtdauer aller Aufnahmen.
  - `db/stats_country.db`: Wortzahl und Dauer gruppiert nach Ländern.
  - `db/stats_files.db`: Metadaten pro Datei (Land, Radio, Datum, Revision, Wortzahl, Dauer).
  - `db/transcription.db`: Tabelle `tokens` mit Token-Informationen (Lemma, Kontext, Sprecherattribute).
  - `db/annotation_data.db`: Tabelle `annotations` mit linguistischen Annotationen und Fremdwörterkennzeichnung.
- Generiert eindeutige `token_id`s für Tokens und aktualisiert JSON-Dateien bei Bedarf.
- Nutzt JSON-Daten aus `grabaciones` als Datenquelle.

---

## 2. Annotation der Sprachdaten (`annotation`)

**Skript:** `annotation_grabaciones.py`

- Annotiert alle JSON-Dateien im Ordner `grabaciones` (relativ zwei Ebenen über dem Skript).
- Teilt Wörter in Sätze anhand von Satzzeichen.
- Nutzt spaCy (Modell `es_dep_news_trf`) zur linguistischen Annotation (POS, Lemma, Morphologie, Abhängigkeiten).
- Verwendet Kontext aus vorherigem, aktuellem und folgendem Satz für bessere Annotation.
- Überspringt bereits annotierte Dateien.
- Post-Processing zur genaueren Klassifikation spanischer Vergangenheits- und analytischer Futurformen.
- Speichert die annotierten Daten zurück in die JSON-Dateien.

---

## 3. Analyse der annotierten Daten (`analysis`)

**Skript:** `analysis_pasado.py`

- Liest alle annotierten JSON-Dateien aus `grabaciones`.
- Filtert Wörter mit Past-Formen, speziell `PerfectoCompuesto` und `PerfectoSimple`.
- Zählt absolute Häufigkeiten und berechnet prozentuale Anteile dieser Formen pro Datei.
- Gruppiert Ergebnisse nach Ländercode (extrahiert aus Dateinamen).
- Schreibt die Auswertung in eine CSV-Datei `analysis_pasado_results.csv` im `analysis`-Ordner.

---

## Datenfluss und Abhängigkeiten

- Die Rohdaten liegen als JSON-Dateien im Ordner `grabaciones`.
- `annotation_grabaciones.py` annotiert diese JSON-Dateien mit linguistischen Informationen.
- `database_creation.py` erstellt Datenbanken aus den (teilweise annotierten) JSON-Daten und ergänzt Token-IDs.
- `analysis_pasado.py` wertet die annotierten JSON-Dateien aus und erzeugt statistische Berichte.

---

Diese Übersicht dient als Ausgangspunkt für zukünftige Tasks im Ordner `LOKAL`.

---

## 4. Dokumentations-Konventionen für LOKAL

### Python (.py)
- Hauptabschnitte mit Block-Kommentaren:
  ```python
  # ===========================================================================
  # Abschnittsname
  # ===========================================================================
  ```
- Funktionen und Klassen mit Docstrings im Google- oder NumPy-Stil.
- Inline-Kommentare sparsam und nur bei komplexer Logik.
- Fortschrittsmeldungen und Statusausgaben in Skripten sind klar und informativ.

### CSV-Ergebnisdateien (.csv)
- CSV-Dateien enthalten eine Kopfzeile mit Spaltennamen.
- Spalten sind durch Semikolon (`;`) getrennt.
- Für jede Datei werden relevante Metriken (z.B. Häufigkeiten, Prozentwerte) pro Land gruppiert.
- Ergebnisdateien werden im jeweiligen Skriptordner abgelegt (z.B. `analysis/analysis_pasado_results.csv`).
- Dokumentation der Spalten in begleitender Markdown-Datei oder im Skript-Header empfohlen.

### Allgemein
- Pfadangaben in Skripten sind relativ zum Skriptstandort oder Projekt-Root.
- JSON-Dateien im Ordner `grabaciones` sind zentrale Datenquelle.
- Skripte schreiben Ergebnisse zurück in JSON, SQLite-Datenbanken oder CSV-Dateien.
- Fortschritts- und Statusmeldungen unterstützen Nachvollziehbarkeit und Debugging.

Diese Konventionen ergänzen die allgemeinen Projektstandards und sind speziell auf die Datenverarbeitung im Ordner `LOKAL` zugeschnitten.
