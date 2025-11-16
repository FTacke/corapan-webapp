# Search UI - Änderungen v1.1

**Datum:** 15. November 2025, 23:58 Uhr  
**Branch:** `search_ui`

---

## 🔄 Durchgeführte Verbesserungen

### 1. ✅ Stabile Filter-Field Breite

**Problem:** Wenn viele Werte ausgewählt wurden, wurde das Filter-Field zu breit und verschob das Layout.

**Lösung:**
- `max-width: 100%` für `.md3-filter-field__value`
- `overflow: hidden` für `.md3-filter-field__trigger`
- `text-overflow: ellipsis` zeigt "..." wenn Text zu lang ist
- `padding-right: 24px` für Icon-Platz

**Ergebnis:** Filter-Fields bleiben immer gleich breit, lange Werte werden mit "..." abgekürzt.

**Beispiel:**
```
Statt:  [España, México, Colombia, Argentina, Chile, ...]
Jetzt:  [ESP, MEX, COL, ARG, CHL, ...]  ← passt immer
```

---

### 2. ✅ Country Codes überall

**Problem:** Ländernamen wurden unterschiedlich angezeigt (teils "Argentina", teils "ARG").

**Lösung:**
- **Template:** Alle `data-label` und `<span>` zeigen jetzt nur Codes (ARG, BOL, CHL, etc.)
- **JavaScript:** Chip-Logik nutzt Codes konsistent
- **Chips:** Zeigen nur Code ohne "País:" Präfix

**Geänderte Dateien:**
- `templates/search/advanced.html` - Alle 20 Länder-Optionen
- `static/js/modules/search/filters.js` - Chip-Generierung

**Vorher:**
```html
<input ... value="ARG" data-label="Argentina">
<span>Argentina</span>
```

**Nachher:**
```html
<input ... value="ARG" data-label="ARG">
<span>ARG</span>
```

**Chip-Anzeige:**
- Vorher: `[ESP]` oder `[España]` (inkonsistent)
- Nachher: `[ESP]` `[MEX]` `[COL]` (immer Code)

---

### 3. ✅ Toggle-Design verbessert

**Problem:** Toggle-Switch war schwer zu erkennen und Position nicht optimal.

**Lösung:**
- `flex-shrink: 0` - Switch behält immer seine Größe
- Thumb-Position korrigiert: `top: 6px; left: 8px`
- Box-Shadow hinzugefügt für bessere Sichtbarkeit
- Checked-State: größerer Thumb (20px statt 16px)
- Bessere Translation: `translateX(16px)` statt 20px

**CSS-Änderungen:**
```css
.md3-switch__thumb {
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.md3-switch-input:checked + .md3-switch .md3-switch__thumb {
  width: 20px;
  height: 20px;
  transform: translateX(16px);
}
```

---

### 4. ✅ Button-Styles MD3-konform

**Problem:** Buttons waren klein, schwarz und passten nicht zum MD3-Design.

**Lösung:**
- Umfassende Button-Styles hinzugefügt
- Korrekte MD3-Farben (Primary, On-Primary, etc.)
- Richtige Größen: `min-height: 40px`, `padding: 10px 24px`
- Border-Radius: `20px` (MD3-Pill-Shape)
- Hover-States mit Farbwechsel
- Box-Shadows für Tiefe
- Icons korrekt sized: `18px`

**Button-Typen:**

#### Filled Button (Primary)
```css
background: var(--md-sys-color-primary, #6750a4);
color: var(--md-sys-color-on-primary, #fff);
```
- Buscar
- Template-Buttons beim Hover

#### Outlined Button
```css
background: transparent;
border: 1px solid var(--md-sys-color-outline);
color: var(--md-sys-color-primary);
```
- Restablecer
- Añadir palabra siguiente
- Template-Buttons (default)
- Eliminar

**Hover-States:**
- Filled: Leichter heller + mehr Shadow
- Outlined: Hintergrund + Primary Border

---

### 5. ✅ Checkboxes & Radio Buttons

- Checkboxes inside dropdown menus now use custom MD3-styled boxes rendered via CSS pseudo-elements; the native inputs remain accessible but visually hidden.
- Checkbox boxes and checkmark use MD3 color tokens and show keyboard focus outlines.
- Radio buttons in the Pattern-Builder now use an inner filled dot (MD3-consistent) rather than thick border width changes.
  - Focus and hover outlines added for accessibility.

