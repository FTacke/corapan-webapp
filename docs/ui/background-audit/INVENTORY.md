# Background-Color Audit: Datei-Inventar

**Projekt:** corapan-webapp (https://corapan.hispanistica.com/)  
**Audit-Datum:** 14. Januar 2026  
**Zweck:** Vollständiges Inventar aller Dateien, die Hintergrundfarben definieren oder beeinflussen können

## 1. Template-Dateien (48 total)

### 1.1 Base Layout
- `templates/base.html` — **KRITISCH**: Hauptlayout, definiert `--app-background` inline und global `background`

### 1.2 Partials (Layout-Komponenten)
- `templates/partials/page_navigation.html` — Seitennavigation (Pagination)
- `templates/partials/status_banner.html` — Status-Banner
- `templates/partials/footer.html` — Footer-Komponente
- `templates/partials/audio-player.html` — Audio-Player-Komponente
- `templates/partials/_navigation_drawer.html` — **KRITISCH**: NavDrawer (Ausnahme erlaubt)
- `templates/partials/_top_app_bar.html` — **KRITISCH**: Top App Bar

### 1.3 MD3 Skeletons (Wiederverwendbare Layouts)
- `templates/_md3_skeletons/auth_login_skeleton.html` — Auth-Login Layout
- `templates/_md3_skeletons/auth_profile_skeleton.html` — Auth-Profil Layout
- `templates/_md3_skeletons/auth_dialog_skeleton.html` — Auth-Dialog Layout
- `templates/_md3_skeletons/page_form_skeleton.html` — Formular-Seiten Layout
- `templates/_md3_skeletons/page_admin_skeleton.html` — Admin-Seiten Layout
- `templates/_md3_skeletons/dialog_skeleton.html` — Dialog-Layout
- `templates/_md3_skeletons/page_text_skeleton.html` — Text-Seiten Layout
- `templates/_md3_skeletons/page_large_form_skeleton.html` — Große Formulare Layout
- `templates/_md3_skeletons/sheet_skeleton.html` — Sheet-Layout

### 1.4 Öffentliche Seiten
- `templates/pages/index.html` — **KRITISCH**: Startseite mit Landing-Cards
- `templates/pages/impressum.html` — Impressum (Text-Seite mit `.md3-page`)
- `templates/pages/privacy.html` — Datenschutz (Text-Seite)
- `templates/pages/player.html` — **KRITISCH**: Player-Interface (komplexes Layout)
- `templates/pages/player_overview.html` — Player-Übersicht
- `templates/pages/atlas.html` — Atlas-Seite (Karte)
- `templates/pages/editor.html` — Editor-Interface
- `templates/pages/editor_overview.html` — Editor-Übersicht
- `templates/pages/admin_dashboard.html` — Admin-Dashboard
- `templates/pages/corpus_metadata.html` — Corpus-Metadaten
- `templates/pages/corpus_guia.html` — Corpus-Guide
- `templates/pages/proyecto_overview.html` — Projekt-Übersicht
- `templates/pages/proyecto_quienes_somos.html` — Über uns
- `templates/pages/proyecto_referencias.html` — Referenzen
- `templates/pages/proyecto_diseno.html` — Design
- `templates/pages/proyecto_como_citar.html` — Zitierweise

### 1.5 Auth-Bereich
- `templates/auth/login.html` — **KRITISCH**: Login-Seite mit `.md3-auth-card`
- `templates/auth/password_forgot.html` — Passwort vergessen
- `templates/auth/password_reset.html` — Passwort zurücksetzen
- `templates/auth/account_profile.html` — Profil
- `templates/auth/account_password.html` — Passwort ändern
- `templates/auth/account_delete.html` — Account löschen
- `templates/auth/admin_users.html` — User-Verwaltung

### 1.6 Search-Bereich
- `templates/search/advanced.html` — Advanced Search Interface
- `templates/search/_results.html` — Search Results Partial
- `templates/search/partials/cql_guide_dialog.html` — CQL Guide Dialog
- `templates/search/partials/filters_block.html` — Filter-Block

### 1.7 Error Pages
- `templates/errors/400.html` — Bad Request
- `templates/errors/401.html` — Unauthorized
- `templates/errors/403.html` — Forbidden
- `templates/errors/404.html` — Not Found
- `templates/errors/500.html` — Internal Server Error

## 2. CSS-Dateien (55 total)

### 2.1 Globale/Core CSS (KRITISCH)
- `static/css/layout.css` — **KRITISCH**: Hauptlayout, definiert `body.app-shell`, Grid-Struktur
- `static/css/app-tokens.css` — **KRITISCH**: App-level Tokens, definiert `--app-background`
- `static/css/branding.css` — Brand-Farben (Gradient)
- `static/css/player-mobile.css` — **KRITISCH**: Player Mobile-Overrides (viele Background-Definitionen!)

### 2.2 MD3 Foundation (KRITISCH)
- `static/css/md3/tokens.css` — **KRITISCH**: Kern-Tokens, definiert `--md-sys-color-*` für Light/Dark Mode
- `static/css/md3/tokens-legacy-shim.css` — Legacy Token-Aliases
- `static/css/md3/typography.css` — Typografie
- `static/css/md3/layout.css` — **KRITISCH**: MD3 Layout-Klassen (`.md3-page`, `.md3-auth-card`, etc.)

### 2.3 MD3 Komponenten (nach Relevanz sortiert)

#### Hoch-Relevant (definieren Background)
- `static/css/md3/components/cards.css` — **KRITISCH**: Cards mit verschiedenen Surface-Levels
- `static/css/md3/components/navigation-drawer.css` — **KRITISCH**: NavDrawer (Ausnahme!)
- `static/css/md3/components/top-app-bar.css` — **KRITISCH**: Top App Bar (transparent/opak)
- `static/css/md3/components/footer.css` — **KRITISCH**: Footer (nutzt `--app-background`)
- `static/css/md3/components/dialog.css` — Dialoge
- `static/css/md3/components/alerts.css` — Alert-Komponenten
- `static/css/md3/components/auth.css` — Auth-Cards (definiert `--_auth-card-bg`)
- `static/css/md3/components/player.css` — Player-Interface
- `static/css/md3/components/audio-player.css` — Audio-Player (Glassmorphism!)
- `static/css/md3/components/advanced-search.css` — Advanced Search UI
- `static/css/md3/components/atlas.css` — Atlas-Karte
- `static/css/md3/components/admin-dashboard.css` — Admin-Dashboard
- `static/css/md3/components/corpus.css` — Corpus-Seiten
- `static/css/md3/components/corpus-metadata.css` — Corpus-Metadaten
- `static/css/md3/components/corpus-search-form.css` — Corpus-Suchformular
- `static/css/md3/components/datatables.css` — DataTables
- `static/css/md3/components/datatables-theme-lock.css` — DataTables Theme-Lock

#### Mittel-Relevant
- `static/css/md3/components/buttons.css` — Buttons (Background für States)
- `static/css/md3/components/chips.css` — Chips
- `static/css/md3/components/textfields.css` — Textfelder
- `static/css/md3/components/forms.css` — Formulare
- `static/css/md3/components/hero.css` — Hero-Komponenten
- `static/css/md3/components/text-pages.css` — Text-Seiten
- `static/css/md3/components/index.css` — Index-Seite
- `static/css/md3/components/login.css` — Login-Seite
- `static/css/md3/components/editor.css` — Editor
- `static/css/md3/components/editor-overview.css` — Editor-Übersicht
- `static/css/md3/components/como-citar.css` — Zitierweise
- `static/css/md3/components/search-ui.css` — Search UI
- `static/css/md3/components/snackbar.css` — Snackbar
- `static/css/md3/components/status-banner.css` — Status-Banner
- `static/css/md3/components/stats.css` — Statistiken
- `static/css/md3/components/transcription-shared.css` — Transkriptionen

#### Niedrig-Relevant (primär Utility)
- `static/css/md3/components/errors.css` — Error-Seiten
- `static/css/md3/components/layout-helpers.css` — Layout-Helfer
- `static/css/md3/components/menu.css` — Menüs
- `static/css/md3/components/mobile-responsive.css` — Mobile Responsive
- `static/css/md3/components/motion.css` — Animationen
- `static/css/md3/components/navbar.css` — Navbar
- `static/css/md3/components/page-navigation.css` — Page-Navigation
- `static/css/md3/components/progress.css` — Progress
- `static/css/md3/components/select2.css` — Select2
- `static/css/md3/components/select2-tagify.css` — Select2-Tagify
- `static/css/md3/components/tabs.css` — Tabs
- `static/css/md3/components/token-chips.css` — Token-Chips
- `static/css/md3/components/toolbar.css` — Toolbar
- `static/css/md3/components/material-symbols-fallback.css` — Material Symbols Fallback

## 3. JavaScript-Dateien (93 total)

### 3.1 Inline-Style-Risiko (JS setzt möglicherweise Background)
- `static/js/modules/stats/initStatsTab.js` — Setzt inline `style="background: var(--md-sys-color-surface-container-low)"`
- `static/js/modules/stats/renderBar.js` — Setzt inline `background-color` für Legende
- `static/js/modules/auth/snackbar.js` — **KRITISCH**: Setzt mehrere inline Background-Styles!
- `static/js/editor/history-panel.js` — Setzt inline Styles
- `static/js/theme.js` — Theme-Management
- `static/js/theme-toggle.js` — Theme-Toggle

### 3.2 Weitere JS-Dateien (möglicherweise Style-Manipulation)
- Alle anderen 87 JS-Dateien: Potenzielle inline-style-Setter (müssten bei Bedarf einzeln geprüft werden)

## 4. Template-Vererbungs-Hierarchie

```
base.html (Root)
├── index.html
├── impressum.html
├── privacy.html
├── player.html
├── atlas.html
├── editor.html
├── admin_dashboard.html
├── corpus_metadata.html
├── corpus_guia.html
├── proyecto_*.html (5 Dateien)
├── auth/*.html (7 Dateien)
│   └── Nutzen oft _md3_skeletons/auth_*.html
├── search/advanced.html
└── errors/*.html (5 Dateien)
```

## 5. Kategorisierung nach Layout-Rolle

### Global (Base/Layout)
- `templates/base.html`
- `static/css/layout.css`
- `static/css/md3/layout.css`

### Layout-Komponenten (Global sichtbar)
- NavDrawer: `templates/partials/_navigation_drawer.html` + `static/css/md3/components/navigation-drawer.css`
- TopAppBar: `templates/partials/_top_app_bar.html` + `static/css/md3/components/top-app-bar.css`
- Footer: `templates/partials/footer.html` + `static/css/md3/components/footer.css`

### Seiten-Container
- `.md3-page` (definiert in `md3/layout.css`)
- `.md3-auth-card` (definiert in `md3/layout.css`)
- `.md3-text-page` (definiert in `md3/layout.css`)

### Komponenten (Lokal)
- Cards, Dialoge, Alerts, Buttons, Forms, etc.

## 6. Zusammenfassung

- **48 Templates** (Jinja2/Flask)
- **55 CSS-Dateien** (davon 8 kritisch)
- **93 JS-Dateien** (davon ~5 mit bekanntem inline-style-Risiko)
- **Kritische Dateien für Background-Audit:**
  - `templates/base.html`
  - `static/css/layout.css`
  - `static/css/app-tokens.css`
  - `static/css/md3/tokens.css`
  - `static/css/md3/layout.css`
  - `static/css/md3/components/cards.css`
  - `static/css/md3/components/navigation-drawer.css`
  - `static/css/md3/components/top-app-bar.css`
  - `static/css/md3/components/footer.css`
  - `static/css/player-mobile.css`
  - `static/js/modules/auth/snackbar.js`

**Nächste Schritte:** Detaillierte Analyse der gefundenen Background-Definitionen in FINDINGS_RAW.md
