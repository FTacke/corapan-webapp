# CO.RA.PAN Development Startup Script (Windows)
# Starts Mock BlackLab Server + Flask App in separate windows

Write-Host "🚀 CO.RA.PAN Development Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if already running
$mockRunning = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*mock_bls_server*" }
$flaskRunning = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*src.app.main*" }

if ($mockRunning -or $flaskRunning) {
    Write-Host "⚠️  Warning: Python processes already running" -ForegroundColor Yellow
    $response = Read-Host "Stop existing processes and restart? (y/n)"
    if ($response -eq 'y') {
        Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Stopped existing Python processes" -ForegroundColor Green
        Start-Sleep -Seconds 2
    } else {
        Write-Host "❌ Cancelled. Please stop existing processes manually." -ForegroundColor Red
        exit 1
    }
}

# Step 1: Start Mock BlackLab Server
Write-Host "📡 Starting Mock BlackLab Server (Port 8081)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
`$Host.UI.RawUI.WindowTitle = 'Mock BlackLab Server - Port 8081'
cd '$PWD'
Write-Host '🟢 Mock BlackLab Server Starting...' -ForegroundColor Green
Write-Host 'Port: 8081' -ForegroundColor Cyan
Write-Host 'Mock data: 324 hits with KWIC' -ForegroundColor Cyan
Write-Host ''
python scripts/mock_bls_server.py 8081
"@

Start-Sleep -Seconds 3

# Step 2: Verify Mock Server is running
Write-Host "🔍 Verifying Mock BlackLab Server..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8081/blacklab-server/" -Method Get -TimeoutSec 5
    Write-Host "✅ Mock BlackLab Server is responding" -ForegroundColor Green
    Write-Host "   Version: $($response.blacklabVersion)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Mock BlackLab Server failed to start" -ForegroundColor Red
    Write-Host "   Check the Mock BLS window for errors" -ForegroundColor Yellow
    exit 1
}

# Step 3: Start Flask App
Write-Host ""
Write-Host "🌐 Starting Flask App (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
`$Host.UI.RawUI.WindowTitle = 'Flask App - Port 8000'
cd '$PWD'
.venv\Scripts\activate
`$env:FLASK_ENV='development'
`$env:BLS_BASE_URL='http://localhost:8081/blacklab-server'
Write-Host '🟢 Flask App Starting...' -ForegroundColor Green
Write-Host 'Port: 8000' -ForegroundColor Cyan
Write-Host 'BLS_BASE_URL: http://localhost:8081/blacklab-server' -ForegroundColor Cyan
Write-Host ''
python -m src.app.main
"@

Start-Sleep -Seconds 8

# Step 4: Verify Flask is running
Write-Host "🔍 Verifying Flask App..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
    if ($health.status -eq "healthy") {
        Write-Host "✅ Flask App is healthy" -ForegroundColor Green
        Write-Host "   Status: $($health.status)" -ForegroundColor Gray
        Write-Host "   BlackLab: $($health.checks.blacklab.ok)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  Flask App started but status is: $($health.status)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Flask App failed to start" -ForegroundColor Red
    Write-Host "   Check the Flask window for errors" -ForegroundColor Yellow
    exit 1
}

# Success
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ Development Environment Ready!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Open in browser:" -ForegroundColor Cyan
Write-Host "   Advanced Search: http://localhost:8000/search/advanced" -ForegroundColor White
Write-Host "   Health Check:    http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "📝 Test search:" -ForegroundColor Cyan
Write-Host "   Search for 'casa' - should return 324 mock results" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Note: Using MOCK BlackLab data (not real search results)" -ForegroundColor Yellow
Write-Host "   For real search, see docs/how-to/advanced-search-dev-setup.md" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to exit this window (services will keep running)..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
