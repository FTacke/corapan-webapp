# Template System Rules

Use this file for the durable template and UI contract. It is intentionally short.

## Authorities

- branding authority: `app/src/app/branding.py`
- shell authority: `app/templates/base.html`
- token authority: `app/static/css/md3/tokens.css` and `app/static/css/app-tokens.css`
- shared layout authority: `app/static/css/layout.css` and `app/static/css/md3/layout.css`

## Hard Rules

- do not introduce a second branding authority in templates, CSS, or JS
- page titles must flow through `format_page_title(...)`
- pages rendered inside `base.html` must not emit nested `main` landmarks
- do not add new hardcoded UI colors outside the canonical token files
- JS must read CSS tokens instead of maintaining its own palette
- do not reconnect `app/static/css/branding.css` without explicit reclassification
- do not add new `--md3-*` callers; `tokens-legacy-shim.css` is compatibility only

## Canonical Page Families

- auth access pages: `app/templates/_md3_skeletons/auth_login_skeleton.html`
- auth account and admin pages: `app/templates/_md3_skeletons/auth_profile_skeleton.html`
- text-heavy pages: `app/templates/_md3_skeletons/page_text_skeleton.html`
- admin dashboards: `app/templates/_md3_skeletons/page_admin_skeleton.html`

Explicit exceptions:

- `app/templates/search/advanced.html`
- `app/templates/pages/player.html`
- `app/templates/pages/editor.html`

## Shared Component Contracts

- dialogs use `md3-dialog__header`, `md3-dialog__content`, and `md3-dialog__actions`
- alerts with icons use `md3-alert__icon` and `md3-alert__content`
- atlas popups should read as header, facts, and action row
- interactive player controls must be real buttons

## Hotspots

- `app/static/css/player-mobile.css`
- `app/static/css/md3/components/audio-player.css`
- `app/static/css/md3/components/editor.css`
- `app/templates/search/advanced.html`
- `app/templates/pages/player.html`
- `app/templates/pages/editor.html`

Keep edits in these files narrow and behavior-preserving.