# Background-Color Audit: Kategorisierte Issues

**Projekt:** corapan-webapp  
**Audit-Datum:** 14. Januar 2026  
**Zweck:** Systematische Kategorisierung aller gefundenen Probleme

## Issue-Kategorien

### 1. Doppelte Source of Truth ⚡ KRITISCH
### 2. Komponenten überschreiben globalen Background ohne Token
### 3. Inline-Styles (JS) ⚡ KRITISCH
### 4. !important Missbrauch ⚡ KRITISCH
### 5. Medienquery-Divergenz
### 6. Dark-Mode Divergenz ⚡ KRITISCH
### 7. Overlay/Opacity Artefakte
### 8. Interaktive Modi-Konflikte
### 9. Template-Vererbungsprobleme

---

## 1. Doppelte Source of Truth ⚡ KRITISCH

### 1.1 `--app-background` wird zweimal definiert

**Fundstellen:**
- `templates/base.html` (Zeile 14, 18)
- `static/css/app-tokens.css` (Zeile 25)

**Problem:**
```css
/* base.html (inline critical CSS) */
:root {
  --app-background: #ffffff; /* Light */
}
@media (prefers-color-scheme: dark) {
  :root {
    --app-background: #14141A; /* Dark */
  }
}

/* app-tokens.css (lädt später) */
:root {
  --app-background: var(--md-sys-color-surface-container); /* ÜBERSCHREIBT! */
}
```

**Auswirkung:**
- Critical CSS wird überschrieben
- FOUC-Risiko bei langsamem CSS-Load
- Inkonsistenz zwischen Initial-Render und Final-State
- App-Background ist `surface-container` statt `surface`

**Warum problematisch:**
- Critical CSS soll FOUC verhindern, wird aber sofort überschrieben
- Zwei verschiedene Definitionen können zu visuellen Sprüngen führen
- Wartbarkeit: Änderungen müssen an zwei Stellen erfolgen

**Empfehlung:**
```css
/* base.html - Nur Fallback-Werte für Critical CSS */
:root {
  --app-background: #c7d5d8; /* surface-container light approximation */
}
@media (prefers-color-scheme: dark) {
  :root {
    --app-background: #14141A; /* surface-container dark approximation */
  }
}

/* app-tokens.css - Kanonische Definition */
:root {
  --app-background: var(--md-sys-color-surface-container);
}
```

**Alternative:** Critical CSS nutzt direkt die finalen Token-Werte (erfordert Inline-Berechnung)

---

### 1.2 Footer setzt Background 3x redundant

**Fundstellen:**
- `static/css/md3/components/footer.css` (Zeile 11, 36, 43)

**Problem:**
```css
.md3-footer {
  background: var(--app-background); /* 1. Definition */
}

.md3-footer__navigation {
  background: var(--app-background); /* 2. Definition (redundant) */
}

@media (max-width: 599px) {
  .md3-footer__navigation {
    background: var(--app-background); /* 3. Definition (nochmal redundant) */
  }
}
```

**Warum problematisch:**
- Redundanz erhöht Wartungsaufwand
- Kaskade funktioniert normal → Child erbt Parent-Background
- CSS wird größer ohne Mehrwert

**Empfehlung:**
```css
/* Nur auf Root-Element setzen */
.md3-footer {
  background: var(--app-background);
}

/* Navigation erbt automatisch */
.md3-footer__navigation {
  /* background: ENTFERNEN */
}
```

---

### 1.3 NavDrawer doppelte Background-Definition

**Fundstellen:**
- `static/css/md3/components/navigation-drawer.css` (Zeile ~30, ~45)

**Problem:**
```css
.md3-navigation-drawer {
  background: var(--md-sys-color-surface);
}

.md3-navigation-drawer__container {
  background: var(--md-sys-color-surface); /* REDUNDANT */
}
```

**Empfehlung:**
- Nur auf `.md3-navigation-drawer` setzen, Container erbt

---

## 2. Komponenten überschreiben globalen Background ohne Token

### 2.1 `#main-content` setzt `transparent`

**Fundstelle:**
- `static/css/layout.css` (Zeile 152)

**Problem:**
```css
#main-content {
  background: transparent; /* Verhindert Background auf Seitenebene */
}
```

