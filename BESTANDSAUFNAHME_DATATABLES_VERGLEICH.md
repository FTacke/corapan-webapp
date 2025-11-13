# Abschnitt 4: DataTables-Konfiguration (Frontend) – Simple vs. Advanced

## 4.1 Simple Search – DataTables Init

**Datei:** `static/js/modules/corpus/datatables.js`  
**Klasse:** `CorpusDatatablesManager`  
**Initialisierung:** L39-100

### Code-Snippet (buildColumns)

**Datei:** `static/js/modules/corpus/datatables.js`  
**Zeilen:** L241-310

```javascript
buildColumns() {
    return [
        // Row number (computed)
        { 
            data: 'row_number', 
            width: '40px', 
            className: 'center-align',
            render: (data) => data || ''
        },
        
        // Left context
        {
            data: 'context_left',
            width: '200px',
            className: 'right-align',
            render: (data) => `<span class="md3-corpus-context">${data || ''}</span>`
        },
        
        // Result (keyword)
        {
            data: 'text',
            width: '150px',
            className: 'center-align',
            render: (data, type, row) => {
                return `<span class="md3-corpus-keyword" 
                              data-filename="${row.filename}" 
                              data-start="${row.start}" 
                              data-end="${row.end}">${data || ''}</span>`;
            }
        },
        
        // Right context
        {
            data: 'context_right',
            width: '200px',
            render: (data) => `<span class="md3-corpus-context">${data || ''}</span>`
        },
        
        // Audio Player
        {
            data: 'audio_available',
            orderable: false,
            searchable: false,
            className: 'center-align',
            width: '120px',
            render: (data, type, row) => this.renderAudioButtons(row)
        },
        
        // Metadata columns (using object keys)
        { data: 'country_code', width: '80px' },   // País
        { data: 'speaker_type', width: '80px' },   // Hablante
        { data: 'sex', width: '80px' },            // Sexo
        { data: 'mode', width: '80px' },           // Modo
        { data: 'discourse', width: '80px' },      // Discurso
        { 
            data: 'token_id', 
            width: '100px',
            render: (data) => `<span class="token-id">${data || ''}</span>`
        },
        
        // Archivo (File icon with player link)
        {
            data: 'filename',
            width: '80px',
            className: 'center-align',
            orderable: true,
            render: (data, type, row) => this.renderFileLink(data, type, row)
        }
    ];
}
```

**Merkmale:**
- **Objekt-Mode:** `data: 'key_name'` (nicht Index!)
- Alle Felder aus `CANON_COLS` verfügbar via Keys
- Render-Funktionen greifen auf `row.fieldname` zu

---

## 4.2 Advanced Search – DataTables Init

**Datei:** `static/js/modules/advanced/initTable.js`  
**Funktion:** `initAdvancedTable(queryParams)`  
**Zeilen:** L54-231

### Code-Snippet (columnDefs)

**Datei:** `static/js/modules/advanced/initTable.js`  
**Zeilen:** L93-207

```javascript
columnDefs: [
  // Column 0: Row number (#)
  {
    targets: 0,
    render: function(data, type, row, meta) {
      return meta.row + meta.settings._iDisplayStart + 1;
    },
    width: '40px',
    searchable: false,
    orderable: false
  },
  // Column 1: Context left
  {
    targets: 1,
    data: 'left',
    render: function(data) {
      return escapeHtml(data || '');
    },
    className: 'md3-datatable__cell--context'
  },
  // Column 2: Match (KWIC) - highlighted
  {
    targets: 2,
    data: 'match',
    render: function(data) {
      return `<mark>${escapeHtml(data || '')}</mark>`;
    },
    className: 'md3-datatable__cell--match'
  },
  // Column 3: Context right
  {
    targets: 3,
    data: 'right',
    render: function(data) {
      return escapeHtml(data || '');
    },
    className: 'md3-datatable__cell--context'
  },
  // Column 4: Audio player
  {
    targets: 4,
    data: null,
    render: function(data, type, row) {
      if (!row.start_ms || !row.filename) {
        return '<span class="md3-datatable__empty">-</span>';
      }
      const startMs = parseInt(row.start_ms) || 0;
      const endMs = parseInt(row.end_ms) || startMs + 5000;
      const audioUrl = `/media/segment/${encodeURIComponent(row.filename)}/${startMs}/${endMs}`;
      return `<audio controls style="width: 150px; height: 30px;">
        <source src="${audioUrl}" type="audio/mpeg">
      </audio>`;
    },
    orderable: false,
    className: 'md3-datatable__cell--audio'
  },
  // Column 5-11: Metadata
  { targets: 5, data: 'country' },
  { targets: 6, data: 'speaker_type' },
  { targets: 7, data: 'sex' },
  { targets: 8, data: 'mode' },
  { targets: 9, data: 'discourse' },
  { targets: 10, data: 'tokid' },
  { targets: 11, data: 'filename' }
]
```

