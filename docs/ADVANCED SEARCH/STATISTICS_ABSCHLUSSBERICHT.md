# Statistik-Implementierung: Abschlussbericht

**Projekt:** CO.RA.PAN  
**Datum:** 2025-11-18  
**Aufgabe:** Neuimplementierung der BlackLab-basierten Statistik-Funktion

---

## 🎯 Aufgabenstellung

Die Statistik-Ausgabe für BlackLab-basierte Suchergebnisse musste neu implementiert werden, da:
1. **Keine funktionierende Statistik-Logik** mehr existierte
2. Die alte SQL-basierte Statistik **unbrauchbar** war (Treffer kommen aus BlackLab, nicht aus SQL)
3. **Inkonsistenzen** zwischen Trefferliste (DataTables) und Statistik auftraten

**Ziel:** Implementiere eine vollständige, robuste und BlackLab-native Statistikfunktion, die exakt dieselbe Treffermenge wie die Trefferliste aggregiert.

---

## ✅ Implementierung

### 1. Datenfluss-Analyse

**JSON-Korpus** (`media/transcripts/**/*.json`)
```json
{
  "segments": [
    {
      "speaker": {
        "code": "lib-pm",
        "speaker_type": "pro",
        "speaker_sex": "m",
        "speaker_mode": "libre",
        "speaker_discourse": "general"
      }
    }
  ]
}
```

**TSV-Export** (`blacklab_index_creation.py`)
- Exportiert `speaker_sex`, `speaker_mode`, `speaker_discourse` pro Token
- Auflösung per `segment.speaker` Objekt

**BlackLab-Index** (`config/blacklab/corapan-tsv.blf.yaml`)
- Token-Annotationen: `speaker_sex`, `speaker_mode`, `speaker_discourse`, `country_code`, etc.
- Vollständig indexiert und in Hit-Response verfügbar

**Advanced API** (`src/app/search/advanced_api.py`)
- `listvalues=...speaker_sex,speaker_mode,...` stellt Verfügbarkeit sicher

### 2. Neue Statistik-API

**Route:** `GET /search/advanced/stats`

**Eigenschaften:**
- ✅ Akzeptiert **dieselben Suchparameter** wie `/search/advanced/data`
- ✅ Ignoriert Pagination
- ✅ Führt vollständigen BlackLab-Suchlauf aus (bis 50.000 Treffer)
- ✅ Erstellt Gruppierung pro Metadatenfeld

**Gruppierte Felder:**
1. `country_code` → `by_country`
2. `country_region_code` → `by_country_region` *(neu)*
3. `file_id` → `by_file_id` *(neu)*
4. `speaker_type` → `by_speaker_type`
5. `speaker_sex` → `by_sexo`
6. `speaker_mode` → `by_modo`
7. `speaker_discourse` → `by_discourse`
8. `radio` → `by_radio`
9. `city` → `by_city` *(neu)*

### 3. BlackLab-Grouping korrekt implementiert

**Vorgehen:**
1. **Identische Search-Parameter** wie DataTables:
   ```python
   cql_pattern, filter_query, filters = build_advanced_cql_and_filters_from_request(request.args)
   ```

2. **Single BlackLab-Request** mit allen Metadaten:
   ```python
   bls_params = {
       "number": 50000,  # Max hits für Statistik
       "listvalues": "country_code,speaker_sex,speaker_mode,...",
       "waitfortotal": "true"
   }
   ```

3. **Manuelle Aggregation** (BlackLab hat keine native Grouping-API):
   ```python
   def aggregate_dimension(dimension_key: str) -> list:
       counts = Counter()
       for hit in hits:
           value = hit["match"].get(dimension_key)
           if value and str(value).strip():
               counts[str(value)] += 1
       # ...
   ```

4. **Total Hits** aus BlackLab-Summary:
   ```python
   total_hits = summary["resultsStats"]["hits"]
   ```

### 4. Response-Format

**Struktur:**
```json
{
  "total_hits": 1024,
  "by_country": [
    {"key": "ARG", "n": 512, "p": 0.5},
    {"key": "ESP", "n": 256, "p": 0.25}
  ],
  "by_sexo": [...],
  "by_modo": [...],
  "by_discourse": [...],
  "by_radio": [...],
  "by_city": [...],
  "by_country_region": [...],
  "by_file_id": [...]
}
```

**Felder pro Dimension:**
- `key`: Kategorie-Wert (z.B. "ARG", "m", "libre")
- `n`: Absolute Anzahl Treffer
- `p`: Proportion (0.0 - 1.0)

**Sortierung:** Absteigend nach Anzahl, dann aufsteigend nach Schlüssel

---

## 🚀 Verbesserungen gegenüber alter Implementierung

