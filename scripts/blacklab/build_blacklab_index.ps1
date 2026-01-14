<#
.SYNOPSIS
  Docker-based BlackLab index builder (BlackLab 5.x / Lucene 9)
.DESCRIPTION
  Builds the corpus index from TSV files using BlackLab IndexTool in Docker.
  Uses --threads 1 to prevent race conditions on Windows/OneDrive.
#>

param(
    [switch]$SkipBackup,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Configuration
$BLACKLAB_IMAGE = "instituutnederlandsetaal/blacklab:latest"
$TSV_SOURCE_DIR = "data\blacklab_export\tsv"
$DOCMETA_FILE = "data\blacklab_export\docmeta.jsonl"
$INDEX_TARGET_DIR = "data\blacklab_index"
$INDEX_TARGET_DIR_NEW = "data\blacklab_index.new"
$BLF_CONFIG = "config\blacklab\corapan-tsv.blf.yaml"

# Resolve paths
$repoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$tsvSourcePath = Join-Path $repoRoot $TSV_SOURCE_DIR
$docmetaPath = Join-Path $repoRoot $DOCMETA_FILE
$indexTargetPath = Join-Path $repoRoot $INDEX_TARGET_DIR
$indexTargetPathNew = Join-Path $repoRoot $INDEX_TARGET_DIR_NEW
$blfConfigPath = Join-Path $repoRoot $BLF_CONFIG
$BUILD_LOG = Join-Path $indexTargetPathNew "build.log"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "BlackLab Index Build (Docker-based, BlackLab 5.x / Lucene 9)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Configuration:" -ForegroundColor White
Write-Host "  Repository:      $repoRoot" -ForegroundColor Gray
Write-Host "  Docker Image:    $BLACKLAB_IMAGE" -ForegroundColor Gray
Write-Host "  TSV Source:      $tsvSourcePath" -ForegroundColor Gray
Write-Host "  Docmeta:         $docmetaPath" -ForegroundColor Gray
Write-Host "  Target Index:    $indexTargetPath" -ForegroundColor Gray
Write-Host ""

# Run migration to normalize JSON files before indexing/export
$migScript = Join-Path $repoRoot "scripts\migrate_json_v3.py"
if (Test-Path $migScript) {
    Write-Host "  Running migrate_json_v3.py to normalize JSON files..." -ForegroundColor Gray
    python $migScript 2>&1 | Out-Host
} else {
    Write-Host "  Note: migrate_json_v3.py not found; skipping migration" -ForegroundColor Yellow
}
# ============================================================================
# Step 1: Verify Prerequisites
# ============================================================================

Write-Host "[1/4] Verifying prerequisites..." -ForegroundColor Yellow

# Check Docker
Write-Host "  Checking Docker..." -ForegroundColor Gray
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Host "  ERROR: Docker not found!" -ForegroundColor Red
    exit 1
}

try {
    $null = docker version --format "{{.Server.Version}}" 2>&1
    Write-Host "  OK Docker is available" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Docker daemon not responding!" -ForegroundColor Red
    exit 1
}

# Check TSV source
if (-not (Test-Path $tsvSourcePath)) {
    Write-Host ("  ERROR: TSV source not found: {0}" -f $tsvSourcePath) -ForegroundColor Red
    exit 1
}

$tsvFiles = @(Get-ChildItem -Path $tsvSourcePath -Filter "*.tsv" -File)
if ($tsvFiles.Count -eq 0) {
    Write-Host "  ERROR: No TSV files found!" -ForegroundColor Red
    exit 1
}
Write-Host ("  OK TSV source: {0} files" -f $tsvFiles.Count) -ForegroundColor Green

# Check docmeta
if (-not (Test-Path $docmetaPath)) {
    Write-Host ("  ERROR: docmeta.jsonl not found: {0}" -f $docmetaPath) -ForegroundColor Red
    exit 1
}

$docmetaLines = @(Get-Content $docmetaPath).Count
Write-Host ("  OK Docmeta: {0} documents" -f $docmetaLines) -ForegroundColor Green

# Check BLF config
if (-not (Test-Path $blfConfigPath)) {
    Write-Host ("  ERROR: BLF config not found: {0}" -f $blfConfigPath) -ForegroundColor Red
    exit 1
}
Write-Host "  OK BLF config found" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 2: Backup Existing Index
# ============================================================================

