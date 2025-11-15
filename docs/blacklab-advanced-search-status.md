# Statusbericht: BlackLab + Advanced Search Integration (14.11.2025)

## UPDATE: CQL Builder Hardening (15.11.2025 - 11:40 Uhr)

**Status**: ✅ **Flask läuft stabil, kein Crash**

### Durchgeführte Hardening-Maßnahmen

CQL-Building-Funktionen wurden defensiv abgesichert gegen `None`/leere Werte:

1. **`build_token_cql()`**: Prüft, ob `token` leer ist → `ValueError`
2. **`build_speaker_code_constraint()`**: Behandelt `filters=None` → leerer String
3. **`build_cql_with_speaker_filter()`**: Prüft `params` und `filters` auf `None`
4. **`build_metadata_cql_constraints()`**: Filtert leere Strings aus Listen, prüft auf `None`
5. **`build_cql()`**: Prüft `params` auf `None` → `ValueError`

### Generierte CQL-Beispiele

**Beispiel 1**: Lemma-Suche mit Country-Filter
```cql
[lemma="casa" & country_code="ven"]
```
- Request: `?q=casa&mode=lemma&country_code=VEN`
- Hits: 29

**Beispiel 2**: Lemma-Suche mit mehreren Countries
```cql
[lemma="ir" & country_code="(arg|chl)"]
```
- Request: `?q=ir&mode=lemma&country_code=ARG&country_code=CHL`
- Hits: 1216

**Beispiel 3**: Lemma-Suche mit Speaker-Filter
```cql
[lemma="casa" & speaker_code="(lib-pf|lec-pf|com-pf|otro-pf)"]
```
- Request: `?q=casa&mode=lemma&sex=f`
- Hits: 284

### Test-Ergebnisse nach Hardening

```
✓ PASS   Health Check
✓ PASS   Simple Search        (761 hits)
✓ PASS   Country Filter       (29 hits - VEN)
✓ PASS   Speaker Filters      (284 hits - sex=f)
✓ PASS   POS Mode             (150866 hits - q=VERB)

Overall: ALL TESTS PASSED
```

**Fazit**: 
- Flask crasht nicht mehr
- Metadatenfilter (country/radio/city/date) laufen über CQL-Annotations-Constraints
- Keine Python-seitige Filterung mehr (BlackLab = Single Source of Truth)
- CQL-Builder ist robust gegen fehlerhafte Inputs

---

## STATUS (15.11.2025 - 09:45 Uhr)

**Filter-Architektur**: ✅ Vollständig repariert. BlackLab ist Single Source of Truth.

**Was funktioniert:**
1. ✅ **Lemma/Forma-Suche**: 761 Treffer für "casa"
2. ✅ **POS-Mode**: 150.866 Treffer für "VERB"
3. ✅ **Speaker-Filter (CQL)**: 284 Treffer für "casa" + sex=f
4. ✅ **Pagination**: recordsTotal/recordsFiltered kommen von BlackLab
5. ✅ **Speaker-Attribute**: werden korrekt aus speaker_code abgeleitet

**Was noch NICHT funktioniert:**
- ❌ **Doc-Metadaten-Filter** (country, radio, city, date): Metadaten sind NICHT im Index
  - **Ursache**: BlackLab 5.x externe Metadaten-Import nicht funktionstüchtig
  - **Lösung**: Siehe `docs/DOCMETA_INTEGRATION_REPORT.md`
  - **Empfehlung**: Metadaten in TSV integrieren (Option A)

---

## Metadaten-Integration: Versuch gescheitert (15.11.2025)

**Versuchte Ansätze** (alle nicht erfolgreich):
1. `blacklab-server.yaml` mit `corpora.corapan.metadata` → HTTP 500 Error
2. `linkedDocuments` in BLF-Datei → `InvalidInputFormatConfig`
3. `valuePath` in Metadatenfeldern → Index baut, Server crashed

**Diagnose**: BlackLab 5.x unterstützt externe JSON-Metadaten-Import entweder nicht, oder die Syntax ist undokumentiert/anders als erwartet.

**Details**: Siehe ausführlichen Bericht in `docs/DOCMETA_INTEGRATION_REPORT.md`

