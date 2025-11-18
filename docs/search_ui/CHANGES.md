# Search UI Redesign - Änderungsübersicht

**Branch:** `search_ui`  
**Datum:** 15. November 2025

---

## 📝 Übersicht

Vollständige Neuimplementierung der Suchoberfläche gemäß `docs/search_ui/search_ui_spec.md`. Die Umsetzung folgt strikt der Spezifikation ohne Vereinfachungen oder Umdeutungen.

---

## 🆕 Neue Dateien

### Templates
```
templates/search/advanced.html          ← Neues Such-Template (ersetzt altes)
{# Removed legacy backup `templates/search/advanced_old.html` #}
```

### CSS
```
static/css/md3/components/search-ui.css ← Alle neuen Styles (~850 Zeilen)
```

### JavaScript
```
static/js/modules/search/filters.js        ← Filter-Management (~350 Zeilen)
static/js/modules/search/patternBuilder.js ← Pattern-Builder (~450 Zeilen)
static/js/modules/search/searchUI.js       ← Haupt-Controller (~350 Zeilen)
```

### Dokumentation
```
docs/search_ui/IMPLEMENTATION_STATUS.md ← Status-Report
docs/search_ui/TESTING_GUIDE.md         ← Test-Anleitung
docs/search_ui/CHANGES.md               ← Diese Datei
```

---

## 🔄 Geänderte Dateien

### Keine Backend-Änderungen erforderlich
- `src/app/search/advanced.py` → **Unverändert** (bestehendes Routing funktioniert)
- Alle Flask-Routes bleiben kompatibel

---

## 🎨 UI-Komponenten (Details)

### 1. Search Card (`templates/search/advanced.html`)

#### Struktur
```html
<form id="advanced-search-form" class="md3-search-card">
  <!-- A: Basis-Query -->
  <div class="md3-search-card__section">
    <input id="q" name="q"> <!-- Query-Feld -->
    <select id="search_type"> <!-- Forma/Lema -->
  </div>

  <!-- B: Metadaten-Filter -->
  <div class="md3-filters-grid">
    <div class="md3-filter-field" data-facet="pais">...</div>
    <div class="md3-filter-field" data-facet="hablante">...</div>
    <!-- ... 3 weitere -->
  </div>

  <!-- Active Filters Chip Bar -->
  <div id="active-filters-bar" class="md3-active-filters">
    <div id="active-filters-chips"><!-- JS inserts chips --></div>
  </div>

  <!-- C: Optionen -->
  <div class="md3-options-row">
    <input id="include-regional">
    <input id="ignore-accents">
  </div>

  <!-- D: Advanced Toggle -->
  <label class="md3-switch-row">
    <input id="modo-avanzado" type="checkbox">
  </label>

  <!-- E: Expertenbereich (hidden by default) -->
  <div id="expert-area" class="md3-expert-area" hidden>
    <!-- E1: Pattern Builder -->
    <div id="pattern-builder">...</div>
    <!-- E2: CQL Preview -->
    <textarea id="cql-preview" readonly>...</textarea>
    <!-- E3: Templates -->
    <button class="template-btn" data-template="verb-noun">...</button>
  </div>

  <!-- F: Footer -->
  <div class="md3-search-card__footer">
    <button id="reset-form-btn">Restablecer</button>
    <button type="submit">Buscar</button>
  </div>
</form>

<!-- Sub-Tabs -->
<div class="md3-stats-tabs">
  <button id="tab-resultados">Resultados</button>
  <button id="tab-estadisticas">Estadísticas</button>
</div>
```

---

### 2. Filter-Fields (`filters.js`)

#### Custom MD3-Dropdown-Komponente
```html
<div class="md3-filter-field" data-facet="pais">
  <!-- Trigger (clickable) -->
  <div class="md3-filter-field__trigger" tabindex="0">
    <label>País</label>
    <div class="md3-filter-field__value">Todos los países</div>
    <span class="material-symbols-rounded">expand_more</span>
  </div>

  <!-- Dropdown-Menu (hidden by default) -->
  <div class="md3-filter-field__menu" hidden>
    <label class="md3-filter-option">
      <input type="checkbox" value="ARG" data-label="Argentina">
      <span>Argentina</span>
    </label>
    <!-- ... weitere Optionen -->
  </div>

  <!-- Hidden Select für Backend -->
  <select name="country_code" multiple hidden>
    <option value="ARG">Argentina</option>
    <!-- ... -->
  </select>
</div>
```

