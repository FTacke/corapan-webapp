# template_master_plan.md

## Ziel
Die Webapp soll als **sauberes, wartbares, sofort adaptierbares Template** dienen.  
Alle zentralen Aspekte (Branding, Design-System, Layout, Config, Dev/Prod) müssen:
- eindeutig gesteuert sein (Single Source of Truth)
- konsistent angewendet werden
- ohne Seiteneffekte änderbar sein

---

## Leitprinzipien (nicht verhandelbar)

- **Single Source of Truth** für alles (Branding, Farben, Layout-Regeln)
- **Keine Hardcodings** (Farben, Abstände, Layouts, Texte)
- **Keine Seiten-Sonderlogik**, wenn es systemisch lösbar ist
- **Globale Shell steuert Layout**, nicht einzelne Seiten
- **Tokens → Semantik → Komponenten → Seiten**, niemals umgekehrt
- **Dev = Prod Verhalten identisch**
- **Neue Features dürfen System nicht umgehen**

Abbruchkriterium: Jede Lösung, die diese Regeln verletzt, wird verworfen.

---

## Locked Architecture Decisions (Phase 2)

### Branding Authority

- `app/src/app/branding.py` ist die einzige zulässige Quelle für template-seitige App-Identität.
- Dorthin gehören: App-Name, Title-Formatierung, Footer-Identität, Kontaktadresse, externe Projekt-Links und Shell-Asset-Dateinamen.
- Templates dürfen Branding-Werte nur aus dem bereitgestellten Context konsumieren.
- Neue Branding-Konstanten in Templates, CSS oder JS sind verboten.

### Token Authority

- Foundation Tokens leben ausschließlich in `app/static/css/md3/tokens.css`.
- App-semantische Tokens leben ausschließlich in `app/static/css/app-tokens.css`.
- `app/static/css/branding.css` ist als Legacy klassifiziert und nicht Teil der aktiven Pipeline.
- `app/static/css/md3/tokens-legacy-shim.css` ist deprecated, darf aber nur als Kompatibilitätsschicht bestehen bleiben, bis alle Live-Caller migriert sind.
- Neue JS-Farbpaletten sind verboten; JS muss CSS-Tokens lesen.

### Layout Authority

- `app/templates/base.html` ist die einzige Shell mit den Landmarken `header`, `aside`, `main` und `footer`.
- Seiten und Skeletons liefern nur Content-Struktur innerhalb des Content-Blocks.
- Verschachtelte `main`-Elemente unterhalb von `base.html` sind verboten.
- Neue `body[data-page]`- oder Shell-Fighting-Overrides sind nur zulässig, wenn die Shell nachweislich erweitert werden muss und der Eingriff dokumentiert wird.

### Page Title Contract

- Dokumenttitel werden über `format_page_title(...)` aus `app/src/app/branding.py` erzeugt.
- `block page_title` bleibt der einzige zulässige Titelblock.
- Neue Seiten dürfen den App-Namen nicht manuell an den Titel anhängen.

### Runtime Theme Contract

- `theme.js` synchronisiert `meta[name="theme-color"]` aus kanonischen CSS-Tokens.
- `base.html` darf keine festen Theme-Farben oder Light/Dark-Hex-Fallbacks mehr definieren.
- Chart-Themes und andere JS-Visualisierungen müssen ihr Farbsystem aus CSS-Variablen auflösen.

### Cleanup Boundary

- Phase 2 entfernt nur hochwirksame Parallelstrukturen und Landmark-Verstöße.
- Deprecated Layer bleiben markiert erhalten, wenn Live-Code noch von ihnen abhängt.
- Löschung von Legacy-Dateien erfolgt erst nach nachgewiesener Entkopplung.

---

## Current Status

- Phase 1: completed (`docs/template_status/2026-03-24_phase1_audit.md`)
- Phase 2: completed (`docs/template_status/2026-03-24_phase2_architecture.md`)
- Phase 3: substantially completed (`docs/template_status/2026-03-24_phase3_token_enforcement.md`)
- Phase 4: in progress

---

## Phase 4 Execution Focus

Diese Phase reduziert strukturelle Varianz, nicht die visuelle Identität.

Ziel dieser Phase:
- Page-Template-Harmonisierung über die wichtigsten Live-Seitenfamilien
- Reduktion seitenbezogener Shell- und Layout-Overrides
- Extraktion oder Standardisierung real genutzter Page-Family-Patterns
- fokussierte Eindämmung von `app/static/css/player-mobile.css`
- stärkere Autorität für wiederverwendbare Skeletons, Partials und Family-Wrapper
- Vorbereitung späterer Legacy-Bereinigung und finaler Template-Readiness-Bewertung

