# BlackLab Wrapper Design Document
**Proposed `LOKAL/_1_blacklab/publish_blacklab.ps1` Design**

---

## Executive Summary

This document proposes a clean PowerShell wrapper script that orchestrates:
1. **Export** (Python module: `src.scripts.blacklab_index_creation`)
2. **Build** (PowerShell script: `scripts/blacklab/build_blacklab_index.ps1`)
3. **Publish** (PowerShell script: `scripts/deploy_sync/publish_blacklab_index.ps1`)

The wrapper provides a single entry point for the complete pipeline, with options to skip phases, dry-run, and fail-fast behavior.

---

## Wrapper Signature & Parameters

### PowerShell Function Signature

```powershell
[CmdletBinding()]
param(
    # ====== Paths & Configuration ======
    [string]$WebappRepoPath = (Resolve-Path "..\.." -ErrorAction Stop).Path,
    
    # ====== Production Server ======
    [string]$ProdHost = "137.248.186.51",
    [string]$ProdUser = "root",
    [int]$SshPort = 22,
    [string]$ProdDataDir = "/srv/webapps/corapan/data",
    [string]$ProdConfigDir = "/srv/webapps/corapan/app/config/blacklab",
    
    # ====== Phase Control ======
    [switch]$SkipExport,
    [switch]$SkipBuild,
    [switch]$SkipPublish,
    
    # ====== Execution Mode ======
    [switch]$WhatIf,          # Dry-run: print commands, don't execute
    [switch]$Force,           # Skip all confirmations
    
    # ====== Logging ======
    [string]$LogPath = (Join-Path ([Environment]::GetFolderPath("Desktop")) "corapan-publish.log"),
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
```

### Parameter Descriptions

#### **Path Parameters**

- **`-WebappRepoPath`**  
  Default: Resolves parent's parent directory (`..\..`) from script location  
  Example: `C:\dev\corapan-webapp`  
  Used by: Export module, Build script, Publish script

#### **Production Server Parameters**

- **`-ProdHost`**  
  Default: `"137.248.186.51"`  
  Example: `"marele.online.uni-marburg.de"` or IP  
  Purpose: SSH target for publishing

- **`-ProdUser`**  
  Default: `"root"`  
  Purpose: SSH user account

- **`-SshPort`**  
  Default: `22`  
  Purpose: Custom SSH port (if non-standard)

- **`-ProdDataDir`**  
  Default: `"/srv/webapps/corapan/data"`  
  Purpose: Remote path where BlackLab index lives

- **`-ProdConfigDir`**  
  Default: `"/srv/webapps/corapan/app/config/blacklab"`  
  Purpose: Remote path to BlackLab config (BLF files)

#### **Phase Control Flags**

- **`-SkipExport`**  
  Usage: Skip Python export phase; assume `data/blacklab_export/` already exists  
  Useful: For testing Build/Publish without re-exporting

- **`-SkipBuild`**  
  Usage: Skip Docker build phase; assume `data/blacklab_index/` already exists  
  Useful: For testing Publish without rebuilding

- **`-SkipPublish`**  
  Usage: Run Export + Build only; do not publish to production  
  Useful: For staging/testing index locally

#### **Execution Mode Flags**

- **`-WhatIf`**  
  Usage: Print all commands that would be executed; don't actually run them  
  Useful: Plan execution, verify parameters before committing

- **`-Force`**  
  Usage: Don't prompt for user confirmation at any stage  
  Useful: Automated/scripted execution (CI/CD context)

#### **Logging Parameters**

- **`-LogPath`**  
  Default: `C:\Users\{user}\Desktop\corapan-publish.log`  
  Usage: All operations logged here (append mode)  
  Contains: Timestamps, phase names, command outputs, errors

- **`-Verbose`**  
  Usage: Print detailed debug info to console (in addition to log file)

---

## Wrapper Internal Structure

### Phase 1: Initialization & Validation

```powershell
# 1. Resolve repo root and verify it exists
# 2. Check WebappRepoPath is valid git repo
# 3. Create/open log file
# 4. Print banner with parameters
# 5. Confirm parameters with user (unless -Force)
```

### Phase 2: Export (Optional, unless -SkipExport)

**Command Invoked:**
```powershell
$cmd = "python -m src.scripts.blacklab_index_creation --format tsv"
& cmd /c $cmd  # or use python directly
```

**Expected Outcome:**
- `data/blacklab_export/tsv/*.tsv` created
- `data/blacklab_export/docmeta.jsonl` created
- Exit code 0

**Error Handling:**
- If exit code ≠ 0 → Log error + exit
- If expected output files missing → Log error + exit

### Phase 3: Build (Optional, unless -SkipBuild)