**Empfohlene Lösung**: 
- **Option A (bevorzugt)**: Metadaten in TSV integrieren
  - `blacklab_index_creation.py` erweitern
  - Doc-Metadaten als zusätzliche TSV-Spalten exportieren
  - Garantiert funktionstüchtig

---

## BlackLab-Index: Verfügbare Felder

**Annotierte Felder (Token-Ebene):**
- `word` (sensitiv), `norm` (insensitiv), `lemma` (sensitiv), `pos` (insensitiv)
- Morphologie: `past_type`, `future_type`, `tense`, `mood`, `person`, `number`, `aspect`
- Timing: `tokid`, `start_ms`, `end_ms`
- Kontext: `sentence_id`, `utterance_id`, `speaker_code`
- `punct` (intern)

**Metadatenfelder (Document-Ebene):**
Status: Schema existiert, aber **Felder sind leer** (docmeta.jsonl nicht importiert)
- `audio_path`, `city`, `country_code`, `date`, `file_id`, `radio` (alle tokenized)
- `fromInputFile` (untokenized)

**Speaker-Attribute:**
- `speaker_type`, `sex`, `mode`, `discourse` sind NICHT als Metadatenfelder indexiert
- Sie werden aus `speaker_code` (Token-Annotation) abgeleitet via `speaker_utils.py`
- Filter über CQL: `[lemma="casa" & speaker_code="(lib-pf|lec-pf|...)"]`

---

## Architektur-Überblick

### Filter-Architektur (korrekt implementiert)

**1. Doc-Metadaten → BlackLab `filter` Parameter**
- `country_code`, `radio`, `city`, `date`
- Syntax: `country_code:VEN AND radio:RCR`
- Via `filters_to_blacklab_query()` in `cql.py`
- **Status**: Funktioniert, aber Index hat keine Metadaten

**2. Speaker-Attribute → CQL Token-Constraint**
- `speaker_type`, `sex`, `mode`, `discourse`
- Mapping über `speaker_utils.get_speaker_codes_for_filters()`
- Integration in CQL: `[lemma="casa" & speaker_code="(lib-pf|lec-pf)"]`
- Via `build_cql_with_speaker_filter()` in `cql.py`
- **Status**: ✅ Funktioniert

**3. Keine Python-Seitenfilterung**
- `recordsTotal` = `recordsFiltered` = BlackLab's `numberOfHits`
- Pagination funktioniert korrekt (DataTables server-side)
- **Status**: ✅ Korrigiert (war vorher kaputt)

---

## Test-Ergebnisse (14.11.2025)

```
✓ PASS   Health Check
✓ PASS   Simple Search        (761 hits)
✗ FAIL   Country Filter       (0 hits - Metadaten fehlen im Index)
✓ PASS   Speaker Filters      (284 hits - sex=f)
✓ PASS   POS Mode             (150866 hits - q=VERB)
```

**Beispiel-Response** (`/search/advanced/data?q=casa&mode=lemma&sex=f&length=3`):
```json
{
  "draw": 1,
  "recordsTotal": 284,
  "recordsFiltered": 284,
  "data": [
    {
      "left": "municipio. Es importante revisar su vehículo antes de salir de",
      "match": "casa.",
      "right": "Un hecho de tránsito se registró en la bajada de",
      "country": "",
      "speaker_type": "pro",
      "sex": "f",
      "mode": "n/a",
      "discourse": "tránsito",
      "filename": "",
      "radio": "",
      "tokid": "gtm222abba73",
      "start_ms": 1629770,
      "end_ms": 1630370,
      "date": "",
      "city": ""
    }
  ]
}
```

**Beobachtung**: Speaker-Attribute (`sex=f`, `mode`, `discourse`) sind korrekt, Doc-Metadaten (`country`, `radio`, `city`, `date`) sind leer.

---

## Nächste Schritte

### 1. Index mit Metadaten neu bauen

**Option A: Metadaten in TSV integrieren**
- TSV-Spalten erweitern: `country_code`, `radio`, `city`, `date` (pro Zeile wiederholt)
- `blacklab_index_creation.py` anpassen
- BLF: `valuePath` für Metadaten auf TSV-Spalten umstellen

**Option B: docmeta.jsonl korrekt importieren**
- `blacklab-server.yaml` erweitern:
  ```yaml
  corpora:
    corapan:
      metadata:
        documentFormat: jsonlines
        path: /data/export/docmeta.jsonl
  ```
