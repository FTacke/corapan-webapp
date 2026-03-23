<#
.SYNOPSIS
    Orchestrates media synchronization to production server
.DESCRIPTION
    Wrapper script that calls scripts/deploy_sync/sync_media.ps1 with proper
    logging and path resolution. Works from any directory.
    
    IMPORTANT: The underlying media transfer logic (rsync, delta, compression)
    in sync_media.ps1 is stable and production-tested. This orchestrator only
    provides logging and workflow convenience.
    
    Note: Connection parameters (hostname, user, port) are configured in
    the underlying sync_media.ps1 script.
.PARAMETER AppRepoPath
    Path to the active app repo root (default: auto-detected under workspace)
.PARAMETER Force
    Force full resync of all media (ignores manifest state)
.PARAMETER ForceMP3
    Force full resync of MP3 files only (transcripts remain delta)
.PARAMETER LogDir
    Directory for log files (default: LOKAL/_2_deploy/_logs)
.EXAMPLE
    .\LOKAL\_2_deploy\deploy_media.ps1
.EXAMPLE
    .\LOKAL\_2_deploy\deploy_media.ps1 -AppRepoPath "C:\dev\corapan\app" -ForceMP3
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [Alias("WebappRepoPath")]
    [string]$AppRepoPath,

    [Parameter(Mandatory = $false)]
    [switch]$Force,

    [Parameter(Mandatory = $false)]
    [switch]$ForceMP3,

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
        "scripts\deploy_sync\sync_media.ps1",
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

$SyncMediaScript = Join-Path $RepoRoot "scripts\deploy_sync\sync_media.ps1"
if (-not (Test-Path $SyncMediaScript)) {
    Write-Err "sync_media.ps1 not found at: $SyncMediaScript"
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
$LogFile = Join-Path $LogDir "deploy_media_$Timestamp.log"

Write-StepHeader "Deploy Media Orchestrator"
Write-Info "Timestamp:     $Timestamp"
Write-Info "Workspace:     $WorkspaceRoot"
Write-Info "App Repo:      $RepoRoot"
Write-Info "Force:         $Force"
Write-Info "ForceMP3:      $ForceMP3"
Write-Info "Log File:      $LogFile"
Write-Info "Workflow:      run after BlackLab publish and data deploy"

# ============================================================================
# EXECUTE SYNC
# ============================================================================

Write-StepHeader "Calling sync_media.ps1"

$SyncArgs = @{
    'RepoRoot' = $RepoRoot
}

if ($Force) {
    $SyncArgs['Force'] = $true
}

if ($ForceMP3) {
    $SyncArgs['ForceMP3'] = $true
}

try {
    Write-Info "Executing: $SyncMediaScript"
    Write-Info "Arguments: $($SyncArgs | ConvertTo-Json -Compress)"

    # Call sync_media.ps1 and capture output
    $Output = & $SyncMediaScript @SyncArgs 2>&1 | Tee-Object -FilePath $LogFile

    Write-StepHeader "Deploy Media Complete"
    Write-Success "Media sync finished successfully"
    Write-Info "Full log: $LogFile"
}
catch {
    Write-Err "Media sync failed"
    Write-Err $_.Exception.Message
    Write-Info "Error log: $LogFile"
    exit 1
}
