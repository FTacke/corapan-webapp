param(
    [string]$DbPath = 'auth.db',
    # By default start BlackLab in the background when launching the dev server.
    # You can opt-out with -SkipBlackLab if you don't want to start it.
    [switch]$SkipBlackLab
)

# Einfache Dev-Umgebung f�r CO.RA.PAN
# Startet den Flask-Server mit SQLite-Auth-DB im Repo-Root.

$env:FLASK_SECRET_KEY  = "dev-secret-change-me"
$env:JWT_SECRET        = "dev-jwt-secret-change-me"
$env:AUTH_DATABASE_URL = "sqlite:///$DbPath"
$env:FLASK_ENV         = "development"

Write-Host "Starting dev server with AUTH_DATABASE_URL=$($env:AUTH_DATABASE_URL)..."

# Start BlackLab in background (unless explicitly skipped)
if (-not $SkipBlackLab) {
    $blacklabScript = Join-Path $PSScriptRoot 'blacklab\start_blacklab_docker_v3.ps1'

    if (Test-Path $blacklabScript) {
        # Quick check: if Docker is not available, skip starting BlackLab and warn the user
        $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue

        if (-not $dockerCmd) {
            Write-Host 'WARN: Docker is not available on PATH — skipping automatic BlackLab startup. Use -SkipBlackLab if intentional.' -ForegroundColor Yellow
        }
        else {
            Write-Host 'Ensuring BlackLab is running in the background...' -ForegroundColor Cyan

            try {
                # Spawn a separate PowerShell process so `exit` calls in the helper won't kill this script.
                # Pass the script path as a separate argument (no manual quote escaping required)
                $args = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $blacklabScript, '-Detach')
                Start-Process -FilePath (Get-Command powershell).Source -ArgumentList $args -WindowStyle Hidden -ErrorAction Stop | Out-Null
                Write-Host 'Requested BlackLab start (background).' -ForegroundColor Green
            }
            catch {
                Write-Host "WARN: Failed to start BlackLab in background: $_" -ForegroundColor Yellow
                Write-Host 'You can start BlackLab manually with: .\scripts\blacklab\start_blacklab_docker_v3.ps1 -Detach' -ForegroundColor Gray
            }
        }
    }
    else {
        Write-Host "WARN: BlackLab start script not found: $blacklabScript" -ForegroundColor Yellow
    }
}
else {
    Write-Host 'Skipping BlackLab startup (SkipBlackLab was passed).' -ForegroundColor Gray
}

# Run the dev server (Flask)
python -m src.app.main
