# BlackLab Statistics Implementation

## Überblick

Die Statistik-Funktion für die erweiterte Suche aggregiert Treffer-Metadaten direkt aus BlackLab-Suchergebnissen und nutzt dabei **exakt dieselbe Suchlogik** wie die DataTables-Trefferliste.

**Endpoint:** `GET /search/advanced/stats`

**Implementierung:** `src/app/search/advanced_api.py` - `advanced_stats()`

---

## Architektur

### Datenfluss

```
User → Frontend (initStatsTabAdvanced.js)
  ↓
GET /search/advanced/stats?q=casa&mode=forma&country_code[]=ARG
  ↓
Backend: build_advanced_cql_and_filters_from_request()
  ↓
BlackLab: /bls/corpora/corapan/hits
  - patt=[word="casa"]
  - number=50000
  - listvalues=country_code,speaker_sex,speaker_mode,...
  ↓
Backend: aggregate_dimension() für jedes Feld
  ↓
JSON Response: {total_hits, by_country, by_sexo, by_modo, ...}
  ↓
Frontend: Render Charts (Chart.js)
```

---

## Technische Details

### 1. Identische Suchlogik wie DataTables

Die Statistik verwendet **dieselbe Hilfsfunktion** wie der DataTables-Endpoint:

```python
cql_pattern, filter_query, filters = build_advanced_cql_and_filters_from_request(request.args)
```

**Garantiert:**
- Identische CQL-Patterns
- Identische Metadaten-Filter
- Identische Corpus-Auswahl
- Identische Treffer-Menge (bis auf Pagination)

### 2. BlackLab-Native Aggregation

**Keine SQL-Datenbank erforderlich!**

Die Statistik aggregiert ausschließlich aus BlackLab-Treffern:

```python
# BlackLab-Request
bls_params = {
    "number": 50000,  # Maximale Anzahl Treffer
    "listvalues": "country_code,speaker_sex,speaker_mode,speaker_discourse,radio,city,file_id",
    "waitfortotal": "true"
}
```

**Aggregierte Felder** (alle aus `hit.match`):
- `country_code` → `by_country`
- `country_region_code` → `by_country_region`
- `speaker_type` → `by_speaker_type`
- `speaker_sex` → `by_sexo`
- `speaker_mode` → `by_modo`
- `speaker_discourse` → `by_discourse`
- `radio` → `by_radio`
- `city` → `by_city`
- `file_id` → `by_file_id`

### 3. Token-Annotationen als Quelle

Alle aggregierten Felder sind **Token-Annotationen** (definiert in `config/blacklab/corapan-tsv.blf.yaml`):

```yaml
annotations:
  - name: speaker_sex
    valuePath: speaker_sex
  - name: speaker_mode
    valuePath: speaker_mode
  - name: country_code
    valuePath: country_code
  # etc.
```

**Datenfluss:**
1. JSON-Korpus (`media/transcripts/**/*.json`) enthält `segment.speaker.speaker_sex`
2. TSV-Export (`blacklab_index_creation.py`) schreibt `speaker_sex` in jede Token-Zeile
3. BlackLab indexiert als Token-Annotation
4. Statistik liest aus `hit.match.speaker_sex`

### 4. Aggregations-Algorithmus

```python
def aggregate_dimension(dimension_key: str) -> list:
    counts = Counter()
    
    for hit in hits:
        match = hit.get("match", {})
        value = match.get(dimension_key)
        
        # Handle list values (take FIRST non-empty)
        if isinstance(value, list):
            for v in value:
                if v and str(v).strip():
                    counts[str(v)] += 1
                    break  # Only count ONCE per hit!
        else:
            if value and str(value).strip():
                counts[str(value)] += 1
    
    total = sum(counts.values())
    
    return [
        {"key": key, "n": count, "p": round(count / total, 3)}
        for key, count in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    ]
```

**Wichtig:**
- Pro Treffer wird jedes Feld **nur einmal** gezählt
- Listenwerte: Nimm das **erste** nicht-leere Element
- Sortierung: Absteigend nach Anzahl, dann aufsteigend nach Schlüssel

---

## Query-Parameter

Die Statistik akzeptiert **alle Parameter** der erweiterten Suche:

### Suchparameter
- `q` oder `query`: Suchbegriff
- `mode`: `forma`, `forma_exacta`, `lemma`, `cql`
- `sensitive`: `0` (insensitiv) oder `1` (sensitiv)

### Filter-Parameter (Multi-Select)
- `country_code[]`: Land-Codes (z.B. `ARG`, `ESP-SEV`)
- `speaker_type[]`: Sprecher-Typ (`pro`, `otro`, `n/a`)
- `sex[]`: Geschlecht (`m`, `f`, `n/a`)
- `speech_mode[]` oder `mode[]`: Sprechmodus (`libre`, `lectura`, `pre`)
- `discourse[]`: Diskurstyp (`general`, `tiempo`, `tránsito`)