- Index neu bauen mit korrekter Metadaten-Quelle

**Empfehlung**: Option A (Metadaten in TSV), da alle Daten dann in einem Format sind.

### 2. Tests nach Index-Rebuild validieren

Nach Index-Neubau mit Metadaten:
- `python test_advanced_api_quick.py` sollte alle 5 Tests bestehen
- Country-Filter sollte Treffer liefern

---

## Geänderte Dateien (Reparatur 14.11.2025)

1. **`src/app/search/advanced_api.py`**:
   - Entfernt: `_matches_metadata_filters()`, `_get_token_metadata()`
   - Entfernt: Python-Seitenfilterung aus Hit-Verarbeitung
   - `recordsFiltered` = `recordsTotal` (BlackLab = Single Source of Truth)

2. **`src/app/search/cql.py`**:
   - `filters_to_blacklab_query()`: Doc-Metadaten als BlackLab-Filter (statt Python)
   - `build_speaker_code_constraint()`: Speaker-Filter in CQL integrieren
   - `build_cql_with_speaker_filter()`: CQL + Speaker-Constraint kombinieren
   - Entfernt: `get_metadata_filters()` (nicht mehr benötigt)
   - Fix: `mode=pos` wird nicht mehr als Speech-Mode behandelt

3. **`src/app/search/cql_validator.py`**:
   - Pipe `|` erlaubt (für Regex-Alternation in CQL)

---

## Commit-Message (NICHT ausgeführt)

```
fix(advanced-search): Restore BlackLab as single source of truth for filtering

PROBLEM:
- Previous implementation broke pagination by filtering in Python
- recordsFiltered was calculated from partial results (1 page only)
- Doc-metadata filters (country, radio) were applied post-BlackLab
- Speaker filters used non-standard BlackLab approach
- CQL validator blocked valid regex alternation (pipes)

SOLUTION:
1. Remove Python-side filtering (_matches_metadata_filters, etc.)
2. Doc-metadata → BlackLab filter parameter (country_code:VEN)
3. Speaker attributes → CQL token constraint (speaker_code="(lib-pf|...)")
4. recordsTotal = recordsFiltered = BlackLab's numberOfHits
5. Fix mode=pos conflict with speech_mode parameter
6. Allow pipes in CQL validator for regex alternation

TEST RESULTS:
✓ Simple lemma search: 761 hits
✓ POS mode (q=VERB): 150,866 hits
✓ Speaker filter (sex=f): 284 hits
✗ Country filter: 0 hits (metadata not in index - needs rebuild)

FILES:
- src/app/search/advanced_api.py: Remove Python filtering
- src/app/search/cql.py: Proper filter architecture
- src/app/search/cql_validator.py: Allow pipes
- docs/blacklab-advanced-search-status.md: Document current state

NEXT: Rebuild index with doc-metadata import to enable country/radio filters
```

---

## 1. Zielsetzung
Das Ziel der aktuellen Arbeit war, die neue BlackLab‑5.x‑Instanz (JSON → TSV → Index) stabil mit dem Flask-basierten Advanced Search Frontend zu verbinden. Dieses Dokument hält fest, welche Teile bereits verlässlich funktionieren, welche Unterschiede zur einfachen Corpus-Suche bestehen und welche offenen Punkte noch angegangen werden müssen.

## 2. Erreichte Ergebnisse
| Bereich | Quelle | Resultat | Kommentar |
| --- | --- | --- | --- |
| **Index & Datenpipeline** | `LOKAL/.../blacklab_index_creation.py` + `scripts/build_blacklab_index_v3.ps1` | ✅ Token-Annotationen gespeichert | TSV-Export enthält `word`, `norm`, `lemma`, `pos`, morphologische Features, Zeitstempel, Speaker-Code; BlackLab erstellt Index mit 1.488.019 Tokens. |
| **BlackLab 5.x Server** | `scripts/start_blacklab_docker_v3.ps1` + `config/blacklab/blacklab-server.yaml` | ✅ Läuft auf Port 8081 | `configVersion 2`, korrekte `annotatedFields`, Mount auf `/data/index/corapan`. |
| **API-Integration** | `src/app/search/advanced_api.py` | ✅ liefert left/match/right + metadata | `listvalues` enthält `word` und `utterance_id`, Ergebnisverarbeitung mappt `before/after` zu `left/right`. |
| **Metadaten (docmeta)** | `data/blacklab_export/docmeta.jsonl` → `_DOCMETA_CACHE` | ⚠️ teilweise | `country`, `radio`, `date`, `city` gefüllt, `speaker_type`, `sex`, `mode`, `discourse` bleiben leer, weil sie im Export nicht zur Verfügung stehen. |
| **Filter & CQL** | `src/app/search/cql.py` & `filters_to_blacklab_query` | ⚠️ noch nicht funktionsfähig | Filterparameter führen aktuell zu `recordsTotal=0`; die Übersetzung in CQL muss überarbeitet werden. |
| **Feldkonsistenz zu Simple Search** | Vergleich Corpus UI (Simple Search) vs. Advanced Search API | ⚠️ Unterschiede | Advanced Search liefert `file_id`, Simple Search nutzt `filename`; die resultierenden `listvalues` und Metadatenschlüssel sind unterschiedlich. |

