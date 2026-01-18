# Phase 18 — Media Runtime-Only Enforcement (No Fallbacks)

**Date:** 2026-01-18  
**Objective:** Enforce runtime-only media paths with **no fallbacks** to repo `./media`. App must fail hard if `CORAPAN_MEDIA_ROOT` is not configured.

## Changes

### 1. Config Enforcement ([src/app/config/__init__.py](../../src/app/config/__init__.py))

Removed all fallbacks to `PROJECT_ROOT / "media"`:

```python
# Media paths (runtime-configured, REQUIRED - no repo fallbacks)
_explicit_media_root = os.getenv("CORAPAN_MEDIA_ROOT")

if not _explicit_media_root:
    raise RuntimeError(
        "CORAPAN_MEDIA_ROOT environment variable is required.\n"
        "Media storage is mandatory for audio/transcripts paths.\n\n"
        "Setup:\n"
        "  - Dev: Run via scripts/dev-start.ps1 (auto-sets CORAPAN_MEDIA_ROOT)\n"
        "  - Production: export CORAPAN_MEDIA_ROOT=/path/to/runtime/media\n\n"
        "No fallbacks to repo media paths are supported."
    )

MEDIA_ROOT = Path(_explicit_media_root)
```

### 2. Dev Script Enhancement ([scripts/dev-start.ps1](../../scripts/dev-start.ps1))

Always sets `CORAPAN_MEDIA_ROOT` and creates required subdirectories:

```powershell
# Set CORAPAN_MEDIA_ROOT (REQUIRED - no fallbacks allowed)
if (-not $env:CORAPAN_MEDIA_ROOT) {
    $env:CORAPAN_MEDIA_ROOT = Join-Path $env:CORAPAN_RUNTIME_ROOT "media"
    Write-Host "INFO: CORAPAN_MEDIA_ROOT not set. Derived from runtime root:" -ForegroundColor Cyan
    Write-Host "   $env:CORAPAN_MEDIA_ROOT" -ForegroundColor Cyan
} else {
    Write-Host "Using CORAPAN_MEDIA_ROOT - custom: $env:CORAPAN_MEDIA_ROOT" -ForegroundColor Green
}

# Create required media subdirectories
$requiredMediaSubdirs = @("mp3-full", "mp3-split", "mp3-temp", "transcripts")
foreach ($subdir in $requiredMediaSubdirs) {
    $subdirPath = Join-Path $env:CORAPAN_MEDIA_ROOT $subdir
    if (-not (Test-Path $subdirPath)) {
        Write-Host "Creating media subdirectory: $subdir" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $subdirPath -Force | Out-Null
    }
}
```

## Evidence: Runtime-Only Media (./media Absent)

### Filesystem Proof

```powershell
# Repo media absent
PS C:\dev\corapan-webapp> Test-Path .\media
False

# Runtime media present with correct structure
PS C:\dev\corapan-webapp> Test-Path C:\dev\corapan-webapp\runtime\corapan\media\mp3-full
True

PS C:\dev\corapan-webapp> Test-Path C:\dev\corapan-webapp\runtime\corapan\media\transcripts
True

PS C:\dev\corapan-webapp> Test-Path C:\dev\corapan-webapp\runtime\corapan\media\mp3-full\ARG\2025-02-04_ARG_Mitre.mp3
True
```

### Config Resolution Logs

App startup confirms runtime-only media:

```
[2026-01-18 18:42:11,883] INFO in __init__: Media config: 
CORAPAN_MEDIA_ROOT=C:\dev\corapan-webapp\runtime\corapan\media 
MEDIA_ROOT=C:\dev\corapan-webapp\runtime\corapan\media 
AUDIO_FULL_DIR=C:\dev\corapan-webapp\runtime\corapan\media\mp3-full
AUDIO_SPLIT_DIR=C:\dev\corapan-webapp\runtime\corapan\media\mp3-split
AUDIO_TEMP_DIR=C:\dev\corapan-webapp\runtime\corapan\media\mp3-temp
TRANSCRIPTS_DIR=C:\dev\corapan-webapp\runtime\corapan\media\transcripts
```

## Contract

### Production
- `CORAPAN_MEDIA_ROOT` **must** be set explicitly via environment variable
- App will **not start** if missing (raises `RuntimeError`)
- No repo media fallbacks allowed

### Development
- `scripts/dev-start.ps1` automatically sets `CORAPAN_MEDIA_ROOT`
- Points to `runtime/corapan/media` (repo-local but gitignored)
- Creates required subdirectories if missing
- Validates proper runtime structure on startup

## Result

✅ Media is **strictly** runtime-only  
✅ Repo `./media` is not used and can remain absent  
✅ No config fallbacks to repo media paths  
✅ App fails hard if `CORAPAN_MEDIA_ROOT` not configured  

**Status:** Media runtime-only enforcement complete.
