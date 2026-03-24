# Phase 3 Token Enforcement

## Scope

- Environment: local versioned application layer under `app/`
- Governance: future-agent guidance under `.github/`
- Goal: reduce structural styling drift while preserving runtime behavior

## What Changed

- Added a shared CSS-variable helper at `app/static/js/modules/core/themeTokens.js`.
- Moved live stats chart theme access further into the canonical CSS token pipeline.
- Replaced several search/stats inline visual JS fragments with class-based markup.
- Converted stats loading and error visual states toward component CSS instead of inline styles.
- Reduced repeated mobile-player literals and removed a few redundant page-level background overrides.
- Updated template-system plan and agent runtime guidance for Phase 3 execution.

## Why

- Phase 2 locked authority boundaries, but the most damaging live styling debt still sat in hotspot JS/CSS files.
- The goal of this run was to cut the highest-leverage hardcoding without redesigning the app or removing risky legacy layers prematurely.

## Operational Impact

- No runtime path, database, container, deployment, or BlackLab wiring changed.
- Production remains unaffected because work stays isolated to the non-deploying `template-refactor` branch.
- Live styling behavior should remain stable while being more closely tied to canonical CSS tokens.

## Compatibility Notes

- `app/static/css/branding.css` remains deprecated legacy and inactive.
- `app/static/css/md3/tokens-legacy-shim.css` remains loaded because untouched live callers still depend on legacy token names.
- Some nearby modules still carry inline style usage and will require later targeted cleanup.

## Follow-up

- Continue migrating remaining safe `--md3-*` callers.
- Reduce `player-mobile.css` override density in controlled slices.
- Finish adjacent search/stats inline-style cleanup without broad UI rewrites.