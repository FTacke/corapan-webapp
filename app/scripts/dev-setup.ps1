<#
.SYNOPSIS
    Full dev setup: install deps, start Postgres + BlackLab (Docker), migrate auth DB, start dev server.

.DESCRIPTION
    One-liner to get a complete CO.RA.PAN development environment running:
    - Python virtualenv and dependencies
    - PostgreSQL (auth DB) via Docker
    - BlackLab Server via Docker
    - Auth DB migration
    - Flask dev server
    - Canonical sibling data/media runtime initialization

.EXAMPLE
    # Recommended: Full stack with Postgres + BlackLab
    .\scripts\dev-setup.ps1

.EXAMPLE
    # Skip installing Python deps (already installed)
    .\scripts\dev-setup.ps1 -SkipInstall

.EXAMPLE
    # Reset auth DB and create initial admin with explicit password
    .\scripts\dev-setup.ps1 -ResetAuth -StartAdminPassword "my-secret"
#>

[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$SkipBlackLab,
    [switch]$SkipDevServer,
    [switch]$ResetAuth,
    [string]$StartAdminPassword = 'change-me'
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

function Set-AppReleaseMetadataFromGitHub {
    param([Parameter(Mandatory = $true)][string]$ApiUrl)

    try {
        $headers = @{
            Accept = 'application/vnd.github+json'
            'User-Agent' = 'corapan-dev-setup'
        }
        $release = Invoke-RestMethod -Uri $ApiUrl -Headers $headers -Method Get -TimeoutSec 15 -ErrorAction Stop
        $releaseTag = [string]$release.tag_name
        $releaseUrl = [string]$release.html_url

        if ([string]::IsNullOrWhiteSpace($releaseTag) -or [string]::IsNullOrWhiteSpace($releaseUrl)) {
            throw "Latest release response did not contain tag_name and html_url."
        }

        $env:APP_RELEASE_TAG = $releaseTag.Trim()
        $env:APP_RELEASE_URL = $releaseUrl.Trim()
        Remove-Item Env:APP_VERSION -ErrorAction SilentlyContinue

        $displayVersion = $env:APP_RELEASE_TAG.TrimStart('v', 'V')
        Write-Host "Using latest official GitHub release for footer: v$displayVersion" -ForegroundColor Green
        Write-Host "Release URL: $($env:APP_RELEASE_URL)" -ForegroundColor Gray
    } catch {
        Remove-Item Env:APP_RELEASE_TAG -ErrorAction SilentlyContinue
        Remove-Item Env:APP_RELEASE_URL -ErrorAction SilentlyContinue
        Write-Host "Could not resolve latest official GitHub release. Footer release line stays hidden in dev." -ForegroundColor Yellow
        Write-Host "Reason: $($_.Exception.Message)" -ForegroundColor Gray
    }
}

# Repository root (scripts is under scripts/) — go up one level
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
$workspaceRoot = Split-Path -Parent $repoRoot
$composeFile = Join-Path $workspaceRoot "docker-compose.dev-postgres.yml"
$externalDataRoot = Join-Path $workspaceRoot "data"
$externalMediaRoot = Join-Path $workspaceRoot "media"
$useExternalRuntime = (Test-Path $externalDataRoot) -and (Test-Path $externalMediaRoot)

Write-Host "`nCO.RA.PAN Dev-Setup" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host "Workspace Root: $workspaceRoot"
Write-Host "App Root:       $repoRoot"

# ==============================================================================
# RUNTIME CONFIGURATION (MUST BE EARLY - before any Python imports)
# ==============================================================================

# Set canonical dev runtime roots.
if (-not $env:CORAPAN_RUNTIME_ROOT) {
    if (-not $useExternalRuntime) {
        throw "Canonical dev layout missing. Expected sibling data/ and media/ next to app/. Repo-local runtime/corapan is inactive in dev."
    }
    $env:CORAPAN_RUNTIME_ROOT = $workspaceRoot
    Write-Host "INFO: CORAPAN_RUNTIME_ROOT not set. Using canonical sibling dev runtime root:" -ForegroundColor Cyan
    Write-Host "   data -> $externalDataRoot" -ForegroundColor Cyan
    Write-Host "   media -> $externalMediaRoot" -ForegroundColor Cyan
    Write-Host "   runtime/corapan is inactive in dev" -ForegroundColor Cyan
    Write-Host "   $env:CORAPAN_RUNTIME_ROOT" -ForegroundColor Cyan
}

$legacyRuntimeRoot = Join-Path $repoRoot "runtime\corapan"
if ([System.IO.Path]::GetFullPath($env:CORAPAN_RUNTIME_ROOT) -eq [System.IO.Path]::GetFullPath($legacyRuntimeRoot)) {
    throw "Repo-local runtime/corapan is inactive in dev. Use the sibling workspace root instead."
}

if (-not $env:CORAPAN_MEDIA_ROOT) {
    $env:CORAPAN_MEDIA_ROOT = $externalMediaRoot
    Write-Host "INFO: CORAPAN_MEDIA_ROOT not set. Using canonical sibling media root:" -ForegroundColor Cyan
    Write-Host "   $env:CORAPAN_MEDIA_ROOT" -ForegroundColor Cyan
}

$legacyMediaRoot = Join-Path $legacyRuntimeRoot "media"
if ([System.IO.Path]::GetFullPath($env:CORAPAN_MEDIA_ROOT) -eq [System.IO.Path]::GetFullPath($legacyMediaRoot)) {
    throw "Repo-local runtime/corapan/media is inactive in dev. Use the sibling media root instead."
}

# Derive PUBLIC_STATS_DIR from CORAPAN_RUNTIME_ROOT
$env:PUBLIC_STATS_DIR = Join-Path $env:CORAPAN_RUNTIME_ROOT "data\public\statistics"

# Ensure runtime directories exist BEFORE Python imports
$runtimeBase = $env:CORAPAN_RUNTIME_ROOT
if (-not (Test-Path $runtimeBase)) {
    Write-Host "Creating runtime directory: $runtimeBase" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $runtimeBase -Force | Out-Null
}

if (-not (Test-Path $env:CORAPAN_MEDIA_ROOT)) {
    Write-Host "Creating media directory: $env:CORAPAN_MEDIA_ROOT" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $env:CORAPAN_MEDIA_ROOT -Force | Out-Null
}

foreach ($subdir in @('mp3-full', 'mp3-split', 'mp3-temp', 'transcripts')) {
    $subdirPath = Join-Path $env:CORAPAN_MEDIA_ROOT $subdir
    if (-not (Test-Path $subdirPath)) {
        Write-Host "Creating media subdirectory: $subdir" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $subdirPath -Force | Out-Null
    }
}

if (-not (Test-Path $env:PUBLIC_STATS_DIR)) {
    Write-Host "Creating statistics directory: $env:PUBLIC_STATS_DIR" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $env:PUBLIC_STATS_DIR -Force | Out-Null
}

# Determine database mode (Postgres is always required in dev)
$dbMode = "postgres"
# Use psycopg2 DSN in local dev because the checked-in dev environment installs psycopg2.
$env:AUTH_DATABASE_URL = "postgresql+psycopg2://corapan_auth:corapan_auth@127.0.0.1:54320/corapan_auth"
Write-Host "Database mode: PostgreSQL" -ForegroundColor Green

# Set common environment variables
$env:FLASK_SECRET_KEY = "dev-secret-change-me"
$env:JWT_SECRET_KEY = "dev-jwt-secret-change-me"
$env:FLASK_ENV = "development"
$env:BLS_BASE_URL = "http://localhost:8081/blacklab-server"
$env:BLACKLAB_BASE_URL = $env:BLS_BASE_URL
$env:BLS_CORPUS = "corapan"
$latestReleaseApiUrl = 'https://api.github.com/repos/FTacke/corapan-webapp/releases/latest'
Set-AppReleaseMetadataFromGitHub -ApiUrl $latestReleaseApiUrl

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
        "Run .\\scripts\\blacklab\\migrate_legacy_blacklab_dev_layout.ps1 -Apply before running full setup with BlackLab."
    )
}

