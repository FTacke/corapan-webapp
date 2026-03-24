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

### Final Template Runtime Map

- Branding authority: `app/src/app/branding.py`.
- Title formatting path: `format_page_title(...)` in `app/src/app/branding.py`, exposed through `app/src/app/__init__.py`.
- Shell authority: `app/templates/base.html`.
- Shared shell/layout primitives: `app/static/css/layout.css` and `app/static/css/md3/layout.css`.
- Canonical token authority:
	- foundation tokens: `app/static/css/md3/tokens.css`
	- semantic app tokens: `app/static/css/app-tokens.css`
- JS theme access path: `app/static/js/modules/core/themeTokens.js`, consumed by runtime theming and token-aware JS modules.
- Canonical page-family sources:
	- auth access pages: `app/templates/_md3_skeletons/auth_login_skeleton.html`
	- auth account/admin pages: `app/templates/_md3_skeletons/auth_profile_skeleton.html`
	- text/static/project pages: `app/templates/_md3_skeletons/page_text_skeleton.html`
	- admin/dashboard pages: `app/templates/_md3_skeletons/page_admin_skeleton.html`
	- landing page: `app/templates/pages/index.html` with `shell_class = 'app-shell--drawerless'`
	- search runtime: `app/templates/search/advanced.html` remains specialized
	- player/editor runtime: `app/templates/pages/player.html` and `app/templates/pages/editor.html` remain specialized
- Reusable dialog/message/action patterns:
	- dialogs and snippets: `app/static/css/md3/components/dialog.css`
	- message/error surfaces: `app/static/css/md3/components/alerts.css`
	- auth/dialog field integration: `app/static/css/md3/components/auth.css`
	- text-page code/copy presentation: `app/static/css/md3/components/text-pages.css`
	- atlas popup/card styling: `app/static/css/md3/components/atlas.css`
- Deprecated or legacy layers still present:
	- `app/static/css/branding.css` — deprecated legacy file, not active token authority
	- `app/static/css/md3/tokens-legacy-shim.css` — deprecated compatibility layer, still required by remaining legacy callers
	- remaining legacy `--md3-*` callers are transitional only and must be treated as migration debt, not standards
- Runtime ownership boundaries to keep explicit:
	- `app/static/css/player-mobile.css` is loaded only by player/editor pages
	- `app/static/css/md3/components/audio-player.css` and player runtime JS remain coupled to specialized transcript/audio behavior

### Template System Rules (Phase 3)

- No new hex color literals outside canonical token files.
- No new inline visual styling in templates or JS when a token-backed class or CSS variable can express the same state.
- JS must read CSS token authority; do not define independent UI palettes in JS.
- Prefer `app/static/js/modules/core/themeTokens.js` for CSS-variable reads instead of ad hoc `getComputedStyle` copies.
- Page CSS must not bypass shell/layout contracts unless the shell contract is proven insufficient and the exception is documented.
- Legacy `--md3-*` names are transitional only. Do not introduce new callers.
- When touching a hotspot file, reduce repeated literal values and redundant overrides before inventing a new abstraction.

### Final Template Rules

- No new hardcoded visual literals outside canonical token files.
- No new local dialog spacing hacks when shared dialog patterns can carry the change.
- Copy and clipboard actions must follow the canonical copy-action pattern used by dialogs, snippets, text pages, and player controls.
- Atlas popup header, close-button spacing, and action links must follow shared card/dialog rhythm rather than ad hoc marker UI styling.
- Message and error surfaces near forms or dialogs should use canonical alert/message patterns, not one-off banners.
- Page CSS must not bypass shell/layout contracts; strengthen shared shell primitives first.
- Player, editor, and search runtime pages remain specialized and must be changed carefully.
- Legacy `--md3-*` usage remains transitional only. Do not add new callers.
- Do not reconnect `app/static/css/branding.css` to the live pipeline without explicit reclassification.
- Do not remove `app/static/css/md3/tokens-legacy-shim.css` until the remaining live `--md3-*` callers are proven gone.

### Page Family Rules

- Auth pages must not rebuild their own hero-plus-page shell. Use:
	- `app/templates/_md3_skeletons/auth_login_skeleton.html` for login/reset/request-access flows
	- `app/templates/_md3_skeletons/auth_profile_skeleton.html` for account/admin-auth flows
- Text-heavy pages must use `app/templates/_md3_skeletons/page_text_skeleton.html` unless they have a verified structural reason not to.
- Dashboard/admin overview pages should prefer `app/templates/_md3_skeletons/page_admin_skeleton.html` when they fit the hero-plus-section pattern.
- `app/templates/search/advanced.html` is a deliberate exception because its tabbed search runtime is page-specific.
- `app/templates/pages/player.html` and `app/templates/pages/editor.html` are deliberate exceptions because they own transcript/audio/editor runtime structure.
- `app/templates/pages/player_overview.html` and `app/templates/pages/editor_overview.html` remain transitional specialized overview pages; do not force them into an unrelated wrapper without proving the structure is truly shared.

### Layout Rules

- `app/templates/base.html` is authoritative for header, drawer, main, footer, and shell wiring.
- Reusable shell variants belong in shared layout primitives, not page-local CSS files.
- New shell behavior should be introduced through `app/static/css/layout.css` or `app/static/css/md3/layout.css` first.
- Page CSS must not recreate drawer/grid/body shell behavior when a shared primitive can carry it.
- `body[data-page]` selectors are exceptions, not the default mechanism for layout control.
- If a page needs to suppress the standard drawer, prefer a reusable shell class like `app-shell--drawerless` over a page-specific shell override.

### Template System Rules (Phase 4)

- When a skeleton exists but live pages still bypass it, either migrate the live family to it or classify that skeleton as non-authoritative.
- Prefer family wrappers that remove repeated page scaffolding over generic macros that hide real structure.
- Keep player/editor, search, and landing exceptions explicit. Do not normalize them by force.
- Keep `player-mobile.css` scoped to player/editor ownership and reduce stale selectors before adding new overrides.
- Do not reintroduce global page-specific CSS for behavior that now lives in shared shell/layout primitives.

### Final Hotspot Warnings

- `app/static/css/player-mobile.css`: still the densest override hotspot; keep edits narrow, behavior-preserving, and limited to live selectors.
- `app/static/css/md3/components/audio-player.css`: still tightly coupled to player/editor runtime behavior and should be changed with the mobile player in mind.
- `app/templates/pages/player.html` and `app/templates/pages/editor.html`: specialized runtime pages; do not force them into generic wrappers.
- `app/templates/pages/player_overview.html` and `app/templates/pages/editor_overview.html`: still transitional overview pages; harmonize only with a proven shared structure.
- `app/templates/search/advanced.html` and `app/static/js/modules/search/searchUI.js`: specialized search runtime; avoid casual dialog/state rewrites or new inline-state workarounds.
- `app/static/js/modules/advanced/formHandler.js` and `app/static/js/modules/advanced/initTable.js`: advanced-search stateful modules; keep visual changes class-based and low risk.
- `app/static/js/modules/atlas/index.js` and `app/static/css/md3/components/atlas.css`: popup/card derivative in transition; preserve Leaflet behavior while refining structure.
- `app/static/js/player/modules/tokens.js` and `app/static/js/player/modules/ui.js`: still contain player-local copy/snackbar/tooltip patterns that should be treated carefully.
- `app/static/css/md3/components/editor.css`: still contains compatibility and legacy color rules; treat as structurally risky.
- `app/static/css/md3/components/datatables.css` and `app/static/css/md3/components/forms.css`: still documented legacy `--md3-*` callers; do not assume the shim is removable while these remain.