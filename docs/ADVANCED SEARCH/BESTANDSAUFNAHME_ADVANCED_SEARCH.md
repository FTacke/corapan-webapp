# Abschnitt 3: Advanced-Search – Backend-Datenfluss und Mapping

## 3.1 Flask-Route Advanced Search (HTML-Seite)

**Route-Funktion:** `index()`  
**URL-Pattern:** `/search/advanced`  
**Datei:** `src/app/search/advanced.py`  
**Zeilen:** L17-25

### Code-Snippet

```python
@bp.route("", methods=["GET"])
def index():
    """
    Render advanced search form.
    
    Returns:
        HTML template with MD3 form + empty results container
    """
    return render_template("search/advanced.html")
```

**Beschreibung:**
- Rendert das Template `templates/search/advanced.html`
- Nur GET-Methode
- Keine Parameter verarbeitet (statische Formularseite)
- Form-Submission erfolgt direkt an DataTables-Endpoint

---

## 3.2 Flask-Route Advanced Search DataTables-Endpoint

**Route-Funktion:** `datatable_data()`  
**URL-Pattern:** `/search/advanced/data`  
**Datei:** `src/app/search/advanced_api.py`  
**Zeilen:** L100-373

### Code-Snippet (Kernlogik)

```python
@bp.route("/data", methods=["GET"])
@limiter.limit("30 per minute")
def datatable_data():
    """DataTables Server-Side processing endpoint."""
    
    # Extract DataTables parameters
    draw = get_int("draw", 1)
    start = get_int("start", 0)
    length = min(get_int("length", 50), MAX_HITS_PER_PAGE)  # Capped at 100
    
    # Build CQL pattern
    cql_pattern = build_cql(request.args)
    
    # Validate CQL
    try:
        validate_cql_pattern(cql_pattern)
    except CQLValidationError as e:
        return jsonify({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "invalid_cql",
            "message": str(e)
        }), 200
    
    # Build filters
    filters = build_filters(request.args)
    validate_filter_values(filters)
    filter_query = filters_to_blacklab_query(filters)
    
    # BLS parameters
    bls_params = {
        "first": start,
        "number": length,
        "wordsaroundhit": 10,
        "listvalues": "tokid,start_ms,end_ms,country,speaker_type,sex,mode,discourse,filename,radio",
    }
    
    if filter_query:
        bls_params["filter"] = filter_query
    
    # Try CQL parameter names (patt, cql, cql_query)
    response = _make_bls_request("/corapan/hits", {**bls_params, "patt": cql_pattern})
    
    # Parse response
    data = response.json()
    summary = data.get("summary", {})
    hits = data.get("hits", [])
    
    # Process hits for DataTable
    processed_hits = []
    for hit in hits:
        left = hit.get("left", {}).get("word", [])
        match = hit.get("match", {}).get("word", [])
        right = hit.get("right", {}).get("word", [])
        
        # Metadata from hit
        match_info = hit.get("match", {})
        tokid = match_info.get("tokid", [None])[0]
        start_ms = match_info.get("start_ms", [0])[0] if match_info.get("start_ms") else 0
        end_ms = match_info.get("end_ms", [0])[0] if match_info.get("end_ms") else 0
        
        # Document metadata
        hit_metadata = hit.get("metadata", {})
        
        # Build row as ARRAY (not object!)
        processed_hits.append([
            " ".join(left[-10:]) if left else "",      # 0: left
            " ".join(match),                            # 1: match
            " ".join(right[:10]) if right else "",      # 2: right
            hit_metadata.get("country", ""),            # 3: country
            hit_metadata.get("speaker_type", ""),       # 4: speaker_type
            hit_metadata.get("sex", ""),                # 5: sex
            hit_metadata.get("mode", ""),               # 6: mode
            hit_metadata.get("discourse", ""),          # 7: discourse
            hit_metadata.get("filename", ""),           # 8: filename
            hit_metadata.get("radio", ""),              # 9: radio
            str(tokid),                                 # 10: tokid
            f"{start_ms}",                              # 11: start_ms
            f"{end_ms}",                                # 12: end_ms
        ])
    
    return jsonify({
        "draw": draw,
        "recordsTotal": summary.get("numberOfHits", 0),
        "recordsFiltered": summary.get("numberOfHits", 0),
        "data": processed_hits,  # ARRAYS, nicht Objekte!
    })
```

**Wichtige Stellen:**

1. **Request-Parameter-Parsing** (L148-155): DataTables-Parameter + CQL-Query
2. **CQL-Building** (L157): `build_cql(request.args)` → CQL-Pattern-String
3. **Validierung** (L160-171): CQL-Syntax + Filter-Werte prüfen
4. **BlackLab-Request** (L193-222): `_make_bls_request()` mit verschiedenen CQL-Parameternamen
5. **Hit-Verarbeitung** (L241-291): BlackLab-JSON → DataTables-Arrays **(ARRAYS, nicht Objekte!)**

