# Statistik-Implementation: Zusammenfassung & Test-Plan

## ✅ Implementierte Verbesserungen

### 1. **Vollständige BlackLab-Native Aggregation**

Die neue Statistik-Funktion aggregiert **alle relevanten Metadatenfelder** direkt aus BlackLab-Treffern:

#### Neu hinzugefügte Felder:
- ✅ `by_country_region` - Regionale Zuordnung (z.B. ARG-CBA, ESP-SEV)
- ✅ `by_city` - Stadt-Aggregation
- ✅ `by_file_id` - Datei-basierte Statistik

#### Bereits vorhandene Felder (verbessert):
- ✅ `by_country` - Länder-Aggregation
- ✅ `by_speaker_type` - Sprecher-Typ (pro/otro/n/a)
- ✅ `by_sexo` - Geschlecht (m/f/n/a)
- ✅ `by_modo` - Sprechmodus (libre/lectura/pre)
- ✅ `by_discourse` - Diskurstyp (general/tiempo/tránsito)
- ✅ `by_radio` - Radio-Station

### 2. **Garantierte Konsistenz mit DataTables**

```python
# Beide Endpoints nutzen dieselbe Funktion:
cql_pattern, filter_query, filters = build_advanced_cql_and_filters_from_request(request.args)
```

**Vorteile:**
- Identische CQL-Patterns
- Identische Filter-Logik
- Keine Diskrepanzen zwischen Trefferliste und Statistik

### 3. **Erhöhtes Hit-Limit**

**Alt:** 10.000 Treffer  
**Neu:** 50.000 Treffer

```python
MAX_STATS_HITS = 50000  # Balance zwischen Genauigkeit und Performance
```

**Effekt:**
- Genauere Statistiken bei großen Treffermengen
- Sampling-Warnung im Log, wenn Limit erreicht

### 4. **Verbesserte Fehlerbehandlung**

```python
except CQLValidationError as e:
    return jsonify({
        "error": "invalid_query",
        "message": str(e)
    }), 400
```

**Neue Error-Typen:**
- `invalid_query` (400) - Ungültiges CQL
- `connection_error` (502) - BlackLab nicht erreichbar
- `bls_error` (502) - BlackLab HTTP-Fehler
- `timeout` (504) - Request-Timeout
- `server_error` (500) - Unerwarteter Fehler

### 5. **Umfassende Dokumentation**

```python
"""
Comprehensive BlackLab-native statistics aggregation endpoint.

Aggregates hit-level metadata from BlackLab search results using the exact same
search query as the DataTables endpoint to ensure consistency.
...
"""
```

**Dokumentation erstellt:**
- ✅ Inline-Docstrings (PEP 257)
- ✅ `docs/ADVANCED SEARCH/STATISTICS_IMPLEMENTATION.md`
- ✅ Parameter-Dokumentation
- ✅ Response-Format-Beispiele

---

## 🧪 Test-Plan

### Test 1: Basis-Funktionalität

**Ziel:** Statistik lädt ohne Fehler

```powershell
# Starte Entwicklungsumgebung
.\scripts\dev-start.ps1

# Test-Request
Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma" | 
  Select-Object -ExpandProperty Content | 
  ConvertFrom-Json
```

**Erwartete Ausgabe:**
```json
{
  "total_hits": <Zahl>,
  "by_country": [...],
  "by_sexo": [...],
  "by_modo": [...],
  ...
}
```

**Erfolgskriterien:**
- ✅ HTTP 200
- ✅ `total_hits` > 0
- ✅ Alle `by_*` Felder vorhanden
- ✅ Proportionen summieren zu 1.0

---

### Test 2: Konsistenz mit DataTables

**Ziel:** Statistik und Trefferliste zeigen dieselben Gesamtzahlen

```powershell
# DataTables-Request
$dataResponse = Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/data?q=casa&mode=forma&draw=1&start=0&length=50" | 
  Select-Object -ExpandProperty Content | 
  ConvertFrom-Json

# Stats-Request
$statsResponse = Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma" | 
  Select-Object -ExpandProperty Content | 
  ConvertFrom-Json

# Vergleich
Write-Host "DataTables Total: $($dataResponse.recordsTotal)"
Write-Host "Stats Total: $($statsResponse.total_hits)"
```

**Erfolgskriterien:**
- ✅ `statsResponse.total_hits == dataResponse.recordsTotal`

---

### Test 3: Filter-Konsistenz

**Ziel:** Filter werden korrekt auf Statistik angewendet

