# CO.RA.PAN Auth Smoke Tests
# ===========================
# Quick validation of auth fixes (GET logout, public routes, tab navigation)

$BASE_URL = "http://localhost:8000"
$PASSED = 0
$FAILED = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200,
        [string]$Method = "GET",
        [hashtable]$Headers = @{},
        [string]$ExpectHeader = $null,
        [string]$ExpectHeaderValue = $null
    )
    
    Write-Host "`n[TEST] $Name" -ForegroundColor Cyan
    Write-Host "       $Method $Url" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            MaximumRedirection = 0
            ErrorAction = "Stop"
            UseBasicParsing = $true
        }
        
        try {
            $response = Invoke-WebRequest @params
            $status = $response.StatusCode
        } catch {
            # PowerShell throws on 3xx redirects with MaximumRedirection=0
            if ($_.Exception.Response) {
                $status = [int]$_.Exception.Response.StatusCode
                $response = $_.Exception.Response
            } else {
                throw
            }
        }
        
        if ($status -eq $ExpectedStatus) {
            Write-Host "   ✅ Status: $status (expected $ExpectedStatus)" -ForegroundColor Green
            
            # Check for expected header
            if ($ExpectHeader -and $response.Headers) {
                $headerValue = $response.Headers[$ExpectHeader]
                if ($headerValue -like "*$ExpectHeaderValue*") {
                    Write-Host "   ✅ Header: $ExpectHeader contains '$ExpectHeaderValue'" -ForegroundColor Green
                } else {
                    Write-Host "   ❌ Header: $ExpectHeader = '$headerValue' (expected '$ExpectHeaderValue')" -ForegroundColor Red
                    $script:FAILED++
                    return
                }
            }
            
            $script:PASSED++
        } else {
            Write-Host "   ❌ Status: $status (expected $ExpectedStatus)" -ForegroundColor Red
            $script:FAILED++
        }
    } catch {
        Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:FAILED++
    }
}

Write-Host "`n╔════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║      CO.RA.PAN Auth Smoke Tests (2025-11-11)         ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Magenta

# ============================================================================
# TEST SUITE 1: Public Routes (No Auth Required)
# ============================================================================
Write-Host "`n📂 PUBLIC ROUTES" -ForegroundColor Yellow

Test-Endpoint `
    -Name "Corpus Home (Public)" `
    -Url "$BASE_URL/corpus/" `
    -ExpectedStatus 200

Test-Endpoint `
    -Name "Advanced Search (Public)" `
    -Url "$BASE_URL/search/advanced" `
    -ExpectedStatus 200

Test-Endpoint `
    -Name "Atlas API (Public)" `
    -Url "$BASE_URL/api/v1/atlas/countries" `
    -ExpectedStatus 200

Test-Endpoint `
    -Name "BLS Proxy Health (Public)" `
    -Url "$BASE_URL/bls/" `
    -ExpectedStatus 200

# ============================================================================
# TEST SUITE 2: Logout (GET Method, No CSRF)
# ============================================================================
Write-Host "`n🚪 LOGOUT ENDPOINTS" -ForegroundColor Yellow

Test-Endpoint `
    -Name "Logout via GET (No Auth Required)" `
    -Url "$BASE_URL/auth/logout" `
    -ExpectedStatus 303 `
    -ExpectHeader "Set-Cookie" `
    -ExpectHeaderValue "Max-Age=0"

Test-Endpoint `
    -Name "Logout POST (Should Still Work)" `
    -Url "$BASE_URL/auth/logout" `
    -Method "POST" `
    -ExpectedStatus 303 `
    -ExpectHeader "Set-Cookie" `
    -ExpectHeaderValue "Max-Age=0"

# ============================================================================
# TEST SUITE 3: Protected Routes (Should Redirect/401 Without Auth)
# ============================================================================
Write-Host "`n🔒 PROTECTED ROUTES" -ForegroundColor Yellow

Test-Endpoint `
    -Name "Admin Dashboard (Protected)" `
    -Url "$BASE_URL/admin/" `
    -ExpectedStatus 302

Test-Endpoint `
    -Name "Player (Protected)" `
    -Url "$BASE_URL/player/" `
    -ExpectedStatus 302

Test-Endpoint `
    -Name "Editor (Protected)" `
    -Url "$BASE_URL/editor/" `
    -ExpectedStatus 302

# ============================================================================
# TEST SUITE 4: Tab Navigation (No 500 Errors)
# ============================================================================
Write-Host "`n🔀 TAB NAVIGATION" -ForegroundColor Yellow

Test-Endpoint `
    -Name "Corpus Home (Default Tab)" `
    -Url "$BASE_URL/corpus/" `
    -ExpectedStatus 200

Test-Endpoint `
    -Name "Corpus Token Tab (Fragment)" `
    -Url "$BASE_URL/corpus/#tab-token" `
    -ExpectedStatus 200

Test-Endpoint `
    -Name "Advanced → Simple (Should Not 500)" `
    -Url "$BASE_URL/corpus/" `
    -ExpectedStatus 200

# ============================================================================
# RESULTS SUMMARY
# ============================================================================
Write-Host "`n╔════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║                    TEST RESULTS                        ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host "`n   ✅ Passed: $PASSED" -ForegroundColor Green
Write-Host "   ❌ Failed: $FAILED" -ForegroundColor $(if ($FAILED -gt 0) { "Red" } else { "Gray" })

if ($FAILED -eq 0) {
    Write-Host "`n🎉 All tests passed! Auth system is healthy." -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n⚠️  Some tests failed. Check errors above." -ForegroundColor Yellow
    exit 1
}
