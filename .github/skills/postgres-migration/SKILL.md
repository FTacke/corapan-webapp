---
name: postgres-migration
description: "Use when designing, reviewing, or applying PostgreSQL schema changes for auth or core data in corapan-webapp."
---

# Postgres Migration Skill

This repository uses PostgreSQL for auth and core data.

## Hard Rules

- never introduce SQLite fallback for auth or core migrations
- never run migrations without explicit user approval
- inspect the canonical environment path before changing migration logic
- treat SQLite as out of scope except for documented side databases
- use AUTH_DATABASE_URL as the only valid auth/core database variable
- do not introduce new uses of DATABASE_URL

## Required Checks

1. verify the affected environment
2. verify the target is PostgreSQL
3. verify AUTH_DATABASE_URL remains the canonical variable
4. verify no helper script reintroduces SQLite defaults for auth
5. verify documentation updates are required or not

## Review Focus

Look for:
- fallback behavior
- implicit engine defaults
- schema drift between scripts and compose
- dangerous admin bootstrapping in production paths