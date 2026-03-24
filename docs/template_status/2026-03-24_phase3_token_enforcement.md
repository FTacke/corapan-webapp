# Phase 3 Token Enforcement

## 1. Executive Summary

This run reduced the most damaging remaining styling drift in the live search/stats path and trimmed a few high-risk page CSS overrides without changing the app’s visual model.

Improved:
- JS theme access now flows through a shared CSS-variable helper.
- Search and stats loading/error states rely less on inline visual styling.
- Stats chart theming moved further away from JS-local fallback palettes.
- Several hotspot CSS files now carry fewer redundant override rules or repeated literals.

Still risky:
- `app/static/css/player-mobile.css` remains the densest override file in the repo.
- `app/static/css/md3/tokens-legacy-shim.css` is still required by live callers not touched in this run.
- Some adjacent modules outside the main target list still contain inline style usage and will need later passes.

## 2. Master Plan Update

Updated `docs/template_status/template_master_plan.md` to:
- mark Phase 1 as completed
- mark Phase 2 as completed
- mark Phase 3 as in progress
- add `Phase 3 Execution Focus`

The new Phase 3 section explicitly targets:
- token enforcement
- JS theme alignment
- hardcoded color/style reduction
- page-level override density reduction
- later legacy-shim removal preparation

## 3. Hardcoding Reduction Applied

Exact files touched:
- `app/static/js/modules/stats/theme/corapanTheme.js`
- `app/static/js/modules/stats/renderBar.js`
- `app/static/js/modules/search/searchUI.js`
- `app/static/js/modules/advanced/formHandler.js`
- `app/static/js/modules/advanced/initTable.js`
- `app/static/js/modules/stats/initStatsTab.js`
- `app/static/js/modules/stats/initStatsTabAdvanced.js`
- `app/static/css/md3/components/advanced-search.css`
- `app/static/css/md3/components/tabs.css`
- `app/static/css/md3/components/stats.css`
- `app/static/css/md3/components/index.css`
- `app/static/css/player-mobile.css`
- `app/static/css/md3/components/player.css`
- `app/static/css/md3/components/editor.css`

Reductions applied:
- replaced search/stats summary inline color/weight markup with component classes
- replaced stats loading skeleton inline styles with CSS classes
- replaced stats total-count inline highlight styling with a class
- replaced editor success-state raw `rgba(...)` colors with app success tokens
- replaced editor dialog overlay raw `rgba(0, 0, 0, 0.4)` with a scrim-token-derived color mix
- removed redundant page-body background override rules from player/editor component CSS
- reduced repeated mobile player spacing literals by introducing token-backed local variables in `player-mobile.css`
- merged duplicate desktop index-page override media blocks in `index.css`

## 4. JS Theme Alignment

Moved toward CSS-token-driven behavior:
- added `app/static/js/modules/core/themeTokens.js` as the shared CSS-variable reader
- updated `corapanTheme.js` to resolve chart colors from CSS tokens via the helper
- updated `renderBar.js` to consume the helper and remove custom tooltip swatch styling in favor of ECharts marker output
- updated search/advanced/stats modules to use shared CSS classes for visual summary/error states instead of inline color styling
- updated stats loading state to use class-based loading styles on the container instead of direct inline opacity/pointer-events control

What still remains:
- some adjacent modules still use inline `style` operations for visibility or utility behavior
- not every stats/search module was migrated in this run
- fallback logic still exists, but it now leans on token-derived or system-color paths instead of JS-local color palettes

## 5. CSS Override Reduction

What got cleaner:
- `index.css` now carries fewer repeated desktop override blocks
- `player.css` and `editor.css` no longer redundantly restate body background overrides already provided by shell/app background behavior
- `editor.css` now uses semantic success tokens for modified-word and modified-speaker highlighting
- `player-mobile.css` now reuses a small set of local token-backed variables for repeated spacing/line-height/player-height values

What is still too brittle to touch yet:
- the fixed mobile player block in `player-mobile.css`
- large stretches of `!important`-heavy mobile layout enforcement
- remaining page-specific override patterns that still depend on the current shell/layout contract

## 6. Legacy Shim Readiness

Progress made:
- new work in touched files avoided introducing new `--md3-*` callers
- touched JS theming code now reads canonical token names through a shared helper

Dependencies still remaining:
- `app/static/css/md3/tokens-legacy-shim.css` remains necessary because other live callers still request legacy `--md3-*` names
- adjacent modules outside this run still contain legacy-style visibility or style wiring

Removal status:
- closer than before, but not ready for removal

## 7. Agent-Learning Update

Updated `.github/agents/skills.md` with:
- a concrete runtime map for branding, title formatting, shell ownership, token ownership, deprecated loaded files, and shared JS theme access
- Phase 3 rules banning new hex literals, independent JS palettes, and new `--md3-*` usage
- hotspot warnings for player mobile, index shell overrides, stats theme/render modules, search UI, and editor CSS

## 8. Remaining Priority Work

1. migrate the remaining visible `style.display` and inline-summary patterns in adjacent search/advanced modules not touched here
2. continue shrinking `player-mobile.css` by extracting only proven shared mobile-player primitives
3. audit remaining live `--md3-*` callers and migrate the safest ones to canonical names
4. reduce remaining raw/inline style usage in stats auxiliary modules
5. reassess whether any remaining page-shell overrides can move into stronger shared layout primitives without churn