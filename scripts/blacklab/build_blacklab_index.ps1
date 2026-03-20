<#
.SYNOPSIS
  Docker-based BlackLab index builder (BlackLab 5.x / Lucene 9)
.DESCRIPTION
  Builds the corpus index from TSV files using BlackLab IndexTool in Docker.
  Uses --threads 1 to prevent race conditions on Windows/OneDrive.
#>

param(
    [switch]$SkipBackup,
    [switch]$Force,
    [switch]$Activate = $true
)

$ErrorActionPreference = "Stop"

# Configuration
$BLACKLAB_IMAGE = if ($env:BLACKLAB_IMAGE) { $env:BLACKLAB_IMAGE } else { "instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7" }
$TSV_SOURCE_DIR = "data\blacklab\export\tsv"
$DOCMETA_FILE = "data\blacklab\export\docmeta.jsonl"
$INDEX_TARGET_DIR = "data\blacklab\index"
$INDEX_TARGET_DIR_NEW = "data\blacklab\quarantine\index.build"
$BLF_CONFIG = "config\blacklab\corapan-tsv.blf.yaml"

# Resolve paths
$repoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$dataRoot = Join-Path $repoRoot "data"
$blacklabRoot = Join-Path $dataRoot "blacklab"
$exportRoot = Join-Path $blacklabRoot "export"
$backupRoot = Join-Path $blacklabRoot "backups"
$quarantineRoot = Join-Path $blacklabRoot "quarantine"
$configRoot = Join-Path $repoRoot "config"

$tsvSourcePath = Join-Path $exportRoot "tsv"
$docmetaPath = Join-Path $exportRoot "docmeta.jsonl"
$indexTargetPath = Join-Path $blacklabRoot "index"
$indexTargetPathNew = Join-Path $quarantineRoot "index.build"
$blfConfigPath = Join-Path $configRoot "blacklab\corapan-tsv.blf.yaml"
$BUILD_LOG = Join-Path $quarantineRoot "build.log"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "BlackLab Index Build (Docker-based, BlackLab 5.x / Lucene 9)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Configuration:" -ForegroundColor White
Write-Host "  Repository:      $repoRoot" -ForegroundColor Gray
Write-Host "  BlackLab Root:   $blacklabRoot" -ForegroundColor Cyan
Write-Host "  Export Root:     $exportRoot" -ForegroundColor Cyan
Write-Host "  Backup Root:     $backupRoot" -ForegroundColor Cyan
Write-Host "  Quarantine Root: $quarantineRoot" -ForegroundColor Cyan
Write-Host "  Docker Image:    $BLACKLAB_IMAGE" -ForegroundColor Cyan
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
# Step 2: Prepare canonical BlackLab directories
# ============================================================================

Write-Host "[2/4] Preparing BlackLab directories..." -ForegroundColor Yellow

New-Item -ItemType Directory -Path $exportRoot -Force | Out-Null
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
New-Item -ItemType Directory -Path $quarantineRoot -Force | Out-Null

if (Test-Path $indexTargetPathNew) {
    Write-Host "  Removing previous staged build..." -ForegroundColor Gray
    Remove-Item -Path $indexTargetPathNew -Recurse -Force
}

Write-Host "  OK Canonical BlackLab directories are ready" -ForegroundColor Green

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
$exportPath = $exportRoot
$exportMount = $exportPath.Replace('\', '/').Replace('C:', '/c')
$indexMount = $indexTargetPathNew.Replace('\', '/').Replace('C:', '/c')
$configMount = (Join-Path $configRoot "blacklab").Replace('\', '/').Replace('C:', '/c')

# Build Docker command
    # Ensure metadata directory exists for IndexTool (IndexTool expects per-file JSONs in linked-file-dir)
    $exportMetadataDir = Join-Path $exportPath "metadata"
    if (-not (Test-Path $exportMetadataDir)) {
        if (Test-Path $docmetaPath) {
            Write-Host "  metadata dir missing; creating from docmeta.jsonl..." -ForegroundColor Gray
            python (Join-Path $repoRoot "scripts\blacklab\docmeta_to_metadata_dir.py") 2>&1 | Out-Host
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

# Swap new index into place atomically (only if -Activate is true)
if ($Activate) {
    $backupDir = Join-Path $backupRoot ("index_{0}" -f (Get-Date -Format "yyyy-MM-dd_HHmmss"))

    if (Test-Path $indexTargetPath) {
        if (-not $SkipBackup) {
            Move-Item -Path $indexTargetPath -Destination $backupDir -Force
            Write-Host ("  OK Backup created: {0}" -f $backupDir) -ForegroundColor Green
        } else {
            Remove-Item -Path $indexTargetPath -Recurse -Force
            Write-Host "  INFO: Existing active index removed without backup" -ForegroundColor Yellow
        }
    }

    Move-Item -Path $newIndexPath -Destination $indexTargetPath -Force
    Write-Host ("  OK Activated new index: {0}" -f $indexTargetPath) -ForegroundColor Green
} else {
    Write-Host ("  INFO: Index built but NOT activated: {0}" -f $newIndexPath) -ForegroundColor Cyan
}

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
Write-Host "  1. Start server:  .\scripts\blacklab\start_blacklab_docker_v3.ps1 -Detach" -ForegroundColor Gray
Write-Host "  2. Test server:   Invoke-WebRequest 'http://localhost:8081/blacklab-server/' -UseBasicParsing" -ForegroundColor Gray
Write-Host "  3. Start Flask:   .venv\Scripts\activate; python -m src.app.main" -ForegroundColor Gray
Write-Host "  4. Test webapp:   http://localhost:8000/search/advanced" -ForegroundColor Gray
Write-Host ""

exit 0