**Warum problematisch:**
- ID-Selector hat hohe Spezifität → schwer zu überschreiben
- Page-Container können keinen eigenen Background setzen (außer mit !important)
- Kommentar sagt "Prevent flash", aber das macht `body` schon

**Auswirkung:**
- `.md3-page` kann KEINEN Background setzen
- Alle Seiten haben transparent Main → Body-Background scheint durch
- Seiten können nicht individualisiert werden

**Empfehlung:**
```css
/* Option 1: Komplett entfernen */
#main-content {
  /* background: ENTFERNEN */
}

/* Option 2: Nur für FOUC-kritische Seiten */
body[data-hydrating] #main-content {
  background: transparent;
}
```

---

### 2.2 Corpus-Root setzt `--app-background` erneut

**Fundstelle:**
- `static/css/md3/components/corpus.css` (Zeile 17)

**Problem:**
```css
.md3-corpus-page {
  background: var(--app-background); /* Warum? Body hat das schon! */
}
```

**Warum problematisch:**
- Page-Container sollte KEINEN Background setzen (Philosophie: Layers)
- Redundant zu Body-Background
- Verhindert flexible Surface-Hierarchie

**Empfehlung:**
```css
.md3-corpus-page {
  /* background: ENTFERNEN */
}
```

---

## 3. Inline-Styles (JS) ⚡ KRITISCH

### 3.1 Snackbar mit harten Farben

**Fundstelle:**
- `static/js/modules/auth/snackbar.js` (Zeilen 120, 164, 178, 182, 186, 201, 205)

**Problem:**
```javascript
// Harte Farben statt Token
style="background-color: var(--md-sys-color-inverse-surface, #313033);"
style="background-color: rgba(208, 188, 255, 0.08);"
style="background-color: rgba(208, 188, 255, 0.12);"
style="background: none;"
style="background-color: rgba(244, 239, 244, 0.08);"
style="background-color: rgba(244, 239, 244, 0.12);"
```

**Warum problematisch:**
- Inline-Styles haben höchste Spezifität (nur !important schlägt sie)
- Harte Farben (`rgba(...)`) sind nicht theme-aware
- Schwer auditierbar und wartbar
- Keine automatische Dark-Mode-Anpassung
- Inkonsistent mit CSS-Definitionen

**Auswirkung:**
- Snackbar-Hover-States brechen im Dark Mode
- CSS-Overrides unmöglich
- Farben nicht zentral änderbar

**Empfehlung:**
```javascript
// Option 1: Klassen statt Inline-Styles
element.classList.add('md3-snackbar--inverse');

// Option 2: Token-Referenzen verwenden
style="background-color: var(--md-sys-color-inverse-surface);"

// Option 3: CSS Custom Properties im JS setzen
element.style.setProperty('--_snackbar-bg', 'var(--md-sys-color-inverse-surface)');
```

**CSS:**
```css
.md3-snackbar--inverse {
  background-color: var(--md-sys-color-inverse-surface);
}

.md3-snackbar--inverse:hover {
  background-color: color-mix(
    in srgb,
    var(--md-sys-color-inverse-surface) 90%,
    var(--md-sys-color-inverse-on-surface) 10%
  );
}
```

---

### 3.2 Stats-Chart Skeleton mit Inline-Style

**Fundstelle:**
- `static/js/modules/stats/initStatsTab.js` (Zeile 105)

**Problem:**
```javascript
'<div class="chart-skeleton" style="height: 360px; background: var(--md-sys-color-surface-container-low); border-radius: 8px; animation: pulse 1.5s ease-in-out infinite;"></div>';
```

**Warum problematisch:**
- Inline-Styles in String-Templates schwer wartbar
- Vermischt Struktur, Präsentation und Verhalten
- Animation sollte in CSS definiert sein

**Empfehlung:**
```javascript
'<div class="md3-chart-skeleton"></div>';
```

