# CO.RA.PAN Corpus Token-Suche & Snapshot - Testspezifikation

## Vorbereitung
- Browser: Chrome/Firefox aktuell
- Testdaten: Mindestens Token-IDs wie ECUb44b0, VEN99289, ARG-Cba0a43f in DB vorhanden

---

## 1. TOKEN-PARSER TESTS

### Test 1.1: Whitespace & Delimiter Normalisierung
**Input:** `" A ;B;  C ,  D\nE  "` (diverse Trennzeichen, Leerzeichen)
**Erwartetes Verhalten:**
- Tagify zeigt 5 Tags: `A`, `B`, `C`, `D`, `E`
- Reihenfolge: genau wie Eingabe
- Keine leeren Tags

### Test 1.2: Duplikat-Erkennung (Case-Insensitive)
**Input:** `ARG-Cba0a43f; arg-cba0a43f`
**Erwartetes Verhalten:**
- Nur 1 Tag wird erstellt (erster Match)
- Tag zeigt Original-Case der ersten Eingabe

### Test 1.3: Ungültige Zeichen werden ignoriert
**Input:** `ABC123-valid; @#$invalid; XYZ_999`
**Erwartetes Verhalten:**
- Tag 1: `ABC123-valid` (akzeptiert)
- `@#$invalid` wird abgelehnt (visuelles Feedback)
- `XYZ_999` wird abgelehnt (Underscore nicht erlaubt)

---

## 2. ORDERING TESTS

### Test 2.1: Input-Reihenfolge → Tabellen-Reihenfolge
**Setup:**
1. Token-Tab öffnen
2. Eingabe: `VEN99289, ECUb44b0, ARG-Cba0a43f`
3. Suche ausführen

**Erwartetes Verhalten:**
- Ergebnistabelle zeigt Treffer in dieser Reihenfolge:
  - Alle `VEN99289`-Zeilen zuerst (nach `start_ms` sortiert)
  - Dann alle `ECUb44b0`-Zeilen
  - Dann alle `ARG-Cba0a43f`-Zeilen

### Test 2.2: Drag-Reorder ändert Ergebnis-Sortierung
**Setup:**
1. Token-Tab: `A, B, C` eingeben
2. Via Drag-&-Drop: `C` an erste Position ziehen → `C, A, B`
3. Suche ausführen

**Erwartetes Verhalten:**
- Tabelle zeigt `C`-Tokens zuerst, dann `A`, dann `B`

### Test 2.3: Sekundär-Sortierung nach start_ms
**Setup:**
- Token mit mehreren Vorkommen im gleichen File
- z.B. 3x `ECUb44b0` bei Start 1000ms, 2000ms, 3000ms

**Erwartetes Verhalten:**
- Innerhalb eines Tokens: chronologische Sortierung (1000 < 2000 < 3000)

---

## 3. CASE-INSENSITIVITY TESTS

### Test 3.1: Matching unabhängig von Groß-/Kleinschreibung
**Setup:**
- DB enthält Token-ID: `ECUb44b0`
- Eingabe: `ecub44b0` (komplett klein)

**Erwartetes Verhalten:**
- Treffer werden gefunden
- Anzeige in Tabelle: Original-Case aus DB (`ECUb44b0`)

### Test 3.2: Mixed-Case Input
**Setup:**
- Eingabe: `EcUb44B0` (gemischt)

**Erwartetes Verhalten:**
- Identische Treffer wie bei Test 3.1

---

## 4. SNAPSHOT TESTS

### Test 4.1: Simple-Suche Export/Import
**Setup:**
1. Simple-Tab: Query `palabra`, Filter `ARG, VEN`, Sexo `m`
2. Suche ausführen → z.B. 42 Treffer
3. "Exportar estado" klicken → `corapan_snapshot.json` Download

**Datei-Validierung:**
```json
{
  "schema": "corapan.corpus.snapshot",
  "version": 1,
  "timestamp": "2025-10-07T...",
  "form": {
    "active_tab": "tab-simple",
    "search_mode": "text",
    "query": "palabra",
    "token_ids": [],
    "filters": {
      "country_code": ["ARG","VEN"],
      "sex": ["m"],
      ...
    }
  }
}
```

**Import-Test:**
1. Seite neu laden (Formular leer)
2. "Importar estado" → Datei auswählen
3. Prüfen:
   - Query-Feld zeigt `palabra`
   - Filter korrekt gesetzt
   - Suche wird automatisch ausgeführt
   - **Trefferanzahl identisch** (42)

### Test 4.2: Token-Suche Export/Import mit Reorder
**Setup:**
1. Token-Tab: `A, B, C` eingeben
2. Via Drag: Umordnen zu `C, A, B`
3. Suche → Ergebnis notieren (Reihenfolge!)
4. Export

