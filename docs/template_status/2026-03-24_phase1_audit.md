# Phase 1 Template Audit - 2026-03-24

## 1. Executive Summary

Overall state: not template-ready.

Why not:
- branding was split between runtime config, base template literals, footer literals, title literals, and asset filenames
- the token system has more than one authority (`md3/tokens.css`, `app-tokens.css`, legacy shim, inactive `branding.css`, and JS chart palettes)
- the global shell exists, but several pages still override it locally instead of consuming it
- nested `<main>` elements are widespread inside templates that already render inside the base shell
- page-level CSS override density is high, especially for landing and player/mobile layouts
- reusable skeletons exist, but many pages still duplicate structure instead of treating the skeletons as the source of truth

Low-risk improvements were applied in this run, but the repository still needs follow-up refactors before it can act as a clean template.

## 2. Findings by Audit Block

### 1. Branding & App Identity

Current state:
- release metadata is centralized in `app/src/app/config/__init__.py`
- display branding was previously spread across `base.html`, `_top_app_bar.html`, `footer.html`, landing page markup, and auth page title blocks
- logos and favicon paths are still hardcoded directly in templates

Concrete problems:
- app name duplication existed in browser title, top app bar title, footer alt text, landing logo alt text, and auth page titles
- auth pages used `block title` while the active base template used `block page_title`
- footer badge URL and footer copyright string were hardcoded in the footer partial
- no central branding file existed for template-facing identity values
- there is still no central logo/favicon manifest; asset filenames remain duplicated
- per-page SEO/OG/Twitter metadata is still absent

Severity: high

Affected files:
- `app/src/app/config/__init__.py`
- `app/src/app/__init__.py`
- `app/templates/base.html`
- `app/templates/partials/_top_app_bar.html`
- `app/templates/partials/footer.html`
- `app/templates/pages/index.html`
- `app/templates/auth/*.html`

### 2. Design Token System

Current state:
- `app/static/css/md3/tokens.css` is the de facto foundation token file
- `app/static/css/app-tokens.css` adds semantic app tokens
- `app/static/css/md3/tokens-legacy-shim.css` keeps legacy token names alive
- `app/static/css/branding.css` defines a parallel brand-token layer, but it is not loaded by the active base template

Concrete problems:
- there are multiple token authorities instead of one clean chain
- `branding.css` suggests a branding path that is currently inactive, which is dangerous for template work because edits there do not affect the live app
- JS chart theming bypasses CSS tokens and hardcodes palettes in `app/static/js/modules/stats/theme/corapanTheme.js`
- `app/static/js/modules/stats/renderBar.js` still falls back to hardcoded hex values and inline tooltip styling
- `base.html` contains hardcoded fallback background values and hardcoded theme-color meta values
- footer/page background consistency depends on `--app-background`, but several page-specific styles still set background behavior independently

Severity: high

Affected files:
- `app/static/css/md3/tokens.css`
- `app/static/css/app-tokens.css`
- `app/static/css/md3/tokens-legacy-shim.css`
- `app/static/css/branding.css`
- `app/static/js/modules/stats/theme/corapanTheme.js`
- `app/static/js/modules/stats/renderBar.js`
- `app/templates/base.html`

### 3. MD3 Component System

Current state:
- a broad MD3 component layer exists under `app/static/css/md3/components/`
- skeleton templates exist under `app/templates/_md3_skeletons/`
- many pages manually assemble near-identical hero/card/form structures

Concrete problems:
- modal and standard navigation drawers duplicate large amounts of markup in one partial
- auth pages repeat the same hero, card, and form structure instead of clearly inheriting from a single template pattern
- player and editor layout CSS appear copy-pasted across component files with page-name-specific overrides
- the presence of skeletons does not mean they are authoritative; actual pages often bypass them

Severity: medium

Affected files:
- `app/templates/partials/_navigation_drawer.html`
- `app/templates/_md3_skeletons/*.html`
- `app/templates/auth/*.html`
- `app/static/css/md3/components/player.css`
- `app/static/css/md3/components/editor.css`

### 4. Layout & App Shell

