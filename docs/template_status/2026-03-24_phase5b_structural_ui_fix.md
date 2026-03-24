# Phase 5b Structural UI Consistency Fixes

## 1. Executive Summary

This pass corrected structural UI mismatches that Phase 5 deliberately left alone.

The important distinction:
- this was not a token pass
- this was not a redesign
- this was a markup/CSS/component-contract correction pass

Primary fixes:
- dialog spacing was normalized at the shared component layer instead of with local overrides
- malformed CQL guide dialog nesting was repaired so header, content, and actions now live in the canonical dialog surface
- auth admin edit errors now use the real alert content contract instead of an icon plus loose message node
- atlas popups now render as a semantic popup card with header, fact list, and action row
- player audio controls now use real buttons and player copy feedback no longer depends on icon markup from an unloaded library

## 2. Structural Audit Findings

### Dialog outer whitespace

Root cause:
- the shared dialog component was applying spacing in too many places at once
- `md3-dialog__surface` already defined a shared gap
- `md3-dialog__header`, `md3-dialog__content`, and `md3-dialog__actions` were still adding their own block separation

Effect:
- dialogs looked looser and less deliberate than cards and other shared surfaces
- pages compensated locally instead of trusting the dialog contract

Fix:
- moved dialog rhythm back to the shared surface/content/action contract in `app/static/css/md3/components/dialog.css`
- removed duplicate external spacing from header/content/actions
- made dialog content own an internal stack and zeroed child outer margins
- bound the large dialog variant to a full-width surface so the dialog shell no longer reads much wider than its actual content

### Alert / message structure

Root cause:
- some alert callers used the canonical icon + content wrapper structure
- others used an icon plus a standalone message node

Effect:
- alignment was inconsistent
- shared alert CSS could not reliably assume a content container

Fix:
- normalized the touched admin-user dialog error to `md3-alert__icon + md3-alert__content + md3-alert__message`
- tightened the shared alert contract by zeroing content-child margins in `alerts.css`
- restored correct hidden behavior for alert containers and preserved a visible field-style error surface instead of a nearly white box
- fixed the deeper token-level defect: the active canonical token file lacked `--md-sys-color-error-container` and `--md-sys-color-on-error-container`, so browser dev tools showed the background rule as not applied because the variable was unresolved rather than truly overridden

### Atlas popup structure

Root cause:
- Phase 5 improved popup visuals, but the popup still behaved like a loose collection of rows and links

Effect:
- the popup read as partially standardized instead of as a proper popup card derivative

Fix:
- rebuilt popup inner markup in `app/static/js/modules/atlas/index.js` around:
  - `header`
  - semantic facts block via `dl`
  - action row
- aligned CSS in `app/static/css/md3/components/atlas.css` to the new structure
- removed the redundant `ATLAS` eyebrow and increased the close-button inset and hit area so the popup chrome no longer sticks awkwardly to the corner
- after reviewing `docs/template_status/X.md`, aligned the close control more strictly to the proven Leaflet overlay pattern: transparent background, `30x30px` overlay hit area, `top/right` inset positioning, color-only hover treatment, and header-local end padding instead of reserving the whole popup's right side
- switched the popup action chips from `secondary-container` styling to the stronger `primary` / `on-primary` token pair so icon and label contrast stay clearly legible in the live atlas popup
- tightened the selectors once more to `.atlas-popup a.atlas-tooltip__action` because global anchor-color rules were still winning in the normal state and producing a low-contrast blue-on-blue result outside hover

### Mobile player control and action alignment

Root cause:
- the audio-player macro still used decorative spans/divs for primary controls
- mobile CSS had to compensate for non-semantic structure with very aggressive overrides
- player copy feedback still emitted bootstrap-icon markup even though the player page does not load bootstrap icons

Effect:
- control alignment was more fragile than necessary
- some feedback markup could render incorrectly or inconsistently

Fix:
- converted mute, rewind, play/pause, and forward controls to real buttons in `app/templates/partials/audio-player.html`
- updated shared audio-player CSS to style semantic buttons instead of relying on decorative inline elements
- updated player/editor audio JS to keep icon state via `textContent` and accessible labels instead of swapping icon-library classes
- updated token-copy snackbar output to material-symbol markup and added a live-region status node on the player page
- fixed the button reset rule so Material Symbols still render as icons on the actual player controls

### Text-page copy action placement

Root cause:
- the corpus-guia copy button still sat inside the `pre` element and therefore inside code flow, even though it was visually intended as an overlay action

Effect:
- the floating action could appear to hang in the middle of the code block instead of reading as a deliberate code-block action

Fix:
- moved the button outside the `pre` in `app/templates/pages/corpus_guia.html`
- updated `app/static/css/md3/components/text-pages.css` so the copy button anchors to the copyable block itself rather than to the code text flow
- tightened this once more into a real top-aligned code-block toolbar so the button stays visually attached to the field instead of floating below or beside it

## 3. Files Changed

Application layer:
- `app/static/css/md3/components/dialog.css`
- `app/static/css/md3/components/alerts.css`
- `app/static/css/md3/components/atlas.css`
- `app/static/css/md3/components/audio-player.css`
- `app/static/css/md3/components/player.css`
- `app/static/css/player-mobile.css`
- `app/templates/search/partials/cql_guide_dialog.html`
- `app/templates/auth/admin_users.html`
- `app/templates/partials/audio-player.html`
- `app/templates/pages/player.html`
- `app/static/js/modules/atlas/index.js`
- `app/static/js/player/modules/tokens.js`
- `app/static/js/player/modules/audio.js`
- `app/static/js/editor/audio-player.js`

Governance / docs layer:
- `docs/template_status/template_master_plan.md`
- `.github/agents/skills.md`
- `docs/changes/2026-03-24-phase5-finalization.md`

## 4. Reusable Contracts Clarified

### Dialogs

- `md3-dialog__surface` owns the outer rhythm
- `md3-dialog__content` owns the internal stack
- `md3-dialog__actions` is the only canonical action zone

### Alerts

- icon alerts should use a content wrapper
- `md3-alert__message` is text content, not layout structure

### Atlas popup

- popup internals should read as popup-card content, not as freeform rows
- action links belong to a shared action row, not an ad hoc link cluster

### Player controls

- runtime IDs remain stable
- interactive controls are real buttons
- icon state is updated through material-symbol text content, not icon-library class swaps

## 5. Known Exceptions After Phase 5b

- `app/static/css/player-mobile.css` is still a hotspot and still dense
- player-local `tooltip-text-pop` helper remains a specialized runtime leftover and should still be treated cautiously
- search, player, editor, and atlas remain explicit runtime exceptions even though their touched UI contracts are now cleaner
- `app/static/css/md3/tokens-legacy-shim.css` remains blocked by remaining live legacy callers unrelated to this pass

## 6. Updated Readiness Verdict

Verdict:
- template-ready with narrower, more honestly classified exceptions

Why the verdict improved:
- the remaining inconsistency is no longer primarily caused by fake standardization in the touched dialog/alert/popup/player contracts
- the remaining risks are concentrated in known runtime hotspots, not in the shared component layer that most future reuse depends on