# Logging Contract

Each productive lane run should emit a local JSON summary under `app/scripts/deploy_sync/_logs/` with at least:

- lane
- source
- target
- transport
- dryRun
- exitCode
- noChange
- changeCount
- deleteCount
- fallbackUsed

Wrapper transcripts under `maintenance_pipelines/_2_deploy/_logs/` remain useful for operator review, but they do not replace the per-lane summary contract.