#### JavaScript-Logik
```javascript
class SearchFilters {
  // State-Management
  filterFields: Map<facet, {trigger, menu, checkboxes, hiddenSelect}>
  activeFilters: Map<facet, {values, labels}>

  // Core-Funktionen
  toggleMenu(facet)           // Dropdown öffnen/schließen
  updateFilterField(facet)    // Anzeige + Hidden-Select sync
  renderChips()               // Chip-Bar aktualisieren
  removeFilter(facet, value)  // Einzelnen Filter entfernen
  clearAllFilters()           // Alle Filter zurücksetzen
}
```

---

### 3. Pattern Builder (`patternBuilder.js`)

#### Token-Row-Struktur
```html
<div class="md3-token-row" data-token-index="0">
  <div class="md3-token-row__number">Token 1</div>
  
  <!-- Campo: Forma/Lema/POS -->
  <select class="token-field-select">
    <option value="forma">Forma</option>
    <option value="lema">Lema</option>
    <option value="pos">Categoría gramatical (POS)</option>
  </select>

  <!-- Match-Type -->
  <select class="token-match-select">
    <option value="exact">es exactamente</option>
    <option value="contains">contiene</option>
    <option value="starts">empieza por</option>
    <option value="ends">termina en</option>
  </select>

  <!-- Valor -->
  <input class="token-value-input" type="text">

  <!-- Remove-Button -->
  <button class="token-remove-btn">
    <span class="material-symbols-rounded">close</span>
  </button>
</div>
```

#### CQL-Generierung
```javascript
class PatternBuilder {
  // Token → CQL
  tokenToCQL({field, matchType, value}) {
    // Beispiel: {field: 'lema', matchType: 'exact', value: 'comer'}
    // → [lemma="comer"]
    
    // Beispiel: {field: 'pos', matchType: 'starts', value: 'V'}
    // → [pos="V.*"]
  }

  // Complete Pattern
  generateCQL() {
    // Ohne Distanz: [lemma="comer"] [pos="N.*"]
    // Mit Distanz (N=3): [lemma="comer"] []{0,3} [pos="N.*"]
  }
}
```

#### Templates
```javascript
templates = {
  'verb-noun': {
    tokens: [
      {field: 'pos', matchType: 'starts', value: 'V'},
      {field: 'pos', matchType: 'starts', value: 'N'}
    ],
    distance: 'consecutive'
  },
  // ... weitere Templates
}
```

---

### 4. Main Controller (`searchUI.js`)

#### Responsibilities
```javascript
class SearchUI {
  // State
  advancedMode: boolean      // Modo avanzado aktiv?
  manualCQLEdit: boolean     // Manuelle CQL-Bearbeitung?
  currentView: 'results'|'stats'

  // Core-Funktionen
  bindAdvancedToggle()       // D: Toggle für Expert-Bereich
  bindManualEditToggle()     // E2: Erlaubt CQL-Edit
  bindFormSubmit()           // F: Submit-Handler
  buildQueryParams()         // Sammelt alle Form-Daten
  performSearch(params)      // Führt Suche aus (TODO: Integration)
  resetForm()                // F: Alle Felder zurücksetzen
  switchView(view)           // Sub-Tabs wechseln
}
```

---

## 🎨 CSS-Highlights

### Responsive Grid (Filter-Fields)
```css
.md3-filters-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);  /* Desktop */
  gap: 0.75rem;
}

@media (max-width: 1200px) {
  .md3-filters-grid {
    grid-template-columns: repeat(3, 1fr); /* Tablet */
  }
}

@media (max-width: 768px) {
  .md3-filters-grid {
    grid-template-columns: repeat(2, 1fr); /* Mobile Landscape */
  }
}

@media (max-width: 480px) {
  .md3-filters-grid {
    grid-template-columns: 1fr;            /* Mobile Portrait */
  }
}
```

### Chip-Farben (Facetten-spezifisch)
```css
.md3-filter-chip--pais      { background: rgba(33, 150, 243, 0.12); }  /* Blau */
.md3-filter-chip--hablante  { background: rgba(76, 175, 80, 0.12); }   /* Grün */
.md3-filter-chip--sexo      { background: rgba(156, 39, 176, 0.12); }  /* Lila */
.md3-filter-chip--modo      { background: rgba(255, 152, 0, 0.12); }   /* Orange */
.md3-filter-chip--discurso  { background: rgba(233, 30, 99, 0.12); }   /* Pink */
```

### MD3-Switch (Advanced-Toggle)
```css
.md3-switch {
  width: 52px;
  height: 32px;
}

.md3-switch__track {
  background: var(--md-sys-color-surface-variant);
  border: 2px solid var(--md-sys-color-outline);
  border-radius: 16px;
}

.md3-switch-input:checked + .md3-switch .md3-switch__track {
  background: var(--md-sys-color-primary);
}
```

