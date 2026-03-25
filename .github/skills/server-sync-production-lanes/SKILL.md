---
name: server-sync-production-lanes
description: "Use when validating, changing, reviewing, or documenting CORAPAN production sync lanes for Windows operator machines, including rsync, cwRsync, tar-over-SSH, scp fallbacks, resume behavior, SSH host-key handling, and non-destructive sync testing."
---

# Server Sync Production Lanes

## Use This Skill When

Use this skill whenever a task touches any of the following:

- `app/scripts/deploy_sync/**`
- `maintenance_pipelines/_2_deploy/**`
- `docs/rsync/**`
- operational guidance for Windows operator syncs
- rsync/cwRsync transport changes
- SSH transport selection for sync scripts
- `scp` fallback behavior
- `tar|ssh` fallback behavior
- resume, partial-transfer, or large-media handling
- host-key policy for production syncs

## Do Not Use When

Do not use this skill for:

- normal GitHub Actions code deploys that do not touch local operator syncs
- generic backend work unrelated to file transfer lanes
- speculative cleanup that is not grounded in a real operator-machine test

## Required Check Order

1. identify the affected lane: Data, Media, or BlackLab
2. identify the real sender environment on the operator machine
3. validate the active SSH path before changing rsync/scp/tar commands
4. use an isolated remote test path before trusting any transport change
5. verify integrity for at least one real transferred artifact
6. only then change scripts or docs

## Live-Tested Constraints From 2026-03-25

These findings are based on a real Windows operator-machine validation against `/srv/webapps/corapan/tmp_sync_test/`.

### 1. rsync Standard Path

- `rsync` was reliable only when cwRsync used its bundled `ssh.exe`
- `rsync` with Windows OpenSSH or generic `ssh` failed reproducibly with protocol-stream errors before data transfer
- do not replace the bundled cwRsync SSH path with a generic `ssh` command unless a real live test proves equivalence

### 2. Resume Matters

- `rsync --partial` successfully resumed a 1-GiB file after manual interruption
- preserve resume behavior for large media or other large runtime artifacts
- do not optimize away `--partial` for large-file lanes

### 3. scp Fallback Must Stay Legacy-Capable

- default `scp` mode failed with `subsystem request failed on channel 0`
- `scp -O` succeeded
- do not remove `-O` fallback support unless the target host is live-validated with the modern SCP/SFTP path

### 4. tar-over-SSH Is Not Universally Safe

- a PowerShell `tar | ssh` pipeline produced a corrupted medium-size file in live testing
- a `cmd`-based `tar|ssh` path succeeded for a medium file
- a 1-GiB `cmd`-based `tar|ssh` run produced a truncated/corrupted file
- therefore `tar|ssh` is a fallback, not a default for large files

### 5. Host-Key Hardening Needs Bootstrap

- with an empty isolated `known_hosts`, both `StrictHostKeyChecking=ask` and `StrictHostKeyChecking=yes` failed
- `StrictHostKeyChecking=no` succeeded and populated the host key
- never switch production sync scripts to strict host-key checking without a tested `known_hosts` provisioning step

### 6. Repo Defaults May Not Match Live Operator Reality

- the live operator access used an SSH alias plus `id_ed25519`
- the repo-encoded `~/.ssh/marele` default was not present on the tested machine
- treat hardcoded key paths as suspicious until validated on the real sender

## Hard Rules

- never test against productive runtime targets; use an isolated path such as `/srv/webapps/corapan/tmp_sync_test/`
- never introduce or reintroduce `--delete` into live validation runs unless the target is isolated and explicitly disposable
- never remove a fallback path because it "looks legacy" without a live replacement test
- never claim `tar|ssh` is equivalent to rsync for large files without integrity validation
- never assume host-key hardening is safe without a `known_hosts` rollout path
- never simplify cwRSync to generic `ssh` in `app/scripts/deploy_sync/**` without a fresh operator-machine proof
- never remove `scp -O` from the fallback contract
- treat Data, Media, and BlackLab as separate production lanes with separate risk profiles
- if a run summary or guardrail exists, extend it instead of bypassing it

## Minimum Validation Matrix

Before changing sync-lane behavior, validate at least:

1. one small file
2. one medium real-world file
3. one large file with interruption/resume if rsync is involved
4. one many-small-files dataset
5. one integrity check using SHA256 or equivalent

## Post-Refactor Validation Minimums

If a change touches `core/*`, `tasks/*`, transport selection, SSH defaults, path guards, or logging, also require:

1. Data task dry-run through `app/scripts/deploy_sync/tasks/sync_data.ps1`
2. Media task dry-run through `app/scripts/deploy_sync/tasks/sync_media.ps1`
3. one isolated live transfer under `/srv/webapps/corapan/tmp_sync_test/`
4. one explicit guard check for empty source or implausible target path
5. verification that the JSON summary contract still emits the required fields

## Legacy Removal Gate

Do not remove a fallback, bridge helper, or legacy sync artifact until:

1. the refactored standard path has been proven in practical validation
2. the fallback contract has been rechecked
3. the removal is documented as a deliberate follow-up rather than folded into a broad refactor

## Required Output

Any review or change proposal in this area must state:

- which lane is affected
- which transport is treated as standard
- which fallbacks remain mandatory
- whether resume behavior was preserved
- whether host-key behavior was tested or only assumed
- whether the change was validated on a real Windows operator machine
- whether logging and guard behavior changed for operators