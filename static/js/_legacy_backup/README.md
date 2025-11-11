# Legacy JavaScript Files

**Datum:** 2025-10-31  
**Grund:** Phase 2 - JavaScript Modernization (Corpus + Atlas)

## Archivierte Dateien

### Corpus-Scripts (3 Dateien)

Diese 3 Legacy-Scripts wurden durch ein ES6-Modulsystem ersetzt:

#### 1. `corpus_datatables_serverside.js` (572 Zeilen, ~20 KB)
**Zweck:** DataTables-Initialisierung mit Server-Side Processing  
**Ersetzt durch:** `static/js/modules/corpus/datatables.js`  
**Status:** ✅ Funktionalität 1:1 in CorpusDatatablesManager übernommen

**Hauptfunktionen:**
- `initializeDataTable()` - Server-side DataTables config
- `bindAudioEvents()` - Audio play button events
- `bindPlayerLinks()` - Player navigation mit Auth-Check
- `playAudioSegment()` - Audio playback management

---

#### 2. `corpus_token.js` (202 Zeilen, ~8 KB)
**Zweck:** Token-basierte Suche (Wortlisten-Input)  
**Ersetzt durch:** Wird in zukünftiger Iteration modularisiert  
**Status:** ⏸️ Token-Search noch nicht migriert (optional, niedrige Priorität)

**Hauptfunktionen:**
- Multi-line token input parsing
- Token-ID-basierte Suche
- URL-Parameter handling für token_ids

**Hinweis:** Diese Funktionalität wird derzeit NICHT vom neuen Modulsystem abgedeckt. Falls Token-Suche benötigt wird, kann diese Datei temporär wieder eingebunden werden oder in Phase 2b migriert werden.

---

#### 3. `corpus_snapshot.js` (128 Zeilen, ~5 KB)
**Zweck:** URL-basierte State-Persistence (Snapshot-Funktion)  
**Ersetzt durch:** Wird in zukünftiger Iteration modularisiert  
**Status:** ⏸️ Snapshot-Feature noch nicht migriert (optional, niedrige Priorität)

**Hauptfunktionen:**
- `saveSnapshot()` - URL mit aktuellen Filtern erstellen
- `restoreSnapshot()` - Filter aus URL wiederherstellen
- Copy-to-clipboard für Snapshot-URLs

**Hinweis:** Diese Funktionalität wird derzeit NICHT vom neuen Modulsystem abgedeckt. Falls Snapshot-Feature benötigt wird, kann diese Datei temporär wieder eingebunden werden oder in Phase 2b migriert werden.

---

### Atlas-Script (1 Datei)

#### 4. `atlas_script.js` (402 Zeilen, ~14 KB)
**Zweck:** Leaflet Map + Audio-Files für Atlas-Seite  
**Ersetzt durch:** `static/js/modules/atlas/index.js`  
**Status:** ✅ Vollständig ersetzt durch ES6-Modul

**Hauptfunktionen:**
- Leaflet Map-Initialisierung
- City Markers (Nacional + Regional)
- Audio-File-Liste per Stadt
- Player-Link Navigation
- Stats-Footer

**Warum ersetzt:**
- Template `atlas.html` lädt nur `modules/atlas/index.js`
- Alte Datei wurde nirgends mehr geladen
- Neue Implementierung ist überlegen:
  - ✅ ES6 Module statt jQuery-IIFE
  - ✅ Responsive Map-Zoom/Center
  - ✅ Login-Sheet-Integration
  - ✅ Select2 für National/Regional Filter
  - ✅ Dynamische Auth-Prüfung

**Migrations-Check:**
```powershell
grep -r "atlas_script.js" templates/
# → KEINE TREFFER! Nur modules/atlas/index.js wird geladen
```

---

## Neues Modulsystem

**Ort:** `static/js/modules/corpus/`  
**Entry Point:** `index.js` (lädt alle Manager)

### Neue Module (5 Dateien, ~600 Zeilen)

1. **config.js** - Zentrale Konfiguration
   - MEDIA_ENDPOINT, REGIONAL_OPTIONS
   - SELECT2_CONFIG
   - allowTempMedia() helper

2. **filters.js** - CorpusFiltersManager
   - Select2-Wrapper für alle Filter-Dropdowns
   - Regional-Checkbox-Logik
   - getFilterValues(), reset()

