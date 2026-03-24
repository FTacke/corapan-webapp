# 2026-03-24 Phase 4 Template Harmonization

## What Changed

- Introduced live canonical auth-family wrappers in:
	- `app/templates/_md3_skeletons/auth_login_skeleton.html`
	- `app/templates/_md3_skeletons/auth_profile_skeleton.html`
- Introduced a live canonical text-page wrapper in `app/templates/_md3_skeletons/page_text_skeleton.html`.
- Introduced a live canonical dashboard wrapper in `app/templates/_md3_skeletons/page_admin_skeleton.html`.
- Migrated the matching live auth/text/admin pages to those wrappers.
- Replaced the landing page's page-local shell suppression with a reusable drawerless shell variant.
- Moved `app/static/css/player-mobile.css` out of the global base shell and into the player/editor pages that actually own that hotspot.
- Tightened `player-mobile.css` around current live player selectors and removed clearly stale mobile-sidebar blocks.
- Updated the template master plan and future-agent runtime map.

## Why It Changed

- Repeated page scaffolding was still bypassing the skeleton layer, which made page families harder to understand and maintain.
- The landing page still depended on a page-local shell override instead of a reusable shell primitive.
- `player-mobile.css` was globally loaded even though only player/editor pages needed it, increasing layout risk outside that runtime.

## Affected Scope

- Environment scope: local versioned application layer under `app/`
- Governance scope: template-plan and future-agent guidance under `docs/` and `.github/`
- Runtime impact: shared page-family structure and shell/layout ownership only; no intended auth, search, player, or editor behavior changes

## Operational Impact

- Auth/text/admin dashboard families now have an explicit canonical extension path.
- Landing shell behavior is easier to reuse and reason about.
- Mobile player overrides have narrower load scope and clearer ownership.

## Compatibility Notes

- Specialized pages remain specialized where runtime structure still justifies it.
- Deprecated token layers remain unchanged.
- Player/editor mobile behavior was contained, not redesigned.

## Legacy Paths Intentionally Kept

- `app/static/css/md3/tokens-legacy-shim.css` remains loaded.
- `app/static/css/branding.css` remains classified legacy.
- `app/templates/pages/player_overview.html` and `app/templates/pages/editor_overview.html` remain transitional direct-shell pages for now.
- `app/templates/search/advanced.html` remains a specialized direct-shell page.

## Follow-Up Notes

- Next cleanup should focus on transitional overview pages and the `player-mobile.css` / `audio-player.css` boundary.
- Any later attempt to unify player/editor overview pages should be based on proven shared structure, not wrapper enthusiasm.
- Skeleton wrapper pages now pass family metadata through explicit template variables instead of runtime block lookups. This avoids render-time regressions in the `proyecto` text-page family and the same latent failure mode in auth pages.