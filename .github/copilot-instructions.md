# corapan Agent Rules

This repository uses a strict source-of-truth model based on operational reality.

## Workspace vs Deploy Boundary

`CORAPAN/.github` is now the active versioned governance and workflow layer for the root repository.

`app/` is the versioned application/deploy implementation subtree inside the root repository.
The workspace and repository root is `CORAPAN/`.

## Priority Order

When runtime, config, code, and docs disagree, use this order:

1. The live operational environment that is currently running
2. The canonical environment files for that environment and src/app/config/__init__.py
3. The affected implementation code
4. Documentation
5. Legacy scripts and historical notes

Documentation is context, not truth.

Agents must prioritize observable runtime behavior and canonical config over stale code comments or documentation.

## Anti-Guess Rule

When required information is missing, ambiguous, or contradictory:
- inspect runtime and canonical config first
- inspect the relevant implementation code next
- ask the user if the answer is still unclear
- never invent a default to make progress

This rule is mandatory for environment selection, database wiring, BlackLab wiring, runtime paths, and deployment behavior.

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

Before changing anything relevant to runtime, configuration, scripts, auth, BlackLab, or deployment, agents must inspect:
- the matching compose or environment file for the affected environment
- src/app/config/__init__.py
- the relevant operational script or helper
- related documentation only as supporting context

For local dev/runtime path questions, interpret these canonical paths from the local workspace root `CORAPAN/`, not from `app/`.

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

Local canonical BlackLab dev structure:
- `data/blacklab/index`
- `data/blacklab/export`
- `data/blacklab/backups`
- `data/blacklab/quarantine`

Treat these as mutable operational runtime state, not as harmless static files.

Legacy or non-canonical local paths such as `app/data`, `app/runtime`, `data/blacklab_index`, and `data/blacklab_export` must never be treated as equal to the canonical dev BlackLab tree unless explicitly reclassified after inspection.

Hard BlackLab safety rules:
- never rebuild or replace the active BlackLab index while `blacklab-server-v3` is serving it
- never assume root HTTP readiness proves the mounted index is healthy
- after BlackLab rebuild/start work, require a real hits query, not only `/blacklab-server/`
- if BlackLab returns HTTP 500 for a valid hits query, inspect container logs for `InvalidIndex`, `CorruptIndexException`, mount mistakes, or active-index corruption before changing CQL, BLF, or app logic
- verify the active mount source, not only the presence of files on disk

## High-Risk Areas

The following areas require explicit validation before any change:
- BLS_CORPUS: no default, never guessed, must be explicitly verified
- AUTH_DATABASE_URL: the only valid auth and core database variable
- DATABASE_URL: legacy only, never a new auth or core source of truth
- SQLite: allowed only for public stats and documented side databases
- Dev vs Prod separation: never mix defaults, scripts, docs, or workflow assumptions across environments
- workspace-root vs deploy-root selection: never confuse `CORAPAN/` with `app/`
- BlackLab active-index handling: never modify the active mounted index in parallel with a serving container

If a task touches any high-risk area, agents must validate the affected environment and canonical config before proposing or making a change.

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

If these sources disagree, classify the conflict explicitly as active, legacy, dangerous, or redundant before editing.

Required local path classifications unless runtime proves otherwise:
- `CORAPAN/` workspace root: active for local agent/runtime setup and versioned repository root
- `app/`: active versioned app/deploy implementation
- `app/data`: legacy or dangerous for local dev runtime assumptions
- `app/runtime`: legacy or dangerous for local dev runtime assumptions
- `CORAPAN/.github`: active local agent setup and active versioned deploy/CI setup

## Dev and Prod Separation

Keep development and production strictly separate.
- no implicit cross-environment defaults
- no mixed setup instructions
- no production behavior hidden inside dev helpers
- no dev convenience fallback treated as production-safe

Always state whether a change applies to dev, prod, or both.

Always also state whether the change applies to:
- local workspace governance under `CORAPAN/.github`
- versioned application/deploy implementation under `app/`
- or both

## CI and Test Integrity

The root CI source of truth is `.github/workflows/`.

Agents must not make CI cosmetically green.
Forbidden examples:
- replacing a real failing check with `echo`
- using `|| true` on required quality checks
- adding `continue-on-error` to required gates without an explicit policy decision

Required CI behavior:
- keep the fast path deterministic and service-free whenever feasible
- classify localhost, external-service, browser, BlackLab, and large-data tests explicitly as `live`, `e2e`, or `data` instead of letting them leak into the default fast suite
- keep PostgreSQL as the required auth/core database for CI flows that validate auth or core app startup
- do not introduce SQLite auth/core shortcuts just to simplify CI
- preserve strict config requirements, but do not enforce them at module import time if that breaks Python import, test collection, or service-free CI validation
- for auth hash support, prefer focused compatibility coverage over a full-suite matrix when the product behavior is compatibility-oriented rather than algorithm-specific across the entire app
- if warnings are filtered in CI or pytest config, the filter must be narrow, justified, and used only for known third-party noise after repo-owned warnings have been fixed

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

If the conflict is between the local workspace layer and the versioned deploy layer, keep both layers explicit and do not collapse them by assumption.

## File Placement Rules

Operational helper and maintenance scripts belong in scripts/.
Do not add ad-hoc operational scripts outside scripts/.

## Documentation Rules

Every non-trivial change must be documented.
Use:
- docs/changes/ for implementation-facing changes
- docs/adr/ for architecture and policy decisions

If a change touches runtime config, BlackLab config, database behavior, deployment behavior, or canonical workflow selection, documentation is mandatory.