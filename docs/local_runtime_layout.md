# Local Runtime Root Layout

**Status:** Optional; recommended for production-like local development  
**Branch:** `work/current`  
**Date:** 2026-01-17

---

## Motivation

By default, the repository expects data, media, and logs to be at the root level:
```
corapan-webapp/
  ├── data/
  ├── media/
  ├── logs/
  └── ... (app code)
```

**Problem:** This doesn't match production structure, which separates application from runtime data:
```
/srv/corapan/
  ├── app/                    ← Application code (read-only)
  ├── config/                 ← Configuration (secrets, not in repo)
  ├── data/                   ← Runtime data (databases, indexes, exports)
  ├── media/                  ← Media files (transcripts, audio)
  └── logs/                   ← Application logs
```

**Solution:** Use a **local runtime root** on your dev machine that mirrors production, while keeping the repo unchanged.

---

## Recommended Local Layout

For Windows developers, create this structure **outside the repository**:

```powershell
# Example (adjust drive/path as needed)
C:\dev\runtime\corapan\
  ├── app/                    ← Symlink or direct reference to repo root
  ├── config/                 ← Local config (JWT keys, secrets)
  ├── data/
  │   ├── db/                 ← SQLite or PostgreSQL data
  │   ├── blacklab_export/    ← Export TSV, metadata
  │   ├── blacklab_index/     ← Lucene index (regenerable)
  │   ├── counters/           ← Search counters cache
  │   ├── exports/            ← User/API exports
  │   └── metadata/           ← Metadata cache
  ├── media/
  │   ├── transcripts/        ← JSON corpus (canonical)
  │   ├── mp3-full/           ← Full-length audio
  │   ├── mp3-split/          ← Segment audio
  │   └── mp3-temp/           ← Temporary processing
  └── logs/
      └── app.log             ← Application logs
```

---

## Setup Instructions

### Option A: Recommended (No Symlinks)

1. **Create the runtime directory:**
   ```powershell
   mkdir -p C:\dev\runtime\corapan\{config,data,media,logs}
   ```

2. **Set the environment variable (persistent, via System Properties):**
   ```powershell
   # One-time setup (PowerShell as Admin)
   [Environment]::SetEnvironmentVariable(
       "CORAPAN_RUNTIME_ROOT",
       "C:\dev\runtime\corapan",
       "User"
   )
   # Then restart your terminal or dot-source your profile
   ```

   Or for **temporary dev session only:**
   ```powershell
   $env:CORAPAN_RUNTIME_ROOT = "C:\dev\runtime\corapan"
   ```

3. **Copy initial data (optional, for fresh setup):**
   ```powershell
   # If you have existing corpus data:
   cp -Recurse "C:\dev\corapan-webapp\media\transcripts" "C:\dev\runtime\corapan\media\"
   cp -Recurse "C:\dev\corapan-webapp\media\mp3-*" "C:\dev\runtime\corapan\media\"
   ```

4. **Run dev setup:**
   ```powershell
   cd C:\dev\corapan-webapp
   .\scripts\dev-setup.ps1
   # Scripts will automatically use CORAPAN_RUNTIME_ROOT if set, otherwise fall back to repo-relative paths
   ```

### Option B: With Symlink (Windows 10+)

If you want the `app/` subdirectory to point to your repo:

```powershell
# PowerShell as Admin
cmd /c mklink /d "C:\dev\runtime\corapan\app" "C:\dev\corapan-webapp"
```

Then scripts can reference `$CORAPAN_RUNTIME_ROOT/app/` for code and other subdirs for data.

---

## Environment Variable: `CORAPAN_RUNTIME_ROOT`

### Configuration

| Aspect | Value |
|--------|-------|
| **Name** | `CORAPAN_RUNTIME_ROOT` |
| **Type** | File system path (absolute) |
| **Default** | If not set, scripts fall back to repository-relative paths (original behavior) |
| **Scope** | User environment variable (persists across sessions) |
| **Windows Path Example** | `C:\dev\runtime\corapan` |
| **Linux/Mac Path Example** | `/home/user/runtime/corapan` or `~/corapan-runtime` |

### How Scripts Use It

BlackLab and other local-development scripts check for `CORAPAN_RUNTIME_ROOT`:

```powershell
# Pseudo-code (actual implementation in scripts/blacklab/build_blacklab_index.ps1)
if ($env:CORAPAN_RUNTIME_ROOT) {
    $DATA_ROOT = Join-Path $env:CORAPAN_RUNTIME_ROOT "data"
    $MEDIA_ROOT = Join-Path $env:CORAPAN_RUNTIME_ROOT "media"
    Write-Host "Using runtime root: $env:CORAPAN_RUNTIME_ROOT"
} else {
    # Fallback: use repo-relative paths (backward compatible)
    $DATA_ROOT = Join-Path $repoRoot "data"
    $MEDIA_ROOT = Join-Path $repoRoot "media"
    Write-Host "CORAPAN_RUNTIME_ROOT not set; using repo-relative paths"
}
```

