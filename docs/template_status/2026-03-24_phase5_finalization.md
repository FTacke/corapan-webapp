# Phase 5 Finalization

## 1. Executive Summary

This run closed the remaining high-visibility UI inconsistencies on `template-refactor` without redesigning the app.

Standardized in reusable ways:
- form-adjacent error/message surfaces now use a stronger canonical field/message treatment
- copy actions across auth dialogs, search dialogs, text pages, and player controls now follow one shared visual pattern
- atlas popup header, close affordance, spacing rhythm, and action styling were cleaned up to read like a card/dialog derivative
- dialog spacing was tightened further by shifting generic behavior back toward the canonical dialog component
- mobile player card spacing and token-action alignment were polished with small selector-safe adjustments

Branch assessment after this run:
- the branch now reads as template-ready with known exceptions, not fully exception-free

## 2. Master Plan Update

Updated `docs/template_status/template_master_plan.md` to:
- mark Phase 1 completed
- mark Phase 2 completed
- mark Phase 3 completed
- mark Phase 4 substantially completed
- mark Phase 5 in progress
- add `## Phase 5 Execution Focus`
- tighten `## Definition of Done` around the live shell, token, family-wrapper, dialog/message/action, and hotspot architecture

## 3. UI Consistency Fixes Applied

### Field/message surfaces

Files touched:
- `app/static/css/md3/components/alerts.css`
- `app/static/css/md3/components/auth.css`
- `app/templates/auth/login.html`
- `app/templates/auth/admin_users.html`

Pattern standardized:
- introduced `md3-alert--field` as the reusable form-/dialog-adjacent message surface
- removed auth-local global alert overrides so auth/dialog pages again consume the canonical alert component
- migrated login and edit-dialog errors to the stronger field/message surface treatment

### Copy actions

Files touched:
- `app/static/css/md3/components/dialog.css`
- `app/static/css/md3/components/text-pages.css`
- `app/static/css/md3/components/player.css`
- `app/templates/auth/admin_users.html`
- `app/templates/search/partials/cql_guide_dialog.html`
- `app/templates/pages/corpus_guia.html`
- `app/templates/pages/proyecto_como_citar.html`
- `app/templates/pages/player.html`
- `app/static/js/auth/admin_users.js`
- `app/static/js/modules/search/searchUI.js`
- `app/static/js/pages/corpus-guia.js`
- `app/static/js/pages/como-citar.js`

Pattern standardized:
- introduced a shared `md3-copy-action` / `md3-copy-action--icon` pattern for icon-only and dialog copy actions
- aligned success/error feedback to shared state classes instead of separate per-page button variants
- aligned placement so code/snippet copy controls sit in consistent relation to their content

### Atlas popup

Files touched:
- `app/static/css/md3/components/atlas.css`
- `app/static/js/modules/atlas/index.js`

Pattern standardized:
- popup content now uses a clearer header block with eyebrow + title
- close-button spacing and hit-area were cleaned up through popup-level styling
- popup action links now read more like compact semantic actions instead of isolated marker links

### Dialogs

Files touched:
- `app/static/css/md3/components/dialog.css`
- `app/static/css/md3/components/advanced-search.css`
- `app/templates/search/partials/cql_guide_dialog.html`

Pattern standardized:
- canonical dialog rhythm now carries more of the generic spacing behavior
- advanced search keeps only advanced-specific dialog overrides instead of redeclaring generic dialog structure
- large prompt content now sits more cleanly inside the shared dialog-content/action model

### Player mobile polish

Files touched:
- `app/static/css/player-mobile.css`
- `app/templates/pages/player.html`
- `app/static/css/md3/components/player.css`

Pattern standardized:
- mobile sidebar cards now have cleaner internal spacing and more stable header alignment
- token copy/reset controls use the shared icon-action visual pattern
- token action alignment on mobile is more orderly without altering the player runtime structure

## 4. Reusable Pattern Improvements

Shared helpers/components/classes introduced or tightened:
- `md3-alert--field`
- `md3-copy-action`
- `md3-copy-action--icon`
- stronger canonical dialog content/action rhythm in `dialog.css`
- narrower advanced-search dialog overrides in `advanced-search.css`

Why these are preferable to local fixes:
- the same problems repeated in auth, search, text-page, atlas, and player UI
- the shared patterns are small, readable, and sit inside the existing MD3/token architecture
- they reduce divergent feedback styles and spacing rules without creating a second design-system layer

## 5. Legacy Reduction Status

What legacy usage was removed or reduced:
- removed the separate citation-page icon-button copy pattern in favor of the shared copy-action pattern
- removed auth-local global alert styling overrides that were competing with the canonical alert component
- reduced duplicate generic dialog rules in `advanced-search.css`

What still remains:
- `app/static/css/md3/tokens-legacy-shim.css`
- remaining legacy `--md3-*` callers, especially documented in `app/static/css/md3/components/datatables.css`, `app/static/css/md3/components/forms.css`, and `app/static/js/main.js` (`--md3-mobile-menu-duration`)
- inactive `app/static/css/branding.css`
- player-local `copy-snackbar` and `tooltip-text-pop` behavior in specialized player JS

Shim removal status:
- full shim removal is still blocked and is not safe yet

Branding legacy status:
- `branding.css` remains more explicitly quarantined by policy and by active non-use; it was not removed in this run because removal would be a cleanup-only change rather than a required template-readiness fix

## 6. Final Template-Readiness Review

### Strengths

- branding authority is centralized and live
- title formatting is centralized and live
- shell/layout authority is centralized and live
- canonical token authority is limited to the intended files
- auth/text/admin page families now have real live wrappers
- dialog, message, and copy-action behavior are more consistent and reusable than in earlier phases
- landing-page shell behavior is now a reusable shell variant rather than a one-page shell hack

### Exceptions

- `app/templates/search/advanced.html` remains a specialized runtime page
- `app/templates/pages/player.html` and `app/templates/pages/editor.html` remain specialized runtime pages
- `app/templates/pages/player_overview.html` and `app/templates/pages/editor_overview.html` remain transitional overview pages
- atlas popup still depends on Leaflet popup mechanics and should be treated as a popup/card derivative rather than a fully generic dialog component

### Technical debt

Acceptable for now:
- `app/static/css/player-mobile.css` remains dense but is now scoped and better contained
- player-local snackbar/tooltip helpers remain localized to specialized player runtime code
- inactive `branding.css` remains present but quarantined and out of the live pipeline

Should eventually be addressed:
- remaining `--md3-*` callers so `tokens-legacy-shim.css` can be removed safely
- clearer ownership between `player-mobile.css` and `app/static/css/md3/components/audio-player.css`
- transitional player/editor overview pages

### Final verdict

- template-ready with known exceptions

Justification:
- the shared architectural model is now real, not aspirational
- the remaining issues are concentrated in explicit specialized runtime hotspots rather than spread across the whole template layer
- the remaining exceptions are important to document, but they no longer block responsible reuse of the template architecture

## 7. Agent-Learning Update

Updated `.github/agents/skills.md` to add/refine:
- the final template runtime map
- the final template rules
- explicit reusable dialog/message/action pattern ownership
- deprecated layers still present
- final hotspot warnings for player, search, atlas, editor, and legacy-token files

## 8. Recommended Next Actions

1. Finish migration of remaining live `--md3-*` callers before attempting token-shim removal.
2. Clarify the ownership boundary between `app/static/css/player-mobile.css` and `app/static/css/md3/components/audio-player.css`.
3. Revisit player/editor overview pages only if a genuinely shared overview wrapper can be proven.