**Command Invoked:**
```powershell
& ".\scripts\blacklab\build_blacklab_index.ps1" -Activate
```

**Expected Outcome:**
- `data/blacklab_index/` exists with files
- Build log in index directory
- Exit code 0

**Error Handling:**
- If exit code ≠ 0 → Log error + exit
- If index directory empty → Log error + exit

### Phase 4: Publish (Optional, unless -SkipPublish)

**Command Invoked:**
```powershell
& ".\scripts\deploy_sync\publish_blacklab_index.ps1" `
  -Host $ProdHost `
  -User $ProdUser `
  -Port $SshPort `
  -DataDir $ProdDataDir `
  -ConfigDir $ProdConfigDir
```

**Expected Outcome:**
- Remote index uploaded to `{ProdDataDir}/blacklab_index.new`
- Validation container confirms corpus "corapan" present
- Atomic swap: `blacklab_index.new` → `blacklab_index`
- Timestamped backup: `blacklab_index.bak_{timestamp}`
- Exit code 0

**Error Handling:**
- If exit code ∉ {0} → Log error + suggest rollback + exit

### Phase 5: Summary & Cleanup

```powershell
# Print success summary with timestamps
# Show backup location (if published)
# Offer quick verification commands
# Log completion timestamp
```

---

## Usage Examples

### Example 1: Full Pipeline (Export → Build → Publish)

```powershell
cd C:\dev\corapan-webapp\LOKAL\_1_blacklab
.\publish_blacklab.ps1
```

**Prompts user for confirmation, then:**
1. Exports JSON → TSV
2. Builds Docker index
3. Publishes to production
4. Validates remote index

### Example 2: Dry-Run (Preview without executing)

```powershell
.\publish_blacklab.ps1 -WhatIf -Verbose
```

**Output:** All commands printed to console/log, nothing executed

### Example 3: Build & Publish Only (Skip Export)

```powershell
.\publish_blacklab.ps1 -SkipExport -Force
```

**Executes:** Build + Publish phases only (assumes TSV already exists)

### Example 4: Export & Build Only (No Production)

```powershell
.\publish_blacklab.ps1 -SkipPublish
```

**Executes:** Export + Build (staging on local machine, no remote upload)

### Example 5: Custom Production Server

```powershell
.\publish_blacklab.ps1 `
  -ProdHost "staging.example.com" `
  -ProdUser "deploy" `
  -SshPort 2222 `
  -ProdDataDir "/var/lib/corapan/data"
```

### Example 6: Automation / CI Context

```powershell
.\publish_blacklab.ps1 `
  -Force `
  -WhatIf:$false `
  -LogPath "D:\logs\publish.log"
```

---

## Error Handling & Recovery

### Fail-Fast Behavior

All scripts follow `$ErrorActionPreference = "Stop"`:
- Any non-zero exit code → Wrapper stops immediately
- Logs error with context
- User can review log and retry

### Phase-Specific Recovery

| Phase | Failure | Recovery |
|-------|---------|----------|
| **Export** | Python module exits ≠0 | Check input JSON format, manually run export module |
| **Build** | Docker build fails | Check Docker running, image pulled, TSV exists |
| **Publish** | SSH fails | Check SSH installed, connectivity, credentials |
| **Publish** | Validation fails | Check BLF config, rebuild locally, investigate corpus |
| **Publish** | Swap fails | Use manual rollback command (provided in logs) |

### Manual Rollback Command

If publish fails at swap stage, script outputs:

```bash
# Provided for manual execution:
ssh root@137.248.186.51
mv /srv/webapps/corapan/data/blacklab_index /srv/webapps/corapan/data/blacklab_index.bad_2026-01-16_120000
mv /srv/webapps/corapan/data/blacklab_index.bak_2026-01-16_120000 /srv/webapps/corapan/data/blacklab_index
```

---

## Logging Format

**Log File:** `C:\Users\{user}\Desktop\corapan-publish.log` (or custom via `-LogPath`)

