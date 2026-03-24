# Template Customization

Use this document when adapting the repository as a template.

## Brand Identity

Change branding in one place:

- `app/src/app/branding.py`

That file owns the app name, title formatting, footer identity, repository links, and other shared branding values.

## Visual System

The active design system is:

- foundation tokens: `app/static/css/md3/tokens.css`
- app semantic tokens: `app/static/css/app-tokens.css`
- shared shell/layout: `app/static/css/layout.css` and `app/static/css/md3/layout.css`

Do not add a second token file or a second shell.

## Template Structure

- `app/templates/base.html` is the only shell
- reuse the `_md3_skeletons/` templates before creating a new page wrapper
- keep search, player, and editor pages specialized unless you have a proven shared replacement

## Feature Decisions

Optional modules live in the application code and can be removed deliberately:

- search and BlackLab integration
- analytics
- player and transcript tooling

If you remove a feature, remove its route, template usage, docs references, and related scripts together.

## Runtime and Deploy Adjustments

Review these values early when adapting the template:

- `AUTH_DATABASE_URL`
- `BLS_BASE_URL`
- `BLS_CORPUS`
- `CORAPAN_RUNTIME_ROOT`
- `CORAPAN_MEDIA_ROOT`

See `docs/operations/local-dev.md`, `docs/operations/production.md`, and `docs/blacklab/README.md` before changing them.