# Vollständige Bestandsaufnahme: Simple-Search vs. Advanced-Search

**Datum:** 2025-11-13  
**Repo:** corapan-webapp  
**Zweck:** Komplette strukturierte Analyse für gemeinsames Hit → Tabellenzeile Mapping

---

## Inhaltsverzeichnis

1. [Überblick über alle relevanten Bestandteile](#1-überblick)
2. [Simple-Search – Backend-Datenfluss und Mapping](#2-simple-search)
3. [Advanced-Search – Backend-Datenfluss und Mapping](#3-advanced-search)
4. [DataTables-Konfiguration (Frontend)](#4-datatables-konfiguration)
5. [Gemeinsame Datenbasis / Mapping-Potenzial](#5-gemeinsame-datenbasis)
6. [Offene Punkte / Potentielle Stolpersteine](#6-offene-punkte)

---

## 1. Überblick über alle relevanten Bestandteile

### 1.1 Backend-Dateien

#### Simple Search (Corpus)

| Datei | Pfad | Zweck |
|-------|------|-------|
| **corpus.py** | `src/app/routes/corpus.py` | Flask-Routes für Corpus-Seite (HTML + DataTables-Endpoint) |
| **corpus_search.py** | `src/app/services/corpus_search.py` | Service-Layer für Token-Suche in SQLite-DB |
| **database.py** | `src/app/services/database.py` | DB-Verbindungs-Helper (`open_db()`) |

**Zeilen-Übersicht:**
- `corpus.py` L64-73: Route `/corpus` (HTML-Seite)
- `corpus.py` L170-321: Route `/corpus/search/datatables` (Server-Side DataTables)
- `corpus_search.py` L22-40: **CANON_COLS** Definition (Kern-API-Contract)
- `corpus_search.py` L306-496: **search_tokens()** Hauptfunktion

#### Advanced Search (BlackLab)

| Datei | Pfad | Zweck |
|-------|------|-------|
| **advanced.py** | `src/app/search/advanced.py` | Flask-Routes für Advanced-Search HTML-Seite |
| **advanced_api.py** | `src/app/search/advanced_api.py` | DataTables-Endpoint + Export (CSV/TSV) |
| **cql.py** | `src/app/search/cql.py` | CQL-Pattern-Builder für BlackLab |
| **cql_validator.py** | `src/app/search/cql_validator.py` | CQL-Validierung |

**Zeilen-Übersicht:**
- `advanced.py` L17-25: Route `/search/advanced` (HTML-Seite)
- `advanced_api.py` L100-373: Route `/search/advanced/data` (DataTables-Endpoint)
- `advanced_api.py` L43-97: **_make_bls_request()** BlackLab-HTTP-Helper
- `advanced_api.py` L376-673: Route `/search/advanced/export` (Streaming CSV/TSV)

#### Gemeinsame Module

| Datei | Pfad | Zweck |
|-------|------|-------|
| **http_client.py** | `src/app/extensions/http_client.py` | Zentraler HTTP-Client (httpx) für BlackLab |
| **config/__init__.py** | `src/app/config/__init__.py` | App-Konfiguration (DB-Pfade, Media-Pfade) |

---

### 1.2 Frontend-Dateien

#### Simple Search

| Datei | Pfad | Zweck |
|-------|------|-------|
| **corpus.html** | `templates/pages/corpus.html` | Haupttemplate mit Suchformular + DataTables |
| **datatables.js** | `static/js/modules/corpus/datatables.js` | DataTables-Init (Server-Side) |
| **filters.js** | `static/js/modules/corpus/filters.js` | Filter-Logik (Select2) |
| **audio.js** | `static/js/modules/corpus/audio.js` | Audio-Player-Integration |

**Zeilen-Übersicht:**
- `corpus.html` L302-323: `<table id="corpus-table">` (12 Spalten)
- `datatables.js` L39-100: `CorpusDatatablesManager.initialize()`
- `datatables.js` L241-310: **buildColumns()** – Spalten-Definitionen

#### Advanced Search

| Datei | Pfad | Zweck |
|-------|------|-------|
| **advanced.html** | `templates/search/advanced.html` | Template mit CQL-Formular + DataTables |
| **initTable.js** | `static/js/modules/advanced/initTable.js` | DataTables-Init (Server-Side) |
| **formHandler.js** | `static/js/modules/advanced/formHandler.js` | Form-Submission + CQL-Generierung |

**Zeilen-Übersicht:**
- `advanced.html` L298-323: `<table id="advanced-table">` (12 Spalten)
- `initTable.js` L54-231: `initAdvancedTable()` Hauptfunktion
- `initTable.js` L93-207: **columnDefs** – Spalten-Definitionen (Index-basiert!)

---

### 1.3 Datenfluss-Übersicht

#### Simple Search (Stichpunkte)

```
Browser → GET /corpus (corpus.py L64)
    ↓
Render corpus.html mit Filter-Formular
    ↓
User-Interaktion: Suche starten
    ↓
DataTables AJAX → GET /corpus/search/datatables (corpus.py L170)
    ↓
SearchParams-Objekt erstellen (corpus.py L261-276)
    ↓
search_tokens() (corpus_search.py L306)
    ↓
SQLite-Query: SELECT <CANON_COLS> FROM tokens WHERE ...
    ↓
Row-Factory: sqlite3.Row → Dict mit stabilen Keys
    ↓
JSON Response: { draw, recordsTotal, recordsFiltered, data: [...] }
    ↓
DataTables rendert Zeilen mit Objekt-Keys (datatables.js L241-310)
```

#### Advanced Search (Stichpunkte)

```
Browser → GET /search/advanced (advanced.py L17)
    ↓
Render advanced.html mit CQL-Formular
    ↓
User-Interaktion: CQL-Query + Filter
    ↓
DataTables AJAX → GET /search/advanced/data (advanced_api.py L100)
    ↓
build_cql() + build_filters() (cql.py)
    ↓
_make_bls_request("/corapan/hits", params) (advanced_api.py L43)
    ↓
BlackLab Server → JSON Response mit hits[]
    ↓
Hits verarbeiten: left/match/right + Metadaten extrahieren
    ↓
processed_hits als ARRAYS (advanced_api.py L277-291)
    ↓
JSON Response: { draw, recordsTotal, recordsFiltered, data: [[...], [...]] }
    ↓
DataTables rendert Zeilen mit Index-basiertem Zugriff (initTable.js L93-207)
```

---

## Siehe Detailberichte

Die folgenden Abschnitte sind in separate Dateien aufgeteilt:

- [Abschnitt 2: Simple-Search Details](./BESTANDSAUFNAHME_SIMPLE_SEARCH.md)
- [Abschnitt 3: Advanced-Search Details](./BESTANDSAUFNAHME_ADVANCED_SEARCH.md)
- [Abschnitt 4: DataTables-Konfiguration Vergleich](./BESTANDSAUFNAHME_DATATABLES_VERGLEICH.md)
- [Abschnitt 5: Gemeinsame Datenbasis](./BESTANDSAUFNAHME_GEMEINSAME_BASIS.md)
- [Abschnitt 6: Offene Punkte](./BESTANDSAUFNAHME_OFFENE_PUNKTE.md)