## 3. Beobachtete Limitierungen
1. **Leere Spalten (`hablante`, `sexo`, `modo`, `discurso`)** – Diese Felder kommen aus den Transkript-JSON-Dateien nicht in den Docmeta Export. Bis sie exportiert werden, bleiben die Spalten in Advanced Search leer (bzw. als `""`).
2. **Filter führen zu 0 Treffern** – Solange `filters_to_blacklab_query` keine gültige CQL‑Kombination aus den Parametern `country`, `mode`, `discourse`, `sex`, `speaker_type` erzeugt, liefert die API keine Treffer mehr. Das betrifft aktuell sämtliche Filterkategorien.
3. **Metadaten widersprechen Corpus UI** – Während Simple Search `filename` (=eigentlicher Dateiname der Transkriptquelle) ausgibt, verwendet Advanced Search das aus Docmeta stammende `file_id`. Auch die zusätzlichen Hilfsfelder (`country_code`, `date`, `radio`, `city`) sind teilweise unterschiedlich benannt bzw. formatiert.
4. **POS-Suche liefert keine Ergebnisse** – Obwohl BlackLab über CQL `[pos="VERB"]` Treffer liefert, liefert das Advanced Search API `recordsTotal=0` für `mode=pos`. Ursache noch unklar (eventuell Filter/Sensitivitäts-Handling oder fehlende Parametrisierung im Frontend).

