# 2026-03-25 Live Sync Validation And Skill

## What Changed

- added a live validation report for the Windows operator production sync lane in `docs/rsync/live_validation_sync.md`
- added a new repository skill proposal in `.github/skills/server-sync-production-lanes/SKILL.md`

## Why

- the repo previously contained only code-level and historical analysis for the sync lane
- a live technical validation was needed to determine which transport paths actually work from the local Windows operator environment
- the results are important enough to preserve as agent guidance so future refactors do not break tested operational behavior

## Environment Scope

- local Windows PowerShell operator machine
- remote production-adjacent isolated test path `/srv/webapps/corapan/tmp_sync_test/`
- no production deploys, no service changes, no destructive operations

## Operational Impact

- documents that `rsync` currently depends on the bundled cwRsync `ssh.exe` in the tested environment
- documents that `scp -O` remains a required fallback
- documents that `tar|ssh` is not a safe default for large files in the tested environment
- records that strict host-key checking needs a real known-hosts bootstrap plan

## Compatibility Notes

- the tested live SSH reality differed from the repo-hardcoded `marele` key path
- the new skill is meant to prevent agents from normalizing transports or removing fallbacks without live proof

## Follow-Up

- align sync scripts with the tested standard path only after a deliberate refactor task
- if host-key hardening is planned, add a documented and validated `known_hosts` provisioning workflow first