$repoLocalDataRoot = Join-Path $repoRoot 'data'
if (-not $SkipBlackLab -and (Test-Path $repoLocalDataRoot)) {
    throw "Repo-local app/data exists. Dev BlackLab must use sibling data/blacklab, not app/data."
}

# ==============================================================================
# PYTHON BOOTSTRAP (DETERMINISTIC - must be before any Python calls)
# ==============================================================================
# NEVER call `python` without explicit path. ALWAYS use $venvPython or $venvPip.
$venvDir    = Join-Path $workspaceRoot '.venv'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
$venvPip    = Join-Path $venvDir 'Scripts\pip.exe'

Write-Host "`nPython bootstrap paths:" -ForegroundColor Cyan
Write-Host "  venv: $venvDir" -ForegroundColor Gray
Write-Host "  python: $venvPython" -ForegroundColor Gray
Write-Host "  pip: $venvPip" -ForegroundColor Gray

# ============================================================================
# Step 1: Python Environment
# ============================================================================
if (-not $SkipInstall) {
    Write-Host "`n[1/5] Setting up Python environment..." -ForegroundColor Yellow

    # Check for virtualenv
    if (-not (Test-Path $venvDir)) {
        Write-Host "  Creating virtual environment (.venv)..." -ForegroundColor Gray
        # System Python only for venv bootstrap (ONE TIME EXCEPTION)
        $sysPython = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $sysPython) {
            Write-Host "ERROR: 'python' not found in PATH. Install Python or add to PATH." -ForegroundColor Red
            exit 1
        }
        Write-Host "  Using system Python for bootstrap: $($sysPython.Source)" -ForegroundColor Gray
        & $sysPython.Source -m venv $venvDir
    }
    
    # Verify venv Python exists
    if (-not (Test-Path $venvPython)) {
        Write-Host "ERROR: venv Python not found at $venvPython" -ForegroundColor Red
        exit 1
    }
    
    # Safety check: venv Python must be functional
    Write-Host "  Verifying venv Python..." -ForegroundColor Gray
    try {
        & $venvPython -c "import sys, runpy; print('OK: ' + sys.executable)"
    } catch {
        Write-Host "ERROR: venv Python not functional: $_" -ForegroundColor Red
        exit 1
    }

    # Activate virtualenv if not already active
    $activateScript = Join-Path $venvDir 'Scripts\Activate.ps1'
    if (Test-Path $activateScript) {
        & $activateScript
    }

    Write-Host "  Installing Python requirements..." -ForegroundColor Gray
    try {
        & $venvPython -m pip install --quiet --upgrade pip
        & $venvPython -m pip install --quiet -r requirements.txt
        & $venvPython -m pip install --quiet argon2_cffi psycopg[binary]
        Write-Host "  Python requirements installed." -ForegroundColor Green
    } catch {
        Write-Host "WARN: pip install failed: $_" -ForegroundColor Yellow
        Write-Host "  You can re-run with -SkipInstall to continue." -ForegroundColor Gray
    }
} else {
    Write-Host "`n[1/5] Skipping Python installation (-SkipInstall)" -ForegroundColor Gray
}

