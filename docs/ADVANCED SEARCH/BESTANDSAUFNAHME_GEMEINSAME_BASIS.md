# Abschnitt 5: Gemeinsame Datenbasis / Mapping-Potenzial

## 5.1 Identische Felder zwischen Simple und Advanced

Folgende Felder sind semantisch identisch und können unified werden:

### Metadaten (100% identisch)

| Feld | Simple (DB) | Advanced (BlackLab) | Aktueller Name (Unified) |
|------|-------------|---------------------|--------------------------|
| **Land** | `country_code` | `metadata.country` | **`country_code`** ✅ |
| **Sprecher-Typ** | `speaker_type` | `metadata.speaker_type` | **`speaker_type`** ✅ |
| **Geschlecht** | `sex` | `metadata.sex` | **`sex`** ✅ |
| **Modus** | `mode` | `metadata.mode` | **`mode`** ✅ |
| **Diskurs** | `discourse` | `metadata.discourse` | **`discourse`** ✅ |
| **Dateiname** | `filename` | `metadata.filename` | **`filename`** ✅ |
| **Radiosender** | `radio` | `metadata.radio` | **`radio`** ✅ (nicht in UI) |

### Treffer-Daten (semantisch identisch, Namen unterschiedlich)

| Feld | Simple (DB) | Advanced (BlackLab) | Vorschlag Unified | Anmerkung |
|------|-------------|---------------------|-------------------|-----------|
| **Kontext links** | `context_left` | `left.word` (join) | **`context_left`** | Expliziter Name bevorzugt |
| **Treffer** | `text` | `match.word` (join) | **`text`** oder **`match`** | Beides OK, `text` ist DB-Standard |
| **Kontext rechts** | `context_right` | `right.word` (join) | **`context_right`** | Expliziter Name |
| **Token-ID** | `token_id` | `match.tokid[0]` | **`token_id`** | Vollständiger Name |
| **Start-Zeit** | `start` (Sekunden) | `match.start_ms[0]` (MS) | **`start`** (Sekunden) | **KONVERTIERUNG NÖTIG:** ms → sek |
| **End-Zeit** | `end` (Sekunden) | `match.end_ms[0]` (MS) | **`end`** (Sekunden) | **KONVERTIERUNG NÖTIG:** ms → sek |

### Zusätzliche Felder (nur in einem System vorhanden)

| Feld | Nur in Simple | Nur in Advanced | Unified-Vorschlag |
|------|---------------|-----------------|-------------------|
| **Lemma** | ✅ `lemma` (DB) | ✅ `match.lemma` (BlackLab) | **`lemma`** (beide können liefern!) |
| **POS** | ❌ (nicht in DB) | ✅ `match.pos` (BlackLab) | **`pos`** (nur Advanced) |
| **Datum** | ✅ `date` (DB) | ❌ (nicht in BlackLab-Metadata?) | **`date`** (nur Simple) |
| **Context-Start** | ✅ `context_start` (DB) | ❌ (nicht geliefert) | **`context_start`** (nur Simple) |
| **Context-End** | ✅ `context_end` (DB) | ❌ (nicht geliefert) | **`context_end`** (nur Simple) |

---

## 5.2 Simple-Search-Mapping-Funktion (bereits vorhanden)

### Funktion: `_row_to_dict()`

**Datei:** `src/app/services/corpus_search.py`  
**Zeilen:** L437-473

**Signatur:**
```python
def _row_to_dict(row: sqlite3.Row) -> dict[str, object]:
    """Konvertiert sqlite3.Row zu Dict mit CANON_COLS Keys."""
```

**Parameter:**
- `row`: sqlite3.Row (mit Row-Factory aktiviert)

**Return:**
- `dict` mit genau den Keys aus `CANON_COLS` + Helper-Felder

**Funktion:**
- Extrahiert alle Felder aus `CANON_COLS` (L22-40)
- Fügt Helper-Felder hinzu:
  - `audio_available`: Boolean (prüft, ob MP3 existiert)
  - `transcript_available`: Boolean (prüft, ob JSON existiert)
  - `transcript_name`: String (JSON-Dateiname)
  - `word_count`: Integer (aus Query oder Default 1)

