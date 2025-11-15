<#
.SYNOPSIS
    Test docmeta.jsonl integration into BlackLab index.

.DESCRIPTION
    This script verifies that document metadata from docmeta.jsonl is correctly
    imported into the BlackLab index and accessible via the API.

.EXAMPLE
    .\test_docmeta_integration.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "DocMeta Integration Test" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$BLS_URL = "http://localhost:8081/blacklab-server"
$CORPUS = "corapan"

# ============================================================================
# Test 1: Check BlackLab is running
# ============================================================================

Write-Host "[1/4] Checking BlackLab Server..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "$BLS_URL" -UseBasicParsing -TimeoutSec 5
    Write-Host "  ✓ BlackLab Server is running" -ForegroundColor Green
} catch {
    Write-Host "  ✗ BlackLab Server not reachable: $_" -ForegroundColor Red
    Write-Host "    Start with: .\scripts\start_blacklab_docker_v3.ps1 -Detach" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# ============================================================================
# Test 2: Check corpus metadata schema
# ============================================================================

Write-Host "[2/4] Checking corpus metadata schema..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$BLS_URL/corpora/$CORPUS" -Method Get
    
    # Check for expected metadata fields
    $metadataFields = $response.metadataFields
    $expectedFields = @("file_id", "country_code", "date", "radio", "city", "audio_path")
    
    Write-Host "  Available metadata fields:" -ForegroundColor Gray
    foreach ($field in $metadataFields.PSObject.Properties) {
        Write-Host "    - $($field.Name): $($field.Value.type)" -ForegroundColor DarkGray
    }
    
    $missingFields = $expectedFields | Where-Object { -not $metadataFields.$_ }
    if ($missingFields) {
        Write-Host "  ✗ Missing metadata fields: $($missingFields -join ', ')" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  ✓ All expected metadata fields present" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to get corpus schema: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# Test 3: Check document metadata is populated
# ============================================================================

Write-Host "[3/4] Checking document metadata population..." -ForegroundColor Yellow

try {
    # Get list of documents
    $response = Invoke-RestMethod -Uri "$BLS_URL/$CORPUS/docs" -Method Get
    
    $totalDocs = $response.summary.numberOfDocs
    Write-Host "  Total documents: $totalDocs" -ForegroundColor Gray
    
    if ($totalDocs -eq 0) {
        Write-Host "  ✗ No documents in index!" -ForegroundColor Red
        exit 1
    }
    
    # Get first document details
    $firstDocPid = $response.docs[0].docPid
    $docResponse = Invoke-RestMethod -Uri "$BLS_URL/$CORPUS/docs/$firstDocPid" -Method Get
    
    $metadata = $docResponse.docInfo.metadata
    
    Write-Host "  Sample document: $firstDocPid" -ForegroundColor Gray
    Write-Host "    file_id: $($metadata.file_id)" -ForegroundColor DarkGray
    Write-Host "    country_code: $($metadata.country_code)" -ForegroundColor DarkGray
    Write-Host "    radio: $($metadata.radio)" -ForegroundColor DarkGray
    Write-Host "    city: $($metadata.city)" -ForegroundColor DarkGray
    Write-Host "    date: $($metadata.date)" -ForegroundColor DarkGray
    
    # Check if metadata is actually populated (not empty)
    if ([string]::IsNullOrEmpty($metadata.country_code) -or 
        [string]::IsNullOrEmpty($metadata.radio) -or 
        [string]::IsNullOrEmpty($metadata.date)) {
        Write-Host "  ✗ Metadata fields are empty!" -ForegroundColor Red
        Write-Host "    Possible causes:" -ForegroundColor Yellow
        Write-Host "    - docmeta.jsonl was not imported during index build" -ForegroundColor Gray
        Write-Host "    - file_id in docmeta.jsonl doesn't match document IDs" -ForegroundColor Gray
        Write-Host "    - blacklab-server.yaml metadata config is incorrect" -ForegroundColor Gray
        exit 1
    }
    
    Write-Host "  ✓ Metadata is populated" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to check documents: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# Test 4: Test metadata filter
# ============================================================================

Write-Host "[4/4] Testing metadata filter..." -ForegroundColor Yellow

try {
    # Try to search with a country filter
    $country = "VEN"
    $filter = "country_code:$country"
    $response = Invoke-RestMethod -Uri "$BLS_URL/$CORPUS/hits?patt=%5Blemma%3D%22casa%22%5D&filter=$filter&number=1" -Method Get
    
    $hits = $response.summary.numberOfHits
    Write-Host "  Search: [lemma=`"casa`"] with country_code:$country" -ForegroundColor Gray
    Write-Host "  Results: $hits hits" -ForegroundColor Gray
    
    if ($hits -eq 0) {
        Write-Host "  ✗ Filter returned 0 hits (expected > 0)" -ForegroundColor Red
        Write-Host "    This suggests metadata filtering is not working correctly" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "  ✓ Metadata filter works" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to test filter: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "All Tests Passed!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Run Python integration tests:" -ForegroundColor Gray
Write-Host "     python test_advanced_api_quick.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Test via Advanced API:" -ForegroundColor Gray
Write-Host "     http://localhost:8000/search/advanced/data?q=casa&mode=lemma&country_code=VEN&length=3" -ForegroundColor Gray
Write-Host ""

exit 0
