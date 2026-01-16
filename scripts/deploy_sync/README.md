# Deploy Sync Scripts

This directory contains the core deployment logic for synchronizing data, media, and BlackLab indexes to the production server.

## Overview

- **Deploy logic lives here** - core SSH/rsync/transfer implementations
- **Orchestrators live in `LOKAL/_2_deploy`** - user-facing scripts that call these entry points with proper parameters and logging

## Entry Points

### `sync_data.ps1`

**Purpose:** Synchronizes application data to production (metadata, counters, stats databases, exports).

**Usage:**
```powershell
.\scripts\deploy_sync\sync_data.ps1 [-RepoRoot <path>] [-Force]
```

**Key Parameters:**
- `-RepoRoot`: Path to webapp repository root (default: C:\dev\corapan-webapp)
- `-Force`: Force full resync (ignores manifest state)

**Connection Configuration:**
Connection parameters (hostname and user) are configured in sync_core.ps1. Port is implicit (default 22) and not exposed as a config variable. Default target: `137.248.186.51` (root@22).

**What it syncs:**
- `data/counters/`
- `data/db_public/`
- `data/metadata/`
- `data/exports/`
- `data/blacklab_export/`
- Stats databases: `data/db/stats_files.db`, `data/db/stats_country.db`

**Recommended:** Use via orchestrator `LOKAL/_2_deploy/deploy_data.ps1`

---

### `sync_media.ps1`

**Purpose:** Synchronizes media files to production (transcripts, MP3 audio files).

**Status:** **Stable production transfer** - do not refactor transfer logic.

**Usage:**
```powershell
.\scripts\deploy_sync\sync_media.ps1 [-RepoRoot <path>] [-Force] [-ForceMP3]
```

**Key Parameters:**
- `-RepoRoot`: Path to webapp repository root (default: C:\dev\corapan-webapp)
- `-Force`: Force full resync of all media
- `-ForceMP3`: Force full resync of MP3 files only (transcripts remain delta)

**Connection Configuration:**
Connection parameters (hostname and user) are configured in sync_core.ps1. Port is implicit (default 22) and not exposed as a config variable. Default target: `137.248.186.51` (root@22).

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
- `-Hostname`: Production server hostname/IP (default: 137.248.186.51)
- `-User`: SSH user (default: root)
- `-Port`: SSH port (default: 22)
- `-DataDir`: Remote data directory (default: /srv/webapps/corapan/data)
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

### Separation of Concerns

- **Data and Media are separate operations** - no `deploy_all` script exists by design
- Each sync operation can fail independently
- Easier to debug and monitor specific transfer types

### DryRun Expectation

Entry points have varying DryRun support:
- `publish_blacklab_index.ps1`: **Supports `-DryRun`** - shows planned actions without executing
- `sync_data.ps1`: **No DryRun support** - executes delta sync based on manifest
- `sync_media.ps1`: **No DryRun support** - executes delta sync based on manifest

For data/media syncs, the manifest-based delta sync mechanism provides safety by only transferring changed files.

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

**Data deploy with logging:**
```powershell
.\LOKAL\_2_deploy\deploy_data.ps1
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
