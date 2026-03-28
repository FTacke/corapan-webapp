# LOKAL/_2_deploy - Deploy Orchestrators

This directory contains **orchestrator scripts** that coordinate deployment operations. These are the user-facing entry points for deploying to production.

## Purpose

- **Orchestrators call scripts in `scripts/deploy_sync/`** with appropriate parameters
- Provide consistent logging (timestamped log files in `_logs/`)
- Handle path resolution (work from any directory via `$PSScriptRoot`)
- Add deployment workflow conveniences (pre-flight checks, summaries)
- **Do NOT contain SSH/remote command logic** - that stays in `scripts/deploy_sync/`

## Available Orchestrators

### `publish_blacklab.ps1`

**Purpose:** Orchestrates BlackLab index publishing workflow.

**Status:** Existing orchestrator (already present in this directory).

**Usage:**
```powershell
.\maintenance_pipelines\_2_deploy\publish_blacklab.ps1 -AppRepoPath .\app -DryRun
```

**What it does:**
- Validates local environment
- Calls `scripts/deploy_sync/publish_blacklab_index.ps1`
- Writes timestamped log file
- Provides summary output

---

### `deploy_data.ps1`

**Purpose:** Orchestrates data synchronization to production.

**Usage:**
```powershell
.\maintenance_pipelines\_2_deploy\deploy_data.ps1 [-AppRepoPath <path>] [-Force]
```

**Parameters:**
- `-AppRepoPath`: Path to app repo root (default: resolved as `<workspace>/app`)
- `-WebappRepoPath`: Legacy alias retained for compatibility
- `-Force`: Force full resync (ignores manifest state)
- `-LogDir`: Log directory (default: `maintenance_pipelines/_2_deploy/_logs`)

**What it does:**
- Resolves paths and validates repo structure
- Calls `scripts/deploy_sync/sync_data.ps1` with parameters
- Writes timestamped log: `_logs/deploy_data_<timestamp>.log`
- Shows ASCII-only summary of results

**Note:** Connection parameters (hostname, user, port) are configured in sync_core.ps1 (used by the underlying sync_data.ps1 script).

**Example:**
```powershell
# Normal delta sync from workspace root
.\maintenance_pipelines\_2_deploy\deploy_data.ps1

# Force full resync from any directory
.\maintenance_pipelines\_2_deploy\deploy_data.ps1 -AppRepoPath "C:\dev\corapan\app" -Force
```

---

### `deploy_media.ps1`

**Purpose:** Orchestrates media synchronization to production.

**Usage:**
```powershell
.\maintenance_pipelines\_2_deploy\deploy_media.ps1 [-AppRepoPath <path>] [-Force] [-ForceMP3]
```

**Parameters:**
- `-AppRepoPath`: Path to app repo root (default: resolved as `<workspace>/app`)
- `-WebappRepoPath`: Legacy alias retained for compatibility
- `-Force`: Force full resync of all media
- `-ForceMP3`: Force full resync of MP3 files only
- `-LogDir`: Log directory (default: `maintenance_pipelines/_2_deploy/_logs`)

**What it does:**
- Resolves paths and validates repo structure
- Calls `scripts/deploy_sync/sync_media.ps1` with parameters
- Writes timestamped log: `_logs/deploy_media_<timestamp>.log`
- Shows ASCII-only summary of results

**Note:** Media transfer logic (rsync, delta, compression) remains in `sync_media.ps1` (stable, do not refactor). Connection parameters are configured in sync_core.ps1.

**Example:**
```powershell
# Normal delta sync from workspace root
.\maintenance_pipelines\_2_deploy\deploy_media.ps1

# Force MP3 resync from any directory
.\maintenance_pipelines\_2_deploy\deploy_media.ps1 -AppRepoPath "C:\dev\corapan\app" -ForceMP3
```

---

## Design Principles 

### 1. Orchestration Only

Orchestrators **do not**:
- Construct SSH commands
- Handle remote quoting/escaping
- Implement transfer logic (rsync, tar, etc.)

Orchestrators **do**:
- Validate local environment
- Call entry points with clean parameters
- Log execution
- Provide user-friendly output

### 2. Path Resolution

All orchestrators use `$PSScriptRoot` to resolve paths relative to the script location, allowing them to be called from any working directory:

```powershell
$ScriptDir = $PSScriptRoot
$RepoRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
```

### 3. Consistent Logging

All orchestrators write timestamped logs to `_logs/` subdirectory:
- `_logs/deploy_data_<timestamp>.log`
- `_logs/deploy_media_<timestamp>.log`
- `_logs/publish_blacklab_<timestamp>.log` (if publish_blacklab.ps1 uses logging)

### 4. ASCII-Only Output

