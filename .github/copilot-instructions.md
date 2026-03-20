# corapan-webapp Agent Rules

This repository uses a strict source-of-truth model based on operational reality.

## Operational Truth Order

When code, docs, and runtime disagree, use this order:

1. The live operational environment that is currently running
2. The canonical environment files for that environment
3. Application config code
4. Documentation
5. Legacy scripts and historical notes

Agents must prioritize real runtime behavior over stale code comments or documentation.

## Canonical Environment Paths

Development source of truth:
- docker-compose.dev-postgres.yml
- scripts/dev-setup.ps1
- scripts/dev-start.ps1

Production source of truth:
- infra/docker-compose.prod.yml
- scripts/deploy_prod.sh
- server-side passwords.env as an operator-managed secret source

Do not treat alternative compose files or older setup paths as equal unless the user explicitly says so.

## Database Rules

PostgreSQL is mandatory for:
- auth
- users
- core application data
- all new stateful backend features

SQLite is allowed only for:
- public stats databases
- explicitly documented non-critical side databases
- existing read-only supporting data stores already used by the application

SQLite is forbidden for:
- auth
- user management
- login flows
- password reset flows
- new core features
- silent fallbacks when PostgreSQL is missing

Never introduce or restore SQLite fallback behavior for auth or core data.

## Database Variables

AUTH_DATABASE_URL is the only valid variable for auth and core database access.

DATABASE_URL is legacy.
- Do not introduce it in new code, docs, scripts, compose files, or migrations.
- Do not switch existing auth or core flows back to DATABASE_URL.
- If existing legacy files still mention DATABASE_URL, classify that usage before changing it.

## BlackLab Rules

BLS_BASE_URL is the canonical BlackLab base URL variable.

BLACKLAB_BASE_URL is deprecated.
- Agents must not introduce new uses of BLACKLAB_BASE_URL.
- Existing occurrences should be treated as legacy compatibility until deliberately cleaned up.

BLS_CORPUS is mandatory and must always be set explicitly.
- No default is allowed.
- Never assume or infer a value such as index.
- If BLS_CORPUS is unclear, inspect the live environment or ask the user.

Agents must never guess BlackLab configuration.

## Config Discipline

Do not invent parallel configuration systems.
Use the existing runtime and deployment configuration as the authority for each environment.

If a required variable is unclear, inspect first or ask.
This applies especially to:
- AUTH_DATABASE_URL
- BLS_BASE_URL
- BLS_CORPUS
- CORAPAN_RUNTIME_ROOT
- CORAPAN_MEDIA_ROOT

## Dev and Prod Separation

Keep development and production strictly separate.
- no implicit cross-environment defaults
- no mixed setup instructions
- no production behavior hidden inside dev helpers
- no dev convenience fallback treated as production-safe

Always state whether a change applies to dev, prod, or both.

## Service and Deployment Safety

Unless the user explicitly asks for it, agents must not:
- start or stop containers
- run deploy scripts
- run database migrations
- run admin bootstrap scripts
- run password reset scripts
- perform destructive git actions such as reset, rebase, or force-checkout

Inspection is preferred over execution.

## passwords.env Rule

passwords.env remains part of the production setup.

Agents may:
- read passwords.env when necessary to understand the current production wiring

Agents must never:
- create or modify passwords.env
- rotate secrets inside passwords.env
- treat passwords.env as a general-purpose editable config file

## Legacy and Inconsistency Handling

Do not automatically delete conflicting paths, variables, or scripts.

If multiple ways exist:
1. determine what is actually used
2. treat that path as the standard
3. classify alternatives as legacy, dangerous, or redundant
4. do not delete them automatically

## File Placement Rules

Operational helper and maintenance scripts belong in scripts/.
Do not add ad-hoc operational scripts outside scripts/.

## Documentation Rules

Every non-trivial change must be documented.
Use:
- docs/changes/ for implementation-facing changes
- docs/adr/ for architecture and policy decisions

If a change touches runtime config, BlackLab config, database behavior, deployment behavior, or canonical workflow selection, documentation is mandatory.