Phase-4-Regeln:
- `base.html` bleibt die einzige Shell-Autorität
- Laufzeitverhalten von Auth, Search, Landing und Player/Editor darf nicht brechen
- Landing-, Search-, Player- und Editor-Flows dürfen spezialisiert bleiben, wenn Produktverhalten das erfordert
- neue Abstraktionen sind nur erlaubt, wenn sie die Live-Struktur klarer und nicht abstrakter machen
- `player-mobile.css` ist ein kontrollierter Hotspot, kein Rewrite-Ziel

---

## Audit-Blöcke

### 1. Branding & App Identity
**Ziel:** Eine zentrale Stelle steuert alles.

Prüfen:
- App-Name (Tab, Header, Footer)
- Meta-Titel / SEO
- Logo / Favicons
- Footer-Text
- externe Links (GitHub, Kontakt etc.)

Soll:
- zentrale `branding/config` (eine Datei, kein Wildwuchs)

---

### 2. Design Token System
**Ziel:** Vollständig zentralisierte Steuerung aller visuellen Grundlagen.

Struktur:
- Foundation Tokens (z. B. Farben, Spacing, Radius)
- Semantic Tokens (background, surface, text, border)
- Component Tokens (card, button, nav, footer)

Prüfen:
- konkurrierende Farbdefinitionen
- direkte Hex-Werte im Code
- uneinheitliche Backgrounds (z. B. Footer vs Page)

Soll:
- Änderung einer Farbe wirkt global korrekt
- keine Tokens außerhalb des Systems

---

### 3. MD3-Komponentensystem
**Ziel:** Einheitliche, wiederverwendbare UI-Bausteine.

Prüfen:
- doppelte Komponenten
- abweichende Varianten pro Seite
- fehlende Standardisierung (Cards, Buttons, Inputs, Dialoge)

Soll:
- klar definierte Komponenten mit Varianten
- keine Copy-Paste-UI

---

### 4. Layout & App Shell
**Ziel:** Global gesteuertes Layout.

Prüfen:
- Header / Main / Footer Verhalten
- Footer-Position (kein Scroll-Zwang)
- Container-Breiten
- Spacing zwischen Sections
- responsive Verhalten

Soll:
- zentrale Layout-Shell
- Seiten enthalten nur Content, kein Layout-Hacking

---

### 5. Page Templates
**Ziel:** Standardisierte Seitentypen.

Templates definieren für:
- Landing
- Auth (Login etc.)
- Search
- Detail
- Static
- Error / Empty States

Prüfen:
- Sonderlösungen pro Seite
- inkonsistente Struktur

---

### 6. Hardcoding & CSS-Audit
**Ziel:** Eliminierung aller versteckten Inkonsistenzen.

Suchen nach:
- Inline-Styles
- `!important`
- direkten Farbwerten
- seitenlokalen CSS-Hacks

Soll:
- alles läuft über Tokens und Systemklassen

---

### 7. Theming & States
**Ziel:** Konsistente Zustände.

Prüfen:
- Hover / Focus / Disabled
- Form Errors / Success
- aktive Navigation
- Dark Mode (falls relevant)

---

### 8. Dev / Prod Parität
**Ziel:** Identisches Verhalten.

Prüfen:
- Pfade
- ENV-Handling
- Asset-Ladeverhalten
- API-Endpoints

Soll:
- keine prod-only Sonderlogik

---

### 9. Konfigurationsarchitektur
**Ziel:** Saubere Trennung.

Trennen:
- Branding
- Runtime Config
- Build/Deploy
- Feature Flags

Prüfen:
- verstreute Konstanten
- doppelte Definitionen

---

### 10. Wartbarkeit / Template-Fähigkeit
**Ziel:** Fremde können die App sofort anpassen.

Muss klar sein:
- Wo ändere ich Farben?
- Wo ändere ich Branding?
- Wie baue ich neue Seiten?
- Welche Regeln gelten?

---

### 11. Accessibility & UX
**Ziel:** Mindeststandard sicherstellen.

Prüfen:
- Kontraste
- Fokuszustände
- Semantik
- Mobile Nutzbarkeit

---

### 12. Repo & Doku-Struktur
**Ziel:** Nachhaltigkeit.

Ergebnis jedes Runs:
- `docs/template_status/YYYY-MM-DD.md`

Enthält:
- Ist-Zustand
- Probleme
- Maßnahmen
- Priorisierung
- betroffene Dateien

---

