#!/usr/bin/env pwsh
# TEST: Sync-StatisticsFiles - Scenario Testing
#
# Tests the hardened Sync-StatisticsFiles function in three scenarios:
# 1. Missing env vars -> SKIP with warning (graceful)
# 2. LocalStatsDir = RepoRoot -> REFUSED (hard guard)
# 3. LocalStatsDir = valid stats dir -> would upload N files (DryRun mode)

param(
    [Parameter(Mandatory = $false)]
    [string]$RepoRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$syncDataScript = Join-Path $RepoRoot "scripts\deploy_sync\sync_data.ps1"
$syncCoreScript = Join-Path $RepoRoot "scripts\deploy_sync\sync_core.ps1"

if (-not (Test-Path $syncCoreScript)) {
    Write-Host "ERROR: sync_core.ps1 not found" -ForegroundColor Red
    exit 1
}

. $syncCoreScript
. $syncDataScript

Write-Host ""
Write-Host "TEST: Sync-StatisticsFiles" -ForegroundColor Cyan
Write-Host ""

# SCENARIO 1: No env vars
Write-Host "SCENARIO 1: No env vars set" -ForegroundColor Yellow
$savedPublicStatsDir = $env:PUBLIC_STATS_DIR
$savedCorapanRoot = $env:CORAPAN_RUNTIME_ROOT
$env:PUBLIC_STATS_DIR = $null
$env:CORAPAN_RUNTIME_ROOT = $null

Write-Host "Expected: SKIP with warning"
Write-Host ""
$result1 = Sync-StatisticsFiles -LocalStatsDir $null -RemoteRuntimeRoot "/srv/webapps/corapan"
$success1 = $result1 -eq $true
Write-Host "Result: $(if ($success1) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($success1) { 'Green' } else { 'Red' })
Write-Host ""

# SCENARIO 2: RepoRoot as LocalStatsDir (guard should trigger)
Write-Host "SCENARIO 2: LocalStatsDir = RepoRoot (guard should reject)" -ForegroundColor Yellow
Write-Host "Expected: REFUSED (found .git, src/, package.json)"
Write-Host ""
$result2 = Sync-StatisticsFiles -LocalStatsDir $RepoRoot -RemoteRuntimeRoot "/srv/webapps/corapan"
$success2 = $result2 -eq $false
Write-Host "Result: $(if ($success2) { 'PASS (correctly refused)' } else { 'FAIL' })" -ForegroundColor $(if ($success2) { 'Green' } else { 'Red' })
Write-Host ""

# SCENARIO 3: Valid stats dir (DryRun)
Write-Host "SCENARIO 3: Valid stats dir with corpus_stats.json + viz_*.png" -ForegroundColor Yellow
$env:CORAPAN_RUNTIME_ROOT = "C:\dev\runtime\corapan"
$statsDir = Join-Path $env:CORAPAN_RUNTIME_ROOT "data\public\statistics"

if (Test-Path $statsDir) {
    $jsonExists = Test-Path (Join-Path $statsDir "corpus_stats.json")
    $pngCount = @(Get-ChildItem -Path $statsDir -Filter "viz_*.png" -File -ErrorAction SilentlyContinue).Count
    
    if ($jsonExists -and $pngCount -gt 0) {
        Write-Host "Stats found: 1 JSON + $pngCount PNG files"
        Write-Host "DryRun mode:"
        Write-Host ""
        $result3 = Sync-StatisticsFiles -LocalStatsDir $statsDir -RemoteRuntimeRoot "/srv/webapps/corapan" -DryRun
        $success3 = $result3 -eq $true
        Write-Host ""
        Write-Host "Result: $(if ($success3) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($success3) { 'Green' } else { 'Red' })
    }
    else {
        Write-Host "Stats dir exists but no files found. Skipping scenario 3."
        $success3 = $true
    }
}
else {
    Write-Host "Stats dir not found. Skipping scenario 3."
    $success3 = $true
}

Write-Host ""
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
$s1Status = if ($success1) { 'PASS' } else { 'FAIL' }
$s2Status = if ($success2) { 'PASS' } else { 'FAIL' }
$s3Status = if ($success3) { 'PASS' } else { 'FAIL' }
Write-Host "Scenario 1: $s1Status" -ForegroundColor $(if ($success1) { 'Green' } else { 'Red' })
Write-Host "Scenario 2: $s2Status" -ForegroundColor $(if ($success2) { 'Green' } else { 'Red' })
Write-Host "Scenario 3: $s3Status" -ForegroundColor $(if ($success3) { 'Green' } else { 'Red' })

$env:PUBLIC_STATS_DIR = $savedPublicStatsDir
$env:CORAPAN_RUNTIME_ROOT = $savedCorapanRoot

if ($success1 -and $success2 -and $success3) {
    exit 0
}
else {
    exit 1
}