**Result:** No breaking changes. Existing workflows continue to work.

---

## Directory Purposes

### `app/` (Application Code)

| Attribute | Value |
|-----------|-------|
| **Content** | Repository code (read-only during runtime) |
| **Option A** | Direct reference: scripts use `$repoRoot` as-is |
| **Option B** | Symlink to repo: `mklink /d app C:\dev\corapan-webapp` |
| **In Scripts** | Referenced via `$repoRoot` (unchanged by this feature) |

---

### `config/` (Runtime Configuration)

| Attribute | Value |
|-----------|-------|
| **Content** | Local secrets, JWT keys, database credentials |
| **Examples** | `config/keys/jwt_secret.key`, `config/.env.local` |
| **Git Status** | NOT tracked; must be created per environment |
| **In Docker** | Mounted as `-v $CORAPAN_RUNTIME_ROOT/config:/config` |
| **Notes** | Production copy is managed by deployment system (Kubernetes secrets, etc.) |

---

### `data/` (Runtime Databases & Indexes)

| Attribute | Value |
|-----------|-------|
| **Content** | SQLite/PostgreSQL data, BlackLab indexes, exports, metadata caches |
| **Regenerable?** | Mostly yes (indexes rebuild in hours; metadata from exports) |
| **Git Status** | NOT tracked |
| **Backup** | Backup before production sync; include in dev machine backup |
| **Size** | ~10–50 GB (depends on corpus size and indexes) |

**Sub-directories:**
- `data/db/` — SQLite auth database (dev fallback)
- `data/db_public/` — Optional public data snapshots
- `data/blacklab_export/` — TSV + metadata for indexing
- `data/blacklab_index/` — Lucene search index
- `data/counters/` — Search counter cache
- `data/exports/` — User/API exports
- `data/metadata/` — Metadata caches

---

### `media/` (Corpus & Audio Files)

| Attribute | Value |
|-----------|-------|
| **Content** | Transcripts (JSON), full MP3s, segment audio |
| **Canonical** | `media/transcripts/` is the source of truth |
| **Size** | ~10–100 GB (depends on corpus) |
| **Git Status** | NOT tracked |
| **Sync** | Can be synced from production or other sources |
| **Fallback** | If `CORAPAN_RUNTIME_ROOT` not set, uses `<repo>/media/` |

**Sub-directories:**
- `media/transcripts/` — JSON corpus (canonical source)
- `media/mp3-full/` — Full-length recordings
- `media/mp3-split/` — Segment-level clips (regenerable)
- `media/mp3-temp/` — Temporary processing scratch space

---

### `logs/` (Application Logs)

| Attribute | Value |
|-----------|-------|
| **Content** | Flask app logs, Docker logs, build logs |
| **Size** | ~1–10 MB (with log rotation) |
| **Git Status** | NOT tracked |
| **Retention** | Implement log rotation (e.g., `logrotate` on Linux or PowerShell task on Windows) |

---

## Workflow Examples

### Example 1: Development with Runtime Root

**Setup (once):**
```powershell
$env:CORAPAN_RUNTIME_ROOT = "C:\dev\runtime\corapan"

# Create directories
mkdir -p "$env:CORAPAN_RUNTIME_ROOT/{config,data,media,logs}"

# Copy corpus from repo (or sync from production)
cp -Recurse "C:\dev\corapan-webapp\media\transcripts" "$env:CORAPAN_RUNTIME_ROOT\media\"
```

**Daily development:**
```powershell
cd C:\dev\corapan-webapp
# CORAPAN_RUNTIME_ROOT is already set; scripts use it automatically
.\scripts\dev-setup.ps1

# Logs go to:
# C:\dev\runtime\corapan\logs\
```

### Example 2: Production-like Staging

**Setup (mirrors production):**
```powershell
# On staging machine
$RUNTIME = "C:\staging\corapan"
[Environment]::SetEnvironmentVariable("CORAPAN_RUNTIME_ROOT", $RUNTIME, "User")

# Restore data from production backup
Expand-Archive ".\backups\prod_data.zip" "$RUNTIME\data\"
Expand-Archive ".\backups\prod_media.zip" "$RUNTIME\media\"
```

**Deploy & Test:**
```powershell
cd C:\staging\code\corapan-webapp  # App code from repo
.\scripts\blacklab\build_blacklab_index.ps1
# Uses $RUNTIME/data/blacklab_export → $RUNTIME/data/blacklab_index
```

### Example 3: No Runtime Root (Backward Compatibility)

**Old behavior still works:**
```powershell
# No CORAPAN_RUNTIME_ROOT set
cd C:\dev\corapan-webapp
.\scripts\dev-setup.ps1

# Scripts fall back to repo-relative paths:
# data/ → C:\dev\corapan-webapp\data\
# media/ → C:\dev\corapan-webapp\media\
# logs/ → C:\dev\corapan-webapp\logs\
```

---

## Migration Path (Not Required)

If you currently have data in your repo and want to move to runtime root:

