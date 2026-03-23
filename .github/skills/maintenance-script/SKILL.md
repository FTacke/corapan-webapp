---
name: maintenance-script
description: "Use when creating or editing helper, admin, repair, audit, or operational scripts under scripts/ in corapan-webapp."
---

# Maintenance Script Skill

## Use This Skill When

Use this skill when creating, editing, reviewing, or classifying scripts under scripts/ that perform helper, admin, repair, audit, migration-adjacent, or operational tasks.

## Do Not Use When

Do not use this skill for:
- application runtime code outside scripts/
- compose-only or deployment-only changes with no script impact
- pure documentation updates with no script behavior involved

## Required Check Order

1. identify whether the script is dev-only, prod-only, or shared
2. inspect the matching canonical compose or startup path
3. inspect src/app/config/__init__.py if the script touches config or auth
4. inspect the script's direct consumers and related docs
5. classify any conflicting behavior before editing

All operational helper scripts belong under scripts/.

## Hard Rules

- do not place operational scripts outside scripts/
- do not create scripts that silently modify production state
- do not add hidden service start, stop, migration, or reset behavior
- require explicit inputs for destructive or stateful actions

## Repository-Specific Checks

- auth and core data must stay PostgreSQL-only
- AUTH_DATABASE_URL is the only valid auth/core database variable
- DATABASE_URL must not be newly introduced
- BLS_BASE_URL is the canonical BlackLab base URL variable
- BLS_CORPUS must be explicit and never guessed
- environment assumptions must be explicit
- dev and prod behavior must not be mixed
- documentation must be updated for new long-lived scripts
- conflicting paths or variables must be classified as active, legacy, dangerous, or redundant before the script is changed

Additional BlackLab operational checks:
- treat `data/blacklab/index` as mutable runtime state, not as a harmless file tree
- never design a rebuild flow that writes or swaps the active index while BlackLab is serving it
- validate canonical local roots from `CORAPAN/`, not from `app/`, unless runtime proves otherwise
- after BlackLab rebuild/start work, require a real hits query, not only root HTTP readiness
- if script behavior depends on a mounted index, verify the active mount source instead of only checking local file existence