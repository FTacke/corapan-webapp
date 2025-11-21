# JavaScript Refactor Documentation

## Ziel des JS-Refactors
- Inline-JS und Inline-Event-Handler konsequent entfernen.
- JavaScript klar modularisieren (`static/js/modules/...`).
- Glue-Code aus Templates in saubere Module verlagern.
- Funktionalität und Optik der App unverändert lassen.

## Überblick über aktuelle JS-Struktur (Bestandsaufnahme)

### Existierende JS-Dateien
- `static/js/app.js`
- `static/js/auth-setup.js`
- `static/js/drawer-logo.js`
- `static/js/main.js`
- `static/js/morph_formatter.js`
- `static/js/nav_proyecto.js`
- `static/js/player-token-marker.js`
- `static/js/player_script.js`
- `static/js/test-transcript-fetch.js`
- `static/js/theme-toggle.js`
- `static/js/theme.js`
- `static/js/turbo.esm.js`
- `static/js/modules/` (Verzeichnis mit Untermodulen)
  - `admin/`
  - `advanced/`
  - `atlas/`
  - `auth/`
  - `navigation/`
  - `player/`
  - `search/`
  - `stats/`

### Inline-Skripte und Events in Templates

#### `templates/search/advanced.html`
- **Tab Switching Script**: Importiert `initTabs` und registriert EventListener.
- **Stats Tab Initialization**: Importiert `initStatsTabAdvanced` und `cleanupStats`, registriert EventListener.
- **Regional checkbox toggle logic**: Importiert `initRegionalToggle` und registriert EventListener.

#### `templates/base.html`
- **CSRF Token Hook**: Injiziert CSRF-Token in HTMX-Requests.
- **401 Handler**: Öffnet Login-Sheet bei 401-Fehlern.
- **Page Router**: Initialisiert seitenspezifische Module basierend auf `data-page`.
- **Preload Guard**: Entfernt `preload`-Klasse nach dem Laden.
- **Auto-trigger login sheet**: Öffnet Login-Sheet, wenn `?login=1` in URL.
- **Page Title & Scroll Logic**: Setzt Seitentitel und Scroll-Status.

## Geplante Zielstruktur (Module, Entry-Points)

### Module
- `static/js/modules/core/`: Globale Funktionalität (CSRF, Auth, Router, UI).
- `static/js/modules/search/`: Suchlogik (Advanced Search, Token Search).
- `static/js/modules/stats/`: Statistik-Visualisierung.
- `static/js/modules/player/`: Audio-Player und Transkript-Sync.
- `static/js/modules/auth/`: Authentifizierung.

### Entry-Points
- `static/js/modules/search/advanced_entry.js`: Für `advanced.html`.
- `static/js/modules/core/entry.js`: Für `base.html` (global).

## Liste der erledigten Refactors

### Templates
- **`templates/search/advanced.html`**: Inline-Skripte (Tabs, Stats, Regional Toggle) in `static/js/modules/search/advanced_entry.js` ausgelagert.
- **`templates/base.html`**: 
  - CSRF, Auth, Router, UI-Logik in `static/js/modules/core/` ausgelagert.
  - `window.__CORAPAN__` Config in `data-config` Attribut am Body verschoben.
  - Zentraler Entry-Point `static/js/modules/core/entry.js` erstellt.
- **`templates/pages/player.html`**: 
  - Config in `data-*` Attribute verschoben.
  - Inline-Import in `static/js/modules/player/entry.js` ausgelagert.
- **`templates/pages/proyecto_estadisticas.html`**: Zoom-Logik in `static/js/modules/stats/zoom.js` ausgelagert.
- **`templates/pages/editor.html`**: Editor-Init in `static/js/modules/editor/entry.js` ausgelagert.
- **`templates/pages/editor_overview.html`**: Tab-Logik in `static/js/modules/editor/overview.js` ausgelagert.
- **`templates/partials/_navigation_drawer.html`**: Inline-Script entfernt, Logik in `static/js/modules/core/ui.js` (via `entry.js`) integriert.

### Neue Module
- `static/js/modules/core/entry.js`: Globaler Entry-Point.
- `static/js/modules/core/csrf.js`: CSRF-Schutz.
- `static/js/modules/core/auth_handler.js`: Auth-Logik.
- `static/js/modules/core/router.js`: Page Router.
- `static/js/modules/core/ui.js`: UI-Utilities (Preload, Title, Scroll, Drawer).
- `static/js/modules/core/config.js`: Global Config Reader.
- `static/js/modules/search/advanced_entry.js`: Advanced Search Entry-Point.
- `static/js/modules/player/entry.js`: Player Entry-Point.
- `static/js/modules/stats/zoom.js`: Stats Page Logic.
- `static/js/modules/editor/entry.js`: Editor Entry-Point.
- `static/js/modules/editor/overview.js`: Editor Overview Logic.

## Offene Punkte
- `static/js/main.js` ist noch ein monolithisches Legacy-Skript, das in `core/entry.js` importiert wird. Es sollte langfristig weiter zerlegt werden.
- Manuelle Regressionstests durchführen.

