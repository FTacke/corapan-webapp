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
    # SQLite mode (no Docker DB needed)
    .\scripts\dev-start.ps1 -UseSQLite

.EXAMPLE
    # Skip BlackLab (if you only need auth/basic features)
    .\scripts\dev-start.ps1 -SkipBlackLab
#>

[CmdletBinding()]
param(
    [switch]$UseSQLite,
    [switch]$SkipBlackLab
)

$ErrorActionPreference = 'Stop'

# Repository root
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

# ==============================================================================
# RUNTIME CONFIGURATION (REQUIRED)
# ==============================================================================

# Set CORAPAN_RUNTIME_ROOT if not already configured
if (-not $env:CORAPAN_RUNTIME_ROOT) {
    # Use sensible Windows-friendly default
    $env:CORAPAN_RUNTIME_ROOT = "C:\dev\runtime\corapan"
    $isDefaultRuntime = $true
    Write-Host "⚠️  CORAPAN_RUNTIME_ROOT not set. Using default:" -ForegroundColor Yellow
    Write-Host "   $env:CORAPAN_RUNTIME_ROOT" -ForegroundColor Yellow
    Write-Host "" -ForegroundColor Yellow
    Write-Host "To persist across sessions, set in PowerShell profile:" -ForegroundColor Gray
    Write-Host "   `$env:CORAPAN_RUNTIME_ROOT = '$env:CORAPAN_RUNTIME_ROOT'" -ForegroundColor Gray
    Write-Host "" -ForegroundColor Yellow
} else {
    $isDefaultRuntime = $false
    Write-Host "Using CORAPAN_RUNTIME_ROOT: $env:CORAPAN_RUNTIME_ROOT" -ForegroundColor Green
}

# Derive PUBLIC_STATS_DIR from CORAPAN_RUNTIME_ROOT
$env:PUBLIC_STATS_DIR = Join-Path $env:CORAPAN_RUNTIME_ROOT "data\public\statistics"

# Ensure runtime statistics directory exists
if (-not (Test-Path $env:PUBLIC_STATS_DIR)) {
    Write-Host "Creating statistics directory: $env:PUBLIC_STATS_DIR" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $env:PUBLIC_STATS_DIR -Force | Out-Null
}

# Check if statistics have been generated
$statsFile = Join-Path $env:PUBLIC_STATS_DIR "corpus_stats.json"
if (-not (Test-Path $statsFile)) {
    Write-Host "" -ForegroundColor Yellow
    Write-Host "⚠️  STATISTICS NOT GENERATED" -ForegroundColor Yellow
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
    Write-Host "✓ Statistics found (generated: $(($statsInfo.LastWriteTime).ToString('yyyy-MM-dd HH:mm:ss')))" -ForegroundColor Green
}

Write-Host "" -ForegroundColor Yellow

# ==============================================================================
# DATABASE & SERVICE CONFIGURATION
# ==============================================================================
if ($UseSQLite) {
    $dbMode = "sqlite"
    $dbPath = "data/db/auth.db"
    $env:AUTH_DATABASE_URL = "sqlite:///$dbPath"
    Write-Host "Database mode: SQLite" -ForegroundColor Yellow
} else {
    $dbMode = "postgres"
    # Use 127.0.0.1 instead of localhost to avoid DNS resolution issues with psycopg3 on Windows
    $env:AUTH_DATABASE_URL = "postgresql+psycopg://corapan_auth:corapan_auth@127.0.0.1:54320/corapan_auth"
    Write-Host "Database mode: PostgreSQL" -ForegroundColor Green
}

# Set common environment variables
$env:FLASK_SECRET_KEY = "dev-secret-change-me"
$env:JWT_SECRET_KEY = "dev-jwt-secret-change-me"
$env:FLASK_ENV = "development"
$env:BLACKLAB_BASE_URL = "http://localhost:8081/blacklab-server"

Write-Host "Starting CO.RA.PAN dev server..." -ForegroundColor Cyan
Write-Host "AUTH_DATABASE_URL = $($env:AUTH_DATABASE_URL)"

# Check and start Docker services if needed
$dockerAvailable = Get-Command docker -ErrorAction SilentlyContinue

if ($dockerAvailable) {
    $needsStart = @()

    # Check Postgres (unless SQLite mode)
    if ($dbMode -eq "postgres") {
        $pgRunning = docker ps --filter "name=corapan_auth_db" --format "{{.Names}}" 2>$null
        if (-not $pgRunning) {
            $needsStart += "corapan_auth_db"
        }
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
        & docker compose -f docker-compose.dev-postgres.yml up -d @needsStart

        # Wait briefly for Postgres if starting
        if ($needsStart -contains "corapan_auth_db") {
            Write-Host "Waiting for PostgreSQL..." -ForegroundColor Gray
            Start-Sleep -Seconds 5
        }
    } else {
        Write-Host "Docker services already running." -ForegroundColor Gray
    }
} elseif ($dbMode -eq "postgres") {
    Write-Host "WARN: Docker not available but Postgres mode selected. Use -UseSQLite if needed." -ForegroundColor Yellow
}

# Run the dev server
Write-Host "`nStarting Flask dev server at http://localhost:8000" -ForegroundColor Cyan

# Use venv Python if available, otherwise fall back to system Python
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    & $venvPython -m src.app.main
} else {
    python -m src.app.main
}
