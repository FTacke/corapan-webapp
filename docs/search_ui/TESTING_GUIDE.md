# Search UI - Schnelltestanleitung

## Vorbereitung

1. **Terminal öffnen** in VS Code
2. **Virtual Environment aktivieren:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
3. **Flask starten:**
   ```powershell
   $env:FLASK_SECRET_KEY="test-key-local"
   python -m src.app.main
   ```
4. **Browser öffnen:**
   - Navigate zu: `http://localhost:5000/search/advanced`

---

## Test-Checkliste

### ✅ Basis-Funktionalität

#### 1. Seite lädt
- [ ] Seite wird ohne Fehler geladen
- [ ] Keine 404 für CSS/JS-Dateien (Browser-Konsole prüfen)
- [ ] MD3-Styles werden angewendet

-#### 2. Filter-Fields
- [ ] Auf "País" klicken → Dropdown öffnet sich
- [ ] Mehrere Länder auswählen (z.B. ESP, MEX, COL, ARG)
- [ ] Feld zeigt die Codes (z.B. `ESP, MEX, COL`) an und wird abgekürzt ("...") — das Feld darf nicht breiter werden
  
- [ ] Dropdown schließen (außerhalb klicken)
- [ ] Gleiches für andere Filter (Hablante, Sexo, Modo, Discurso)

#### 3. Aktive Filter Chips
- [ ] Chips erscheinen unterhalb der Filter
- [ ] Länder-Chips zeigen nur Code (z.B. "ESP")
- [ ] Andere Chips zeigen Typ + Wert (z.B. "Sexo: masculino")
- [ ] Auf Chip klicken → Filter wird entfernt
- [ ] Chip verschwindet
- [ ] Wert im Filter-Field wird entfernt

#### 3a. Label Backgrounds
- [ ] Floating labels (`.md3-outlined-textfield__label` und `__label--select`) sollten die Hintergrundfarbe des Elternelements erben.
- [ ] Prüfen: Label sitzt nahtlos auf dem Feld; kein sichtbarer Kontrast-Rahmen beim Fokus oder normaler Zustand.

#### 4. Optionen (Checkboxen)
- [ ] "Incluir emisoras regionales" an/aus schalten
- [ ] "Ignorar acentos/mayúsculas" an/aus schalten

---

### ✅ Advanced Mode

#### 5. Advanced-Toggle
   - Switch default (initial) ist deaktiviert/aus, optisch im "off" Zustand
   - Track zeigt die surface-variant Farbe
   - Thumb ist auf der linken Seite mit neutralem Ton

#### 6. Pattern-Builder
  - Campo: "Lema" wählen
  - Tipo: "es exactamente"
  - Valor: "comer" eingeben
  - Campo: "Categoría gramatical (POS)"
  - Tipo: "empieza por"
  - Valor: "N"

#### 7. Distanz-Regel

#### 8. CQL-Preview

#### 9. Plantillas
- [ ] "Verbo + sustantivo" Button klicken
- [ ] Pattern-Builder wird mit 2 Tokens befüllt
- [ ] CQL-Preview wird aktualisiert
- [ ] Andere Templates testen

---

### ✅ Form-Actions

#### 10. Formular absenden
- [ ] Query eingeben (z.B. "casa")
- [ ] Search-Type wählen (z.B. "Forma")
- [ ] Filter auswählen
- [ ] "Buscar" Button klicken
- [ ] Browser-Konsole prüfen: Query-Parameter werden geloggt
- [ ] (Hinweis: Tatsächliche Suche gegen BlackLab noch zu integrieren)

#### 11. Formular zurücksetzen
- [ ] Filter setzen, Query eingeben, Advanced-Mode aktivieren
- [ ] "Restablecer" Button klicken
- [ ] Alle Felder werden zurückgesetzt
- [ ] Filter-Chips verschwinden
- [ ] Advanced-Mode wird deaktiviert
- [ ] Query-Feld ist leer

---

### ✅ Sub-Tabs

#### 12. Tab-Switching
- [ ] Standard: "Resultados" Tab ist aktiv
- [ ] "Estadísticas" Tab klicken
- [ ] Tab wird aktiv (blaue Unterline)
- [ ] Platzhalter-Panel wird angezeigt
- [ ] Zurück zu "Resultados"

---

## Browser-Konsole prüfen

### Erwartete Logs (ohne Fehler)
```
✅ Search UI initialized
✅ [SearchFilters] Initialized filter field: pais
✅ [SearchFilters] Initialized filter field: hablante
...
✅ [PatternBuilder] Initialized
```

### Bei Formular-Submit
```
[SearchUI] Submitting search: {q: "casa", search_type: "forma", ...}
```

---

## Häufige Probleme

### CSS/JS lädt nicht
- **Problem:** Browser-Konsole zeigt 404 für CSS/JS
- **Lösung:** Flask muss laufen, Static-Files müssen vorhanden sein
- **Check:** `static/css/md3/components/search-ui.css` existiert?

### Filter-Dropdown öffnet sich nicht
- **Problem:** JavaScript-Fehler in Konsole
- **Lösung:** Module-Loading prüfen, `filters.js` geladen?

### CQL-Preview bleibt leer
- **Problem:** Pattern-Builder nicht initialisiert
- **Lösung:** Advanced-Mode aktivieren, Token-Werte eingeben

### Chips erscheinen nicht
- **Problem:** Filter-Synchronisation fehlgeschlagen
- **Lösung:** Browser neu laden, JavaScript-Fehler checken

---

## Responsive-Test (optional)

1. **Browser-Developer-Tools öffnen** (F12)
2. **Responsive-Modus aktivieren** (Ctrl+Shift+M)
3. **Verschiedene Auflösungen testen:**
   - Desktop (1920x1080)
   - Tablet (768x1024)
   - Mobile (375x667)
4. **Prüfen:**
   - [ ] Filter-Grid passt sich an (5→3→2→1 Spalten)
   - [ ] Token-Rows werden gestapelt
   - [ ] Buttons bleiben erreichbar
   - [ ] Keine horizontalen Scrollbalken

---

## Accessibility-Test (optional)

### Keyboard-Navigation
- [ ] Tab-Taste: Durch alle interaktiven Elemente navigieren
- [ ] Enter/Space: Dropdowns öffnen, Buttons aktivieren
- [ ] Escape: Dropdowns schließen (TODO: noch zu implementieren)
- [ ] Focus-Indicator ist immer sichtbar

### Screen-Reader (optional)
- [ ] Labels sind mit Inputs verbunden
- [ ] ARIA-Attribute korrekt gesetzt
- [ ] Live-Regionen für dynamische Inhalte

---

## Ergebnis dokumentieren

Nach dem Test:
1. **Screenshots** von wichtigen UI-States machen
2. **Gefundene Bugs** notieren
3. **Verbesserungsvorschläge** sammeln
4. **Performance-Eindruck** festhalten

---

**Viel Erfolg beim Testen! 🚀**
