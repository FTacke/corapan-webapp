# Agent Governance Classification Overview

Date: 2026-03-20
Scope: repository governance, source-of-truth selection, and classification only
Change type: documentation and classification

This document records the current classification of notable setup, config, and workflow paths in corapan-webapp.

It does not perform cleanup, deletion, migration, or behavior changes.

## Active

- docker-compose.dev-postgres.yml
  Canonical development compose path observed in the running local dev stack.

- scripts/dev-setup.ps1
  Canonical development setup script for the local dev workflow.

- scripts/dev-start.ps1
  Canonical daily development start path for the local app workflow.

- infra/docker-compose.prod.yml
  Confirmed production compose path.

- scripts/deploy_prod.sh
  Confirmed production deployment script.

- src/app/config/__init__.py
  Effective application config authority after live runtime and canonical environment files.

- passwords.env in production
  Operator-managed production secret source that remains part of the confirmed prod setup.

- BLS_BASE_URL
  Canonical BlackLab base URL variable under the new governance rules.

- AUTH_DATABASE_URL
  Canonical auth and core database variable under the new governance rules.

## Legacy

- infra/docker-compose.dev.yml
  Plausible development path still present in the repo, but not the canonical or observed dev path.

- README.md references to SQLite fallback for auth or core setup
  Historical narrative that no longer matches the intended governance direction.

- docs/local_runtime_layout.md mixed SQLite and PostgreSQL guidance
  Historical or mixed documentation that is not the canonical rule source.

- BLACKLAB_BASE_URL occurrences in helper scripts
  Deprecated naming retained as legacy compatibility only.

- DATABASE_URL references in old operational or helper contexts
  Legacy variable name that must not be newly introduced.

## Dangerous

- scripts/docker-entrypoint.sh SQLite fallback for auth database initialization
  Conflicts with the PostgreSQL-only rule for auth and core data.

- scripts/apply_auth_migration.py SQLite default path and sqlite engine default
  Can steer auth-related workflows toward a forbidden fallback path.

- scripts/create_initial_admin.py sqlite default when AUTH_DATABASE_URL is absent
  Keeps a prohibited auth fallback path alive.

- scripts/reset_user_password.py sqlite default when AUTH_DATABASE_URL is absent
  Keeps a prohibited auth fallback path alive.

- Defaulting BLS_CORPUS to index in code paths
  Conflicts with the explicit-set-only rule and can cause wrong corpus targeting.

- Parallel use of AUTH_DATABASE_URL and DATABASE_URL in auth or core contexts
  Encourages ambiguity about the real database source of truth.

- Documentation that treats multiple dev paths as equally authoritative
  Makes agent and operator mistakes more likely.

## Redundant

- docker-compose.dev-postgres.yml and infra/docker-compose.dev.yml as parallel dev stack definitions
  Two overlapping development entry points create duplicate operational narratives.

- BLS_BASE_URL and BLACKLAB_BASE_URL as parallel BlackLab base URL names
  One should be canonical, the other only legacy compatibility.

- AUTH_DATABASE_URL and DATABASE_URL for the same auth or core database target
  Duplicate variable concepts for the same responsibility.

- Multiple overlapping setup documents such as README.md, startme.md, docs/index.md, and audit-style docs
  Useful for context, but redundant as sources of truth when they diverge.

## Notes

- The classifications above are intentionally conservative.
- Legacy, dangerous, and redundant items are recorded for governance and future cleanup planning only.
- No file in this document is marked for automatic deletion.