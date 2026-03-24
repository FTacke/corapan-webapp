# Agent Workflow for CORAPAN Root

This file governs work at the workspace and repository root.

Root workflow and governance truth lives in `CORAPAN/.github`.
Application implementation truth lives in `CORAPAN/app`.

If a task touches both layers, agents must keep the boundary explicit and state which layer they are changing.

## Priority Chain

When sources disagree, use this order:

1. live operational reality
2. canonical environment files and `app/src/app/config/__init__.py`
3. affected implementation or workflow code
4. documentation
5. legacy or historical material

Documentation is context, not truth.

## Root CI Integrity Rules

- `.github/workflows/*.yml` is the active CI and deploy truth for the root repository
- do not make CI look green by replacing real checks with `echo`, `continue-on-error`, `|| true`, or placeholder steps
- fast CI must stay service-free and deterministic whenever possible
- tests that require localhost servers, external services, BlackLab, browser automation, or large runtime data must be marked and kept out of default fast pytest selection
- auth and core-data CI must use PostgreSQL, not SQLite fallbacks
- strict required-config validation is allowed at app-config load time or at feature use, but must not break Python import or pytest collection
- repo-owned CI warnings should be fixed at the source; third-party warnings may be filtered only narrowly and explicitly
- full-suite algorithm matrices are not a substitute for focused compatibility coverage; prefer targeted tests when only compatibility behavior differs

## Required Read Order For CI Changes

Before changing CI, tests, runtime wiring, or agent governance, inspect:

1. `.github/workflows/*.yml` relevant to the task
2. `app/src/app/config/__init__.py`
3. relevant scripts under `scripts/` or `app/scripts/`
4. affected tests and implementation code
5. `docs/ci_fix/`, `docs/changes/`, and `docs/adr/` as context

## Documentation Requirements

When a CI or governance change is real and non-trivial, update:

- `docs/changes/` for implementation-facing behavior
- `docs/adr/` for workflow or policy decisions
- `docs/ci_fix/` for audit and repair history when the work is part of CI stabilization

## Escalation Triggers

Ask before proceeding if:

- a change would start containers, run migrations, or perform deployment work
- a test cannot be made deterministic without changing product behavior
- the correct CI owner layer is ambiguous between root governance and app implementation
- BlackLab state, auth database wiring, or runtime root selection is unclear