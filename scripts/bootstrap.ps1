param(
    [switch]$Dev
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[bootstrap] $Message"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv wurde nicht gefunden." -ForegroundColor Yellow
    Write-Host "Installiere uv (Windows PowerShell):" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\""
    exit 1
}

if (-not (Test-Path ".python-version")) {
    throw ".python-version nicht gefunden. Abbruch."
}

if (-not (Test-Path "requirements.txt")) {
    throw "requirements.txt nicht gefunden. Abbruch."
}

$pythonVersion = (Get-Content ".python-version" -Raw).Trim()
if (-not $pythonVersion) {
    throw ".python-version ist leer. Abbruch."
}

Write-Step "Installiere/prüfe Python $pythonVersion via uv"
uv python install $pythonVersion

if (-not (Test-Path ".venv")) {
    Write-Step "Erstelle .venv"
    uv venv --python $pythonVersion .venv
} else {
    Write-Step "Verwende bestehende .venv"
}

$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Python-Interpreter in .venv nicht gefunden: $pythonExe"
}

Write-Step "Verwende Interpreter: $pythonExe"

Write-Step "Synchronisiere Runtime-Dependencies aus requirements.txt"
uv pip sync --python $pythonExe requirements.txt

if (Test-Path "requirements-dev.txt") {
    if ($Dev) {
        Write-Step "Synchronisiere Dev-Dependencies aus requirements-dev.txt"
        uv pip sync --python $pythonExe requirements-dev.txt
    } else {
        Write-Step "Dev-Lockfile gefunden. Für Dev-Tools optional: .\scripts\bootstrap.ps1 -Dev"
    }
}

Write-Host ""
Write-Host "Bootstrap abgeschlossen." -ForegroundColor Green
Write-Host "Nächste Schritte:"
Write-Host "  1) Optional: .venv aktivieren: .\.venv\Scripts\Activate.ps1"

if ((Test-Path ".env.example") -and (-not (Test-Path ".env"))) {
    Write-Host "  2) Falls benötigt: .env anlegen: Copy-Item .env.example .env"
} else {
    Write-Host "  2) .env prüfen (falls für deinen Run erforderlich)"
}

Write-Host "  3) App starten: python -m src.app.main"
Write-Host "  4) Tests (optional): pytest"