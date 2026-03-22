# Dev Auth And Atlas Robustness

Date: 2026-03-20
Scope: local development startup, auth initialization, and optional atlas degradation
Change type: local-dev robustness fix

## What Changed

- changed the canonical local dev auth DSN in dev helper scripts from `postgresql+psycopg` to `postgresql+psycopg2`
- made the Flask app refuse to continue when auth initialization fails, instead of starting in a half-initialized state
- added an early auth schema check for the required `users` table to stop late login 500s caused by an unmigrated local DB
- added a PostgreSQL readiness wait loop to `scripts/dev-start.ps1`
- made atlas country-stat access return an empty list when optional local SQLite files are missing
- updated the dev scripts to prefer sibling `../data` and `../media` directories when they exist next to `webapp/`, with repo-local `runtime/corapan` kept as fallback
- updated local-dev documentation to match the fixed local startup path

## Why It Changed

Local development was starting with an auth DSN that required the `psycopg` driver, while the checked-in dev environment had `psycopg2` installed.
That caused auth initialization to fail during app startup, but the development app continued running, so the failure only surfaced later as a login 500.

Atlas local data is optional and should not break the app in dev when local side databases or metadata are absent.

## Affected Files

- src/app/__init__.py
- src/app/services/atlas.py
- scripts/dev-start.ps1
- scripts/dev-setup.ps1
- docs/operations/local-dev.md
- startme.md

## Operational Impact

- local dev now uses the PostgreSQL driver that is actually present in the checked-in environment
- auth misconfiguration or missing driver now fails early at startup instead of producing delayed login 500s
- missing local atlas country DBs now degrade to empty responses in dev
- local dev now resolves data and media against the real workspace layout when `C:\dev\corapan\data` and `C:\dev\corapan\media` exist beside `webapp`

## What Was Not Changed

- production compose wiring
- production deployment scripts
- BlackLab query logic
- auth schema or migration execution
- optional atlas metadata behavior in production

## Follow-Up

- review remaining local dev docs that still mention the old psycopg DSN format
- review other optional atlas and side-database call sites for the same degrade-cleanly pattern if more local 500s appear