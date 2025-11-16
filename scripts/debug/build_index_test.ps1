# Encoding: UTF-8
# BlackLab Index Build Script - ASCII Version

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $SCRIPT_DIR))
$PYTHON_SCRIPT = Join-Path $SCRIPT_DIR "blacklab_index_creation.py"
$TRANSCRIPTS_DIR = Join-Path $PROJECT_ROOT "media\transcripts"
$EXPORTS_DIR = Join-Path $PROJECT_ROOT "data\exports"
$EXPORT_TSV_DIR = Join-Path $EXPORTS_DIR "tsv"
$DOCMETA_PATH = Join-Path $EXPORTS_DIR "docmeta.jsonl"

Write-Host "Starting build..." -ForegroundColor Cyan
Write-Host "Paths:"
Write-Host "  PROJECT_ROOT: $PROJECT_ROOT"
Write-Host "  PYTHON_SCRIPT: $PYTHON_SCRIPT"
Write-Host ""

Write-Host "[1/3] Checking Prerequisites..."

$jsonCount = (Get-ChildItem -Path $TRANSCRIPTS_DIR -Filter "*.json" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Host "  Found $jsonCount JSON files in $TRANSCRIPTS_DIR"

Write-Host ""
Write-Host "[2/3] Running Python export..."
Write-Host "  python $PYTHON_SCRIPT --root $TRANSCRIPTS_DIR --out $EXPORT_TSV_DIR --docmeta $DOCMETA_PATH"
Write-Host ""

python $PYTHON_SCRIPT --root $TRANSCRIPTS_DIR --out $EXPORT_TSV_DIR --docmeta $DOCMETA_PATH

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK] Export successful"
    $tsvCount = (Get-ChildItem -Path $EXPORT_TSV_DIR -Filter "*.tsv" -File -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Host "  Created $tsvCount TSV files"
} else {
    Write-Host ""
    Write-Host "[FEHLER] Export failed (Exit Code: $LASTEXITCODE)"
    exit 1
}

Write-Host ""
Write-Host "[FERTIG] Step 1 complete. Now run:"
Write-Host "  .\scripts\build_blacklab_index.ps1"
Write-Host ""
