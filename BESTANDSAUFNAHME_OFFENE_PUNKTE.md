# Abschnitt 6: Offene Punkte / Potentielle Stolpersteine

## 6.1 Unsicherheiten

### 1. BlackLab-Feld `date` vorhanden?

**Problem:** Simple-DB hat `date` (Aufnahmedatum), aber ich sehe es nicht in BlackLab-Metadaten.

**Prüfung nötig:**
- Ist `date` im BlackLab-Index konfiguriert? (siehe `config/blacklab/*.blf.yaml`)
- Falls ja: `metadata.date` sollte verfügbar sein
- Falls nein: Advanced kann kein Datum anzeigen (im Gegensatz zu Simple)

**Auswirkung:**
- Wenn `date` fehlt, kann Advanced keine zeitbasierte Filterung/Anzeige bieten
- Unified-Mapping muss `date` optional machen

---

### 2. Zeit-Einheiten: Sekunden vs. Millisekunden

**Problem:** Simple nutzt Sekunden (`start: 42.5`), Advanced nutzt Millisekunden (`start_ms: 42500`).

**Aktuell:**
- Simple: `start` und `end` sind REAL (Sekunden, z.B. 42.5)
- Advanced: `start_ms` und `end_ms` sind INTEGER (Millisekunden, z.B. 42500)

**Unified-Vorschlag:**
- Konvertiere Advanced → Sekunden: `start_ms / 1000.0`
- API-Contract: **Sekunden** (REAL, 2 Nachkommastellen)
- Frontend muss nicht wissen, ob Quelle DB oder BlackLab ist

**Code:**
```python
"start": match_info.get("start_ms", [0])[0] / 1000.0 if match_info.get("start_ms") else 0.0,
```

---

### 3. `context_start` / `context_end` in BlackLab?

**Problem:** Simple-DB hat `context_start` und `context_end` (Start/End des gesamten Kontexts), aber BlackLab liefert diese nicht direkt.

**Möglichkeit 1:** BlackLab berechnet diese nicht, da `wordsaroundhit=10` nur die Wörter liefert, nicht deren Zeitstempel.

**Möglichkeit 2:** BlackLab-Index hat diese Informationen, aber `listvalues` enthält sie nicht.

**Workaround:** Falls nicht vorhanden, könnten wir schätzen:
```python
"context_start": (start_ms / 1000.0) - 2.0,  # Schätzung: 2 Sekunden vor Wort
"context_end": (end_ms / 1000.0) + 2.0,      # Schätzung: 2 Sekunden nach Wort
```

**Oder:** Feld optional machen (nur für Simple verfügbar).

---

### 4. Audio-Player-Logik unterschiedlich

**Simple:** Backend liefert `audio_available: true/false`, Frontend rendert 2 Buttons (Pal + Ctx).

**Advanced:** Frontend rendert `<audio>`-Tag direkt, nutzt `/media/segment/...`-Endpoint.

**Frage:** Sollen beide das gleiche Render-Verhalten haben?

**Vorschlag:**
- Unified: Backend liefert `audio_available`, `start`, `end`, `context_start`, `context_end`
- Frontend entscheidet, ob Buttons oder Audio-Tag (kann unterschiedlich bleiben)

---

## 6.2 Semantische Unterschiede

### 1. Normalisierung (sensitive=0 vs. Case-Insensitive)

**Simple:**
- `sensitive=1`: Suche auf `text` (Original)
- `sensitive=0`: Suche auf `norm` (lowercase, no accents)
- Normalisierung via `_normalize_for_search()` (L179-197)

**Advanced:**
- `case_sensitive=0`: CQL nutzt `(?i)` Flag (Case-Insensitive)
- Akzent-Normalisierung: Unklar, ob BlackLab das automatisch macht?

**Potenzielle Inkonsistenz:**
- Simple: "Casa" ≠ "casa" (bei sensitive=1)
- Advanced: "Casa" = "casa" (bei case_sensitive=0, aber `(?i)` macht das)

**Frage:** Behandeln beide Systeme Akzente gleich?

**Prüfung nötig:** Test mit Wort "año" vs. "ano"
- Simple sensitive=0: Findet beide
- Advanced case_sensitive=0: Findet beide? (hängt von BlackLab-Analyzer ab)

---

### 2. Multi-Word-Sequenzen

