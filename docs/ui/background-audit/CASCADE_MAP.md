# Background-Color Audit: Kaskaden-Hierarchie

**Projekt:** corapan-webapp  
**Audit-Datum:** 14. Januar 2026  
**Zweck:** Dokumentation der Background-Kaskade und Override-Hierarchie

## 1. Globale Kaskaden-Übersicht

### 1.1 Root-Level (Höchste Priorität)

```
html, body
  ├── Definiert in: base.html (inline critical CSS)
  ├── Wert: background: var(--app-background)
  ├── Token-Definition: --app-background: #ffffff (light) / #14141A (dark)
  ├── Spezifität: Element-Selector (niedrig)
  └── !important: Nein
```

**Überschreibungen:**
```
:root (base.html inline)
  ├── --app-background: #ffffff
  └── @media (prefers-color-scheme: dark)
        └── --app-background: #14141A

:root (app-tokens.css - lädt NACH base.html)
  └── --app-background: var(--md-sys-color-surface-container)  ⚠️ ÜBERSCHREIBT!
```

**KONFLIKT:** Die Token-Definition in `app-tokens.css` überschreibt die Critical-CSS-Definition in `base.html`!

### 1.2 Body-Level (App-Shell)

```
body.app-shell
  ├── Definiert in: layout.css (Zeile 17)
  ├── Wert: background: var(--app-background)
  ├── Spezifität: Klassen-Selector (mittel)
  └── !important: Nein
```

**Effektiver Wert:**
- Desktop: `var(--md-sys-color-surface-container)` (aus app-tokens.css)
- Mobile: `var(--md-sys-color-surface-container)` (aus app-tokens.css)
- Critical CSS Phase: `#ffffff` / `#14141A` (vor CSS-Load)

### 1.3 Main-Content-Level

```
#main-content
  ├── Definiert in: layout.css (Zeile 152)
  ├── Wert: background: transparent
  ├── Spezifität: ID-Selector (hoch)
  ├── !important: Nein
  └── Zweck: "Prevent color flash on first paint"
```

**Bewertung:**
- ⚠️ REDUNDANT: Wenn `body` bereits Background hat, ist `transparent` hier überflüssig
- ⚠️ RISIKO: Verhindert Background-Definitionen auf Seitenebene

## 2. Surface-Layer-Hierarchie (DOM-Pfad)

### 2.1 Typischer DOM-Pfad für Content-Seiten

```
html (background: --app-background)
  └── body.app-shell (background: --app-background)
      ├── #navigation-drawer (background: var(--md-sys-color-surface)) [AUSNAHME]
      ├── .md3-top-app-bar (background: surface | transparent) [RESPONSIVE]
      ├── #main-content (background: transparent)
      │   └── .md3-page (NO background, nur --_page-bg: surface)
      │       └── .md3-page__section (NO background)
      │           └── .md3-card (background: --_card-bg [surface-container-*])
      │               └── .md3-card__content (NO background)
      └── #site-footer (background: --app-background)
```

### 2.2 DOM-Pfad für Auth-Seiten

```
html (background: --app-background)
  └── body.app-shell (background: --app-background)
      ├── #main-content (background: transparent)
      │   └── .md3-page (NO background)
      │       └── .md3-auth-card (background: --_auth-card-bg [surface])
      │           └── .md3-auth-form (NO background)
      └── #site-footer (background: --app-background)
```

### 2.3 DOM-Pfad für Player

```
html (background: --app-background)
  └── body.app-shell (background: --app-background)
      ├── #main-content (background: transparent)
      │   └── #player-page-root.md3-player-page (NO background)
      │       └── .md3-player-container (NO background)
      │           ├── .md3-player-transcript (NO background)
      │           │   ├── .md3-player-header (NO background)
      │           │   ├── #transcriptionContainer (NO background)
      │           │   └── .audio-player-container (background: rgba(255,255,255,0.95) [GLASSMORPHISM])
      │           └── .player-sidebar (background: surface-container-low [MOBILE])
      │               └── .md3-player-card (background: surface-container-low)
      │                   └── .md3-player-card-header (background: surface-container-highest)
      └── #site-footer (background: --app-background)
```

**Player-Besonderheiten:**
- Mobile: Sidebar + Cards haben eigene Backgrounds
- Desktop: Transparency + Glassmorphism
- Audio-Player: Harte Farbe statt Token!

## 3. Spezifitäts-Tabelle (sortiert nach Priorität)

