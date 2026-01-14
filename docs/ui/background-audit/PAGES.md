# Background-Color Audit: Seitenbasierte Analyse

**Projekt:** corapan-webapp  
**Audit-Datum:** 14. Januar 2026  
**Zweck:** Detaillierte Analyse repräsentativer Seiten

## Legende

**Risiko-Level:**
- 🟢 **Niedrig:** Token-basiert, keine Konflikte
- 🟡 **Mittel:** Kleinere Inkonsistenzen oder Fallback-Werte
- 🔴 **Hoch:** Harte Farben, !important, oder multiple konkurrierende Definitionen

## 1. Startseite (Index)

### 1.1 Template-Info
- **Pfad:** `templates/pages/index.html`
- **Extends:** `base.html`
- **Container:** `.md3-index-page` (keine Background-Definition)
- **URL:** https://corapan.hispanistica.com/

### 1.2 DOM-Struktur & Backgrounds
```
html (background: --app-background)
  └── body.app-shell (background: --app-background)
      ├── #navigation-drawer (background: surface)
      ├── .md3-top-app-bar (background: surface | transparent)
      ├── #main-content (background: transparent)
      │   └── .md3-index-page (KEIN background)
      │       ├── .md3-index-logo (KEIN background)
      │       └── .md3-index-cards (KEIN background)
      │           └── .md3-card.md3-card--filled.md3-card--landing (3x)
      │               ├── background: var(--md-sys-color-surface-container-high)
      │               ├── padding: var(--space-4)
      │               └── border-radius: var(--radius-md)
      └── .md3-footer (background: --app-background)
```

### 1.3 Background-Definitionen auf dem Pfad
1. **html/body:** `--app-background` → `surface-container` (via tokens)
2. **main-content:** `transparent` (scheint body durch)
3. **Landing Cards:** `surface-container-high` (private Token `--_card-bg`)
4. **Footer:** `--app-background` → `surface-container`

### 1.4 Vermutete Surface-Layer (MD3)
- **Page Background:** `surface-container` (Level 1)
- **Landing Cards:** `surface-container-high` (Level 4)
- **Elevation:** Cards: `var(--elev-1)`

### 1.5 Risiko-Bewertung
🟢 **NIEDRIG**
- Alle Definitionen Token-basiert
- Klare Hierarchie (Container → Cards)
- Konsistent mit MD3-Spec

**Keine Issues gefunden.**

---

## 2. Login-Seite

### 2.1 Template-Info
- **Pfad:** `templates/auth/login.html`
- **Extends:** `base.html`
- **Container:** `.md3-page` + `.md3-auth-card`
- **URL:** https://corapan.hispanistica.com/auth/login

### 2.2 DOM-Struktur & Backgrounds
```
html (background: --app-background)
  └── body.app-shell (background: --app-background)
      ├── #main-content (background: transparent)
      │   └── .md3-page (KEIN background, nur --_page-bg: surface)
      │       ├── .md3-page__header (KEIN background)
      │       │   └── .md3-hero.md3-hero--card
      │       │       └── background: var(--md-sys-color-surface)
      │       └── .md3-page__main
      │           └── .md3-auth-card (background: var(--md-sys-color-surface))
      │               ├── --_auth-card-bg: surface
      │               ├── --app-textfield-label-bg: --_auth-card-bg
      │               └── .md3-auth-form (KEIN background)
      │                   ├── .md3-alert (background: error-container)
      │                   └── .md3-outlined-textfield (KEIN background)
      └── .md3-footer (background: --app-background)
```

### 2.3 Background-Definitionen auf dem Pfad
1. **html/body:** `--app-background` → `surface-container`
2. **main-content:** `transparent`
3. **Hero Card:** `surface` (aus `md3/layout.css`)
4. **Auth Card:** `surface` (aus `md3/layout.css`)
5. **Alert:** `error-container` (bei Fehler)
6. **Footer:** `--app-background` → `surface-container`

### 2.4 Vermutete Surface-Layer (MD3)
- **Page Background:** `surface-container` (Level 1)
- **Hero + Auth Card:** `surface` (Level 0 - Base)
- **Alert:** `error-container` (Semantic)

### 2.5 Risiko-Bewertung
🟡 **MITTEL**

**Issues:**
1. Auth-Card nutzt `surface` statt `surface-container-high` (anders als andere Cards)
2. Hero + Auth-Card BEIDE auf `surface` → keine visuelle Hierarchie
3. Alert-Fallback mit harter Farbe: `#fdecea`