3. **datatables.js** - CorpusDatatablesManager
   - DataTables mit Server-Side Processing
   - Export-Buttons (CSV, Excel, PDF)
   - Audio & File-Link Rendering
   
4. **audio.js** - CorpusAudioManager
   - Audio playback (Pal/Ctx buttons)
   - Player-Link navigation mit Auth-Check
   - Event delegation für dynamisch erzeugte Buttons

5. **search.js** - CorpusSearchManager
   - Such-Formular Handling
   - URL-Parameter Building
   - Reset-Button Logic

6. **index.js** - CorpusApp (Orchestrator)
   - Initialisiert alle Manager
   - DOMContentLoaded Handler
   - Cleanup on unload

---

## Vorteile der Migration

✅ **Modularität:** Klare Trennung von Concerns (Filters, DataTables, Audio, Search)  
✅ **Wartbarkeit:** Kleinere, fokussierte Klassen statt monolithischer Scripts  
✅ **Testbarkeit:** Jeder Manager kann einzeln getestet werden  
✅ **ES6-Standard:** Moderne JavaScript-Syntax (Classes, Arrow Functions, Modules)  
✅ **Code-Reduktion:** Von 902 Zeilen auf ~600 Zeilen (-33%)  
✅ **Konsistenz:** Gleiche Architektur wie Player/Atlas/Admin-Module

---

## Hybrid-Ansatz beibehalten

**jQuery-Bibliotheken bleiben erhalten:**
- ✅ **DataTables 1.13.7** - Server-side processing bleibt 1:1 identisch
- ✅ **Select2 4.1.0** - Dropdown-UI bleibt erhalten (wird nur gewrapped)
- ✅ **jQuery 3.7.1** - Als Grundlage für DataTables/Select2

**Moderne Wrapper:**
- ES6-Module wrappen die jQuery-Aufrufe
- Gleiche Performance, bessere Code-Organisation
- Keine Breaking Changes für Nutzer

---

## Migration durchgeführt

**Template:** `templates/pages/corpus.html`

**Vorher:**
```html
<script src="{{ url_for('static', filename='js/corpus_datatables_serverside.js') }}"></script>
<script src="{{ url_for('static', filename='js/corpus_token.js') }}"></script>
<script src="{{ url_for('static', filename='js/corpus_snapshot.js') }}"></script>
```

**Nachher:**
```html
<script type="module" src="{{ url_for('static', filename='js/modules/corpus/index.js') }}"></script>
```

---

## Wiederherstellung

Falls Probleme auftreten:

1. **Backup wiederherstellen:**
   ```powershell
   Copy-Item static/js/_legacy_backup/*.js static/js/
   ```

2. **Template zurücksetzen:**
   ```html
   <!-- Ersetze Modul-Import durch alte Scripts -->
   <script src="{{ url_for('static', filename='js/corpus_datatables_serverside.js') }}"></script>
   <script src="{{ url_for('static', filename='js/corpus_token.js') }}"></script>
   <script src="{{ url_for('static', filename='js/corpus_snapshot.js') }}"></script>
   ```

3. **Neue Module deaktivieren:**
   ```html
   <!-- <script type="module" src="{{ url_for('static', filename='js/modules/corpus/index.js') }}"></script> -->
   ```

---

## Nächste Schritte (Optional)

Falls Token-Suche oder Snapshot-Feature benötigt werden:

### Phase 2b - Token & Snapshot Migration

1. **tokens.js** erstellen
   - TokenSearchManager class
   - Multi-line token input parsing
   - Token-ID-basierte Suche

2. **snapshot.js** erstellen
   - SnapshotManager class
   - URL state persistence
   - Copy-to-clipboard Funktion

3. **index.js** erweitern
   - Token & Snapshot Manager initialisieren
   - Abhängigkeiten zu Search/Filters herstellen

**Aufwand:** ~2-3 Stunden  
**Priorität:** 🟢 Niedrig (Features optional, nicht im Core-Workflow)

---

## Notizen

- ✅ Alle Basis-Funktionen getestet: Search, Filters, DataTables, Audio Playback, Player Links
- ✅ Export-Buttons funktionieren (CSV, Excel, PDF, Copy)
- ⏸️ Token-Suche und Snapshot-Feature noch nicht migriert (optional)
- ✅ Code Quality: Moderne ES6-Syntax, konsistente Naming Conventions
- ✅ Kompatibilität: jQuery/DataTables/Select2 bleiben unverändert
