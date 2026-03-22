<#
.SYNOPSIS
    Start BlackLab Server 5.x in Docker container.

.DESCRIPTION
    This script starts BlackLab Server 5.0.0-SNAPSHOT (Lucene 9.11.1) in a Docker container.
    It exposes the server on http://localhost:8081/blacklab-server/
    
    The container mounts:
    - data/blacklab/index (read-only) for the index
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

function Convert-ToDockerMountPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    $mountPath = $Path.Replace('\\', '/')
    if ($mountPath -match '^[A-Za-z]:') {
        $mountPath = '/' + ($mountPath.Substring(0,1).ToLower()) + $mountPath.Substring(2)
    }

    return $mountPath
}

function Get-BlackLabSmokePattern {
    param([Parameter(Mandatory = $true)][string]$WorkspaceRoot)

    $tsvDir = Join-Path $WorkspaceRoot "data\blacklab\export\tsv"
    if (Test-Path $tsvDir) {
        $candidateFiles = @(Get-ChildItem -Path $tsvDir -Filter "*.tsv" -File | Where-Object { $_.Name -notlike '*_min.tsv' } | Sort-Object Name)
        foreach ($candidateFile in $candidateFiles) {
            $candidateLines = @(Get-Content -Path $candidateFile.FullName -TotalCount 25 | Select-Object -Skip 1)
            foreach ($line in $candidateLines) {
                if ([string]::IsNullOrWhiteSpace($line)) {
                    continue
                }

                $columns = $line -split "`t"
                if ($columns.Count -eq 0) {
                    continue
                }

                $token = $columns[0].Trim()
                if ([string]::IsNullOrWhiteSpace($token)) {
                    continue
                }

                $escapedToken = $token.Replace('\\', '\\\\').Replace('"', '\\"')
                return '[word="' + $escapedToken + '"]'
            }
        }
    }

    return '[word="casa"]'
}

function Test-BlackLabHttpReadiness {
    param(
        [Parameter(Mandatory = $true)][string]$BaseUrl,
        [Parameter(Mandatory = $true)][string]$SmokePattern,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $rootReady = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $BaseUrl -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 404) {
                $rootReady = $true
                break
            }
        } catch {
        }
        Start-Sleep -Seconds 2
    }

    if (-not $rootReady) {
        throw "BlackLab root endpoint did not become ready within $TimeoutSeconds seconds"
    }

    $queryUrl = "${BaseUrl}corpora/corapan/hits?patt=$([System.Uri]::EscapeDataString($SmokePattern))&number=1"
    $queryResponse = Invoke-WebRequest -Uri $queryUrl -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    if ($queryResponse.StatusCode -ne 200) {
        throw "BlackLab smoke query returned HTTP $($queryResponse.StatusCode)"
    }
}

# Configuration
# BlackLab 5.x (Lucene 9.x)
# Using :latest (Docker-based server startup)
$BLACKLAB_IMAGE = "instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7"
$CONTAINER_NAME = "blacklab-server-v3"
$HOST_PORT = 8081
$CONTAINER_PORT = 8080
$INDEX_DIR = "data\blacklab\index"
$CONFIG_DIR = "config\blacklab"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "BlackLab Server Start (5.x)" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Resolve roots
# $PSScriptRoot is webapp\scripts\blacklab
$webappRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$workspaceRoot = Split-Path -Parent $webappRoot
$dataRoot = Join-Path $workspaceRoot "data"
$configRoot = Join-Path $workspaceRoot "config"
$legacyBlackLabExport = Join-Path $workspaceRoot "data\blacklab_export"
$legacyBlackLabIndex = Join-Path $workspaceRoot "data\blacklab_index"
$repoLocalDataRoot = Join-Path $webappRoot "data"
$stagedIndexPath = Join-Path $workspaceRoot "data\blacklab\quarantine\index.build"

# Make paths absolute
$indexPath = Join-Path $dataRoot "blacklab\index"
$configPath = Join-Path $configRoot "blacklab"

Write-Host "Konfiguration:" -ForegroundColor White
Write-Host "  Docker-Image:    $BLACKLAB_IMAGE" -ForegroundColor Gray
Write-Host "  Container:       $CONTAINER_NAME" -ForegroundColor Gray
Write-Host "  Workspace Root:  $workspaceRoot" -ForegroundColor Cyan
Write-Host "  Webapp Root:     $webappRoot" -ForegroundColor Cyan
Write-Host "  Data Root:       $dataRoot" -ForegroundColor Cyan
Write-Host "  Config Root:     $configRoot" -ForegroundColor Cyan
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

if (Test-Path $repoLocalDataRoot) {
    Write-Host "  FEHLER: Repo-local webapp\\data exists." -ForegroundColor Red
    Write-Host "    Dev BlackLab must mount the sibling workspace root data\\blacklab tree, not webapp\\data." -ForegroundColor Yellow
    exit 1
}