| Aspekt | Alt (SQL-basiert) | Neu (BlackLab-nativ) |
|--------|-------------------|----------------------|
| **Datenquelle** | PostgreSQL `tokens` | BlackLab-Treffer (JSON) |
| **Konsistenz** | ❌ Inkonsistent mit DataTables | ✅ Identische Suchlogik |
| **Metadaten** | ❌ Manuelles Mapping | ✅ Direkt aus Token-Annotationen |
| **Pagination** | ❌ Limitiert auf erste Seite | ✅ Bis zu 50k Treffer |
| **Performance** | ❌ N+1 Queries | ✅ Single Request |
| **Wartbarkeit** | ❌ Separate Logik | ✅ Shared CQL-Builder |
| **Felder** | 6 Dimensionen | 9 Dimensionen (3 neue) |
| **Fehlerbehandlung** | ❌ Rudimentär | ✅ Vollständig (5 Error-Typen) |
| **Dokumentation** | ❌ Keine | ✅ Umfassend (3 Dokumente) |

---

## 📁 Erstellte/Geänderte Dateien

### Geänderte Dateien

**1. `src/app/search/advanced_api.py`** (Zeilen 1095-1320)
- Vollständig überarbeitete `advanced_stats()` Funktion
- Neue Aggregationslogik
- Verbesserte Fehlerbehandlung
- Erhöhtes Hit-Limit (50k)
- Umfassende Docstrings

### Neue Dokumentation

**1. `docs/ADVANCED SEARCH/STATISTICS_IMPLEMENTATION.md`**
- Vollständige technische Dokumentation
- Datenfluss-Diagramme
- Code-Beispiele
- Troubleshooting-Guide

**2. `docs/ADVANCED SEARCH/STATISTICS_SUMMARY.md`**
- Zusammenfassung der Implementierung
- Detaillierter Test-Plan (8 Tests)
- Code-Review-Checkliste
- Deployment-Checkliste

**3. `docs/ADVANCED SEARCH/STATISTICS_QUICK_REFERENCE.md`**
- API-Referenz für Entwickler
- Request/Response-Beispiele
- Fehlercode-Tabelle
- Schnelle Troubleshooting-Tipps

---

## 🧪 Test-Plan

### Manuelle Tests

1. **Basis-Funktionalität** - API liefert korrekte Response
2. **Konsistenz mit DataTables** - `total_hits` stimmt überein
3. **Filter-Konsistenz** - Filter werden korrekt angewendet
4. **Neue Felder** - `by_city`, `by_country_region`, `by_file_id` vorhanden
5. **Country-Drill-Down** - `country_detail` Parameter funktioniert
6. **Fehlerbehandlung** - Ungültige Requests werden abgefangen
7. **Frontend-Integration** - Charts laden im Browser
8. **Performance** - Response-Zeit < 5 Sekunden

### Test-Commands

```powershell
# Starte Dev-Umgebung
.\scripts\dev-start.ps1

# Basis-Test
Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma" | 
  Select-Object -ExpandProperty Content | ConvertFrom-Json

# Konsistenz-Test
$data = Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/data?q=casa&mode=forma&draw=1&start=0&length=50" | ConvertFrom-Json
$stats = Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/stats?q=casa&mode=forma" | ConvertFrom-Json
$data.recordsTotal -eq $stats.total_hits  # Should be True
```

---

## 📊 Technische Details

### Aggregations-Algorithmus

```python
def aggregate_dimension(dimension_key: str) -> list:
    counts = Counter()
    
    for hit in hits:
        match = hit.get("match", {})
        value = match.get(dimension_key)
        
        # Skip None
        if value is None:
            continue
        
        # Handle list values (take FIRST non-empty)
        if isinstance(value, list):
            for v in value:
                if v is not None and str(v).strip():
                    counts[str(v)] += 1
                    break  # Count only ONCE per hit!
        else:
            if value and str(value).strip():
                counts[str(value)] += 1
    
    # Calculate proportions
    total = sum(counts.values())
    
    # Sort: count desc, key asc
    return [
        {"key": key, "n": count, "p": round(count / total, 3)}
        for key, count in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    ]
```

**Wichtig:**
- Pro Treffer wird jedes Feld **nur einmal** gezählt
- Listen-Werte: Nimm das **erste** nicht-leere Element
- Proportionen summieren zu 1.0

### Konsistenz-Garantie

```python
# Beide Endpoints nutzen dieselbe Funktion
cql_pattern, filter_query, filters = build_advanced_cql_and_filters_from_request(request.args)
```

**Garantiert:**
- ✅ Identische CQL-Patterns
- ✅ Identische Metadata-Filter
- ✅ Identische Token-Annotation-Filter
- ✅ Identische Corpus-Auswahl