Current state:
- the active shell is centralized in `app/templates/base.html`
- header, navigation drawer, main, and footer are defined once in the base template
- grid-based shell behavior lives in `app/static/css/layout.css`

Concrete problems:
- the shell is frequently overridden by page-specific CSS, especially on landing and player/mobile pages
- `layout.css` uses short-page min-height behavior that the landing page must explicitly undo in `md3/components/index.css`
- many page templates insert their own `<main>` element inside base main, which breaks the shell semantic contract
- page-specific selectors like `body[data-page="index"]` and `body.app-shell[data-page="player"]` show the shell is not yet strong enough to remain page-agnostic

Severity: high

Affected files:
- `app/templates/base.html`
- `app/static/css/layout.css`
- `app/static/css/md3/components/index.css`
- `app/static/css/md3/components/player.css`
- `app/static/css/player-mobile.css`
- `app/templates/pages/corpus_metadata.html`
- `app/templates/auth/*.html`
- `app/templates/pages/*.html`

### 5. Page Templates

Current state:
- page families are visible, but not consistently enforced by shared templates

Detected page types:
- landing: `app/templates/pages/index.html`
- auth: `app/templates/auth/login.html`, `account_*`, `password_*`, `admin_users.html`
- search: `app/templates/search/advanced.html`, `_results.html`, `search/partials/*`
- detail/editor/player: `app/templates/pages/player.html`, `player_overview.html`, `editor.html`, `editor_overview.html`
- static/content: `app/templates/pages/proyecto_*`, `impressum.html`, `privacy.html`, `corpus_guia.html`, `corpus_metadata.html`, `atlas.html`
- error/empty: `app/templates/errors/*.html`

Concrete problems:
- many page families have skeletons, but live pages are only loosely aligned with them
- nested main markup is common across auth and content pages
- corpus metadata and atlas pages use more custom structure than the text-page pattern
- landing has a custom page shell and shell-specific CSS exceptions

Severity: medium

Affected files:
- `app/templates/_md3_skeletons/*.html`
- `app/templates/auth/*.html`
- `app/templates/pages/*.html`
- `app/templates/search/*.html`

### 6. Hardcoding & CSS Audit

Current state:
- source-level hardcoding remains widespread in CSS and JS

Concrete problems:
- inline style occurrences in JS: 18
- inline style occurrences in templates: 4
- `!important` occurrences in CSS: 768
- hex color occurrences in CSS: 370
- hex color occurrences in JS: 59
- hex color occurrences in templates: 4
- page-shell override selectors in CSS: 11

Notable hot spots:
- `app/static/css/player-mobile.css`
- `app/static/css/md3/components/index.css`
- `app/static/js/modules/stats/theme/corapanTheme.js`
- `app/static/js/modules/stats/renderBar.js`
- `app/static/js/modules/search/searchUI.js`

Severity: high

Affected files:
- `app/static/css/player-mobile.css`
- `app/static/css/md3/components/index.css`
- `app/static/js/modules/stats/theme/corapanTheme.js`
- `app/static/js/modules/stats/renderBar.js`
- `app/static/js/modules/search/*.js`
- `app/templates/base.html`
- `app/templates/pages/proyecto_como_citar.html`

### 7. Theming & States

Current state:
- MD3 hover/focus states are present in several components
- footer, drawer, and app bar have usable focus-visible behavior

Concrete problems:
- state behavior is not fully driven by shared tokens because JS-generated markup and chart themes use their own styling
- chart colors, tooltip styles, and certain inline error states do not inherit a single token pipeline
- the dark-mode story is partly token-driven and partly fallback-driven

Severity: medium

Affected files:
- `app/static/css/md3/components/footer.css`
- `app/static/css/md3/components/navigation-drawer.css`
- `app/static/js/modules/stats/theme/corapanTheme.js`
- `app/static/js/modules/advanced/formHandler.js`
- `app/static/js/modules/search/searchUI.js`

### 8. Dev / Prod Parity

Current state:
- canonical dev selection is root `docker-compose.dev-postgres.yml` plus `scripts/dev-start.ps1` delegating to `app/scripts/dev-start.ps1`
- canonical prod selection is `app/infra/docker-compose.prod.yml` plus `app/scripts/deploy_prod.sh`
- release metadata is injected from GitHub in both dev-start and deploy scripts
- asset paths are consistent because both environments use the same Flask templates and `url_for('static', ...)`