```css
.md3-chart-skeleton {
  height: 360px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: var(--radius-md);
  animation: md3-pulse 1.5s ease-in-out infinite;
}

@keyframes md3-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

---

### 3.3 Stats-Bar Legend mit dynamischen Farben

**Fundstelle:**
- `static/js/modules/stats/renderBar.js` (Zeile 174)

**Problem:**
```javascript
`<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${item.color};"></span>`
```

**Warum problematisch:**
- Inline-Styles (aber hier wahrscheinlich nötig für dynamische Farben)
- Zu viele Style-Properties inline

**Empfehlung:**
```javascript
`<span class="md3-legend-dot" style="background-color:${item.color};"></span>`
```

```css
.md3-legend-dot {
  display: inline-block;
  margin-right: var(--space-1);
  border-radius: 50%;
  width: 10px;
  height: 10px;
}
```

---

## 4. !important Missbrauch ⚡ KRITISCH

### 4.1 Player-Mobile mit 4+ !important

**Fundstelle:**
- `static/css/player-mobile.css` (Zeilen 206, 291, 292, 514)

**Problem:**
```css
.md3-player-mark-buttons button {
  background: transparent !important;
}

.md3-audio-player.mobile {
  background: var(--md-sys-color-surface-container) !important;
  background-color: var(--md-sys-color-surface-container) !important; /* DOPPELT! */
}

.md3-player-shortcuts-list .kbd {
  background: transparent !important;
}
```

**Warum problematisch:**
- !important verhindert normale CSS-Kaskade
- Doppelte Definition (`background` + `background-color`) ist redundant
- Macht Customization unmöglich
- Zeigt Spezifitäts-Probleme im Grunddesign

**Auswirkung:**
- Theme-Customization unmöglich
- Testing/Debugging erschwert
- Wartbarkeit reduziert

**Empfehlung:**
```css
/* Spezifität erhöhen statt !important */
.md3-player-mobile .md3-audio-player {
  background: var(--md-sys-color-surface-container);
}

/* Oder BEM-Modifier */
.md3-audio-player--mobile {
  background: var(--md-sys-color-surface-container);
}
```

---

### 4.2 DataTables mit 10+ !important

**Fundstelle:**
- `static/css/md3/components/datatables.css`
- `static/css/md3/components/datatables-theme-lock.css`

**Problem:**
```css
.dataTable thead {
  background: var(--md-sys-color-surface-container-high) !important;
}

.dataTable tbody tr:nth-child(even) {
  background: var(--md-sys-color-surface-container-low) !important;
}

/* ... 10+ weitere !important */
```

**Warum problematisch:**
- DataTables-Library überschreibt alles → !important als "Notlösung"
- Zwei separate Dateien (datatables.css + datatables-theme-lock.css) mit Überschneidungen
- Customization unmöglich

**Empfehlung:**
```css
/* Option 1: DataTables-CSS komplett überschreiben (nicht ergänzen) */
/* Option 2: DataTables mit Scoped-CSS isolieren */
/* Option 3: DataTables-API nutzen für Style-Customization */

/* Nur theme-lock.css behalten, datatables.css entfernen */
```

---

### 4.3 Button Disabled mit !important

**Fundstelle:**
- `static/css/md3/components/buttons.css` (Zeile 299)

**Problem:**
```css
.md3-button[disabled] {
  background: rgba(28, 27, 31, 0.12) !important;
}
```

**Warum problematisch:**
- !important + harte Farbe = doppeltes Problem
- Disabled sollte höchste Priorität haben, aber elegant

**Empfehlung:**
```css
/* Höhere Spezifität ohne !important */
.md3-button.md3-button--filled[disabled],
.md3-button.md3-button--tonal[disabled],
.md3-button.md3-button--outlined[disabled] {
  background: color-mix(in srgb, var(--md-sys-color-on-surface) 12%, transparent);
}

/* Oder Attribut-Selector verstärken */
.md3-button[disabled][disabled] {
  background: color-mix(...);
}
```

---

## 5. Medienquery-Divergenz

### 5.1 Top-App-Bar: Opak ↔ Transparent

**Fundstelle:**
- `static/css/md3/components/top-app-bar.css`

**Status:**
✅ **KEIN Problem** - Gewolltes responsives Verhalten

```css
/* Mobile: Opak */
.md3-top-app-bar {
  background: var(--md-sys-color-surface);
}