## Arbeitsphasen

### Phase 1 – Audit (Ist-Zustand)
- vollständige Analyse aller Blöcke
- Dokumentation unter `docs/template_status/`
- Status: abgeschlossen

### Phase 2 – Zielarchitektur festziehen
- finale Definition:
  - Branding-Zentrale
  - Token-System
  - Layout-Shell
  - Component-System
- Status: abgeschlossen

### Phase 3 – Token Enforcement & Hotspot Reduction
- Token-Durchsetzung in Live-CSS und Live-JS verstärken
- JS-Theme-Verbrauch an CSS-Token-Autorität ausrichten
- hartcodierte Farben und Inline-Visual-Styling in Hotspot-Dateien abbauen
- Override-Dichte in den riskantesten Seiten-Dateien reduzieren
- sichere Vorbereitung für spätere Entfernung des Legacy-Shims schaffen
- Status: weitgehend abgeschlossen

### Phase 3 – Foundations refactoren
- Tokens vereinheitlichen
- Branding zentralisieren
- Config bereinigen

### Phase 4 – Template-Harmonisierung & Override-Containment
- Seitenfamilien auf kanonische Family-Wrapper oder Skeletons ausrichten
- page-spezifische Shell- und Layout-Ausnahmen weiter reduzieren
- reusable Strukturen aus Skeletons und Partials real autoritativ machen
- Player-Mobile-Hotspot auf klare Ownership und schmalere Override-Fläche begrenzen
- verbleibende Ausnahmen für die finale Template-Readiness explizit dokumentieren
- Status: in Arbeit

### Phase 5 – Cleanup
- Hardcodings entfernen
- Altlasten löschen
- CSS bereinigen

### Phase 6 – Governance & Agent-Integration
- Regeln in `agents/skills.md` überführen
- verbindliche Standards definieren

---

## Phase 3 Execution Focus

Diese Phase ist kein Redesign und kein Beauty-Pass.

Ziel dieser Phase:
- konsequente Token-Enforcement in Live-Dateien
- weitere Angleichung von JS-Theme-Verhalten an CSS-Token-Autorität
- Reduktion von hartcodierten Farben, Inline-Visual-Styling und wiederholten Literalwerten
- Reduktion der Override-Dichte in bekannten Hotspot-Dateien
- gezielte Migration berührter Live-Caller weg von `--md3-*`, soweit sicher
- Vorbereitung einer späteren Legacy-Shim-Entfernung ohne Laufzeitbruch

Phase-3-Hotspots:
- `app/static/js/modules/stats/theme/corapanTheme.js`
- `app/static/js/modules/stats/renderBar.js`
- `app/static/js/modules/search/searchUI.js`
- `app/static/js/modules/advanced/formHandler.js`
- `app/static/css/md3/components/index.css`
- `app/static/css/player-mobile.css`
- `app/static/css/md3/components/player.css`
- `app/static/css/md3/components/editor.css`

Phase-3-Regel:
- reduziere die schädlichsten Abweichungen zuerst
- bevorzuge wiederverwendbare Reduktion statt großflächiger Umschreibung
- lasse riskante Legacy-Schichten markiert bestehen, wenn Live-Abhängigkeiten noch vorhanden sind

---

## Phase 4 Working Rules

- Page-CSS darf Shell-Verhalten nicht nachbauen, wenn ein wiederverwendbares Layout-Primitive dasselbe sicher leisten kann.
- Page-Familien sollen nur dann direkt `base.html` erweitern, wenn kein real geteilter Familienrahmen existiert oder die Seite bewusst eine Ausnahme bleibt.
- Skeletons und Partials sind nur dann kanonisch, wenn Live-Seiten tatsächlich über sie laufen.
- `player-mobile.css` darf nur kontrolliert konsolidiert werden: tote Selektoren, doppelte Literale und unnötige globale Reichweite abbauen, aber keine riskante Neuarchitektur erzwingen.

---

## Output je Run

Jeder Durchlauf erzeugt:

1. Statusbericht (`docs/template_status/...`)
2. konkrete Fix-Vorschläge
3. Liste verbotener Muster (für Agents)
4. Liste offener Baustellen

---

## Definition of Done

Die App ist template-ready, wenn:

- Branding an **einer Stelle** vollständig steuerbar ist
- Farbänderung global korrekt greift (inkl. Footer etc.)
- keine Hardcodings mehr existieren
- alle Seiten über Templates laufen
- Layout vollständig über Shell gesteuert wird
- Dev und Prod identisch funktionieren
- ein externer Entwickler ohne Kontext sofort arbeiten kann