# Phase 4 Template Harmonization

## 1. Executive Summary

This run made the live page-family layer more canonical without redesigning the product UI.

Harmonized:
- auth pages now flow through live auth-family skeletons instead of each page rebuilding the same hero and page shell
- static and long-form text pages now flow through a live text-page skeleton
- the admin dashboard now uses a live dashboard skeleton
- the landing page shell exception was moved into a reusable drawerless shell variant
- `player-mobile.css` is now owned only by player/editor pages instead of the global shell

Still exceptional:
- `app/templates/search/advanced.html` remains a specialized search runtime page
- `app/templates/pages/player.html` and `app/templates/pages/editor.html` remain specialized runtime pages
- `app/templates/pages/player_overview.html` and `app/templates/pages/editor_overview.html` remain partially transitional overview pages
- `app/static/css/player-mobile.css` remains a brittle hotspot even after scope reduction and selector cleanup

## 2. Master Plan Update

Updated `docs/template_status/template_master_plan.md` to:
- mark Phase 3 as substantially completed
- mark Phase 4 as in progress
- add `Phase 4 Execution Focus`
- add explicit Phase 4 working rules around family wrappers, shell authority, and hotspot containment

The plan now reflects the live architecture more accurately:
- shell ownership remains in `app/templates/base.html`
- shell variants can be expressed through reusable layout primitives
- Phase 4 is about structural variance reduction, not a design refresh

## 3. Page Family Harmonization

Families improved and their current canonical sources:

- Auth access pages:
	- canonical source: `app/templates/_md3_skeletons/auth_login_skeleton.html`
	- live pages now using it: `auth/login.html`, `auth/password_forgot.html`, `auth/password_reset.html`

- Auth account/admin pages:
	- canonical source: `app/templates/_md3_skeletons/auth_profile_skeleton.html`
	- live pages now using it: `auth/account_profile.html`, `auth/account_password.html`, `auth/account_delete.html`, `auth/admin_users.html`

- Static and long-form text pages:
	- canonical source: `app/templates/_md3_skeletons/page_text_skeleton.html`
	- live pages now using it: `pages/privacy.html`, `pages/impressum.html`, `pages/corpus_guia.html`, `pages/proyecto_overview.html`, `pages/proyecto_diseno.html`, `pages/proyecto_quienes_somos.html`, `pages/proyecto_como_citar.html`, `pages/proyecto_referencias.html`

- Admin/dashboard pages:
	- canonical source: `app/templates/_md3_skeletons/page_admin_skeleton.html`
	- live page now using it: `pages/admin_dashboard.html`

What divergence was reduced:
- repeated hero-card scaffolding across auth pages
- repeated text-page hero and text-container scaffolding across static/project/search-guide pages
- redundant direct extension of `base.html` in page families that already had a clear shared structure

## 4. Layout Override Reduction

Reduced override patterns:
- the landing page no longer hides the drawer via an index-only shell hack in `index.css`
- shell suppression for the landing page now uses a reusable `app-shell--drawerless` variant through shared layout primitives
- `index.css` now focuses on landing-page content spacing instead of shell control
- `player-mobile.css` is no longer globally loaded by `base.html`

Reusable primitives or structure that replaced page-specific behavior:
- `shell_class = 'app-shell--drawerless'` in `pages/index.html`
- shared desktop shell behavior in `app/static/css/layout.css`
- family wrappers in `_md3_skeletons/` for auth/text/admin-dashboard pages

## 5. Player/Mobile Hotspot Containment

Cleanups applied:
- `app/static/css/player-mobile.css` is now loaded only by `pages/player.html` and `pages/editor.html`
- obvious live selectors were retargeted toward current `md3-player-*` structure where safe
- dead or legacy-only mobile sidebar/metadata blocks were removed where no live template usage remained
- some remaining rules now explicitly support both legacy and current player selectors during the transition

What remains brittle:
- the audio-player mobile stack still has dense `!important` usage
- player and editor share parts of the mobile runtime while still carrying some structural divergence
- `app/static/css/md3/components/audio-player.css` and `app/static/css/player-mobile.css` still need a later ownership review before any deeper reduction

Why it remains brittle:
- the mobile player is still behavior-sensitive and tied to transcript/audio runtime state
- a broader rewrite would carry unnecessary regression risk for player/editor flows

## 6. Skeleton / Partial Authority

Reusable structures that are now actually canonical:
- `app/templates/_md3_skeletons/auth_login_skeleton.html`
- `app/templates/_md3_skeletons/auth_profile_skeleton.html`
- `app/templates/_md3_skeletons/page_text_skeleton.html`
- `app/templates/_md3_skeletons/page_admin_skeleton.html`

What remains intentionally weaker or specialized:
- `search/advanced.html` because its tabbed runtime and advanced-search flow are page-specific
- `pages/player.html` and `pages/editor.html` because they own transcript/audio/editor runtime structure
- `pages/player_overview.html` and `pages/editor_overview.html` because they are still transitional and do not yet share enough stable structure to justify forced unification

## 7. Agent-Learning Update

Updated `.github/agents/skills.md` to add or refine:
- a practical template runtime map
- canonical page-family sources
- layout rules that prefer shared shell primitives over page-local shell hacks
- explicit Phase 4 rules for skeleton authority and exception handling
- hotspot warnings that reflect the new live ownership boundaries

## 8. Remaining Priority Work

1. Harmonize `player_overview.html` and `editor_overview.html` only after proving a shared overview structure that is not weaker than the current live pages.
2. Continue shrinking `app/static/css/player-mobile.css` and clarify the boundary with `app/static/css/md3/components/audio-player.css`.
3. Reassess `search/advanced.html` for a possible specialized search-family wrapper that does not interfere with its runtime behavior.
4. Audit remaining direct `base.html` page families for any other repeated scaffolding that now has a stable wrapper candidate.
5. Continue migration away from legacy `--md3-*` callers before any shim-removal attempt.