**Warum gut:**
- Zentrale Stelle für DB → DataTables Mapping
- Garantiert stabile Keys (unabhängig von DB-Spaltenreihenfolge)
- Bereits produktiv im Einsatz

---

## 5.3 Advanced-Search-Mapping (aktuell verteilt)

### Status Quo

**Datei:** `src/app/search/advanced_api.py`  
**Zeilen:** L240-291

**Aktuell:** Mapping passiert **inline** im Endpoint:

```python
processed_hits = []
for hit in hits:
    left = hit.get("left", {}).get("word", [])
    match = hit.get("match", {}).get("word", [])
    right = hit.get("right", {}).get("word", [])
    
    match_info = hit.get("match", {})
    tokid = match_info.get("tokid", [None])[0]
    start_ms = match_info.get("start_ms", [0])[0] if match_info.get("start_ms") else 0
    end_ms = match_info.get("end_ms", [0])[0] if match_info.get("end_ms") else 0
    
    hit_metadata = hit.get("metadata", {})
    
    # ARRAY-Bildung (nicht Objekt!)
    processed_hits.append([
        " ".join(left[-10:]) if left else "",
        " ".join(match),
        " ".join(right[:10]) if right else "",
        hit_metadata.get("country", ""),
        hit_metadata.get("speaker_type", ""),
        hit_metadata.get("sex", ""),
        hit_metadata.get("mode", ""),
        hit_metadata.get("discourse", ""),
        hit_metadata.get("filename", ""),
        hit_metadata.get("radio", ""),
        str(tokid),
        f"{start_ms}",
        f"{end_ms}",
    ])
```

**Problem:**
- Mapping verteilt (auch im Export-Endpoint L586-612 dupliziert!)
- ARRAY-Rückgabe (nicht Objekt-kompatibel mit Simple)
- Keine zentrale Helper-Funktion

---

## 5.4 Wie leicht wäre gemeinsames Mapping?

### Schwierigkeitsgrad: **LEICHT** ✅

**Schritt 1:** Erweitere `corpus_search.py` um BlackLab-Support

```python
# src/app/services/corpus_search.py

def serialize_hit_to_row(hit: dict | sqlite3.Row, source: str = 'db') -> dict:
    """
    Unified Hit → Row Mapping für Simple (DB) und Advanced (BlackLab).
    
    Args:
        hit: Hit-Objekt (sqlite3.Row oder BlackLab-JSON-Dict)
        source: 'db' für Simple, 'blacklab' für Advanced
    
    Returns:
        Dict mit CANON_COLS Keys + Helper-Felder
    """
    if source == 'db':
        return _row_to_dict(hit)  # Bereits vorhanden!
    
    elif source == 'blacklab':
        # BlackLab → CANON_COLS Mapping
        left = hit.get("left", {}).get("word", [])
        match = hit.get("match", {}).get("word", [])
        right = hit.get("right", {}).get("word", [])
        
        match_info = hit.get("match", {})
        metadata = hit.get("metadata", {})
        
        # Zeit-Konvertierung: ms → sekunden
        start_ms = match_info.get("start_ms", [0])[0] if match_info.get("start_ms") else 0
        end_ms = match_info.get("end_ms", [0])[0] if match_info.get("end_ms") else 0
        
        return {
            # CANON_COLS
            "token_id": match_info.get("tokid", [None])[0] or "",
            "filename": metadata.get("filename", ""),
            "country_code": metadata.get("country", ""),
            "radio": metadata.get("radio", ""),
            "date": metadata.get("date", ""),  # Falls vorhanden
            "speaker_type": metadata.get("speaker_type", ""),
            "sex": metadata.get("sex", ""),
            "mode": metadata.get("mode", ""),
            "discourse": metadata.get("discourse", ""),
            "text": " ".join(match),
            "start": start_ms / 1000.0,  # Konvertierung MS → Sekunden
            "end": end_ms / 1000.0,
            "context_left": " ".join(left[-10:]) if left else "",
            "context_right": " ".join(right[:10]) if right else "",
            "context_start": 0,  # BlackLab liefert nicht (könnte berechnet werden)
            "context_end": 0,
            "lemma": " ".join(match_info.get("lemma", [])),
            
            # Helper-Felder
            "audio_available": True,  # Annahme: BL-Hits haben immer Audio
            "word_count": len(match) if match else 1,
        }
```

