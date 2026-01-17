<#
.SYNOPSIS
    Start BlackLab Server 5.x in Docker container.

.DESCRIPTION
    This script starts BlackLab Server 5.0.0-SNAPSHOT (Lucene 9.11.1) in a Docker container.
    It exposes the server on http://localhost:8081/blacklab-server/
    
    The container mounts:
    - data/blacklab_index (read-only) for the index
    - config/blacklab for server configuration

.PARAMETER Detach
    Run container in detached mode (background).

.PARAMETER Remove
    Automatically remove container when it exits (default: true).

.EXAMPLE
    .\scripts\start_blacklab_docker_v3.ps1
    
    Start BlackLab Server in foreground (interactive logs).

.EXAMPLE
    .\scripts\start_blacklab_docker_v3.ps1 -Detach
    
    Start BlackLab Server in background.

.NOTES
    Author: GitHub Copilot
    Date: November 13, 2025
    BlackLab Version: 5.0.0-SNAPSHOT (Lucene 9.11.1)
    Docker Image: instituutnederlandsetaal/blacklab:latest
    
    This is the current production version. BlackLab 4.x was skipped due to
    upstream Reflections library issues.
    
    To stop the container:
    docker stop blacklab-server-v3
#>

[CmdletBinding()]
param(
    [switch]$Detach,
    [switch]$Remove = $true,
    [switch]$Restart
)

$ErrorActionPreference = "Stop"

# Configuration
# BlackLab 5.x (Lucene 9.x)
# Using :latest (Docker-based server startup)
$BLACKLAB_IMAGE = "instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7"
$CONTAINER_NAME = "blacklab-server-v3"
$HOST_PORT = 8081
$CONTAINER_PORT = 8080
$INDEX_DIR = "data\blacklab_index"
$CONFIG_DIR = "config\blacklab"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "BlackLab Server Start (5.x)" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Get repository root (two levels up from scripts/blacklab -> repo root)
# $PSScriptRoot is scripts\blacklab, so take the parent twice to reach the repo root
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# Make paths absolute
$indexPath = Join-Path $repoRoot $INDEX_DIR
$configPath = Join-Path $repoRoot $CONFIG_DIR

Write-Host "Konfiguration:" -ForegroundColor White
Write-Host "  Docker-Image:    $BLACKLAB_IMAGE" -ForegroundColor Gray
Write-Host "  Container:       $CONTAINER_NAME" -ForegroundColor Gray
Write-Host "  Index:           $indexPath" -ForegroundColor Gray
Write-Host "  Config:          $configPath" -ForegroundColor Gray
Write-Host "  Port:            $HOST_PORT -> $CONTAINER_PORT" -ForegroundColor Gray
Write-Host "  URL:             http://localhost:$HOST_PORT/blacklab-server/" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# Step 1: Verify Prerequisites
# ============================================================================

Write-Host "[1/4] Pruefe Voraussetzungen..." -ForegroundColor Yellow

# Check Docker
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Host "  FEHLER: Docker ist nicht verfuegbar." -ForegroundColor Red
    exit 1
}

try {
    docker version --format "{{.Server.Version}}" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FEHLER: Docker-Daemon ist nicht erreichbar." -ForegroundColor Red
        exit 1
    }
    Write-Host "  OK Docker ist verfuegbar" -ForegroundColor Green
} catch {
    Write-Host "  FEHLER: Docker-Daemon ist nicht erreichbar: $_" -ForegroundColor Red
    exit 1
}

# Check if index exists
if (-not (Test-Path $indexPath)) {
    Write-Host "  FEHLER: Index-Verzeichnis nicht gefunden: $indexPath" -ForegroundColor Red
    Write-Host "    Bitte baue zuerst den Index:" -ForegroundColor Yellow
    Write-Host "    .\scripts\build_blacklab_index_v3.ps1" -ForegroundColor Gray
    exit 1
}

$indexFiles = Get-ChildItem -Path $indexPath -File -Recurse -ErrorAction SilentlyContinue
if ($indexFiles.Count -eq 0) {
    Write-Host "  FEHLER: Index-Verzeichnis ist leer: $indexPath" -ForegroundColor Red
    Write-Host "    Bitte baue zuerst den Index:" -ForegroundColor Yellow
    Write-Host "    .\scripts\build_blacklab_index_v3.ps1" -ForegroundColor Gray
    exit 1
}

Write-Host "  OK Index gefunden: $($indexFiles.Count) Dateien" -ForegroundColor Green