# ============================================================================
# Step 2: Docker Services (Postgres + BlackLab)
# ============================================================================
$dockerAvailable = Get-Command docker -ErrorAction SilentlyContinue

if ($dbMode -eq "postgres" -or -not $SkipBlackLab) {
    Write-Host "`n[2/5] Starting Docker services..." -ForegroundColor Yellow

    if (-not $dockerAvailable) {
        Write-Host "ERROR: Docker not found on PATH. Install Docker Desktop to continue." -ForegroundColor Red
        exit 1
    }

    # Determine which services to start
    $services = @()
    if ($dbMode -eq "postgres") {
        $services += "corapan_auth_db"
    }
    if (-not $SkipBlackLab) {
        $services += "blacklab-server-v3"
    }

    $servicesStr = $services -join " "
    Write-Host "  Starting: $servicesStr" -ForegroundColor Gray

    # Clean up any conflicting containers first
    foreach ($svc in $services) {
        $existing = docker ps -aq --filter "name=$svc" 2>$null
        if ($existing) {
            Write-Host "  Removing existing container: $svc" -ForegroundColor Gray
            docker rm -f $svc 2>$null | Out-Null
        }
    }

    # Start services (suppress progress output)
    $composeExitCode = 0
    try {
        $ErrorActionPreference = 'Continue'
        & docker compose -f $composeFile up -d @services 2>$null
        $composeExitCode = $LASTEXITCODE
        $ErrorActionPreference = 'Stop'
    } catch {
        $ErrorActionPreference = 'Stop'
        $composeExitCode = $LASTEXITCODE
    }
    
    if ($composeExitCode -ne 0) {
        Write-Host "ERROR: docker compose failed (exit code: $composeExitCode)" -ForegroundColor Red
        Write-Host "  Check: docker compose -f $composeFile logs" -ForegroundColor Gray
        exit 1
    }

    # Wait for Postgres to be healthy and accepting connections
    if ($dbMode -eq "postgres") {
        Write-Host "  Waiting for PostgreSQL to be ready..." -ForegroundColor Gray
        $maxWait = 60
        $waited = 0
        $ready = $false

        while ($waited -lt $maxWait) {
            # Check if Postgres is responding
            $testResult = docker exec corapan_auth_db pg_isready -U corapan_auth -d corapan_auth 2>$null
            if ($LASTEXITCODE -eq 0) {
                $ready = $true
                break
            }
            Start-Sleep -Seconds 2
            $waited += 2
            Write-Host "    ... waiting ($waited seconds)" -ForegroundColor Gray
        }

        if ($ready) {
            Start-Sleep -Seconds 2
            Write-Host "  PostgreSQL is ready." -ForegroundColor Green
        } else {
            Write-Host "ERROR: PostgreSQL not ready after ${maxWait}s." -ForegroundColor Red
            Write-Host "  Check: docker logs corapan_auth_db" -ForegroundColor Gray
            exit 1
        }
    }
}

