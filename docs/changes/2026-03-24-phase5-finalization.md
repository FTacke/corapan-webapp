# Phase 5 Finalization

## Scope

Environment scope: local versioned application/template layer under `app/` and local agent governance under `.github/`.

This run closed the remaining high-visibility template-refactor gaps without redesigning the application.

## What Changed

- updated `docs/template_status/template_master_plan.md` to mark Phase 1-3 completed, Phase 4 substantially completed, and Phase 5 in progress
- tightened the master plan Definition of Done around the now-live shell, token, page-family, and dialog/message/action architecture
- standardized form-adjacent message surfaces through a reusable `md3-alert--field` pattern in `app/static/css/md3/components/alerts.css`
- removed auth-local alert overrides in `app/static/css/md3/components/auth.css` so auth and dialog error surfaces consume the canonical alert component again
- tightened reusable dialog rhythm and added a canonical `md3-copy-action` pattern in `app/static/css/md3/components/dialog.css`
- moved text-page citation/copy UI to the shared copy-action pattern in `app/static/css/md3/components/text-pages.css`
- reduced duplicate generic dialog rules in `app/static/css/md3/components/advanced-search.css` so advanced search keeps only advanced-dialog-specific overrides
- cleaned up atlas popup header/spacing/close-button/action styling in `app/static/css/md3/components/atlas.css` and `app/static/js/modules/atlas/index.js`
- aligned visible copy actions in:
  - `app/templates/auth/admin_users.html`
  - `app/templates/search/partials/cql_guide_dialog.html`
  - `app/templates/pages/corpus_guia.html`
  - `app/templates/pages/proyecto_como_citar.html`
  - `app/templates/pages/player.html`
- aligned copy feedback behavior in:
  - `app/static/js/auth/admin_users.js`
  - `app/static/js/modules/search/searchUI.js`
  - `app/static/js/pages/corpus-guia.js`
  - `app/static/js/pages/como-citar.js`
- applied a small behavior-safe mobile player polish in `app/static/css/player-mobile.css`
- updated `.github/agents/skills.md` with the final runtime map, template rules, and hotspot warnings

## Why

Phase 4 made the family architecture mostly canonical, but the branch still had visible inconsistencies in:

- auth and dialog error/message surfaces
- copy and clipboard actions
- dialog content rhythm
- atlas popup presentation
- mobile player card/control alignment

These were the remaining visible issues most likely to undermine template-readiness despite the architecture already being in place.

## Operational Impact

- no runtime path, database, auth storage, BlackLab wiring, or deployment behavior changed
- runtime behavior for auth, search, atlas, player, and editor flows was preserved
- the work is limited to shared CSS/JS/UI behavior and documentation on `template-refactor`

## Compatibility Notes

- `app/static/css/md3/tokens-legacy-shim.css` is still required; shim removal remains blocked by legacy `--md3-*` callers and `--md3-mobile-menu-duration`
- `app/static/css/branding.css` remains inactive legacy and was intentionally not reconnected
- player-local copy/snackbar and tooltip helpers still exist in specialized runtime JS and remain documented hotspots rather than being force-abstracted at the end of the branch

## Follow-up / Rollback Notes

- if a Phase 5 UI regression appears, first inspect the shared patterns in `alerts.css`, `dialog.css`, `text-pages.css`, `atlas.css`, and `player-mobile.css` before patching page-local CSS
- do not remove the token shim or quarantine files opportunistically; the remaining blockers are still explicit and live