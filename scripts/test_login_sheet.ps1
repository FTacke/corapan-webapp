# Login Sheet Integration Tests
# Tests für Login-Sheet-Funktionalität und intended redirect

Write-Host "`n=== CO.RA.PAN Login Sheet Tests ===" -ForegroundColor Cyan
Write-Host "Testing login sheet functionality and intended redirect..." -ForegroundColor Gray

$baseUrl = "http://127.0.0.1:8000"
$allPassed = $true

# Test 1: Sheet-Endpoint verfügbar
Write-Host "`n[TEST 1] Sheet-Endpoint verfügbar" -ForegroundColor Yellow
$response = curl.exe -s -i "$baseUrl/auth/login_sheet"
if ($response -match "HTTP/1.1 200" -and $response -match "login-sheet" -and $response -match "login-form") {
    Write-Host "✓ PASSED: Sheet endpoint returns 200 with form" -ForegroundColor Green
} else {
    Write-Host "✗ FAILED: Sheet endpoint not working" -ForegroundColor Red
    $allPassed = $false
}

# Test 1b: Hidden next-Input vorhanden
Write-Host "`n[TEST 1b] Hidden next-Input im Sheet" -ForegroundColor Yellow
$response = curl.exe -s "$baseUrl/auth/login_sheet?next=/player"
if ($response -match 'type="hidden".*name="next".*value="/player"') {
    Write-Host "✓ PASSED: Hidden next input present with correct value" -ForegroundColor Green
} else {
    Write-Host "✗ FAILED: Hidden next input missing or incorrect" -ForegroundColor Red
    $allPassed = $false
}

# Test 3: Atlas-Player HTMX-Gating
Write-Host "`n[TEST 3] Atlas-Player HTMX-Gating" -ForegroundColor Yellow
$response = curl.exe -s -i -H "HX-Request: true" "$baseUrl/player?transcription=test&audio=test.mp3"
if ($response -match "HTTP/1.1 204" -and $response -match "HX-Redirect:.*login_sheet.*next=") {
    Write-Host "✓ PASSED: HTMX request redirected to login_sheet with next" -ForegroundColor Green
} else {
    Write-Host "✗ FAILED: HTMX gating not working" -ForegroundColor Red
    $allPassed = $false
}

# Test 4: Login via Sheet → intended redirect
Write-Host "`n[TEST 4] Login mit intended redirect" -ForegroundColor Yellow
$postData = 'username=admin&password=admin&next=/player?transcription=test%26audio=test.mp3'
$response = curl.exe -s -i -H "HX-Request: true" -X POST "$baseUrl/auth/login" -d $postData -H "Content-Type: application/x-www-form-urlencoded"
$checkPattern = "HX-Redirect: /player"
if ($response -match "HTTP/1.1 204" -and $response -match $checkPattern -and $response -match "Set-Cookie:.*access_token") {
    Write-Host "✓ PASSED: Login redirects to intended URL with cookies" -ForegroundColor Green
} else {
    Write-Host "✗ FAILED: Login redirect or cookies not working" -ForegroundColor Red
    $allPassed = $false
}

# Test 5: Full-Page Fallback
Write-Host "`n[TEST 5] Full-Page Fallback (ohne HTMX)" -ForegroundColor Yellow
$response = curl.exe -s -i "$baseUrl/player?transcription=test&audio=test.mp3"
if ($response -match "HTTP/1.1 303" -and $response -match "Location:.*auth/login\?next=") {
    Write-Host "✓ PASSED: Full-page request redirects to login with next" -ForegroundColor Green
} else {
    Write-Host "✗ FAILED: Full-page fallback not working" -ForegroundColor Red
    $allPassed = $false
}

# Test 6a: Security - External Domain
Write-Host "`n[TEST 6a] Security: External Domain abgelehnt" -ForegroundColor Yellow
$postData = 'username=admin&password=admin&next=https://evil.tld/'
$response = curl.exe -s -i -X POST "$baseUrl/auth/login" -d $postData -H "Content-Type: application/x-www-form-urlencoded"
if ($response -match "HTTP/1.1 303" -and $response -match "Location: /`$") {
    Write-Host "✓ PASSED: External domain rejected, redirected to Inicio" -ForegroundColor Green
} else {
    Write-Host "✗ FAILED: Open redirect vulnerability!" -ForegroundColor Red
    $allPassed = $false
}

# Test 6b: Security - Auth URLs
Write-Host "`n[TEST 6b] Security: Auth-URLs abgelehnt (Loop-Prävention)" -ForegroundColor Yellow
$postData = 'username=admin&password=admin&next=/auth/login'
$response = curl.exe -s -i -X POST "$baseUrl/auth/login" -d $postData -H "Content-Type: application/x-www-form-urlencoded"
if ($response -match "HTTP/1.1 303" -and $response -match "Location: /`$") {
    Write-Host "✓ PASSED: Auth URL rejected, redirected to Inicio" -ForegroundColor Green
} else {
    Write-Host "✗ FAILED: Auth URL loop not prevented!" -ForegroundColor Red
    $allPassed = $false
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "✓ ALL TESTS PASSED" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ SOME TESTS FAILED" -ForegroundColor Red
    exit 1
}
