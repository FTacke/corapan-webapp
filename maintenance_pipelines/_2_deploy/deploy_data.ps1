<#
.SYNOPSIS
    Orchestrates data synchronization and statistics deployment to production server
.DESCRIPTION
    Wrapper script that calls scripts/deploy_sync/tasks/sync_data.ps1 for the
    canonical data lane, including the built-in statistics step.
    Works from any directory.
    
    Data Sync:
    - Syncs runtime data directories: db/public, metadata, exports
      - Syncs stats databases: stats_files.db, stats_country.db
      - EXCLUDES production state: counters/, db/ (hard-protected)
    - EXCLUDES BlackLab data: handled separately via publish_blacklab.ps1
    
        Statistics Deployment:
            - Owned by sync_data.ps1 as the single canonical transfer point
            - Can be skipped via -SkipStatistics
    
    Connection Parameters:
      Configured in scripts/deploy_sync/sync_core.ps1
.PARAMETER AppRepoPath
    Path to the active app repo root (default: auto-detected under workspace)
.PARAMETER Force
    Force full resync (ignores manifest state)
.PARAMETER SkipStatistics
    Skip statistics upload (only sync data directories)
.PARAMETER LogDir
    Directory for log files (default: maintenance_pipelines/_2_deploy/_logs)
.EXAMPLE
    .\maintenance_pipelines\_2_deploy\deploy_data.ps1
.EXAMPLE
    .\maintenance_pipelines\_2_deploy\deploy_data.ps1 -Force
.EXAMPLE
    .\maintenance_pipelines\_2_deploy\deploy_data.ps1 -SkipStatistics
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [Alias("WebappRepoPath")]
    [string]$AppRepoPath,

    [Parameter(Mandatory = $false)]
    [switch]$Force,

    [Parameter(Mandatory = $false)]
    [switch]$SkipStatistics,

    [Parameter(Mandatory = $false)]
    [string]$LogDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Resolve-FullPath([string]$PathLike) {
    if ([System.IO.Path]::IsPathRooted($PathLike)) {
        return (Resolve-Path -LiteralPath $PathLike -ErrorAction Stop).Path
    }
    return (Resolve-Path -LiteralPath (Join-Path (Get-Location) $PathLike) -ErrorAction Stop).Path
}

function Test-AppRepoRoot([string]$CandidatePath) {
    if (-not (Test-Path -LiteralPath $CandidatePath -PathType Container)) {
        return $false
    }

    $requiredFiles = @(
        "scripts\deploy_sync\tasks\sync_data.ps1",
        "scripts\deploy_sync\sync_core.ps1"
    )

    foreach ($relativePath in $requiredFiles) {
        if (-not (Test-Path -LiteralPath (Join-Path $CandidatePath $relativePath) -PathType Leaf)) {
            return $false
        }
    }

    return $true
}

function Resolve-AppRepoRoot([string]$CandidatePath, [string]$WorkspaceRootPath) {
    $candidates = @()
    if ($CandidatePath) {
        $candidates += (Resolve-FullPath $CandidatePath)
    }
    else {
        $candidates += (Join-Path $WorkspaceRootPath "app")
    }

    foreach ($candidate in $candidates) {
        if (Test-AppRepoRoot $candidate) {
            return $candidate
        }
    }

    throw "Could not resolve active app repository. Checked: $($candidates -join ', ')"
}

function Write-StepHeader([string]$Message) {
    $line = "=" * 78
    Write-Host "`n$line" -ForegroundColor Cyan
    Write-Host " $Message" -ForegroundColor Cyan
    Write-Host "$line" -ForegroundColor Cyan
}

function Write-Info([string]$Message) {
    Write-Host "[INFO] $Message" -ForegroundColor White
}

function Write-Success([string]$Message) {
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warn([string]$Message) {
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Err([string]$Message) {
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# ============================================================================
# PATH RESOLUTION
# ============================================================================

$ScriptDir = $PSScriptRoot
$WorkspaceRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

try {
    $RepoRoot = Resolve-AppRepoRoot -CandidatePath $AppRepoPath -WorkspaceRootPath $WorkspaceRoot
}
catch {
    Write-Err "Cannot resolve AppRepoPath: $AppRepoPath"
    Write-Err $_.Exception.Message
    exit 1
}

if (-not (Test-Path $RepoRoot)) {
    Write-Err "Repo path does not exist: $RepoRoot"
    exit 1
}

$SyncDataScript = Join-Path $RepoRoot "scripts\deploy_sync\tasks\sync_data.ps1"
if (-not (Test-Path $SyncDataScript)) {
    Write-Err "tasks\\sync_data.ps1 not found at: $SyncDataScript"
    exit 1
}

# ============================================================================
# LOGGING SETUP
# ============================================================================

if (-not $LogDir) {
    $LogDir = Join-Path $ScriptDir "_logs"
}

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "deploy_data_$Timestamp.log"

Write-StepHeader "Deploy Data Orchestrator"
Write-Info "Timestamp:     $Timestamp"
Write-Info "Workspace:     $WorkspaceRoot"
Write-Info "App Repo:      $RepoRoot"
Write-Info "Force:         $Force"
Write-Info "Skip Stats:    $SkipStatistics"
Write-Info "Log File:      $LogFile"
Write-Info "Workflow:      publish_blacklab.ps1 before deploy_data.ps1"

# ============================================================================
# EXECUTE DATA SYNC
# ============================================================================

Write-StepHeader "Data Synchronization"
Write-Info ""
Write-Info "Protected production state (NEVER synced):"
Write-Info "  - data/counters (runtime state)"
Write-Info "  - data/db/ (auth, transcription databases)"
Write-Info ""
Write-Info "Syncing:"
Write-Info "  - data/db/public/"
Write-Info "  - data/metadata/"
Write-Info "  - data/exports/"
Write-Info "  - data/db/stats_files.db"
Write-Info "  - data/db/stats_country.db"
Write-Info ""
Write-Info "BlackLab note:"
Write-Info "  - data/blacklab/export is NOT deployed here"
Write-Info "  - use publish_blacklab.ps1 for export/build/publish"
Write-Info ""

$SyncArgs = @{
    'RepoRoot' = $RepoRoot
}

if ($Force) {
    $SyncArgs['Force'] = $true
    Write-Warn "Force mode enabled - all files will be synced"
}

if ($SkipStatistics) {
    $SyncArgs['SkipStatistics'] = $true
}

try {
    Write-Info "Executing: $SyncDataScript"

    # Call sync_data.ps1 and capture output
    $Output = & $SyncDataScript @SyncArgs 2>&1 | Tee-Object -FilePath $LogFile

    Write-Success "Data sync completed successfully"
}
catch {
    Write-Err "Data sync failed"
    Write-Err $_.Exception.Message
    Write-Info "Check log for details: $LogFile"
    exit 1
}

# ============================================================================
# COMPLETION
# ============================================================================

Write-StepHeader "Deploy Complete"
Write-Success "Deployment finished"
Write-Info "Full log: $LogFile"
Write-Host ""