### Zusatzparameter
- `include_regional`: `1` = Regionale Broadcasts einschließen
- `country_detail`: Nachfilterung nach spezifischem Land (für Drill-Down)

---

## Response-Format

```json
{
  "total_hits": 1024,
  "by_country": [
    {"key": "ARG", "n": 512, "p": 0.5},
    {"key": "ESP", "n": 256, "p": 0.25},
    {"key": "MEX", "n": 256, "p": 0.25}
  ],
  "by_country_region": [
    {"key": "ARG-CBA", "n": 128, "p": 0.5},
    {"key": "ESP-SEV", "n": 64, "p": 0.25}
  ],
  "by_speaker_type": [
    {"key": "pro", "n": 768, "p": 0.75},
    {"key": "otro", "n": 256, "p": 0.25}
  ],
  "by_sexo": [
    {"key": "m", "n": 512, "p": 0.5},
    {"key": "f", "n": 512, "p": 0.5}
  ],
  "by_modo": [
    {"key": "libre", "n": 640, "p": 0.625},
    {"key": "lectura", "n": 384, "p": 0.375}
  ],
  "by_discourse": [
    {"key": "general", "n": 800, "p": 0.781},
    {"key": "tiempo", "n": 224, "p": 0.219}
  ],
  "by_radio": [
    {"key": "Radio Mitre", "n": 512, "p": 0.5},
    {"key": "Radio Nacional", "n": 512, "p": 0.5}
  ],
  "by_city": [
    {"key": "Buenos Aires", "n": 384, "p": 0.375},
    {"key": "Córdoba", "n": 320, "p": 0.3125}
  ],
  "by_file_id": [
    {"key": "2023-08-10_ARG_Mitre", "n": 256, "p": 0.25}
  ]
}
```

**Felder:**
- `key`: Kategorie-Wert (z.B. "ARG", "m", "libre")
- `n`: Absolute Anzahl Treffer
- `p`: Proportion (0.0 - 1.0)

---

## Performance & Limits

### Hit-Limit
- **Maximum:** 50.000 Treffer pro Statistik-Request
- **Grund:** Balance zwischen Genauigkeit und Performance
- **Sampling:** Wenn mehr Treffer existieren, wird eine Stichprobe aggregiert

```python
MAX_STATS_HITS = 50000
```

### Rate-Limiting
- **30 Requests/Minute** (wie DataTables-Endpoint)

### Timeout
- Verwendet Standard-HTTP-Client-Timeout (konfiguriert in `extensions/http_client.py`)

---

## Fehlerbehandlung

### HTTP-Status-Codes

| Code | Error Type | Beschreibung |
|------|-----------|--------------|
| 200 | OK | Erfolgreiche Aggregation |
| 400 | `invalid_query` | Ungültiges CQL oder Filter |
| 502 | `connection_error` | BlackLab nicht erreichbar |
| 502 | `bls_error` | BlackLab HTTP-Fehler |
| 504 | `timeout` | BlackLab-Request Timeout |
| 500 | `server_error` | Unerwarteter Fehler |

### Error-Response

```json
{
  "error": "connection_error",
  "message": "BlackLab Server is not reachable"
}
```

---

## Frontend-Integration

### Verwendung in `initStatsTabAdvanced.js`

```javascript
// Build URL from form
const url = buildStatsUrl();  // Reads #advanced-search-form

// Fetch stats
const response = await fetch(url, {
  method: 'GET',
  headers: {'Accept': 'application/json'},
  credentials: 'same-origin'
});

const data = await response.json();

// Render charts
renderBar(containerEl, data.by_country, 'País', 'absolute');
renderBar(containerEl, data.by_sexo, 'Sexo', 'absolute');
// etc.
```

### Chart-Rendering

Die Statistik-Daten werden mit **Chart.js** als horizontale Balkendiagramme dargestellt:

```javascript
import { renderBar } from './renderBar.js';

charts.country = renderBar(
  document.getElementById('chart-country'),
  data.by_country,
  'País',
  'absolute'  // oder 'percent'
);
```

---

## Vergleich: Alte SQL-Statistik vs. Neue BlackLab-Statistik