1. **Set `CORAPAN_RUNTIME_ROOT`:**
   ```powershell
   $env:CORAPAN_RUNTIME_ROOT = "C:\dev\runtime\corapan"
   mkdir -p "$env:CORAPAN_RUNTIME_ROOT/{config,data,media,logs}"
   ```

2. **Migrate data (one-time):**
   ```powershell
   # Copy existing data
   cp -Recurse "C:\dev\corapan-webapp\data\*" "$env:CORAPAN_RUNTIME_ROOT\data\"
   cp -Recurse "C:\dev\corapan-webapp\media\*" "$env:CORAPAN_RUNTIME_ROOT\media\"
   ```

3. **Update repo (optional cleanup, see caveats):**
   ```powershell
   cd C:\dev\corapan-webapp
   # Remove old copies (keep .gitkeep for structure)
   rm -Recurse "data/*" -Exclude ".gitkeep"
   rm -Recurse "media/*" -Exclude ".gitkeep"
   git add data/ media/
   git commit -m "chore: clear local data (using CORAPAN_RUNTIME_ROOT)"
   ```

**Caveat:** Only do this if you're sure all data is safe elsewhere. Better to keep repo-relative data and use both (old and new) until everyone is migrated.

---

## Docker Integration

If using Docker for database or BlackLab:

### Volume Mounts (Updated Composition)

**Old (repo-relative):**
```yaml
volumes:
  - ./data/blacklab_export:/data/export:ro
  - ./data/blacklab_index:/data/index:rw
```

**New (runtime root aware, pseudo-code in compose override):**
```yaml
# If CORAPAN_RUNTIME_ROOT is set, compose should use:
volumes:
  - ${CORAPAN_RUNTIME_ROOT:-./data}/blacklab_export:/data/export:ro
  - ${CORAPAN_RUNTIME_ROOT:-./data}/blacklab_index:/data/index:rw
```

Or, set `docker-compose.override.yml` per environment:

```yaml
# docker-compose.override.yml (not in repo)
version: "3.8"
services:
  blacklab-server-v3:
    volumes:
      - ${CORAPAN_RUNTIME_ROOT}/data/blacklab_export:/data/export:ro
      - ${CORAPAN_RUNTIME_ROOT}/data/blacklab_index:/data/index:rw
```

---

## Troubleshooting

### Q: I set `CORAPAN_RUNTIME_ROOT`, but scripts still use repo-relative paths.

**A:** Environment variable changes don't apply to already-running shells. Restart your terminal.

```powershell
# Restart PowerShell or reload profile
& $PROFILE
# or just close and re-open terminal
```

### Q: Can I use a relative path for `CORAPAN_RUNTIME_ROOT`?

**A:** Not recommended. Use absolute paths to avoid ambiguity when changing directories. If needed, resolve at script start:

```powershell
$runtimeRoot = $env:CORAPAN_RUNTIME_ROOT
if (-not [System.IO.Path]::IsPathRooted($runtimeRoot)) {
    $runtimeRoot = Resolve-Path (Join-Path (Get-Location) $runtimeRoot) | Select-Object -ExpandProperty Path
}
```

### Q: Does this work on Linux/Mac?

**A:** Yes. Adjust paths:

```bash
# Linux/Mac
export CORAPAN_RUNTIME_ROOT=/home/user/runtime/corapan
mkdir -p $CORAPAN_RUNTIME_ROOT/{config,data,media,logs}
```

Scripts that use PowerShell (`.ps1`) will need cross-platform alternatives (e.g., bash versions), but the principle is identical.

### Q: What if production uses `/srv/corapan/` and I use `C:\dev\runtime\corapan\`?

**A:** Structure is identical; paths are OS-specific. The important thing is the **layout**, not the absolute paths. Scripts should use relative subdirectories (`data/`, `media/`, etc.) off the root.

---

## Next Steps

1. **For Local Dev:** Optional; use only if you want production-like layout on your machine.
2. **For Staging:** Recommended; ensures staging matches production structure.
3. **For Production:** Not applicable (production uses server paths like `/srv/corapan/`).
4. **For CI/CD:** Set `CORAPAN_RUNTIME_ROOT` in pipeline configuration; scripts will use it automatically.

---

## Summary

| Aspect | Behavior |
|--------|----------|
| **Default Behavior** | Repo-relative paths (no change) |
| **With `CORAPAN_RUNTIME_ROOT` Set** | Uses `$RUNTIME_ROOT/data`, `$RUNTIME_ROOT/media`, etc. |
| **Fallback** | Always falls back to repo-relative if variable not set |
| **Breaking Changes** | None; fully backward compatible |
| **Migration Required?** | No; optional for developers who want production-like layout |
| **Docker Support** | Set `CORAPAN_RUNTIME_ROOT` in compose environment or override file |
| **Scripts Updated** | BlackLab build/indexing scripts only; others unchanged |

---

**Generated:** 2026-01-17 | **Branch:** `work/current` | **Status:** Recommended practice