All output strings use ASCII characters only (no Unicode arrows, ellipses, etc.) to avoid PowerShell encoding issues:
- Use "->" instead of Unicode arrows
- Use "..." instead of ellipses
- Use standard quotes instead of typographic quotes

### 5. DryRun Support

DryRun support varies by orchestrator:
- **`publish_blacklab.ps1`**: Full DryRun support (passes `-DryRun` to underlying script)
- **`deploy_data.ps1`**: No DryRun (relies on manifest-based delta sync for safety)
- **`deploy_media.ps1`**: No DryRun (relies on manifest-based delta sync for safety)

For data/media syncs, the underlying scripts use manifest files to track state and only transfer changed files, providing inherent safety.

---

## Separation: Data vs Media

**Why separate orchestrators?**

- Data and media have different:
  - Transfer characteristics (many small files vs few large files)
  - Risk profiles (data corruption vs bandwidth issues)
  - Update frequencies (data changes often, media rarely)
- Independent failure domains (data sync failure doesn't block media sync)
- Clearer logging and monitoring (separate log files)
- **No `deploy_all` script exists by design** - deliberate choice to avoid accidental mass operations

**When to use each:**

- **`deploy_data.ps1`**: After processing metadata, updating stats, changing counters, or exporting new data
- **`deploy_media.ps1`**: After adding/updating transcripts or audio files
- **`publish_blacklab.ps1`**: After building a new BlackLab index locally

---

## Workflow Examples

### Full Production Update (Data + Media)

```powershell
# 1. Execute data deploy
.\maintenance_pipelines\_2_deploy\deploy_data.ps1

# 2. Execute media deploy
.\maintenance_pipelines\_2_deploy\deploy_media.ps1

# 3. Verify production
# (manual check or monitoring)
```

### Data-Only Update

```powershell
# After metadata or stats changes
.\maintenance_pipelines\_2_deploy\deploy_data.ps1
```

### Media-Only Update

```powershell
# After adding new transcripts or audio
.\maintenance_pipelines\_2_deploy\deploy_media.ps1
```

### BlackLab Index Update

```powershell
# After building data/blacklab/index locally
.\maintenance_pipelines\_2_deploy\publish_blacklab.ps1 -AppRepoPath .\app -DryRun
.\maintenance_pipelines\_2_deploy\publish_blacklab.ps1 -AppRepoPath .\app
```

---

## Directory Structure

```
maintenance_pipelines/_2_deploy/
|-- README.md                    # This file
|-- publish_blacklab.ps1         # BlackLab index orchestrator
|-- deploy_data.ps1              # Data sync orchestrator
|-- deploy_media.ps1             # Media sync orchestrator
\`-- _logs/                      # Timestamped execution logs
    |-- deploy_data_*.log
    |-- deploy_media_*.log
    \`-- publish_blacklab_*.log
```

---

## Migration from Old Scripts

**Before (2025 and earlier):**
- Monolithic `deploy_full_prod.ps1` in `scripts/deploy_sync/`
- Combined `update_data_media.ps1`
- Direct calls to sync scripts without orchestration

**After (January 2026):**
- Separated data/media orchestrators in `maintenance_pipelines/_2_deploy/`
- Clear entry points in `scripts/deploy_sync/`
- Consistent logging and path handling
- Legacy scripts archived in `scripts/deploy_sync/legacy/`

---

## Troubleshooting

### "Cannot find script" errors

**Problem:** Script called from wrong directory.

**Solution:** Use absolute paths or rely on `$PSScriptRoot` resolution in orchestrators.

### SSH/Encoding issues

**Problem:** Unicode characters in logs causing gibberish output.

**Solution:** Orchestrators use ASCII-only. If issues persist, check underlying entry point scripts.

### "DryRun shows nothing"

**Problem:** No changes detected or manifest up-to-date.

**Solution:** Normal behavior for delta sync. Manifest tracks file states and only changed files are transferred. Use `-Force` to override manifest if a full resync is needed.

### Log files not created

**Problem:** `_logs/` directory doesn't exist.

**Solution:** Orchestrators should create it automatically. Verify write permissions on `maintenance_pipelines/_2_deploy/`.

---

## Best Practices

1. **Check logs** - timestamped logs in `_logs/` preserve execution history
2. **Run from repo root** - although orchestrators handle paths, it's clearer
3. **One operation at a time** - don't run data and media deploys simultaneously
4. **Verify production** - after deploy, check production server health/functionality
5. **Use `-Force` sparingly** - normal delta sync is safer and faster

---

## Related Documentation

- Entry point scripts: `scripts/deploy_sync/README.md`
- BlackLab publishing: `scripts/deploy_sync/PUBLISH_BLACKLAB_INDEX.md`
- SSH helpers: `scripts/deploy_sync/_lib/ssh.ps1`
