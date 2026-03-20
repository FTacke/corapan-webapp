---
description: "Use when editing Flask app code, auth, runtime path handling, BlackLab integration, routes, services, or backend behavior in corapan-webapp."
applyTo: "src/**/*.py,templates/**/*.html,static/**/*.js,static/**/*.css"
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

## Runtime Paths

Treat CORAPAN_RUNTIME_ROOT and CORAPAN_MEDIA_ROOT as explicit runtime boundaries.
Do not bypass them with new repo-local shortcuts for production behavior.
Dev-only convenience behavior must stay explicitly dev-only.

## Legacy Awareness

This repository contains legacy docs, scripts, and parallel setup traces.
Do not assume every existing file represents the current standard.
Classify competing paths before editing.