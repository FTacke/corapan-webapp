---
name: change-documentation
description: "Use when a code, config, runtime, deployment, or workflow change in corapan-webapp must be documented in docs/changes or docs/adr."
---

# Change Documentation Skill

Use this skill when a change affects behavior, operations, configuration, database rules, deployment behavior, or canonical workflow selection.

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