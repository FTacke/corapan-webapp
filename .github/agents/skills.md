### Template System Learnings (Phase 1)

- Forbidden: introducing a second branding authority in templates, CSS, or JS when a value already belongs in a shared branding config.
- Forbidden: adding new `block title` page titles. The active shell uses `block page_title`.
- Forbidden: treating `app/static/css/branding.css` as live without first classifying and wiring it deliberately.
- Forbidden: page-specific shell overrides as the default solution. Do not add new `body[data-page]` layout exceptions unless the shell contract is proven insufficient and the exception is documented.
- Forbidden: nested `<main>` elements inside templates rendered within `app/templates/base.html`.
- Forbidden: new JS chart palettes or UI colors hardcoded as hex values when CSS tokens already exist.
- Forbidden: using inline `style=` output from JS for reusable UI states when a component class can express the same behavior.

- Correct pattern: branding text for app name, footer identity, canonical external brand links, and default meta text belongs in `app/src/app/branding.py` and is exposed through template context.
- Correct pattern: foundation tokens live in `app/static/css/md3/tokens.css`, app semantics live in `app/static/css/app-tokens.css`, and components should consume those tokens rather than inventing their own palette.
- Correct pattern: the base shell in `app/templates/base.html` owns header, navigation drawer, main container, and footer. Pages should provide content, not redefine shell landmarks.
- Correct pattern: page families should converge on shared skeletons or macros before adding more custom structure.
- Correct pattern: when hardcoded values are unavoidable as fallbacks, classify them explicitly and keep them isolated from canonical styling.

- Anti-pattern example: auth templates used `block title` while the live base template used `block page_title`.
- Anti-pattern example: `app/static/css/branding.css` defines brand-token mappings but is not loaded by the active base template.
- Anti-pattern example: `app/static/js/modules/stats/theme/corapanTheme.js` hardcodes chart palettes instead of consuming CSS token values.
- Anti-pattern example: `app/static/css/md3/components/index.css` and `app/static/css/player-mobile.css` rely on shell-fighting overrides rather than stronger shared layout primitives.
- Anti-pattern example: many templates render `<main>` inside the content block even though `app/templates/base.html` already renders the page main landmark.

### Template System Rules (Phase 2)

- Branding authority is locked to `app/src/app/branding.py`. Add new app identity values there and expose them via template context.
- Document titles must be built with `format_page_title(...)`. Do not manually append `CO.RA.PAN`, separators, or alternate app names in templates.
- `app/templates/base.html` is the only live shell. Pages and skeletons must not emit nested `main` landmarks.
- Active token authority is limited to `app/static/css/md3/tokens.css` and `app/static/css/app-tokens.css`.
- `app/static/css/branding.css` is classified legacy, not active. Do not reconnect it casually.
- `app/static/css/md3/tokens-legacy-shim.css` is deprecated compatibility only. No new `--md3-*` usage is allowed.
- JS theming must read CSS custom properties instead of maintaining a separate palette.
- If a page appears to need shell-specific layout fixes, strengthen shared shell/layout primitives first. Page-local shell hacks are the exception, not the rule.