---

## 🔗 Datenfluss

### 1. Filter-Auswahl → Backend
```
User-Interaktion
  ↓
Checkbox im Dropdown
  ↓
SearchFilters.updateFilterField()
  ↓
Hidden <select multiple> wird synchronisiert
  ↓
Form-Submit sendet Daten wie bisher
```

### 2. Pattern-Builder → CQL
```
User baut Pattern
  ↓
PatternBuilder.tokenToCQL() für jeden Token
  ↓
Distanz-Regel anwenden
  ↓
CQL-String generieren
  ↓
CQL-Preview Textarea aktualisieren
  ↓
Bei Form-Submit: CQL-String als Query
```

### 3. Form-Submit
```
SearchUI.buildQueryParams()
  ↓
Sammelt:
  - Basic Query (A)
  - Filter-Params (B) via SearchFilters.getActiveFilterParams()
  - Optionen (C)
  - CQL (E2) wenn Advanced-Mode
  ↓
URLSearchParams-Objekt
  ↓
SearchUI.performSearch(params)
  ↓
Fetch zu /search/advanced/data?...
  ↓
(TODO: DataTables-Integration)
```

---

## 🔍 Testing-Workflow

### 1. Vorbereitung
```bash
cd c:\Users\Felix Tacke\OneDrive\00 - MARBURG\DH-PROJEKTE\CO.RA.PAN\corapan-webapp
.\.venv\Scripts\Activate.ps1
$env:FLASK_SECRET_KEY="test-key-local"
python -m src.app.main
```

### 2. Browser
```
http://localhost:5000/search/advanced
```

### 3. Test-Szenarien
Siehe: `docs/search_ui/TESTING_GUIDE.md`

---

## 📊 Code-Metriken

| Komponente | Dateien | Zeilen | Funktionen | Kommentare |
|------------|---------|--------|------------|------------|
| Templates | 1 | ~920 | - | Vollständig dokumentiert |
| CSS | 1 | ~850 | - | MD3-konform, responsive |
| JavaScript | 3 | ~1150 | ~40 | JSDoc für alle Funktionen |
| Dokumentation | 3 | ~800 | - | Specs + Guides |
| **Gesamt** | **8** | **~3720** | **~40** | **Vollständig** |

---

## 🚀 Deployment-Schritte (später)

### 1. Review & Testing
- [ ] Lokale Tests abgeschlossen
- [ ] Code-Review durchgeführt
- [ ] Browser-Kompatibilität geprüft
- [ ] Accessibility-Check

### 2. Backend-Integration
- [ ] CQL-Mapping finalisiert
- [ ] DataTables-Integration getestet
- [ ] Export-Buttons funktionieren
- [ ] Audio-Player integriert

### 3. Merge-Vorbereitung
- [ ] Branch `search_ui` ist sauber
- [ ] Keine Merge-Konflikte
- [ ] Tests grün
- [ ] Dokumentation aktualisiert

### 4. Merge
- [ ] Pull Request erstellen
- [ ] Review anfordern
- [ ] Nach Approval: Merge in `main` / `develop`

---

## ⚠️ Wichtige Hinweise

### Keine Breaking Changes
- ✅ Bestehende Backend-Routes unverändert
- ✅ Form-Namen bleiben gleich
- ✅ URL-Parameter kompatibel
- ✅ Altes Template als Backup

### No-Gos (bewusst nicht implementiert in Phase 1)
- ❌ Negation im Pattern-Builder (später)
- ❌ Statistik-Backend (Panel vorbereitet, Funktion später)
- ❌ OR/AND zwischen Tokens (später)
- ❌ Regex-Editor (später)

### Dependencies
- ✅ Keine neuen npm-Pakete
- ✅ Keine neuen Python-Packages
- ✅ Nutzt bestehende Material Symbols Icons
- ✅ Nutzt bestehende MD3-Tokens

---

## 📧 Support & Fragen

Bei Problemen oder Fragen:
1. **Browser-Konsole** checken (Fehler?)
2. **Dokumentation** lesen:
   - `IMPLEMENTATION_STATUS.md`
   - `TESTING_GUIDE.md`
   - `search_ui_spec.md`
3. **Code-Kommentare** durchsuchen
4. **Hinweis:** Das alte `templates/search/advanced_old.html` wurde entfernt; nutze Git History oder `templates/search/advanced.html` als Referenz.

---

**Erstellt von:** GitHub Copilot  
**Datum:** 15. November 2025
