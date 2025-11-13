<#
.SYNOPSIS
    Stop BlackLab Server Docker container.

.DESCRIPTION
    This script stops the BlackLab Server Docker container for the CO.RA.PAN project.
    By default, it only stops the container without removing it, so it can be quickly
    restarted with start_blacklab_docker.ps1.
    
    Use the -Remove switch to also remove the container after stopping.

.PARAMETER Remove
    If specified, removes the container after stopping it.

.EXAMPLE
    .\scripts\stop_blacklab_docker.ps1
    Stops the container but keeps it for later restart.

.EXAMPLE
    .\scripts\stop_blacklab_docker.ps1 -Remove
    Stops and removes the container completely.

.NOTES
    Author: GitHub Copilot
    Date: November 13, 2025
    Requires: Docker Desktop for Windows
#>

[CmdletBinding()]
param(
    [switch]$Remove
)

$ErrorActionPreference = "Stop"

$CONTAINER_NAME = "corapan-blacklab-dev"

Write-Host "BlackLab Docker Stop Script" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    $null = docker version 2>$null
} catch {
    Write-Host "ERROR: Docker is not running or not installed." -ForegroundColor Red
    exit 1
}

# Check if container exists
$containerExists = docker ps -a --filter "name=^/${CONTAINER_NAME}$" --format "{{.Names}}" 2>$null

if ($containerExists -ne $CONTAINER_NAME) {
    Write-Host "Container '$CONTAINER_NAME' does not exist." -ForegroundColor Yellow
    Write-Host "Nothing to stop." -ForegroundColor Gray
    exit 0
}

# Check if container is running
$containerRunning = docker ps --filter "name=^/${CONTAINER_NAME}$" --format "{{.Names}}" 2>$null

if ($containerRunning -eq $CONTAINER_NAME) {
    Write-Host "Stopping BlackLab container..." -ForegroundColor Yellow
    docker stop $CONTAINER_NAME
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ BlackLab container stopped successfully." -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to stop container." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Container '$CONTAINER_NAME' is already stopped." -ForegroundColor Gray
}

# Remove container if requested
if ($Remove) {
    Write-Host ""
    Write-Host "Removing container..." -ForegroundColor Yellow
    docker rm $CONTAINER_NAME
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ BlackLab container removed successfully." -ForegroundColor Green
        Write-Host ""
        Write-Host "To recreate the container, run:" -ForegroundColor Cyan
        Write-Host "  .\scripts\start_blacklab_docker.ps1" -ForegroundColor Gray
    } else {
        Write-Host "ERROR: Failed to remove container." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "Container stopped but not removed." -ForegroundColor Gray
    Write-Host "To restart: .\scripts\start_blacklab_docker.ps1" -ForegroundColor Cyan
    Write-Host "To remove:  .\scripts\stop_blacklab_docker.ps1 -Remove" -ForegroundColor Cyan
}

Write-Host ""
