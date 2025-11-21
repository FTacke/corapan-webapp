# UI, MD3 & Template Audit Report

**Datum:** 21.11.2025
**Status:** Audit Complete
**Fokus:** Design-System-Konsistenz, Frontend-Architektur, Template-Qualität

## 1. Ziel und Umfang des Audits

Dieser Bericht analysiert den aktuellen Stand der Frontend-Implementierung im Hinblick auf:
- **Konsistenz:** Einhaltung des Material Design 3 (MD3) Systems.
- **Wartbarkeit:** Trennung von Struktur (HTML), Design (CSS) und Logik (JS).
- **Modernisierung:** Identifikation von Legacy-Mustern (Inline-Styles, Hardcoded Colors, Inline-Event-Handler).

Es wurden keine funktionalen Änderungen vorgenommen. Ziel ist ein Maßnahmenplan für zukünftige Refactorings.

## 2. MD3/Theme-Setup (Status-Quo)

Das Projekt verfügt bereits über eine solide Basis für MD3:

- **Token-System:** Vorhanden in `static/css/md3/tokens.css`. Definiert `--md-sys-color-*` Variablen für Light/Dark Mode.
- **Struktur:** Der Ordner `static/css/md3/` enthält modulare CSS-Dateien (`typography.css`, `layout.css`, `components/`).
- **Nutzung:** Neue Komponenten (z.B. in der erweiterten Suche) nutzen diese Tokens bereits aktiv.

**Bewertung:** Das Fundament steht, die Durchdringung ist jedoch inkonsistent (Mischbetrieb mit Legacy-Styles).

## 3. Token-Konformitätsanalyse

### 3.1 Farb-Token-Konsistenz (Farbrollen-Analyse)

| MD3-Farbrolle | Status | Korrekte Nutzung (Beispiele) | Inkonsistente / Falsche Nutzung |
| :--- | :--- | :--- | :--- |
| **Primary** (`--md-sys-color-primary`) | ✅ Gut | Advanced Search Buttons, Active Tabs | `login.html` (nutzt `#667eea`, `#5568d3`) |
| **Surface** (`--md-sys-color-surface`) | ⚠️ Teils | `layout.css` (Body Background) | `base.html` (Fallback `#fff`), `login.html` (`#fee`) |
| **On-Surface** (`--md-sys-color-on-surface`) | ✅ Gut | Text in `typography.css` | `login.html` (`color: #1a1a1a`), `advanced.html` (Inline `color: var(...)`) |
| **Error** (`--md-sys-color-error`) | ❌ Schlecht | Kaum genutzt | `login.html` (`#f44336`, `#c62828` für Fehler) |
| **Outline** (`--md-sys-color-outline`) | ⚠️ Teils | Input Borders (Search) | `login.html` (`border: 1px solid #ddd`) |

**Befund:** `login.html` ist ein kompletter Ausreißer und ignoriert das Token-System vollständig.

### 3.2 Typografie-Token-Konsistenz

Das System definiert Klassen wie `.md3-display-*`, `.md3-headline-*`, `.md3-body-*` in `typography.css`.

| Bereich | Status | Problem |
| :--- | :--- | :--- |
| **Headings** | ✅ OK | Meist korrekt via CSS-Klassen gelöst. |
| **Icons** | ⚠️ Warnung | `index.html`: `style="font-size: 0.9rem;"` auf `material-symbols-rounded`. Sollte via Utility-Klasse gelöst werden. |
| **Body Text** | ⚠️ Warnung | `advanced.html`: `class="md3-body-medium"` oft kombiniert mit Inline-Styles für Margins. |

### 3.3 Spacing-Token-Konsistenz

MD3 nutzt ein 4px-Grid (0.25rem). `layout.css` bietet `.md3-space-*`.

| Template | Befund | Empfehlung |
| :--- | :--- | :--- |
| `advanced.html` | `style="margin-top: 1.5rem;"`, `style="margin: 0.5rem..."`, `style="padding: 1rem;"` | Ersetzen durch `.md3-space-6`, `.md3-space-2`, `.md3-space-4` oder Utility-Klassen (`mt-6`, `p-4`). |
| `login.html` | Unbekannte Spacing-Werte via CSS/Inline. | Komplettes Refactoring auf MD3-Grid. |
| `player.html` | Inline-Styles für Positionierung. | Flexbox/Grid-Klassen nutzen. |

