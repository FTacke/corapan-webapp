# 2026-03-21 BlackLab Operational Safety Hardening

## What Changed

- Hardened `scripts/blacklab/build_blacklab_index.ps1` with an explicit running-container block and staged-index validation before activation.
- Hardened `scripts/blacklab/start_blacklab_docker_v3.ps1` with canonical-path checks, explicit restart semantics, and a post-start hits smoke query.
- Hardened `scripts/dev-start.ps1` and `scripts/dev-setup.ps1` so BlackLab must answer a real hits query before local startup is treated as healthy.
- Added architecture and incident documentation for the 2026-03-21 BlackLab corruption failure.

## Why

Dev BlackLab returned 500 for valid advanced-search hits queries because the active mounted index was corrupt. The incident showed that:

- root endpoint readiness is insufficient
- a successful build log is insufficient
- implicit container replacement is too permissive
- canonical path discipline must remain strict in dev

## Operational Impact

- Rebuilds now require the serving container to be stopped first.
- Starting or reusing BlackLab now validates the active index with a real search request.
- Broken BlackLab index state now fails fast during dev startup instead of surfacing later as misleading app errors.