# Phase 2 Architecture Lock

## Scope

- Environment scope: local versioned application layer under `app/`
- Governance scope: repository rules and future-agent guidance under `.github/`
- Runtime goal: lock ownership boundaries without changing product behavior

## Locked Decisions

### Branding

- `app/src/app/branding.py` is now the single template-facing branding authority.
- The branding layer now owns page-title formatting, contact addresses, external project URLs, and shell asset filenames.
- Live templates were moved off hardcoded branding literals for drawer logos, footer assets, favicon, and canonical external contact/project links.

### Tokens

- Active token authority remains split only across:
  - `app/static/css/md3/tokens.css` for foundation roles
  - `app/static/css/app-tokens.css` for app semantics
- `app/static/css/branding.css` was explicitly classified as deprecated legacy, not live authority.
- `app/static/css/md3/tokens-legacy-shim.css` remains loaded as a deprecated compatibility layer because live code still requests legacy `--md3-*` names.

### Layout Shell

- `app/templates/base.html` remains the only shell that renders the main landmark.
- Live auth/content pages and reusable skeletons were updated to remove nested `main` landmarks.
- This turns the shell rule from guidance into an enforceable structural contract.

### Theme Runtime

- `app/templates/base.html` no longer hardcodes theme-color meta hex values or inline light/dark background approximations.
- `app/static/js/theme.js` now synchronizes `meta[name="theme-color"]` from canonical CSS tokens.
- Runtime chart theming was moved toward CSS-token resolution in stats JS instead of a separate JS color system.

## Concrete Changes Applied

- Expanded `app/src/app/branding.py` with title formatting and shell asset filenames.
- Exposed `format_page_title` through `app/src/app/__init__.py`.
- Replaced live template title suffix hardcoding with `format_page_title(...)`.
- Replaced live shell asset filename literals in footer, drawer, landing logo, and favicon usage.
- Removed nested `main` landmarks from auth pages, static pages, dashboard/overview pages, and reusable skeleton templates.
- Marked token authority/deprecation boundaries directly in the relevant CSS files.
- Updated stats theme JS to resolve colors from CSS variables.

## Known Deferred Items

- `app/static/css/md3/components/index.css`, `player.css`, and related page-level override files still need a later shell/layout cleanup pass.
- The legacy token shim cannot be removed yet because live JS/CSS callers still request `--md3-*` variables.
- Some content text still contains legitimate product-name mentions; only title/authority hardcoding was targeted here.

## Outcome

- Branding ownership is explicit.
- Title generation is centralized.
- The base shell is the only live layout landmark owner.
- Token authority is documented and constrained.
- Deprecated layers are classified without unsafe deletion.