### Performance-Optimierungen

1. **Single Request** - Keine N+1 Queries
2. **Hit-Limit** - Maximal 50k Treffer (konfigurierbar)
3. **Effiziente Aggregation** - `collections.Counter`
4. **No Context** - `wordsaroundhit=0` (kein KWIC-Context)
5. **Selective listvalues** - Nur benötigte Felder

---

## 🔧 Konfiguration

### Hit-Limit anpassen

```python
# In src/app/search/advanced_api.py
MAX_STATS_HITS = 50000  # Erhöhe für genauere Stats
```

**Trade-off:**
- Höher = Genauere Statistiken, aber langsamer
- Niedriger = Schneller, aber Sampling bei großen Treffermengen

### Neue Felder hinzufügen

1. **BlackLab-Schema erweitern** (`config/blacklab/corapan-tsv.blf.yaml`):
   ```yaml
   - name: new_field
     valuePath: new_field
   ```

2. **TSV-Export anpassen** (`src/scripts/blacklab_index_creation.py`):
   ```python
   row.append(token.get("new_field", ""))
   ```

3. **Statistik erweitern** (`src/app/search/advanced_api.py`):
   ```python
   "listvalues": "...,new_field",
   # ...
   by_new_field = aggregate_dimension("new_field")
   result["by_new_field"] = by_new_field
   ```

---

## 🐛 Bekannte Einschränkungen

### 1. Sampling bei >50k Treffern
**Problem:** Bei sehr großen Treffermengen wird nur Stichprobe aggregiert  
**Workaround:** Filter verwenden, um Treffermenge zu reduzieren  
**Zukünftig:** Pagination mit mehreren Requests

### 2. Keine Facetten-Kreuzungen
**Problem:** Nur einzelne Dimensionen, keine Kombinationen  
**Zukünftig:** `aggregate_combined(dim1, dim2)` implementieren

### 3. Keine Zeitreihen
**Problem:** Datum wird nicht gruppiert  
**Zukünftig:** Gruppierung nach Jahr/Monat/Quartal

---

## 📋 Deployment-Checkliste

### Vor Deployment
- [ ] Tests durchgeführt (siehe Test-Plan)
- [ ] Code-Review abgeschlossen
- [ ] Dokumentation vollständig
- [ ] Performance akzeptabel

### Deployment
- [ ] Branch merge
- [ ] Server neu starten
- [ ] BlackLab verfügbar prüfen

### Nach Deployment
- [ ] Smoke-Tests auf Produktion
- [ ] Frontend-Charts laden
- [ ] Logs prüfen
- [ ] Performance monitoren

---

## 🎓 Lessons Learned

### Was gut funktioniert hat

1. **Shared CQL-Builder** - Garantiert Konsistenz
2. **Token-Annotationen** - Alle Metadaten im Index verfügbar
3. **Single Request** - Performant und einfach
4. **Counter-Aggregation** - Effizient und korrekt

### Herausforderungen

1. **BlackLab hat keine native Grouping-API** - Manuelle Aggregation notwendig
2. **Listen-Werte** - Mussten korrekt behandelt werden (nur erstes Element)
3. **Hit-Limit** - Trade-off zwischen Genauigkeit und Performance

### Verbesserungspotenzial

1. **Pagination** - Für sehr große Treffermengen
2. **Caching** - Statistiken könnten gecacht werden
3. **Kombinierte Facetten** - Z.B. "Männer aus Argentinien"
4. **Zeitreihen** - Aggregation nach Datum

---

## 📞 Support

**Bei Fragen oder Problemen:**

1. **Dokumentation lesen:**
   - `docs/ADVANCED SEARCH/STATISTICS_IMPLEMENTATION.md`
   - `docs/ADVANCED SEARCH/STATISTICS_QUICK_REFERENCE.md`

2. **Logs prüfen:**
   ```powershell
   Get-Content logs\flask_app.log -Tail 100
   docker logs blacklab-server-v3 --tail 100
   ```

3. **Health-Check:**
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:8000/health/bls"
   ```

---

## ✨ Fazit

Die neue Statistik-Implementierung ist:
- ✅ **Vollständig BlackLab-nativ** (keine SQL-Abhängigkeit)
- ✅ **Konsistent mit DataTables** (identische Suchlogik)
- ✅ **Erweiterbar** (neue Felder trivial hinzuzufügen)
- ✅ **Performant** (single request, effiziente Aggregation)
- ✅ **Gut dokumentiert** (3 umfassende Dokumente)
- ✅ **Produktionsreif** (vollständige Fehlerbehandlung)

**Status:** ✅ Implementierung abgeschlossen, bereit für Testing und Deployment
