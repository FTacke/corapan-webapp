# Agent Workflow for CORAPAN Root

Use this file for root-level work. The active repository rules live in `.github/`; this file is only the short root contract.

## Ownership

- `CORAPAN/.github` is the active governance and workflow layer
- `CORAPAN/app` is the versioned application and deploy implementation
- if a task touches both, keep the boundary explicit

## Decision Order

When sources disagree, use this order:

1. live operational reality
2. canonical environment files and `app/src/app/config/__init__.py`
3. affected implementation or workflow code
4. documentation
5. legacy material

Documentation is context, not truth.

## Canonical Paths

Development:

- `docker-compose.dev-postgres.yml`
- `scripts/dev-setup.ps1`
- `scripts/dev-start.ps1`

Production:

- `app/infra/docker-compose.prod.yml`
- `app/scripts/deploy_prod.sh`
- `.github/workflows/*.yml`

## Hard Rules

- `AUTH_DATABASE_URL` is the only valid auth/core database variable
- `BLS_BASE_URL` is the canonical BlackLab base URL variable
- `BLS_CORPUS` must always be explicit
- PostgreSQL is required for auth and core data
- do not introduce new SQLite auth/core flows
- do not make CI cosmetically green with `echo`, `continue-on-error`, or `|| true`
- do not start containers, run deployments, or run migrations without explicit approval

## Required Reads

Before changing CI, governance, runtime wiring, or deployment-adjacent files, inspect:

1. the relevant `.github/workflows/*.yml`
2. `app/src/app/config/__init__.py`
3. the relevant scripts under `scripts/` or `app/scripts/`
4. the affected implementation
5. `docs/changes/`, `docs/adr/`, and `docs/ci_fix/` as context

## Documentation

- use `docs/changes/` for implementation-facing repository changes
- use `docs/adr/` for policy or architecture decisions
- use `docs/ci_fix/` only for current CI stabilization state, not as a dump for every run