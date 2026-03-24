# Template Master Plan

## Goal

The repository should remain a clean, adaptable template with a single source of truth for branding, UI structure, runtime configuration, and operational workflows.

## Locked Decisions

- branding authority: `app/src/app/branding.py`
- shell authority: `app/templates/base.html`
- token authority: `app/static/css/md3/tokens.css` and `app/static/css/app-tokens.css`
- local development authority: root `scripts/dev-setup.ps1`, root `scripts/dev-start.ps1`, root `docker-compose.dev-postgres.yml`
- production authority: `app/infra/docker-compose.prod.yml`, `app/scripts/deploy_prod.sh`, `.github/workflows/deploy.yml`

## Non-Negotiable Rules

- no parallel branding, token, or runtime configuration systems
- no new page-local shell hacks when the shared shell can carry the behavior
- no new auth/core SQLite workflows
- no new undocumented canonical workflow changes

## Final Status

- template architecture is established
- the UI/template system has a stable authority model
- repository cleanup and canonicalization are now part of the final branch closeout

## Repo Hygiene and Canonicalization Pass

This pass covers:

- repository root hygiene
- dependency and config file consolidation
- documentation canonization
- removal of obsolete migration and process artifacts
- final agent-guidance efficiency review

This pass intentionally excludes `maintenance_pipelines/`.

The output of the pass is tracked in `docs/template_status/2026-03-24_repo_hygiene_canonicalization.md`.
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

### Phase 5 – Finalization & Readiness
- letzte sichtbare UI-Inkonsistenzen über Shared Patterns bereinigen
- Dialog-, Message-, Field- und Copy-Action-Patterns kanonisch ausrichten
- Atlas-Popup, mobile Player-Polish und sichere Legacy-Reduktion abschließen
- ehrliche finale Template-Readiness bewerten und dokumentieren

### Phase 6 – Governance & Agent-Integration
- Regeln in `agents/skills.md` überführen
- verbindliche Standards definieren

---

## Definition of Done

Der Branch ist erst dann sauber abschließbar, wenn alle folgenden Punkte erfüllt sind:

- Branding-Autorität bleibt ausschließlich in `app/src/app/branding.py`
- Dokumenttitel laufen ausschließlich über `format_page_title(...)`
- `app/templates/base.html` bleibt die einzige Shell-Autorität; Familienwrapper und Seiten erzeugen keine konkurrierende Shell
- aktive Token-Autorität bleibt auf `app/static/css/md3/tokens.css` und `app/static/css/app-tokens.css` begrenzt
- JS-Theme-Zugriff läuft über CSS-Custom-Properties und die gemeinsame Token-Lese-Pipeline
- Auth-, Text- und Admin-Familien nutzen ihre kanonischen Skeletons; bewusste Spezialfälle sind explizit klassifiziert
- Dialog-, Message-, Field- und Copy-Actions folgen Shared Patterns statt seitenlokaler Einzelregeln
- Atlas-Popup, Search-Dialoge und Auth-Dialoge lesen als konsistente Derivate derselben Komponentenfamilie
- `player-mobile.css`, Search-Runtime und Audio-/Editor-Hotspots bleiben als kontrollierte Ausnahmen dokumentiert
- verbleibende Legacy-Layer (`tokens-legacy-shim.css`, `branding.css`, einzelne `--md3-*` Caller) sind entweder sicher reduziert oder mit konkreten Blockern dokumentiert
- `.github/agents/skills.md` beschreibt die finale Runtime-Map, Regeln und Hotspots so konkret, dass ein Folge-Agent ohne Neu-Audit sicher weiterarbeiten kann
- `docs/template_status/` und `docs/changes/` enthalten eine ehrliche finale Readiness-Bewertung inklusive Stärken, Ausnahmen, Restschuld und Release-Empfehlung

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