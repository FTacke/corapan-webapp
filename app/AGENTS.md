# Agent Workflow for corapan-webapp

This is the short app-level contract. Detailed governance lives in `.github/copilot-instructions.md` and the matching `.github/instructions/*.md` files.

## Decision Order

When sources disagree, use this order:

1. live operational reality
2. canonical config for the affected environment, including compose and `src/app/config/__init__.py`
3. affected implementation code
4. documentation
5. legacy material

## Canonical Paths

Development:

- `../docker-compose.dev-postgres.yml`
- `../scripts/dev-setup.ps1`
- `../scripts/dev-start.ps1`

Production:

- `infra/docker-compose.prod.yml`
- `scripts/deploy_prod.sh`

## Hard Rules

- PostgreSQL is mandatory for auth and core data
- `AUTH_DATABASE_URL` is the only valid auth/core database variable
- `DATABASE_URL` is legacy
- `BLS_BASE_URL` is canonical
- `BLS_CORPUS` must always be explicit
- `CORAPAN_RUNTIME_ROOT` and `CORAPAN_MEDIA_ROOT` are required runtime boundaries
- do not add new repo-local runtime shortcuts
- do not run migrations, deploys, password resets, or container state changes without approval

## Required Reads

Before changing config, auth, BlackLab, runtime paths, scripts, or deployment files, inspect:

1. the matching compose or environment file
2. `src/app/config/__init__.py`
3. the relevant script or helper
4. the affected implementation
5. the relevant docs as context

## Documentation

- use `../docs/changes/` for notable implementation-facing changes
- use `../docs/adr/` for policy or architecture changes