## 4. Design-Drift – Vergleich gegen Soll-Architektur

### 4.1 MD3-Komponenten-Check

| Komponente | Status | Implementierung | Anmerkung |
| :--- | :--- | :--- | :--- |
| **Buttons** | ⚠️ Mixed | `.md3-button` (CSS) vs. Bootstrap-Reste | Alte `btn`-Klassen teilweise noch sichtbar. |
| **Cards** | ⚠️ Mixed | `.md3-card` (CSS) vs. `div style="..."` | Login-Sheet ist eine "Fake-Card". |
| **Navigation Drawer** | ✅ Gut | `_navigation_drawer.html` | Nutzt sauberes HTML/CSS. |
| **Top App Bar** | ✅ Gut | `_top_app_bar.html` | MD3-konform. |
| **Search Bar** | ✅ Gut | Advanced Search | Nutzt Tokens und MD3-Struktur. |
| **Dialogs/Modals** | ❌ Legacy | `_login_sheet.html` | Eigenbau-Overlay, kein natives `<dialog>` oder MD3-Modal. |

### 4.2 Theming-Durchdringung

- **Vollständig Tokenisiert:** `search/advanced.html` (bis auf Layout-Hacks), `partials/_navigation_drawer.html`.
- **Teilweise Tokenisiert:** `base.html`, `pages/index.html`.
- **Nicht Tokenisiert (Legacy):** `auth/login.html`, `auth/_login_sheet.html`.

## 5. JS-Audit

### 5.1 Liste aller Inline-Event-Handler

Diese Handler müssen in Event-Listener (`addEventListener`) in separaten JS-Dateien umgewandelt werden.

| Template | Event | Funktion / Code | Schweregrad |
| :--- | :--- | :--- | :--- |
| `pages/player.html` | `onmouseover` | `showTooltip(event)` | **MEDIUM** |
| `pages/player.html` | `onmouseout` | `hideTooltip(event)` | **MEDIUM** |
| `auth/_login_sheet.html` | `onclick` | `document.getElementById('login-sheet').remove()` | **HIGH** (Logik im HTML) |
| `search/advanced.html` | `onclick` | (Diverse Toggle-Logik via `aria-controls` ist ok, aber JS-Fallback prüfen) | **LOW** |

### 5.2 Liste aller Inline `<script>`-Blöcke

| Template | Art der Logik | Ziel-Modul (`static/js/modules/...`) |
| :--- | :--- | :--- |
| `search/advanced.html` | Glue-Code (Imports, Init) | `search/controller.js` oder `advanced/main.js` |
| `partials/_navigation_drawer.html` | UI-Interaktion (Drawer Toggle) | `layout/drawer.js` |
| `partials/audio-player.html` | Player-Steuerung & State | `player/audio-controller.js` |
| `pages/proyecto_estadisticas.html` | ECharts Init | `stats/charts-init.js` |

### 5.3 Glue-Code-Hotspots

- **`advanced.html`:** Enthält ~50 Zeilen Inline-JS (Module Imports und Initialisierung). Das Template fungiert als Controller.
  - *Lösung:* Ein einziges Entry-Point-Skript (`<script type="module" src=".../advanced-search.js">`) einbinden.
- **`audio-player.html`:** Vermischt HTML-Struktur mit Playback-Logik.
  - *Lösung:* Custom Element (`<audio-player>`) oder reines JS-Binding.

## 6. Komponenten-/Template-Struktur-Audit

### 6.1 Partial-Analyse

| Partial | Inhalt | Status |
| :--- | :--- | :--- |
| `_navigation_drawer.html` | Hauptmenü | ✅ Gut, wiederverwendbar. |
| `_top_app_bar.html` | Header | ✅ Gut. |
| `audio-player.html` | Globaler Player | ⚠️ Enthält Inline-JS. |
| `_login_sheet.html` | Login Overlay | ❌ Legacy-Struktur, Inline-Events. |

