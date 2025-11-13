<#
.SYNOPSIS
    Build BlackLab Lucene 9 index from TSV source files.

.DESCRIPTION
    This script rebuilds the BlackLab index from TSV files in data/blacklab_index.backup/tsv/.
    It creates a fresh Lucene 9 compatible index by running BlackLab's indexing tool inside
    the Docker container.

    Prerequisites:
    - Docker Desktop must be running
    - TSV source files must exist in data/blacklab_index.backup/tsv/
    - BlackLab config must exist in config/blacklab/corapan-tsv.blf.yaml
    - docmeta.jsonl must exist in data/blacklab_index.backup/

    The script will:
    1. Verify all prerequisites
    2. Backup existing index (if present)
    3. Create empty target directory
    4. Run BlackLab IndexTool inside Docker container
    5. Verify the new index was created successfully

.PARAMETER SkipBackup
    Skip backing up the existing index (use with caution).

.PARAMETER Force
    Skip confirmation prompts.

.EXAMPLE
    .\scripts\build_blacklab_index.ps1
    
    Standard index rebuild with safety prompts.

.EXAMPLE
    .\scripts\build_blacklab_index.ps1 -Force
    
    Rebuild without confirmation prompts.

.NOTES
    Author: GitHub Copilot
    Date: November 13, 2025
    Requires: Docker Desktop, BlackLab container image
#>

