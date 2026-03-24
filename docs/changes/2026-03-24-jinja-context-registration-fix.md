# 2026-03-24 Jinja Context Registration Fix

## What Changed

- made `register_context_processors(app)` idempotent in `app/src/app/__init__.py`
- made `register_blueprints(app)` ensure the standard Jinja context helpers are registered before template rendering

## Why

The production app already exposed `format_page_title(...)` and the shared branding helpers through `create_app()`. The CI failure came from test fixtures that built bare Flask apps, registered blueprints, and rendered templates without calling `register_context_processors(app)`.

That caused template rendering failures such as:

- `jinja2.exceptions.UndefinedError: 'format_page_title' is undefined`
- 500 responses for routes like `/privacy` in blueprint-based test apps

## Affected Scope

- shared Flask app registration for blueprint-based test apps
- template rendering in tests and other non-factory app assembly paths

## Operational Impact

- no production config or runtime contract changed
- `create_app()` behavior stays the same
- manually assembled Flask apps that call `register_blueprints(app)` now receive the same standard Jinja helpers as the main app factory

## Compatibility Notes

- the registration is idempotent, so calling `register_context_processors(app)` directly remains safe
- this fix does not change auth, runtime-path, or BlackLab wiring

## Follow-Up

- CI still needs its environment set correctly for tests that import runtime configuration and require explicit `CORAPAN_RUNTIME_ROOT`