### 6.2 Komponenten-Potenzial (Jinja Macros)

Folgende UI-Elemente werden oft kopiert und sollten zentralisiert werden:

1.  **Icon-Button:** `<button class="md3-icon-button">...</button>`
2.  **Filter-Chip:** `<label class="md3-filter-chip">...</label>`
3.  **Data-Card:** Container für Statistiken/Ergebnisse.
4.  **Section-Header:** Einheitliche Überschriften mit Spacing.

### 6.3 Template-Tauglichkeits-Score

| Template | Score | Begründung |
| :--- | :--- | :--- |
| `search/advanced.html` | **B-** | Gute MD3-Basis, aber zu viel Inline-JS/CSS und zu monolithisch. |
| `auth/login.html` | **D** | Veraltet, Hardcoded Styles, nicht wartbar. |
| `pages/index.html` | **C+** | Solide, aber kleine Inkonsistenzen (Icons). |
| `base.html` | **B** | Gute Struktur, Meta-Tags ok, wenig Inline-Styles. |

## 7. SOLL-ARCHITEKTUR (Template-Frontend)

Für alle zukünftigen Refactorings gilt folgende Architektur als Zielbild:

1.  **Strict Separation:**
    - **HTML (Jinja2):** Nur Struktur und Daten-Binding. Keine `style="..."`, keine `on...="..."`.
    - **CSS:** Ausschließlich Klassen. Werte nur über Tokens (`var(--md-sys-color-...)`).
    - **JS:** Ausschließlich ES-Module in `static/js/`. Bindung an HTML nur über IDs/Klassen (`querySelector`).

2.  **Design System (MD3):**
    - **Farben:** 100% Abdeckung durch Tokens. Keine Hex-Codes im Code.
    - **Spacing:** Nutzung der MD3-Skala (4px Grid).
    - **Typografie:** Nutzung der globalen Klassen (`md3-body-large`, etc.).

3.  **Komponentisierung:**
    - Wiederkehrende UI-Patterns werden als **Jinja-Macros** (`templates/macros/ui.html`) definiert.
    - Große Blöcke werden in **Partials** ausgelagert.

4.  **Theming:**
    - Ein zentrales `theme.css` (oder `tokens.css`) steuert das gesamte Look & Feel.
    - Dark Mode Support ist implizit durch Token-Variablen gegeben.

## 8. Handlungsempfehlungen & Priorisierung

### Prio A: Kurzfristig / High Impact (Quick Wins)

1.  **Refactor `login.html`**
    - *Aufwand:* Medium
    - *Risiko:* Low
    - *Mehrwert:* 5/5 (Beseitigt größten Legacy-Schuldner, ermöglicht Dark Mode).
    - *Action:* Inline-Styles entfernen, MD3-Klassen anwenden, Tokens nutzen.

2.  **Inline-Events entfernen (`player.html`, `_login_sheet.html`)**
    - *Aufwand:* Low
    - *Risiko:* Low
    - *Mehrwert:* 4/5 (Saubere CSP-Compliance, bessere Wartbarkeit).
    - *Action:* Event-Listener in JS-Dateien auslagern.

### Prio B: Mittelfristig (Stabilisierung)

1.  **Glue-Code auslagern (`advanced.html`)**
    - *Aufwand:* Medium
    - *Risiko:* Medium (Funktionalität sicherstellen)
    - *Mehrwert:* 4/5 (Template wird lesbar, Logik testbar).
    - *Action:* `advanced-search-init.js` erstellen.

2.  **Hardcoded Colors eliminieren**
    - *Aufwand:* Medium (Suchen & Ersetzen)
    - *Risiko:* Low
    - *Mehrwert:* 3/5 (Konsistentes Design).

### Prio C: Langfristig (Architektur)

1.  **Komponenten-Bibliothek (Macros) einführen**
    - *Aufwand:* High
    - *Risiko:* Medium
    - *Mehrwert:* 5/5 (Langfristige Entwicklungsgeschwindigkeit).

2.  **Utility-Klassen für Spacing**
    - *Aufwand:* Low
    - *Risiko:* Low
    - *Mehrwert:* 3/5 (Ersetzt Inline-Margins).
