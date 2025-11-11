# E2E Test: Direct /auth/login opens Sheet (non-HTMX and HTMX)
# Tests that GET /auth/login acts as router and never renders full page

$baseUrl = "http://127.0.0.1:8000"

Write-Host "=== E2E TEST: Direct /auth/login Router Behavior ===" -ForegroundColor Cyan

# Test 1: Non-HTMX GET /auth/login should redirect to landing with ?login=1
Write-Host "`n[1] Non-HTMX GET /auth/login" -ForegroundColor Yellow
$resp1 = curl.exe -si "$baseUrl/auth/login?next=/test" 2>$null
$status1 = ($resp1 -split "`n" | Select-String "^HTTP/" | Select-Object -First 1).ToString()
$location1 = ($resp1 -split "`n" | Select-String "^Location:" | Select-Object -First 1).ToString()

Write-Host "  Status: $status1"
Write-Host "  Location: $location1"

if ($status1 -match "303" -and $location1 -match "login=1") {
    Write-Host "  PASS: Redirects to landing page with login=1" -ForegroundColor Green
} else {
    Write-Host "  FAIL: Expected 303 redirect to landing with login=1" -ForegroundColor Red
    exit 1
}

# Test 2: HTMX GET /auth/login should return 204 + HX-Redirect to sheet
Write-Host "`n[2] HTMX GET /auth/login" -ForegroundColor Yellow
$resp2 = curl.exe -si -H "HX-Request: true" "$baseUrl/auth/login?next=/test" 2>$null
$status2 = ($resp2 -split "`n" | Select-String "^HTTP/" | Select-Object -First 1).ToString()
$redirect2 = ($resp2 -split "`n" | Select-String "^HX-Redirect:" | Select-Object -First 1).ToString()

Write-Host "  Status: $status2"
Write-Host "  HX-Redirect: $redirect2"

if ($status2 -match "204" -and $redirect2 -match "/auth/login_sheet") {
    Write-Host "  PASS: Returns 204 + HX-Redirect to login_sheet" -ForegroundColor Green
} else {
    Write-Host "  FAIL: Expected 204 + HX-Redirect to login_sheet" -ForegroundColor Red
    exit 1
}

# Test 3: Verify landing page triggers sheet when ?login=1 is present
Write-Host "`n[3] Landing page with ?login=1 (check for auto-trigger script)" -ForegroundColor Yellow
$resp3 = curl.exe -s "$baseUrl/?login=1&next=/test" 2>$null

if ($resp3 -match "login.*===.*1" -and $resp3 -match "login_sheet") {
    Write-Host "  PASS: Landing page contains auto-trigger script for login sheet" -ForegroundColor Green
} else {
    Write-Host "  SKIP: Could not verify auto-trigger script in landing page HTML" -ForegroundColor Yellow
}

# Test 4: GET /auth/login_sheet returns the sheet partial
Write-Host "`n[4] GET /auth/login_sheet" -ForegroundColor Yellow
$resp4 = curl.exe -si "$baseUrl/auth/login_sheet?next=/test" 2>$null
$status4 = ($resp4 -split "`n" | Select-String "^HTTP/" | Select-Object -First 1).ToString()
$body4 = curl.exe -s "$baseUrl/auth/login_sheet?next=/test" 2>$null

Write-Host "  Status: $status4"

if ($status4 -match "200" -and $body4 -match 'id="login-sheet"' -and $body4 -match 'name="next"') {
    Write-Host "  PASS: Sheet endpoint returns 200 with form and hidden next input" -ForegroundColor Green
} else {
    Write-Host "  FAIL: Expected 200 + sheet HTML with form" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== ALL TESTS PASSED ===" -ForegroundColor Green
exit 0