---

## 3.3 BlackLab-Proxy / `_make_bls_request`

**Funktion:** `_make_bls_request()`  
**Datei:** `src/app/search/advanced_api.py`  
**Zeilen:** L43-97

### Code-Snippet

```python
def _make_bls_request(
    path: str,
    params: dict,
    method: str = "GET",
    timeout_override: Optional[float] = None
) -> httpx.Response:
    """
    Make request to BlackLab Server with proper error handling.
    """
    client = get_http_client()
    
    # Clean path (remove /bls/ prefix if present)
    if path.startswith("/bls/"):
        path = path[4:]
    elif path.startswith("bls/"):
        path = "/" + path[4:]
    elif not path.startswith("/"):
        path = "/" + path
    
    # Construct full URL
    full_url = f"{BLS_BASE_URL}{path}"
    
    try:
        response = client.get(full_url, params=params)
        response.raise_for_status()
        return response
    except httpx.TimeoutException:
        logger.error(f"BLS timeout on {path}")
        raise
    except httpx.HTTPStatusError as e:
        logger.error(f"BLS error on {path}: {e.response.status_code}")
        raise
```

**Beschreibung:**
- Basis-URL: `BLS_BASE_URL` (aus Config, z.B. `http://localhost:8080`)
- Pfad: z.B. `/corapan/hits` (kombiniert zu `http://localhost:8080/corapan/hits`)
- Parameter: CQL-Query (`patt` oder `cql`), Filter (`filter`), Paging (`first`, `number`)
- Nutzt zentralen HTTP-Client (httpx) aus `extensions/http_client.py`

### Beispiel-Parameter für BlackLab

```python
{
    "patt": '[word="casa"]',  # CQL-Pattern
    "first": 0,               # Offset
    "number": 50,             # Anzahl Treffer
    "wordsaroundhit": 10,     # Kontext-Wörter links/rechts
    "listvalues": "tokid,start_ms,end_ms,country,speaker_type,sex,mode,discourse,filename,radio",
    "filter": "country:ARG"   # Optional: Metadaten-Filter
}
```

---

## 3.4 Beispiel: Roh-BlackLab-Antwort vs. DataTables-Response

### BlackLab-Roh-Response (gekürzt)

**Request:**
```
GET http://localhost:8080/corapan/hits?
  patt=[word="casa"]
  &first=0
  &number=2
  &wordsaroundhit=10
  &listvalues=tokid,start_ms,end_ms,country,speaker_type,sex,mode,discourse,filename,radio
```

**Response:**
```json
{
  "summary": {
    "searchParam": {
      "patt": "[word="casa"]",
      "first": 0,
      "number": 2,
      "wordsaroundhit": 10
    },
    "searchTime": 245,
    "numberOfHits": 342,
    "numberOfDocs": 85,
    "docsRetrieved": 85,
    "stoppedCountingHits": false,
    "stoppedRetrievingHits": false
  },
  "hits": [
    {
      "docPid": "ARG_pro_m_pre_general_001",
      "start": 123,
      "end": 124,
      "left": {
        "word": ["en", "la"],
        "lemma": ["en", "el"],
        "pos": ["SP", "DA"]
      },
      "match": {
        "word": ["casa"],
        "lemma": ["casa"],
        "pos": ["NC"],
        "tokid": ["ARG_pro_m_pre_general_001_00123"],
        "start_ms": [42500],
        "end_ms": [43200]
      },
      "right": {
        "word": ["de", "mis", "padres"],
        "lemma": ["de", "mi", "padre"],
        "pos": ["SP", "DP", "NC"]
      },
      "metadata": {
        "country": "ARG",
        "speaker_type": "pro",
        "sex": "m",
        "mode": "pre",
        "discourse": "general",
        "filename": "ARG_pro_m_pre_general_001.mp3",
        "radio": "Radio 10"
      }
    },
    {
      "docPid": "MEX_otro_f_libre_tiempo_005",
      "start": 456,
      "end": 457,
      "left": {
        "word": ["en", "mi"],
        "lemma": ["en", "mi"],
        "pos": ["SP", "DP"]
      },
      "match": {
        "word": ["casa"],
        "lemma": ["casa"],
        "pos": ["NC"],
        "tokid": ["MEX_otro_f_libre_tiempo_005_00456"],
        "start_ms": [125800],
        "end_ms": [126300]
      },
      "right": {
        "word": ["está", "muy"],
        "lemma": ["estar", "mucho"],
        "pos": ["VA", "RG"]
      },
      "metadata": {
        "country": "MEX",
        "speaker_type": "otro",
        "sex": "f",
        "mode": "libre",
        "discourse": "tiempo",
        "filename": "MEX_otro_f_libre_tiempo_005.mp3",
        "radio": "FM 100"
      }
    }
  ]
}
```