**Datei-Validierung:**
```json
{
  "form": {
    "active_tab": "tab-token",
    "search_mode": "token_ids",
    "token_ids": ["C","A","B"],
    ...
  }
}
```

**Import-Test:**
1. Seite neu laden
2. Import
3. Prüfen:
   - Token-Tab aktiv
   - Tagify zeigt 3 Tags: `C`, `A`, `B` (in dieser Reihenfolge)
   - Tabelle zeigt gleiche Reihenfolge wie vor Export

### Test 4.3: Snapshot mit invaliden Daten
**Setup:**
- JSON-Datei manuell editieren: `"version": 999`

**Erwartetes Verhalten:**
- Import zeigt Alert: `"Formato de archivo inválido"` oder ähnlich
- Formular bleibt unverändert

---

## 5. LIMIT TESTS

### Test 5.1: >2000 Tokens → Warnung
**Setup:**
- 2500 Token-IDs in Tagify eingeben (z.B. via Paste)

**Erwartetes Verhalten:**
- UI zeigt Warnung: `"Máximo 2000 tokens permitidos"`
- Zusätzliche Tags werden abgelehnt

### Test 5.2: Server-Side Limit Enforcement
**Setup:**
- Request mit 2500 Tokens manipuliert (Browser DevTools)

**Erwartetes Verhalten:**
- Server akzeptiert nur erste 2000
- Keine Fehler, Suche erfolgt mit 2000

---

## 6. SICHERHEIT TESTS

### Test 6.1: SQL-Injection Schutz
**Setup:**
- Token-Input: `ECU'; DROP TABLE tokens; --`

**Erwartetes Verhalten:**
- Ungültige Zeichen werden von Tagify abgelehnt
- Falls doch durchgelassen: Backend nutzt Prepared Statements → kein SQL-Fehler

### Test 6.2: XSS-Schutz
**Setup:**
- Token: `<script>alert('XSS')</script>`

**Erwartetes Verhalten:**
- Tagify akzeptiert nicht (Regex-Whitelist)
- Falls in DB: Jinja2 Auto-Escaping verhindert Ausführung

### Test 6.3: Leere Eingabe
**Setup:**
- Token-Tab: keine Tags
- Suche klicken

**Erwartetes Verhalten:**
- Alert: `"Por favor ingresa al menos un Token-ID"`

---

## 7. INTEGRATION TESTS

### Test 7.1: Audio-Buttons nach Token-Suche
**Setup:**
- Token-Suche mit gültigen IDs
- Ergebnistabelle geladen

**Erwartetes Verhalten:**
- Audio-Play-Button funktioniert
- Download-Button funktioniert
- Spectrogram-Button funktioniert

### Test 7.2: Player-Link aus Token-Tabelle
**Setup:**
- Klick auf Emisión-Icon in Token-Ergebnis

**Erwartetes Verhalten:**
- Player öffnet mit korrektem Token-ID-Parameter
- Audio lädt

### Test 7.3: DataTables stateSave
**Setup:**
1. Suche ausführen → Seite 3 navigieren
2. Sortierung ändern (z.B. nach País)
3. Browser-Refresh

**Erwartetes Verhalten:**
- Seite 3 bleibt aktiv
- Sortierung bleibt erhalten

---

## 8. CROSS-BROWSER TESTS

- [ ] Chrome 120+
- [ ] Firefox 120+
- [ ] Safari 17+ (Mac)
- [ ] Edge 120+

**Prüfpunkte:**
- Tagify Drag-&-Drop funktioniert
- Select2 Dropdowns funktionieren
- Snapshot Download funktioniert
- JSON File-Upload funktioniert

---

## 9. PERFORMANCE TESTS

### Test 9.1: 1000 Tokens
**Setup:**
- 1000 gültige Token-IDs eingeben
- Suche ausführen

**Erwartetes Verhalten:**
- Antwortzeit < 5 Sekunden
- Tabelle rendert ohne Freeze
- Browser bleibt responsiv

### Test 9.2: 10.000 Zeilen in Tabelle
**Setup:**
- Query mit sehr vielen Treffern

**Erwartetes Verhalten:**
- DataTables Pagination funktioniert flüssig
- Scroll performance akzeptabel

---

## TEST-CHECKLISTE (ABNAHME)

- [ ] Alle Parser-Tests bestanden
- [ ] Ordering korrekt
- [ ] Case-Insensitivity funktioniert
- [ ] Snapshot Export/Import beide Modi
- [ ] Limits werden enforced
- [ ] Keine Sicherheitslücken
- [ ] Audio/Player funktionieren
- [ ] Cross-Browser kompatibel
- [ ] Performance akzeptabel