**Schritt 2:** Nutze in Advanced-API

```python
# src/app/search/advanced_api.py

from ..services.corpus_search import serialize_hit_to_row

@bp.route("/data", methods=["GET"])
def datatable_data():
    # ... (BLS-Request wie vorher)
    
    hits = data.get("hits", [])
    
    # OBJEKT-Mode (statt Arrays)
    processed_hits = [
        serialize_hit_to_row(hit, source='blacklab')
        for hit in hits
    ]
    
    return jsonify({
        "draw": draw,
        "recordsTotal": number_of_hits,
        "recordsFiltered": number_of_hits,
        "data": processed_hits,  # Jetzt Objekte!
    })
```

**Schritt 3:** Frontend muss nicht geändert werden (bereits Key-basiert!)

---

## 5.5 POS/lemma-Erweiterbarkeit

### Was ist bereits vorhanden?

| Feature | Simple (DB) | Advanced (BlackLab) | UI-Anzeige aktuell |
|---------|-------------|---------------------|---------------------|
| **Lemma** | ✅ `lemma` (Spalte) | ✅ `match.lemma[]` | ❌ Nicht angezeigt |
| **POS** | ❌ Nicht in DB | ✅ `match.pos[]` | ❌ Nicht angezeigt |
| **Morphologie** | ❌ Nicht in DB | ✅ (falls indexiert) | ❌ Nicht angezeigt |

### Potenzial

**Lemma anzeigen:** Könnte als zusätzliche Spalte in beide UIs eingebaut werden

**Spalte 13: Lemma**
- Simple: `data: 'lemma'` (aus DB)
- Advanced: `data: 'lemma'` (aus `serialize_hit_to_row`)

**POS anzeigen:** Nur in Advanced möglich (nicht in Simple-DB)

**Spalte 14: POS** (nur Advanced)
- Advanced: `data: 'pos'`
- Simple: `-` (nicht verfügbar)

**Export:** Beide Felder könnten im CSV/TSV-Export inkludiert werden

---

## Zusammenfassung

### Gemeinsame Felder (Ready for Unification)

**11 identische Felder:**
1. `country_code`
2. `speaker_type`
3. `sex`
4. `mode`
5. `discourse`
6. `filename`
7. `context_left` (Simple direkt, Advanced von `left.word`)
8. `text` (Simple direkt, Advanced von `match.word`)
9. `context_right` (Simple direkt, Advanced von `right.word`)
10. `token_id` (Simple direkt, Advanced von `match.tokid[0]`)
11. `lemma` (beide haben, keiner zeigt)

**2 Felder mit Konvertierung nötig:**
- `start` (Simple: Sekunden, Advanced: Millisekunden → `/1000`)
- `end` (Simple: Sekunden, Advanced: Millisekunden → `/1000`)

**Exklusive Felder:**
- Simple only: `date`, `context_start`, `context_end`, `radio` (aber radio ist auch in BlackLab?)
- Advanced only: `pos` (POS-Tags)

### Mapping-Funktion bereits da?

**Ja, für Simple!**
- `_row_to_dict()` ist bereits produktiv
- Kann leicht erweitert werden zu `serialize_hit_to_row(hit, source='db'|'blacklab')`

### Empfohlener nächster Schritt

1. Erweitere `corpus_search.py` um `serialize_hit_to_row()` mit BlackLab-Support
2. Nutze in `advanced_api.py` L240-291 (ersetze Array-Building)
3. Nutze in `advanced_api.py` L586-612 (Export) → DRY
4. Frontend muss nicht geändert werden (bereits Key-basiert)
5. Beide UIs haben identische Data-Struktur → Wartbarkeit ↑
