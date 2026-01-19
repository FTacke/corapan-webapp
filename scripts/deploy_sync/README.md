# Deploy Sync Scripts

This directory contains the core deployment logic for synchronizing data, media, and BlackLab indexes to the production server.

## Overview

- **Deploy logic lives here** - core SSH/rsync/transfer implementations
- **Orchestrators live in `LOKAL/_2_deploy`** - user-facing scripts that call these entry points with proper parameters and logging

## Entry Points

### `sync_data.ps1`

**Purpose:** Synchronizes application data to production (metadata, stats databases, exports).

**Usage:**
```powershell
.\scripts\deploy_sync\sync_data.ps1 [-RepoRoot <path>] [-Force]
```

**Key Parameters:**
- `-RepoRoot`: Path to webapp repository root (default: C:\dev\corapan-webapp)
- `-Force`: Force full resync (ignores manifest state)
- `-DryRun`: Print remote targets only (no transfer)

**Connection Configuration:**
Connection parameters (hostname/user/port/key) and remote runtime roots are configured in `scripts/deploy_sync/_lib/ssh.ps1` (single source of truth).

**What it syncs:**
- `runtime/corapan/data/db/public/`
- `runtime/corapan/data/public/metadata/`
- `runtime/corapan/data/exports/`
- `runtime/corapan/data/blacklab_export/`
- Stats databases: `runtime/corapan/data/db/public/stats_files.db`, `runtime/corapan/data/db/public/stats_country.db`

**PROTECTED PRODUCTION STATE (PERMANENTLY EXCLUDED):**
- `data/db/` - Contains auth.db, transcription.db (production databases) - **NEVER synced**
  - Only exception: specific stats DB files listed above are synced

These paths contain production runtime state that must NEVER be overwritten by any data deploy. The protection is HARD-CODED and cannot be bypassed, even with parameter flags. If you need to manually restore production state, use SSH restore procedures instead.

**Manifest-Speicherung:**
- Pro Verzeichnis wird ein eigenes Manifest unter `data/<segment>/.sync_state/` gespeichert.
- Beispiel: `data/public/metadata/.sync_state/public_metadata_manifest.json`
- **Robustheit:** Falls `.sync_state` oder Manifest-Dateien geloescht wurden, erstellt der Sync die Verzeichnisse/Manifeste automatisch neu.

**Statistics Deployment (HARDENED):**
`sync_data.ps1` runs `Sync-StatisticsFiles` for statistics files (corpus_stats.json, viz_*.png)
with strict safety guards:

**What gets deployed:**
- ONLY: `corpus_stats.json` and `viz_*.png` files
- Target: `/srv/webapps/corapan/runtime/corapan/data/public/statistics`
- Mode: Overwrite-only (no delete, no directory structures)

**Safety Guards:**
- **Regex Quoting:** Remote verification uses single-quoted regex to avoid bash syntax errors.
- Hard validation prevents syncing from repo root or parent directories
- Per-file allowlist: corpus_stats.json + all viz_*.png (no other files)
- Post-upload verification ensures only expected files are present on remote
- If guard triggers: deployment is refused with clear error message

**How it works:**
- `[PHASE 1]` Determines local stats dir from env vars (PUBLIC_STATS_DIR or CORAPAN_RUNTIME_ROOT)
- `[PHASE 2]` Hard guards: rejects if dir contains .git, src/, package.json, etc.
- `[PHASE 3]` Validates corpus_stats.json exists and at least 1 viz_*.png exists
- `[PHASE 4-5]` Per-file upload via rsync (corpus_stats.json, then each viz_*.png)
- `[PHASE 6]` Post-upload verification: `ls -1 remote | grep -vE '^(corpus_stats\.json|viz_.*\.png)$'` must be empty
- `[PHASE 7]` Sets ownership

**Usage:**
- Called by: `sync_data.ps1` (and by `LOKAL/_2_deploy/deploy_data.ps1` orchestrator)
- Requires: `PUBLIC_STATS_DIR` or `CORAPAN_RUNTIME_ROOT` environment variable set
- Behavior: SKIP with warning if stats dir not ready (non-critical)
- Testing: Pass `-DryRun` flag to see files without uploading

**Recommended:** Use via orchestrator `LOKAL/_2_deploy/deploy_data.ps1` which handles both data sync AND statistics upload.

---

### `sync_media.ps1`

**Purpose:** Synchronizes media files to production (transcripts, MP3 audio files).

**Status:** **Stable production transfer** - do not refactor transfer logic.

