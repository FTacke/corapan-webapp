# 2026-03-24 Template Audit Safe Wins

## Scope

- Environment: shared app templates and UI metadata
- Layer: `app/` implementation plus root agent-governance documentation

## What Changed

- Added `app/src/app/branding.py` as a template-facing branding source for shared identity values.
- Injected branding values into Jinja context from `app/src/app/__init__.py`.
- Updated the active base template to use shared branding for the default browser title and default meta description.
- Replaced hardcoded branding values in the top app bar, footer, landing-page alt text, and auth/search page titles.
- Normalized auth templates to the active `page_title` block contract.

## Why

- The audit found branding text duplicated across templates and a title-block mismatch between auth templates and the active base shell.
- These were low-risk fixes that improve consistency without changing layout, auth flow, or runtime wiring.

## Operational Impact

- No runtime path, auth database, BlackLab, deploy, or container behavior changed.
- Browser metadata and shared branding strings are now easier to adapt from one place.

## Compatibility Notes

- `app/static/css/branding.css` remains inactive and was intentionally not wired into the live template to avoid an unreviewed visual change.
- Existing logo asset filenames remain unchanged.

## Follow-up

- Remove or deliberately integrate the inactive parallel branding CSS layer.
- Migrate remaining title suffix literals and JS chart palettes to the final template system.
