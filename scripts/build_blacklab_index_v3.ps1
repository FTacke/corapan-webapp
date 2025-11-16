<#
.SYNOPSIS
    Build BlackLab index using BlackLab 5.x Docker image.

.DESCRIPTION
    This script rebuilds the BlackLab index from TSV files using BlackLab 5.0.0-SNAPSHOT (Lucene 9.11.1).
    It runs the index creation inside a Docker container to avoid local JAR/Java issues.

    Prerequisites:
    - Docker must be installed and running
    - TSV source files must exist in data/blacklab_export/tsv/
    - BlackLab config must exist in config/blacklab/corapan-tsv.blf.yaml
    - docmeta.jsonl must exist in data/blacklab_export/

    The script will:
    1. Verify all prerequisites (Docker, TSV files)
    2. Backup existing index (if present)
    3. Create empty target directory
    4. Run BlackLab IndexTool in Docker container to build the index
    5. Verify the new index was created successfully

.PARAMETER SkipBackup
    Skip backing up the existing index (use with caution).

.PARAMETER Force
    Skip confirmation prompts.

.EXAMPLE
    .\scripts\build_blacklab_index_v3.ps1
    
    Standard index rebuild with safety prompts.

.EXAMPLE
    .\scripts\build_blacklab_index_v3.ps1 -Force
    
    Rebuild without confirmation prompts.

.NOTES
    Author: GitHub Copilot
    Date: November 13, 2025
    BlackLab Version: 5.0.0-SNAPSHOT (Lucene 9.11.1)
    Docker Image: instituutnederlandsetaal/blacklab:latest
    
    This is the current production version. BlackLab 4.x was skipped due to
    upstream Reflections library issues.
#>

#[CmdletBinding()]
param(
    [switch]$SkipBackup,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Configuration (Compatibility wrapper, forwards to canonical script)
# BlackLab 5.x (Lucene 9.x) as of 2025-11-13
$BLACKLAB_IMAGE = "instituutnederlandsetaal/blacklab:latest"
$EXPORT_DIR = "data\blacklab_export"
$TSV_DIR = Join-Path $EXPORT_DIR "tsv"
$DOCMETA_FILE = Join-Path $EXPORT_DIR "docmeta.jsonl"
$INDEX_TARGET_DIR = "data\blacklab_index"
$BLF_CONFIG = "config\blacklab\corapan-tsv.blf.yaml"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "BlackLab Index Build (5.x / Lucene 9)" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Get repository root (parent of scripts/)
$repoRoot = Split-Path -Parent $PSScriptRoot

# Make all paths absolute
$exportPath = Join-Path $repoRoot $EXPORT_DIR
$tsvPath = Join-Path $repoRoot $TSV_DIR
$docmetaPath = Join-Path $repoRoot $DOCMETA_FILE
$indexTargetPath = Join-Path $repoRoot $INDEX_TARGET_DIR
$blfConfigPath = Join-Path $repoRoot $BLF_CONFIG

Write-Host "Konfiguration:" -ForegroundColor White
Write-Host "  NOTE: This script is kept for compatibility. Use scripts/build_blacklab_index.ps1 as canonical" -ForegroundColor Yellow
Write-Host "  Repository:      $repoRoot" -ForegroundColor Gray
Write-Host "  Docker-Image:    $BLACKLAB_IMAGE" -ForegroundColor Gray
Write-Host "  Export-Quelle:   $exportPath" -ForegroundColor Gray
Write-Host "  TSV-Quelle:      $tsvPath" -ForegroundColor Gray
Write-Host "  Docmeta:         $docmetaPath" -ForegroundColor Gray
Write-Host "  Ziel-Index:      $indexTargetPath" -ForegroundColor Gray
Write-Host "  BLF-Config:      $blfConfigPath" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# Step 1: Verify Prerequisites
# ============================================================================

Write-Host "[1/5] Pruefe Voraussetzungen..." -ForegroundColor Yellow

# Check Docker
Write-Host "  Pruefe Docker..." -ForegroundColor Gray
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Host "  FEHLER: Docker ist nicht verfuegbar oder nicht im PATH." -ForegroundColor Red
    Write-Host "    Bitte installiere Docker Desktop und starte es." -ForegroundColor Yellow
    exit 1
}

try {
    $dockerVersion = docker version --format "{{.Server.Version}}" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FEHLER: Docker-Daemon ist nicht erreichbar." -ForegroundColor Red
        Write-Host "    Bitte starte Docker Desktop." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  OK Docker ist verfuegbar: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  FEHLER: Docker-Daemon ist nicht erreichbar: $_" -ForegroundColor Red
    exit 1
}

