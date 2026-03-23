# Lessons Integrated 2026-03-21

## Purpose

This note records the local workspace-governance updates integrated into `CORAPAN/.github` after the recent CORAPAN dev-stabilization and BlackLab corruption incidents.

## What Was Integrated

### Workspace and Root Model

- `CORAPAN/` is the local workspace root.
- `app/` is the versioned app/deploy implementation subtree.
- local agent governance and versioned workflow truth are both controlled from `CORAPAN/.github`.
- `app/data` and `app/runtime` must not be treated as canonical local runtime roots unless runtime evidence proves otherwise.

### BlackLab Operational Safety

- local canonical BlackLab tree is:
  - `data/blacklab/index`
  - `data/blacklab/export`
  - `data/blacklab/backups`
  - `data/blacklab/quarantine`
- the active BlackLab index is mutable operational state, not a harmless file tree.
- the active index must not be rebuilt or replaced while `blacklab-server-v3` is serving it.
- root HTTP readiness is weaker evidence than a real hits query.
- if valid hits return HTTP 500, inspect logs and active mounts before changing CQL, BLF, or backend logic.

### Operational Lessons Learned

- when BlackLab 500s on valid hits, check container logs first for `InvalidIndex`, `CorruptIndexException`, or file mismatch
- when paths or mounts are changed, verify the active mount source, not only disk file existence
- before activating a rebuilt index, ensure the serving-container state is unambiguous
- do not confuse workspace governance files with versioned deploy truth

## Where The Rules Were Integrated

- `CORAPAN/.github/copilot-instructions.md`
- `CORAPAN/.github/agents/corapan-code-agent.agent.md`
- `CORAPAN/.github/instructions/backend.instructions.md`
- `CORAPAN/.github/instructions/devops.instructions.md`
- `CORAPAN/.github/skills/config-validation/SKILL.md`
- `CORAPAN/.github/skills/maintenance-script/SKILL.md`
- `CORAPAN/.github/skills/blacklab-operational-safety/SKILL.md`
- `CORAPAN/.github/workflows/README.md`

## Binding Rules Now In Force

1. Workspace root and deploy repo root must be classified explicitly before changes.
2. `CORAPAN/.github` controls local agent behavior and the active versioned workflow truth.
3. BlackLab rebuild/start validation must use a real hits query, not just readiness.
4. Active BlackLab index state must not be modified in parallel with a serving container.
5. BlackLab hits-500 on valid queries is an index/mount/corruption hypothesis first, not a query-logic hypothesis first.

## Current State

The root lift is complete.

- `CORAPAN/.github` is versioned as part of the active root repository.
- workflow truth lives under `CORAPAN/.github/workflows`.
- the application implementation lives under `CORAPAN/app/`.