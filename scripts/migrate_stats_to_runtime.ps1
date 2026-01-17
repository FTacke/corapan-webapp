[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# Repository root
$repoRoot = Split-Path -Parent $PSScriptRoot

# Ensure CORAPAN_RUNTIME_ROOT (dev default)
if (-not $env:CORAPAN_RUNTIME_ROOT) {
    $env:CORAPAN_RUNTIME_ROOT = Join-Path $repoRoot "runtime\corapan"
}

$sourceDir = Join-Path $repoRoot "data\public\statistics"
$targetDir = Join-Path $env:CORAPAN_RUNTIME_ROOT "data\public\statistics"

if (-not (Test-Path $sourceDir)) {
    Write-Host "No repo statistics directory found at: $sourceDir" -ForegroundColor Gray
    exit 0
}

$targetFiles = @()
if (Test-Path $targetDir) {
    $targetFiles = Get-ChildItem -Path $targetDir -File -Recurse -ErrorAction SilentlyContinue
}

if ($targetFiles.Count -gt 0) {
    Write-Host "Runtime statistics already present at: $targetDir" -ForegroundColor Gray
    exit 0
}

Write-Host "Migrating repo statistics to runtime..." -ForegroundColor Yellow
Write-Host "  Source: $sourceDir" -ForegroundColor Gray
Write-Host "  Target: $targetDir" -ForegroundColor Gray

New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
Copy-Item -Path (Join-Path $sourceDir '*') -Destination $targetDir -Recurse -Force

$copied = Get-ChildItem -Path $targetDir -File -Recurse -ErrorAction SilentlyContinue
Write-Host "Copied files: $($copied.Count)" -ForegroundColor Green