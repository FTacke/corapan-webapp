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

BlackLab production config discipline:
- for the current root-lifted production checkout layout, the versioned BlackLab config directory is `/srv/webapps/corapan/app/app/config/blacklab`
- do not assume `/srv/webapps/corapan/app/config/blacklab` is the active production config path; treat it as stale or dangerous unless live runtime proves otherwise
- if DEV search works and PROD search fails, compare live DEV vs PROD mounts and `/etc/blacklab` contents before changing app/backend code

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

## Local Sync Lane Discipline

When editing or reviewing:
- `app/scripts/deploy_sync/**`
- `maintenance_pipelines/_2_deploy/**`
- `docs/rsync/**`

you must also apply the `server-sync-production-lanes` skill.

Required assumptions for that area:
- repo-bundled cwRSync plus bundled `ssh.exe` is the live-validated standard rsync path
- `scp -O` remains a required fallback
- `tar|ssh` is not a standard large-file transport
- Data, Media, and BlackLab lanes must remain explicit and separate

Before removing a fallback, deleting a legacy sync artifact, or changing transport/guard behavior in that area, you must first:
- run the refactored Data and Media task entry points in dry-run
- if transport or guards changed, run at least one isolated live transfer under `/srv/webapps/corapan/tmp_sync_test/`
- verify the JSON summary contract still holds

Do not classify a legacy sync artifact as removable until the refactored standard path has been proven stable in practical validation.