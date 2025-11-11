#!/usr/bin/env pwsh
<#
.SYNOPSIS
Test simplified auth flow - no progress page, dev-friendly rate limiting
.DESCRIPTION
- Login should 303 redirect directly (not polling page)
- Rate-limit should NOT block in dev mode (6+ attempts)
- CSS assets should exist and be valid
#>

$ErrorActionPreference = "Continue"
$BaseUrl = "http://127.0.0.1:8000"

Write-Host "=== Auth Flow Simplification Test ===" -ForegroundColor Green
Write-Host ""

# Test 1: Check if server is running
Write-Host "[1] Checking server..." -ForegroundColor Yellow
try {
    $ping = Invoke-WebRequest -Uri "$BaseUrl/" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Server is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Server not responding!" -ForegroundColor Red
    exit 1
}

# Test 2: Login flow (should get 303, not polling page)
Write-Host ""
Write-Host "[2] Testing login flow (admin/admin)..." -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "$BaseUrl/auth/login" `
    -Method POST `
    -Body "username=admin&password=admin" `
    -ContentType "application/x-www-form-urlencoded" `
    -MaximumRedirection 0 `
    -ErrorAction SilentlyContinue `
    -TimeoutSec 5

$status = $response.StatusCode
$location = $response.Headers['Location']
$cookies = $response.Headers['Set-Cookie']

if ($status -eq 303) {
    Write-Host "✓ Got 303 redirect (not polling page)" -ForegroundColor Green
    Write-Host "  Location: $location"
} else {
    Write-Host "✗ Got $status instead of 303" -ForegroundColor Red
}

if ($cookies -and $cookies -match "access_token_cookie") {
    Write-Host "✓ Set-Cookie headers present" -ForegroundColor Green
} else {
    Write-Host "✗ Missing Set-Cookie headers" -ForegroundColor Red
}

# Test 3: Check for progress page in response
if ($null -eq $response.Content -or -not ($response.Content -like "*Autenticando*")) {
    Write-Host "✓ No progress page HTML in response" -ForegroundColor Green
} else {
    Write-Host "✗ Found progress page HTML!" -ForegroundColor Red
}

# Test 4: Rate limiting (6 rapid attempts - should NOT block in dev)
Write-Host ""
Write-Host "[3] Testing rate-limit exemption in dev mode (6 rapid attempts)..." -ForegroundColor Yellow
$blocked_count = 0

for ($i = 1; $i -le 6; $i++) {
    $response = Invoke-WebRequest -Uri "$BaseUrl/auth/login" `
        -Method POST `
        -Body "username=admin&password=wrongpass" `
        -ContentType "application/x-www-form-urlencoded" `
        -MaximumRedirection 0 `
        -ErrorAction SilentlyContinue `
        -TimeoutSec 5
    
    $status = $response.StatusCode
    Write-Host "  Attempt $i: $status"
    
    if ($status -eq 429) {
        $blocked_count++
    }
}

if ($blocked_count -eq 0) {
    Write-Host "✓ No 429 blocks in dev mode (rate-limit working correctly)" -ForegroundColor Green
} else {
    Write-Host "⚠ Got $blocked_count x 429 blocks (rate-limit NOT exempted in dev)" -ForegroundColor Yellow
}

# Test 5: CSS files exist
Write-Host ""
Write-Host "[4] Testing CSS asset files..." -ForegroundColor Yellow
@("progress.css", "chips.css") | ForEach-Object {
    try {
        $css_response = Invoke-WebRequest `
            -Uri "$BaseUrl/static/css/md3/components/$_" `
            -TimeoutSec 5 `
            -ErrorAction Stop
        
        $mime = $css_response.Headers['Content-Type']
        $status = $css_response.StatusCode
        
        if ($status -eq 200 -and $mime -match "text/css") {
            Write-Host "✓ $_`: $status $mime" -ForegroundColor Green
        } else {
            Write-Host "✗ $_`: $status $mime (should be 200 text/css)" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ $_`: 404 or error" -ForegroundColor Red
    }
}

# Test 6: No /auth/ready endpoint
Write-Host ""
Write-Host "[5] Checking /auth/ready endpoint (should NOT exist)..." -ForegroundColor Yellow
try {
    $ready_response = Invoke-WebRequest `
        -Uri "$BaseUrl/auth/ready?next=/" `
        -TimeoutSec 5 `
        -ErrorAction Stop
    
    if ($ready_response.StatusCode -eq 404) {
        Write-Host "✓ /auth/ready correctly returns 404" -ForegroundColor Green
    } else {
        Write-Host "✗ /auth/ready still exists (status $($ready_response.StatusCode))" -ForegroundColor Red
    }
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "✓ /auth/ready correctly returns 404" -ForegroundColor Green
    } else {
        Write-Host "? /auth/ready check inconclusive" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Green
