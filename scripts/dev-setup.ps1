<#
.SYNOPSIS
    Full dev setup: install deps, create auth DB (optionally), start BlackLab (detached) and the dev server.

.DESCRIPTION
    Convenience helper for new developer machines or when you want a single command to start everything
    required for local development: Python deps, SQLite auth DB (only if missing or when forcing reset),
    BlackLab in Docker (detached) and finally the Flask dev server.

.EXAMPLE
    # Start everything (default behaviour)
    .\scripts\dev-setup.ps1

.EXAMPLE
    # Skip installing Python deps and start BlackLab + dev server
    .\scripts\dev-setup.ps1 -SkipInstall

.EXAMPLE
    # Reset auth DB and create initial admin with explicit password
    .\scripts\dev-setup.ps1 -ResetAuth -StartAdminPassword "change-me"
#>

[CmdletBinding()]
param(
    [switch]$SkipBlackLab,
    [switch]$SkipInstall,
    [switch]$SkipDevServer,
    [switch]$ResetAuth,
    [string]$DbPath = 'auth.db',
    [string]$StartAdminPassword = 'change-me',
    [switch]$RestartBlackLab
)

$ErrorActionPreference = 'Stop'

# repo root (scripts is under scripts/) — go up one level to reach repo root
# $PSScriptRoot is scripts, so parent is the repository root
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "Dev-setup starting in repository root: $repoRoot" -ForegroundColor Cyan

if (-not $SkipInstall) {
    Write-Host "\n[1/4] Installing Python requirements (using the active 'python')" -ForegroundColor Yellow

    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        Write-Host "ERROR: 'python' not found on PATH. Activate your virtualenv (e.g. .\.venv\Scripts\Activate.ps1) or install Python." -ForegroundColor Red
        exit 1
    }

    try {
        & python -m pip install -r requirements.txt
        & python -m pip install argon2_cffi
        Write-Host "Python requirements installed." -ForegroundColor Green
    } catch {
        Write-Host "WARN: Running pip install failed: $_" -ForegroundColor Yellow
        Write-Host "You can re-run with -SkipInstall to continue without installing." -ForegroundColor Gray
    }
} else {
    Write-Host "Skipping Python dependency installation (-SkipInstall)." -ForegroundColor Gray
}

# Step: ensure auth DB exists (unless we skip everything) or perform reset
if ($ResetAuth) {
    Write-Host "\n[2/4] Resetting auth DB ($DbPath) and creating initial admin" -ForegroundColor Yellow
    & python scripts/apply_auth_migration.py --db $DbPath --reset
    & python scripts/create_initial_admin.py --db $DbPath --username admin --password $StartAdminPassword
    Write-Host "Auth DB reset and admin created (username=admin)." -ForegroundColor Green
} else {
    if (-not (Test-Path $DbPath)) {
        Write-Host "\n[2/4] auth DB not found — creating DB and initial admin (username=admin)." -ForegroundColor Yellow
        & python scripts/apply_auth_migration.py --db $DbPath
        & python scripts/create_initial_admin.py --db $DbPath --username admin --password $StartAdminPassword
        Write-Host "Auth DB created and admin created." -ForegroundColor Green
    } else {
        Write-Host "\n[2/4] auth DB already present at $DbPath — skipping DB creation." -ForegroundColor Gray
    }
}

# Step: start BlackLab in background (unless skipped)
if (-not $SkipBlackLab) {
    Write-Host "\n[3/4] Starting BlackLab (detached Docker container)..." -ForegroundColor Yellow
    $blScript = Join-Path $PSScriptRoot 'blacklab\start_blacklab_docker_v3.ps1'
    if (-not (Test-Path $blScript)) {
        Write-Host "ERROR: BlackLab start script not found: $blScript" -ForegroundColor Red
    } else {
        $args = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $blScript, '-Detach')
        if ($RestartBlackLab) { $args += '-Restart' }

        try {
            Start-Process -FilePath (Get-Command powershell).Source -ArgumentList $args -WindowStyle Hidden -ErrorAction Stop | Out-Null
            Write-Host "Requested BlackLab start (background)." -ForegroundColor Green
        } catch {
            Write-Host "WARN: Could not start BlackLab: $_" -ForegroundColor Yellow
            Write-Host "You can start it manually: .\scripts\blacklab\start_blacklab_docker_v3.ps1 -Detach" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "Skipping BlackLab startup (-SkipBlackLab)." -ForegroundColor Gray
}

# Step: start dev server
if (-not $SkipDevServer) {
    Write-Host "\n[4/4] Starting dev server (Flask). This runs in the foreground; use a separate terminal if you want to keep using the shell." -ForegroundColor Yellow
    # We already started BlackLab (or requested it); pass -SkipBlackLab to dev-start.ps1 so it won't try to start it again
    & ${PSScriptRoot}\dev-start.ps1 -DbPath $DbPath -SkipBlackLab
} else {
    Write-Host "Skipping dev server startup (-SkipDevServer)." -ForegroundColor Gray
}

Write-Host "\nDev-setup finished." -ForegroundColor Cyan
