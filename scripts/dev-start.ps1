<#
.SYNOPSIS
    Quick dev server start (assumes setup is already complete).

.DESCRIPTION
    Use this script for daily development after initial setup with dev-setup.ps1.
    - Checks if Docker services (Postgres + BlackLab) are running, starts them if not
    - Starts the Flask dev server

    For first-time setup or full reinstall, use: .\scripts\dev-setup.ps1

.EXAMPLE
    # Default: Postgres mode (starts Docker services if needed)
    .\scripts\dev-start.ps1

.EXAMPLE
    # Skip BlackLab (if you only need auth/basic features)
    .\scripts\dev-start.ps1 -SkipBlackLab
#>

[CmdletBinding()]
param(
    [switch]$SkipBlackLab
)

$ErrorActionPreference = 'Stop'

# Repository root
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

# ==============================================================================
# RUNTIME CONFIGURATION (REQUIRED)
# ==============================================================================

# Set CORAPAN_RUNTIME_ROOT to repo-local path (inside repo, not committed)
if (-not $env:CORAPAN_RUNTIME_ROOT) {
    # Runtime is now repo-local under $RepoRoot\runtime\corapan
    $env:CORAPAN_RUNTIME_ROOT = Join-Path $repoRoot "runtime\corapan"
    $isDefaultRuntime = $true
    Write-Host "INFO: CORAPAN_RUNTIME_ROOT not set. Using repo-local default:" -ForegroundColor Cyan
    Write-Host "   $env:CORAPAN_RUNTIME_ROOT" -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Cyan
} else {
    $isDefaultRuntime = $false
    Write-Host "Using CORAPAN_RUNTIME_ROOT - custom: $env:CORAPAN_RUNTIME_ROOT" -ForegroundColor Green
}

# Set CORAPAN_MEDIA_ROOT (REQUIRED - no fallbacks allowed)
if (-not $env:CORAPAN_MEDIA_ROOT) {
    $env:CORAPAN_MEDIA_ROOT = Join-Path $env:CORAPAN_RUNTIME_ROOT "media"
    Write-Host "INFO: CORAPAN_MEDIA_ROOT not set. Derived from runtime root:" -ForegroundColor Cyan
    Write-Host "   $env:CORAPAN_MEDIA_ROOT" -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Cyan
} else {
    Write-Host "Using CORAPAN_MEDIA_ROOT - custom: $env:CORAPAN_MEDIA_ROOT" -ForegroundColor Green
}

# Derive PUBLIC_STATS_DIR from CORAPAN_RUNTIME_ROOT
$env:PUBLIC_STATS_DIR = Join-Path $env:CORAPAN_RUNTIME_ROOT "data\public\statistics"

# Dev Postgres data dir (host path for docker volume)
$env:POSTGRES_DEV_DATA_DIR = Join-Path $env:CORAPAN_RUNTIME_ROOT "data\db\restricted\postgres_dev"

# Ensure runtime base directory exists
$runtimeBase = $env:CORAPAN_RUNTIME_ROOT
if (-not (Test-Path $runtimeBase)) {
    Write-Host "Creating runtime directory: $runtimeBase" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $runtimeBase -Force | Out-Null
}

# Ensure runtime media directory and required subdirectories exist
if (-not (Test-Path $env:CORAPAN_MEDIA_ROOT)) {
    Write-Host "Creating media directory: $env:CORAPAN_MEDIA_ROOT" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $env:CORAPAN_MEDIA_ROOT -Force | Out-Null
}

$requiredMediaSubdirs = @("mp3-full", "mp3-split", "mp3-temp", "transcripts")
foreach ($subdir in $requiredMediaSubdirs) {
    $subdirPath = Join-Path $env:CORAPAN_MEDIA_ROOT $subdir
    if (-not (Test-Path $subdirPath)) {
        Write-Host "Creating media subdirectory: $subdir" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $subdirPath -Force | Out-Null
    }
}

# Ensure runtime statistics directory exists
if (-not (Test-Path $env:PUBLIC_STATS_DIR)) {
    Write-Host "Creating statistics directory: $env:PUBLIC_STATS_DIR" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $env:PUBLIC_STATS_DIR -Force | Out-Null
}

# Ensure runtime restricted DB directory exists (for postgres_dev volume)
$restrictedDbDir = Split-Path -Parent $env:POSTGRES_DEV_DATA_DIR
if (-not (Test-Path $restrictedDbDir)) {
    Write-Host "Creating restricted DB directory: $restrictedDbDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $restrictedDbDir -Force | Out-Null
}

# Migrate legacy repo stats to runtime if needed
$repoStatsDir = Join-Path $repoRoot "data\public\statistics"
$repoStatsFile = Join-Path $repoStatsDir "corpus_stats.json"
$statsFile = Join-Path $env:PUBLIC_STATS_DIR "corpus_stats.json"
if (-not (Test-Path $statsFile) -and (Test-Path $repoStatsFile)) {
    Write-Host "INFO: Runtime stats missing; migrating legacy repo stats to runtime." -ForegroundColor Cyan
    & (Join-Path $repoRoot "scripts\migrate_stats_to_runtime.ps1")
}