**Simple:**
- Multi-Word via `_build_word_query()` (L200-287)
- JOIN über `tokens` Tabelle (z.B. `t1 JOIN t2 ON t2.id = t1.id + 1`)
- Resultat: `text = "Wort1 Wort2"` (kombiniert)

**Advanced:**
- Multi-Word via CQL: `[word="Wort1"] [word="Wort2"]`
- BlackLab liefert `match.word = ["Wort1", "Wort2"]` (Array)
- Backend joined: `" ".join(match)`

**Semantisch identisch**, aber Implementation unterschiedlich.

---

## 6.3 Kandidaten-Ort für gemeinsame Helper-Funktion

### Empfehlung: `src/app/services/corpus_search.py`

**Begründung:**
- Bereits zentrale Stelle für Corpus-Suche
- `CANON_COLS` definiert hier (L22-40)
- `_row_to_dict()` bereits vorhanden (L437-473)
- Logische Erweiterung: `serialize_hit_to_row(hit, source='db'|'blacklab')`

**Zeilen:** Nach L473 (nach `_row_to_dict`)

**Neue Funktion:**

```python
def serialize_hit_to_row(
    hit: dict | sqlite3.Row,
    source: Literal['db', 'blacklab'] = 'db',
    row_number: int | None = None
) -> dict[str, object]:
    """
    Unified Hit → Row Mapping für Simple (DB) und Advanced (BlackLab).
    
    Garantiert:
    - Identische Keys aus CANON_COLS für beide Quellen
    - Zeit in Sekunden (konvertiert von MS wenn nötig)
    - Helper-Felder (audio_available, word_count)
    
    Args:
        hit: Hit-Objekt (sqlite3.Row oder BlackLab-JSON-Dict)
        source: 'db' für Simple (SQLite), 'blacklab' für Advanced
        row_number: Optional Zeilennummer (für row_number Field)
    
    Returns:
        Dict mit CANON_COLS Keys + Helper-Felder
    
    Example (Simple):
        >>> row = cursor.fetchone()  # sqlite3.Row
        >>> serialize_hit_to_row(row, source='db', row_number=1)
        {'token_id': 'ARG_...', 'text': 'casa', ...}
    
    Example (Advanced):
        >>> hit = bls_response['hits'][0]  # BlackLab JSON
        >>> serialize_hit_to_row(hit, source='blacklab', row_number=1)
        {'token_id': 'ARG_...', 'text': 'casa', ...}
    """
    if source == 'db':
        result = _row_to_dict(hit)
        if row_number is not None:
            result['row_number'] = row_number
        return result
    
    elif source == 'blacklab':
        # BlackLab → CANON_COLS Mapping
        left = hit.get("left", {}).get("word", [])
        match = hit.get("match", {}).get("word", [])
        right = hit.get("right", {}).get("word", [])
        
        match_info = hit.get("match", {})
        metadata = hit.get("metadata", {})
        
        # Zeit-Konvertierung: MS → Sekunden
        start_ms = match_info.get("start_ms", [0])[0] if match_info.get("start_ms") else 0
        end_ms = match_info.get("end_ms", [0])[0] if match_info.get("end_ms") else 0
        
        result = {
            # CANON_COLS (17 Felder)
            "token_id": match_info.get("tokid", [None])[0] or "",
            "filename": metadata.get("filename", ""),
            "country_code": metadata.get("country", ""),
            "radio": metadata.get("radio", ""),
            "date": metadata.get("date", ""),  # Möglicherweise nicht vorhanden
            "speaker_type": metadata.get("speaker_type", ""),
            "sex": metadata.get("sex", ""),
            "mode": metadata.get("mode", ""),
            "discourse": metadata.get("discourse", ""),
            "text": " ".join(match),
            "start": start_ms / 1000.0,  # Konvertierung
            "end": end_ms / 1000.0,
            "context_left": " ".join(left[-10:]) if left else "",
            "context_right": " ".join(right[:10]) if right else "",
            "context_start": (start_ms / 1000.0) - 2.0,  # Schätzung
            "context_end": (end_ms / 1000.0) + 2.0,
            "lemma": " ".join(match_info.get("lemma", [])),
            
            # Helper-Felder
            "audio_available": bool(metadata.get("filename")),
            "word_count": len(match) if match else 1,
        }
        
        if row_number is not None:
            result['row_number'] = row_number
        
        return result
    
    else:
        raise ValueError(f"Unknown source: {source}")
```

---

## 6.4 Stolpersteine bei Umsetzung

