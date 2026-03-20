---
name: maintenance-script
description: "Use when creating or editing helper, admin, repair, audit, or operational scripts under scripts/ in corapan-webapp."
---

# Maintenance Script Skill

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