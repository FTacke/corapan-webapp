param(
    [string]$DbPath = "auth.db"
)

# Einfache Dev-Umgebung für CO.RA.PAN
# Startet den Flask-Server mit SQLite-Auth-DB im Repo-Root.

$env:FLASK_SECRET_KEY  = "dev-secret-change-me"
$env:JWT_SECRET        = "dev-jwt-secret-change-me"
$env:AUTH_DATABASE_URL = "sqlite:///$DbPath"
$env:FLASK_ENV         = "development"

Write-Host "Starting dev server with AUTH_DATABASE_URL=$($env:AUTH_DATABASE_URL)..."
python -m src.app.main
