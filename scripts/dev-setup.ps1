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
    - Runtime directory initialization (repo-local)

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

# Repository root (scripts is under scripts/) — go up one level
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "`nCO.RA.PAN Dev-Setup" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host "Repository: $repoRoot"

# ==============================================================================
# RUNTIME CONFIGURATION (MUST BE EARLY - before any Python imports)
# ==============================================================================

# Set CORAPAN_RUNTIME_ROOT to repo-local path if not already configured
if (-not $env:CORAPAN_RUNTIME_ROOT) {
    $env:CORAPAN_RUNTIME_ROOT = Join-Path $repoRoot "runtime\corapan"
    Write-Host "INFO: CORAPAN_RUNTIME_ROOT not set. Using repo-local default:" -ForegroundColor Cyan
    Write-Host "   $env:CORAPAN_RUNTIME_ROOT" -ForegroundColor Cyan
}

# Derive PUBLIC_STATS_DIR from CORAPAN_RUNTIME_ROOT
$env:PUBLIC_STATS_DIR = Join-Path $env:CORAPAN_RUNTIME_ROOT "data\public\statistics"

# Ensure runtime directories exist BEFORE Python imports
$runtimeBase = $env:CORAPAN_RUNTIME_ROOT
if (-not (Test-Path $runtimeBase)) {
    Write-Host "Creating runtime directory: $runtimeBase" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $runtimeBase -Force | Out-Null
}

if (-not (Test-Path $env:PUBLIC_STATS_DIR)) {
    Write-Host "Creating statistics directory: $env:PUBLIC_STATS_DIR" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $env:PUBLIC_STATS_DIR -Force | Out-Null
}

# Determine database mode (Postgres is always required in dev)
$dbMode = "postgres"
# Use 127.0.0.1 instead of localhost to avoid DNS resolution issues with psycopg3 on Windows
$env:AUTH_DATABASE_URL = "postgresql+psycopg://corapan_auth:corapan_auth@127.0.0.1:54320/corapan_auth"
Write-Host "Database mode: PostgreSQL" -ForegroundColor Green

# Set common environment variables
$env:FLASK_SECRET_KEY = "dev-secret-change-me"
$env:JWT_SECRET_KEY = "dev-jwt-secret-change-me"
$env:FLASK_ENV = "development"
$env:BLACKLAB_BASE_URL = "http://localhost:8081/blacklab-server"

# ==============================================================================
# PYTHON BOOTSTRAP (DETERMINISTIC - must be before any Python calls)
# ==============================================================================
# NEVER call `python` without explicit path. ALWAYS use $venvPython or $venvPip.
$venvDir    = Join-Path $repoRoot '.venv'
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
        & docker compose -f docker-compose.dev-postgres.yml up -d @services 2>$null
        $composeExitCode = $LASTEXITCODE
        $ErrorActionPreference = 'Stop'
    } catch {
        $ErrorActionPreference = 'Stop'
        $composeExitCode = $LASTEXITCODE
    }
    
    if ($composeExitCode -ne 0) {
        Write-Host "ERROR: docker compose failed (exit code: $composeExitCode)" -ForegroundColor Red
        Write-Host "  Check: docker compose -f docker-compose.dev-postgres.yml logs" -ForegroundColor Gray
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
    $maxWait = 90
    $waited = 0
    $blReady = $false

    # Use curl.exe directly (not PowerShell curl alias which -> Invoke-WebRequest)
    $curlExe = Get-Command curl.exe -ErrorAction SilentlyContinue
    if (-not $curlExe) {
        Write-Host "WARN: curl.exe not found. Skipping BlackLab health check." -ForegroundColor Yellow
    } else {
        while ($waited -lt $maxWait) {
            # Use curl.exe with -fsS (fail silently, exit code = HTTP status)
            & curl.exe -fsS $blUrl *>$null
            if ($LASTEXITCODE -eq 0) {
                $blReady = $true
                break
            }
            Start-Sleep -Seconds 5
            $waited += 5
            Write-Host "  ... waiting for BlackLab ($waited seconds)" -ForegroundColor Gray
        }

        if ($blReady) {
            Write-Host "  BlackLab Server ready at $blUrl" -ForegroundColor Green
        } else {
            Write-Host "WARN: BlackLab not responding after ${maxWait}s at $blUrl" -ForegroundColor Yellow
            Write-Host "  Run: docker ps; docker logs blacklab-server-v3 --tail 200" -ForegroundColor Gray
        }
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
    Write-Host "  BLACKLAB_BASE_URL = $($env:BLACKLAB_BASE_URL)" -ForegroundColor Gray
    Write-Host "`n  Dev server will run in foreground. Press Ctrl+C to stop." -ForegroundColor Cyan
    Write-Host "  Open http://localhost:8000 in your browser" -ForegroundColor Cyan
    Write-Host "  Login: admin / $StartAdminPassword`n" -ForegroundColor Cyan

    & $venvPython -m src.app.main
} else {
    Write-Host "`n[5/5] Skipping dev server (-SkipDevServer)" -ForegroundColor Gray
}

Write-Host "`nDev-setup complete." -ForegroundColor Cyan