# Check TSV source directory
if (-not (Test-Path $tsvPath)) {
    Write-Host "  FEHLER: TSV-Quellverzeichnis nicht gefunden: $tsvPath" -ForegroundColor Red
    Write-Host "    Bitte fuehre zuerst den JSON->TSV Export aus:" -ForegroundColor Yellow
    Write-Host "    .\LOKAL\01 - Add New Transcriptions\03b build blacklab_index\build_index.ps1" -ForegroundColor Gray
    exit 1
}

$tsvFiles = Get-ChildItem -Path $tsvPath -Filter "*.tsv" -File
if ($tsvFiles.Count -eq 0) {
    Write-Host "  FEHLER: Keine TSV-Dateien in $tsvPath gefunden." -ForegroundColor Red
    exit 1
}

Write-Host "  OK TSV-Quelle: $($tsvFiles.Count) Dateien gefunden" -ForegroundColor Green

# Check docmeta.jsonl
if (-not (Test-Path $docmetaPath)) {
    Write-Host "  FEHLER: docmeta.jsonl nicht gefunden: $docmetaPath" -ForegroundColor Red
    exit 1
<CmdletBinding/>

$docmetaLines = (Get-Content $docmetaPath | Measure-Object -Line).Lines
Write-Host "  OK Docmeta: $docmetaLines Dokumente" -ForegroundColor Green

# Check BLF config
if (-not (Test-Path $blfConfigPath)) {
    Write-Host "  FEHLER: BlackLab-Konfiguration nicht gefunden: $blfConfigPath" -ForegroundColor Red
    exit 1
}

Write-Host "  OK BlackLab-Config gefunden" -ForegroundColor Green

Write-Host ""

# ============================================================================
# Step 2: Pull Docker Image
# ============================================================================

Write-Host "[2/5] Pruefe Docker-Image..." -ForegroundColor Yellow

$imageExists = docker images --format "{{.Repository}}:{{.Tag}}" | Select-String -Pattern "^$BLACKLAB_IMAGE$" -Quiet

if (-not $imageExists) {
    Write-Host "  Image nicht lokal vorhanden, starte Download..." -ForegroundColor Gray
    Write-Host "  Dies kann einige Minuten dauern..." -ForegroundColor Gray
    
    docker pull $BLACKLAB_IMAGE
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FEHLER: Docker-Image konnte nicht heruntergeladen werden." -ForegroundColor Red
        exit 1
    }
    
Write-Host "  NOTE: This script forwards to scripts/build_blacklab_index.ps1 (canonical)." -ForegroundColor Yellow
Write-Host "          Use the canonical script directly: .\scripts\build_blacklab_index.ps1" -ForegroundColor Yellow
Write-Host "          Forwarding call..." -ForegroundColor Gray

# Forward args to canonical script
$forwardArgs = @()
if ($SkipBackup) { $forwardArgs += "-SkipBackup" }
if ($Force) { $forwardArgs += "-Force" }
& "$PSScriptRoot\build_blacklab_index.ps1" @forwardArgs
exit $LASTEXITCODE
    Write-Host "  OK Image heruntergeladen" -ForegroundColor Green
} else {
    Write-Host "  OK Image ist bereits vorhanden" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Step 3: Backup Existing Index
# ============================================================================

Write-Host "[3/5] Sichere vorhandenen Index..." -ForegroundColor Yellow

if (Test-Path $indexTargetPath) {
    $indexFiles = Get-ChildItem -Path $indexTargetPath -File -Recurse -ErrorAction SilentlyContinue
    if ($indexFiles.Count -gt 0) {
        if (-not $SkipBackup) {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $backupDir = Join-Path $repoRoot "data\blacklab_index.old_$timestamp"
            
            Write-Host "  Verschiebe vorhandenen Index nach: $backupDir" -ForegroundColor Gray
            
            if (-not $Force) {
                $confirmation = Read-Host "  Fortfahren? (j/n)"
                if ($confirmation -ne 'j' -and $confirmation -ne 'J') {
                    Write-Host "  Abgebrochen." -ForegroundColor Yellow
                    exit 0
                }
            }
            
            Move-Item -Path $indexTargetPath -Destination $backupDir -Force
            Write-Host "  OK Backup erstellt: $backupDir" -ForegroundColor Green
        } else {
            Write-Host "  INFO: Backup uebersprungen (--SkipBackup)" -ForegroundColor Yellow
            
            if (-not $Force) {
                Write-Host "  WARNUNG: Vorhandener Index wird geloescht!" -ForegroundColor Red
                $confirmation = Read-Host "  Wirklich fortfahren? (j/n)"
                if ($confirmation -ne 'j' -and $confirmation -ne 'J') {
                    Write-Host "  Abgebrochen." -ForegroundColor Yellow
                    exit 0
                }
            }
            
            Remove-Item -Path $indexTargetPath -Recurse -Force
            Write-Host "  Index geloescht" -ForegroundColor Gray
        }
    } else {
        Write-Host "  Kein vorhandener Index gefunden (Verzeichnis ist leer)" -ForegroundColor Gray
    }
} else {
    Write-Host "  Kein vorhandener Index gefunden" -ForegroundColor Gray
}

# Create empty index directory
New-Item -ItemType Directory -Path $indexTargetPath -Force | Out-Null
Write-Host "  OK Zielverzeichnis vorbereitet: $indexTargetPath" -ForegroundColor Green

Write-Host ""

# ============================================================================
# Step 4: Run BlackLab Index Build in Docker
# ============================================================================

Write-Host "[4/5] Starte Index-Build..." -ForegroundColor Yellow
Write-Host "  Dies kann 5-10 Minuten dauern..." -ForegroundColor Gray
Write-Host ""

# Build Docker volume mount paths (convert Windows paths to /c/... format for Docker)
$exportMount = $exportPath.Replace('\', '/').Replace('C:', '/c')
$indexMount = $indexTargetPath.Replace('\', '/').Replace('C:', '/c')
$configMount = (Join-Path $repoRoot "config\blacklab").Replace('\', '/').Replace('C:', '/c')

# Build the docker command
# BlackLab 5.x uses IndexTool via java -cp
$dockerArgs = @(
    "run", "--rm"
    "-v", "${exportMount}:/data/export:ro"
    "-v", "${indexMount}:/data/index:rw"
    "-v", "${configMount}:/config:ro"
    $BLACKLAB_IMAGE
    "java", "-cp", "/usr/local/lib/blacklab-tools/*"
    "nl.inl.blacklab.tools.IndexTool", "create"
    "/data/index"
    "/data/export/tsv"
    "/config/corapan-tsv.blf.yaml"
    "--linked-file-dir", "/data/export"
    "--threads", "1"
)

Write-Host "  Docker-Befehl:" -ForegroundColor Gray
Write-Host "  docker $($dockerArgs -join ' ')" -ForegroundColor DarkGray
Write-Host ""

try {
    & docker $dockerArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "  FEHLER: Index-Build fehlgeschlagen (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "  FEHLER beim Index-Build: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  OK Index-Build abgeschlossen" -ForegroundColor Green

Write-Host ""

# ============================================================================
# Step 5: Verify Index
# ============================================================================

Write-Host "[5/5] Verifiziere Index..." -ForegroundColor Yellow

$indexFiles = Get-ChildItem -Path $indexTargetPath -File -Recurse -ErrorAction SilentlyContinue

if ($indexFiles.Count -eq 0) {
    Write-Host "  FEHLER: Index-Verzeichnis ist leer!" -ForegroundColor Red
    exit 1
}

# Calculate index size
$indexSizeMB = ($indexFiles | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "  OK Index erstellt: $($indexFiles.Count) Dateien, $([math]::Round($indexSizeMB, 2)) MB" -ForegroundColor Green

# Check for essential Lucene files
$segmentsFile = Get-ChildItem -Path $indexTargetPath -Filter "segments*" -File -Recurse | Select-Object -First 1
if (-not $segmentsFile) {
    Write-Host "  WARNUNG: Keine Lucene-Segments-Datei gefunden - Index koennte beschaedigt sein" -ForegroundColor Yellow
} else {
    Write-Host "  OK Lucene-Segmente gefunden: $($segmentsFile.Name)" -ForegroundColor Green
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Index-Build erfolgreich abgeschlossen!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Naechste Schritte:" -ForegroundColor White
Write-Host "  1. Starte BlackLab Server:" -ForegroundColor Gray
Write-Host "     .\scripts\start_blacklab_docker_v3.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Teste Advanced Search:" -ForegroundColor Gray
Write-Host "     http://localhost:5000/search/advanced" -ForegroundColor Gray
Write-Host ""

exit 0
