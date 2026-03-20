---
name: config-validation
description: "Use when validating environment variables, compose files, runtime paths, deployment config, BlackLab wiring, or conflicting configuration sources in corapan-webapp."
---

# Config Validation Skill

This skill exists to stop agents from guessing configuration.

## Purpose

Determine:
- which config source is canonical
- which variables are active
- which names are deprecated
- whether dev and prod are cleanly separated
- whether live runtime disagrees with code or docs

## Validation Order

1. live operational reality if observable
2. canonical compose and startup scripts
3. application config code
4. documentation
5. legacy files

## Repository Policy

Canonical variables:
- AUTH_DATABASE_URL for auth/core database access
- BLS_BASE_URL for BlackLab base URL
- BLS_CORPUS as an explicit required variable

Deprecated or suspicious patterns:
- DATABASE_URL for auth/core access
- BLACKLAB_BASE_URL as a standard variable
- implicit BLS_CORPUS defaults
- auth SQLite fallback behavior

## Required Output

For each conflicting config source, classify it as:
- active
- legacy
- dangerous
- redundant