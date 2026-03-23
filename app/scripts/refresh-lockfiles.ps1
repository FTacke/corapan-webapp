$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[lockfiles] $Message"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv wurde nicht gefunden." -ForegroundColor Yellow
    Write-Host "Installiere uv (Windows PowerShell):" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\""
    exit 1
}

if (-not (Test-Path "requirements.in")) {
    throw "requirements.in nicht gefunden."
}

if (-not (Test-Path "requirements-dev.in")) {
    throw "requirements-dev.in nicht gefunden."
}

Write-Step "Kompiliere requirements.txt aus requirements.in"
uv pip compile requirements.in -o requirements.txt

Write-Step "Kompiliere requirements-dev.txt aus requirements-dev.in"
uv pip compile requirements-dev.in -o requirements-dev.txt

Write-Step "Fertig. Lockfiles wurden aktualisiert (keine Installation durchgeführt)."