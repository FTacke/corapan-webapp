# Agent Workflow for corapan-webapp

This repository expects a strict workflow for all agents.

## Default Order

1. Read
- inspect the relevant code, config, compose file, script, and docs
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