### DataTables-Response (gekürzt)

**Advanced Search transformiert zu:**

```json
{
  "draw": 1,
  "recordsTotal": 342,
  "recordsFiltered": 342,
  "data": [
    [
      "en la",                                    // 0: left (letzte 10 Wörter)
      "casa",                                     // 1: match
      "de mis padres",                            // 2: right (erste 10 Wörter)
      "ARG",                                      // 3: country
      "pro",                                      // 4: speaker_type
      "m",                                        // 5: sex
      "pre",                                      // 6: mode
      "general",                                  // 7: discourse
      "ARG_pro_m_pre_general_001.mp3",            // 8: filename
      "Radio 10",                                 // 9: radio
      "ARG_pro_m_pre_general_001_00123",          // 10: tokid
      "42500",                                    // 11: start_ms
      "43200"                                     // 12: end_ms
    ],
    [
      "en mi",
      "casa",
      "está muy",
      "MEX",
      "otro",
      "f",
      "libre",
      "tiempo",
      "MEX_otro_f_libre_tiempo_005.mp3",
      "FM 100",
      "MEX_otro_f_libre_tiempo_005_00456",
      "125800",
      "126300"
    ]
  ]
}
```

**Mapping BlackLab → DataTables:**

| BlackLab-Feld | Position im Array | Beschreibung |
|---------------|-------------------|--------------|
| `left.word` (letzte 10) | 0 | Kontext links |
| `match.word` (join) | 1 | Treffer |
| `right.word` (erste 10) | 2 | Kontext rechts |
| `metadata.country` | 3 | Land |
| `metadata.speaker_type` | 4 | Sprecher-Typ |
| `metadata.sex` | 5 | Geschlecht |
| `metadata.mode` | 6 | Modus |
| `metadata.discourse` | 7 | Diskurs |
| `metadata.filename` | 8 | Dateiname |
| `metadata.radio` | 9 | Radiosender |
| `match.tokid[0]` | 10 | Token-ID |
| `match.start_ms[0]` | 11 | Start (Millisekunden) |
| `match.end_ms[0]` | 12 | Ende (Millisekunden) |

---

## 3.5 POS/Advanced-spezifische Inhalte

### CQL-Builder

**Datei:** `src/app/search/cql.py`  
**Funktion:** `build_cql(args)`  
**Zeilen:** ca. L1-150

**Beschreibung:**
- Baut CQL-Pattern aus Request-Parametern
- Modi: `forma_exacta`, `forma`, `lemma`, `cql` (Expert)
- POS-Auswahl: via `pos` Parameter (Komma-separiert)
- Case-Insensitivity: via `case_sensitive=0` Parameter

### Beispiel-CQL-Generierung

**Request:**
```
GET /search/advanced/data?
  q=casa
  &mode=forma
  &pos=NC,NP
  &case_sensitive=0
```

**Generierter CQL:**
```cql
[word="(?i)casa" & pos="NC|NP"]
```

**Bedeutung:**
- `(?i)` = Case-insensitive
- `word="casa"` = Wortform
- `pos="NC|NP"` = POS-Filter (Noun Common oder Proper)

### POS in Spalten?

**Aktuell:** POS/lemma/Features werden **nur zur Filterung** benutzt, **nicht in DataTables-Spalten angezeigt**.

**Potenzial:** BlackLab liefert bereits:
- `match.lemma[]` – Lemma des Treffers
- `match.pos[]` – POS-Tags
- Weitere Annotationen (sofern im Index konfiguriert)

Diese könnten in Zukunft als zusätzliche Spalten angezeigt werden.

---

## Zusammenfassung Advanced Search

**Datenfluss:**
1. User → CQL-Formular → Submit
2. `/search/advanced/data` empfängt Parameter
3. `build_cql()` → CQL-Pattern-String
4. `_make_bls_request()` → BlackLab HTTP-Call
5. BlackLab → JSON mit `hits[]` + `summary`
6. Hits verarbeiten → **Arrays** (13 Elemente pro Hit)
7. DataTables → Rendert Zeilen mit Index-basiertem Zugriff

**Wichtig:**
- Advanced nutzt **Arrays** (`data: [[...], [...]]`)
- Simple nutzt **Objekte** (`data: [{...}, {...}]`)
- BlackLab-Felder müssen manuell extrahiert werden (z.B. `hit.get("match", {}).get("tokid", [None])[0]`)