**Empfehlung:**
- Auth-Card auf `surface-container-high` anheben (wie Landing Cards)
- Hero auf `surface-container` setzen für Hierarchie

---

## 3. Player-Seite

### 3.1 Template-Info
- **Pfad:** `templates/pages/player.html`
- **Extends:** `base.html`
- **Container:** `.md3-player-page`
- **URL:** https://corapan.hispanistica.com/player?transcription=... (dynamisch)

### 3.2 DOM-Struktur & Backgrounds (Desktop)
```
html (background: --app-background)
  └── body.app-shell (background: --app-background)
      ├── #navigation-drawer (background: surface)
      ├── .md3-top-app-bar (background: transparent)
      ├── #main-content (background: transparent)
      │   └── #player-page-root.md3-player-page (KEIN background)
      │       └── .md3-player-container (KEIN background)
      │           ├── .md3-player-transcript (KEIN background)
      │           │   ├── .md3-player-header (KEIN background)
      │           │   ├── #transcriptionContainer (KEIN background)
      │           │   └── .audio-player-container
      │           │       └── background: rgba(255,255,255,0.95) + blur(20px)
      │           └── .player-sidebar (KEIN background Desktop)
      │               └── .md3-player-card (KEIN background Desktop)
      └── .md3-footer (background: --app-background)
```

### 3.3 DOM-Struktur & Backgrounds (Mobile)
```
html (background: --app-background)
  └── body.app-shell (background: --app-background)
      ├── #main-content (background: transparent)
      │   └── #player-page-root.md3-player-page (KEIN background)
      │       └── .md3-player-container (KEIN background)
      │           ├── .md3-player-transcript (KEIN background)
      │           │   └── .audio-player-container.mobile
      │           │       └── background: surface-container !important
      │           └── .player-sidebar
      │               ├── background: surface-container-low
      │               └── .md3-player-card
      │                   ├── background: surface-container-low
      │                   └── .md3-player-card-header
      │                       └── background: surface-container-highest
      └── .md3-footer (background: --app-background)
```

### 3.4 Background-Definitionen auf dem Pfad
**Desktop:**
1. **html/body:** `--app-background` → `surface-container`
2. **Top-App-Bar:** `transparent`
3. **Audio-Player:** `rgba(255,255,255,0.95)` + Glassmorphism

**Mobile:**
1. **html/body:** `--app-background` → `surface-container`
2. **Audio-Player:** `surface-container` (!important)
3. **Player-Sidebar:** `surface-container-low`
4. **Player-Card:** `surface-container-low`
5. **Card-Header:** `surface-container-highest`

### 3.5 Vermutete Surface-Layer (MD3)
**Desktop:**
- **Page Background:** `surface-container` (Level 1)
- **Audio-Player:** Glassmorphism (harte Farbe!)

**Mobile:**
- **Page Background:** `surface-container` (Level 1)
- **Sidebar:** `surface-container-low` (Level 2)
- **Cards:** `surface-container-low` (Level 2)
- **Card-Headers:** `surface-container-highest` (Level 5)

### 3.6 Risiko-Bewertung
🔴 **HOCH**

**Kritische Issues:**
1. **Audio-Player Glassmorphism:** Harte Farbe `rgba(255,255,255,0.95)` ohne Dark-Mode-Anpassung!
2. **!important Overrides:** Mobile Audio-Player mit doppelter !important-Definition
3. **Inkonsistente Surface-Levels:** Card-Header auf `highest` (Level 5) ist zu hoch

**Weitere Issues:**
4. Keine klare Hierarchie zwischen Sidebar/Cards/Headers
5. Desktop vs. Mobile völlig unterschiedliche Background-Strategie

**Empfehlung:**
- Audio-Player: Token-basiertes Glassmorphism mit `color-mix()`
- Mobile: Sidebar/Cards auf einheitlichen Level reduzieren
- !important entfernen und Spezifität korrigieren

---

## 4. Advanced Search

### 4.1 Template-Info
- **Pfad:** `templates/search/advanced.html`
- **Extends:** `base.html`
- **Container:** `.advanced-search-container`
- **URL:** https://corapan.hispanistica.com/advanced-search

