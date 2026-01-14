# Background-Color Audit: Rohe Findings

**Projekt:** corapan-webapp  
**Audit-Datum:** 14. Januar 2026  
**Zweck:** Dokumentation aller gefundenen Background-Definitionen aus Grep-Suchen

## Zusammenfassung

- **200+ matches** für `background:` und `background-color:`
- **200+ matches** für `var(--*surface*)`
- **0 matches** für inline `style=".*background"` in Templates (gut!)

## 1. Kritische globale Background-Definitionen

### 1.1 base.html (Root-Level Definition)
```html
<!-- Zeile 14 -->
:root {
  --app-background: #ffffff;
}

<!-- Zeile 18 -->
@media (prefers-color-scheme: dark) {
  :root {
    --app-background: #14141A;
  }
}

<!-- Zeile 23 -->
html, body {
  background: var(--app-background);
}

<!-- Zeile 46 -->
body[data-hydrating] :focus-visible {
  background: transparent !important;
}
```

**Bewertung:** 
- ✅ Korrekt: Inline Critical CSS verhindert FOUC
- ⚠️ Problem: `--app-background` wird ZWEIMAL definiert (hier + in app-tokens.css)
- ⚠️ Problem: Harte Farbwerte statt Token-Referenzen

### 1.2 app-tokens.css (App-Level Token)
```css
/* Zeile 25 */
--app-background: var(--md-sys-color-surface-container);

/* Zeile 47 (Dark Mode) */
@media (prefers-color-scheme: dark) {
  :root {
    --app-color-login-bg: #14141A;
  }
}
```

**Bewertung:**
- ⚠️ KONFLIKT: Überschreibt die base.html Definition
- ✅ Korrekt: Nutzt MD3-Token als Referenz

### 1.3 layout.css (Body-Level)
```css
/* Zeile 17 */
body.app-shell {
  background: var(--app-background);
}

/* Zeile 87 - Turbo Loading Gradient */
body.turbo-loading::before {
  background: linear-gradient(...);
}

/* Zeile 152 */
#main-content {
  background: transparent; /* Prevent color flash */
}
```

**Bewertung:**
- ✅ Korrekt: Nutzt `--app-background`
- ⚠️ Problem: `#main-content` setzt explizit `transparent` → möglicherweise redundant

### 1.4 md3/layout.css (Container-Level)
```css
/* Zeile 38 */
.md3-page {
  --_page-bg: var(--md-sys-color-surface);
}

/* Zeile 76 */
.md3-auth-card {
  --_auth-card-bg: var(--md-sys-color-surface);
  background: var(--_auth-card-bg);
}

/* Zeile 329 */
.md3-hero--card {
  background: var(--md-sys-color-surface);
}

/* Zeile 359 */
.md3-section--card {
  background: var(--md-sys-color-surface-container);
}

/* Zeile 376 */
.md3-section--code {
  background-color: var(--md-sys-color-surface-container-low);
}

/* Zeile 400 */
.md3-divider--transparent {
  background-color: transparent;
}

/* Zeile 488 */
.md3-page__section--transparent {
  background: transparent;
}

/* Zeile 499 */
.md3-card--surface-high {
  background-color: var(--md-sys-color-surface-container-highest);
}
```

**Bewertung:**
- ⚠️ Problem: `.md3-page` definiert `--_page-bg` aber setzt KEINEN Background selbst
- ⚠️ Problem: Viele Container setzen eigenen Background → Kaskaden-Konflikt

## 2. Footer-Komponente

### 2.1 footer.css
```css
/* Zeile 11 */
.md3-footer {
  background: var(--app-background);
}

/* Zeile 36 */
.md3-footer__navigation {
  background: var(--app-background);
}

/* Zeile 43 (Mobile) */
@media (max-width: 599px) {
  .md3-footer__navigation {
    background: var(--app-background);
  }
}

/* Zeile 233 */
.md3-footer__link-badge {
  background: var(--md-sys-color-surface);
}
```

**Bewertung:**
- ✅ Korrekt: Nutzt `--app-background` konsequent
- ⚠️ Problem: Redundante Definitionen (3x `--app-background`)
- ⚠️ Problem: Badge nutzt `surface` statt `surface-container`

## 3. Navigation-Drawer (Erlaubte Ausnahme)

### 3.1 navigation-drawer.css
```css
/* Zeile ~30 */
.md3-navigation-drawer {
  background: var(--md-sys-color-surface);
}

/* Zeile ~45 */
.md3-navigation-drawer__container {
  background: var(--md-sys-color-surface);
}
```

**Bewertung:**
- ✅ Erlaubte Ausnahme: NavDrawer darf abweichen
- ✅ Korrekt: Nutzt MD3-Token `surface`
- ⚠️ Frage: Warum zweimal definiert (drawer + container)?

