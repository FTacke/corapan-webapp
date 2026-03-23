---
description: "Use when editing migrations, SQL, SQLAlchemy usage, database config, auth database scripts, PostgreSQL behavior, or SQLite side-database handling in corapan-webapp."
applyTo: "app/migrations/**/*.sql,app/scripts/**/*.py,app/src/**/*.py,app/tests/**/*.py"
---

# Database Rules

## Canonical Policy

PostgreSQL is required for:
- auth
- users
- application core state
- all new stateful backend features

SQLite is allowed only for:
- public stats
- explicitly documented non-critical side databases

SQLite is forbidden for auth and core data.

## Canonical Variable

AUTH_DATABASE_URL is the only valid variable for auth and core database access.

DATABASE_URL is legacy.
- Do not add new uses of DATABASE_URL.
- Do not base new migrations or scripts on DATABASE_URL.
- If an existing legacy file still uses it, classify the usage before changing it.

## Migration Safety

Never run migrations unless the user explicitly asks.
Never add migration logic that silently chooses SQLite for auth.
Never make auth/core migrations depend on fallback engines.

## Review Checklist

When touching DB-related code, verify:
1. which environment is affected
2. whether auth and core data remain PostgreSQL-only
3. whether SQLite use stays confined to allowed side cases
4. whether docs/changes or docs/adr must be updated