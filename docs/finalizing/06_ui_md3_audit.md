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

## 3. Inline-Styles & Layout-Anti-Patterns

Die Analyse der Templates zeigt signifikante Unterschiede in der Code-Qualität:

### Problemzonen (High Priority)
- **`templates/auth/login.html`:** Massive Nutzung von Inline-Styles für Layout und Farben.
  - *Beispiel:* `style="background: linear-gradient(...); color: #1a1a1a;"`
  - *Problem:* Ignoriert das zentrale Theme, schwer wartbar, kein Dark-Mode-Support.

### Mittlere Auffälligkeiten
- **`templates/search/advanced.html`:**
  - Viele `style="display: none;"` (akzeptabel für JS-Toggles, aber Utility-Klasse `hidden` wäre besser).
  - Layout-Korrekturen via `style="margin-top: 1.5rem;"` oder `style="overflow: visible;"`.
  - *Empfehlung:* Ersetzen durch MD3-Spacing-Klassen oder spezifische CSS-Regeln.

### Layout-Konsistenz
- Es fehlen teilweise Utility-Klassen für Spacing (Margins/Paddings). Oft wird Abstand durch Ad-hoc-Styles erzeugt.

## 4. Farb-Handling (Tokens vs. Hardcoded)

### Token-konforme Bereiche
- **Advanced Search UI:** Nutzt weitgehend `--md-sys-color-*` Variablen (z.B. `var(--md-sys-color-primary)`).
- **General Layout:** `layout.css` nutzt Tokens für Hintergründe und Textfarben.

### Hardcoded-Farben-Bereiche (Legacy)
| Datei / Bereich | Befund | Beispiel |
|-----------------|--------|----------|
| `templates/auth/login.html` | Hardcoded Hex-Werte überall | `#667eea`, `#f44336`, `#fee` |
| `templates/base.html` | Meta-Tags & Fallbacks | `#ffffff`, `#14141A` (in Meta-Tags ok, in CSS vermeiden) |
| `templates/pages/proyecto_como_citar.html` | Badge-Farben | In URL-Parametern (schwer zu vermeiden, aber dokumentierenswert) |

**Risiko:** Inkonsistentes Erscheinungsbild, insbesondere bei zukünftigen Theme-Anpassungen oder Dark-Mode-Optimierungen.

## 5. JS-Struktur (Inline vs. Module)

Das Projekt befindet sich im Übergang zu einer modernen ES-Module-Architektur.

### Positiv: Modulare Struktur
- `static/js/modules/` ist gut strukturiert (`search/`, `advanced/`, `stats/`).
- `templates/search/advanced.html` importiert diese Module sauber als `type="module"`.

### Negativ: Legacy & Inline-Logik
- **Inline-Event-Handler:**
  - `templates/pages/player.html`: `onmouseover="showTooltip(event)"`, `onmouseout="..."`. Veraltetes Pattern.
  - `templates/auth/_login_sheet.html`: `onclick="document.getElementById(...).remove()"`.
- **Inline-Skripte (Glue Code):**
  - `templates/search/advanced.html`: Enthält mehrere `<script type="module">` Blöcke, die Logik direkt im HTML definieren, statt sie nur zu importieren.
  - `templates/partials/_navigation_drawer.html`: Inline-Script für UI-Interaktion.
  - `templates/partials/audio-player.html`: Inline-Script für Player-Steuerung.

## 6. Template-Tauglichkeit & Wiederverwendbarkeit

- **Partials:** Gute Nutzung von `templates/partials/` (z.B. `_navigation_drawer.html`, `audio-player.html`).
- **Monolithen:** `templates/search/advanced.html` ist sehr groß und enthält Markup, Styles und JS-Glue-Code. Könnte weiter in Partials zerlegt werden (z.B. `_search_filters.html`, `_results_table.html`).
- **Komponenten:** Es fehlt eine klare Bibliothek an UI-Komponenten (Buttons, Cards, Inputs) als Jinja-Macros oder Includes. Oft wird HTML kopiert.

## 7. Handlungsempfehlungen & Priorisierung

### Prio A: Kurzfristig / High Impact (Quick Wins)
1.  **Refactor `login.html`:** Vollständige Entfernung der Inline-Styles. Ersetzen durch MD3-Klassen und Nutzung der Tokens aus `tokens.css`.
2.  **Inline-Events entfernen:** `onmouseover`/`onclick` in `player.html` und `_login_sheet.html` durch Event-Listener in separaten JS-Dateien ersetzen.

### Prio B: Mittelfristig (Stabilisierung)
1.  **Glue-Code auslagern:** Die Inline-Skripte in `advanced.html` und `audio-player.html` in dedizierte Controller-Skripte unter `static/js/modules/` verschieben.
2.  **Hardcoded Colors eliminieren:** Suche nach Hex-Codes in `static/css/` (außer `tokens.css`) und Ersetzung durch Variablen.

### Prio C: Langfristig (Architektur)
1.  **Komponenten-Bibliothek:** Erstellung von wiederverwendbaren Jinja-Macros für Standard-Elemente (Buttons, Inputs), um Konsistenz zu erzwingen.
2.  **Utility-Klassen:** Einführung eines kleinen Sets an Spacing-Utilities (z.B. basierend auf MD3-Spacing-Scale), um `style="margin: ..."` zu vermeiden.

## Fazit

Das Frontend ist funktional und auf einem guten Weg (MD3-Ansatz, ES-Modules). Die größte technische Schuld liegt in isolierten Legacy-Templates (`login.html`) und verstreutem Inline-JS. Eine gezielte Bereinigung dieser Bereiche wird die Wartbarkeit massiv erhöhen.
