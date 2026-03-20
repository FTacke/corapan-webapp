---
description: "Use when editing Docker, compose files, deployment scripts, environment-variable wiring, runtime paths, operational docs, or deployment-related config in corapan-webapp."
applyTo: "Dockerfile,docker-compose*.yml,infra/**/*.yml,scripts/**/*.sh,scripts/**/*.ps1,.github/workflows/**/*.yml,docs/**/*.md,.env.example,passwords.env.template"
---

# DevOps Rules

## Canonical Environment Files

Development:
- docker-compose.dev-postgres.yml
- scripts/dev-setup.ps1
- scripts/dev-start.ps1

Production:
- infra/docker-compose.prod.yml
- scripts/deploy_prod.sh
- passwords.env as operator-managed secret input

Treat other operational paths as legacy, dangerous, or redundant unless explicitly reclassified.

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