| Aspekt | Alte SQL-Statistik | Neue BlackLab-Statistik |
|--------|-------------------|------------------------|
| **Datenquelle** | PostgreSQL `tokens` Tabelle | BlackLab-Treffer (JSON) |
| **Konsistenz** | ❌ Inkonsistent mit DataTables | ✅ Identische Suchlogik |
| **Metadaten** | ❌ Manuelles Mapping | ✅ Direkt aus Token-Annotationen |
| **Pagination** | ❌ Limitiert auf erste Seite | ✅ Bis zu 50k Treffer |
| **Performance** | ❌ N+1 Queries, langsam | ✅ Single Request, schnell |
| **Wartung** | ❌ Separate Logik | ✅ Shared CQL-Builder |

---

## Testing

### Manueller Test (Browser)

1. Starte BlackLab und Flask:
   ```powershell
   .\scripts\dev-start.ps1
   ```

2. Öffne erweiterte Suche:
   ```
   http://localhost:8000/search/advanced
   ```

3. Suche nach "casa" (forma, insensitiv)

4. Wechsel zu Tab "Estadísticas"

5. Prüfe:
   - ✅ Charts werden geladen
   - ✅ Total Hits korrekt
   - ✅ Alle Dimensionen vorhanden
   - ✅ Proportionen summieren zu 100%

### API-Test (cURL)

```powershell
# Einfache Suche
Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma" | Select-Object -ExpandProperty Content | ConvertFrom-Json

# Mit Filtern
Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma&country_code[]=ARG&sex[]=m" | Select-Object -ExpandProperty Content | ConvertFrom-Json

# Country-Drill-Down
Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma&country_detail=ARG" | Select-Object -ExpandProperty Content | ConvertFrom-Json
```

### Unit-Tests (TODO)

```python
def test_stats_consistency_with_datatable():
    """Stats should aggregate same hits as DataTables."""
    # Same query parameters
    params = {"q": "casa", "mode": "forma"}
    
    # Fetch DataTables data
    data_response = client.get("/search/advanced/data", query_string=params)
    data_json = data_response.get_json()
    
    # Fetch stats
    stats_response = client.get("/search/advanced/stats", query_string=params)
    stats_json = stats_response.get_json()
    
    # Total hits should match
    assert stats_json["total_hits"] == data_json["recordsTotal"]
```

---

## Troubleshooting

### Problem: Statistik zeigt 0 Treffer

**Check:**
```python
logger.info(f"STATS CQL: patt={cql_pattern}, filter={filter_query}")
```

**Häufige Ursachen:**
- CQL-Pattern ungültig
- Filter zu restriktiv
- BlackLab-Index leer

**Lösung:**
- Prüfe BlackLab direkt: `http://localhost:8081/blacklab-server/corapan`
- Validiere CQL: `/search/advanced/validate` (falls implementiert)

### Problem: Statistik weicht von DataTables ab

**Check:**
```python
# Compare CQL patterns
data_cql = build_advanced_cql_and_filters_from_request(data_args)
stats_cql = build_advanced_cql_and_filters_from_request(stats_args)
assert data_cql == stats_cql
```

**Häufige Ursachen:**
- Parameter unterschiedlich übergeben
- `include_regional` nicht gesetzt
- `country_detail` nachträglich angewendet

**Lösung:**
- Nutze identische Query-String für beide Endpoints
- Vergleiche logged CQL patterns

### Problem: Fehlende Kategorien in Charts

**Check:**
```python
logger.info(f"Stats: by_sexo={by_sex}, by_modo={by_mode}")
```

**Häufige Ursachen:**
- Annotation nicht in `listvalues`
- Feld nicht indexiert
- Werte leer/None

**Lösung:**
- Prüfe `listvalues` Parameter
- Prüfe BlackLab-Schema (`corapan-tsv.blf.yaml`)
- Inspect first hit: `hit["match"].keys()`

---

## Erweiterungen (Zukünftig)

### 1. Aggregation nach Datum

```python
by_date = aggregate_dimension("date")
# Gruppierung nach Jahr/Monat möglich
```

### 2. Kombinierte Facetten

```python
def aggregate_combined(dim1: str, dim2: str):
    """Aggregate by two dimensions (e.g., country + sex)."""
    counts = Counter()
    for hit in hits:
        v1 = hit["match"].get(dim1)
        v2 = hit["match"].get(dim2)
        if v1 and v2:
            counts[(v1, v2)] += 1
    return counts
```

### 3. Export als CSV

```python
@bp.route("/stats/export", methods=["GET"])
def export_stats():
    """Export statistics as CSV."""
    # ... (ähnlich zu /export Endpoint)
```

---

## Siehe auch

- `docs/ADVANCED SEARCH/BESTANDSAUFNAHME_ADVANCED_SEARCH.md` - DataTables-Flow
- `docs/concepts/advanced-search-architecture.md` - Architektur-Übersicht
- `config/blacklab/corapan-tsv.blf.yaml` - BlackLab-Schema
- `src/scripts/blacklab_index_creation.py` - TSV-Export-Logik
