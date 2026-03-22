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

function Get-BlackLabSmokePattern {
    param([Parameter(Mandatory = $true)][string]$WorkspaceRoot)

    $tsvDir = Join-Path $WorkspaceRoot 'data\blacklab\export\tsv'
    if (Test-Path $tsvDir) {
        $candidateFiles = @(Get-ChildItem -Path $tsvDir -Filter '*.tsv' -File | Where-Object { $_.Name -notlike '*_min.tsv' } | Sort-Object Name)
        foreach ($candidateFile in $candidateFiles) {
            $candidateLines = @(Get-Content -Path $candidateFile.FullName -TotalCount 25 | Select-Object -Skip 1)
            foreach ($line in $candidateLines) {
                if ([string]::IsNullOrWhiteSpace($line)) {
                    continue
                }

                $columns = $line -split "`t"
                if ($columns.Count -eq 0) {
                    continue
                }

                $token = $columns[0].Trim()
                if ([string]::IsNullOrWhiteSpace($token)) {
                    continue
                }

                $escapedToken = $token.Replace('\\', '\\\\').Replace('"', '\\"')
                return '[word="' + $escapedToken + '"]'
            }
        }
    }

    return '[word="casa"]'
}

function Test-BlackLabAvailability {
    param(
        [Parameter(Mandatory = $true)][string]$BaseUrl,
        [Parameter(Mandatory = $true)][string]$SmokePattern,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $rootReady = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $BaseUrl -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 404) {
                $rootReady = $true
                break
            }
        } catch {
        }

        Start-Sleep -Seconds 2
    }

    if (-not $rootReady) {
        throw "BlackLab root endpoint did not become ready within $TimeoutSeconds seconds"
    }

    $queryUrl = "${BaseUrl}corpora/corapan/hits?patt=$([System.Uri]::EscapeDataString($SmokePattern))&number=1"
    $queryResponse = Invoke-WebRequest -Uri $queryUrl -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    if ($queryResponse.StatusCode -ne 200) {
        throw "BlackLab smoke query returned HTTP $($queryResponse.StatusCode)"
    }
}

# Repository root
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
$workspaceRoot = Split-Path -Parent $repoRoot
$composeFile = Join-Path $workspaceRoot "docker-compose.dev-postgres.yml"
$externalDataRoot = Join-Path $workspaceRoot "data"
$externalMediaRoot = Join-Path $workspaceRoot "media"
$useExternalRuntime = (Test-Path $externalDataRoot) -and (Test-Path $externalMediaRoot)

# ==============================================================================
# RUNTIME CONFIGURATION (REQUIRED)
# ==============================================================================

# Set canonical dev runtime roots.
if (-not $env:CORAPAN_RUNTIME_ROOT) {
    if (-not $useExternalRuntime) {
        throw "Canonical dev layout missing. Expected sibling data/ and media/ next to webapp/. Repo-local runtime/corapan is inactive in dev."
    }
    $env:CORAPAN_RUNTIME_ROOT = $workspaceRoot
    Write-Host "INFO: CORAPAN_RUNTIME_ROOT not set. Using canonical sibling dev runtime root:" -ForegroundColor Cyan
    Write-Host "   $env:CORAPAN_RUNTIME_ROOT" -ForegroundColor Cyan
    Write-Host "   data -> $externalDataRoot" -ForegroundColor Cyan
    Write-Host "   media -> $externalMediaRoot" -ForegroundColor Cyan
    Write-Host "   runtime/corapan is inactive in dev" -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Cyan
    $isDefaultRuntime = $true
} else {
    $isDefaultRuntime = $false
    Write-Host "Using CORAPAN_RUNTIME_ROOT - custom: $env:CORAPAN_RUNTIME_ROOT" -ForegroundColor Green
}

$legacyRuntimeRoot = Join-Path $repoRoot "runtime\corapan"
if ([System.IO.Path]::GetFullPath($env:CORAPAN_RUNTIME_ROOT) -eq [System.IO.Path]::GetFullPath($legacyRuntimeRoot)) {
    throw "Repo-local runtime/corapan is inactive in dev. Use the sibling workspace root instead."
}

# Set CORAPAN_MEDIA_ROOT (REQUIRED - no fallbacks allowed)
if (-not $env:CORAPAN_MEDIA_ROOT) {
    $env:CORAPAN_MEDIA_ROOT = $externalMediaRoot
    Write-Host "INFO: CORAPAN_MEDIA_ROOT not set. Using canonical sibling media root:" -ForegroundColor Cyan
    Write-Host "   $env:CORAPAN_MEDIA_ROOT" -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Cyan
} else {
    Write-Host "Using CORAPAN_MEDIA_ROOT - custom: $env:CORAPAN_MEDIA_ROOT" -ForegroundColor Green
}

