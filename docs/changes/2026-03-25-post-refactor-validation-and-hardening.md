# 2026-03-25 Post-Refactor Validation And Hardening

## Summary

Validated the refactored local production sync lanes in practice and fixed the runtime defects that only appeared during real dry-run and isolated live execution.

## What Was Proven

- Data and Media task entry points execute successfully in dry-run
- the JSON logging contract is emitted for Data, Media, and BlackLab
- the shared empty-source and remote-path guards trigger correctly
- repo-bound cwRSync is the active live transport again after fixing app-root path resolution
- `scp -O` remains a working fallback
- one-file media syncs now work and return `NoChange` correctly on a second run

## Hardening Fixes

- fixed a parser/runtime bug in `app/scripts/deploy_sync/core/guards.ps1`
- fixed BlackLab local staging path resolution in `app/scripts/deploy_sync/publish_blacklab_index.ps1`
- fixed production mount validation and JSON mount parsing in `app/scripts/deploy_sync/sync_core.ps1`
- fixed app-root tool resolution for repo-bound cwRSync in `app/scripts/deploy_sync/sync_core.ps1`
- fixed single-file manifest array handling in `app/scripts/deploy_sync/sync_core.ps1`
- hardened SSH key default resolution in `app/scripts/deploy_sync/_lib/ssh.ps1`

## Residual Risk

- full BlackLab dry-run remains blocked locally until `data/blacklab/quarantine/index.build` exists
- the current production BlackLab hits endpoint returns HTTP 500 because the running container cannot find `blacklab-server.(json|yaml)` in `/etc/blacklab`

## Documentation

- added `docs/rsync/post_refactor_validation_report.md` as the practical source of truth for the post-refactor proof and legacy classification