| Selector | Typ | Spezifität | Datei | !important | Effekt |
|----------|-----|------------|-------|------------|--------|
| `html, body` | Element | 0,0,1 | base.html | Nein | App-Background Root |
| `body.app-shell` | Klasse | 0,1,1 | layout.css | Nein | App-Background Body |
| `#main-content` | ID | 1,0,0 | layout.css | Nein | Transparent Override |
| `.md3-page` | Klasse | 0,1,0 | md3/layout.css | Nein | KEIN Background! |
| `.md3-auth-card` | Klasse | 0,1,0 | md3/layout.css | Nein | Surface (Auth) |
| `.md3-card--tonal` | Klasse | 0,1,0 | cards.css | Nein | Surface-Container |
| `.md3-card--outlined` | Klasse | 0,1,0 | cards.css | Nein | Surface-Container-Low |
| `.md3-card--elevated` | Klasse | 0,1,0 | cards.css | Nein | Surface-Container-Low |
| `.md3-card--landing` | Klasse | 0,1,0 | cards.css | Nein | Surface-Container-High |
| `.md3-navigation-drawer` | Klasse | 0,1,0 | navigation-drawer.css | Nein | Surface (Ausnahme) |
| `.md3-top-app-bar` | Klasse | 0,1,0 | top-app-bar.css | Nein | Surface / Transparent |
| `.md3-footer` | Klasse | 0,1,0 | footer.css | Nein | App-Background |
| `.md3-audio-player.mobile` | 2 Klassen | 0,2,0 | player-mobile.css | **JA!** | Surface-Container (⚠️) |
| `.dataTable thead` | Element+Klasse | 0,1,1 | datatables.css | **JA!** | Surface-Container-High |
| `button[disabled]` | Attribut+Element | 0,1,1 | buttons.css | **JA!** | rgba(28,27,31,0.12) |

## 4. Override-Analyse (wo überschreibt was?)

### 4.1 Globale Overrides

#### Problem 1: `--app-background` wird zweimal definiert
```
LADE-REIHENFOLGE:
1. base.html (inline) → --app-background: #ffffff
2. app-tokens.css → --app-background: var(--md-sys-color-surface-container) ✓ GEWINNT
```

**Auswirkung:**
- Critical CSS wird überschrieben
- App-Background ist **nicht** mehr `surface`, sondern `surface-container`
- Könnte zu FOUC führen bei langsamem CSS-Load

#### Problem 2: `#main-content` setzt `transparent`
```
body.app-shell (background: --app-background)
  └── #main-content (background: transparent) ← ÜBERSCHREIBT!
```

**Auswirkung:**
- `body`-Background scheint durch
- Page-Container können NICHT ihren eigenen Background setzen (außer mit höherer Spezifität)

### 4.2 Container-Level Overrides

#### Cards überschreiben Page-Background
```
.md3-page (KEIN background)
  └── .md3-card (background: surface-container-*) ✓ DEFINIERT Background
```

**Auswirkung:**
- Cards sind "Inseln" auf transparentem Page-Container
- Korrekt nach MD3-Philosophie

#### Auth-Cards vs. Regular Cards
```
.md3-auth-card (background: var(--md-sys-color-surface))
.md3-card--tonal (background: var(--md-sys-color-surface-container))
```

**Auswirkung:**
- Auth-Cards heller als Regular Cards
- Inkonsistenz? Oder gewollt?

### 4.3 Responsive Overrides

#### Top-App-Bar: Opak → Transparent
```
/* Default (Mobile) */
.md3-top-app-bar {
  background: var(--md-sys-color-surface);
}

/* Desktop */
@media (min-width: 840px) {
  .md3-top-app-bar {
    background: transparent; ← ÜBERSCHREIBT
  }
}
```

**Bewertung:** ✅ Korrekt und gewollt

#### Player Sidebar: Kein Background → Background
```
/* Desktop (implizit) */
.player-sidebar {
  background: none; /* oder transparent */
}

/* Mobile */
@media (max-width: 599px) {
  .player-sidebar {
    background: var(--md-sys-color-surface-container-low); ← ÜBERSCHREIBT
  }
}
```

**Bewertung:** ✅ Korrekt (Mobile braucht opaken Background)

### 4.4 JavaScript Overrides (KRITISCH!)

#### Snackbar setzt inline Backgrounds
```javascript
// snackbar.js setzt:
style="background-color: var(--md-sys-color-inverse-surface, #313033);"
style="background-color: rgba(208, 188, 255, 0.08);"
style="background-color: rgba(244, 239, 244, 0.08);"
```

**Auswirkung:**
- Inline-Styles haben HÖCHSTE Spezifität (nach !important)
- CSS-Overrides unmöglich ohne !important
- Schwer auditierbar und wartbar

## 5. Media-Query-Divergenzen

### 5.1 Compact (< 600px)

| Komponente | Background | Token |
|------------|------------|-------|
| Body | `--app-background` | `surface-container` |
| Top-App-Bar | `surface` | ✓ |
| NavDrawer | `surface` (modal) | ✓ |
| Footer | `--app-background` | `surface-container` |
| Main-Content | `transparent` | n/a |
| Player-Sidebar | `surface-container-low` | ✓ |
| Audio-Player | `rgba(255,255,255,0.95)` | ⚠️ HARTE FARBE |

### 5.2 Medium (600px - 839px)

| Komponente | Background | Token |
|------------|------------|-------|
| Body | `--app-background` | `surface-container` |
| Top-App-Bar | `surface` | ✓ |
| NavDrawer | `surface` (modal) | ✓ |
| Footer | `--app-background` | `surface-container` |
| Main-Content | `transparent` | n/a |

### 5.3 Expanded (≥ 840px)

