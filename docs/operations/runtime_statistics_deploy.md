# Runtime Statistics Deployment

> Statistics are runtime-only assets under `data/public/statistics`.
> The canonical production lane is the data sync task, not a second orchestrator-side upload.

## Overview

Runtime statistics are uploaded by `app/scripts/deploy_sync/sync_data.ps1`.
`maintenance_pipelines/_2_deploy/deploy_data.ps1` is now only a wrapper that calls the canonical data task once.

That matters because the old wrapper-side second upload caused deployment drift and duplicate behavior.

## What Gets Uploaded

- `corpus_stats.json`
- `viz_*.png`

The target remains `/srv/webapps/corapan/data/public/statistics/`.

## What Does Not Happen Here

- no BlackLab export deployment
- no `data/blacklab/export` sync
- no auth database overwrite
- no second statistics pass after the data task completes

## Local Prerequisites

Set one of the following before calling the data lane:

```powershell
$env:PUBLIC_STATS_DIR = "C:\dev\corapan\data\public\statistics"
```

or

```powershell
$env:CORAPAN_RUNTIME_ROOT = "C:\dev\corapan"
```

When only `CORAPAN_RUNTIME_ROOT` is set, the statistics source is derived as `data/public/statistics` below that root.

## Canonical Usage

Standard run:

```powershell
.\maintenance_pipelines\_2_deploy\deploy_data.ps1
```

Skip statistics intentionally:

```powershell
.\maintenance_pipelines\_2_deploy\deploy_data.ps1 -SkipStatistics
```

Force data resync while leaving the statistics step in overwrite mode:

```powershell
.\maintenance_pipelines\_2_deploy\deploy_data.ps1 -Force
```

## Transport Contract

- standard transport: repo-bundled cwRsync `rsync.exe` with bundled `ssh.exe`
- statistics upload is allowlist-based and does not use `--delete`
- operator SSH identity is machine-specific and must be validated locally
- do not assume historical `marele` key defaults are the live operator truth

## Failure Behavior

- missing stats directory: graceful skip with guidance
- missing `corpus_stats.json` or missing `viz_*.png`: graceful skip
- rsync or SSH failure during upload: task returns failure

## Protected Production State

The data lane still excludes production-owned state such as:

- `data/db/auth.db`
- non-allowlisted `data/db/*`
- `data/blacklab/*`

## Verification

Local task logs are written under `app/scripts/deploy_sync/_logs/` as JSON summaries.
Wrapper transcripts remain under `maintenance_pipelines/_2_deploy/_logs/`.

**Solution:**
```powershell
# Verify cwRsync installation
Test-Path "C:\dev\corapan\app\tools\cwrsync\bin\rsync.exe"

# Check PATH includes cwRsync
$env:Path -split ';' | Select-String cwrsync
```

### "Statistics directory does not exist"

**Cause:** Environment variable points to non-existent directory

**Solution:**
```powershell
# Verify path
Test-Path $env:PUBLIC_STATS_DIR

# Create if needed
New-Item -ItemType Directory -Path $env:PUBLIC_STATS_DIR -Force
```

### "corpus_stats.json not found"

**Cause:** Statistics haven't been generated

**Solution:**
```powershell
# Run generator with explicit output path
python .\maintenance_pipelines\_0_json\05_publish_corpus_statistics.py --out "$env:PUBLIC_STATS_DIR"
```

### "No viz_*.png files found"

**Cause:** Statistics generation incomplete or failed

**Solution:**
```powershell
# Check generator output
python .\maintenance_pipelines\_0_json\05_publish_corpus_statistics.py --out "$env:PUBLIC_STATS_DIR"

# Look for errors in console output
```

## Development Notes

### Why Separate from Data Sync?

Statistics files are:
1. **Runtime-only** - never committed to Git
2. **Generated content** - not source data
3. **Different cadence** - updated less frequently than core data
4. **Optional** - app works without them (statistics page may be empty)

### Why No Atomic Swap?

Unlike BlackLab index deployment (which needs atomic swap for zero-downtime):
- Statistics are read-only data
- No locking or consistency requirements
- Brief inconsistency during upload is acceptable
- Files are small (upload takes seconds)

### Future Enhancements

Potential improvements (not currently implemented):
- [ ] Timestamp check (skip upload if remote files are newer)
- [ ] Checksum validation (verify upload integrity)
- [ ] Backup creation (keep N previous versions)
- [ ] Dry-run mode (show what would be uploaded)

## See Also

- [maintenance_pipelines/_0_json/05_publish_corpus_statistics.py](../../maintenance_pipelines/_0_json/05_publish_corpus_statistics.py) - Statistics generator
- [scripts/deploy_sync/README.md](../../scripts/deploy_sync/README.md) - Core deploy sync documentation
- [docs/local_runtime_layout.md](../../docs/local_runtime_layout.md) - Runtime directory structure