**Format:**
```
[2026-01-16 14:30:45] ========================================
[2026-01-16 14:30:45] BlackLab Wrapper v1.0
[2026-01-16 14:30:45] ========================================
[2026-01-16 14:30:45] Repo:              C:\dev\corapan-webapp
[2026-01-16 14:30:45] Prod Host:         137.248.186.51
[2026-01-16 14:30:45] Mode:              Full (Export → Build → Publish)
[2026-01-16 14:30:45]
[2026-01-16 14:30:45] [PHASE 1] Export
[2026-01-16 14:30:46] Running: python -m src.scripts.blacklab_index_creation --format tsv
[2026-01-16 14:35:22] Export completed: 42 TSV files, docmeta.jsonl written
[2026-01-16 14:35:22]
[2026-01-16 14:35:22] [PHASE 2] Build
[2026-01-16 14:35:23] Running: .\scripts\blacklab\build_blacklab_index.ps1
[2026-01-16 14:52:10] Build completed: index size 1.2 GB, activated
[2026-01-16 14:52:10]
[2026-01-16 14:52:10] [PHASE 3] Publish
[2026-01-16 14:52:11] Running: .\scripts\deploy_sync\publish_blacklab_index.ps1 ...
[2026-01-16 15:09:33] Upload completed: 42 files, 1.2 GB
[2026-01-16 15:09:45] Validation passed: corpus 'corapan', docs=12345, tokens=987654
[2026-01-16 15:09:46] Swap completed: backup at blacklab_index.bak_2026-01-16_150946
[2026-01-16 15:10:02] Production sanity check: OK
[2026-01-16 15:10:02]
[2026-01-16 15:10:02] ========================================
[2026-01-16 15:10:02] SUCCESS (Total time: ~40 minutes)
[2026-01-16 15:10:02] ========================================
```

---

## Integration with LOKAL Workflow

### Folder Structure (Proposed)

```
LOKAL/
├── _1_blacklab/
│   ├── publish_blacklab.ps1         ← NEW WRAPPER
│   ├── blacklab_export.py           (existing, reference only)
│   └── README.md                    (document wrapper usage)
├── _0_json/
└── ...
```

### Workflow for Operators

1. **Prepare:** Ensure JSON files in `media/transcripts/` are up-to-date
2. **Execute:**
   ```powershell
   cd LOKAL\_1_blacklab
   .\publish_blacklab.ps1
   ```
3. **Review:** Check log at `Desktop\corapan-publish.log`
4. **Verify:** Check production at `https://corapan.hispanistica.com/search`

---

## Dependencies & Assumptions

### Required Local Tools

- **PowerShell 5.1+** (built into Windows 10+)
- **Python 3.12+** (from project `requirements.txt`)
- **Docker Desktop** (for build phase)
- **OpenSSH** (for publish phase) — `Add-WindowsCapability -Online -Name OpenSSH.Client`

### Required Remote (Production)

- **Docker** (for validation container)
- **curl** (for health checks)
- **tar** or **scp** (for file transfer)

### Project Structure Assumptions

- Git repo at `$WebappRepoPath`
- `src/scripts/blacklab_index_creation.py` exists
- `scripts/blacklab/build_blacklab_index.ps1` exists
- `scripts/deploy_sync/publish_blacklab_index.ps1` exists
- `config/blacklab/corapan-tsv.blf.yaml` exists

---

## Testing Strategy (Pre-Implementation)

Before running full pipeline:

1. **Export Only:**
   ```powershell
   .\publish_blacklab.ps1 -SkipBuild -SkipPublish
   ```
   → Verify `data/blacklab_export/tsv/` has files

2. **Build Only (with existing TSV):**
   ```powershell
   .\publish_blacklab.ps1 -SkipExport -SkipPublish
   ```
   → Verify `data/blacklab_index/` is activated

3. **Dry-Run Full:**
   ```powershell
   .\publish_blacklab.ps1 -WhatIf
   ```
   → Verify command sequence is correct

4. **Full Pipeline (test environment):**
   ```powershell
   .\publish_blacklab.ps1 `
     -ProdHost "test.example.com" `
     -Force
   ```
   → Test on non-production server first

---

## Future Enhancements (Out of Scope)

1. **Parallel Execution:** Multiple export workers configured via wrapper
2. **Incremental Builds:** Only re-export/build changed files (hash-based)
3. **Rollback to Previous:** Wrapper offers interactive rollback menu
4. **Slack Notifications:** Post completion status to Slack
5. **Health Checks:** Periodic production corpus checks post-publish
6. **Index Scheduling:** Wrapper reads calendar to auto-publish on specific days

---

## Quick Reference

### Minimal Command (Full Pipeline)
```powershell
cd C:\dev\corapan-webapp\LOKAL\_1_blacklab
.\publish_blacklab.ps1
```

### Skip Export (Use Existing TSV)
```powershell
.\publish_blacklab.ps1 -SkipExport
```

### Local Only (No Production)
```powershell
.\publish_blacklab.ps1 -SkipPublish
```

### Dry-Run
```powershell
.\publish_blacklab.ps1 -WhatIf
```

### With Custom Log Path
```powershell
.\publish_blacklab.ps1 -LogPath "D:\logs\bl-publish.log"
```

### Automated (No Prompts)
```powershell
.\publish_blacklab.ps1 -Force
```