/* Desktop: Transparent */
@media (min-width: 840px) {
  .md3-top-app-bar {
    background: transparent;
  }
}
```

**Bewertung:** Korrekt nach MD3-Spec

---

### 5.2 Player Sidebar: Kein Background ↔ Background

**Fundstelle:**
- `static/css/player-mobile.css`

**Status:**
✅ **KEIN Problem** - Gewolltes responsives Verhalten

```css
/* Desktop: transparent/none */
.player-sidebar {
  background: none;
}

/* Mobile: opak */
@media (max-width: 599px) {
  .player-sidebar {
    background: var(--md-sys-color-surface-container-low);
  }
}
```

**Bewertung:** Mobile braucht opaken Background für Overlay-Modus

---

## 6. Dark-Mode Divergenz ⚡ KRITISCH

### 6.1 Audio-Player Glassmorphism ohne Dark-Mode

**Fundstelle:**
- `static/css/md3/components/audio-player.css` (Zeile 44, 352)

**Problem:**
```css
.audio-player-container {
  background: rgba(255, 255, 255, 0.95); /* ⚠️ NUR Light Mode! */
  backdrop-filter: blur(20px);
}

@media (max-width: 599px) {
  .audio-player-container {
    background: rgba(255, 255, 255, 0.95) !important; /* NOCHMAL! */
  }
}
```

**Warum problematisch:**
- Harte weiße Farbe funktioniert NICHT im Dark Mode
- Keine `@media (prefers-color-scheme: dark)` Definition
- Glassmorphism-Effekt bricht komplett im Dark Mode
- !important verhindert Overrides

**Auswirkung:**
- Dark Mode: Weißer Player auf dunklem Background = gebrochenes Design
- Nutzer-Erfahrung massiv beeinträchtigt
- Accessibility-Problem (Kontrast)

**Empfehlung:**
```css
.audio-player-container {
  /* Light Mode */
  background: color-mix(in srgb, var(--md-sys-color-surface) 95%, transparent);
  backdrop-filter: blur(20px);
}

@media (prefers-color-scheme: dark) {
  .audio-player-container {
    background: color-mix(in srgb, var(--md-sys-color-surface) 95%, transparent);
    /* Surface ist automatisch dunkel im Dark Mode */
  }
}