### 1. BlackLab-Index muss alle Metadaten haben

**Kritisch:**
- `country`, `speaker_type`, `sex`, `mode`, `discourse`, `filename`, `radio`
- Falls eines fehlt, muss Unified-Mapping mit Defaults arbeiten

**Prüfung nötig:**
- `config/blacklab/*.blf.yaml` durchsehen
- Sind alle Metadaten-Felder indexiert?

---

### 2. Frontend-Anpassungen minimal halten

**Glück:** Advanced-Frontend nutzt bereits Keys (`data: 'left'`, `data: 'match'`).

**ABER:** Backend liefert Arrays! Das muss geändert werden.

**Risiko:** Möglicherweise hat Advanced-Frontend versteckte Abhängigkeiten zu Array-Indizes?

**Empfehlung:** Schrittweise Migration:
1. Backend auf Objekte umstellen
2. Frontend testen (sollte funktionieren, da Keys definiert sind)
3. Falls Probleme: Frontend-Code debuggen

---

### 3. Export-Endpoints (CSV/TSV) auch anpassen

**Advanced:** `advanced_api.py` L376-673 (Export-Streaming)

**Aktuell:** Mapping dort dupliziert (L586-612).

**Nach Unified-Mapping:** Nutze `serialize_hit_to_row()` auch im Export:

```python
for hit in hits:
    row = serialize_hit_to_row(hit, source='blacklab')
    writer.writerow(row)  # CSV-Writer nutzt Dict-Keys
```

---

## 6.5 Checkliste für externen Assistenten

Wenn ein externer Assistent die Unified-Mapping-Implementierung macht, sollte er:

### Schritt 1: Code-Analyse (bereits erledigt in diesem Bericht)

- [x] Simple-Search Backend verstehen
- [x] Advanced-Search Backend verstehen
- [x] DataTables-Konfigurationen vergleichen
- [x] Identische Felder identifizieren

### Schritt 2: Helper-Funktion erstellen

- [ ] `serialize_hit_to_row()` in `corpus_search.py` implementieren
- [ ] Unit-Tests schreiben (DB-Mocking + BlackLab-JSON-Fixtures)
- [ ] Edge-Cases testen (fehlende Felder, leere Arrays, etc.)

### Schritt 3: Advanced-API refactoren

- [ ] `advanced_api.py` L277-291: Nutze `serialize_hit_to_row()` statt Array-Building
- [ ] `advanced_api.py` L586-612: Nutze `serialize_hit_to_row()` im Export
- [ ] Response-Format ändern: Arrays → Objekte

### Schritt 4: Frontend testen

- [ ] Advanced-Search aufrufen
- [ ] DataTables rendert korrekt (sollte automatisch funktionieren)
- [ ] Falls Probleme: Frontend-JS debuggen

### Schritt 5: Integration testen

- [ ] Simple-Search: Weiterhin funktioniert (keine Breaking Changes)
- [ ] Advanced-Search: Objekte statt Arrays, identische Spalten wie Simple
- [ ] Export: CSV/TSV mit korrekten Headers

### Schritt 6: Dokumentation

- [ ] Update `docs/reference/corpus-api-canonical-columns.md`
- [ ] Migration-Guide schreiben (Arrays → Objekte für Advanced)
- [ ] CHANGELOG.md aktualisieren

---

## Zusammenfassung

### Unsicherheiten (vor Implementierung klären)

1. **BlackLab-Index:** Sind alle Metadaten-Felder vorhanden? (`date`, `radio`, etc.)
2. **Zeit-Kontext:** Liefert BlackLab `context_start`/`context_end`? Falls nein: Schätzung OK?
3. **Normalisierung:** Behandeln Simple (norm) und Advanced (case_insensitive) Akzente gleich?

### Stolpersteine

1. **Array → Objekt Migration** in Advanced-API (Breaking Change intern)
2. **Export-Endpoints** müssen auch angepasst werden (DRY)
3. **Frontend-Tests** nötig (sollte automatisch funktionieren, aber sicher ist sicher)

### Empfohlener Ort für gemeinsame Funktion

**`src/app/services/corpus_search.py`** (nach L473)

**Funktion:** `serialize_hit_to_row(hit, source='db'|'blacklab', row_number=None)`

**Begründung:**
- Bereits zentrale Stelle für Corpus-Suche
- `CANON_COLS` hier definiert
- `_row_to_dict()` hier vorhanden (als Basis)
- Logische Erweiterung
