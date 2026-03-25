# Sync Lane Refactor Implementation Report

## Scope

This report covers the refactor work applied after the live Windows validation and the final plan in `docs/rsync/refactor_plan.md`.

## Source Set

- `docs/rsync/live_validation_sync.md`
- `docs/rsync/refactor_plan.md`
- `docs/rsync/technical_precheck_sync_constraints.md`
- `docs/rsync/2026-03-25_server-sync-audit.md`
- `docs/rsync/server-agent_rsync_audit.md`

## Implemented Items

- added `app/scripts/deploy_sync/core/` transition modules for paths, guards, logging, ssh, rsync, and transport
- added `app/scripts/deploy_sync/tasks/` transition entry points for Data, Media, and BlackLab
- changed shared rsync calls to repo-bundled cwRSync transport instead of generic `rsync` on `PATH`
- preserved existing fallbacks instead of removing them speculatively
- removed duplicate statistics deployment from `maintenance_pipelines/_2_deploy/deploy_data.ps1`
- upgraded BlackLab validation from corpora-only checks to a real hits query gate
- added JSON run summaries for the active lane scripts
- reduced active documentation drift around statistics deployment and sync-lane transport rules

## Deliberately Not Done

- no forced host-key hardening rollout
- no big-bang deletion of legacy scripts
- no speculative transport rewrite that would replace proven operator workarounds
- no attempt to standardize BlackLab large uploads onto a new unvalidated transport

## Transition Model

The current implementation is intentionally phased:

- orchestrators call `tasks/*`
- `tasks/*` delegate to the still-active lane scripts
- the lane scripts now consume shared `core/*` helpers where risk was low and evidence was strong

This keeps operator-facing behavior stable while making the transport and guard logic more centralized.