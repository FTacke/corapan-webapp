# Agent Structure Hardening

Date: 2026-03-20
Scope: repository steering structure only
Change type: instructions, agent workflow, and skill-trigger hardening

This change strengthens the repository control surface used by VS Code and Copilot.

It does not change:
- runtime behavior
- deployment topology
- database schema or migration state
- application code paths
- container behavior

## What Changed

- sharpened the source-of-truth priority chain in .github/copilot-instructions.md and AGENTS.md
- added an explicit rule that documentation is context, not truth
- added an explicit anti-guess rule for missing or conflicting information
- made the multi-file pre-change checklist mandatory in AGENTS.md and the repository-specific agent
- strengthened high-risk handling for BLS_CORPUS, AUTH_DATABASE_URL, DATABASE_URL, SQLite boundaries, and dev versus prod separation
- added explicit use, non-use, and check-order sections to repository skills
- made config-validation mandatory for config-sensitive tasks

## Why It Changed

The repository already had strong governance rules, but several of them were distributed across files and still left room for:
- implicit defaults
- inconsistent instruction priority
- incomplete multi-file context gathering
- missed skill activation
- silent conflict resolution by assumption

This hardening makes the behavior more deterministic across Copilot and agent workflows.

## Affected Files

- .github/copilot-instructions.md
- AGENTS.md
- .github/agents/corapan-code-agent.agent.md
- .github/skills/change-documentation/SKILL.md
- .github/skills/config-validation/SKILL.md
- .github/skills/maintenance-script/SKILL.md
- .github/skills/postgres-migration/SKILL.md

## Operational Impact

- agents must inspect compose, config, scripts, implementation code, and docs before relevant changes
- agents must classify source conflicts explicitly as active, legacy, dangerous, or redundant
- agents must ask instead of inventing defaults when required information is unclear
- config-sensitive tasks should load config-validation more reliably

## Compatibility Notes

- existing architecture and runtime policy remain unchanged
- existing canonical paths remain unchanged
- existing deprecated-path handling remains classification-first, not deletion-first

## Follow-Up

- repository instruction files under .github/instructions/ can remain as-is unless later task-specific gaps are observed
- future agent or skill additions should follow the same use, non-use, and check-order pattern