# Template Architecture Lock

## Summary

Phase 2 locked the active template architecture around three explicit authorities:

- branding in `app/src/app/branding.py`
- tokens in `app/static/css/md3/tokens.css` and `app/static/css/app-tokens.css`
- layout shell in `app/templates/base.html`

## Implemented

- Added centralized page-title formatting and shell asset filenames to branding config.
- Routed live template titles through `format_page_title(...)`.
- Removed nested `main` landmarks from live templates and reusable skeletons.
- Removed hardcoded shell theme-color/background values from `base.html`.
- Updated runtime theme JS to derive browser theme color from CSS tokens.
- Classified `app/static/css/branding.css` as legacy and `tokens-legacy-shim.css` as deprecated compatibility.
- Moved stats chart theming away from an independent JS palette toward CSS-token resolution.

## Not Removed Yet

- The legacy token shim stays active until all live `--md3-*` callers are migrated.
- Existing page-specific layout overrides remain for a later controlled cleanup pass.

## Rationale

This pass favors architectural control over broad visual churn. The goal was to stop further divergence, make ownership explicit, and reduce the most harmful shell/token/branding violations without risking runtime regressions.