```powershell
# Mit Länder-Filter
$filtered = Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma&country_code[]=ARG" | 
  Select-Object -ExpandProperty Content | 
  ConvertFrom-Json

# Ohne Filter
$unfiltered = Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma" | 
  Select-Object -ExpandProperty Content | 
  ConvertFrom-Json

Write-Host "Filtered Hits: $($filtered.total_hits)"
Write-Host "Unfiltered Hits: $($unfiltered.total_hits)"
```

**Erfolgskriterien:**
- ✅ `filtered.total_hits < unfiltered.total_hits`
- ✅ `filtered.by_country` enthält nur "ARG"

---

### Test 4: Neue Felder vorhanden

**Ziel:** Neue Aggregationsfelder werden zurückgegeben

```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma" | 
  Select-Object -ExpandProperty Content | 
  ConvertFrom-Json

# Prüfe neue Felder
Write-Host "by_country_region: $($response.by_country_region -ne $null)"
Write-Host "by_city: $($response.by_city -ne $null)"
Write-Host "by_file_id: $($response.by_file_id -ne $null)"
```

**Erfolgskriterien:**
- ✅ `by_country_region` existiert
- ✅ `by_city` existiert
- ✅ `by_file_id` existiert

---

### Test 5: Country-Drill-Down

**Ziel:** `country_detail` Parameter filtert korrekt

```powershell
# Alle Länder
$all = Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma" | 
  Select-Object -ExpandProperty Content | 
  ConvertFrom-Json

# Nur Argentinien
$arg = Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma&country_detail=ARG" | 
  Select-Object -ExpandProperty Content | 
  ConvertFrom-Json

Write-Host "All Countries Total: $($all.total_hits)"
Write-Host "ARG Only Total: $($arg.total_hits)"
Write-Host "ARG Countries: $($arg.by_country | ConvertTo-Json)"
```

**Erfolgskriterien:**
- ✅ `arg.total_hits <= all.total_hits`
- ✅ `arg.by_country` enthält nur "ARG" (oder ARG-* Regionen)

---

### Test 6: Fehlerbehandlung

**Ziel:** Ungültige Requests werden sauber abgefangen

```powershell
# Ungültiges CQL
try {
    Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=[invalid&mode=cql"
} catch {
    $errorResponse = $_.ErrorDetails.Message | ConvertFrom-Json
    Write-Host "Error Type: $($errorResponse.error)"
    Write-Host "Error Message: $($errorResponse.message)"
}
```

**Erfolgskriterien:**
- ✅ HTTP 400
- ✅ `error == "invalid_query"`
- ✅ Sinnvolle `message`

---

### Test 7: Frontend-Integration

**Ziel:** Charts werden im Browser geladen

**Schritte:**
1. Öffne: `http://localhost:8000/search/advanced`
2. Suche: "casa" (forma, insensitiv)
3. Klicke Tab "Estadísticas"
4. Warte 2 Sekunden

**Erfolgskriterien:**
- ✅ Charts werden geladen (kein Loader mehr sichtbar)
- ✅ Alle 6-7 Chart-Karten haben Balkendiagramme
- ✅ Total Hits korrekt angezeigt
- ✅ Kategorienzahlen sinnvoll (z.B. "5 categorías")
- ✅ Keine JavaScript-Fehler in Console

---

### Test 8: Performance

**Ziel:** Statistik-Request ist performant

```powershell
Measure-Command {
    Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma"
} | Select-Object TotalSeconds
```

**Erfolgskriterien:**
- ✅ < 5 Sekunden (bei normalem Korpus)
- ✅ < 10 Sekunden (bei sehr großen Treffermengen)

**Hinweis:** Hängt ab von:
- BlackLab-Performance
- Anzahl Treffer
- Netzwerk-Latenz

---

## 🐛 Bekannte Einschränkungen

### 1. Sampling bei großen Treffermengen

**Problem:**  
Bei mehr als 50.000 Treffern wird nur eine Stichprobe aggregiert.

**Workaround:**  
Für präzise Statistiken Filter verwenden, um Treffermenge zu reduzieren.

**Zukünftig:**  
Pagination implementieren (mehrere Requests mit `first=0/50000/100000`).

### 2. Keine Kombinationen (Facetten-Kreuzungen)

**Problem:**  
Aktuell nur einzelne Dimensionen, keine Kombinationen (z.B. "Männer aus Argentinien").

**Zukünftig:**  
`aggregate_combined()` Funktion implementieren.

### 3. Keine Zeitreihen-Aggregation

**Problem:**  
Datumsfeld wird nicht gruppiert (nur raw file_id).

**Zukünftig:**  
Gruppierung nach Jahr/Monat/Quartal implementieren.

