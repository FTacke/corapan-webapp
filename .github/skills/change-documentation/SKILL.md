---
name: change-documentation
description: "Use when a code, config, runtime, deployment, or workflow change in corapan-webapp must be documented in docs/changes or docs/adr."
---

# Change Documentation Skill

## Use This Skill When

Use this skill when a change affects behavior, operations, configuration, database rules, deployment behavior, canonical workflow selection, or repository governance.

## Do Not Use When

Do not use this skill for:
- pure read-only analysis with no resulting repository change
- transient debugging notes that will not be committed
- changes that are strictly local scratch work and not part of the repository outcome

## Required Check Order

1. identify what changed or will change
2. determine whether the change affects implementation, policy, or both
3. decide whether docs/changes, docs/adr, or both are required
4. capture environment scope, operational impact, and compatibility notes

## Output Requirements

Create or update:
- a docs/changes entry for implementation-facing impact
- a docs/adr entry when the change alters architecture, policy, or source-of-truth selection

## Must Capture

- what changed
- why it changed
- affected environment
- operational impact
- compatibility notes
- rollback or follow-up notes
- legacy paths intentionally kept

## Repository Policy

Do not leave runtime, database, deployment, or config changes undocumented.
Do not let historical docs become the only record of a new workflow or policy choice.