# BlackLab Advanced Filter 500 Fix

Datum: 2026-03-21
Umgebung: Development / lokaler Workspace

## Kurzfazit

Die 500-Fehler in der Dev-Advanced-Search wurden nicht durch falsche Feldnamen oder falsche App-Filterebenen verursacht, sondern durch einen korrumpierten aktiven Dev-BlackLab-Index.

Nach einem gezielten Rebuild des Dev-Index und einem Neustart des BlackLab-Containers liefern die direkten BlackLab-Queries sowie der aktive Browser-Endpunkt `/search/advanced/data` wieder `200`.

## Minimal reproduzierbare Befunde vor dem Fix

Direkt gegen BlackLab getestet:

- `[word="casa"]` -> `500`
- `[word="casa" & country_code="ARG"]` -> `500`
- `[word="casa" & country_scope="national"]` -> `500`

Wichtig:

- der Fehler trat nicht nur bei den Zusatzfiltern auf
- bereits der einfache Wort-Query war auf dem aktiven Dev-Index defekt
- die Zusatzfilter machten das Problem sichtbar, waren aber nicht die Primaerursache

## Tatsaechliche BlackLab-Log-Ursache

BlackLab-Logbefund waehrend des Fehlers:

- `InvalidIndex`
- `CorruptIndexException`
- `file mismatch, expected id=..., got=...`
- betroffenes Segment: `/data/index/corapan/_2.blcs.fields`

Klassifikation:

- BlackLab crasht trotz vorhandener Annotationen
- Ursache ist ein inkonsistenter Lucene/BlackLab-Index, nicht ein unbekanntes Feld in der CQL

## Status der Annotationen/Felder

### Aktiver Dev-Corpus

Direkter Corpus-Endpoint `GET /blacklab-server/corpora/corapan` meldet die relevanten Annotationen als vorhanden:

- `country_code`
- `country_scope`
- `country_parent_code`
- `country_region_code`
- `speaker_code`

### Aktive BLF

Der aktive Dev-Container mountet in der laufenden Dev-Compose-Konfiguration:

- `C:\dev\corapan\data\blacklab\index -> /data/index/corapan`
- `C:\dev\corapan\config\blacklab -> /etc/blacklab`

Bewertung:

- fuer den live laufenden Dev-BlackLab war die aktive Konfiguration die Root-Konfiguration unter `C:\dev\corapan\config\blacklab`
- die repolokale Kopie unter `webapp/config/blacklab` war fuer den Live-Container nicht die aktive Mount-Quelle
- inhaltlich sind die BLF-Dateien fuer die relevanten Felder gleich; nur `blacklab-server.yaml` unterscheidet sich in einem Kommentartext

### BLF-/Export-Modell

Die aktive TSV-BLF definiert die relevanten Felder als Token-Annotationen unter `annotatedFields.contents.annotations`:

- `country_code`
- `country_scope`
- `country_parent_code`
- `country_region_code`

Zusaetzlich werden dieselben Werte auch als Dokument-Metadata modelliert.

Der aktuelle TSV-Export enthaelt die Spalten ebenfalls explizit:

- `country_code`
- `country_scope`
- `country_parent_code`
- `country_region_code`

Das aktuelle `docmeta.jsonl` enthaelt dieselben Schluessel ebenfalls.

## Ursachenklassifikation

Die zutreffende Ursache ist:

- `BlackLab crasht trotz vorhandener Annotation`

Nicht zutreffend:

- Annotation fehlt im Index
- Annotation falsch benannt
- Annotation ist kein Token-Feld
- Export/TSV passt nicht zur BLF
- App sendet Filter auf falscher Ebene

## Durchgefuehrte Behebung

Es war keine Aenderung an der Query-Generierung notwendig.

Durchgefuehrt wurde stattdessen eine operative Reparatur des Dev-Index:

1. `blacklab-server-v3` gestoppt
2. kanonisches Build-Skript ausgefuehrt:
   - `webapp/scripts/blacklab/build_blacklab_index.ps1 -Activate`
3. neuer Index aktiviert
4. alter aktiver Index automatisch gesichert unter:
   - `data/blacklab/backups/index_2026-03-21_001627`
5. `blacklab-server-v3` erneut gestartet
6. Health-Status wieder `healthy`

## Validierung nach dem Fix

### Direkte BlackLab-Tests

- `[word="casa"]` -> `200`
- `[word="casa" & country_code="ARG"]` -> `200`
- `[word="casa" & country_scope="national"]` -> `200`

### Browser-relevanter App-Pfad

Getestet:

- `GET /health` -> `200`
- `GET /search/advanced` -> `200`
- `GET /search/advanced/data?...q=casa...` -> `200`
- `GET /search/advanced/data?...q=casa&country_code=ARG...` -> `200`
- `GET /search/advanced/data?...q=casa&country_scope=national...` -> `200`

Beobachtung:

- der aktuelle Browser-Code nutzt `GET /search/advanced/data`
- dieser aktive UI-Endpunkt funktioniert nach dem Rebuild wieder sauber
- der aeltere HTML-Teilpfad `/search/advanced/results` liefert weiterhin `400` wegen JSON/XML-Parsing, war aber nicht der 500-Ausloeser und nicht der aktive DataTables-Browserpfad

## Ergebnis

Ja: Dev-BlackLab ist fuer die aktuelle Advanced Search wieder funktional sauber.

Begruendung:

- BlackLab selbst beantwortet die relevanten CQL-Muster wieder korrekt
- die gefilterten Country-Queries laufen wieder
- der aktive Browser-Endpunkt der Advanced Search liefert wieder erfolgreiche Antworten statt 500