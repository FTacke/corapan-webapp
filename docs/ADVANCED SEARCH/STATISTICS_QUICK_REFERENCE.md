# Statistik-API: Quick Reference

## Endpoint

```
GET /search/advanced/stats
```

## Request-Parameter

### Suchparameter
| Parameter | Typ | Beschreibung | Beispiel |
|-----------|-----|--------------|----------|
| `q` oder `query` | string | Suchbegriff | `casa` |
| `mode` | string | Suchmodus | `forma`, `lemma`, `cql` |
| `sensitive` | string | Groß-/Kleinschreibung | `0`, `1` |

### Filter-Parameter (Multi-Select)
| Parameter | Typ | Beschreibung | Beispiel |
|-----------|-----|--------------|----------|
| `country_code[]` | array | Länder-Codes | `ARG`, `ESP-SEV` |
| `speaker_type[]` | array | Sprecher-Typ | `pro`, `otro` |
| `sex[]` | array | Geschlecht | `m`, `f` |
| `speech_mode[]` | array | Sprechmodus | `libre`, `lectura` |
| `discourse[]` | array | Diskurstyp | `general`, `tiempo` |

### Zusatz-Parameter
| Parameter | Typ | Beschreibung | Beispiel |
|-----------|-----|--------------|----------|
| `include_regional` | string | Regionale Broadcasts | `0`, `1` |
| `country_detail` | string | Drill-Down nach Land | `ARG` |

## Response-Format

```json
{
  "total_hits": 1024,
  "by_country": [
    {"key": "ARG", "n": 512, "p": 0.5},
    {"key": "ESP", "n": 256, "p": 0.25}
  ],
  "by_country_region": [...],
  "by_speaker_type": [...],
  "by_sexo": [...],
  "by_modo": [...],
  "by_discourse": [...],
  "by_radio": [...],
  "by_city": [...],
  "by_file_id": [...]
}
```

### Feld-Struktur
| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `key` | string | Kategorie-Wert |
| `n` | integer | Absolute Anzahl |
| `p` | float | Proportion (0.0-1.0) |

## Error-Responses

| Status | Error-Type | Beschreibung |
|--------|-----------|--------------|
| 400 | `invalid_query` | Ungültiges CQL oder Filter |
| 502 | `connection_error` | BlackLab nicht erreichbar |
| 502 | `bls_error` | BlackLab HTTP-Fehler |
| 504 | `timeout` | Request-Timeout |
| 500 | `server_error` | Unerwarteter Fehler |

```json
{
  "error": "connection_error",
  "message": "BlackLab Server is not reachable"
}
```

## Beispiel-Requests

### PowerShell

```powershell
# Basis-Suche
Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma" | 
  Select-Object -ExpandProperty Content | ConvertFrom-Json

# Mit Filtern
$uri = "http://localhost:8000/search/advanced/stats?q=casa&mode=forma&country_code[]=ARG&sex[]=m"
Invoke-WebRequest -Uri $uri | Select-Object -ExpandProperty Content | ConvertFrom-Json

# Country-Drill-Down
Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma&country_detail=ARG" | 
  Select-Object -ExpandProperty Content | ConvertFrom-Json
```

### JavaScript (Frontend)

```javascript
// Fetch stats
const params = new URLSearchParams({
  q: 'casa',
  mode: 'forma',
  'country_code[]': 'ARG'
});

const response = await fetch(`/search/advanced/stats?${params}`, {
  method: 'GET',
  headers: {'Accept': 'application/json'},
  credentials: 'same-origin'
});

const data = await response.json();
console.log('Total hits:', data.total_hits);
console.log('Countries:', data.by_country);
```

### cURL

```bash
# Basis-Suche
curl "http://localhost:8000/search/advanced/stats?q=casa&mode=forma"

# Mit Filtern
curl "http://localhost:8000/search/advanced/stats?q=casa&mode=forma&country_code[]=ARG&sex[]=m"
```

## Limits & Performance

| Limit | Wert | Beschreibung |
|-------|------|--------------|
| Max Hits | 50.000 | Maximale Anzahl aggregierter Treffer |
| Rate Limit | 30/min | Maximale Requests pro Minute |
| Timeout | 30s | HTTP-Request-Timeout |

## Aggregierte Felder

Alle Felder stammen aus **Token-Annotationen** (BlackLab Index):

| Response-Feld | Token-Annotation | Beschreibung |
|---------------|------------------|--------------|
| `by_country` | `country_code` | Länder-Code |
| `by_country_region` | `country_region_code` | Regional-Code |
| `by_speaker_type` | `speaker_type` | Sprecher-Typ |
| `by_sexo` | `speaker_sex` | Geschlecht |
| `by_modo` | `speaker_mode` | Sprechmodus |
| `by_discourse` | `speaker_discourse` | Diskurstyp |
| `by_radio` | `radio` | Radio-Station |
| `by_city` | `city` | Stadt |
| `by_file_id` | `file_id` | Datei-ID |

## Konsistenz-Garantie

Die Statistik verwendet **exakt dieselbe Suchlogik** wie der DataTables-Endpoint:

```python
# Shared CQL-Builder
cql_pattern, filter_query, filters = build_advanced_cql_and_filters_from_request(request.args)
```

**Garantiert:**
- ✅ Identische CQL-Patterns
- ✅ Identische Filter
- ✅ Identische Treffer-Menge (bis auf Pagination)

## Troubleshooting

### Problem: 0 Treffer

**Check:**
```python
logger.info(f"STATS CQL: patt={cql_pattern}, filter={filter_query}")
```

**Lösungen:**
- Prüfe BlackLab-Status: `http://localhost:8081/blacklab-server`
- Teste identische Suche in DataTables
- Prüfe Filter-Parameter

### Problem: Inkonsistenz mit DataTables

**Check:**
```powershell
# Vergleiche Total Hits
$data = Invoke-WebRequest -Uri ".../data?..." | ConvertFrom-Json
$stats = Invoke-WebRequest -Uri ".../stats?..." | ConvertFrom-Json
$data.recordsTotal -eq $stats.total_hits
```

**Lösungen:**
- Verwende identische Query-Parameter
- Entferne `country_detail` (nur für Drill-Down)
- Prüfe `include_regional` Parameter

### Problem: Frontend lädt nicht

**Check:**
- Browser Console (F12) → Network Tab
- JavaScript-Fehler?
- HTTP 502/504 Errors?

**Lösungen:**
- Prüfe `/health/bls` Endpoint
- Starte BlackLab neu: `.\scripts\start_blacklab_docker_v3.ps1`
- Prüfe Flask-Logs

## Code-Referenz

### Implementierung
```python
# Datei: src/app/search/advanced_api.py
@bp.route("/stats", methods=["GET"])
@limiter.limit("30 per minute")
def advanced_stats():
    """Comprehensive BlackLab-native statistics aggregation endpoint."""
    # ...
```

### Frontend-Integration
```javascript
// Datei: static/js/modules/stats/initStatsTabAdvanced.js
export async function loadStats() {
    const url = buildStatsUrl();  // Liest #advanced-search-form
    const response = await fetch(url);
    const data = await response.json();
    renderCharts(data);
}
```

## Siehe auch

- **Vollständige Dokumentation:** `docs/ADVANCED SEARCH/STATISTICS_IMPLEMENTATION.md`
- **Test-Plan:** `docs/ADVANCED SEARCH/STATISTICS_SUMMARY.md`
- **Architektur:** `docs/concepts/advanced-search-architecture.md`