Write-Host "[2/4] Backing up existing index..." -ForegroundColor Yellow

$backupDir = Join-Path $repoRoot "data\blacklab_index.backup"
$targetIndexPath = $indexTargetPath

if (Test-Path $targetIndexPath) {
    $indexFiles = @(Get-ChildItem -Path $indexTargetPath -File -Recurse -ErrorAction SilentlyContinue)
    if ($indexFiles.Count -gt 0) {
        if (-not $SkipBackup) {
            # Remove old backup if it exists
            if (Test-Path $backupDir) {
                Write-Host "  Removing old backup..." -ForegroundColor Gray
                Remove-Item -Path $backupDir -Recurse -Force
            }
            
            Write-Host ("  Creating backup: {0}" -f $backupDir) -ForegroundColor Gray
            
            if (-not $Force) {
                $confirm = Read-Host "  Continue? (y/n)"
                if ($confirm -ne 'y' -and $confirm -ne 'Y') {
                    Write-Host "Aborted."
                    exit 0
                }
            }
            
            Move-Item -Path $targetIndexPath -Destination $backupDir -Force
            Write-Host ("  OK Backup created: {0}" -f $backupDir) -ForegroundColor Green
        } else {
            Write-Host "  INFO: Backup skipped" -ForegroundColor Yellow
            if (-not $Force) {
                $confirm = Read-Host "  Delete existing index? (y/n)"
                if ($confirm -ne 'y' -and $confirm -ne 'Y') {
                    Write-Host "Aborted."
                    exit 0
                }
            }
            Remove-Item -Path $indexTargetPath -Recurse -Force
            Write-Host "  OK Index deleted" -ForegroundColor Green
        }
    }
}

Write-Host ""

# ============================================================================
# Step 3: Pull Docker Image
# ============================================================================

Write-Host "[3/4] Checking Docker image..." -ForegroundColor Yellow

$imageExists = docker images --format "{{.Repository}}:{{.Tag}}" | Where-Object { $_ -eq $BLACKLAB_IMAGE } | Measure-Object | Select-Object -ExpandProperty Count

if ($imageExists -eq 0) {
    Write-Host "  Pulling image (this may take a few minutes)..." -ForegroundColor Gray
    docker pull $BLACKLAB_IMAGE
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to pull image!" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  OK Image available" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 4: Run Index Build in Docker
# ============================================================================

Write-Host "[4/4] Running index build..." -ForegroundColor Yellow
Write-Host "  This will take 5-10 minutes..." -ForegroundColor Gray
Write-Host ""

# Create a clean temporary index directory (we'll swap atomically after a successful build)
if (Test-Path $indexTargetPathNew) { Remove-Item -Path $indexTargetPathNew -Recurse -Force }
New-Item -ItemType Directory -Path $indexTargetPathNew -Force | Out-Null

# Prepare a clean TSV directory that excludes *_min.tsv files (these are small/alternate-format TSVs used for tests)
$tsvForIndexDir = Join-Path $tsvSourcePath "tsv_for_index"
if (Test-Path $tsvForIndexDir) { Remove-Item -Path $tsvForIndexDir -Recurse -Force }
New-Item -ItemType Directory -Path $tsvForIndexDir -Force | Out-Null

# Copy only TSV files that are NOT suffix _min.tsv
Write-Host "  Copying TSV files (excluding '*_min.tsv') to: $tsvForIndexDir" -ForegroundColor Gray
Get-ChildItem -Path $tsvSourcePath -Filter "*.tsv" -File | Where-Object { $_.Name -notlike '*_min.tsv' } | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $tsvForIndexDir -Force
}