### 6. ✅ Switch Default and Label Backgrounds

- The advanced-mode switch track uses a neutral surface-variant as its default "off" appearance; the thumb uses a neutral surface with an outline. This prevents the switch from visually popping when unchecked.
- The switch now includes `role="switch"` and `aria-checked` attributes so screen readers and assistive tech see the initial `off` state and subsequent state updates.
- Floating labels (`.md3-outlined-textfield__label` and `.md3-outlined-textfield__label--select`) inherit their container background so labels do not visually contrast with their fields (no visible seams on surfaces).


## 📊 Geänderte Dateien

| Datei | Änderungen | Zeilen |
|-------|------------|--------|
| `static/css/md3/components/search-ui.css` | Filter-Field Stabilität, Toggle-Design, Button-Styles | ~100 |
| `templates/search/advanced.html` | Alle Country-Labels zu Codes | ~80 |
| `static/js/modules/search/filters.js` | Chip-Text nur Codes für Länder | ~5 |

---

## 🎨 Visuelle Verbesserungen

### Vorher → Nachher

#### Filter-Fields
```
Vorher: [España, México, Colombia, Argent...]  ← überläuft
Nachher: [ESP, MEX, COL, ARG, CHL, PER...]     ← feste Breite
         ↑ mit "..." wenn zu lang
```

#### Chips
```
Vorher: [España ✕] [México ✕]
Nachher: [ESP ✕] [MEX ✕]
```

#### Toggle
```
Vorher: ○────   ← blass, klein
Nachher: ●────   ← Shadow, besser sichtbar
         ↑ größer bei aktiv
```

#### Buttons
```
Vorher: [Buscar] [Restablecer]  ← klein, schwarz
Nachher: [ Buscar ] [ Restablecer ]  ← MD3-Pill, farbig
         ↑ Icons + korrekte Größe
```

---

## 🧪 Testing

### Zu prüfen:

1. **Filter-Fields:**
   - [ ] Viele Länder auswählen → Field bleibt gleich breit
   - [ ] Text zeigt "..." wenn zu lang
   - [ ] Alle Länder zeigen nur Codes (ARG, nicht Argentina)

2. **Chips:**
   - [ ] Länder-Chips zeigen nur Code: `[ESP]` `[MEX]`
   - [ ] Andere Chips mit Präfix: `[Sexo: masculino]`

3. **Toggle:**
   - [ ] Aus: kleiner grauer Thumb mit Shadow
   - [ ] Ein: großer weißer Thumb, lila Track
   - [ ] Smooth Animation beim Wechsel

4. **Buttons:**
   - [ ] "Buscar": Lila Hintergrund, weiß Text
   - [ ] "Restablecer": Outline, lila Text
   - [ ] "Añadir palabra siguiente": Outline mit Icon
   - [ ] Hover: Farbwechsel sichtbar
   - [ ] Alle Buttons gleiche Höhe (40px)

---

## 💡 Technische Details

### Filter-Field Stabilität
```css
/* Verhindert Überlauf */
.md3-filter-field__trigger {
  position: relative;
  overflow: hidden;
  padding: 12px 40px 12px 16px; /* Platz für Icon */
}

.md3-filter-field__value {
  max-width: 100%;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  padding-right: 24px;
}
```

### Button Konsistenz
```css
/* Alle Buttons einheitlich */
.md3-button,
.md3-button--filled,
.md3-button--outlined {
  min-height: 40px;
  padding: 10px 24px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}
```

---

## ✅ Checkliste

- [x] Filter-Field Breite stabil
- [x] Ellipsis bei langen Werten
- [x] Country Codes überall konsistent
- [x] Chips zeigen nur Codes für Länder
- [x] Toggle-Design verbessert
- [x] Buttons MD3-konform gestylt
- [x] Hover-States für alle Buttons
- [x] Icons korrekte Größe
- [ ] Lokale Tests durchgeführt
- [ ] Browser-Check (Chrome/Firefox/Edge)

---

## 🚀 Deployment

**Status:** Ready for testing

**Nächster Schritt:** Lokale Tests durchführen

```bash
# Flask starten
.\.venv\Scripts\Activate.ps1
$env:FLASK_SECRET_KEY="test-key"
python -m src.app.main

# Browser: http://localhost:5000/search/advanced
```

---

**Geändert von:** GitHub Copilot  
**Datum:** 15. November 2025, 23:58 Uhr