### 4.2 DOM-Struktur & Backgrounds
```
html (background: --app-background)
  └── body.app-shell (background: --app-background)
      ├── #main-content (background: transparent)
      │   └── .advanced-search-container
      │       ├── background: var(--md-sys-color-surface-container)
      │       ├── .pattern-badge--surface
      │       │   └── background: surface-variant (fallback: #f3edf7)
      │       ├── .pattern-badge--primary
      │       │   └── background: primary (fallback: #0a5981)
      │       ├── .query-preview
      │       │   └── background: surface-container-low
      │       ├── .search-results-card
      │       │   └── background: surface-container-lowest (fallback: #ffffff)
      │       └── .search-modal
      │           └── background: surface (fallback: #ffffff)
      └── .md3-footer (background: --app-background)
```

### 4.3 Background-Definitionen auf dem Pfad
1. **html/body:** `--app-background` → `surface-container`
2. **Search Container:** `surface-container`
3. **Pattern Badges:** `surface-variant` / `primary` (mit Fallbacks!)
4. **Query Preview:** `surface-container-low`
5. **Results Card:** `surface-container-lowest` (Fallback: `#ffffff`)
6. **Modal:** `surface` (Fallback: `#ffffff`)

### 4.4 Vermutete Surface-Layer (MD3)
- **Page Background:** `surface-container` (Level 1)
- **Search Container:** `surface-container` (Level 1) - gleich wie Page!
- **Results Card:** `surface-container-lowest` (Level 0-)
- **Query Preview:** `surface-container-low` (Level 2)
- **Modal:** `surface` (Level 0)

### 4.5 Risiko-Bewertung
🟡 **MITTEL**

**Issues:**
1. **Fallback-Werte:** Harte Farben (`#f3edf7`, `#0a5981`, `#ffffff`) statt Token-basiert
2. **Hover-State:** `rgba(0,0,0,0.04)` statt Token
3. **Search-Container = Page-Background:** Kein visueller Unterschied
4. **Overlay:** `rgba(0,0,0,0.4)` könnte im Dark Mode zu dunkel sein

**Empfehlung:**
- Fallbacks entfernen oder Token-basiert gestalten
- Search-Container eine Stufe höher heben (`surface-container-high`)
- Hover mit `color-mix()` statt hartem rgba

---

## 5. Atlas-Seite

### 5.1 Template-Info
- **Pfad:** `templates/pages/atlas.html`
- **Extends:** `base.html`
- **Container:** `.md3-atlas-page`
- **URL:** https://corapan.hispanistica.com/atlas

### 5.2 DOM-Struktur & Backgrounds
```
html (background: --app-background)
  └── body.app-shell (background: --app-background)
      ├── #main-content (background: transparent)
      │   └── .md3-atlas-page
      │       ├── .md3-atlas-container
      │       │   └── background: var(--md-sys-color-surface-container)
      │       ├── .md3-atlas-map-card
      │       │   └── background: var(--md-sys-color-surface)
      │       ├── .md3-atlas-legend-card
      │       │   └── background: var(--md-sys-color-surface)
      │       └── .md3-atlas-marker--primary-container
      │           └── background: var(--md-sys-color-primary-container)
      └── .md3-footer (background: --app-background)
```

### 5.3 Background-Definitionen auf dem Pfad
1. **html/body:** `--app-background` → `surface-container`
2. **Atlas Container:** `surface-container`
3. **Map/Legend Cards:** `surface`
4. **Map Markers:** `primary-container` (mit `color-mix()` für Hover)

### 5.4 Vermutete Surface-Layer (MD3)
- **Page Background:** `surface-container` (Level 1)
- **Atlas Container:** `surface-container` (Level 1)
- **Map/Legend Cards:** `surface` (Level 0)
- **Markers:** `primary-container` (Semantic)

### 5.5 Risiko-Bewertung
🟢 **NIEDRIG**

**Keine kritischen Issues.**

**Kleines Problem:**
- Atlas-Container = Page-Background (wie bei Search)

**Empfehlung:**
- Atlas-Container optional eine Stufe höher heben

---

## 6. Impressum (Text-Seite)

### 6.1 Template-Info
- **Pfad:** `templates/pages/impressum.html`
- **Extends:** `base.html`
- **Container:** `.md3-page` + `.md3-text-page`
- **URL:** https://corapan.hispanistica.com/impressum

### 6.2 DOM-Struktur & Backgrounds
```
html (background: --app-background)
  └── body.app-shell (background: --app-background)
      ├── #main-content (background: transparent)
      │   └── .md3-page (KEIN background)
      │       ├── .md3-page__header (KEIN background)
      │       │   └── .md3-hero.md3-hero--card
      │       │       └── background: var(--md-sys-color-surface)
      │       └── .md3-text-page (KEIN background)
      │           └── .md3-text-content (KEIN background)
      └── .md3-footer (background: --app-background)
```

