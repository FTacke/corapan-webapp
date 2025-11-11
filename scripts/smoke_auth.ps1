# CO.RA.PAN Auth & Navigation Smoke Tests
# ========================================
# Tests Logout GET/POST, Public Routes, and Advanced↔Simple Navigation
# Run: .\scripts\smoke_auth.ps1

param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

Write-Host "`n=== CO.RA.PAN Auth Smoke Tests ===" -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl`n" -ForegroundColor Gray

$passed = 0
$failed = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [int[]]$ExpectedStatus = @(200),
        [string]$ExpectedHeader = $null,
        [string]$ExpectedContent = $null
    )
    
    Write-Host "[TEST] $Name" -ForegroundColor Yellow
    Write-Host "  URL: $Method $Url" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            MaximumRedirection = 0
            ErrorAction = "SilentlyContinue"
            UseBasicParsing = $true
        }
        
        $response = Invoke-WebRequest @params
        $status = $response.StatusCode
        
        # Check status
        if ($ExpectedStatus -contains $status) {
            Write-Host "  ✓ Status: $status" -ForegroundColor Green
            $script:passed++
        } else {
            Write-Host "  ✗ Status: $status (expected: $($ExpectedStatus -join ' or '))" -ForegroundColor Red
            $script:failed++
            return
        }
        
        # Check header
        if ($ExpectedHeader) {
            $headerParts = $ExpectedHeader -split ":", 2
            $headerName = $headerParts[0].Trim()
            $headerValue = $headerParts[1].Trim()
            
            $actualValue = $response.Headers[$headerName]
            if ($actualValue -like "*$headerValue*") {
                Write-Host "  ✓ Header: $headerName contains '$headerValue'" -ForegroundColor Green
                $script:passed++
            } else {
                Write-Host "  ✗ Header: $headerName = '$actualValue' (expected: *$headerValue*)" -ForegroundColor Red
                $script:failed++
            }
        }
        
        # Check content
        if ($ExpectedContent) {
            if ($response.Content -match $ExpectedContent) {
                Write-Host "  ✓ Content contains: $ExpectedContent" -ForegroundColor Green
                $script:passed++
            } else {
                Write-Host "  ✗ Content does not contain: $ExpectedContent" -ForegroundColor Red
                $script:failed++
            }
        }
        
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        
        if ($ExpectedStatus -contains $status) {
            Write-Host "  ✓ Status: $status" -ForegroundColor Green
            $script:passed++
            
            # Check redirect location if expected
            if ($ExpectedHeader -and $ExpectedHeader -like "Location:*") {
                $location = $_.Exception.Response.Headers["Location"]
                $expectedLoc = ($ExpectedHeader -split ":", 2)[1].Trim()
                
                if ($location -like "*$expectedLoc*") {
                    Write-Host "  ✓ Location: $location" -ForegroundColor Green
                    $script:passed++
                } else {
                    Write-Host "  ✗ Location: $location (expected: *$expectedLoc*)" -ForegroundColor Red
                    $script:failed++
                }
            }
            
            # Check Set-Cookie header
            $setCookie = $_.Exception.Response.Headers["Set-Cookie"]
            if ($setCookie) {
                if ($setCookie -match "Max-Age=0" -or $setCookie -match "Expires=") {
                    Write-Host "  ✓ Set-Cookie: Contains Max-Age=0 or Expires (logout)" -ForegroundColor Green
                    $script:passed++
                }
            }
        } else {
            Write-Host "  ✗ Status: $status (expected: $($ExpectedStatus -join ' or '))" -ForegroundColor Red
            Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
            $script:failed++
        }
    }
    
    Write-Host ""
}

# =====================================
# Test 1: GET /auth/logout
# =====================================
Test-Endpoint `
    -Name "GET /auth/logout (should redirect and clear cookies)" `
    -Url "$BaseUrl/auth/logout" `
    -Method "GET" `
    -ExpectedStatus @(302, 303) `
    -ExpectedHeader "Location: /"

# =====================================
# Test 2: POST /auth/logout
# =====================================
Test-Endpoint `
    -Name "POST /auth/logout (should redirect and clear cookies)" `
    -Url "$BaseUrl/auth/logout" `
    -Method "POST" `
    -ExpectedStatus @(302, 303) `
    -ExpectedHeader "Location: /"

# =====================================
# Test 3: /corpus (public, no auth)
# =====================================
Test-Endpoint `
    -Name "GET /corpus (public access)" `
    -Url "$BaseUrl/corpus" `
    -Method "GET" `
    -ExpectedStatus @(200) `
    -ExpectedContent "Búsqueda simple"

# =====================================
# Test 4: /search/advanced (public)
# =====================================
Test-Endpoint `
    -Name "GET /search/advanced (public access)" `
    -Url "$BaseUrl/search/advanced" `
    -Method "GET" `
    -ExpectedStatus @(200) `
    -ExpectedContent "Búsqueda avanzada"

# =====================================
# Test 5: Advanced → Simple Link
# =====================================
Write-Host "[TEST] Advanced → Simple navigation link" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/search/advanced" -UseBasicParsing
    
    # Check for correct link to /corpus (not /corpus/search?active_tab=...)
    if ($response.Content -match 'href="[^"]*\/corpus"' -or 
        $response.Content -match 'href="[^"]*\/corpus#tab-simple"') {
        Write-Host "  ✓ Contains link to /corpus or /corpus#tab-simple" -ForegroundColor Green
        $script:passed++
    } else {
        Write-Host "  ✗ Does not contain correct link to /corpus" -ForegroundColor Red
        $script:failed++
    }
    
    # Check that it does NOT use the old pattern
    if ($response.Content -notmatch 'corpus\.search\?active_tab=') {
        Write-Host "  ✓ Does NOT use old pattern corpus.search?active_tab=" -ForegroundColor Green
        $script:passed++
    } else {
        Write-Host "  ✗ Still uses old pattern corpus.search?active_tab=" -ForegroundColor Red
        $script:failed++
    }
} catch {
    Write-Host "  ✗ Failed to fetch /search/advanced" -ForegroundColor Red
    $script:failed++
}
Write-Host ""

# =====================================
# Test 6: Build ID in Footer
# =====================================
Write-Host "[TEST] Build ID present in footer" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/" -UseBasicParsing
    
    if ($response.Content -match '<!-- BUILD (\d{14}|dev) -->') {
        $buildId = $matches[1]
        Write-Host "  ✓ Build ID found: $buildId" -ForegroundColor Green
        $script:passed++
    } else {
        Write-Host "  ✗ Build ID not found in HTML" -ForegroundColor Red
        $script:failed++
    }
} catch {
    Write-Host "  ✗ Failed to fetch /" -ForegroundColor Red
    $script:failed++
}
Write-Host ""

# =====================================
# Summary
# =====================================
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red

if ($failed -eq 0) {
    Write-Host "`n✓ All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n✗ Some tests failed. Check output above." -ForegroundColor Red
    exit 1
}