**Merkmale:**
- **ABER:** Backend liefert ARRAYS! (`data: [[...], [...]]`)
- Frontend definiert Keys (`data: 'left'`, `data: 'match'`, etc.)
- **Inkonsistenz:** Backend-Arrays werden automatisch auf Keys gemappt?

**ACHTUNG:** Hier liegt ein **potenzieller Bug**! 

- Backend `advanced_api.py` L277-291 liefert **Arrays**:
  ```python
  processed_hits.append([
      row["left"],      # Index 0
      row["match"],     # Index 1
      row["right"],     # Index 2
      # ...
  ])
  ```

- Frontend erwartet aber **Objekte** mit Keys (`data: 'left'`)?

**Mögliche Erklärung:**
- DataTables kann beide Formate verarbeiten
- Wenn `columns[i].data = 'key'` gesetzt ist, aber Backend Arrays liefert, mappt DataTables automatisch Index → Key
- **ABER:** Das ist fragil! Besser: Backend sollte auch Objekte liefern.

---

## 4.3 Vergleichstabelle Simple vs. Advanced

| Spalte im UI | Simple: `data` Key | Advanced: `data` Key | Backend-Quelle Simple | Backend-Quelle Advanced |
|--------------|--------------------|----------------------|-----------------------|-------------------------|
| **#** (Row Number) | `row_number` | *(computed via meta.row)* | Backend: `row_number` | Frontend: berechnet |
| **Ctx.←** | `context_left` | `left` | DB: `context_left` | BlackLab: `left.word` |
| **Resultado/Match** | `text` | `match` | DB: `text` | BlackLab: `match.word` |
| **Ctx.→** | `context_right` | `right` | DB: `context_right` | BlackLab: `right.word` |
| **Audio** | `audio_available` + render | `null` + render | Backend: berechnet | Frontend: rendert Audio-Tag |
| **País** | `country_code` | `country` | DB: `country_code` | BlackLab: `metadata.country` |
| **Hablante** | `speaker_type` | `speaker_type` | DB: `speaker_type` | BlackLab: `metadata.speaker_type` |
| **Sexo** | `sex` | `sex` | DB: `sex` | BlackLab: `metadata.sex` |
| **Modo** | `mode` | `mode` | DB: `mode` | BlackLab: `metadata.mode` |
| **Discurso** | `discourse` | `discourse` | DB: `discourse` | BlackLab: `metadata.discourse` |
| **Token-ID** | `token_id` | `tokid` | DB: `token_id` | BlackLab: `match.tokid[0]` |
| **Archivo** | `filename` + render | `filename` | DB: `filename` | BlackLab: `metadata.filename` |

### Unterschiede

| Aspekt | Simple | Advanced |
|--------|--------|----------|
| **Response-Format** | Objekte: `[{key: val}, ...]` | **Arrays:** `[[val, val, ...]]` (aber Frontend erwartet Keys?) |
| **Context-Keys** | `context_left`, `context_right` | `left`, `right` |
| **Country-Key** | `country_code` | `country` |
| **TokenID-Key** | `token_id` | `tokid` |
| **Audio-Rendering** | Backend berechnet `audio_available`, Frontend rendert 2 Buttons | Frontend rendert Audio-Tag direkt |
| **Row-Number** | Backend liefert mit | Frontend berechnet |

### Gemeinsame Felder (semantisch identisch)

