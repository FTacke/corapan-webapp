## CO.RA.PAN Zenodo Repositories – Übersicht

Dieses Verzeichnis enthält Skripte zur Aufbereitung der vier CO.RA.PAN Zenodo-Datensätze:

| Datensatz | Visibility | DOI |
| --- | --- | --- |
| **Full Corpus** | Restricted | [https://doi.org/10.5281/zenodo.15360942](https://doi.org/10.5281/zenodo.15360942) |
| **Sample Corpus** | Public | [https://doi.org/10.5281/zenodo.15378479](https://doi.org/10.5281/zenodo.15378479) |
| **Metadata** | Public | *DOI folgt nach Erstveröffentlichung* |
| **Web Application & Code** | Public | [https://doi.org/10.5281/zenodo.17834023](https://doi.org/10.5281/zenodo.17834023) |


---


## 1. Full Corpus (Restricted)

**Ordner:** `Zenodo Full Corpus/`  
**Skript:** `zenodo_full-corpus.py`

Das **Full Corpus** enthält länderspezifische ZIP-Archive mit Audiodateien und Transkriptionen.


### Zugriffsbedingungen


* **Visibility:** Restricted (Zugriff auf Anfrage)
* **Grund:** Urheberrechtlich geschützte Audiodaten und Transkriptionen; Freigabe nur für berechtigte Nutzer\:innen.


### Inhaltsstruktur


| Datei                             | Beschreibung                                   |
| --------------------------------- | ---------------------------------------------- |
| `README.md`                       | Diese Übersicht und Gebrauchsanleitung         |
| `{LÄNDERCODE}.zip`                | ZIP-Archiv für jedes Land (Audio & JSON)       |


#### ZIP-Struktur pro Land

Jede `{LÄNDERCODE}.zip` Datei enthält:

```
{LÄNDERCODE}/
├── mp3-files/
│   ├── *.mp3        (Audiodateien)
│   └── ...
└── json-transcripts/
    ├── *.json       (Transkriptionen mit Annotationen)
    └── ...
```


### Zusammenstellung der ZIP-Archive


1. **Quellordner:**
   * `media/mp3-full/` – gruppiert nach Ländercode mit Audiodateien
   * `media/transcripts/` – gruppiert nach Ländercode mit annotierten Transkriptionen (JSON)
2. **Skript:** `zenodo_full-corpus.py` erstellt für jedes Land ein ZIP im Ordner `Zenodo Full Corpus/`.
3. **Log-Datei:** `zip_process.log` dokumentiert Dateien und Änderungszeiten für inkrementelle Updates.
4. **Metadaten:** Werden separat über `zenodo_metadata.py` → `Zenodo Metadata/` bereitgestellt (siehe Abschnitt 2).


### Versionierung & Updates


* **Zenodo-Datensatz:** Full Corpus (Restricted)
  * **DOI:** [https://doi.org/10.5281/zenodo.15360942](https://doi.org/10.5281/zenodo.15360942)
  * **Neue Versionen:** werden als neue Versionseinträge auf Zenodo hochgeladen (automatische Versionsnummern)

* **Update-Prozess:**
  1. Lokale Änderungen oder neue Länder in `media/mp3-full/` und `media/transcripts/`
  2. Ausführen von `zenodo_full-corpus.py` → aktualisierte ZIPs und Metadaten
  3. Neue Version des Full Corpus auf Zenodo hochladen (nur veränderte ZIPs + Metadaten-Dateien + `README.md`)


---


## 2. Metadata (Public)

**Ordner:** `Zenodo Metadata/`  
**Skript:** `zenodo_metadata.py`

Das **Metadata** Repository enthält alle Metadaten-Dateien zum Corpus – frei zugänglich unter CC-BY 4.0.


### Zugriffsbedingungen

* **Visibility:** Public (Open Access)
* **Lizenz:** CC-BY 4.0


### Inhaltsstruktur

| Datei | Beschreibung |
| --- | --- |
| `corapan_recordings.tsv` | Globale Metadaten-Tabelle (alle Aufnahmen) |
| `corapan_recordings.json` | Recordings-Metadaten (JSON-Format) |
| `corapan_recordings.jsonld` | Recordings-Metadaten (JSON-LD-Format) |
| `corapan_corpus_metadata.json` | Corpus-Metadaten (JSON-Format) |
| `corapan_corpus_metadata.jsonld` | Corpus-Metadaten (JSON-LD-Format) |
| `corapan_recordings_{CODE}.tsv` | Länderspezifische Metadaten (TSV) |
| `corapan_recordings_{CODE}.json` | Länderspezifische Metadaten (JSON) |
| `tei_headers.zip` | TEI-Header-Dateien (ZIP-Archiv) |


### Update-Prozess

1. Metadaten generieren: `python LOKAL/_1_metadata/export_metadata.py -v v1.0 -d 2025-12-15`
2. Für Zenodo kopieren: `python LOKAL/_1_zenodo-repos/zenodo_metadata.py`
3. Neue Version auf Zenodo hochladen


---


## 3. Sample Corpus (Public)

**DOI:** [https://doi.org/10.5281/zenodo.15378479](https://doi.org/10.5281/zenodo.15378479)

Ein öffentlich zugängliches Sample des Corpus für Testzwecke und erste Einblicke.

*Aufbereitung erfolgt manuell.*


---


## 4. Web Application & Code (Public)

**DOI:** [https://doi.org/10.5281/zenodo.17834023](https://doi.org/10.5281/zenodo.17834023)

Der Quellcode der CO.RA.PAN Web-Applikation (dieses Repository).

*Zenodo-Integration über GitHub-Release-Sync.*


---


### Links & DOIs (Zusammenfassung)


| Datensatz | DOI |
| --- | --- |
| **Full Corpus (Restricted)** | [https://doi.org/10.5281/zenodo.15360942](https://doi.org/10.5281/zenodo.15360942) |
| **Sample Corpus (Public)** | [https://doi.org/10.5281/zenodo.15378479](https://doi.org/10.5281/zenodo.15378479) |
| **Metadata (Public)** | *DOI folgt nach Erstveröffentlichung* |
| **Web-App & Code** | [https://doi.org/10.5281/zenodo.17834023](https://doi.org/10.5281/zenodo.17834023) |


### Datenverarbeitung & Annotation


Die JSON-Transkriptionen enthalten linguistische Annotationen:

* **Morphologische Analyse:** POS-Tags, Lemmata, Dependenzen
* **Zeitformen-Erkennung:** Automatische Klassifikation von Vergangenheits- und Futurformen
* **Annotationswerkzeug:** spaCy (`es_dep_news_trf`)


### Kontakt & Support


Für Fragen zum Datensatz oder zur Nutzung bitte:
* Zenodo-Datensatz-Seite nutzen (Direct Message oder Kontaktformular)
* Oder: CO.RA.PAN-Projektteam kontaktieren


---

**Hinweis:** Dieses Verzeichnis dient der Aufbereitung aller vier Zenodo-Datensätze des CO.RA.PAN-Projekts.