## 4. Top-App-Bar

### 4.1 top-app-bar.css
```css
/* Zeile ~30 (Default: Opak) */
.md3-top-app-bar {
  background: var(--md-sys-color-surface);
}

/* Zeile ~48 (Expanded: Transparent) */
@media (min-width: 840px) {
  .md3-top-app-bar {
    background: transparent;
  }
}
```

**Bewertung:**
- ✅ Korrekt: Responsive Verhalten (opak mobile, transparent desktop)
- ✅ Korrekt: Nutzt MD3-Token

## 5. Cards (Kritisch!)

### 5.1 cards.css
```css
/* Zeile 28-29 */
.md3-card--tonal {
  --_card-bg: var(--md-sys-color-surface-container);
  background: var(--_card-bg);
}

/* Zeile 41-42 */
.md3-card--outlined {
  --_card-bg: var(--md-sys-color-surface-container-low);
  background: var(--_card-bg);
}

/* Zeile 54-55 */
.md3-card--elevated {
  --_card-bg: var(--md-sys-color-surface-container-low);
  background: var(--_card-bg);
}

/* Zeile 77 */
.md3-card--landing {
  --_card-bg: var(--md-sys-color-surface-container-high);
  background: var(--_card-bg);
}

/* Zeile 101 */
.md3-card--transparent {
  background: transparent;
}

/* Zeile 129-197 (Surface-Level Utilities) */
.md3-surface--base { background: var(--md-sys-color-surface); }
.md3-surface--lowest { background: var(--md-sys-color-surface-container-lowest); }
.md3-surface--low { background: var(--md-sys-color-surface-container-low); }
.md3-surface--mid { background: var(--md-sys-color-surface-container); }
.md3-surface--high { background: var(--md-sys-color-surface-container-high); }
/* ... weitere Surface-Utilities */
```

**Bewertung:**
- ✅ Gut: Nutzt private Token (`--_card-bg`) für Inheritance
- ✅ Gut: Unterschiedliche Surface-Levels für verschiedene Card-Typen
- ⚠️ Problem: Viele Utility-Klassen → erhöht Komplexität

## 6. Player-Komponenten (Hoch-Komplex!)

### 6.1 player.css
- Keine direkten Background-Definitionen gefunden (nutzt andere Komponenten)

### 6.2 player-mobile.css (KRITISCH!)
```css
/* Zeile 99 */
.md3-player-sidebar {
  background: var(--md-sys-color-surface-container-low);
}

/* Zeile 153 */
.md3-player-card {
  background: var(--md-sys-color-surface-container-low);
}

/* Zeile 188 */
.md3-player-card-header {
  background: var(--md-sys-color-surface-container-highest);
}

/* Zeile 206 */
.md3-player-mark-buttons button {
  background: transparent !important;
}

/* Zeile 240 */
.md3-player-mark-buttons button.active {
  background: var(--md-sys-color-primary-container);
}

/* Zeile 291-292 (Mobile Audio Player) */
.md3-audio-player.mobile {
  background: var(--md-sys-color-surface-container) !important;
  background-color: var(--md-sys-color-surface-container) !important;
}

/* Zeile 514 */
.md3-player-shortcuts-list .kbd {
  background: transparent !important;
}
```

**Bewertung:**
- ⚠️ PROBLEM: Viele `!important` Overrides
- ⚠️ PROBLEM: Doppelte Definitionen (background + background-color)
- ⚠️ PROBLEM: Inkonsistente Surface-Levels

### 6.3 audio-player.css
```css
/* Zeile 44 */
.audio-player-container {
  background: rgba(255, 255, 255, 0.95);
}

/* Zeile 87 */
.audio-progress {
  background: var(--md-sys-color-surface-container-highest);
}

/* Zeile 95 */
.audio-progress__track {
  background: var(--md-sys-color-outline-variant);
}

/* Zeile 103 */
.audio-progress__fill {
  background: var(--md-sys-color-primary);
}

/* Zeile 352 (Mobile Glassmorphism) */
@media (max-width: 599px) {
  .audio-player-container {
    background: rgba(255, 255, 255, 0.95) !important;
  }
}
```

**Bewertung:**
- ⚠️ PROBLEM: Harte Farbe `rgba(255, 255, 255, 0.95)` statt Token
- ⚠️ PROBLEM: Keine Dark-Mode-Anpassung für Glassmorphism!
- ⚠️ PROBLEM: `!important` auf Mobile

## 7. Advanced Search