## 4. Empfohlene nächste Schritte
- **Filter-CQL-Generator überarbeiten**: `filters_to_blacklab_query` muss gezielt CQL wie `[country_code="VEN"]` oder `[pos="VERB"]` produzieren, ohne das Pattern mit `mode` zu überlagern. Ein kleiner Log-Auszug pro Filter-Query hilft bei der Validierung.
- **Docmeta erweitern**: `hablante`, `sexo`, `modo`, `discurso` sollten entweder direkt im Export aufgenommen oder über eine separate Datei (z. B. `docmeta_enriched.jsonl`) ergänzt werden.`
- **Feldnamen aus Simple Search übernehmen**: Für die Felder `filename`/`file_id` und `country`/`country_code` sollte ein Mapping definiert werden, damit die beiden UIs dieselben Spalten liefern.
- **POS-Mode debuggen**: Untersuchen, welche CQL tatsächlich abgesendet wird (Logging in `_make_bls_request` einbauen) und ob `mode=pos` im Frontend korrekt übergeben wird. Eine direkte Abfrage mit `mode=pos` sollte im Browser das gleiche Resultat wie `[pos="VERB"]` zeigen.
- **Testfälle dokumentieren**: Beispiele wie `q=casa` (lemma), `q=crisis` (`mode=forma`) und `mode=pos=VERB` dokumentieren, um Regressionen leichter zu erkennen.

Mit diesen Informationen kann das Team gezielt weiterarbeiten, um alle Filter und zusätzlichen Spalten abzustimmen.

---

## Doc-Metadaten-Integration: Zusammenfassung (14.11.2025 - 15:30 Uhr)

### Geänderte Dateien (Metadaten-Anbindung)

1. **`config/blacklab/blacklab-server.yaml`** (NEU: Metadaten-Import)
   ```yaml
   corpora:
     corapan:
       metadata:
         documentFormat: jsonlines
         path: /data/export/docmeta.jsonl
         idField: file_id
   ```

2. **`scripts/start_blacklab_docker_v3.ps1`** (Docker-Mount erweitert)
   - Mount hinzugefügt: `data\blacklab_export` → `/data/export` (read-only)
   - Ermöglicht BlackLab-Zugriff auf `docmeta.jsonl`

3. **`config/blacklab/corapan-tsv.blf.yaml`** (Metadaten-Typen korrigiert)
   - `country_code`, `date`, `file_id`, `audio_path`: `type: untokenized`
   - `radio`, `city`: `type: text` (tokenisiert)
   - Entfernt: ungültige `valuePath`-Einträge (nicht benötigt für externe JSONL)

4. **`test_docmeta_integration.ps1`** (NEU: Validierungs-Skript)
   - Prüft BlackLab-Server-Erreichbarkeit
   - Verifiziert Metadaten-Schema
   - Testet ob Felder gefüllt sind
   - Validiert Filter-Funktionalität

### Erwartete Ergebnisse (nach Index-Rebuild)

**BlackLab Corpus Schema** (`GET /blacklab-server/corpora/corapan`):
```json
{
  "metadataFields": {
    "file_id": {"type": "text", "values": 146},
    "country_code": {"type": "text", "values": 9},
    "date": {"type": "text", "values": 146},
    "radio": {"type": "text", "values": 15},
    "city": {"type": "text", "values": 12},
    "audio_path": {"type": "text", "values": 0}
  }
}
```

**Dokument mit Metadaten** (Beispiel):
```json
{
  "docPid": "2023-08-10_ARG_Mitre",
  "metadata": {
    "file_id": "2023-08-10_ARG_Mitre",
    "country_code": "ARG",
    "date": "2023-08-10",
    "radio": "Radio Mitre",
    "city": "Buenos Aires",
    "audio_path": ""
  }
}
```

**Advanced API mit Country-Filter**:
```
Request: GET /search/advanced/data?q=casa&mode=lemma&country_code=VEN&length=1
```
```json
{
  "recordsTotal": 150,
  "recordsFiltered": 150,
  "data": [{
    "match": "casa",
    "country": "VEN",
    "radio": "RCR",
    "city": "Caracas",
    "date": "2022-01-18",
    "speaker_type": "pre",
    "sex": "m"
  }]
}
```

### Offene Punkte

1. **_DOCMETA_CACHE vs. BlackLab-Metadaten**
   - UI-Metadaten werden aktuell aus `_DOCMETA_CACHE` geladen (in `advanced_api.py`)
   - Filter laufen aber über BlackLab
   - **Empfehlung**: Beide Quellen sind synchron, kein Handlungsbedarf
   - **Optional**: `_DOCMETA_CACHE` entfernen, nur BlackLab-Metadaten nutzen

2. **Tests erweitern**
   - `test_advanced_api_quick.py` um Metadaten-Validierung erweitern
   - Prüfen: Sind `country`, `radio`, `city`, `date` in Response gefüllt?

### Commit-Message (für diese Runde)

```
feat(blacklab): wire docmeta.jsonl into corapan index metadata

- Configure blacklab-server.yaml with JSONL metadata import
- Mount data/blacklab_export in Docker for docmeta.jsonl access  
- Fix metadata field types in corapan-tsv.blf.yaml
- Add test_docmeta_integration.ps1 validation script

Doc metadata filters (country, radio, city, date) will work after
index rebuild. TSV export and speaker filters remain unchanged.
```

---

## Vorgeschlagene Commit-Message (CQL Hardening - 15.11.2025)

```
fix(advanced-search): harden CQL builder to prevent Flask crashes

- Make build_token_cql/build_cql robust against missing/empty metadata filters
- Add defensive None checks in build_cql_with_speaker_filter
- Filter empty strings from country_codes list in build_metadata_cql_constraints
- Ensure all CQL building functions handle None/empty inputs gracefully
- Use annotation-based constraints for country/radio/city/date consistently

CQL-Building-Funktionen werfen jetzt klare ValueErrors bei ungültigen Inputs
statt mit AttributeError/KeyError zu crashen. Metadatenfilter werden über
Token-Annotations im CQL-Pattern angewendet (nicht mehr über BlackLab doc filter).

Tests: All 5 tests in test_advanced_api_quick.py pass (simple search, country
filter, speaker filter, POS mode).
```