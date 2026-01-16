#!/usr/bin/env pwsh
<#
.SYNOPSIS
    CO.RA.PAN Release Gates Check

.DESCRIPTION
    Automated checks for data cleanup release:
    - Verify stats_all.db is fully removed
    - Verify /api/corpus_stats endpoint exists
    - Verify AUTH_DATABASE_URL has no SQLite fallback
    - Verify corpus_stats.json exists or 404 is handled

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
# Check 1: stats_all.db references removed
# ==============================================================================

Write-CheckHeader "Check 1: stats_all.db fully removed"

$patterns = @(
    "stats_all\.db",
    "fetch_overview",
    "atlas/overview",
    "get_stats_all_from_db"
)

$foundIssues = $false
foreach ($pattern in $patterns) {
    Write-Host "  Searching for: $pattern" -ForegroundColor White
    
    $matches = Get-ChildItem -Path $srcPath -Recurse -Include "*.py" | 
        Select-String -Pattern $pattern -AllMatches
    
    if ($matches) {
        foreach ($match in $matches) {
            # Allow in comments if it's a clear reference to "removed" or "replaced"
            $line = $match.Line
            if ($line -match "#.*($pattern).*(removed|replaced|obsolete|deprecated|no longer)") {
                Write-Info "Allowed in comment: $($match.Path):$($match.LineNumber)"
                continue
            }
            
            Write-Fail "Found '$pattern' at $($match.Path):$($match.LineNumber)"
            Write-Info "   $($match.Line.Trim())"
            $foundIssues = $true
        }
    }
}

if (-not $foundIssues) {
    Write-Pass "No stats_all references in src/"
} else {
    Write-Fail "Found stats_all references that should be removed"
}

# ==============================================================================
# Check 2: /api/corpus_stats endpoint exists
# ==============================================================================

Write-CheckHeader "Check 2: /api/corpus_stats endpoint exists"

$corpusFile = "src\app\routes\corpus.py"
if (Test-Path $corpusFile) {
    $content = Get-Content $corpusFile -Raw
    
    if ($content -match '@(blueprint|corpus_bp)\.get\("/api/corpus_stats"\)') {
        Write-Pass "Endpoint @blueprint.get('/api/corpus_stats') exists"
        
        # Check if it handles missing file gracefully
        if ($content -match "if not.*exists|\.exists\(\).*404|return.*404|abort\(404\)") {
            Write-Pass "Endpoint handles missing corpus_stats.json (404)"
        } else {
            Write-Warn "Endpoint may not handle missing corpus_stats.json"
        }
    } else {
        Write-Fail "/api/corpus_stats endpoint not found in $corpusFile"
    }
} else {
    Write-Fail "$corpusFile not found"
}

# ==============================================================================
# Check 3: AUTH_DATABASE_URL has no SQLite fallback
# ==============================================================================

Write-CheckHeader "Check 3: AUTH_DATABASE_URL fail-fast (no SQLite fallback)"

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
# Check 4: corpus_stats.json existence (warning only)
# ==============================================================================

Write-CheckHeader "Check 4: corpus_stats.json availability"

$statsFile = "static\img\statistics\corpus_stats.json"
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
# Check 5: Stats databases (stats_files.db, stats_country.db)
# ==============================================================================

Write-CheckHeader "Check 5: Active stats databases"

$statsFiles = @{
    "stats_files.db" = "data\db\stats_files.db"
    "stats_country.db" = "data\db\stats_country.db"
}

foreach ($name in $statsFiles.Keys) {
    $path = $statsFiles[$name]
    if (Test-Path $path) {
        Write-Pass "$name exists"
    } else {
        Write-Warn "$name not found (run 03_build_metadata_stats.py)"
    }
}

# Check that stats_all.db is NOT present
$statsAllPath = "data\db\stats_all.db"
if (Test-Path $statsAllPath) {
    Write-Warn "stats_all.db still exists at $statsAllPath"
    Write-Info "This file is obsolete and can be deleted"
} else {
    Write-Pass "stats_all.db correctly absent"
}

# ==============================================================================
# Check 6: Obsolete endpoints removed
# ==============================================================================

Write-CheckHeader "Check 6: Obsolete endpoints removed"

$checks = @(
    @{
        File = "src\app\routes\atlas.py"
        Pattern = '/api/v1/atlas/overview'
        Name = "/api/v1/atlas/overview endpoint"
    },
    @{
        File = "src\app\routes\public.py"
        Pattern = 'get_stats_all_from_db'
        Name = "get_stats_all_from_db endpoint"
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