### 7.1 advanced-search.css
```css
/* Zeile 36 */
.advanced-search-container {
  background: var(--md-sys-color-surface-container);
}

/* Zeile 191 */
.pattern-badge--surface {
  background-color: var(--md-sys-color-surface-variant, #f3edf7);
}

/* Zeile 199 */
.pattern-badge--primary {
  background-color: var(--md-sys-color-primary, #0a5981);
}

/* Zeile 232 */
.query-preview {
  background-color: var(--md-sys-color-surface-container-low);
}

/* Zeile 331 */
.search-tab-content {
  background: transparent;
}

/* Zeile 335:hover */
.search-tab-content:hover {
  background: rgba(0,0,0,0.04);
}

/* Zeile 340 */
.search-results-card {
  background: var(--md-sys-color-surface-container-lowest, #ffffff);
}

/* Zeile 413 */
.search-modal {
  background-color: var(--md-sys-color-surface, #ffffff);
}

/* Zeile 521 */
.search-overlay {
  background: rgba(0, 0, 0, 0.4);
}

/* Zeile 539 */
.search-dialog {
  background: var(--md-sys-color-surface);
}
```

**Bewertung:**
- ⚠️ Problem: Fallback-Werte als harte Farben (z.B. `#f3edf7`, `#ffffff`)
- ⚠️ Problem: Hover mit hartem `rgba(0,0,0,0.04)` statt Token
- ✅ Gut: Konsequente Nutzung von Surface-Container-Hierarchy

## 8. Auth-Komponenten

### 8.1 auth.css
```css
/* Zeile 6 */
.md3-auth-form {
  --_auth-card-bg: var(--md-sys-color-surface-container-high);
}

/* Zeile 11 */
.md3-auth-card {
  background: var(--_auth-card-bg);
}

/* Zeile 73 */
.md3-auth-header {
  background: transparent;
}

/* Zeile 216 */
.md3-auth-error {
  background: var(--md-sys-color-error-container);
}

/* Zeile 339 */
.md3-auth-profile-card {
  background: var(--md-sys-color-surface);
}

/* Zeile 350 */
.md3-auth-profile-header {
  background: var(--md-sys-color-surface-container-high);
}

/* Zeile 366 */
.md3-auth-profile-section {
  background: var(--md-sys-color-surface-container-low);
}
```

**Bewertung:**
- ✅ Gut: Nutzt private Token für Inheritance
- ✅ Gut: Konsequente Surface-Container-Hierarchy
- ⚠️ Problem: Auth-Card hat anderen Background als reguläre Cards

### 8.2 login.css
- Keine direkten Background-Definitionen (nutzt auth.css)

## 9. DataTables

### 9.1 datatables.css + datatables-theme-lock.css
```css
/* Viele Definitionen für Table-Backgrounds */
.dataTables_wrapper { background: var(--md-sys-color-surface); }
.dataTable thead { background: var(--md-sys-color-surface-container-high) !important; }
.dataTable tbody tr:nth-child(even) { background: var(--md-sys-color-surface-container-low) !important; }
/* ... ca. 20+ weitere Background-Definitionen */
```

**Bewertung:**
- ⚠️ PROBLEM: Sehr viele `!important` Overrides
- ⚠️ PROBLEM: Zwei separate Dateien (datatables.css + datatables-theme-lock.css) mit Überschneidungen
- ✅ Gut: Nutzt MD3-Tokens konsequent

## 10. Alerts

### 10.1 alerts.css
```css
/* Zeile 34 */
.md3-alert {
  background-color: var(--md-sys-color-surface-container);
}

/* Zeile 138 */
.md3-alert--error {
  background-color: var(--md-sys-color-error-container, #fdecea);
}

/* Zeile 158 */
.md3-alert--warning {
  background-color: var(--md-sys-color-warning-container, #fff3e0);
}

/* Zeile 178 */
.md3-alert--info {
  background-color: var(--md-sys-color-primary-container, #e8f0fe);
}

/* Zeile 198 */
.md3-alert--success {
  background-color: color-mix(in srgb,
    var(--md-sys-color-surface) 70%,
    var(--md-sys-color-primary) 30%);
}

/* Zeile 388 */
.md3-alert__action-button {
  background: transparent;
}

/* Zeile 401:hover */
.md3-alert__action-button:hover {
  background: rgba(0, 0, 0, 0.08);
}
```

**Bewertung:**
- ⚠️ Problem: Fallback-Werte als harte Farben
- ⚠️ Problem: Hover mit hartem `rgba(0, 0, 0, 0.08)`
- ✅ Gut: Success nutzt `color-mix()` für konsistente Tints

## 11. Buttons