Concrete problems:
- prod compose still exports legacy `DATABASE_URL` alongside canonical `AUTH_DATABASE_URL`
- app-local `app/infra/docker-compose.dev.yml` also exports legacy `DATABASE_URL`, which conflicts with current policy even if it is not the canonical dev entrypoint
- dev and prod runtime roots are intentionally different, but the distinction is operational rather than template-documented inside the UI layer
- dev startup script auto-manages support services while production relies on container orchestration; behavior is equivalent at the app layer but not through a single config abstraction

Severity: medium

Affected files:
- `docker-compose.dev-postgres.yml`
- `scripts/dev-start.ps1`
- `app/scripts/dev-start.ps1`
- `app/infra/docker-compose.prod.yml`
- `app/infra/docker-compose.dev.yml`
- `app/scripts/deploy_prod.sh`

### 9. Configuration Architecture

Current state:
- runtime config is mostly centralized in `app/src/app/config/__init__.py`
- branding was not previously separated from template literals

Concrete problems:
- runtime config is centralized, but template branding was not
- `branding.css` creates a false configuration surface because it looks canonical but is not active
- application config, template config, and JS theme config are not yet separated cleanly

Severity: high

Affected files:
- `app/src/app/config/__init__.py`
- `app/src/app/branding.py`
- `app/static/css/branding.css`
- `app/static/js/modules/stats/theme/corapanTheme.js`

### 10. Maintainability / Template Fitness

Current state:
- the repo contains strong building blocks, but the path to adaptation is not obvious enough for an external developer

Concrete problems:
- before this run there was no single file for template-facing branding text
- changing primary branding still requires touching asset filenames, some title blocks, and potentially inactive CSS
- component duplication makes it hard to know which pattern is canonical
- shell exceptions are distributed across page CSS rather than encoded into reusable layout contracts

Severity: high

Affected files:
- `app/src/app/branding.py`
- `app/templates/**/*.html`
- `app/static/css/**/*.css`
- `app/static/js/modules/stats/**/*.js`

### 11. Accessibility & UX

Current state:
- many components use semantic headings and focus-visible styles
- footer and drawer generally follow navigable patterns

Concrete problems:
- nested `<main>` elements hurt semantic clarity for assistive technology
- fixed/sticky mobile player behavior is override-heavy and likely fragile on smaller devices
- inline style output in JS reduces consistency and makes accessible state tuning harder
- no evidence of a systematic contrast audit or token-enforced contrast guarantees across chart colors

Severity: medium

Affected files:
- `app/templates/auth/*.html`
- `app/templates/pages/*.html`
- `app/static/css/player-mobile.css`
- `app/static/js/modules/stats/theme/corapanTheme.js`

### 12. Repo & Documentation Structure

Current state:
- a master plan exists in `docs/template_status/template_master_plan.md`
- prior to this run there was no phase-1 audit report and no root agent learnings file for template work

Concrete problems:
- template governance knowledge was not captured in a future-agent rules file
- there was no date-stamped audit artifact for the current template status

Severity: low

Affected files:
- `docs/template_status/template_master_plan.md`
- `.github/agents/skills.md`
- `docs/template_status/2026-03-24_phase1_audit.md`

## 3. Token System Reality Check

Where tokens exist:
- foundation tokens: `app/static/css/md3/tokens.css`
- semantic app tokens: `app/static/css/app-tokens.css`
- legacy alias layer: `app/static/css/md3/tokens-legacy-shim.css`

Where they are bypassed:
- inactive parallel brand mapping in `app/static/css/branding.css`
- base template inline fallback colors in `app/templates/base.html`
- chart palette and theme literals in `app/static/js/modules/stats/theme/corapanTheme.js`
- chart fallback colors and inline tooltip styles in `app/static/js/modules/stats/renderBar.js`
- heavy mobile/player overrides in `app/static/css/player-mobile.css`

Biggest structural flaw:
- CSS tokens are not the only authority for color and layout. The live app still mixes CSS tokens, legacy aliases, an inactive brand-token file, and JS-side color definitions. That breaks the required `tokens -> semantics -> components -> pages` contract.