# ============================================================================
# Step 3: Auth DB Migration
# ============================================================================
Write-Host "`n[3/5] Auth database setup..." -ForegroundColor Yellow

# Verify venv Python exists
if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: venv Python not found. Setup incomplete." -ForegroundColor Red
    exit 1
}

# Postgres migration with error handling
if ($ResetAuth) {
    Write-Host "  Resetting Postgres auth DB..." -ForegroundColor Gray
    & $venvPython scripts/apply_auth_migration.py --engine postgres --reset
} else {
    Write-Host "  Applying Postgres migration..." -ForegroundColor Gray
    & $venvPython scripts/apply_auth_migration.py --engine postgres
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: PostgreSQL migration failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}
Write-Host "  PostgreSQL migration complete." -ForegroundColor Green

# Create initial admin if needed
Write-Host "  Ensuring admin user exists..." -ForegroundColor Gray
& $venvPython scripts/create_initial_admin.py --username admin --password $StartAdminPassword
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to create admin user." -ForegroundColor Red
    exit 1
}
Write-Host "  Postgres auth DB ready." -ForegroundColor Green

# ============================================================================
# Step 4: BlackLab Healthcheck (using curl.exe, not PowerShell curl)
# ============================================================================
if (-not $SkipBlackLab) {
    Write-Host "`n[4/5] Checking BlackLab Server..." -ForegroundColor Yellow
    $blUrl = "http://127.0.0.1:8081/blacklab-server/"
    $smokePattern = Get-BlackLabSmokePattern -WorkspaceRoot $workspaceRoot

    try {
        Test-BlackLabAvailability -BaseUrl $blUrl -SmokePattern $smokePattern -TimeoutSeconds 90
        Write-Host "  BlackLab Server ready and active index readable at $blUrl" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: BlackLab started, but the active index is not readable." -ForegroundColor Red
        Write-Host "  Smoke query: $smokePattern" -ForegroundColor Yellow
        Write-Host "  Stop blacklab-server-v3, rebuild with .\app\scripts\blacklab\build_blacklab_index.ps1, then start again." -ForegroundColor Yellow
        Write-Host "  Inspect: docker logs blacklab-server-v3 --tail 200" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "`n[4/5] Skipping BlackLab check (-SkipBlackLab)" -ForegroundColor Gray
}

# ============================================================================
# Step 5: Start Dev Server
# ============================================================================
if (-not $SkipDevServer) {
    Write-Host "`n[5/5] Starting Flask dev server..." -ForegroundColor Yellow
    Write-Host "  AUTH_DATABASE_URL = $($env:AUTH_DATABASE_URL)" -ForegroundColor Gray
    Write-Host "  BLS_BASE_URL = $($env:BLS_BASE_URL)" -ForegroundColor Gray
    Write-Host "  BLACKLAB_BASE_URL = $($env:BLACKLAB_BASE_URL) (legacy compatibility)" -ForegroundColor Gray
    Write-Host "  BLS_CORPUS = $($env:BLS_CORPUS)" -ForegroundColor Gray
    Write-Host "`n  Dev server will run in foreground. Press Ctrl+C to stop." -ForegroundColor Cyan
    Write-Host "  Open http://localhost:8000 in your browser" -ForegroundColor Cyan
    Write-Host "  Login: admin / $StartAdminPassword`n" -ForegroundColor Cyan

    & $venvPython -m src.app.main
} else {
    Write-Host "`n[5/5] Skipping dev server (-SkipDevServer)" -ForegroundColor Gray
}

Write-Host "`nDev-setup complete." -ForegroundColor Cyan