### 6.3 Background-Definitionen auf dem Pfad
1. **html/body:** `--app-background` → `surface-container`
2. **Hero Card:** `surface`
3. **Text Content:** Transparent (Body Background scheint durch)

### 6.4 Vermutete Surface-Layer (MD3)
- **Page Background:** `surface-container` (Level 1)
- **Hero Card:** `surface` (Level 0)
- **Text Content:** Transparent über `surface-container`

### 6.5 Risiko-Bewertung
🟢 **NIEDRIG**

**Keine Issues gefunden.**

---

## 7. Admin Dashboard

### 7.1 Template-Info
- **Pfad:** `templates/pages/admin_dashboard.html`
- **Extends:** `base.html`
- **Container:** `.admin-dashboard`
- **URL:** https://corapan.hispanistica.com/admin/dashboard (Login required)

### 7.2 DOM-Struktur & Backgrounds
```
html (background: --app-background)
  └── body.app-shell (background: --app-background)
      ├── #main-content (background: transparent)
      │   └── .admin-dashboard
      │       ├── .admin-stat-card
      │       │   └── background: var(--md-sys-color-primary-container)
      │       ├── .admin-stat-card--error
      │       │   └── background: color-mix(error 15%, transparent)
      │       ├── .admin-table-card
      │       │   └── background: var(--md-sys-color-surface-container-lowest)
      │       └── .admin-action-row
      │           └── background: var(--md-sys-color-surface-container-low)
      └── .md3-footer (background: --app-background)
```

### 7.3 Background-Definitionen auf dem Pfad
1. **html/body:** `--app-background` → `surface-container`
2. **Stat Cards:** `primary-container` (Standard), `error` (Mix) für Probleme
3. **Table Card:** `surface-container-lowest`
4. **Action Row:** `surface-container-low`

### 7.4 Vermutete Surface-Layer (MD3)
- **Page Background:** `surface-container` (Level 1)
- **Stat Cards:** `primary-container` (Semantic)
- **Table Card:** `surface-container-lowest` (Level 0-)
- **Action Row:** `surface-container-low` (Level 2)

### 7.5 Risiko-Bewertung
🟢 **NIEDRIG**

**Keine kritischen Issues.**

**Observation:**
- Gute Nutzung von semantischen Containern (`primary-container`, `error`)
- Klare Hierarchie

---

## 8. Corpus Metadata

### 8.1 Template-Info
- **Pfad:** `templates/pages/corpus_metadata.html`
- **Extends:** `base.html`
- **Container:** `.md3-corpus-metadata`
- **URL:** https://corapan.hispanistica.com/corpus/metadata

### 8.2 DOM-Struktur & Backgrounds
```
html (background: --app-background)
  └── body.app-shell (background: --app-background)
      ├── #main-content (background: transparent)
      │   └── .md3-corpus-metadata
      │       ├── .md3-metadata-badge
      │       │   └── background: color-mix(primary 8%, transparent)
      │       ├── .md3-metadata-badge:hover
      │       │   └── background: color-mix(primary 16%, transparent)
      │       ├── .md3-metadata-card
      │       │   └── background: var(--md-sys-color-surface)
      │       ├── .md3-metadata-section
      │       │   └── background: var(--md-sys-color-surface-container-low)
      │       └── .md3-metadata-highlight
      │           └── background: var(--md-sys-color-surface-container-highest)
      └── .md3-footer (background: --app-background)
```

### 8.3 Background-Definitionen auf dem Pfad
1. **html/body:** `--app-background` → `surface-container`
2. **Metadata Badges:** `color-mix()` mit Primary (8% / 16% hover)
3. **Metadata Cards:** `surface`
4. **Metadata Sections:** `surface-container-low`
5. **Highlights:** `surface-container-highest`

### 8.4 Vermutete Surface-Layer (MD3)
- **Page Background:** `surface-container` (Level 1)
- **Cards:** `surface` (Level 0)
- **Sections:** `surface-container-low` (Level 2)
- **Highlights:** `surface-container-highest` (Level 5)
- **Badges:** Tinted Overlays (Dynamic)

### 8.5 Risiko-Bewertung
🟢 **NIEDRIG**

**Keine kritischen Issues.**

**Observation:**
- ✅ Excellente Nutzung von `color-mix()` für Hover-States
- ✅ Gute Surface-Hierarchie

---

## 9. Error Pages (404)