/* Alternative mit Opacity */
.audio-player-container {
  background: var(--md-sys-color-surface);
  opacity: 0.95;
  backdrop-filter: blur(20px);
}
```

---

### 6.2 Fallback-Werte mit Light-Mode-Farben

**Fundstellen:**
- `static/css/md3/components/advanced-search.css` (Zeilen 191, 199, 340, 413)
- `static/css/md3/components/alerts.css` (Zeilen 138, 158, 178)

**Problem:**
```css
.pattern-badge--surface {
  background-color: var(--md-sys-color-surface-variant, #f3edf7); /* ⚠️ Light Fallback */
}

.pattern-badge--primary {
  background-color: var(--md-sys-color-primary, #0a5981); /* ⚠️ Light Fallback */
}

.md3-alert--error {
  background-color: var(--md-sys-color-error-container, #fdecea); /* ⚠️ Light Fallback */
}
```

**Warum problematisch:**
- Fallbacks sind Light-Mode-Farben
- Dark Mode: Wenn Token fehlt, wird helle Farbe auf dunklem Background gezeigt
- Kontrast-Problem, Accessibility-Violation

**Empfehlung:**
```css
/* Option 1: Fallback entfernen (Token ist immer definiert) */
.pattern-badge--surface {
  background-color: var(--md-sys-color-surface-variant);
}

/* Option 2: Fallback mit color-scheme-aware Variablen */
@supports not (background: var(--md-sys-color-surface-variant)) {
  @media (prefers-color-scheme: light) {
    .pattern-badge--surface {
      background-color: #f3edf7;
    }
  }
  @media (prefers-color-scheme: dark) {
    .pattern-badge--surface {
      background-color: #3a3740; /* Dark-Mode Equivalent */
    }
  }
}
```

---

### 6.3 Hover-States mit falscher Dark-Mode-Richtung

**Fundstellen:**
- `static/css/md3/components/alerts.css` (Zeile 401)
- `static/css/md3/components/advanced-search.css` (Zeile 335)

**Problem:**
```css
.md3-alert__action-button:hover {
  background: rgba(0, 0, 0, 0.08); /* ⚠️ Verdunkeln im Light, aber auch im Dark! */
}

.search-tab-content:hover {
  background: rgba(0,0,0,0.04); /* ⚠️ Gleicher Fehler */
}
```

**Warum problematisch:**
- Light Mode: Schwarz darüber = Verdunkeln ✓
- Dark Mode: Schwarz darüber = NOCH MEHR Verdunkeln ✗ (sollte aufhellen!)
- Inkonsistente Interaktion

**Empfehlung:**
```css
.md3-alert__action-button:hover {
  background: color-mix(
    in srgb,
    var(--md-sys-color-on-surface) 8%,
    transparent
  );
  /* on-surface ist automatisch hell/dunkel je nach Mode */
}

/* Alternative mit prefers-color-scheme */
@media (prefers-color-scheme: light) {
  .md3-alert__action-button:hover {
    background: rgba(0, 0, 0, 0.08);
  }
}

@media (prefers-color-scheme: dark) {
  .md3-alert__action-button:hover {
    background: rgba(255, 255, 255, 0.08); /* Aufhellen statt Verdunkeln */
  }
}
```

---

## 7. Overlay/Opacity Artefakte

### 7.1 Search Overlay zu dunkel im Dark Mode

**Fundstelle:**
- `static/css/md3/components/advanced-search.css` (Zeile 521)

**Problem:**
```css
.search-overlay {
  background: rgba(0, 0, 0, 0.4); /* 40% schwarz */
}
```

**Warum problematisch:**
- Light Mode: 40% schwarz auf hell = gut sichtbar ✓
- Dark Mode: 40% schwarz auf dunkel = zu dunkel, kaum Unterschied ✗

**Empfehlung:**
```css
.search-overlay {
  background: color-mix(
    in srgb,
    var(--md-sys-color-on-surface) 40%,
    transparent
  );
}

/* Oder */
@media (prefers-color-scheme: light) {
  .search-overlay {
    background: rgba(0, 0, 0, 0.4);
  }
}

@media (prefers-color-scheme: dark) {
  .search-overlay {
    background: rgba(255, 255, 255, 0.15); /* Helleres Overlay */
  }
}
```

---

## 8. Interaktive Modi-Konflikte

### 8.1 Player Mobile vs. Desktop völlig unterschiedlich

**Fundstellen:**
- `static/css/md3/components/player.css`
- `static/css/player-mobile.css`

**Problem:**
- **Desktop:** Glassmorphism, transparente Sidebar, kein Card-Background
- **Mobile:** Opake Backgrounds, Surface-Container-Hierarchy, !important Overrides

**Warum problematisch:**
- Zwei völlig unterschiedliche Design-Systeme
- Mobile überschreibt mit !important statt natürlicher Kaskade
- Wartung erfordert beide Dateien zu pflegen
- Inkonsistente User-Experience

**Empfehlung:**
```css
/* Vereinheitlichen: Basis-Styles in player.css */
.md3-player-sidebar {
  /* Gemeinsame Styles */
}

/* Responsive Overrides ohne !important */
@media (max-width: 599px) {
  .md3-player-sidebar {
    background: var(--md-sys-color-surface-container-low);
  }
}

/* Glassmorphism nur Desktop */
@media (min-width: 840px) {
  .audio-player-container {
    background: color-mix(in srgb, var(--md-sys-color-surface) 95%, transparent);
    backdrop-filter: blur(20px);
  }
}
```

---

## 9. Template-Vererbungsprobleme

### 9.1 Auth-Card vs. Regular Card Inkonsistenz

**Fundstellen:**
- `static/css/md3/layout.css` (Zeile 76)
- `static/css/md3/components/cards.css` (Zeile 77)

**Problem:**
```css
/* Auth Card */
.md3-auth-card {
  --_auth-card-bg: var(--md-sys-color-surface);
  background: var(--_auth-card-bg);
}

/* Landing Card (Index) */
.md3-card--landing {
  --_card-bg: var(--md-sys-color-surface-container-high);
  background: var(--_card-bg);
}
```

**Warum problematisch:**
- Auth-Card: Surface (Level 0)
- Landing Card: Surface-Container-High (Level 4)
- **4 Stufen Unterschied!**
- Visuell: Auth-Card heller als alle anderen Cards
- Inkonsistente User-Experience

**Empfehlung:**
```css
/* Vereinheitlichen */
.md3-auth-card {
  --_auth-card-bg: var(--md-sys-color-surface-container-high);
  background: var(--_auth-card-bg);
}
```

---

### 9.2 Hero-Card auf gleichem Level wie Content-Cards

**Fundstellen:**
- `static/css/md3/layout.css` (Zeile 329)

**Problem:**
```css
/* Hero Card (Header) */
.md3-hero--card {
  background: var(--md-sys-color-surface);
}

/* Auth Card (Content) */
.md3-auth-card {
  background: var(--md-sys-color-surface);
}
```

**Warum problematisch:**
- Hero (Header) und Content-Card auf gleichem Surface-Level
- Keine visuelle Hierarchie zwischen Header und Content
- MD3-Spec: Header sollte niedriger/höher sein als Content

**Empfehlung:**
```css
/* Hero niedriger (Background-Level) */
.md3-hero--card {
  background: var(--md-sys-color-surface-container);
}

/* Auth Card höher (prominent) */
.md3-auth-card {
  background: var(--md-sys-color-surface-container-high);
}
```

---

## 10. Zusammenfassung nach Priorität

### ⚡ KRITISCH (Sofort beheben - Sprint 1)
1. **Doppelte `--app-background`-Definition** (base.html vs. app-tokens.css)
2. **Audio-Player Glassmorphism ohne Dark-Mode** (player.css)
3. **JS Inline-Styles in Snackbar** (snackbar.js)
4. **10+ !important in DataTables** (datatables.css)
5. **4+ !important in Player-Mobile** (player-mobile.css)
6. **Fallback-Werte mit Light-Mode-Farben** (advanced-search.css, alerts.css)

### 🔴 Hoch (Sprint 2)
7. **`#main-content` transparent verhindert Page-Background** (layout.css)
8. **Hover-States mit falscher Dark-Mode-Richtung** (alerts.css, etc.)
9. **Auth-Card vs. Landing-Card Inkonsistenz** (layout.css, cards.css)
10. **Player Mobile vs. Desktop Design-Divergenz** (player.css, player-mobile.css)

### 🟡 Mittel (Sprint 3)
11. **Footer Background 3x redundant** (footer.css)
12. **NavDrawer Background 2x redundant** (navigation-drawer.css)
13. **Corpus-Root setzt Background** (corpus.css)
14. **Button Disabled !important** (buttons.css)
15. **Search Overlay Dark-Mode** (advanced-search.css)

### 🟢 Niedrig (Backlog)
16. **Stats Skeleton Inline-Styles** (initStatsTab.js)
17. **Stats Legend Inline-Styles** (renderBar.js)
18. **DataTables Doppeldatei** (datatables.css + datatables-theme-lock.css)
19. **Hero-Card gleiches Level wie Content** (layout.css)

## 11. Impact-Matrix

| Issue | Auswirkung | Aufwand | Risiko |
|-------|------------|---------|--------|
| Doppelte `--app-background` | Hoch (FOUC) | Niedrig | Niedrig |
| Audio Glassmorphism Dark | Hoch (Broken UI) | Mittel | Niedrig |
| JS Inline-Styles | Mittel (Wartung) | Hoch | Mittel |
| DataTables !important | Mittel (Customization) | Hoch | Hoch |
| Player !important | Mittel | Niedrig | Niedrig |
| Fallback-Werte | Hoch (A11y) | Niedrig | Niedrig |
| #main-content transparent | Mittel (Flexibilität) | Niedrig | Mittel |
| Hover Dark-Mode | Mittel (UX) | Niedrig | Niedrig |
| Auth-Card Inkonsistenz | Niedrig (Ästhetik) | Niedrig | Niedrig |
| Player Design-Divergenz | Mittel (Wartung) | Hoch | Mittel |

**Nächster Schritt:** MD3-CSS-System Einheitlichkeit prüfen (Punkt 9 der Aufgabe)
