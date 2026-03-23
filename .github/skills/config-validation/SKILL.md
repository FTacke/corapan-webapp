---
name: config-validation
description: "Use when validating environment variables, compose files, runtime paths, deployment config, BlackLab wiring, or conflicting configuration sources in corapan-webapp."
---

# Config Validation Skill

## Use This Skill When

Use this skill whenever a task involves any of the following:
- environment variables
- database configuration
- BlackLab or BLS configuration
- compose-file selection
- runtime path selection
- deployment configuration
- conflicting config sources across compose, scripts, code, and docs
- workspace-root versus repo/deploy-root selection
- local root `.github` versus versioned deploy workflow truth

This skill is mandatory for config questions and for any change that could otherwise rely on guessed defaults.

## Do Not Use When

Do not use this skill for:
- isolated implementation changes with no config, environment, path, or source-of-truth impact
- purely presentational UI work with no runtime or config implications
- historical documentation cleanup where no current config decision is involved

## Required Check Order

1. live operational reality if observable
2. canonical compose and startup scripts for the affected environment
3. src/app/config/__init__.py and other config code
4. affected implementation code
5. documentation as context
6. legacy files only for classification

This skill exists to stop agents from guessing configuration.

## Purpose

Determine:
- which config source is canonical
- which variables are active
- which names are deprecated
- whether dev and prod are cleanly separated
- whether live runtime disagrees with code or docs
- whether the task is governed by local workspace setup or versioned deploy setup

## Validation Order

1. live operational reality if observable
2. canonical compose and startup scripts
3. application config code
4. documentation
5. legacy files

When implementation code adds extra runtime wiring beyond config code, inspect that code before trusting documentation.

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

Conflicts must be classified explicitly, not resolved by assumption.

Default local classifications unless live runtime disproves them:
- `CORAPAN/`: active workspace root
- `app/`: active versioned app/deploy repo
- `CORAPAN/.github`: active local agent-governance layer
- `CORAPAN/.github/workflows`: active versioned deploy/CI layer
- `app/data`: legacy or dangerous for local runtime assumptions
- `app/runtime`: legacy or dangerous for local runtime assumptions

BlackLab-specific validation rules:
- a real hits query is stronger evidence than `/blacklab-server/` readiness
- if valid hits return 500, check active mounts and container logs for `InvalidIndex` or `CorruptIndexException` before blaming field logic
- do not treat a successful build log as proof that the active index is safe to serve

## Required Output

For each conflicting config source, classify it as:
- active
- legacy
- dangerous
- redundant

The output must also state which source won and why, using the required check order.