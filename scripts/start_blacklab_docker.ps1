<#
.SYNOPSIS
    Start BlackLab Server in Docker for local development.

.DESCRIPTION
    This script starts the BlackLab Server Docker container for the CO.RA.PAN project.
    It checks if the container already exists and handles three cases:
    1. Container exists and is running -> Do nothing, report status
    2. Container exists but is stopped -> Start the existing container
    3. Container doesn't exist -> Create and run a new container

    The container configuration:
    - Name: corapan-blacklab-dev
    - Image: corpuslab/blacklab-server:3.5.0
    - Port mapping: 8081 (host) -> 8080 (container)
    - Volumes:
        - config/blacklab/corapan.blf.yaml (read-only)
        - data/blacklab_index/ (read-write)
    - BLS_BASE_URL: http://localhost:8081/blacklab-server

.EXAMPLE
    .\scripts\start_blacklab_docker.ps1

.NOTES
    Author: GitHub Copilot
    Date: November 13, 2025
    Requires: Docker Desktop for Windows
#>

$ErrorActionPreference = "Stop"

$CONTAINER_NAME = "corapan-blacklab-dev"
$IMAGE = "instituutnederlandsetaal/blacklab:latest"
$HOST_PORT = 8081
$CONTAINER_PORT = 8080
$CONFIG_DIR = "config/blacklab"
$INDEX_DIR = "data/blacklab_index"

Write-Host "BlackLab Docker Startup Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    $null = docker version 2>$null
} catch {
    Write-Host "ERROR: Docker is not running or not installed." -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Check if container exists
$containerExists = docker ps -a --filter "name=^/${CONTAINER_NAME}$" --format "{{.Names}}" 2>$null

if ($containerExists -eq $CONTAINER_NAME) {
    # Container exists - check if it's running
    $containerRunning = docker ps --filter "name=^/${CONTAINER_NAME}$" --format "{{.Names}}" 2>$null
    
    if ($containerRunning -eq $CONTAINER_NAME) {
        Write-Host "✓ BlackLab container is already running." -ForegroundColor Green
        Write-Host ""
        Write-Host "Container: $CONTAINER_NAME" -ForegroundColor White
        Write-Host "URL:       http://localhost:${HOST_PORT}/blacklab-server" -ForegroundColor White
        Write-Host ""
        Write-Host "You can now start Flask with:" -ForegroundColor Cyan
        Write-Host "  .venv\Scripts\activate" -ForegroundColor Gray
        Write-Host "  `$env:FLASK_ENV=`"development`"" -ForegroundColor Gray
        Write-Host "  python -m src.app.main" -ForegroundColor Gray
        exit 0
    } else {
        # Container exists but is stopped
        Write-Host "Starting existing BlackLab container..." -ForegroundColor Yellow
        docker start $CONTAINER_NAME
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ BlackLab container started successfully." -ForegroundColor Green
        } else {
            Write-Host "ERROR: Failed to start container." -ForegroundColor Red
            exit 1
        }
    }
} else {
    # Container doesn't exist - create and run it
    Write-Host "Creating new BlackLab container..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Configuration:" -ForegroundColor White
    Write-Host "  Container:    $CONTAINER_NAME" -ForegroundColor Gray
    Write-Host "  Image:        $IMAGE" -ForegroundColor Gray
    Write-Host "  Port mapping: ${HOST_PORT}:${CONTAINER_PORT}" -ForegroundColor Gray
    Write-Host "  Config dir:   $CONFIG_DIR" -ForegroundColor Gray
    Write-Host "  Index:        $INDEX_DIR" -ForegroundColor Gray
    Write-Host ""
    
    # Get absolute paths for volume mounts
    $repoRoot = Split-Path -Parent $PSScriptRoot
    $configPath = Join-Path $repoRoot $CONFIG_DIR
    $indexPath = Join-Path $repoRoot $INDEX_DIR
    
    # Verify files exist
    if (-not (Test-Path $configPath)) {
        Write-Host "ERROR: Config directory not found at $configPath" -ForegroundColor Red
        exit 1
    }
    
    if (-not (Test-Path $indexPath)) {
        Write-Host "WARNING: Index directory not found at $indexPath" -ForegroundColor Yellow
        Write-Host "Creating index directory..." -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $indexPath -Force | Out-Null
    }
    
    # Run Docker container
    docker run -d `
        --name $CONTAINER_NAME `
        -p "${HOST_PORT}:${CONTAINER_PORT}" `
        -v "${configPath}:/etc/blacklab:ro" `
        -v "${indexPath}:/data/index/corapan:ro" `
        $IMAGE
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ BlackLab container created and started successfully." -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to create container." -ForegroundColor Red
        exit 1
    }
}

# Wait a moment for container to fully start
Start-Sleep -Seconds 2

# Verify container is running
$containerRunning = docker ps --filter "name=^/${CONTAINER_NAME}$" --format "{{.Names}}" 2>$null

if ($containerRunning -eq $CONTAINER_NAME) {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "BlackLab is now running!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Container: $CONTAINER_NAME" -ForegroundColor White
    Write-Host "URL:       http://localhost:${HOST_PORT}/blacklab-server" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Start Flask in a separate terminal:" -ForegroundColor White
    Write-Host "     .venv\Scripts\activate" -ForegroundColor Gray
    Write-Host "     `$env:FLASK_ENV=`"development`"" -ForegroundColor Gray
    Write-Host "     python -m src.app.main" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Open browser: http://localhost:8000/search/advanced" -ForegroundColor White
    Write-Host ""
    Write-Host "Useful commands:" -ForegroundColor Cyan
    Write-Host "  Stop:  .\scripts\stop_blacklab_docker.ps1" -ForegroundColor Gray
    Write-Host "  Logs:  docker logs $CONTAINER_NAME --follow" -ForegroundColor Gray
    Write-Host "  Test:  curl http://localhost:${HOST_PORT}/blacklab-server/" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "WARNING: Container started but not showing as running." -ForegroundColor Yellow
    Write-Host "Check logs with: docker logs $CONTAINER_NAME" -ForegroundColor Gray
}