if ((Test-Path $legacyBlackLabExport) -or (Test-Path $legacyBlackLabIndex)) {
    Write-Host "  FEHLER: Legacy BlackLab dev layout detected under data\\blacklab_export or data\\blacklab_index." -ForegroundColor Red
    Write-Host "    Migrate first: .\\scripts\\blacklab\\migrate_legacy_blacklab_dev_layout.ps1 -Apply" -ForegroundColor Yellow
    exit 1
}

# Check if index exists
if (-not (Test-Path $indexPath)) {
    Write-Host "  FEHLER: Index-Verzeichnis nicht gefunden: $indexPath" -ForegroundColor Red
    Write-Host "    Bitte baue zuerst den Index:" -ForegroundColor Yellow
    Write-Host "    .\webapp\scripts\blacklab\build_blacklab_index.ps1" -ForegroundColor Gray
    exit 1
}

$indexFiles = Get-ChildItem -Path $indexPath -File -Recurse -ErrorAction SilentlyContinue
if ($indexFiles.Count -eq 0) {
    Write-Host "  FEHLER: Index-Verzeichnis ist leer: $indexPath" -ForegroundColor Red
    Write-Host "    Bitte baue zuerst den Index:" -ForegroundColor Yellow
    Write-Host "    .\webapp\scripts\blacklab\build_blacklab_index.ps1" -ForegroundColor Gray
    exit 1
}

Write-Host "  OK Index gefunden: $($indexFiles.Count) Dateien" -ForegroundColor Green

if (Test-Path $stagedIndexPath) {
    $stagedIndexFiles = @(Get-ChildItem -Path $stagedIndexPath -File -Recurse -ErrorAction SilentlyContinue)
    if ($stagedIndexFiles.Count -gt 0) {
        Write-Host "  WARNUNG: Staged index exists under data\\blacklab\\quarantine\\index.build." -ForegroundColor Yellow
        Write-Host "    Ensure a previous rebuild completed before serving the active index." -ForegroundColor Yellow
    }
}

# Check config
if (-not (Test-Path $configPath)) {
    Write-Host "  FEHLER: Config-Verzeichnis nicht gefunden: $configPath" -ForegroundColor Red
    Write-Host "    Dev BlackLab must use the canonical sibling config\\blacklab tree." -ForegroundColor Yellow
    exit 1
}

$requiredConfigFiles = @(
    (Join-Path $configPath "blacklab-server.yaml"),
    (Join-Path $configPath "corapan-tsv.blf.yaml")
)
foreach ($requiredConfigFile in $requiredConfigFiles) {
    if (-not (Test-Path $requiredConfigFile)) {
        Write-Host "  FEHLER: Required BlackLab config missing: $requiredConfigFile" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# ============================================================================
# Step 2: Stop Existing Container
# ============================================================================

Write-Host "[2/4] Pruefe vorhandene Container..." -ForegroundColor Yellow

$existingContainer = docker ps -a --filter "name=$CONTAINER_NAME" --format "{{.Names}}" 2>$null

if ($existingContainer -eq $CONTAINER_NAME) {
    if (-not $Restart) {
        Write-Host "  FEHLER: Container '$CONTAINER_NAME' existiert bereits." -ForegroundColor Red
        Write-Host "    Stoppe ihn manuell oder starte dieses Skript explizit mit -Restart." -ForegroundColor Yellow
        exit 1
    }

    Write-Host "  Container '$CONTAINER_NAME' existiert bereits, ersetze ihn wegen -Restart..." -ForegroundColor Gray
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
$indexMount = Convert-ToDockerMountPath -Path $indexPath
$configMount = Convert-ToDockerMountPath -Path $configPath

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
    Write-Host "Warte auf BlackLab-Server und pruefe Lesbarkeit des aktiven Index ..." -ForegroundColor Yellow
    $smokePattern = Get-BlackLabSmokePattern -WorkspaceRoot $workspaceRoot

    try {
        Test-BlackLabHttpReadiness -BaseUrl "http://localhost:$HOST_PORT/blacklab-server/" -SmokePattern $smokePattern -TimeoutSeconds 90
        Write-Host "BlackLab ist erreichbar und der aktive Index beantwortet Suchanfragen." -ForegroundColor Green
    } catch {
        Write-Host "FEHLER: BlackLab startete, aber der aktive Index ist nicht lesbar." -ForegroundColor Red
        Write-Host "  Smoke query: $smokePattern" -ForegroundColor Yellow
        Write-Host "  Logs: docker logs --tail 100 $CONTAINER_NAME" -ForegroundColor Yellow
        try {
            docker logs --tail 100 $CONTAINER_NAME
        } catch {
        }
        try {
            docker stop $CONTAINER_NAME *>$null
        } catch {
        }
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "Server gestoppt." -ForegroundColor Yellow
    Write-Host ""
}

exit 0
