<#
SYNOPSIS
    Combined developer start script: start BlackLab, then Flask, and wait for /health/bls

DESCRIPTION
    This convenience script starts BlackLab using the `start_blacklab_docker_v3.ps1` script
    (with optional restart policy), then starts the Flask dev server in the background.
    It waits for the Flask `/health/bls` endpoint to become healthy before returning.

PARAMETERS
    -Restart  - Pass --restart=unless-stopped to the BlackLab docker run command.
    -NoBlackLab - Skip starting BlackLab (useful if it's already running).
    -NoFlask - Skip starting Flask.
    -FlaskPort <int> - Port for Flask (default: 8000)
    -BlackLabPort <int> - Port for the BlackLab server (default: 8081)

#>

[CmdletBinding()]
param(
    [switch]$Restart,
    [switch]$NoBlackLab,
    [switch]$NoFlask,
    [int]$FlaskPort = 8000,
    [int]$BlackLabPort = 8081
)

$ErrorActionPreference = 'Stop'

# Repo root
$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Dev start: BlackLab + Flask" -ForegroundColor Cyan
Write-Host "Repo root: $repoRoot" -ForegroundColor Gray

if (-not $NoBlackLab) {
    Write-Host "Starting BlackLab (detached)..." -ForegroundColor Yellow
    $params = @{ 'Detach' = $true }
    if ($Restart) { $params['Restart'] = $true }
    $argsNormalized = ($params.GetEnumerator() | ForEach-Object { "-$($_.Key)" }) -join ' '
    $cmd = "./scripts/start_blacklab_docker_v3.ps1 $argsNormalized"
    Write-Host "Command: $cmd" -ForegroundColor Gray
    & ./scripts/start_blacklab_docker_v3.ps1 @params
}

# Start Flask if requested
if (-not $NoFlask) {
    # Find python executable in local venv if it exists
    $venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) { $pythonExe = $venvPython } else { $pythonExe = 'python' }

    # Skip if flask is already listening on the port
    $flaskListening = (netstat -ano | Select-String ":$FlaskPort") -ne $null
    if ($flaskListening) {
        Write-Host "Flask server already listening on port $FlaskPort - skipping start" -ForegroundColor Green
    } else {
        Write-Host "Starting Flask dev server (background)..." -ForegroundColor Yellow
        # Set environment var for dev
        $oldFlaskEnv = $env:FLASK_ENV
        $env:FLASK_ENV = 'development'

        # Start in background
        $proc = Start-Process -FilePath $pythonExe -ArgumentList '-m','src.app.main' -WorkingDirectory $repoRoot -NoNewWindow -PassThru
        Write-Host "Flask process started (pid: $($proc.Id))" -ForegroundColor Gray
    }
}

# Poll the Flask health endpoint until OK
Write-Host "Waiting for /health/bls to return ok=true ..." -ForegroundColor Yellow
$startTime = Get-Date
$timeoutSeconds = 120
$healthy = $false
while ( ((Get-Date) - $startTime).TotalSeconds -lt $timeoutSeconds -and -not $healthy ) {
    try {
        $resp = Invoke-RestMethod -Uri "http://localhost:$FlaskPort/health/bls" -UseBasicParsing -TimeoutSec 2
        if ($resp.ok -eq $true) {
            $healthy = $true
            break
        }
    } catch {
        # ignore and retry
    }
    Start-Sleep -Seconds 2
    $elapsed = [int] ((Get-Date) - $startTime).TotalSeconds
    if ($elapsed % 10 -eq 0) { Write-Host "  Waiting... ($elapsed/$timeoutSeconds seconds elapsed)" -ForegroundColor Gray }
}

if ($healthy) {
    Write-Host "Dev environment is healthy: /health/bls OK" -ForegroundColor Green
    Write-Host "BlackLab: http://localhost:$BlackLabPort/blacklab-server/" -ForegroundColor Cyan
    Write-Host "Flask: http://localhost:$FlaskPort" -ForegroundColor Cyan
} else {
    Write-Host "WARNING: /health/bls did not return ok=true within $timeoutSeconds seconds." -ForegroundColor Yellow
    Write-Host "Check Flask logs and BlackLab container logs." -ForegroundColor Gray
}

exit 0