# Convert Windows paths to Docker format
$exportPath = Join-Path $repoRoot "data\blacklab_export"
$exportMount = $exportPath.Replace('\', '/').Replace('C:', '/c')
$indexMount = $indexTargetPathNew.Replace('\', '/').Replace('C:', '/c')
$configMount = (Join-Path $repoRoot "config\blacklab").Replace('\', '/').Replace('C:', '/c')

# Build Docker command
    # Ensure metadata directory exists for IndexTool (IndexTool expects per-file JSONs in linked-file-dir)
    $exportMetadataDir = Join-Path $exportPath "metadata"
    if (-not (Test-Path $exportMetadataDir)) {
        if (Test-Path $docmetaPath) {
            Write-Host "  metadata dir missing; creating from docmeta.jsonl..." -ForegroundColor Gray
            python scripts/docmeta_to_metadata_dir.py 2>&1 | Out-Host
        } else {
            Write-Host "  WARNING: docmeta.jsonl missing; continuing without metadata directory" -ForegroundColor Yellow
        }
    }

    $dockerArgs = @(
    "run", "--rm"
    "-v", ($exportMount + ":/data/export:ro")
    "-v", ($indexMount + ":/data/index:rw")
    "-v", ($configMount + ":/config:ro")
    $BLACKLAB_IMAGE
    "java", "-cp", "/usr/local/lib/blacklab-tools/*"
    "nl.inl.blacklab.tools.IndexTool", "create"
    "/data/index"
    "/data/export/tsv/tsv_for_index"
    "/config/corapan-tsv.blf.yaml"
    "--linked-file-dir", "/data/export/metadata",
    "--threads", "1"
)

# Initialize build log
$logHeader = "# BlackLab Index Build Log - $(Get-Date -Format o)`n# Image: $BLACKLAB_IMAGE`n`n"
$logHeader | Out-File -FilePath $BUILD_LOG -Encoding utf8 -Force

Write-Host "  Docker command:" -ForegroundColor DarkGray
Write-Host ("  docker {0}" -f ($dockerArgs -join ' ')) -ForegroundColor DarkGray
Write-Host ""

try {
    & docker $dockerArgs *>> $BUILD_LOG
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host ("  ERROR: Build failed (exit code: {0})" -f $LASTEXITCODE) -ForegroundColor Red
        Write-Host ("  See log: {0}" -f $BUILD_LOG) -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host ("  ERROR: {0}" -f $_) -ForegroundColor Red
    exit 1
}

Write-Host "  OK Index build completed" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Verify and Summary
# ============================================================================

# Check the newly created index directory
$newIndexPath = $indexTargetPathNew
$indexFiles = @(Get-ChildItem -Path $newIndexPath -File -Recurse -ErrorAction SilentlyContinue)
if ($indexFiles.Count -eq 0) {
    Write-Host "ERROR: New index directory is empty!" -ForegroundColor Red
    exit 1
}

# Swap new index into place atomically. Backup existing index if present
if (Test-Path $indexTargetPath) {
    if (Test-Path $backupDir) { Remove-Item -Path $backupDir -Recurse -Force }
    Move-Item -Path $indexTargetPath -Destination $backupDir -Force
    Write-Host ("  OK Backup created: {0}" -f $backupDir) -ForegroundColor Green
}

Move-Item -Path $newIndexPath -Destination $indexTargetPath -Force
Write-Host ("  OK Activated new index: {0}" -f $indexTargetPath) -ForegroundColor Green

$indexSizeMB = [math]::Round(($indexFiles | Measure-Object -Property Length -Sum).Sum / 1MB, 2)

Write-Host "================================================================" -ForegroundColor Green
Write-Host "Index Build Completed Successfully!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor White
Write-Host ("  TSV Files:   {0}" -f $tsvFiles.Count) -ForegroundColor Gray
Write-Host ("  Documents:   {0}" -f $docmetaLines) -ForegroundColor Gray
Write-Host ("  Index Size:  {0} MB" -f $indexSizeMB) -ForegroundColor Gray
Write-Host ("  Index Path:  {0}" -f $targetIndexPath) -ForegroundColor Gray
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Start server:  .\scripts\start_blacklab_docker_v3.ps1 -Detach" -ForegroundColor Gray
Write-Host "  2. Test server:   Invoke-WebRequest 'http://localhost:8081/blacklab-server/' -UseBasicParsing" -ForegroundColor Gray
Write-Host "  3. Start Flask:   .venv\Scripts\activate; python -m src.app.main" -ForegroundColor Gray
Write-Host "  4. Test webapp:   http://localhost:8000/search/advanced" -ForegroundColor Gray
Write-Host ""

exit 0
