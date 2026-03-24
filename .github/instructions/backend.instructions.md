---
description: "Use when editing Flask app code, auth, runtime path handling, BlackLab integration, routes, services, or backend behavior in corapan-webapp."
applyTo: "app/src/**/*.py,app/templates/**/*.html,app/static/**/*.js,app/static/**/*.css"
---

# Backend Rules

Work from the operational source of truth.

Canonical development path:
- docker-compose.dev-postgres.yml
- scripts/dev-setup.ps1
- scripts/dev-start.ps1

Canonical production path:
- infra/docker-compose.prod.yml
- scripts/deploy_prod.sh

Before changing backend behavior:
1. inspect src/app/config/__init__.py
2. inspect the canonical environment file for the affected environment
3. verify whether the behavior is dev-only, prod-only, or shared

## Auth and Core Data

Auth and core application state must use PostgreSQL via AUTH_DATABASE_URL.
Do not add SQLite-based auth logic.
Do not add automatic fallback behavior when AUTH_DATABASE_URL is missing.
Do not introduce DATABASE_URL for auth or core flows.

## BlackLab

Use BLS_BASE_URL as the only standard base URL variable.
Treat BLACKLAB_BASE_URL as legacy.

BLS_CORPUS must always be set explicitly.
Do not add a default.
Do not assume index or any other corpus name.
If the active corpus is unclear, inspect the live setup or ask.

When BlackLab returns HTTP 500 for a valid hits query:
1. inspect container logs first
2. check for `InvalidIndex`, `CorruptIndexException`, file mismatch, or mount/source mistakes
3. verify the active mounted index source
4. only then consider CQL, BLF, or backend query logic changes

Root endpoint or generic health success is weaker evidence than a real hits query.

## Runtime Paths

Treat CORAPAN_RUNTIME_ROOT and CORAPAN_MEDIA_ROOT as explicit runtime boundaries.
Do not bypass them with new repo-local shortcuts for production behavior.
Dev-only convenience behavior must stay explicitly dev-only.

For local dev analysis, `CORAPAN/` is the workspace root and `app/` is the versioned app/deploy repo.
Do not treat `app/data` or `app/runtime` as canonical local runtime roots unless runtime evidence proves otherwise.

## Legacy Awareness

This repository contains legacy docs, scripts, and parallel setup traces.
Do not assume every existing file represents the current standard.
Classify competing paths before editing.

For homepage/index layout regressions, prefer page-local fixes in `app/static/css/md3/components/index.css` before changing shared app-shell or global MD3 layout primitives.
Respect the existing MD3 card and surface composition; only change shared layout rules when the issue is proven to affect multiple pages.