# Check config
if (-not (Test-Path $configPath)) {
    Write-Host "  WARNUNG: Config-Verzeichnis nicht gefunden: $configPath" -ForegroundColor Yellow
    Write-Host "    Server wird mit Default-Config starten." -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# Step 2: Stop Existing Container
# ============================================================================

Write-Host "[2/4] Pruefe vorhandene Container..." -ForegroundColor Yellow

$existingContainer = docker ps -a --filter "name=$CONTAINER_NAME" --format "{{.Names}}" 2>$null

if ($existingContainer -eq $CONTAINER_NAME) {
    Write-Host "  Container '$CONTAINER_NAME' existiert bereits, stoppe..." -ForegroundColor Gray
    docker stop $CONTAINER_NAME 2>&1 | Out-Null
    docker rm $CONTAINER_NAME 2>&1 | Out-Null
    Write-Host "  OK Alter Container entfernt" -ForegroundColor Green
} else {
    Write-Host "  OK Keine vorhandenen Container" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Step 3: Pull Image (if needed)
# ============================================================================

Write-Host "[3/4] Pruefe Docker-Image..." -ForegroundColor Yellow

$imageExists = docker images --format "{{.Repository}}:{{.Tag}}" | Select-String -Pattern "^$BLACKLAB_IMAGE$" -Quiet

if (-not $imageExists) {
    Write-Host "  Image nicht vorhanden, starte Download..." -ForegroundColor Gray
    docker pull $BLACKLAB_IMAGE
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FEHLER: Image konnte nicht heruntergeladen werden." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  OK Image heruntergeladen" -ForegroundColor Green
} else {
    Write-Host "  OK Image ist vorhanden" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Step 4: Start Container
# ============================================================================

Write-Host "[4/4] Starte BlackLab Server..." -ForegroundColor Yellow

# Convert Windows paths to Docker volume format
# Replace backslashes and transform drive letter (C:) into /c prefix for Docker
$indexMount = $indexPath.Replace('\', '/')
$configMount = $configPath.Replace('\', '/')
if ($indexMount -match '^[A-Za-z]:') { $indexMount = '/' + ($indexMount.Substring(0,1).ToLower()) + $indexMount.Substring(2) }
if ($configMount -match '^[A-Za-z]:') { $configMount = '/' + ($configMount.Substring(0,1).ToLower()) + $configMount.Substring(2) }

# Build docker run arguments
# Note: BlackLab 5.x expects indexLocations to contain subdirectories, each being an index
# So we mount the index as /data/index/corapan (not directly as /data/index)
$dockerArgs = @(
    "run"
    "--name", $CONTAINER_NAME
    "-p", "${HOST_PORT}:${CONTAINER_PORT}"
    "-v", "${indexMount}:/data/index/corapan:ro"
)

# Add config mount if directory exists
if (Test-Path $configPath) {
    $dockerArgs += "-v"
    $dockerArgs += "${configMount}:/etc/blacklab:ro"
}

# Add --rm flag if Remove is enabled and not running detached
# When running detached, avoid --rm by default so the container persists and logs can be inspected
if ($Remove -and -not $Detach -and -not $Restart) {
    $dockerArgs += "--rm"
}

# Add restart policy if requested
if ($Restart) {
    # If Restart is requested, do not use --rm due to incompatibility
    if ($Remove) {
        Write-Host "  WARNUNG: --restart wurde angegeben, --rm wird ignoriert." -ForegroundColor Yellow
    }
    $dockerArgs += "--restart=unless-stopped"
}

# Add -d flag if Detach is enabled
if ($Detach) {
    $dockerArgs += "-d"
}

# Add image name
$dockerArgs += $BLACKLAB_IMAGE

Write-Host "  Docker-Befehl:" -ForegroundColor Gray
Write-Host "  docker $($dockerArgs -join ' ')" -ForegroundColor DarkGray
Write-Host ""

try {
    & docker $dockerArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "  FEHLER: Container konnte nicht gestartet werden (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "  FEHLER beim Container-Start: $_" -ForegroundColor Red
    exit 1
}

# After starting, check if the container exited immediately (likely due to a crash)
$containerStatus = docker ps -a --filter "name=$CONTAINER_NAME" --format "{{.Status}}" 2>$null
if ($containerStatus -and $containerStatus -match "Exited") {
    Write-Host "  FEHLER: Container ist unmittelbar nach dem Start beendet (Exited)." -ForegroundColor Red
    Write-Host "  Zeige letzte Logs (100 Zeilen):" -ForegroundColor Gray
    docker logs --tail 100 $CONTAINER_NAME
    exit 1
}

if ($Detach) {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "BlackLab Server gestartet (Hintergrund)" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Server-URL:" -ForegroundColor White
    Write-Host "  http://localhost:$HOST_PORT/blacklab-server/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Container-Status:" -ForegroundColor White
    Write-Host "  docker ps --filter name=$CONTAINER_NAME" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Logs anzeigen:" -ForegroundColor White
    Write-Host "  docker logs -f $CONTAINER_NAME" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Container stoppen:" -ForegroundColor White
    Write-Host "  docker stop $CONTAINER_NAME" -ForegroundColor Gray
    Write-Host ""
    # Health check: wait for BlackLab HTTP endpoint to respond before returning
    Write-Host "Warte auf BlackLab-Server (HTTP) ..." -ForegroundColor Yellow
    $startTime = Get-Date
    $timeoutSeconds = 90
    $ready = $false

    while ( ((Get-Date) - $startTime).TotalSeconds -lt $timeoutSeconds -and -not $ready ) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$HOST_PORT/blacklab-server/" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 404) {
                $ready = $true
                break
            }
        } catch {
            # ignore and retry
        }
        Start-Sleep -Seconds 2
    }

    if ($ready) {
        Write-Host "BlackLab ist erreichbar auf http://localhost:$HOST_PORT/blacklab-server/" -ForegroundColor Green
    } else {
        Write-Host "WARNUNG: BlackLab antwortete nicht innerhalb von $timeoutSeconds Sekunden." -ForegroundColor Yellow
        Write-Host "Pruefen Sie Container-Logs: docker logs --tail 100 $CONTAINER_NAME" -ForegroundColor Gray
        try {
            docker logs --tail 50 $CONTAINER_NAME
        } catch {
            Write-Host "Fehler beim Lesen der Container-Logs: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host ""
    Write-Host "Server gestoppt." -ForegroundColor Yellow
    Write-Host ""
}

exit 0
