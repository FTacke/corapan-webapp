# Runtime Statistics Deployment

> **Important:** Statistics are **runtime-only**. Do NOT look for them in `static/img/statistics/` (that's a legacy location removed from Git).
> See [Legacy Static Statistics](./legacy_static_statistics.md) for context.

## Overview

The `deploy_data.ps1` orchestrator now includes automatic upload of runtime statistics files to production. These files are generated locally and deployed separately from the main data sync.

## Statistics Files

**Generated files:**
- `corpus_stats.json` - JSON data for dynamic frontend consumption
- `viz_*.png` - Visualization images (pie charts, bar charts, country summaries)

**Examples:**
- `viz_total_corpus.png`
- `viz_genero_profesionales.png`
- `viz_modo_genero_profesionales.png`
- `viz_argentina_resumen.png`
- `viz_colombia_resumen.png`
- etc.

## Deployment Behavior

### Simple Overwrite (No Atomic Swap)

Statistics deployment uses a **simple overwrite strategy**:
- ✅ Directly uploads to `/srv/webapps/corapan/data/public/statistics/`
- ✅ Overwrites existing files
- ❌ No backup creation
- ❌ No atomic swap
- ❌ No rollback mechanism

**Rationale:** Statistics files are:
- Non-critical for app functionality
- Quick to regenerate locally
- Small in size (< 10 MB total)
- Updated infrequently

## Local Setup

### Required Environment Variables

Set **ONE** of the following before deploying statistics:

**Option 1: Direct statistics path**
```powershell
$env:PUBLIC_STATS_DIR = "C:\dev\runtime\corapan\data\public\statistics"
```

**Option 2: Runtime root (auto-derives statistics path)**
```powershell
$env:CORAPAN_RUNTIME_ROOT = "C:\dev\runtime\corapan"
# Statistics path becomes: $CORAPAN_RUNTIME_ROOT\data\public\statistics
```

### Generating Statistics

**Full workflow:**
```powershell
# 1. Set environment
$env:CORAPAN_RUNTIME_ROOT = "C:\dev\runtime\corapan"

# 2. Generate statistics (requires CSV input from step 04)
python .\LOKAL\_0_json\04_internal_country_statistics.py
python .\LOKAL\_0_json\05_publish_corpus_statistics.py

# 3. Deploy data + statistics
.\LOKAL\_2_deploy\deploy_data.ps1
```

**Quick regeneration (if CSVs already exist):**
```powershell
python .\LOKAL\_0_json\05_publish_corpus_statistics.py --out "$env:PUBLIC_STATS_DIR"
.\LOKAL\_2_deploy\deploy_data.ps1
```

## Deployment Usage

### Standard Deployment (Data + Statistics)

```powershell
.\LOKAL\_2_deploy\deploy_data.ps1
```

This will:
1. Sync data directories (public/metadata, exports, db/public, blacklab_export, stats databases)
2. Upload statistics files to `/srv/webapps/corapan/data/public/statistics/`
3. Set correct ownership (hrzadmin:hrzadmin)

**Note:** `counters/` and `db/auth.db` are protected production state and are NEVER synced by default.

### Skip Statistics

```powershell
.\LOKAL\_2_deploy\deploy_data.ps1 -SkipStatistics
```

Use this when:
- Statistics haven't been generated yet
- Only data directories need updating
- Testing data sync independently

### Force Mode

```powershell
.\LOKAL\_2_deploy\deploy_data.ps1 -Force
```

Forces full data resync (ignores manifest state). Statistics upload is always overwrite, so `-Force` doesn't affect statistics behavior.

## Production State Protection

### What is NEVER Synced

The following paths contain production runtime state and are **always protected** from being overwritten by a normal data deploy:

- **`data/counters/`** - Runtime state files (page views, downloads, feature counters, etc.)
- **`data/db/auth.db`** - Production authentication database

These are critical for production stability and must never be lost or overwritten.

### Emergency Override (Very Rare)

In an extreme emergency, you can override the protection with three explicit flags:

```powershell
.\LOKAL\_2_deploy\deploy_data.ps1 `
    -IncludeCounters `
    -IncludeAuthDb `
    -IUnderstandThisWillOverwriteProductionState
```

**This is DANGEROUS and should only be done with explicit approval from a senior team member.** The script will:
1. Show a prominent 5-second warning
2. Require you to acknowledge each override flag explicitly
3. Log everything to the deployment log

**Do NOT use these flags unless you fully understand the consequences.**

## Error Handling

### Missing Environment Variables

If neither `PUBLIC_STATS_DIR` nor `CORAPAN_RUNTIME_ROOT` is set:
- Deployment prints clear error message
- Provides setup instructions
- **Exits with code 0** (graceful skip, not fatal error)

### Missing Statistics Files

If environment is configured but files don't exist:
- Validates presence of `corpus_stats.json`
- Validates presence of at least one `viz_*.png`
- Prints generation instructions
- **Exits with code 0** (graceful skip)

### Upload Failures

rsync or SSH failures during statistics upload:
- **Exit with code 1** (fatal error)
- Full error details logged to `LOKAL/_2_deploy/_logs/deploy_data_<timestamp>.log`

## Remote Target

**Production path:**
```
/srv/webapps/corapan/data/public/statistics/
```

**Served via FastAPI:**
- `/corpus/api/corpus_stats` → `corpus_stats.json`
- `/corpus/api/statistics/viz_total_corpus.png` → image files
- etc.

## Technical Details

### Transport Mechanism

**rsync via cwRsync:**
- Selective file upload (only `corpus_stats.json` and `viz_*.png`)
- Compression enabled (`-z`)
- Verbose output (`-v`)
- No `--delete` flag (doesn't remove untracked files on server)

**rsync pattern matching:**
```powershell
--include "corpus_stats.json"
--include "viz_*.png"
--exclude "*"
```

### SSH Authentication

Uses the same SSH configuration as data/media sync:
- Key: `$env:USERPROFILE\.ssh\marele` (8.3 short name for cwRsync)
- User: `root`
- Host: `marele.online.uni-marburg.de` (137.248.186.51)
- No passphrase (dedicated deploy key)

### Ownership

After upload, sets ownership recursively on `/srv/webapps/corapan/data/public/`:
```bash
chown -R 1000:1000 /srv/webapps/corapan/data/public/
```

**Note:** Applied to parent `data/public/` directory (not just `statistics/` subdirectory) for consistency.

## Verification

After successful deployment, the script shows remote directory listing:

```
Remote statistics directory contents:
  -rw-r--r-- 1 hrzadmin hrzadmin  45231 Jan 17 12:34 corpus_stats.json
  -rw-r--r-- 1 hrzadmin hrzadmin 123456 Jan 17 12:34 viz_total_corpus.png
  -rw-r--r-- 1 hrzadmin hrzadmin  98765 Jan 17 12:34 viz_genero_profesionales.png
  ...
```

**Manual verification:**
```bash
ssh root@marele.online.uni-marburg.de "ls -lh /srv/webapps/corapan/data/public/statistics/"
```

**HTTP verification (from production):**
```bash
curl https://corapan.com/corpus/api/corpus_stats
curl -I https://corapan.com/corpus/api/statistics/viz_total_corpus.png
```

## Troubleshooting

### "rsync not available"

**Cause:** cwRsync not found in PATH

**Solution:**
```powershell
# Verify cwRsync installation
Test-Path "C:\dev\corapan-webapp\tools\cwrsync\bin\rsync.exe"

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
python .\LOKAL\_0_json\05_publish_corpus_statistics.py --out "$env:PUBLIC_STATS_DIR"
```

### "No viz_*.png files found"

**Cause:** Statistics generation incomplete or failed

**Solution:**
```powershell
# Check generator output
python .\LOKAL\_0_json\05_publish_corpus_statistics.py --out "$env:PUBLIC_STATS_DIR"

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
