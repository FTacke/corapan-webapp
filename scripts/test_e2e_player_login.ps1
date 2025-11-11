# E2E Test: Player unauth -> Sheet -> Login -> Player
# Tests the full authentication flow for protected player page

$baseUrl = "http://127.0.0.1:8000"
$testUrl = "$baseUrl/player?transcription=test&audio=test.mp3"

Write-Host "=== E2E TEST: Player Auth Flow ===" -ForegroundColor Cyan

# Step 1: Request player page without auth (HTMX)
Write-Host "`n[1] Request player page (HTMX, unauth)" -ForegroundColor Yellow
$resp1 = curl.exe -si -H "HX-Request: true" $testUrl 2>$null
$status1 = ($resp1 -split "`n" | Select-String "^HTTP/" | Select-Object -First 1).ToString()
$redirect1 = ($resp1 -split "`n" | Select-String "^HX-Redirect:" | Select-Object -First 1).ToString()

Write-Host "  Status: $status1"
Write-Host "  Redirect: $redirect1"

if ($status1 -match "204" -and $redirect1 -match "/auth/login_sheet") {
    Write-Host "  PASS: Player gating redirects to login sheet" -ForegroundColor Green
} else {
    Write-Host "  FAIL: Expected 204 + HX-Redirect to login_sheet" -ForegroundColor Red
    exit 1
}

# Step 2: Fetch the login sheet
Write-Host "`n[2] Fetch login sheet" -ForegroundColor Yellow
$sheetUrl = "$baseUrl/auth/login_sheet?next=/player?transcription=test%26audio=test.mp3"
$resp2 = curl.exe -s $sheetUrl 2>$null

if ($resp2 -match 'id="login-sheet"' -and $resp2 -match 'name="next"') {
    Write-Host "  PASS: Sheet contains form with next input" -ForegroundColor Green
} else {
    Write-Host "  FAIL: Sheet missing required elements" -ForegroundColor Red
    exit 1
}

# Step 3: POST login (HTMX)
Write-Host "`n[3] POST login with credentials (HTMX)" -ForegroundColor Yellow
$loginData = 'username=admin&password=admin&next=/player?transcription=test&audio=test.mp3'
$resp3 = curl.exe -si -X POST -H "HX-Request: true" -H "Content-Type: application/x-www-form-urlencoded" "$baseUrl/auth/login" -d $loginData 2>$null
$status3 = ($resp3 -split "`n" | Select-String "^HTTP/" | Select-Object -First 1).ToString()
$redirect3 = ($resp3 -split "`n" | Select-String "^HX-Redirect:" | Select-Object -First 1).ToString()
$cookies3 = ($resp3 -split "`n" | Select-String "^Set-Cookie:.*access_token_cookie" | Select-Object -First 1).ToString()

Write-Host "  Status: $status3"
Write-Host "  Redirect: $redirect3"
Write-Host "  Cookie: $(if ($cookies3) { 'SET' } else { 'MISSING' })"

if ($status3 -match "204" -and $redirect3 -match "/player" -and $cookies3) {
    Write-Host "  PASS: Login successful, redirects to intended player URL with JWT" -ForegroundColor Green
} else {
    Write-Host "  FAIL: Expected 204 + HX-Redirect to /player + Set-Cookie" -ForegroundColor Red
    exit 1
}

# Step 4: Access player with JWT cookie
Write-Host "`n[4] Access player with JWT cookie" -ForegroundColor Yellow
$cookieMatch = $resp3 -split "`n" | Select-String -Pattern "Set-Cookie: access_token_cookie=" | Select-Object -First 1
if ($cookieMatch) {
    $cookieStr = $cookieMatch.ToString()
    $cookieValue = ($cookieStr -replace '^Set-Cookie: access_token_cookie=', '' -split ';')[0]
    $resp4 = curl.exe -si -b "access_token_cookie=$cookieValue" "$testUrl" 2>$null
    $status4 = ($resp4 -split "`n" | Select-String "^HTTP/" | Select-Object -First 1).ToString()
    
    Write-Host "  Status: $status4"
    
    if ($status4 -match "200") {
        Write-Host "  PASS: Player accessible with JWT cookie" -ForegroundColor Green
    } else {
        Write-Host "  FAIL: Expected 200 OK for authenticated player request" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  SKIP: Could not extract cookie for step 4" -ForegroundColor Yellow
}

Write-Host "`n=== ALL TESTS PASSED ===" -ForegroundColor Green
exit 0
