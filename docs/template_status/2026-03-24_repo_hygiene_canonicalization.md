# Repo Hygiene and Canonicalization Pass

## 1. Executive Summary

This pass removed duplicated quick-start material, tracked build residue, obsolete migration reports, and stale audit/process documents. The repo now has a smaller canonical documentation set and a clearer dependency/config story.

## 2. Scope

Included:

- repository root hygiene
- dependency and config file consolidation
- documentation canonization
- removal of obsolete migration and process artifacts
- agent-guidance cleanup

Excluded:

- `maintenance_pipelines/`

## 3. Inventory Findings

Root files:

- canonical: `README.md`, `AGENTS.md`, `.github/`, `scripts/`, `docker-compose.dev-postgres.yml`
- rewritten: repo README and agent contract
- removed: duplicated quick-start and tracked build residue

Dependency and config files:

- kept: `requirements.in`, `requirements.txt`, `requirements-dev.in`, `requirements-dev.txt`, `pyproject.toml`, `package.json`, `package-lock.json`, `.env.example`, `passwords.env.template`
- removed: stale `uv.lock`
- corrected: env templates, compose files, package-lock metadata, project metadata

Docs:

- kept as canonical: `architecture/`, `operations/`, `modules/`, `adr/`, `blacklab/README.md`, `changes/`, `ci_fix/README.md`, `template_status/`
- removed: migration-era reports, transient audits, run-by-run CI logs, phase notes, background audits, and one-off fix notes

Agent guidance:

- kept: root `AGENTS.md`, app `AGENTS.md`, `.github/copilot-instructions.md`, `.github/instructions/`, `.github/skills/`
- trimmed: `.github/agents/skills.md`

## 4. Dependency / Config Decisions

Python dependencies:

- kept the compiled requirements workflow as canonical
- removed `uv.lock` because the repo uses `uv pip compile` and `uv pip sync`, not `uv sync`
- updated docs to stop implying a second Python lock workflow

Node dependencies:

- kept `package.json` and `package-lock.json` for Playwright only
- aligned lockfile metadata with the package manifest

Environment templates:

- kept `.env.example` for local and app-level config examples
- kept `passwords.env.template` as a production secret template
- removed stale SQLite and legacy variable guidance from the templates

Compose/config wiring:

- kept root `docker-compose.dev-postgres.yml` as the canonical local dev compose
- removed the duplicate `app/docker-compose.dev-postgres.yml`
- kept `app/infra/docker-compose.dev.yml` as a secondary helper because current pre-deploy helpers still consume it
- removed legacy `DATABASE_URL` exports from compose files

## 5. Root Hygiene Changes

- rewrote `README.md` to describe the real repository contract
- rewrote `AGENTS.md` as a short root policy layer
- removed tracked build metadata under `app/src/corapan_web.egg-info/`
- removed the redundant `app/startme.md`

## 6. Docs Canonicalization

Removed:

- `docs/data_cleanup/`
- `docs/prod_migration/`
- `docs/repo_finish/`
- `docs/state/`
- `docs/problem/`
- historical `docs/changes/` entries that only recorded transition phases
- run-by-run `docs/ci_fix/runs/` logs
- transient template phase notes under `docs/template_status/`
- one-off UI, search, testing, and background audit notes

Merged or replaced:

- quick-start and setup guidance folded into `README.md`, `app/README.md`, and `docs/operations/local-dev.md`
- BlackLab discovery docs replaced by `docs/blacklab/README.md`
- template adaptation guidance replaced by `docs/architecture/template-customization.md`

Final docs structure:

- `docs/architecture/`
- `docs/operations/`
- `docs/modules/`
- `docs/blacklab/`
- `docs/adr/`
- `docs/changes/`
- `docs/ci_fix/`
- `docs/template_status/`
- `docs/local_runtime_layout.md`
- `docs/runtime_data_contract.md`

## 7. Agent Guidance Cleanup

`AGENTS.md`:

- reduced to the root decision order, canonical paths, hard rules, and documentation expectations

`.github/agents/skills.md`:

- reduced from phase-history and hotspot narrative to the durable template contract only

Final division of responsibility:

- `.github/copilot-instructions.md` carries the full repository policy
- `AGENTS.md` and `app/AGENTS.md` are short entry contracts
- `.github/agents/skills.md` covers template/UI authority only

## 8. Remaining Uncertain Items

- `app/infra/docker-compose.dev.yml` remains because current pre-deploy helpers still reference it; it is no longer presented as the canonical local development path
- `.github/agents/lessons-integrated-2026-03-21.md` remains as a historical agent artifact because it is still exposed in the current agent inventory

## 9. Final Repo Judgment

The repo is materially cleaner and more intentional than before this pass. The dependency and config story is now coherent, the docs layer is smaller and easier to trust, and future agents have a shorter path to the real rules. The main remaining compromise is retaining a secondary full-stack dev compose file for helper compatibility.