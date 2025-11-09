---
title: "Corpus Search Architecture"
status: active
owner: backend-team
updated: "2025-11-08"
tags: [corpus, search, datatables, architecture, database]
links:
  - ../concepts/authentication-flow.md
  - ../how-to/corpus-advanced-search.md
  - ../reference/database-schema.md
---

# Corpus Search Architecture

Detaillierte Referenzdokumentation der aktuellen Suchfunktionalität im CO.RA.PAN Corpus, einschließlich Tech-Stack, Datenbankstruktur, DataTables-Integration und Datenfluss.

---

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Tech-Stack](#tech-stack)
3. [Datenbankstruktur](#datenbankstruktur)
4. [Suchmode und Parameter](#suchmode-und-parameter)
5. [Backend-Architektur](#backend-architektur)
6. [Frontend-Architektur](#frontend-architektur)
7. [Datenfluss](#datenfluss)
8. [DataTables-Mapping](#datatables-mapping)
9. [Filterlogik](#filterlogik)
10. [Implementierte Suchfunktionen](#implementierte-suchfunktionen)
11. [Geplante erweiterte Suche](#geplante-erweiterte-suche)

---

## Überblick

Das Corpus-Search-System implementiert zwei aktive Suchfunktionen:

1. **Einfache Suche (Simple Search)** - Text/Lemma-basierte Wortsuche mit Wildcard-Matching
2. **Token-ID-Suche (Token Search)** - Direkte Suche nach eindeutigen Token-Identifikatoren

Eine dritte Funktion ist geplant:

3. **Erweiterte Suche (Advanced Search)** - Komplexe Abfragen mit mehreren Bedingungen (derzeit deaktiviert)

**Aktive Komponenten:**
- Backend: Flask-REST-API mit SQLite
- Frontend: ES6-Module mit jQuery, Select2, Tagify, DataTables
- Datenbank: SQLite-DB mit indexierten Token-Tabellen
- UI: MD3-Design-System mit Datentabellen-Rendering

---

## Tech-Stack

### Backend

| Komponente | Technologie | Zweck |
|-----------|-----------|--------|
| Framework | Flask (Python 3.11+) | REST-API, Route-Handling |
| Datenbank | SQLite3 | Persistente Speicherung von Tokens |
| ORM | Keine (Raw SQL mit Context Manager) | Performance, direkter DB-Zugriff |
| Authentifizierung | Flask-JWT-Extended | Optional JWT für private Audio |
| Routing | Blueprint (`corpus.py`) | Modulare Route-Organisation |

**Dateien:**
- `src/app/routes/corpus.py` - Route-Handler (2 Endpoints)
- `src/app/services/corpus_search.py` - Search-Service mit SQL-Builder
- `src/app/services/database.py` - DB-Connection-Manager

### Frontend

| Komponente | Bibliothek | Version | Zweck |
|-----------|-----------|---------|--------|
| jQuery | jQuery | 3.7.1 | DOM-Manipulation, Event-Handling |
| Datenbank-UI | DataTables | 1.13.7 | Server-Side Processing, Tabellen-Rendering |
| Multi-Select | Select2 | 4.1.0-rc.0 | Filter-Dropdowns (Land, Hablante, Sexo, etc.) |
| Token-Input | Tagify | Latest | Token-ID-Input mit Drag-Drop |
| Datenmanipulation | Sortable.js | Latest | Drag-Drop für Token-Reordering |
| Charts | ECharts | 5.5.1 | Statistik-Visualisierung (Stats-Tab) |
| Icons | Font Awesome 6 | 6+ | UI-Icons |
| Design | MD3 (Material Design 3) | Custom CSS | Styling + Theme |

**Dateien:**
- `static/js/modules/corpus/index.js` - Main Entry Point
- `static/js/modules/corpus/datatables.js` - DataTables Manager
- `static/js/modules/corpus/search.js` - Form-Handling
- `static/js/modules/corpus/filters.js` - Select2 Filter-Manager
- `static/js/modules/corpus/tokens.js` - Tagify Token-Manager
- `static/js/modules/corpus/audio.js` - Audio-Player Integration
- `static/js/modules/corpus/config.js` - Constants + Configuration
- `static/js/modules/corpus/api.js` - API-Calls (falls vorhanden)

**Template:**
- `templates/pages/corpus.html` - Main UI + Form

---

## Datenbankstruktur

### Tabelle: `tokens`

Die zentrale Datenbank ist `data/db/transcription.db` mit einer **Tokens-Tabelle**:

```sql
-- Pseudo-Schema (aus Code abgeleitet)
CREATE TABLE tokens (
  id              INTEGER PRIMARY KEY,           -- 0: Row ID (auto-increment)
  token_id        TEXT NOT NULL UNIQUE,          -- 1: Eindeutige Token-ID (z.B. "ARG_RN_20050101_001_00000042")
  filename        TEXT NOT NULL,                 -- 2: Audio-Dateiname (z.B. "ARG_RN_20050101_001.mp3")
  country_code    TEXT NOT NULL,                 -- 3: Ländercode (ARG, ESP, MEX, etc. oder regional: ARG-CHU)
  radio           TEXT,                          -- 4: Sendenanme
  date            TEXT,                          -- 5: Aufnahmedatum
  speaker_type    TEXT NOT NULL,                 -- 6: pro / otro
  sex             TEXT NOT NULL,                 -- 7: m / f / null
  mode            TEXT NOT NULL,                 -- 8: pre (Anuncio), lectura, libre (Habla libre)
  discourse       TEXT NOT NULL,                 -- 9: general, tiempo, tránsito
  text            TEXT NOT NULL,                 -- 10: Das Wort selbst
  start           REAL NOT NULL,                 -- 15: Startzeitstempel (Sekunden)
  end             REAL NOT NULL,                 -- 16: Endzeitstempel (Sekunden)
  context_left    TEXT,                          -- 13: Vorhergehendes Wort
  context_right   TEXT,                          -- 14: Nächstes Wort
  context_start   REAL,                          -- Context-Startzeit
  context_end     REAL,                          -- Context-Endzeit
  lemma           TEXT                           -- Lemma (falls vorhanden)
);

-- Indizes für Performance
CREATE INDEX idx_token_id ON tokens(token_id);
CREATE INDEX idx_country ON tokens(country_code);
CREATE INDEX idx_text ON tokens(text);
CREATE INDEX idx_lemma ON tokens(lemma);
CREATE INDEX idx_mode ON tokens(mode);
CREATE INDEX idx_speaker_type ON tokens(speaker_type);
CREATE INDEX idx_sex ON tokens(sex);
CREATE INDEX idx_discourse ON tokens(discourse);
CREATE INDEX idx_filename ON tokens(filename);
```

### Spalten-Mapping (Python → SQL)

```python
# Spalte 0: id (Row-ID)
# Spalte 1: token_id
# Spalte 2: filename
# Spalte 3: country_code
# Spalte 4: radio
# Spalte 5: date
# Spalte 6: speaker_type
# Spalte 7: sex
# Spalte 8: mode
# Spalte 9: discourse
# Spalte 10: text (das Wort)
# Spalte 11-12: (reserviert)
# Spalte 13: context_left
# Spalte 14: context_right
# Spalte 15: start (in Sekunden)
# Spalte 16: end
```

### Länder-/Regioncodes

**Nationale Emissoras (19):**
- `ARG`, `BOL`, `CHL`, `COL`, `CRI`, `CUB`, `ECU`, `ESP`, `GTM`, `HND`, `MEX`, `NIC`, `PAN`, `PRY`, `PER`, `DOM`, `SLV`, `URY`, `USA`, `VEN`

**Regionale Emissoras (5):**
- `ARG-CHU` (Chubutien)
- `ARG-CBA` (Córdoba)
- `ARG-SDE` (San de Estero)
- `ESP-CAN` (Kanarische Inseln)
- `ESP-SEV` (Sevilla)

**Filter-Logik:**
- Standard: Nur nationale Codes
- Mit `include_regional=1`: Nationale + Regionale Codes

---

## Suchmode und Parameter

### Suchmode-Typen

| Mode | DB-Spalte | Operator | Beispiel | Notizen |
|------|----------|----------|---------|---------|
| `text` | `text` | `LIKE %word%` | "ar" → "aro", "palabra" | Wildcard-Match (case-insensitive) |
| `text_exact` | `text` | `= word` | "palabra" → nur "palabra" | Exakte Übereinstimmung |
| `lemma` | `lemma` | `LIKE %lemma%` | "ser" → "soy", "eres", "somos" | Lemma-Wildcard |
| `lemma_exact` | `lemma` | `= lemma` | "ser" → nur "ser" | Lemma exakt |
| `token_ids` | `token_id` | `IN (...)` | Token-IDs komma-getrennt | Direkte Token-Suche |

### SearchParams Dataclass

```python
@dataclass
class SearchParams:
    # Suchkriterien
    query: str                           # Suchtext (z.B. "palabra")
    search_mode: str = "text"            # text | text_exact | lemma | lemma_exact | token_ids
    token_ids: Sequence[str] = ()        # Token-IDs (nur für token_ids Mode)
    
    # Filter
    countries: Sequence[str] = ()        # Länder-Filter (z.B. ["ARG", "MEX"])
    speaker_types: Sequence[str] = ()    # pro / otro
    sexes: Sequence[str] = ()            # m / f
    speech_modes: Sequence[str] = ()     # pre / lectura / libre
    discourses: Sequence[str] = ()       # general / tiempo / tránsito
    
    # Pagination & Sorting
    page: int = 1                        # Seite (1-based)
    page_size: int = 20                  # Einträge pro Seite (max 100)
    sort: str | None = None              # Spalte zum Sortieren
    order: str = "asc"                   # asc | desc
    
    # DataTables Server-Side Search
    table_search: str = ""               # Search-Box in DataTables (volltext in allen Spalten)
```

### Filter-Kombinationen

Alle Filter sind **kumulativ** (AND-Logik):

```
query="palabra" 
  AND country_code IN ("ARG", "MEX")
  AND speaker_type = "pro"
  AND sex = "f"
  AND mode = "lectura"
  AND discourse = "general"
```

Falls ein Filter **nicht angegeben** ist → **kein Filter** auf diese Spalte

---

## Backend-Architektur

### Route: `GET /corpus`

**Zweck:** Corpus-Startseite laden

**Handler:** `corpus_home()`

**Context (Template-Variablen):**
```python
{
    "query": "",
    "token_ids": "",
    "search_mode": "text",
    "results": [],                      # Leeres Array auf Start
    "total_results": 0,
    "unique_countries": 0,
    "unique_filenames": 0,
    "selected_countries": ["all"],
    "selected_speaker_types": ["all"],
    "selected_sexes": ["all"],
    "selected_speech_modes": ["all"],
    "selected_discourses": ["all"],
    "active_tab": "tab-simple",         # oder "tab-token"
    "allow_public_temp_audio": False,   # Config
    "is_authenticated": bool,           # JWT-Status
    # ... weitere Default-Werte
}
```

### Route: `GET|POST /corpus/search`

**Zweck:** Einfache/Token-Suche durchführen, Ergebnisse auf Seite rendern

**Handler:** `search()`

**Request-Parameter:**

```
GET /corpus/search?query=palabra&search_mode=text&country_code=ARG&country_code=MEX&page=1&page_size=25
```

| Parameter | Quelle | Typ | Beispiel |
|-----------|--------|-----|---------|
| `query` | GET/POST | string | "palabra" |
| `search_mode` | GET/POST | string | text, text_exact, lemma, lemma_exact |
| `search_mode_override` | GET/POST | string | (für Token-Suche intern) |
| `token_ids` | GET/POST (comma-sep) | string | "TOKEN1,TOKEN2,TOKEN3" |
| `country_code[]` | GET/POST (multi) | string[] | ["ARG", "MEX"] |
| `include_regional` | GET/POST | "0" \| "1" | "1" |
| `speaker_type[]` | GET/POST (multi) | string[] | ["pro", "otro"] |
| `sex[]` | GET/POST (multi) | string[] | ["m", "f"] |
| `speech_mode[]` | GET/POST (multi) | string[] | ["pre", "lectura", "libre"] |
| `discourse[]` | GET/POST (multi) | string[] | ["general", "tiempo", "tránsito"] |
| `page` | GET/POST | int | 1 |
| `page_size` | GET/POST | int | 20-100 |
| `sort` | GET/POST | string | "text", "country_code", etc. |
| `order` | GET/POST | string | "asc" \| "desc" |
| `active_tab` | GET/POST (hidden) | string | "tab-simple" \| "tab-token" |

**Backend-Verarbeitung:**

```python
# 1. Parameter parsen
data_source = request.form if POST else request.args
query = data_source.get("query")
search_mode = data_source.get("search_mode_override") or data_source.get("search_mode")
countries = data_source.getlist("country_code")
include_regional = data_source.get("include_regional") == "1"

# 2. Länder-Filter auflösen
if not countries:
    if include_regional:
        countries = national_codes + regional_codes  # 19 + 5
    else:
        countries = national_codes  # 19

# 3. SearchParams bauen
params = SearchParams(
    query=query,
    search_mode=search_mode,
    token_ids=_parse_token_ids(),
    countries=countries,
    speaker_types=...,
    # etc.
)

# 4. search_tokens(params) aufrufen → Service-Layer
service_result = search_tokens(params)

# 5. Context für Template bauen
context = {
    "results": service_result["items"],         # Seite mit Ergebnissen
    "all_results": service_result["all_items"], # Alle Ergebnisse
    "total_results": service_result["total"],
    "unique_countries": service_result["unique_countries"],
    "unique_filenames": service_result["unique_files"],
    # ...
}

# 6. Template rendern
return render_template("pages/corpus.html", **context)
```

### Route: `GET /corpus/search/datatables`

**Zweck:** Server-Side DataTables Endpoint (AJAX)

**Handler:** `search_datatables()`

**Request (DataTables Protocol):**

```
GET /corpus/search/datatables?
  draw=1
  start=0
  length=25
  search[value]=palabra           # DataTables search-box (volltext in allen Spalten)
  query=palabra                   # Original query (einfache Suche)
  search_mode=text
  order[0][column]=2              # Sort column: 2 = "Palabra"
  order[0][dir]=asc
  country_code=ARG&country_code=MEX
  include_regional=0
  speaker_type=pro
  sex=f
  speech_mode=lectura
  discourse=general
  page=1
  page_size=25
```

**Response (DataTables Protocol):**

```json
{
  "draw": 1,
  "recordsTotal": 12345,
  "recordsFiltered": 234,
  "data": [
    [1, "el", "palabra", "siguiente", true, "ARG", "pro", "m", "lectura", "general", "ARG_RN_..._001", "ARG_RN_...mp3", 45.123, 45.567, 44.0, 47.0],
    [2, "la", "otra", "palabra", false, "MEX", "otro", "f", "libre", "tiempo", "MEX_...", "MEX_...mp3", 102.45, 103.12, 100.0, 105.0],
    // ... weitere Rows
  ]
}
```

**Spalten-Reihenfolge (Index):**
```
0: Row number (#)
1: context_left (Ctx.←)
2: text (Palabra)
3: context_right (Ctx.→)
4: audio_available (boolean)
5: country_code (País)
6: speaker_type (Hablante)
7: sex (Sexo)
8: mode (Modo)
9: discourse (Discurso)
10: token_id (Token-ID)
11: filename (Archivo)
12: start (word start, hidden)
13: end (word end, hidden)
14: context_start (context start, hidden)
15: context_end (context end, hidden)
```

### Service: `search_tokens(params: SearchParams)`

**Datei:** `src/app/services/corpus_search.py`

**Workflow:**

```
1. Filter-Klauzeln bauen (WHERE clauses)
   - Token-IDs
   - Länder
   - Speaker-Typ
   - Sexo
   - Mode
   - Discourse
   - DataTables Search (volltext-search über alle Spalten)

2. Word-Query bauen (je nach search_mode)
   text/lemma:
     - Single Word: SELECT * FROM tokens WHERE text/lemma LIKE "%word%"
     - Multi-Word: SELECT * FROM tokens t1 
       JOIN tokens t2 ON t2.filename = t1.filename AND t2.id = t1.id + 1
       WHERE t1.text LIKE "word1" AND t2.text LIKE "word2"
   
   token_ids:
     - SELECT * FROM tokens WHERE token_id IN (...)

3. COUNT-Query ausführen
   SELECT COUNT(*) FROM (word_query) WHERE filters

4. ORDER BY auflösen
   - Token-IDs: CASE WHEN token_id = ? THEN 0 ELSE 999999 END (Input-Reihenfolge)
   - Normale Suche: sort_column ASC/DESC

5. LIMIT/OFFSET anwenden (Pagination)

6. Daten abrufen
   SELECT * FROM (word_query) WHERE filters ORDER BY ... LIMIT page_size OFFSET offset

7. Ergebnisse in Dicts konvertieren
   - Audio-Verfügbarkeit prüfen (safe_audio_full_path)
   - Transcript-Verfügbarkeit prüfen (safe_transcript_path)
   - unique_countries / unique_files zählen

8. Dict zurückgeben
   {
     "items": [...],          # Aktuelle Seite
     "all_items": [...],      # Alle Ergebnisse (Server-Side: gleich wie items)
     "total": 12345,
     "page": 1,
     "page_size": 25,
     "total_pages": 494,
     "unique_countries": 5,
     "unique_files": 120,
   }
```

**SQL-Beispiel (Einfache Suche):**

```sql
-- Query: "palabra", Mode: "text", Country: ARG, Speaker: pro
SELECT * FROM tokens t1
WHERE t1.text LIKE "%palabra%"
  AND t1.country_code IN ("ARG")
  AND t1.speaker_type = "pro"
ORDER BY t1.text ASC
LIMIT 25 OFFSET 0
```

**SQL-Beispiel (Token-IDs, Input-Reihenfolge):**

```sql
-- Token-IDs: ["TOKEN1", "TOKEN2", "TOKEN3"]
SELECT * FROM tokens
WHERE token_id IN ("TOKEN1", "TOKEN2", "TOKEN3")
  AND country_code IN ("ARG", "MEX")
ORDER BY 
  CASE 
    WHEN token_id = "TOKEN1" THEN 0
    WHEN token_id = "TOKEN2" THEN 1
    WHEN token_id = "TOKEN3" THEN 2
    ELSE 999999
  END,
  start ASC
LIMIT 25 OFFSET 0
```

---

## Frontend-Architektur

### ES6-Module

```
static/js/modules/corpus/
├── index.js                 # Main Entry Point (CorpusApp)
├── init.js                  # Initialization Utilities
├── datatables.js            # CorpusDatatablesManager (Server-Side)
├── filters.js               # CorpusFiltersManager (Select2)
├── search.js                # CorpusSearchManager (Form + Navigation)
├── tokens.js                # CorpusTokenManager (Tagify)
├── audio.js                 # CorpusAudioManager (Player Integration)
├── config.js                # Constants (REGIONAL_OPTIONS, SELECT2_CONFIG)
├── api.js                   # API-Calls (falls vorhanden)
├── state.js                 # Global State Management (optional)
├── render.js                # Rendering Utilities (optional)
```

### Main Entry Point: `CorpusApp`

**Datei:** `static/js/modules/corpus/index.js`

```javascript
class CorpusApp {
  async initialize() {
    // 1. Warten auf externe Dependencies
    await this.waitForDependencies()
    
    // 2. Komponenten initialisieren
    this.filters = new CorpusFiltersManager()
    this.filters.initialize()
    
    this.datatables = new CorpusDatatablesManager()
    this.datatables.initialize()
    
    this.search = new CorpusSearchManager(this.filters)
    this.search.initialize()
    
    this.tokens = new CorpusTokenManager()
    this.tokens.initialize()
    
    this.audio = new CorpusAudioManager()
    this.audio.initialize()
    
    this.isInitialized = true
  }
}

// Globale Instanz
window.corpusApp = new CorpusApp()
window.addEventListener('DOMContentLoaded', () => window.corpusApp.initialize())
```

### Component: `CorpusDatatablesManager`

**Zweck:** DataTables mit Server-Side Processing verwalten

**Key Methods:**

```javascript
initialize() {
  // 1. DataTables Plugin initialisieren
  this.table = new DataTable('#corpus-table', {
    serverSide: true,
    processing: true,
    
    // AJAX an Backend
    ajax: {
      url: '/corpus/search/datatables',
      type: 'GET',
      data: (d) => this.buildAjaxData(d),  // Converter für DataTables Format
      traditional: true,                   // Array-Serialisierung
      dataSrc: 'data'
    },
    
    // Spalten (12 sichtbar + 4 versteckt = 16 Spalten)
    columns: this.buildColumns(),
    
    // Buttons (Export, etc.)
    buttons: this.buildExportButtons(),
    
    // Callbacks
    initComplete: () => this.adjustColumns(),
    drawCallback: () => this.updateAudioButtons()
  })
}

buildAjaxData(datatablesData) {
  // Converter: DataTables Format → Backend Format
  // Input: { draw, start, length, search, order, ... }
  // Output: { query, search_mode, country_code[], ..., search[value], ... }
  
  const params = new URLSearchParams()
  params.append('query', window.searchQuery)
  params.append('search_mode', window.searchMode)
  
  // Filter aus URL kopieren
  this.urlParams.forEach((value, key) => {
    if (key !== 'query' && key !== 'search_mode') {
      params.append(key, value)
    }
  })
  
  // DataTables Parameter
  params.append('draw', datatablesData.draw)
  params.append('start', datatablesData.start)
  params.append('length', datatablesData.length)
  params.append('search[value]', datatablesData.search.value)
  // Ordering
  if (datatablesData.order.length > 0) {
    params.append('order[0][column]', datatablesData.order[0].column)
    params.append('order[0][dir]', datatablesData.order[0].dir)
  }
  
  return params.toString()
}

buildColumns() {
  // 16 Spalten definieren (12 sichtbar, 4 versteckt)
  return [
    { data: 0, title: '#', orderable: false },
    { data: 1, title: 'Ctx.←', orderable: false },
    { data: 2, title: 'Palabra', orderable: true },
    { data: 3, title: 'Ctx.→', orderable: false },
    { data: 4, title: 'Audio', orderable: false, render: this.renderAudioButton },
    { data: 5, title: 'País', orderable: true },
    { data: 6, title: 'Hablante', orderable: true },
    { data: 7, title: 'Sexo', orderable: true },
    { data: 8, title: 'Modo', orderable: true },
    { data: 9, title: 'Discurso', orderable: true },
    { data: 10, title: 'Token-ID', orderable: true },
    { data: 11, title: 'Archivo', orderable: true },
    // Versteckt:
    { data: 12, visible: false },  // start
    { data: 13, visible: false },  // end
    { data: 14, visible: false },  // context_start
    { data: 15, visible: false }   // context_end
  ]
}

renderAudioButton(data, type, row) {
  // data: audio_available (boolean)
  // row: [0: idx, 1: ctx_left, 2: text, ..., 12: start, 13: end, ...]
  if (!data) {
    return '<span class="text-muted">N/A</span>'
  }
  const start = row[12]
  const end = row[13]
  return `<button class="btn-audio" data-start="${start}" data-end="${end}">▶</button>`
}

updateAudioButtons() {
  // Audio-Player Event-Handler an neue Buttons binden
  document.querySelectorAll('.btn-audio').forEach(btn => {
    btn.addEventListener('click', this.audio.playClip.bind(this.audio))
  })
}
```

### Component: `CorpusFiltersManager`

**Zweck:** Select2-Filter und Regional-Checkbox verwalten

```javascript
class CorpusFiltersManager {
  initialize() {
    // 1. Select2 enhancen
    $('#filter-country-national').select2(SELECT2_CONFIG)
    $('#filter-speaker').select2(SELECT2_CONFIG)
    $('#filter-sex').select2(SELECT2_CONFIG)
    $('#filter-mode').select2(SELECT2_CONFIG)
    $('#filter-discourse').select2(SELECT2_CONFIG)
    
    // 2. Event-Handler binden
    this.regionalCheckbox.addEventListener('change', 
      () => this.onRegionalToggle()
    )
  }
  
  onRegionalToggle() {
    // Regional-Checkbox geändert
    // Filter-Logik: Regional-Optionen zeigen/verstecken
    const isChecked = this.regionalCheckbox.checked
    const countrySelect = $(this.countrySelect)
    
    if (isChecked) {
      // Regional-Codes anzeigen
      REGIONAL_OPTIONS.forEach(opt => {
        if (!countrySelect.find(`option[value="${opt.code}"]`).length) {
          countrySelect.append(`<option value="${opt.code}">${opt.name}</option>`)
        }
      })
    } else {
      // Regional-Codes verstecken
      REGIONAL_OPTIONS.forEach(opt => {
        countrySelect.find(`option[value="${opt.code}"]`).remove()
      })
      countrySelect.val(null).trigger('change')
    }
  }
  
  getFilterValues() {
    return {
      countries: $('#filter-country-national').val() || [],
      includeRegional: this.regionalCheckbox.checked,
      speaker: $('#filter-speaker').val() || [],
      sex: $('#filter-sex').val() || [],
      mode: $('#filter-mode').val() || [],
      discourse: $('#filter-discourse').val() || []
    }
  }
}
```

### Component: `CorpusTokenManager`

**Zweck:** Token-ID-Input mit Tagify verwalten

```javascript
class CorpusTokenManager {
  initTagify() {
    // Tagify initialisieren
    this.tagify = new Tagify(this.tokenInput, {
      delimiters: ',;\\s\\n\\r\\t',      // Separatoren
      pattern: /^[A-Za-z0-9-]+$/,        // Validierungsmuster
      duplicates: false,
      maxTags: 2000,
      editTags: 1,
      enforceWhitelist: false,
      dropdown: { enabled: 0 }
    })
    
    // Drag-Drop mit SortableJS
    Sortable.create(this.tagify.DOM.scope, {
      animation: 150,
      draggable: '.tagify__tag',
      onEnd: () => this.tagify.updateValueByDOMTags()
    })
  }
  
  onTokenApplyClick() {
    // Token-IDs aus Input lesen
    const tokenIds = this.tagify.value.map(tag => tag.value).join(',')
    
    // Versteckt-Feld aktualisieren
    this.hiddenTokens.value = tokenIds
    
    // Search-Mode Override setzen
    this.searchModeOverride.value = 'token_ids'
    
    // Form absenden
    this.form.submit()
  }
}
```

### Component: `CorpusSearchManager`

**Zweck:** Formular-Submit und Navigation

```javascript
class CorpusSearchManager {
  bindFormSubmit() {
    this.form.on('submit', (e) => {
      e.preventDefault()
      
      // URL-Parameter bauen
      const params = new URLSearchParams()
      params.append('query', this.form.find('input[name="query"]').val())
      params.append('search_mode', this.form.find('select[name="search_mode"]').val())
      
      // Filter hinzufügen
      const filters = this.filtersManager.getFilterValues()
      filters.countries.forEach(c => params.append('country_code', c))
      if (filters.includeRegional) params.append('include_regional', '1')
      // ... weitere Filter
      
      // Navigieren
      window.location.href = '/corpus/search?' + params.toString()
    })
  }
}
```

---

## Datenfluss

### Szenario: Einfache Wortsuche

```
1. USER ACTION
   ↓
   Benutzer gibt "palabra" ein, wählt Land "ARG", klickt "Buscar"
   
2. FRONTEND
   ↓
   CorpusSearchManager.bindFormSubmit()
   → buildSearchParams() → URL mit query=palabra&country_code=ARG&search_mode=text
   → window.location.href = '/corpus/search?...'
   
3. BROWSER
   ↓
   GET /corpus/search?query=palabra&country_code=ARG&search_mode=text
   
4. BACKEND (Route Handler)
   ↓
   corpus.search()
   → _parse_token_ids() → []
   → SearchParams(query="palabra", search_mode="text", countries=["ARG"], ...)
   → search_tokens(params)
   
5. BACKEND (Service Layer)
   ↓
   corpus_search.search_tokens()
   → _build_word_query(["palabra"], "text", exact=False)
     → SQL: SELECT * FROM tokens t WHERE t.text LIKE "%palabra%"
   → _append_in_clause(..., "country_code", ["ARG"])
     → Filter: AND country_code IN ("ARG")
   → LIMIT/OFFSET für page=1, page_size=25
   → Execute: SELECT * FROM tokens WHERE text LIKE "%palabra%" AND country_code IN ("ARG") LIMIT 25
   → Result: Dict mit items, total, unique_countries, etc.
   
6. BACKEND (Template Rendering)
   ↓
   _render_corpus(context)
   → render_template("pages/corpus.html", results=[...], total_results=234, ...)
   
7. FRONTEND (HTML Response)
   ↓
   <table id="corpus-table"> mit Ergebnissen
   
8. FRONTEND (DataTables Initialization)
   ↓
   CorpusDatatablesManager.initialize()
   → DataTable('#corpus-table', { serverSide: true, ajax: {...} })
   → AJAX → GET /corpus/search/datatables?draw=1&start=0&length=25&query=palabra&...
   
9. BACKEND (DataTables Endpoint)
   ↓
   corpus.search_datatables()
   → Parse DataTables parameters
   → search_tokens(params) mit table_search, ordering, pagination
   → Format Response als JSON: { draw, recordsTotal, recordsFiltered, data: [...] }
   
10. FRONTEND (DataTables Rendering)
    ↓
    DataTable empfängt JSON
    → Rows rendern: [idx, ctx_left, word, ctx_right, audio_btn, country, ...]
    → Buttons binden (Audio-Player, etc.)
```

### Szenario: Token-ID-Suche

```
1. USER ACTION
   ↓
   Benutzer gibt Token-IDs "TOKEN1, TOKEN2, TOKEN3" ein in Token-Tab
   
2. FRONTEND (Token Manager)
   ↓
   CorpusTokenManager.onTokenApplyClick()
   → tagify.value = [{ value: "TOKEN1" }, { value: "TOKEN2" }, { value: "TOKEN3" }]
   → hiddenTokens.value = "TOKEN1,TOKEN2,TOKEN3"
   → searchModeOverride.value = "token_ids"
   → form.submit()
   
3. BROWSER
   ↓
   POST /corpus/search (wegen Tagify-Form-Submit)
   Body: token_ids=TOKEN1,TOKEN2,TOKEN3&search_mode_override=token_ids
   
4. BACKEND (Route Handler)
   ↓
   corpus.search()
   → data_source = request.form
   → search_mode = search_mode_override → "token_ids"
   → _parse_token_ids() → ["TOKEN1", "TOKEN2", "TOKEN3"]
   → SearchParams(search_mode="token_ids", token_ids=["TOKEN1", ...], ...)
   → search_tokens(params)
   
5. BACKEND (Service Layer)
   ↓
   corpus_search.search_tokens()
   → token_ids normalisieren → ["TOKEN1", "TOKEN2", "TOKEN3"]
   → Filter: WHERE token_id IN ("TOKEN1", "TOKEN2", "TOKEN3")
   → ORDER BY: CASE WHEN token_id = "TOKEN1" THEN 0 ... END (Input-Reihenfolge beibehalten!)
   → Execute: SELECT * FROM tokens WHERE token_id IN (...) ORDER BY CASE ... LIMIT 25
   → Result: 3 Rows in der gewünschten Reihenfolge
   
6. BACKEND (Template Rendering)
   ↓
   context['active_tab'] = 'tab-token'  # Token-Tab aktiv
   → render_template("pages/corpus.html", ...)
   
7. FRONTEND (HTML Response)
   ↓
   Seite mit Token-Tab aktiv, Ergebnisse in Tabelle
```

---

## DataTables-Mapping

### Request-Flow

```
Frontend (User Interaction)
  ↓
DataTables: sort, filter, paginate
  ↓
buildAjaxData(datatablesData)
  ↓
Convert: DataTables Format → Backend Format
  ↓
AJAX GET /corpus/search/datatables?query=...&search_mode=...&draw=...&start=...&length=...&order[0][column]=...
  ↓
Backend: search_datatables()
  ↓
Parse Parameters
  ↓
search_tokens(SearchParams(...))
  ↓
Execute SQL mit Ordering, LIMIT, OFFSET
  ↓
Format Response als DataTables JSON
  ↓
Return: { draw, recordsTotal, recordsFiltered, data: [...] }
  ↓
DataTables: Render Table, bind Event-Handler
  ↓
Frontend: User sieht Ergebnisse, kann sortieren/filtern
```

### Column Index Mapping

```javascript
// Frontend DataTables Columns (buildColumns)
[
  { data: 0, title: '#' },              // Index 0: Row number
  { data: 1, title: 'Ctx.←' },          // Index 1: context_left
  { data: 2, title: 'Palabra' },        // Index 2: text (SORTIERBAR)
  { data: 3, title: 'Ctx.→' },          // Index 3: context_right
  { data: 4, title: 'Audio' },          // Index 4: audio_available boolean
  { data: 5, title: 'País' },           // Index 5: country_code (SORTIERBAR)
  { data: 6, title: 'Hablante' },       // Index 6: speaker_type (SORTIERBAR)
  { data: 7, title: 'Sexo' },           // Index 7: sex (SORTIERBAR)
  { data: 8, title: 'Modo' },           // Index 8: mode (SORTIERBAR)
  { data: 9, title: 'Discurso' },       // Index 9: discourse (SORTIERBAR)
  { data: 10, title: 'Token-ID' },      // Index 10: token_id (SORTIERBAR)
  { data: 11, title: 'Archivo' },       // Index 11: filename (SORTIERBAR)
  // Versteckt:
  { data: 12, visible: false },         // Index 12: start (Zeit)
  { data: 13, visible: false },         // Index 13: end (Zeit)
  { data: 14, visible: false },         // Index 14: context_start
  { data: 15, visible: false }          // Index 15: context_end
]

// Backend Column Map (search_datatables)
column_map = {
  0: "",                  // # → kein Sort
  1: "",                  // Ctx.← → kein Sort
  2: "text",              // Palabra → text
  3: "",                  // Ctx.→ → kein Sort
  4: "",                  // Audio → kein Sort
  5: "country_code",      // País → country_code
  6: "speaker_type",      // Hablante → speaker_type
  7: "sex",               # Sexo → sex
  8: "mode",              # Modo → mode
  9: "discourse",         # Discurso → discourse
  10: "token_id",         # Token-ID → token_id
  11: "filename"          # Archivo → filename
}
```

### DataTables Response Format

```json
{
  "draw": 1,
  "recordsTotal": 12345,        // Gesamtzahl ohne Filterung
  "recordsFiltered": 234,       // Gesamtzahl mit Filterung (hier: = recordsTotal)
  "data": [
    [
      1,                        // 0: Row Index
      "el",                     // 1: context_left
      "palabra",                // 2: text (Wort)
      "siguiente",              // 3: context_right
      true,                     // 4: audio_available
      "ARG",                    // 5: country_code
      "pro",                    // 6: speaker_type
      "m",                      // 7: sex
      "lectura",                // 8: mode
      "general",                // 9: discourse
      "ARG_RN_20050101_001_00000042",  // 10: token_id
      "ARG_RN_20050101_001.mp3",       // 11: filename
      45.123,                   // 12: start (hidden)
      45.567,                   // 13: end (hidden)
      44.0,                     // 14: context_start (hidden)
      47.0                      // 15: context_end (hidden)
    ],
    // ... weitere Rows
  ]
}
```

---

## Filterlogik

### Standard-Filter

**Backend-Filter (alle kombiniert mit AND):**

```sql
WHERE
  (query conditions - word LIKE oder token_id IN)
  AND country_code IN (...)
  AND speaker_type IN (...)
  AND sex IN (...)
  AND mode IN (...)
  AND discourse IN (...)
  AND (table_search conditions)  # DataTables search-box
```

### Länder-Filter-Logik

```
Benutzeraktion:
  1. Checkbox "Incluir emisoras regionales" ist UNCHECKED (default)
     → Nur nationale Codes: ARG, BOL, CHL, ..., VEN (19 total)
  
  2. Benutzer checkt "Incluir emisoras regionales"
     → Nationale + Regionale Codes: ... + ARG-CHU, ARG-CBA, ARG-SDE, ESP-CAN, ESP-SEV (24 total)
  
  3. Benutzer wählt spezifische Länder (z.B. ARG, MEX)
     → Nur diese (und regional abhängig von Checkbox)

Backend-Logik (corpus.py, search()):
```python
if not countries:
    if include_regional:
        countries = national_codes + regional_codes  # 24
    else:
        countries = national_codes  # 19
elif not include_regional:
    # Regional-Codes herausfiltern, falls regional_checkbox OFF
    countries = [c for c in countries if c not in regional_codes]
```

### DataTables Search (table_search)

Benutzer gibt Text in DataTables-SearchBox ein:

```javascript
search[value]=palabra
```

Backend wendet **Volltext-OR-Filter** an:

```python
if params.table_search:
    search_term = f"%{params.table_search}%"
    filters.append(f"({
      text LIKE ?
      OR context_left LIKE ?
      OR context_right LIKE ?
      OR country_code LIKE ?
      OR speaker_type LIKE ?
      OR sex LIKE ?
      OR mode LIKE ?
      OR discourse LIKE ?
      OR token_id LIKE ?
      OR filename LIKE ?
    })")
    filter_params.extend([search_term] * 10)
```

---

## Implementierte Suchfunktionen

### 1. Einfache Wortsuche (Simple Search) ✅

**Status:** Aktiv

**UI:** Tab "Búsqueda simple"

**Suchfelder:**
- Suchtext (Query): "palabra" → text LIKE "%palabra%"
- Suchmode-Dropdown: text | text_exact | lemma | lemma_exact

**Filter:**
- Land (multi-select)
- Include Regional (checkbox)
- Hablante (multi-select): pro, otro
- Sexo (multi-select): m, f
- Modo (multi-select): pre, lectura, libre
- Discurso (multi-select): general, tiempo, tránsito

**Button:** "Buscar" → POST /corpus/search

**Ergebnis:**
- Datentabelle mit 12 Spalten
- Server-Side Pagination (DataTables)
- Sortierbar nach: Palabra, País, Hablante, Sexo, Modo, Discurso, Token-ID, Archivo
- DataTables Search-Box für Volltext-Filterung

### 2. Token-ID-Suche (Token Search) ✅

**Status:** Aktiv

**UI:** Tab "Token"

**Suchfeld:**
- Token-IDs (Tagify Input): Komma-getrennte Token-IDs
- Beispiel: "TOKEN1, TOKEN2, TOKEN3"

**Features:**
- Drag-Drop zum Reordern (Sortable.js)
- Paste-Support (mehrere Token auf einmal)
- Max 2000 Tokens

**Button:** "Buscar" → POST /corpus/search mit search_mode_override=token_ids

**Ergebnis:**
- Tokens in **Input-Reihenfolge** angezeigt (CASE WHEN order by)
- Sonst gleich wie Simple Search

### 3. Statistiken (Statistics) ✅

**Status:** Aktiv (als Sub-Tab unter "Búsqueda simple")

**UI:** Sub-Tab "Estadísticas" (neben "Resultados")

**Charts:**
- By Country (ECharts, toggle count/percent)
- By Speaker Type (pro/otro)
- By Sex (m/f)
- By Mode (pre/lectura/libre)
- By Discourse (general/tiempo/tránsito)

**Filter:**
- Country-Filter dropdown

**Quelle:** Backend liefert Stats via `/corpus/stats` (falls vorhanden)

---

## Geplante erweiterte Suche

### 3. Erweiterte Suche (Advanced Search) 🚧

**Status:** Geplant, aktuell deaktiviert (`disabled` Attribut im HTML)

**Geplante Features:**

| Feature | Beschreibung | Beispiel |
|---------|-----------|---------|
| Multi-Word Sequenzen | Mehrere Wörter in Sequenz | "el" + "gato" + "negro" |
| Wildcards | Platzhalter in Wort | "pa*bra" |
| POS-Filter | Part-of-Speech-Filter | Noun, Verb, Adjective |
| Phonetic Search | Phonetische Suche | Ähnlich klingende Wörter |
| Frequenz-Range | Häufigkeits-Filter | Top 100, Bottom 10% |
| Kombinierte Bedingungen | AND/OR/NOT Logic | (Wort1 OR Wort2) AND NOT Wort3 |
| Regular Expressions | Regex-Support | /^[a-z]{3,5}$/ |

**Backend-Anforderungen:**
- SQL-Builder mit erweiterten JOINs (Word-Sequenzen)
- Regex-Support (SQLite REGEXP oder Python-Fallback)
- POS-Daten in DB (falls nicht vorhanden: Migration erforderlich)
- Query-Parser für komplexe Ausdrücke
- Performance-Optimierung (Indexing für neue Suchtypen)

**Frontend-Anforderungen:**
- Query-Builder UI (visual/code-based)
- Preview/Validation
- Saved Queries
- Example-Suggestions

---

## Siehe auch

- [Database Schema Reference](database-schema.md) - Detaillierte DB-Struktur mit allen Indizes
- [How To: Corpus Advanced Search Implementation](../how-to/corpus-advanced-search.md) - Schritt-für-Schritt-Guide für erweiterte Suche
- [Authentication Flow](../concepts/authentication-flow.md) - JWT-basierte Audio-Authentifizierung
- [API Reference](api-reference.md) - Alle REST-Endpoints dokumentiert
- [Deployment Guide](../operations/deployment.md) - Production-Setup mit Datenbankoptimierung