## 4. Hardcoding Report

### Inline styles
- JS: 18 matches
- Templates: 4 matches
- Main offenders: `app/static/js/modules/search/searchUI.js`, `app/static/js/modules/stats/initStatsTab.js`, `app/static/js/modules/stats/initStatsTabAdvanced.js`, `app/static/js/modules/advanced/formHandler.js`

### `!important`
- CSS matches: 768
- Concentrated in: `app/static/css/player-mobile.css`, `app/static/css/md3/components/index.css`, plus utility-heavy global layout styles

### Direct hex colors
- CSS: 370 matches
- JS: 59 matches
- Templates: 4 matches
- Source buckets:
  - expected foundation usage in `md3/tokens.css`
  - dangerous parallel branding palette in `branding.css`
  - dangerous runtime theme literals in `stats/theme/corapanTheme.js`
  - dangerous fallback literals in `renderBar.js` and `base.html`

### Page-specific shell hacks
- 11 shell-override selectors detected in CSS
- Main offenders:
  - `app/static/css/md3/components/index.css`
  - `app/static/css/md3/components/player.css`
  - `app/static/css/md3/components/editor.css`

### Safe-to-remove-now vs later-refactor

Safe wins applied now:
- auth title blocks normalized to the active `page_title` contract
- template-facing branding strings moved into `app/src/app/branding.py`
- top app bar, footer, landing title/alt text, and default meta text now consume the shared branding context

Needs later refactor:
- `branding.css` disposition: remove or reactivate deliberately, but do not leave it as a silent parallel system
- JS chart theme migration to CSS-token-driven palette access
- player mobile override reduction
- landing page shell exceptions
- nested `<main>` cleanup across templates

## 5. Quick Wins Applied

Exact changes made:
- created `app/src/app/branding.py` as the first template-facing branding config
- injected branding values from `app/src/app/__init__.py` into all templates
- added default application-name and meta-description tags in `app/templates/base.html`
- replaced hardcoded top app bar site title with shared branding in `app/templates/partials/_top_app_bar.html`
- replaced footer brand URL, badge alt text, logo alt text, and copyright text with shared branding in `app/templates/partials/footer.html`
- replaced landing-page title and logo alt text with shared branding in `app/templates/pages/index.html`
- normalized `app/templates/search/advanced.html` so the browser title includes the app name
- fixed auth template title-block mismatch by switching auth templates from `block title` to `block page_title`

Files changed for quick wins:
- `app/src/app/branding.py`
- `app/src/app/__init__.py`
- `app/templates/base.html`
- `app/templates/partials/_top_app_bar.html`
- `app/templates/partials/footer.html`
- `app/templates/pages/index.html`
- `app/templates/search/advanced.html`
- `app/templates/auth/login.html`
- `app/templates/auth/account_profile.html`
- `app/templates/auth/account_password.html`
- `app/templates/auth/account_delete.html`
- `app/templates/auth/password_forgot.html`
- `app/templates/auth/password_reset.html`
- `app/templates/auth/admin_users.html`

## 6. Required Refactors (next phases)

Priority 1:
- decide the single branding authority for text plus assets and either remove or deliberately activate `app/static/css/branding.css`
- remove nested `<main>` usage from page templates so the base shell remains the only page landmark owner
- eliminate JS-side chart palettes and drive chart colors from live CSS tokens

Priority 2:
- collapse landing-page shell exceptions into shell-safe layout primitives instead of `body[data-page]` overrides
- reduce `player-mobile.css` override density by moving stable layout rules into reusable component/layout classes
- extract duplicated navigation drawer structure into a single macro or shared data-driven renderer

Priority 3:
- align auth, text, and overview pages with the existing `_md3_skeletons` as actual source-of-truth templates
- replace remaining hardcoded page-title suffixes with a shared formatting helper or consistent template convention
- introduce a central logo/favicon asset manifest for template adaptation

Priority 4:
- add per-page SEO metadata hooks once branding and page-template ownership are stable
- remove deprecated utility usage as pages migrate to token-driven semantic layout helpers