### 11.1 buttons.css
```css
/* Zeile 20 */
.md3-button--filled {
  background: var(--md-sys-color-primary);
}

/* Zeile 50:hover */
.md3-button--filled:hover {
  background-color: color-mix(/* ... */);
}

/* Zeile 102 */
.md3-button--tonal {
  background: var(--md-sys-color-primary-container);
}

/* Zeile 137 */
.md3-button--outlined {
  background: transparent;
}

/* Zeile 152:hover */
.md3-button--outlined:hover {
  background-color: color-mix(in srgb, var(--md-sys-color-primary) 8%, transparent);
}

/* Zeile 170 */
.md3-button--text {
  background: transparent;
}

/* Zeile 200 */
.md3-button--error {
  background: var(--md-sys-color-error);
}

/* Zeile 264 */
.md3-button--ghost {
  background: transparent;
}

/* Zeile 299 */
.md3-button[disabled] {
  background: rgba(28, 27, 31, 0.12) !important;
}
```

**Bewertung:**
- ✅ Gut: Nutzt MD3-Tokens + `color-mix()` für States
- ⚠️ Problem: Disabled hat harte Farbe `rgba(28, 27, 31, 0.12)`
- ⚠️ Problem: `!important` auf Disabled

## 12. JavaScript Inline-Styles (KRITISCH!)

### 12.1 modules/auth/snackbar.js
```javascript
/* Zeile 120 */
background-color: var(--md-sys-color-inverse-surface, #313033);

/* Zeile 164 */
background: none;

/* Zeile 178 */
background-color: rgba(208, 188, 255, 0.08);

/* Zeile 182 */
background-color: rgba(208, 188, 255, 0.12);

/* Zeile 201 */
background-color: rgba(244, 239, 244, 0.08);

/* Zeile 205 */
background-color: rgba(244, 239, 244, 0.12);
```

**Bewertung:**
- ⚠️ KRITISCH: Inline-Styles in JS schwer auditierbar
- ⚠️ KRITISCH: Harte Farben statt Token-Referenzen
- ⚠️ PROBLEM: Inkonsistent mit CSS-Definitionen

### 12.2 modules/stats/initStatsTab.js
```javascript
/* Zeile 105 */
'<div class="chart-skeleton" style="height: 360px; background: var(--md-sys-color-surface-container-low); border-radius: 8px; animation: pulse 1.5s ease-in-out infinite;"></div>';
```

**Bewertung:**
- ⚠️ Problem: Inline-Style in String-Template
- ✅ Gut: Nutzt Token-Referenz

### 12.3 modules/stats/renderBar.js
```javascript
/* Zeile 174 */
`<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${item.color};"></span>`
```

**Bewertung:**
- ⚠️ Problem: Inline-Style für Legende (aber wahrscheinlich dynamisch)

## 13. Weitere Komponenten (Kurzübersicht)

### Atlas
- `atlas.css`: Nutzt `surface-container`, `surface`, `primary-container` konsistent

### Corpus
- `corpus.css`: Definiert `background: var(--app-background)` auf Root-Container (⚠️ Konflikt?)
- `corpus-metadata.css`: Viele Surface-Container-Levels
- `corpus-search-form.css`: `surface-container`

### Como Citar
- `como-citar.css`: `surface-container-low`

### Editor
- `editor.css`: Keine direkten Background-Definitionen
- `editor-overview.css`: Keine direkten Background-Definitionen

### Chips
- `chips.css`: `surface-container-high`, `surface-container-highest`, `primary`

### Dialogs
- Keine direkten Findings in diesem Grep (müsste separat geprüft werden)

### Hero
- `hero.css`: Keine direkten Findings (nutzt wahrscheinlich md3/layout.css)

### Text Pages
- `text-pages.css`: Keine direkten Findings

### Index
- `index.css`: Keine direkten Findings

### Errors
- `errors.css`: Keine direkten Findings

## 14. Zusammenfassung der Probleme

### Hoch-Priorität (Sofort adressieren)
1. **Doppelte Definition von `--app-background`** (base.html vs. app-tokens.css)
2. **JS Inline-Styles mit harten Farben** (snackbar.js)
3. **Viele `!important` Overrides** (player-mobile.css, datatables.css)
4. **Harte Farben in Glassmorphism** (audio-player.css)
5. **Inkonsistente Surface-Levels** (zu viele Varianten)

### Mittel-Priorität
6. Fallback-Werte als harte Farben statt Token
7. Redundante Background-Definitionen (Footer 3x, etc.)
8. Hover-States mit harten `rgba()` statt `color-mix()`
9. Disabled-States mit harten Farben
10. Corpus-Root setzt `--app-background` erneut

### Niedrig-Priorität
11. Zu viele Surface-Utility-Klassen
12. Zwei DataTables-Dateien mit Überschneidungen
13. Transparent-Overrides möglicherweise redundant

**Nächster Schritt:** CASCADE_MAP.md mit Hierarchie-Analyse
