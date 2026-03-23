---
description: "Use when editing Docker, compose files, deployment scripts, environment-variable wiring, runtime paths, operational docs, or deployment-related config in corapan-webapp."
applyTo: "app/Dockerfile,app/docker-compose*.yml,app/infra/**/*.yml,app/scripts/**/*.sh,app/scripts/**/*.ps1,.github/workflows/**/*.yml,docs/**/*.md,app/.env.example,app/passwords.env.template"
---

# DevOps Rules

## Workspace vs Deploy Boundary

`CORAPAN/.github` is now both:

- the local workspace governance layer
- the active versioned CI/deploy truth for the root repository

## Canonical Environment Files

Development:
- docker-compose.dev-postgres.yml
- scripts/dev-setup.ps1
- scripts/dev-start.ps1

For local dev questions, these are interpreted from the `CORAPAN/` workspace root.

Production:
- infra/docker-compose.prod.yml
- scripts/deploy_prod.sh
- passwords.env as operator-managed secret input

Treat other operational paths as legacy, dangerous, or redundant unless explicitly reclassified.

For local runtime-path analysis, classify these by default unless live runtime disproves it:
- `CORAPAN/data/...`: active local runtime tree
- `app/data`: legacy or dangerous for local runtime assumptions
- `app/runtime`: legacy or dangerous for local runtime assumptions

## Safety Boundaries

Do not start or stop services without explicit approval.
Do not run deploy scripts without explicit approval.
Do not run admin bootstrap or password reset scripts without explicit approval.
Do not run migrations without explicit approval.
Do not use destructive git commands in deployment contexts.

## Config Discipline

Do not introduce parallel config systems.
Prefer aligning docs and scripts to the existing operational truth.

Canonical variables:
- AUTH_DATABASE_URL for auth/core database access
- BLS_BASE_URL for BlackLab base URL
- BLS_CORPUS as an explicit required variable

Deprecated variables:
- DATABASE_URL for auth/core access
- BLACKLAB_BASE_URL as a standard base URL variable

BlackLab dev path discipline:
- canonical local BlackLab tree is `data/blacklab/{index,export,backups,quarantine}`
- do not treat `data/blacklab_index`, `data/blacklab_export`, `app/data`, or `app/runtime` as equal alternatives without explicit reclassification
- verify active mount sources, not just file existence
- health or root readiness alone does not prove the active index is readable
- after rebuild/start, require a real hits query
- if valid hits return 500, inspect logs for `InvalidIndex` or `CorruptIndexException` before changing app logic

## passwords.env

passwords.env is part of the production setup.
It may be read for analysis, but must never be modified by an agent.

## Documentation Discipline

Any change to:
- compose topology
- environment variables
- runtime paths
- deployment flow
- database policy
- BlackLab configuration policy
requires documentation updates.

For workflow and governance changes under `CORAPAN/.github`, document whether they affect local agent behavior, versioned CI/deploy behavior, or both.