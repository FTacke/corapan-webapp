<#
.SYNOPSIS
    Debug minimal index using VEN TSV files to reproduce FileAlreadyExistsException.

.DESCRIPTION
    This script creates a temporary index and runs the IndexTool inside Docker
    with only the provided VEN TSV files (or default two problem files). It uses
    `--threads 1` to isolate the concurrency factor and outputs logs to
    `data/blacklab_index.debug_ven/build.log`.
#>

param(
    [string[]]$Files = @("2022-01-18_VEN_RCR.tsv", "2022-03-14_VEN_RCR.tsv"),
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Docker image (using latest BlackLab 5.x)
$BLACKLAB_IMAGE = "instituutnederlandsetaal/blacklab:latest"

# Paths
$repoRoot = Split-Path -Parent $PSScriptRoot
$EXPORT_DIR = Join-Path $repoRoot "data\blacklab_export"
$TSV_DIR = Join-Path $EXPORT_DIR "tsv"
$DEBUG_INDEX_DIR = Join-Path $repoRoot "data\blacklab_index.debug_ven"
$BLF_CONFIG = Join-Path $repoRoot "config\blacklab\corapan-tsv.blf.yaml"
$BUILD_LOG = Join-Path $DEBUG_INDEX_DIR "build.log"

Write-Host "Debug BlackLab VEN Index" -ForegroundColor Cyan
Write-Host "---------------------------------" -ForegroundColor Cyan
Write-Host "Using image: $BLACKLAB_IMAGE" -ForegroundColor Gray
Write-Host "Debug index: $DEBUG_INDEX_DIR" -ForegroundColor Gray
Write-Host "Files: $($Files -join ", ")" -ForegroundColor Gray
Write-Host ""

if (-not (Test-Path $TSV_DIR)) {
    Write-Host "ERROR: TSV directory not found: $TSV_DIR" -ForegroundColor Red
    exit 1
}

# Prepare debug index dir
if (Test-Path $DEBUG_INDEX_DIR) {
    if (-not $Force) {
        $confirm = Read-Host "Debug index already exists. Delete and continue? (j/n)"
        if ($confirm -ne 'j' -and $confirm -ne 'J') { Write-Host "Aborted."; exit 0 }
    }
    Remove-Item $DEBUG_INDEX_DIR -Recurse -Force
}
New-Item -ItemType Directory -Path $DEBUG_INDEX_DIR | Out-Null

# Create temp directory with only VEN files (IndexTool needs a directory, not individual files)
$tempTsvDir = Join-Path $repoRoot "data\.blacklab_temp_ven"
if (Test-Path $tempTsvDir) { Remove-Item $tempTsvDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempTsvDir | Out-Null

foreach ($file in $Files) {
    $sourcePath = Join-Path $TSV_DIR $file
    if (-not (Test-Path $sourcePath)) {
        Write-Host "ERROR: File not found: $sourcePath" -ForegroundColor Red
        Remove-Item $tempTsvDir -Recurse -Force
        exit 1
    }
    Copy-Item $sourcePath $tempTsvDir -Force
    Write-Host "  Copied: $file" -ForegroundColor Gray
}

# Build Docker mounts (windows path to docker path)
$tempTsvMount = $tempTsvDir.Replace('\', '/').Replace('C:', '/c')
$indexMount = $DEBUG_INDEX_DIR.Replace('\', '/').Replace('C:', '/c')
$configMount = (Join-Path $repoRoot "config\blacklab").Replace('\', '/').Replace('C:', '/c')

# IndexTool expects a directory path, not individual files
$dockerArgs = @(
    "run", "--rm"
    "-v", "${tempTsvMount}:/data/export:ro"
    "-v", "${indexMount}:/data/index:rw"
    "-v", "${configMount}:/config:ro"
    $BLACKLAB_IMAGE
    "java", "-cp", "/usr/local/lib/blacklab-tools/*"
    "nl.inl.blacklab.tools.IndexTool", "create"
    "/data/index"
    "/data/export"
    "/config/corapan-tsv.blf.yaml"
    "--linked-file-dir", "/data/export"
    "--threads", "1"
)

Write-Host "Docker command: docker $($dockerArgs -join ' ')" -ForegroundColor Gray

try {
    # Initialize build log
    $logHeader = "# Debug VEN Index Build Log - $(Get-Date -Format o) : $BLACKLAB_IMAGE`n"
    $logHeader | Out-File -FilePath $BUILD_LOG -Encoding utf8 -Force
    & docker $dockerArgs *>> $BUILD_LOG
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Index build failed. See log: $BUILD_LOG" -ForegroundColor Red
        Remove-Item $tempTsvDir -Recurse -Force -ErrorAction SilentlyContinue
        exit 1
    }
    Write-Host "OK: Debug index build completed successfully" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Exception: $_" -ForegroundColor Red
    Remove-Item $tempTsvDir -Recurse -Force -ErrorAction SilentlyContinue
    exit 1
} finally {
    # Clean up temp directory
    Remove-Item $tempTsvDir -Recurse -Force -ErrorAction SilentlyContinue
}

exit 0