**Usage:**
```powershell
.\scripts\deploy_sync\sync_media.ps1 [-RepoRoot <path>] [-Force] [-ForceMP3] [-DryRun]
```

**Key Parameters:**
- `-RepoRoot`: Path to webapp repository root (default: C:\dev\corapan-webapp)
- `-Force`: Force full resync of all media
- `-ForceMP3`: Force full resync of MP3 files only (transcripts remain delta)
- `-DryRun`: Print remote targets only (no transfer)

**Connection Configuration:**
Connection parameters (hostname/user/port/key) and remote runtime roots are configured in `scripts/deploy_sync/_lib/ssh.ps1` (single source of truth).

**What it syncs:**
- `media/transcripts/`
- `media/mp3-full/` (large files, GB scale)
- `media/mp3-split/` (large files, GB scale)

**Notes:**
- Uses rsync with delta transfer and compression
- Large transfers can take hours on first sync
- Supports resumable partial transfers
- Per-directory manifest tracking in `.sync_state/`

**Recommended:** Use via orchestrator `LOKAL/_2_deploy/deploy_media.ps1`

---

### `publish_blacklab_index.ps1`

**Purpose:** Publishes a validated BlackLab index from local staging to production with atomic swap.

**Usage:**
```powershell
.\scripts\deploy_sync\publish_blacklab_index.ps1 [-Hostname <host>] [-User <user>] [-Port <port>] [-DryRun]
```

**Key Parameters:**
- `-Hostname`: Production server hostname/IP (default: from `scripts/deploy_sync/_lib/ssh.ps1`)
- `-User`: SSH user (default: from `scripts/deploy_sync/_lib/ssh.ps1`)
- `-Port`: SSH port (default: from `scripts/deploy_sync/_lib/ssh.ps1`)
- `-DataDir`: Remote data directory (default: `${CORAPAN_RUNTIME_ROOT}/data` via `scripts/deploy_sync/_lib/ssh.ps1`)
- `-ConfigDir`: Remote BlackLab config directory (default: /srv/webapps/corapan/app/config/blacklab)
- `-DryRun`: Show what would be done without making changes
- `-KeepBackups`: Number of backups to retain (default: 2)
- `-NoBackupCleanup`: Skip automatic cleanup of old backups

**Process:**
1. Validates local `data/blacklab_index.new/` exists
2. Uploads index to production staging area
3. Validates index on production using BlackLab Docker container
4. Performs atomic swap: `blacklab_index` -> `blacklab_index.bak_<timestamp>`, `blacklab_index.new` -> `blacklab_index`
5. Verifies production server health
6. Cleans up old backups (keeps last N)

**For detailed documentation:** See `PUBLISH_BLACKLAB_INDEX.md` in this directory.

**Recommended:** Use via orchestrator `LOKAL/_2_deploy/publish_blacklab.ps1`

---

## Helper Libraries

### `_lib/ssh.ps1`

**Purpose:** Canonical SSH command execution pattern with proper quoting/escaping for Windows PowerShell.

**Usage:**
```powershell
. "$PSScriptRoot\_lib\ssh.ps1"
Invoke-SSH -Hostname $Hostname -User $User -Port $Port -Command "ls -la /srv"
```

**Why it exists:** SSH command execution from Windows PowerShell requires careful handling of quoting, escaping, and shell metacharacters. This library provides a tested, reliable pattern.

---

### `sync_core.ps1`

**Purpose:** Shared sync functions for data and media synchronization (manifest handling, rsync/tar logic).

**Status:** Required dependency for `sync_data.ps1` and `sync_media.ps1`.

**Key functions:**
- Manifest generation and comparison
- rsync integration (Windows/cwRsync)
- tar+base64 fallback transport
- Per-directory `.sync_state/` manifest tracking

**Note:** This is a supporting library - not a direct entry point.

---

## Safety & Best Practices

### Runtime-First Production Contract

**Production is runtime-first.** The runtime root is:

- `/srv/webapps/corapan/runtime/corapan`

The container **must** mount runtime paths directly into `/app`:

- `/srv/webapps/corapan/runtime/corapan/data`  -> `/app/data`
- `/srv/webapps/corapan/runtime/corapan/media` -> `/app/media`
- `/srv/webapps/corapan/runtime/corapan/logs`  -> `/app/logs`
- `/srv/webapps/corapan/runtime/corapan/config`-> `/app/config`

**Legacy paths are deprecated:**

- `/srv/webapps/corapan/data|media|logs` are legacy and **not** target paths for deploy scripts.