Diese Felder haben die **gleiche Bedeutung**, aber **unterschiedliche Namen**:

| Semantisches Feld | Simple Key | Advanced Key | Vorschlag Unified |
|-------------------|------------|--------------|-------------------|
| Kontext links | `context_left` | `left` | `context_left` (bevorzugt, expliziter) |
| Kontext rechts | `context_right` | `right` | `context_right` |
| Land | `country_code` | `country` | `country_code` (Standard ISO-Code) |
| Token-ID | `token_id` | `tokid` | `token_id` (vollständiger Name) |
| Treffer | `text` | `match` | `text` oder `match` (beides OK) |

---

## 4.4 Empfehlung für gemeinsames Mapping

### Ziel: Unified Response Format

**Beide Endpoints sollten identische Objekt-Strukturen liefern:**

```json
{
  "draw": 1,
  "recordsTotal": 342,
  "recordsFiltered": 342,
  "data": [
    {
      "row_number": 1,
      "context_left": "en la",
      "text": "casa",                    // oder "match"
      "context_right": "de mis padres",
      "country_code": "ARG",             // unified: nicht "country"
      "speaker_type": "pro",
      "sex": "m",
      "mode": "pre",
      "discourse": "general",
      "token_id": "ARG_..._00123",       // unified: nicht "tokid"
      "filename": "ARG_pro_m_pre_general_001.mp3",
      "start": 42.5,                     // Simple: sekunden, Advanced: ms → unified?
      "end": 43.2,
      "audio_available": true,           // Helper-Feld
      "word_count": 1                    // Helper-Feld
    }
  ]
}
```

### Kandidat für gemeinsame Helper-Funktion

**Ort:** `src/app/services/corpus_search.py` (bereits vorhanden für Simple)  
**Funktion:** `serialize_hit_to_row(hit, source='db')` 

```python
def serialize_hit_to_row(hit: dict | sqlite3.Row, source: str = 'db') -> dict:
    """
    Konvertiert Hit (DB oder BlackLab) zu DataTables-Zeile mit CANON_COLS Keys.
    
    Args:
        hit: Hit-Objekt (sqlite3.Row oder BlackLab-JSON-Dict)
        source: 'db' (Simple) oder 'blacklab' (Advanced)
    
    Returns:
        Dict mit stabilen Keys für DataTables
    """
    if source == 'db':
        # Simple: Hit ist sqlite3.Row
        return _row_to_dict(hit)  # Bereits vorhanden!
    
    elif source == 'blacklab':
        # Advanced: Hit ist BlackLab-JSON
        left = hit.get("left", {}).get("word", [])
        match = hit.get("match", {}).get("word", [])
        right = hit.get("right", {}).get("word", [])
        
        match_info = hit.get("match", {})
        metadata = hit.get("metadata", {})
        
        return {
            "context_left": " ".join(left[-10:]) if left else "",
            "text": " ".join(match),  # oder "match"
            "context_right": " ".join(right[:10]) if right else "",
            "country_code": metadata.get("country", ""),
            "speaker_type": metadata.get("speaker_type", ""),
            "sex": metadata.get("sex", ""),
            "mode": metadata.get("mode", ""),
            "discourse": metadata.get("discourse", ""),
            "token_id": match_info.get("tokid", [None])[0] or "",
            "filename": metadata.get("filename", ""),
            "start": match_info.get("start_ms", [0])[0] / 1000 if match_info.get("start_ms") else 0,
            "end": match_info.get("end_ms", [0])[0] / 1000 if match_info.get("end_ms") else 0,
            "audio_available": True,  # Vereinfachung: BL-Hits haben immer Audio
            "word_count": len(match) if match else 1,
        }
```

**Nutzung in Advanced:**

```python
# advanced_api.py L240-291
processed_hits = []
for hit in hits:
    row_obj = serialize_hit_to_row(hit, source='blacklab')
    processed_hits.append(row_obj)  # Jetzt Objekte, nicht Arrays!
```

**Vorteil:**
- Beide Endpoints liefern identische Strukturen
- Frontend-Code kann identisch sein
- Wartbarkeit: Mapping-Logik zentral
