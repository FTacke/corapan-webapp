# Agent Workflow for corapan-webapp

This repository expects a strict workflow for all agents.

## Mandatory Priority Chain

When sources disagree, use this order and do not skip steps:

1. live operational reality
2. canonical config for the affected environment, including compose and src/app/config/__init__.py
3. relevant implementation code
4. documentation
5. legacy and historical material

Documentation is context, not truth.

If required information is missing or contradictory:
- inspect canonical config and observable runtime first
- inspect implementation code next
- ask the user if uncertainty remains
- never invent defaults or implied values

## Default Order 

1. Read
- inspect the relevant compose file, src/app/config/__init__.py, scripts, implementation code, and docs
- identify the active environment and canonical source of truth

2. Check
- verify whether live operational reality is observable
- classify competing paths as active, legacy, dangerous, or redundant

3. Plan
- define the smallest safe change
- state assumptions explicitly
- ask if environment, database path, deployment path, or BlackLab config is not fully clear

4. Change
- edit only the files required for the task
- do not create new parallel systems
- do not silently rewrite canonical workflow choices

5. Validate
- run the safest relevant validation
- prefer read-only checks first
- do not run migrations, deploys, service restarts, or admin scripts without approval

6. Document
- add or update docs/changes for notable implementation changes
- add or update docs/adr for architectural or policy decisions

No task may skip from Read directly to Change.

## Mandatory Multi-File Checklist

Before any relevant change, the agent must inspect all applicable sources in this checklist:

1. the matching compose or environment file for the target environment
2. src/app/config/__init__.py
3. the relevant operational or helper scripts
4. the affected implementation code
5. the relevant documentation as context only

This checklist is mandatory for:
- config or environment changes
- auth or database work
- BlackLab or BLS work
- runtime path handling
- compose, Docker, deployment, or script work
- source-of-truth or governance changes

If one checklist item is not applicable, the agent must be able to say why.

## Deterministic Task Pattern

Every task must follow this sequence:

1. read multi-file context
2. determine the active reality
3. classify conflicts as active, legacy, dangerous, or redundant
4. formulate the smallest safe plan
5. only then make changes

Direct implementation without these steps is not allowed.

## CI And Test Integrity

- `.github/workflows/*.yml` at the root repository are the active CI truth
- do not make failing CI appear green with `|| true`, placeholder `echo` steps, or hidden `continue-on-error`
- keep the fast path deterministic and service-free whenever possible
- tests that hit localhost services, external systems, browser automation, BlackLab, or large runtime data must be marked and excluded from the default fast pytest selection
- do not restore SQLite auth/core fallbacks just to simplify CI
- preserve strict config requirements, but do not enforce them so early that Python import or pytest collection fails
- when only hash compatibility differs, prefer focused compatibility tests over a full-suite algorithm matrix
- fix repo-owned warnings at the source; only use narrow filters for known third-party warnings

## Repository-Specific Rules

- PostgreSQL is mandatory for auth and core data
- SQLite is allowed only for public stats and documented side databases
- AUTH_DATABASE_URL is the only valid auth/core database variable
- DATABASE_URL is legacy and must not be newly introduced
- BLS_BASE_URL is the canonical BlackLab base URL variable
- BLS_CORPUS must always be explicitly set
- agents must never guess BLS_CORPUS
- dev and prod must stay strictly separated
- scripts/ is the place for operational helper scripts
- passwords.env may be read for analysis but must never be modified
- do not delete legacy paths automatically

## Canonical Operational Paths

Development:
- docker-compose.dev-postgres.yml
- scripts/dev-setup.ps1
- scripts/dev-start.ps1

Production:
- infra/docker-compose.prod.yml
- scripts/deploy_prod.sh

If code or docs disagree with the live environment, prioritize the live environment first.

## Escalation Triggers

Ask the user before proceeding if:
- more than one compose path looks plausible
- database strategy is ambiguous
- BLS_BASE_URL or BLS_CORPUS is unclear
- a change would affect deployment behavior
- a change would start, stop, migrate, reset, or deploy anything stateful
- the mandatory multi-file checklist cannot be completed safely