$legacyMediaRoot = Join-Path $legacyRuntimeRoot "media"
if ([System.IO.Path]::GetFullPath($env:CORAPAN_MEDIA_ROOT) -eq [System.IO.Path]::GetFullPath($legacyMediaRoot)) {
    throw "Repo-local runtime/corapan/media is inactive in dev. Use the sibling media root instead."
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

$statsFile = Join-Path $env:PUBLIC_STATS_DIR "corpus_stats.json"

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
# Use psycopg2 DSN in local dev because the checked-in dev environment installs psycopg2.
$env:AUTH_DATABASE_URL = "postgresql+psycopg2://corapan_auth:corapan_auth@127.0.0.1:54320/corapan_auth"
Write-Host "Database mode: PostgreSQL" -ForegroundColor Green

# Set common environment variables
$env:FLASK_SECRET_KEY = "dev-secret-change-me"
$env:JWT_SECRET_KEY = "dev-jwt-secret-change-me"
$env:FLASK_ENV = "development"
$env:ALLOW_PUBLIC_TRANSCRIPTS = "true"
$env:ALLOW_PUBLIC_FULL_AUDIO = "true"
$env:BLS_BASE_URL = "http://localhost:8081/blacklab-server"
$env:BLACKLAB_BASE_URL = $env:BLS_BASE_URL
$env:BLS_CORPUS = "corapan"

$blacklabRoot = Join-Path $workspaceRoot "data\blacklab"
$canonicalBlackLabDirs = @(
    $blacklabRoot,
    (Join-Path $blacklabRoot "index"),
    (Join-Path $blacklabRoot "export"),
    (Join-Path $blacklabRoot "backups"),
    (Join-Path $blacklabRoot "quarantine")
)

foreach ($directory in $canonicalBlackLabDirs) {
    if (-not (Test-Path $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }
}

$legacyBlackLabExport = Join-Path $workspaceRoot "data\blacklab_export"
$legacyBlackLabIndex = Join-Path $workspaceRoot "data\blacklab_index"
$canonicalBlackLabExport = Join-Path $blacklabRoot "export"
$canonicalBlackLabIndex = Join-Path $blacklabRoot "index"
$canonicalBlackLabExportContent = @(
    Get-ChildItem -Path $canonicalBlackLabExport -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne ".gitkeep" }
)
$canonicalBlackLabIndexContent = @(
    Get-ChildItem -Path $canonicalBlackLabIndex -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne ".gitkeep" }
)

if (
    -not $SkipBlackLab -and
    ((Test-Path $legacyBlackLabExport) -or (Test-Path $legacyBlackLabIndex)) -and
    ($canonicalBlackLabExportContent.Count -eq 0 -or $canonicalBlackLabIndexContent.Count -eq 0)
) {
    throw (
        "Legacy BlackLab dev layout detected under data\\blacklab_export or data\\blacklab_index, but the canonical tree data\\blacklab\\{index,export,backups,quarantine} is not populated. " +
        "Run .\\scripts\\blacklab\\migrate_legacy_blacklab_dev_layout.ps1 -Apply before starting BlackLab."
    )
}

$repoLocalDataRoot = Join-Path $repoRoot 'data'
if (-not $SkipBlackLab -and (Test-Path $repoLocalDataRoot)) {
    throw "Repo-local webapp/data exists. Dev BlackLab must use sibling data/blacklab, not webapp/data."
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
        docker compose -f $composeFile up -d $needsStart

        # Wait for Postgres to become ready before starting Flask.
        if ($needsStart -contains "corapan_auth_db") {
            Write-Host "Waiting for PostgreSQL..." -ForegroundColor Gray
            $maxWait = 60
            $waited = 0
            $pgReady = $false

            while ($waited -lt $maxWait) {
                docker exec corapan_auth_db pg_isready -U corapan_auth -d corapan_auth *>$null
                if ($LASTEXITCODE -eq 0) {
                    $pgReady = $true
                    break
                }
                Start-Sleep -Seconds 2
                $waited += 2
                Write-Host "  ... waiting for PostgreSQL ($waited seconds)" -ForegroundColor Gray
            }

            if (-not $pgReady) {
                Write-Host "ERROR: PostgreSQL not ready after ${maxWait}s." -ForegroundColor Red
                Write-Host "  Check: docker logs corapan_auth_db" -ForegroundColor Gray
                exit 1
            }
        }
    } else {
        Write-Host "Docker services already running." -ForegroundColor Gray
    }

    if (-not $SkipBlackLab) {
        $smokePattern = Get-BlackLabSmokePattern -WorkspaceRoot $workspaceRoot
        Write-Host "Validating BlackLab readiness with a live query..." -ForegroundColor Gray
        try {
            Test-BlackLabAvailability -BaseUrl "http://127.0.0.1:8081/blacklab-server/" -SmokePattern $smokePattern -TimeoutSeconds 90
            Write-Host "BlackLab is reachable and the active index answers search requests." -ForegroundColor Green
        } catch {
            Write-Host "ERROR: BlackLab is running but the active index is not readable." -ForegroundColor Red
            Write-Host "  Smoke query: $smokePattern" -ForegroundColor Yellow
            Write-Host "  Rebuild the index with .\webapp\scripts\blacklab\build_blacklab_index.ps1 after stopping blacklab-server-v3." -ForegroundColor Yellow
            Write-Host "  Inspect logs with: docker logs --tail 100 blacklab-server-v3" -ForegroundColor Yellow
            exit 1
        }
    }
} else {
    Write-Host "WARN: Docker not available but Postgres is required for development." -ForegroundColor Red
}

# Run the dev server
Write-Host "`nStarting Flask dev server at http://localhost:8000" -ForegroundColor Cyan

# Use workspace-root venv Python if available, otherwise fall back to system Python
$venvPython = Join-Path $workspaceRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = "python"
}

Write-Host "Starting Flask dev server..." -ForegroundColor Cyan
Write-Host "NOTE: Server will run in foreground. Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

# Start server in current terminal (env vars are inherited)
& $venvPython -m src.app.main