### 9.1 Template-Info
- **Pfad:** `templates/errors/404.html`
- **Extends:** `base.html`
- **Container:** `.md3-error-page`
- **URL:** https://corapan.hispanistica.com/404 (bei ungültiger URL)

### 9.2 DOM-Struktur & Backgrounds
```
html (background: --app-background)
  └── body.app-shell (background: --app-background)
      ├── #main-content (background: transparent)
      │   └── .md3-error-page (KEIN background)
      │       └── .md3-error-card (KEIN background in errors.css)
      │           └── Nutzt wahrscheinlich Standard-Card-Styles
      └── .md3-footer (background: --app-background)
```

### 9.3 Background-Definitionen auf dem Pfad
1. **html/body:** `--app-background` → `surface-container`
2. **Error Card:** Wahrscheinlich von `.md3-card--*` geerbt

### 9.4 Vermutete Surface-Layer (MD3)
- **Page Background:** `surface-container` (Level 1)
- **Error Card:** Vermutlich `surface-container-*` (je nach Card-Klasse)

### 9.5 Risiko-Bewertung
🟢 **NIEDRIG**

**Keine Issues gefunden** (einfache Seite)

---

## 10. Player Overview

### 10.1 Template-Info
- **Pfad:** `templates/pages/player_overview.html`
- **Extends:** `base.html`
- **Container:** `.md3-player-overview`
- **URL:** https://corapan.hispanistica.com/player

### 10.2 DOM-Struktur & Backgrounds
```
html (background: --app-background)
  └── body.app-shell (background: --app-background)
      ├── #main-content (background: transparent)
      │   └── .md3-player-overview
      │       └── (wahrscheinlich Cards für Transkriptionen)
      └── .md3-footer (background: --app-background)
```

### 10.3 Risiko-Bewertung
🟢 **NIEDRIG** (keine speziellen Backgrounds außer Standard-Cards)

---

## 11. Corpus Guia

### 11.1 Template-Info
- **Pfad:** `templates/pages/corpus_guia.html`
- **Extends:** `base.html`
- **Container:** `.md3-corpus-guia`
- **URL:** https://corapan.hispanistica.com/corpus/guia

### 11.2 Risiko-Bewertung
🟢 **NIEDRIG** (Text-Seite ähnlich Impressum)

---

## 12. Proyecto-Seiten (Übersicht)

### 12.1 Template-Info
- **Pfade:** `templates/pages/proyecto_*.html` (5 Dateien)
- **Extends:** `base.html`
- **Container:** `.md3-text-page`
- **URL:** https://corapan.hispanistica.com/proyecto/*

### 12.2 Risiko-Bewertung
🟢 **NIEDRIG** (Standard Text-Seiten mit Hero-Cards)

---

## 13. Zusammenfassung nach Risiko

### 🔴 Hoch-Risiko Seiten (1)
1. **Player** → Glassmorphism + !important + inkonsistente Surface-Levels

### 🟡 Mittel-Risiko Seiten (2)
2. **Advanced Search** → Fallback-Werte, Hover-States
3. **Login** → Auth-Card Surface-Level inkonsistent

### 🟢 Niedrig-Risiko Seiten (10)
4. **Index** → Token-basiert, klar
5. **Atlas** → Token-basiert, klar
6. **Impressum** → Standard Text-Seite
7. **Admin Dashboard** → Gute Semantic-Container
8. **Corpus Metadata** → Excellente `color-mix()`-Nutzung
9. **Error Pages** → Einfach, Standard
10. **Player Overview** → Standard Cards
11. **Corpus Guia** → Standard Text-Seite
12. **Proyecto-Seiten** → Standard Text-Seiten
13. **Privacy** → Standard Text-Seite

## 14. Priorisierte Handlungsempfehlungen

### Sofort (Sprint 1)
1. **Player:** Audio-Player Glassmorphism mit Token-basiertem Ansatz neu implementieren
2. **Player:** !important-Overrides entfernen
3. **Login:** Auth-Card auf `surface-container-high` anheben

### Nächster Sprint (Sprint 2)
4. **Advanced Search:** Fallback-Werte entfernen
5. **Advanced Search:** Hover-States mit `color-mix()` statt rgba
6. **Alle Seiten:** Container-Background vs. Page-Background differenzieren

### Backlog
7. Hero-Card vs. Auth-Card Hierarchie vereinheitlichen
8. Surface-Level-Dokumentation für alle Komponenten erstellen

**Nächster Schritt:** ISSUES.md mit kategorisierten Problemen