# Check if statistics have been generated
if (-not (Test-Path $statsFile)) {
    Write-Host "" -ForegroundColor Yellow
    Write-Host "WARNING: STATISTICS NOT GENERATED" -ForegroundColor Yellow
    Write-Host "   corpus_stats.json not found at: $statsFile" -ForegroundColor Yellow
    Write-Host "" -ForegroundColor Yellow
    Write-Host "To generate statistics in one command, copy and run:" -ForegroundColor Cyan
    Write-Host "   python .\LOKAL\_0_json\05_publish_corpus_statistics.py --out `"$env:PUBLIC_STATS_DIR`"" -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Yellow
    Write-Host "Or generate CSVs first, then statistics:" -ForegroundColor Gray
    Write-Host "   python .\LOKAL\_0_json\04_internal_country_statistics.py" -ForegroundColor Gray
    Write-Host "   python .\LOKAL\_0_json\05_publish_corpus_statistics.py" -ForegroundColor Gray
    Write-Host "" -ForegroundColor Yellow
    Write-Host "Continuing startup... (API will return 404 for stats endpoints until generated)" -ForegroundColor Gray
    Write-Host "" -ForegroundColor Yellow
} else {
    $statsInfo = Get-Item $statsFile
    Write-Host "SUCCESS: Statistics found (generated: $(($statsInfo.LastWriteTime).ToString('yyyy-MM-dd HH:mm:ss')))" -ForegroundColor Green
}

Write-Host "" -ForegroundColor Yellow

# ==============================================================================
# DATABASE & SERVICE CONFIGURATION
# ==============================================================================
# Postgres is required (SQLite is deprecated)
$dbMode = "postgres"
# Use 127.0.0.1 instead of localhost to avoid DNS resolution issues with psycopg3 on Windows
$env:AUTH_DATABASE_URL = "postgresql+psycopg://corapan_auth:corapan_auth@127.0.0.1:54320/corapan_auth"
Write-Host "Database mode: PostgreSQL" -ForegroundColor Green

# Set common environment variables
$env:FLASK_SECRET_KEY = "dev-secret-change-me"
$env:JWT_SECRET_KEY = "dev-jwt-secret-change-me"
$env:FLASK_ENV = "development"
$env:ALLOW_PUBLIC_TRANSCRIPTS = "true"
$env:ALLOW_PUBLIC_FULL_AUDIO = "true"
$env:BLACKLAB_BASE_URL = "http://localhost:8081/blacklab-server"
$env:BLS_BASE_URL = "http://localhost:8081/blacklab-server"
if (-not $env:BLS_CORPUS) {
    $env:BLS_CORPUS = "index"
}

Write-Host "Starting CO.RA.PAN dev server..." -ForegroundColor Cyan
Write-Host "AUTH_DATABASE_URL = $($env:AUTH_DATABASE_URL)"

# Check and start Docker services if needed
$dockerAvailable = Get-Command docker -ErrorAction SilentlyContinue

if ($dockerAvailable) {
    $needsStart = @()

    # Check Postgres (always required)
    $pgRunning = docker ps --filter "name=corapan_auth_db" --format "{{.Names}}" 2>$null
    if (-not $pgRunning) {
        $needsStart += "corapan_auth_db"
    }

    # Check BlackLab (unless skipped)
    if (-not $SkipBlackLab) {
        $blRunning = docker ps --filter "name=blacklab-server-v3" --format "{{.Names}}" 2>$null
        if (-not $blRunning) {
            $needsStart += "blacklab-server-v3"
        }
    }

    if ($needsStart.Count -gt 0) {
        $servicesStr = $needsStart -join ", "
        Write-Host "Starting Docker services: $servicesStr" -ForegroundColor Yellow
        docker compose -f docker-compose.dev-postgres.yml up -d $needsStart

        # Wait briefly for Postgres if starting
        if ($needsStart -contains "corapan_auth_db") {
            Write-Host "Waiting for PostgreSQL..." -ForegroundColor Gray
            Start-Sleep -Seconds 5
        }
    } else {
        Write-Host "Docker services already running." -ForegroundColor Gray
    }
} else {
    Write-Host "WARN: Docker not available but Postgres is required for development." -ForegroundColor Red
}

# Run the dev server
Write-Host "`nStarting Flask dev server at http://localhost:8000" -ForegroundColor Cyan

# Use venv Python if available, otherwise fall back to system Python
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = "python"
}

Write-Host "Starting Flask dev server..." -ForegroundColor Cyan
Write-Host "NOTE: Server will run in foreground. Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

# Start server in current terminal (env vars are inherited)
& $venvPython -m src.app.main
