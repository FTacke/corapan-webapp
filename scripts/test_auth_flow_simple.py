#!/usr/bin/env python3
"""
Test simplified auth flow - no progress page, dev-friendly rate limiting
"""
import requests
import sys
import time

BASE_URL = "http://127.0.0.1:8000"

def test_server():
    """Check if server is running"""
    print("[1] Checking server...", flush=True)
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=5)
        print("✓ Server is running")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Server not responding: {e}")
        return False

def test_login_flow():
    """Test login returns 303 (not polling page)"""
    print("\n[2] Testing login flow (admin/admin)...", flush=True)
    
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": "admin", "password": "admin"},
            allow_redirects=False,
            timeout=5
        )
        
        status = resp.status_code
        location = resp.headers.get('Location', 'N/A')
        cookies = resp.headers.get('Set-Cookie', '')
        
        if status == 303:
            print(f"✓ Got 303 redirect (not polling page)")
            print(f"  Location: {location}")
        else:
            print(f"✗ Got {status} instead of 303")
        
        if 'access_token_cookie' in cookies:
            print("✓ Set-Cookie headers present")
        else:
            print("✗ Missing Set-Cookie headers")
        
        # Check no progress page HTML
        if "Autenticando" not in resp.text and "spinner" not in resp.text:
            print("✓ No progress page HTML in response")
        else:
            print("✗ Found progress page HTML!")
    
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")

def test_rate_limit():
    """Test rate-limiting (6 rapid attempts - should NOT block in dev)"""
    print("\n[3] Testing rate-limit exemption in dev mode (6 rapid attempts)...", flush=True)
    
    blocked_count = 0
    for i in range(1, 7):
        try:
            resp = requests.post(
                f"{BASE_URL}/auth/login",
                data={"username": "admin", "password": "wrongpass"},
                allow_redirects=False,
                timeout=5
            )
            status = resp.status_code
            print(f"  Attempt {i}: {status}")
            
            if status == 429:
                blocked_count += 1
        except requests.exceptions.RequestException as e:
            print(f"  Attempt {i}: Error - {e}")
    
    if blocked_count == 0:
        print("✓ No 429 blocks in dev mode (rate-limit working correctly)")
    else:
        print(f"⚠ Got {blocked_count}x 429 blocks (rate-limit NOT exempted in dev)")

def test_css_files():
    """Test CSS asset files exist"""
    print("\n[4] Testing CSS asset files...", flush=True)
    
    files = ["progress.css", "chips.css"]
    for filename in files:
        try:
            resp = requests.get(
                f"{BASE_URL}/static/css/md3/components/{filename}",
                timeout=5
            )
            mime = resp.headers.get('Content-Type', 'unknown')
            status = resp.status_code
            
            if status == 200 and 'text/css' in mime:
                print(f"✓ {filename}: {status} {mime}")
            else:
                print(f"✗ {filename}: {status} {mime} (should be 200 text/css)")
        except requests.exceptions.RequestException as e:
            print(f"✗ {filename}: Error - {e}")

def test_ready_endpoint():
    """Test /auth/ready endpoint (should NOT exist)"""
    print("\n[5] Checking /auth/ready endpoint (should NOT exist)...", flush=True)
    
    try:
        resp = requests.get(
            f"{BASE_URL}/auth/ready?next=/",
            timeout=5,
            allow_redirects=False
        )
        
        if resp.status_code == 404:
            print("✓ /auth/ready correctly returns 404")
        else:
            print(f"✗ /auth/ready still exists (status {resp.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"⚠ /auth/ready check failed: {e}")

if __name__ == "__main__":
    print("=== Auth Flow Simplification Test ===\n")
    
    if not test_server():
        sys.exit(1)
    
    test_login_flow()
    test_rate_limit()
    test_css_files()
    test_ready_endpoint()
    
    print("\n=== Test Complete ===")
