# Runtime Statistics Deployment

This document is limited to the active production sync lane.

## Canonical Flow

The only canonical statistics deployment path is:

1. `maintenance_pipelines/_2_deploy/deploy_data.ps1`
2. `app/scripts/deploy_sync/tasks/sync_data.ps1`
3. `app/scripts/deploy_sync/sync_data.ps1`
4. `Sync-StatisticsFiles`

There is no second orchestrator-side statistics upload anymore.

## Included Runtime Data

The data lane syncs:

- `data/db/public`
- `data/public/metadata`
- `data/exports`
- `data/db/stats_files.db`
- `data/db/stats_country.db`
- runtime statistics files in `data/public/statistics`

The data lane does not sync `data/blacklab/export`.
BlackLab remains a separate lane.

## Operator Usage

```powershell
.\maintenance_pipelines\_2_deploy\deploy_data.ps1
```

Skip runtime statistics intentionally:

```powershell
.\maintenance_pipelines\_2_deploy\deploy_data.ps1 -SkipStatistics
```

## Source Resolution

Set one of these before deploying statistics:

```powershell
$env:PUBLIC_STATS_DIR = "C:\dev\corapan\data\public\statistics"
```

or

```powershell
$env:CORAPAN_RUNTIME_ROOT = "C:\dev\corapan"
```

## Transport Reality

- standard transport: repo-bundled cwRSync `rsync.exe`
- SSH transport for rsync: repo-bundled cwRSync `ssh.exe`
- live operator identity may differ from historical `marele` defaults
- do not rewrite this lane to generic Windows OpenSSH rsync without live validation

## Safety Rules

- statistics upload is allowlist-only
- statistics upload does not use `--delete`
- production auth/core state is still excluded
- wrapper logs stay in `_2_deploy/_logs`
- task summaries now also land in `app/scripts/deploy_sync/_logs`

## Removed Drift

The following old statements are no longer valid and must not be reintroduced:

- `blacklab_export` is part of the standard data lane
- `deploy_data.ps1` should source `sync_data.ps1` a second time for stats
- emergency flags documented here but not implemented in the active wrapper are usable operator paths

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

- [LOKAL/_0_json/05_publish_corpus_statistics.py](../../LOKAL/_0_json/05_publish_corpus_statistics.py) - Statistics generator
- [scripts/deploy_sync/README.md](../../scripts/deploy_sync/README.md) - Core deploy sync documentation
- [docs/local_runtime_layout.md](../../docs/local_runtime_layout.md) - Runtime directory structure
