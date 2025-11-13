# Start BlackLab Server (Docker) for Windows Dev Environment
# 
# Purpose: Start BlackLab Server in Docker container with proper port mapping
#          and volume mounts for the CO.RA.PAN corpus index.
#
# Requirements:
# - Docker Desktop installed and running
# - BlackLab index built at: data/blacklab_index/
# - BlackLab config at: config/blacklab/corapan.blf.yaml
#
# Usage:
#   .\scripts\start_blacklab_windows.ps1
#
# Verify it's running:
#   Invoke-WebRequest -Uri "http://localhost:8081/blacklab-server/" | Select-Object StatusCode
#
# Stop BlackLab:
#   docker stop blacklab-dev
#   docker rm blacklab-dev

# Configuration
$ContainerName = "blacklab-dev"
$HostPort = 8081
$ContainerPort = 8080
$ImageName = "instituutnederlandsetaal/blacklab-server:4.0.0-beta.3"
$WorkDir = Get-Location

Write-Host "Starting BlackLab Server for CO.RA.PAN..." -ForegroundColor Cyan
Write-Host ""

# Check if container already exists
$Existing = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}"
if ($Existing -eq $ContainerName) {
    Write-Host "Container '$ContainerName' already exists." -ForegroundColor Yellow
    $Running = docker ps --filter "name=$ContainerName" --format "{{.Names}}"
    if ($Running -eq $ContainerName) {
        Write-Host "Container is already running on http://localhost:$HostPort/blacklab-server" -ForegroundColor Green
        exit 0
    }
    Write-Host "Starting existing container..." -ForegroundColor Cyan
    docker start $ContainerName
    Start-Sleep -Seconds 3
    Write-Host "BlackLab started: http://localhost:$HostPort/blacklab-server" -ForegroundColor Green
    exit 0
}

# Check if index exists
if (-not (Test-Path "$WorkDir\data\blacklab_index\index.json")) {
    Write-Host "ERROR: BlackLab index not found at data/blacklab_index/" -ForegroundColor Red
    Write-Host "Please build the index first" -ForegroundColor Yellow
    exit 1
}

# Check if config exists
if (-not (Test-Path "$WorkDir\config\blacklab\corapan.blf.yaml")) {
    Write-Host "ERROR: BlackLab config not found at config/blacklab/corapan.blf.yaml" -ForegroundColor Red
    exit 1
}

# Start new container
Write-Host "Starting new Docker container..." -ForegroundColor Cyan
Write-Host "Image: $ImageName" -ForegroundColor Gray
Write-Host "Port mapping: ${HostPort}:${ContainerPort}" -ForegroundColor Gray
Write-Host "Index: $WorkDir\data\blacklab_index" -ForegroundColor Gray
Write-Host ""

docker run -d `
  --name $ContainerName `
  -p "${HostPort}:${ContainerPort}" `
  -v "${WorkDir}\config\blacklab\corapan.blf.yaml:/etc/blacklab/corapan.blf.yaml:ro" `
  -v "${WorkDir}\data\blacklab_index:/data/blacklab_index:ro" `
  -e "BLACKLAB_CONFIG_YAML=/etc/blacklab/corapan.blf.yaml" `
  $ImageName

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to start BlackLab container" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Waiting for BlackLab to initialize (5 seconds)..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Health check
Write-Host "Checking BlackLab health..." -ForegroundColor Cyan
try {
    $Response = Invoke-WebRequest -Uri "http://localhost:$HostPort/blacklab-server/" -Method Get -TimeoutSec 5
    if ($Response.StatusCode -eq 200) {
        Write-Host "SUCCESS: BlackLab is running!" -ForegroundColor Green
        Write-Host ""
        Write-Host "BlackLab Server URL: http://localhost:$HostPort/blacklab-server" -ForegroundColor Cyan
        Write-Host "Corpus endpoint: http://localhost:$HostPort/blacklab-server/corapan/" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "  1. Start Flask app: python -m src.app.main" -ForegroundColor Gray
        Write-Host "  2. Open: http://localhost:8000/search/advanced" -ForegroundColor Gray
        Write-Host "  3. Search for 'casa' or other tokens" -ForegroundColor Gray
        Write-Host ""
        Write-Host "To stop BlackLab:" -ForegroundColor Yellow
        Write-Host "  docker stop $ContainerName" -ForegroundColor Gray
        Write-Host "  docker rm $ContainerName" -ForegroundColor Gray
    } else {
        Write-Host "WARNING: BlackLab responded with unexpected status" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ERROR: BlackLab health check failed" -ForegroundColor Red
    Write-Host "Container may still be initializing. Check logs with:" -ForegroundColor Yellow
    Write-Host "  docker logs $ContainerName" -ForegroundColor Yellow
    exit 1
}
