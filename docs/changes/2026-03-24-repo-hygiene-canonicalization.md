# 2026-03-24 Repo Hygiene and Canonicalization

## What Changed

- removed redundant and migration-era repository files that no longer defined the active system
- standardized the dependency story on compiled `requirements*.in` and `requirements*.txt`
- removed the stale `uv.lock` path and tracked build metadata from the application tree
- rewrote the canonical docs, env templates, and agent guidance files to match the live repository model
- reduced duplicate quick-start and audit documentation in favor of a smaller canonical set
- removed `app/static/css/md3/tokens-legacy-shim.css` after migrating the last live runtime caller to canonical tokens

## Why

The repository had accumulated overlapping setup docs, historical audit trails, generated artifacts, and conflicting config examples. The cleanup makes the active workflow easier to identify and harder to misuse.

## Affected Scope

- repository root governance and docs
- app dependency and config files
- compose and script-facing config guidance
- agent-facing template rules
- MD3 token loading and token-audit rules

## Compatibility Notes

- `maintenance_pipelines/` was intentionally excluded
- `app/infra/docker-compose.dev.yml` remains as a secondary full-stack helper because current pre-deploy helpers still reference it
- the root development entry points remain unchanged
- the frontend now requires canonical `--app-*`, `--space-*`, and `--md-sys-*` tokens only