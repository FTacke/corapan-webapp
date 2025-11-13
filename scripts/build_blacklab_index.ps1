<#
.SYNOPSIS
    Build BlackLab Lucene 9 index from TSV source files using IndexTool.

.DESCRIPTION
    This script rebuilds the BlackLab index from TSV files in data/blacklab_index.backup/tsv/.
    It creates a fresh Lucene 9 compatible index by running BlackLab's IndexTool via JAR file.

    Prerequisites:
    - Java 11+ must be installed and on PATH
    - BlackLab JAR file (either via $env:BLACKLAB_JAR or in tools/blacklab/)
    - TSV source files must exist in data/blacklab_index.backup/tsv/
    - BlackLab config must exist in config/blacklab/corapan-tsv.blf.yaml
    - docmeta.jsonl must exist in data/blacklab_index.backup/

    The script will:
    1. Verify all prerequisites (Java, JAR, TSV files)
    2. Backup existing index (if present)
    3. Create empty target directory
    4. Run BlackLab IndexTool to build the index
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
    Requires: Java 11+, BlackLab JAR
#>

[CmdletBinding()]
param(
    [switch]$SkipBackup,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Configuration
$TSV_SOURCE_DIR = "data\blacklab_index.backup\tsv"
$DOCMETA_FILE = "data\blacklab_index.backup\docmeta.jsonl"
$INDEX_TARGET_DIR = "data\blacklab_index"
$BLF_CONFIG = "config\blacklab\corapan-tsv.blf.yaml"
$JAR_FALLBACK = "tools\blacklab\blacklab-server.jar"

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
$jarFallbackPath = Join-Path $repoRoot $JAR_FALLBACK

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

Write-Host "[1/5] Pruefe Voraussetzungen..." -ForegroundColor Yellow

# Check Java
Write-Host "  Pruefe Java..." -ForegroundColor Gray
$javaCmd = Get-Command java -ErrorAction SilentlyContinue
if ($javaCmd) {
    $oldErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $javaVersion = & java -version 2>&1 | Select-String "version" | Select-Object -First 1
    $ErrorActionPreference = $oldErrorAction
    Write-Host "  OK Java ist verfuegbar: $javaVersion" -ForegroundColor Green
} else {
    Write-Host "  FEHLER: Java ist nicht verfuegbar oder nicht im PATH." -ForegroundColor Red
    Write-Host "    Bitte installiere Java 11+ und fuege es zum PATH hinzu." -ForegroundColor Yellow
    exit 1
}

# Find BlackLab JAR
Write-Host "  Suche BlackLab JAR..." -ForegroundColor Gray
$blacklabJar = $null

if ($env:BLACKLAB_JAR) {
    if (Test-Path $env:BLACKLAB_JAR) {
        $blacklabJar = $env:BLACKLAB_JAR
        Write-Host "  OK BlackLab JAR gefunden via Umgebungsvariable: $blacklabJar" -ForegroundColor Green
    } else {
        Write-Host "  WARNUNG: BLACKLAB_JAR ist gesetzt, aber Datei nicht gefunden: $env:BLACKLAB_JAR" -ForegroundColor Yellow
    }
}

if (-not $blacklabJar -and (Test-Path $jarFallbackPath)) {
    $blacklabJar = $jarFallbackPath
    Write-Host "  OK BlackLab JAR gefunden: $blacklabJar" -ForegroundColor Green
}

if (-not $blacklabJar) {
    Write-Host "  FEHLER: BlackLab JAR nicht gefunden!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Bitte lade das BlackLab Server JAR herunter:" -ForegroundColor Yellow
    Write-Host "    1. Besuche: https://github.com/INL/BlackLab/releases" -ForegroundColor Gray
    Write-Host "    2. Lade blacklab-server-X.Y.Z.jar herunter" -ForegroundColor Gray
    Write-Host "    3. Speichere es als: $jarFallbackPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Alternativ: Setze die Umgebungsvariable:" -ForegroundColor Yellow
    Write-Host "    `$env:BLACKLAB_JAR = `"C:\Pfad\zu\blacklab-server.jar`"" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Check TSV source directory
if (-not (Test-Path $tsvSourcePath)) {
    Write-Host "  FEHLER: TSV-Quellverzeichnis nicht gefunden: $tsvSourcePath" -ForegroundColor Red
    exit 1
}

$tsvFiles = Get-ChildItem -Path $tsvSourcePath -Filter "*.tsv" -File
if ($tsvFiles.Count -eq 0) {
    Write-Host "  FEHLER: Keine TSV-Dateien in $tsvSourcePath gefunden." -ForegroundColor Red
    exit 1
}

Write-Host "  OK TSV-Quelle: $($tsvFiles.Count) Dateien gefunden" -ForegroundColor Green

# Check docmeta.jsonl
if (-not (Test-Path $docmetaPath)) {
    Write-Host "  FEHLER: docmeta.jsonl nicht gefunden: $docmetaPath" -ForegroundColor Red
    exit 1
}

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
            Write-Host "  OK Vorhandener Index geloescht" -ForegroundColor Green
        }
    } else {
        Write-Host "  INFO: Verzeichnis ist leer, kein Backup noetig" -ForegroundColor Gray
    }
} else {
    Write-Host "  INFO: Kein vorhandener Index, kein Backup noetig" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# Step 3: Prepare Target Directory
# ============================================================================

Write-Host "[3/5] Erstelle Zielverzeichnis..." -ForegroundColor Yellow

if (-not (Test-Path $indexTargetPath)) {
    New-Item -ItemType Directory -Path $indexTargetPath -Force | Out-Null
    Write-Host "  OK Verzeichnis erstellt: $indexTargetPath" -ForegroundColor Green
} else {
    Write-Host "  OK Verzeichnis existiert bereits" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Step 4: Run BlackLab IndexTool
# ============================================================================

Write-Host "[4/5] Starte BlackLab-Indexierung..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Dies kann mehrere Minuten dauern (146 Dateien, ~1.5M Tokens)..." -ForegroundColor Gray
Write-Host ""

# Build IndexTool command
# Note: IndexTool expects TSV glob pattern for input files
$tsvGlob = Join-Path $tsvSourcePath "*.tsv"

$javaArgs = @(
    "-cp", $blacklabJar,
    "nl.inl.blacklab.tools.IndexTool",
    "create",
    $indexTargetPath,
    $tsvGlob,
    $blfConfigPath
)

# Add docmeta if exists
if (Test-Path $docmetaPath) {
    $javaArgs += "--docmeta"
    $javaArgs += $docmetaPath
}

Write-Host "  Fuehre aus: java $($javaArgs -join ' ')" -ForegroundColor Gray
Write-Host ""

try {
    & java $javaArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "  OK Indexierung erfolgreich abgeschlossen" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "  FEHLER: Indexierung fehlgeschlagen (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
        Write-Host "    Pruefe die Ausgabe oben fuer Details." -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "  FEHLER beim Ausfuehren von IndexTool: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# Step 5: Verify Index
# ============================================================================

Write-Host "[5/5] Pruefe Index..." -ForegroundColor Yellow

# Check if index directory has content
$indexFiles = Get-ChildItem -Path $indexTargetPath -File -Recurse
if ($indexFiles.Count -eq 0) {
    Write-Host "  FEHLER: Index-Verzeichnis ist leer!" -ForegroundColor Red
    Write-Host "    Die Indexierung ist fehlgeschlagen." -ForegroundColor Yellow
    exit 1
}

Write-Host "  OK Index enthaelt $($indexFiles.Count) Dateien" -ForegroundColor Green

# Calculate index size
$indexSize = (Get-ChildItem -Path $indexTargetPath -Recurse | Measure-Object -Property Length -Sum).Sum
$indexSizeMB = [math]::Round($indexSize / 1MB, 2)
Write-Host "  OK Index-Groesse: $indexSizeMB MB" -ForegroundColor Green

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
    Write-Host "  OK Lucene-Index-Dateien gefunden (Lucene 9 kompatibel)" -ForegroundColor Green
} else {
    Write-Host "  WARNUNG: Keine typischen Lucene-Dateien gefunden" -ForegroundColor Yellow
    Write-Host "    Der Index koennte unvollstaendig sein." -ForegroundColor Yellow
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
Write-Host "  Index-Groesse: $indexSizeMB MB" -ForegroundColor Gray
Write-Host "  Index-Pfad:   $indexTargetPath" -ForegroundColor Gray
Write-Host ""
Write-Host "Naechste Schritte:" -ForegroundColor Cyan
Write-Host "  1. BlackLab-Server starten:" -ForegroundColor White
Write-Host "     .\scripts\start_blacklab_docker.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Test durchfuehren:" -ForegroundColor White
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