| Komponente | Background | Token |
|------------|------------|-------|
| Body | `--app-background` | `surface-container` |
| Top-App-Bar | `transparent` | n/a |
| NavDrawer | `surface` (permanent) | ✓ |
| Footer | `--app-background` | `surface-container` |
| Main-Content | `transparent` | n/a |

**Konsistenz:** ✅ Weitgehend konsistent (außer harte Farben)

## 6. Dark-Mode-Divergenzen

### 6.1 Token-basierte Komponenten (Korrekt)

```css
/* Alle Token-basierten Komponenten passen sich automatisch an */
.md3-card--tonal {
  background: var(--md-sys-color-surface-container);
  /* Light: hellgrau, Dark: dunkelgrau */
}
```

**Bewertung:** ✅ Funktioniert korrekt

### 6.2 Harte Farben (PROBLEM!)

```css
/* Audio-Player Glassmorphism */
.audio-player-container {
  background: rgba(255, 255, 255, 0.95); /* ⚠️ NUR für Light Mode! */
}
```

**Bewertung:** ⚠️ KRITISCH: Keine Dark-Mode-Anpassung!

```javascript
// Snackbar
background-color: rgba(208, 188, 255, 0.08); /* ⚠️ Harte Farbe */
```

**Bewertung:** ⚠️ PROBLEM: Keine automatische Anpassung

### 6.3 Fallback-Werte

```css
.pattern-badge--surface {
  background-color: var(--md-sys-color-surface-variant, #f3edf7);
  /* ⚠️ Fallback ist Light-Mode-Farbe! */
}
```

**Bewertung:** ⚠️ Problem bei Dark Mode, wenn Token fehlt

## 7. Overlay/Opacity-Artefakte

### 7.1 Audio-Player Glassmorphism

```css
.audio-player-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
}
```

**Effekt:**
- 5% Transparenz lässt Background durchscheinen
- Bei dunklem Background: grauer statt weißer Player
- Dark Mode: Komplett falsch (weiß auf dunkel)

**Bewertung:** ⚠️ Artefakt bei dunklen Backgrounds

### 7.2 Search Overlay

```css
.search-overlay {
  background: rgba(0, 0, 0, 0.4);
}
```

**Effekt:**
- 40% schwarzes Overlay
- Dark Mode: Könnte zu dunkel sein (schwarz auf dunkelgrau)

**Bewertung:** ⚠️ Möglicherweise zu dunkel im Dark Mode

### 7.3 Alert Hover-States

```css
.md3-alert__action-button:hover {
  background: rgba(0, 0, 0, 0.08);
}
```

**Effekt:**
- Light Mode: 8% schwarz = subtile Verdunklung
- Dark Mode: Falsche Richtung (sollte aufhellen, nicht verdunkeln)

**Bewertung:** ⚠️ Falsche Hover-Richtung im Dark Mode

## 8. !important-Missbrauch

### 8.1 Player-Mobile

```css
.md3-audio-player.mobile {
  background: var(--md-sys-color-surface-container) !important;
  background-color: var(--md-sys-color-surface-container) !important; /* Doppelt! */
}

.md3-player-mark-buttons button {
  background: transparent !important;
}

.md3-player-shortcuts-list .kbd {
  background: transparent !important;
}
```

**Anzahl:** 4+ Instanzen in einer Datei!

**Bewertung:** ⚠️ Verhindert normale CSS-Kaskade

### 8.2 DataTables

```css
.dataTable thead {
  background: var(--md-sys-color-surface-container-high) !important;
}

.dataTable tbody tr:nth-child(even) {
  background: var(--md-sys-color-surface-container-low) !important;
}

/* ... 10+ weitere !important */
```

**Anzahl:** 10+ Instanzen!

**Bewertung:** ⚠️ KRITISCH: DataTables-Library überschreibt alles

### 8.3 Buttons Disabled

```css
.md3-button[disabled] {
  background: rgba(28, 27, 31, 0.12) !important;
}
```

**Bewertung:** ⚠️ !important + harte Farbe = doppeltes Problem

## 9. Zusammenfassung der Kaskaden-Probleme

### Kritisch (Sofort beheben)
1. **Doppelte `--app-background`-Definition** (base.html vs. app-tokens.css)
2. **`#main-content` transparent** verhindert Page-Background
3. **Audio-Player Glassmorphism** mit harter Farbe ohne Dark-Mode
4. **JS Inline-Styles** in snackbar.js mit harten Farben
5. **10+ !important in DataTables** verhindert Customization

### Hoch (Nächster Sprint)
6. Fallback-Werte mit harten Light-Mode-Farben
7. Overlay/Opacity mit falscher Dark-Mode-Richtung
8. Hover-States mit harten `rgba()` statt Token-basiert
9. Player-Mobile mit 4+ !important
10. Auth-Card vs. Regular Card Inkonsistenz

### Mittel (Backlog)
11. Redundante Background-Definitionen (Footer 3x)
12. Zu viele Surface-Level-Varianten
13. DataTables-Theme-Lock vs. DataTables (Duplizierung)

**Nächster Schritt:** PAGES.md mit seitenbasierten Stichproben