**Preflight guard:**

`sync_data.ps1` and `sync_media.ps1` run a remote preflight check. If the container is not running or mounts drift from the contract, the script aborts with:

> Prod mount drift: corapan-webapp is not runtime-first. Fix docker-compose.prod.yml mounts.

### Production State Protection (Hard-Coded)

**CRITICAL:** The following directory is **PERMANENTLY PROTECTED** and can NEVER be synced by any deploy:

- `data/db/` - Production databases including auth.db and transcription.db

These protections are **NOT configurable** via parameters. They are enforced at the script level:

1. **Hard blocklist** in `sync_data.ps1` prevents these paths from being added to sync lists
2. **Validation** rejects any configuration that includes these paths
3. **Exit code 3** if protection is violated (indicating configuration error)

This design prevents accidental overwrites of production runtime state during normal deployments.

**If you need to manually restore production state:**
- Use SSH to connect to the server
- Use manual file operations via `rsync`, `scp`, or `tar`
- Never use the deploy scripts for production state restoration

### Statistics Deployment (Controlled & Optional)

Statistics files (corpus_stats.json, viz_*.png) are:
- Deployed by `sync_data.ps1` via `Sync-StatisticsFiles`
- Synced to: `/srv/webapps/corapan/runtime/corapan/data/public/statistics`
- Mode: Overwrite-only (no delete, no atomic swap)
- Optional: Deployment continues even if stats are not ready
- Controlled by: `Sync-StatisticsFiles` function in `sync_data.ps1`
- Source: `PUBLIC_STATS_DIR` or `CORAPAN_RUNTIME_ROOT/data/public/statistics` environment variables

### Separation of Concerns

- **Data and Media are separate operations** - no `deploy_all` script exists by design
- Each sync operation can fail independently
- Easier to debug and monitor specific transfer types

### DryRun Expectation

Entry points have varying DryRun support:
- `publish_blacklab_index.ps1`: **Supports `-DryRun`** - shows planned actions without executing
- `sync_data.ps1`: **Supports `-DryRun`** - prints remote targets only
- `sync_media.ps1`: **Supports `-DryRun`** - prints remote targets only

### Logging & Encoding

- All log output uses **ASCII-only characters** (no Unicode arrows/symbols)
- Avoids encoding issues in PowerShell terminals and log files
- Examples: use "->" instead of Unicode arrows, "..." instead of ellipses, etc.

### SSH/Remote Execution

- No complex SSH command quoting in orchestrators
- Orchestrators delegate to these entry points with clean parameters
- SSH complexity handled in `_lib/ssh.ps1` and entry point scripts

---

## Examples

### Direct Entry Point Usage

**Data sync with custom repo path:**
```powershell
.\scripts\deploy_sync\sync_data.ps1 -RepoRoot "C:\custom\path"
```

**Force full data resync:**
```powershell
.\scripts\deploy_sync\sync_data.ps1 -Force
```

**Force full media resync:**
```powershell
.\scripts\deploy_sync\sync_media.ps1 -Force
```

**Publish BlackLab index with DryRun:**
```powershell
.\scripts\deploy_sync\publish_blacklab_index.ps1 -DryRun
```

### Orchestrator Usage (Recommended)

**Data deploy with logging (includes statistics):**
```powershell
.\LOKAL\_2_deploy\deploy_data.ps1
```

**Data deploy without statistics:**
```powershell
.\LOKAL\_2_deploy\deploy_data.ps1 -SkipStatistics
```

**Media deploy with logging:**
```powershell
.\LOKAL\_2_deploy\deploy_media.ps1
```

**Publish BlackLab with full orchestration and DryRun:**
```powershell
.\LOKAL\_2_deploy\publish_blacklab.ps1 -WebappRepoPath . -DryRun
```

---

## Legacy Files

Deprecated/obsolete scripts are moved to `legacy/<timestamp>/` subdirectories to preserve history without cluttering the active codebase.

Current legacy archive: `legacy/20260116_211115/`
- `deploy_full_prod.ps1` - old monolithic deploy script
- `update_data_media.ps1` - old combined data+media updater

**Note:** `sync_core.ps1` was initially moved to legacy but has been restored as it is a required dependency for `sync_data.ps1` and `sync_media.ps1`.

---

## Migration Notes

**January 2026 Cleanup:**
- Separated data/media sync operations
- Created clear orchestrator layer in `LOKAL/_2_deploy/`
- Applied ASCII-only logging standards
- Moved legacy scripts to timestamped archive
- No functional changes to stable media transfer logic