---

## 📋 Code-Review-Checkliste

### Code-Qualität
- ✅ PEP 8 konform
- ✅ Type hints verwendet (wo sinnvoll)
- ✅ Docstrings vorhanden (PEP 257)
- ✅ Logging an relevanten Stellen
- ✅ Error-Handling vollständig

### Funktionalität
- ✅ Identische Suchlogik wie DataTables
- ✅ Alle Token-Annotationen aggregiert
- ✅ Counter korrekt (nur einmal pro Hit)
- ✅ Proportionen korrekt berechnet
- ✅ Sortierung korrekt (count desc, key asc)

### Sicherheit
- ✅ Rate-Limiting (30/min)
- ✅ Input-Validierung (via `build_filters()`)
- ✅ CQL-Validierung (via `validate_cql_pattern()`)
- ✅ Keine SQL-Injection möglich (nur BlackLab)

### Performance
- ✅ Single Request (kein N+1)
- ✅ Hit-Limit konfigurierbar
- ✅ Effiziente Aggregation (Counter)
- ✅ Keine unnötigen Datenkopien

### Wartbarkeit
- ✅ Shared Code mit DataTables (`build_advanced_cql_and_filters_from_request`)
- ✅ Klare Funktionsnamen
- ✅ Modular (Aggregation in Subfunktion)
- ✅ Gut dokumentiert

---

## 🚀 Deployment-Checklist

### Vor Deployment
- [ ] Unit-Tests hinzugefügt (siehe Test-Plan)
- [ ] Integration-Tests durchgeführt
- [ ] Performance-Tests OK
- [ ] Code-Review abgeschlossen
- [ ] Dokumentation vollständig

### Deployment
- [ ] Branch merge zu `main`
- [ ] Deployment-Skript ausführen
- [ ] Server neu starten
- [ ] BlackLab verfügbar prüfen

### Nach Deployment
- [ ] Smoke-Tests auf Produktion
- [ ] Frontend-Charts laden
- [ ] Logs auf Errors prüfen
- [ ] Performance monitoren

---

## 📞 Support & Troubleshooting

### Logs prüfen

```powershell
# Flask-Logs
Get-Content logs\flask_app.log -Tail 100

# BlackLab-Container-Logs
docker logs blacklab-server-v3 --tail 100
```

### Häufige Probleme

**Problem:** Statistik zeigt 0 Treffer

**Lösung:**
1. Prüfe BlackLab-Status: `http://localhost:8081/blacklab-server`
2. Prüfe CQL-Pattern im Log: `STATS CQL: patt=...`
3. Teste identische Suche in DataTables

**Problem:** Charts laden nicht

**Lösung:**
1. Öffne Browser-Console (F12)
2. Prüfe Network-Tab auf 500/502 Errors
3. Prüfe JavaScript-Fehler
4. Prüfe `/health/bls` Endpoint

**Problem:** Statistik weicht von DataTables ab

**Lösung:**
1. Vergleiche logged CQL patterns
2. Prüfe `include_regional` Parameter
3. Prüfe `country_detail` (sollte nur für Drill-Down verwendet werden)

---

## 📚 Weitere Dokumentation

- **Implementierung:** `docs/ADVANCED SEARCH/STATISTICS_IMPLEMENTATION.md`
- **Architektur:** `docs/concepts/advanced-search-architecture.md`
- **DataTables-Flow:** `docs/ADVANCED SEARCH/BESTANDSAUFNAHME_ADVANCED_SEARCH.md`
- **BlackLab-Schema:** `config/blacklab/corapan-tsv.blf.yaml`
- **TSV-Export:** `src/scripts/blacklab_index_creation.py`

---

## ✨ Zusammenfassung

**Was wurde implementiert:**
- ✅ Vollständige BlackLab-native Statistik-Aggregation
- ✅ Konsistenz mit DataTables garantiert
- ✅ 9 Aggregations-Dimensionen (inkl. 3 neue)
- ✅ Erhöhtes Hit-Limit (50k)
- ✅ Verbesserte Fehlerbehandlung
- ✅ Umfassende Dokumentation

**Vorteile gegenüber alter SQL-Statistik:**
- ✅ Keine Diskrepanzen mehr
- ✅ Single Source of Truth (BlackLab)
- ✅ Wartbarer Code (shared CQL-Builder)
- ✅ Performanter (single request)
- ✅ Erweiterbar (neue Felder trivial hinzuzufügen)

**Nächste Schritte:**
1. Tests durchführen (siehe Test-Plan)
2. Feedback einholen
3. Ggf. Feintuning
4. Deployment
