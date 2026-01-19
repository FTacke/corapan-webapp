#!/usr/bin/env pwsh
<#
.SYNOPSIS
    CO.RA.PAN Release Gates Check

DESCRIPTION
    Automated checks for runtime data contract:
    - Verify corpus stats endpoint exists
    - Verify AUTH_DATABASE_URL has no SQLite fallback
    - Verify runtime stats assets are present (warning only)
    - Verify runtime public stats DBs exist (warning only)

.PARAMETER RepoRoot
    Path to repository root (default: current directory)

.EXAMPLE
    .\scripts\check_release_gates.ps1
    .\scripts\check_release_gates.ps1 -RepoRoot C:\dev\corapan-webapp
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$RepoRoot = (Get-Location).Path
)

# ==============================================================================
# Setup
# ==============================================================================

$ErrorActionPreference = "Stop"
$script:ExitCode = 0
$script:FailCount = 0

if (-not (Test-Path $RepoRoot)) {
    Write-Error "RepoRoot does not exist: $RepoRoot"
    exit 1
}

# Navigate to repo root for relative paths
Push-Location $RepoRoot

# Resolve src directory
$srcPath = Join-Path $RepoRoot "src"
if (-not (Test-Path $srcPath)) {
    Write-Error "Source directory not found: $srcPath"
    exit 1
}

function Write-CheckHeader {
    param([string]$Message)
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
}

function Write-Pass {
    param([string]$Message)
    Write-Host "  ✅ $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "  ❌ $Message" -ForegroundColor Red
    $script:FailCount++
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  ⚠️  $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "     $Message" -ForegroundColor Gray
}

# ==============================================================================
# Check 1: corpus stats endpoint exists
# ==============================================================================

$corpusStatsRoute = "/corpus/api/" + "corpus_stats"
Write-CheckHeader "Check 1: corpus stats endpoint exists"

$corpusFile = "src\app\routes\corpus.py"
if (Test-Path $corpusFile) {
    $content = Get-Content $corpusFile -Raw
    
    if ($content -match '_CORPUS_STATS_ROUTE') {
        Write-Pass "Endpoint @blueprint.get(_CORPUS_STATS_ROUTE) exists (mounted under $corpusStatsRoute)"
        
        # Check if it handles missing file gracefully
        if ($content -match "if not.*exists|\.exists\(\).*404|return.*404|abort\(404\)") {
            Write-Pass "Endpoint handles missing corpus_stats.json (404)"
        } else {
            Write-Warn "Endpoint may not handle missing corpus_stats.json"
        }
    } else {
        Write-Fail "Corpus stats endpoint not found in $corpusFile"
    }
} else {
    Write-Fail "$corpusFile not found"
}

# ==============================================================================
# Check 2: AUTH_DATABASE_URL has no SQLite fallback
# ==============================================================================

Write-CheckHeader "Check 2: AUTH_DATABASE_URL fail-fast (no SQLite fallback)"

$configFile = "src\app\config\__init__.py"
if (Test-Path $configFile) {
    $content = Get-Content $configFile -Raw
    
    # Check for SQLite fallback pattern
    if ($content -match 'AUTH_DATABASE_URL.*=.*os\.environ\.get.*sqlite:///') {
        Write-Fail "Found SQLite fallback in $configFile"
        Write-Info "AUTH_DATABASE_URL should fail if not set (no default)"
    } elseif ($content -match 'AUTH_DATABASE_URL\s*=\s*os\.getenv.*\s+if not AUTH_DATABASE_URL.*raise') {
        Write-Pass "AUTH_DATABASE_URL has fail-fast check (no fallback)"
    } else {
        Write-Warn "Could not verify fail-fast behavior for AUTH_DATABASE_URL"
    }
    
    # Check .env.example
    $envExample = ".env.example"
    if (Test-Path $envExample) {
        $envContent = Get-Content $envExample -Raw
        
        if ($envContent -match 'AUTH_DATABASE_URL=.*postgresql') {
            Write-Pass ".env.example uses PostgreSQL URL"
        } elseif ($envContent -match 'AUTH_DATABASE_URL=.*sqlite') {
            Write-Fail ".env.example still uses SQLite URL"
        } else {
            Write-Warn "Could not find AUTH_DATABASE_URL in .env.example"
        }
    }
} else {
    Write-Fail "$configFile not found"
}

# ==============================================================================
# Check 3: corpus_stats.json existence (warning only)
# ==============================================================================

Write-CheckHeader "Check 3: corpus_stats.json availability"

$runtimeRoot = if ($env:CORAPAN_RUNTIME_ROOT) { $env:CORAPAN_RUNTIME_ROOT } else { Join-Path $RepoRoot "runtime\corapan" }
$statsDir = Join-Path $runtimeRoot "data\public\statistics"
$statsFile = Join-Path $statsDir "corpus_stats.json"

if (Test-Path $statsFile) {
    Write-Pass "corpus_stats.json exists at $statsFile"
    
    # Validate JSON
    try {
        $json = Get-Content $statsFile -Raw | ConvertFrom-Json
        if ($json.total_words -and $json.total_duration -and $json.country_count) {
            Write-Pass "JSON has required fields (total_words, total_duration, country_count)"
        } else {
            Write-Warn "JSON may be missing expected fields"
        }
    } catch {
        Write-Fail "corpus_stats.json is not valid JSON: $($_.Exception.Message)"
    }
} else {
    Write-Warn "corpus_stats.json not found (expected for fresh checkout)"
    Write-Info "Run: python LOKAL/_0_json/05_publish_corpus_statistics.py"
    Write-Info "Endpoint will return 404 until file is generated"
}

# ==============================================================================
# Check 4: Stats databases (stats_files.db, stats_country.db)
# ==============================================================================

Write-CheckHeader "Check 4: Active stats databases"

$statsFiles = @{
    "stats_files.db" = (Join-Path $runtimeRoot "data\db\public\stats_files.db")
    "stats_country.db" = (Join-Path $runtimeRoot "data\db\public\stats_country.db")
}

foreach ($name in $statsFiles.Keys) {
    $path = $statsFiles[$name]
    if (Test-Path $path) {
        Write-Pass "$name exists"
    } else {
        Write-Warn "$name not found (run 03_build_metadata_stats.py)"
    }
}

# ==============================================================================
# Check 5: Obsolete endpoints removed
# ==============================================================================

Write-CheckHeader "Check 5: Obsolete endpoints removed"

$checks = @(
    @{
        File = "src\app\routes\atlas.py"
        Pattern = '/api/v1/atlas/overview'
        Name = "/api/v1/atlas/overview endpoint"
    },
    @{
        File = "src\app\services\atlas.py"
        Pattern = 'def fetch_overview'
        Name = "fetch_overview() function"
    }
)

foreach ($check in $checks) {
    if (Test-Path $check.File) {
        $content = Get-Content $check.File -Raw
        if ($content -match $check.Pattern) {
            Write-Fail "$($check.Name) still exists in $($check.File)"
        } else {
            Write-Pass "$($check.Name) correctly removed"
        }
    }
}

# ==============================================================================
# Summary
# ==============================================================================

Pop-Location

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
if ($script:FailCount -eq 0) {
    Write-Host "  ✅ ALL CHECKS PASSED" -ForegroundColor Green
    Write-Host "     Release gates are satisfied" -ForegroundColor Gray
    exit 0
} else {
    Write-Host "  ❌ $($script:FailCount) CHECK(S) FAILED" -ForegroundColor Red
    Write-Host "     Fix issues before proceeding with release" -ForegroundColor Gray
    exit 1
}