[CmdletBinding()]
param(
    [switch]$SkipBackup,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Configuration
$CONTAINER_NAME = "corapan-blacklab-dev"
$IMAGE = "instituutnederlandsetaal/blacklab:latest"
$TSV_SOURCE_DIR = "data\blacklab_index.backup\tsv"
$DOCMETA_FILE = "data\blacklab_index.backup\docmeta.jsonl"
$INDEX_TARGET_DIR = "data\blacklab_index"
$BLF_CONFIG = "config\blacklab\corapan-tsv.blf.yaml"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "BlackLab Index Build (Lucene 9)" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Get repository root (parent of scripts/)
$repoRoot = Split-Path -Parent $PSScriptRoot

# Make all paths absolute
$tsvSourcePath = Join-Path $repoRoot $TSV_SOURCE_DIR
$docmetaPath = Join-Path $repoRoot $DOCMETA_FILE
$indexTargetPath = Join-Path $repoRoot $INDEX_TARGET_DIR
$blfConfigPath = Join-Path $repoRoot $BLF_CONFIG

Write-Host "Konfiguration:" -ForegroundColor White
Write-Host "  Repository:   $repoRoot" -ForegroundColor Gray
Write-Host "  TSV-Quelle:   $tsvSourcePath" -ForegroundColor Gray
Write-Host "  Docmeta:      $docmetaPath" -ForegroundColor Gray
Write-Host "  Ziel-Index:   $indexTargetPath" -ForegroundColor Gray
Write-Host "  BLF-Config:   $blfConfigPath" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# Step 1: Verify Prerequisites
# ============================================================================

Write-Host "[1/5] Überprüfe Voraussetzungen..." -ForegroundColor Yellow

# Check Docker
try {
    $null = docker version 2>$null
    Write-Host "  ✓ Docker ist verfügbar" -ForegroundColor Green
} catch {
    Write-Host "  ✗ FEHLER: Docker ist nicht verfügbar oder läuft nicht." -ForegroundColor Red
    Write-Host "    Bitte starte Docker Desktop und versuche es erneut." -ForegroundColor Yellow
    exit 1
}

# Check TSV source directory
if (-not (Test-Path $tsvSourcePath)) {
    Write-Host "  ✗ FEHLER: TSV-Quellverzeichnis nicht gefunden: $tsvSourcePath" -ForegroundColor Red
    exit 1
}

$tsvFiles = Get-ChildItem -Path $tsvSourcePath -Filter "*.tsv" -File
if ($tsvFiles.Count -eq 0) {
    Write-Host "  ✗ FEHLER: Keine TSV-Dateien in $tsvSourcePath gefunden." -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ TSV-Quelle: $($tsvFiles.Count) Dateien gefunden" -ForegroundColor Green

# Check docmeta.jsonl
if (-not (Test-Path $docmetaPath)) {
    Write-Host "  ✗ FEHLER: docmeta.jsonl nicht gefunden: $docmetaPath" -ForegroundColor Red
    exit 1
}

$docmetaLines = (Get-Content $docmetaPath | Measure-Object -Line).Lines
Write-Host "  ✓ Docmeta: $docmetaLines Dokumente" -ForegroundColor Green

# Check BLF config
if (-not (Test-Path $blfConfigPath)) {
    Write-Host "  ✗ FEHLER: BlackLab-Konfiguration nicht gefunden: $blfConfigPath" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ BlackLab-Config gefunden" -ForegroundColor Green

# Check if Docker image is available
Write-Host "  Überprüfe Docker-Image..." -ForegroundColor Gray
$imageExists = docker images -q $IMAGE 2>$null
if (-not $imageExists) {
    Write-Host "  ! Docker-Image nicht lokal verfügbar, wird beim ersten Start heruntergeladen." -ForegroundColor Yellow
} else {
    Write-Host "  ✓ Docker-Image verfügbar" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Step 2: Backup Existing Index
# ============================================================================

Write-Host "[2/5] Sichere vorhandenen Index..." -ForegroundColor Yellow

if (Test-Path $indexTargetPath) {
    $indexFiles = Get-ChildItem -Path $indexTargetPath -File -Recurse
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
            Write-Host "  ✓ Backup erstellt: $backupDir" -ForegroundColor Green
        } else {
            Write-Host "  ! Backup übersprungen (--SkipBackup)" -ForegroundColor Yellow
            
            if (-not $Force) {
                Write-Host "  WARNUNG: Vorhandener Index wird gelöscht!" -ForegroundColor Red
                $confirmation = Read-Host "  Wirklich fortfahren? (j/n)"
                if ($confirmation -ne 'j' -and $confirmation -ne 'J') {
                    Write-Host "  Abgebrochen." -ForegroundColor Yellow
                    exit 0
                }
            }
            
            Remove-Item -Path $indexTargetPath -Recurse -Force
            Write-Host "  ✓ Vorhandener Index gelöscht" -ForegroundColor Green
        }
    } else {
        Write-Host "  ! Verzeichnis ist leer, kein Backup nötig" -ForegroundColor Gray
    }
} else {
    Write-Host "  ! Kein vorhandener Index, kein Backup nötig" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# Step 3: Prepare Target Directory
# ============================================================================

Write-Host "[3/5] Erstelle Zielverzeichnis..." -ForegroundColor Yellow

if (-not (Test-Path $indexTargetPath)) {
    New-Item -ItemType Directory -Path $indexTargetPath -Force | Out-Null
    Write-Host "  ✓ Verzeichnis erstellt: $indexTargetPath" -ForegroundColor Green
} else {
    Write-Host "  ✓ Verzeichnis existiert bereits" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Step 4: Run BlackLab Indexing
# ============================================================================

Write-Host "[4/5] Starte BlackLab-Indexierung..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Dies kann mehrere Minuten dauern (146 Dateien, ~1.5M Tokens)..." -ForegroundColor Gray
Write-Host ""

# Docker paths (container-internal)
$containerTsvPath = "/data/tsv"
$containerDocmetaPath = "/data/docmeta.jsonl"
$containerIndexPath = "/data/index"
$containerConfigPath = "/etc/blacklab/corapan-tsv.blf.yaml"

# Prepare parent directory for TSV source (we need to mount the parent to include both tsv/ and docmeta.jsonl)
$tsvSourceParent = Split-Path -Parent $tsvSourcePath

# Run BlackLab IndexTool in Docker
# We mount:
# - data/blacklab_index.backup/ -> /data (contains tsv/ and docmeta.jsonl)
# - data/blacklab_index/ -> /data/index (target)
# - config/blacklab/ -> /etc/blacklab (config)

$dockerCmd = @(
    "run", "--rm",
    "-v", "`"$tsvSourceParent`:/data:ro`"",
    "-v", "`"$indexTargetPath`:/data/index:rw`"",
    "-v", "`"$(Split-Path -Parent $blfConfigPath)`:/etc/blacklab:ro`"",
    $IMAGE,
    "blacklab-indexer",
    "create",
    $containerIndexPath,
    "$containerTsvPath/*.tsv",
    $containerConfigPath,
    "--docmeta", $containerDocmetaPath
)

Write-Host "  Führe aus: docker $($dockerCmd -join ' ')" -ForegroundColor Gray
Write-Host ""

try {
    $process = Start-Process -FilePath "docker" -ArgumentList $dockerCmd -NoNewWindow -Wait -PassThru
    
    if ($process.ExitCode -eq 0) {
        Write-Host ""
        Write-Host "  ✓ Indexierung erfolgreich abgeschlossen" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "  ✗ FEHLER: Indexierung fehlgeschlagen (Exit Code: $($process.ExitCode))" -ForegroundColor Red
        Write-Host "    Prüfe die Ausgabe oben für Details." -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "  ✗ FEHLER beim Ausführen von Docker: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# Step 5: Verify Index
# ============================================================================

Write-Host "[5/5] Überprüfe Index..." -ForegroundColor Yellow

# Check if index directory has content
$indexFiles = Get-ChildItem -Path $indexTargetPath -File -Recurse
if ($indexFiles.Count -eq 0) {
    Write-Host "  ✗ FEHLER: Index-Verzeichnis ist leer!" -ForegroundColor Red
    Write-Host "    Die Indexierung ist fehlgeschlagen." -ForegroundColor Yellow
    exit 1
}

Write-Host "  ✓ Index enthält $($indexFiles.Count) Dateien" -ForegroundColor Green

# Calculate index size
$indexSize = (Get-ChildItem -Path $indexTargetPath -Recurse | Measure-Object -Property Length -Sum).Sum
$indexSizeMB = [math]::Round($indexSize / 1MB, 2)
Write-Host "  ✓ Index-Größe: $indexSizeMB MB" -ForegroundColor Green

# Check for expected Lucene files
$expectedFiles = @("segments_*", "*.si", "*.fnm")
$hasLuceneFiles = $false
foreach ($pattern in $expectedFiles) {
    if (Get-ChildItem -Path $indexTargetPath -Filter $pattern -Recurse -File) {
        $hasLuceneFiles = $true
        break
    }
}

if ($hasLuceneFiles) {
    Write-Host "  ✓ Lucene-Index-Dateien gefunden (Lucene 9 kompatibel)" -ForegroundColor Green
} else {
    Write-Host "  ! WARNUNG: Keine typischen Lucene-Dateien gefunden" -ForegroundColor Yellow
    Write-Host "    Der Index könnte unvollständig sein." -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# Success Summary
# ============================================================================

Write-Host "=========================================" -ForegroundColor Green
Write-Host "Index-Build erfolgreich abgeschlossen!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Zusammenfassung:" -ForegroundColor White
Write-Host "  Quelle:       $($tsvFiles.Count) TSV-Dateien" -ForegroundColor Gray
Write-Host "  Dokumente:    $docmetaLines" -ForegroundColor Gray
Write-Host "  Index-Größe:  $indexSizeMB MB" -ForegroundColor Gray
Write-Host "  Index-Pfad:   $indexTargetPath" -ForegroundColor Gray
Write-Host ""
Write-Host "Nächste Schritte:" -ForegroundColor Cyan
Write-Host "  1. BlackLab-Server starten:" -ForegroundColor White
Write-Host "     .\scripts\start_blacklab_docker.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Test durchführen:" -ForegroundColor White
Write-Host "     Invoke-WebRequest -Uri 'http://localhost:8081/blacklab-server/' -UseBasicParsing" -ForegroundColor Gray
Write-Host "     Erwartung: HTTP 200 mit JSON (kein HTTP 500)" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Flask starten und Advanced Search testen:" -ForegroundColor White
Write-Host "     .venv\Scripts\activate" -ForegroundColor Gray
Write-Host "     `$env:FLASK_ENV=`"development`"" -ForegroundColor Gray
Write-Host "     python -m src.app.main" -ForegroundColor Gray
Write-Host "     http://localhost:8000/search/advanced" -ForegroundColor Gray
Write-Host ""

exit 0
