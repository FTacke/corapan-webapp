#!/usr/bin/env pwsh

Write-Host "`n=== CO.RA.PAN - Only-Sheet Login Tests ===" -ForegroundColor Cyan
Write-Host "Testing consolidated login-sheet flow with intended redirect..." -ForegroundColor Gray

$baseUrl = "http://127.0.0.1:8000"
$allPassed = $true

# Test 1: Direkter Aufruf /auth/login
Write-Host "`n[TEST 1] Direkter Aufruf /auth/login" -ForegroundColor Yellow
$response = curl.exe -s -i "http://127.0.0.1:8000/auth/login?next=/player?transcription=test%26audio=test.mp3"
if ($response -match "HTTP/1.1 303" -and $response -match "Location:.*login=1.*next=") {
    Write-Host "✓ PASSED: 303 to /?login=1&next=..." -ForegroundColor Green
} else {
    Write-Host "✗ FAILED: Should redirect to landing page with login=1 flag" -ForegroundColor Red
    $allPassed = $false
}

# Test 2: Navbar/Drawer Login Sheet (hx-get)
Write-Host "`n[TEST 2] Navbar/Drawer Login → Sheet (hx-get)" -ForegroundColor Yellow
$response = curl.exe -s -i "http://127.0.0.1:8000/auth/login_sheet?next=/corpus"
if ($response -match "HTTP/1.1 200" -and $response -match "login-sheet" -and $response -match 'type="hidden".*name="next"') {
    Write-Host "✓ PASSED: Sheet returned with hidden next input" -ForegroundColor Green
} else {
    Write-Host "✗ FAILED: Sheet not working properly" -ForegroundColor Red
    $allPassed = $false
}

# Test 3: Atlas-Player HTMX-Gating
Write-Host "`n[TEST 3] Atlas-Player HTMX-Gating → login_sheet" -ForegroundColor Yellow
$response = curl.exe -s -i -H "HX-Request: true" "http://127.0.0.1:8000/player?transcription=test&audio=test.mp3"
if ($response -match "HTTP/1.1 204" -and $response -match "HX-Redirect:.*login_sheet") {
    Write-Host "✓ PASSED: 204 with HX-Redirect to login_sheet" -ForegroundColor Green
} else {
    Write-Host "✗ FAILED: Player gating not working" -ForegroundColor Red
    $allPassed = $false
}

# Test 4: Login via Sheet mit next → intended target
Write-Host "`n[TEST 4] Login via Sheet mit intended redirect" -ForegroundColor Yellow
$postData = 'username=admin&password=admin&next=/player?transcription=test%26audio=test.mp3'
$response = curl.exe -s -i -H "HX-Request: true" -X POST "http://127.0.0.1:8000/auth/login" -d $postData -H "Content-Type: application/x-www-form-urlencoded"
if ($response -match "HTTP/1.1 204" -and $response -match "HX-Redirect: /player" -and $response -match "Set-Cookie.*access_token") {
    Write-Host "✓ PASSED: 204 with HX-Redirect to intended URL + cookies" -ForegroundColor Green
} else {
    Write-Host "✗ FAILED: Login redirect not working" -ForegroundColor Red
    $allPassed = $false
}

# Test 5: Full-Page Fallback (Inicio mit login=1 triggert Sheet)
Write-Host "`n[TEST 5] Full-Page Fallback: ?login=1 triggert Sheet" -ForegroundColor Yellow
$response = curl.exe -s "http://127.0.0.1:8000/?login=1&next=/test"
if ($response -match "Auto-trigger login sheet" -or $response -match "get.*login_sheet") {
    Write-Host "✓ PASSED: Inicio page loads with Sheet-trigger script" -ForegroundColor Green
} else {
    Write-Host "✗ FAILED: Full-page fallback script not present" -ForegroundColor Red
    $allPassed = $false
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "✓ ALL TESTS PASSED - Only-Sheet Login fully operational" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ SOME TESTS FAILED" -ForegroundColor Red
    exit 1
}
