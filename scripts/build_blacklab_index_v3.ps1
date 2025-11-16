<#
.SYNOPSIS
    Compatibility wrapper for BlackLab index build.

.DESCRIPTION
    This script is kept for backward compatibility only. It delegates to the canonical
    build_blacklab_index.ps1 script. All new code should call build_blacklab_index.ps1 directly.

.PARAMETER SkipBackup
    Skip backing up the existing index (use with caution).

.PARAMETER Force
    Skip confirmation prompts.

.EXAMPLE
    .\scripts\build_blacklab_index_v3.ps1
    
    Standard index rebuild (delegates to build_blacklab_index.ps1).

.EXAMPLE
    .\scripts\build_blacklab_index_v3.ps1 -Force
    
    Rebuild without confirmation prompts (delegates to build_blacklab_index.ps1).

.NOTES
    DEPRECATED: Use scripts/build_blacklab_index.ps1 directly.
    This wrapper is maintained only for backward compatibility with existing workflows.
#>

param(
    [switch]$SkipBackup,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Yellow
Write-Host "Compatibility Wrapper (v3)" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "NOTE: This script delegates to build_blacklab_index.ps1" -ForegroundColor Yellow
Write-Host "      Please use that script directly in the future." -ForegroundColor Gray
Write-Host ""

# Get repository root (parent of scripts/)
$repoRoot = Split-Path -Parent $PSScriptRoot
$canonicalScript = Join-Path $repoRoot "scripts\build_blacklab_index.ps1"

if (-not (Test-Path $canonicalScript)) {
    Write-Host "ERROR: Canonical script not found: $canonicalScript" -ForegroundColor Red
    exit 1
}

# Build argument list for delegation
$delegateArgs = @()
if ($SkipBackup) { $delegateArgs += "-SkipBackup" }
if ($Force) { $delegateArgs += "-Force" }

Write-Host "Delegating to: $canonicalScript" -ForegroundColor Gray
if ($delegateArgs.Count -gt 0) {
    Write-Host "With arguments: $($delegateArgs -join ' ')" -ForegroundColor Gray
}
Write-Host ""

# Delegate to canonical script
& $canonicalScript @delegateArgs

exit $LASTEXITCODE
