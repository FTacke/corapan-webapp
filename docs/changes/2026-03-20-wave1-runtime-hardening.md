# Wave 1 Runtime Hardening

Date: 2026-03-20
Scope: shared runtime, auth-adjacent helpers, active dev helpers, and four high-risk docs
Change type: governance-aligned safety hardening

This change implements Wave 1 of the cleanup plan.

It removes silent fallback behavior in scoped files without changing production wiring, deployment flow, container topology, or data.

## What Changed

- required `BLS_CORPUS` explicitly in the canonical app config and BlackLab HTTP client
- removed implicit `BLS_CORPUS=index` behavior from shared runtime and active dev helper paths
- removed active `DATABASE_URL` fallback for auth/core startup in `scripts/docker-entrypoint.sh`
- removed SQLite fallback behavior from scoped auth/core helpers
- made auth-adjacent helpers fail fast unless `AUTH_DATABASE_URL` is explicitly set to PostgreSQL
- switched active dev helpers to treat `BLS_BASE_URL` as the canonical primary variable
- kept `BLACKLAB_BASE_URL` only as a legacy compatibility mirror in the active dev helpers
- aligned the four highest-risk docs with the technical behavior

## Why It Changed

The repository governance requires:
- explicit `BLS_CORPUS`
- `AUTH_DATABASE_URL` as the only auth/core database variable
- no SQLite fallback for auth/core data
- `BLS_BASE_URL` as the canonical BlackLab base URL variable

The scoped files still contained silent fallback paths that could lead to wrong runtime behavior or wrong operator guidance.

## Affected Files

- src/app/config/__init__.py
- src/app/extensions/http_client.py
- scripts/docker-entrypoint.sh
- scripts/apply_auth_migration.py
- scripts/create_initial_admin.py
- scripts/reset_user_password.py
- scripts/dev-start.ps1
- scripts/dev-setup.ps1
- README.md
- docs/architecture/configuration.md
- docs/operations/local-dev.md
- docs/blacklab/blacklab_deployment.md

## What Was Intentionally Not Changed

- infra/docker-compose.prod.yml
- scripts/deploy_prod.sh
- .env.example
- passwords.env
- production compose wiring
- deploy behavior
- container execution
- data or database state
- alternate dev-path cleanup
- BlackLab build or index logic
- broad documentation harmonization outside the four scoped docs

## Operational Impact

- missing `BLS_CORPUS` now fails fast instead of silently targeting a guessed corpus
- auth/core helper scripts now require explicit PostgreSQL wiring via `AUTH_DATABASE_URL`
- active dev helper scripts now export `BLS_CORPUS=corapan` explicitly for the canonical dev stack

## Follow-Up For Later Waves

- align alternate dev paths and convenience targets with the canonical dev workflow
- clean up production-adjacent legacy variable duplication where safe
- classify and narrow overlapping setup documentation beyond the four highest-risk sources