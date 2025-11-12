#!/usr/bin/env python3
"""Browser Sanity Tests for Advanced Search V2 Stabilization."""

import subprocess
import time
import sys
import os
import json

# Start Flask + Mock BLS in background
print("=" * 70)
print("SANITY TEST SUITE: Advanced Search Stabilization V2")
print("=" * 70)

print("\n[1/6] Starting Mock BLS Server on port 8081...")
bls_proc = subprocess.Popen(
    [sys.executable, 'scripts/mock_bls_server.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
time.sleep(2)
print("✓ Mock BLS Server started")

print("\n[2/6] Starting Flask App on port 8000...")
env = os.environ.copy()
env['FLASK_APP'] = 'src.app'
env['FLASK_ENV'] = 'development'

flask_proc = subprocess.Popen(
    [sys.executable, '-m', 'flask', 'run', '--port', '8000'],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
time.sleep(3)
print("✓ Flask App started")

try:
    import requests
    
    print("\n[3/6] Testing Form Page Load (/search/advanced)...")
    r = requests.get('http://localhost:8000/search/advanced')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert 'id="advanced-search-form"' in r.text, "Form #advanced-search-form not found in HTML"
    print("✓ Form page loads correctly")
    print(f"  - Status: {r.status_code}")
    print(f"  - Form ID: advanced-search-form (found in HTML)")
    
    print("\n[4/6] Testing API Endpoint Response (/search/advanced/data)...")
    params = {
        'q': 'casa',
        'mode': 'forma',
        'draw': 1,
        'start': 0,
        'length': 50
    }
    r = requests.get('http://localhost:8000/search/advanced/data', params=params)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert 'draw' in data, "Missing 'draw' key"
    assert 'recordsTotal' in data, "Missing 'recordsTotal' key"
    assert 'recordsFiltered' in data, "Missing 'recordsFiltered' key"
    assert 'data' in data, "Missing 'data' key"
    print("✓ DataTables JSON schema correct")
    print(f"  - Status: {r.status_code}")
    print(f"  - Draw: {data['draw']}")
    print(f"  - Records Total: {data['recordsTotal']}")
    print(f"  - Records Filtered: {data['recordsFiltered']}")
    print(f"  - Data Array Length: {len(data['data'])}")
    
    # Check for error scenarios
    if 'error' in data:
        print(f"  - Error: {data.get('error')}")
        print(f"  - Message: {data.get('message')}")
    
    print("\n[5/6] Testing Error Handling (Invalid CQL)...")
    params = {
        'q': '[invalid cql}',
        'mode': 'cql',
        'draw': 1,
        'start': 0,
        'length': 50
    }
    r = requests.get('http://localhost:8000/search/advanced/data', params=params)
    assert r.status_code == 200, f"Expected 200, got {r.status_code} (should return 200 with error in JSON)"
    data = r.json()
    assert 'draw' in data, "Error response missing 'draw' key (DataTables needs this)"
    assert data.get('recordsTotal') == 0, "Error should return recordsTotal=0"
    print("✓ Error handling returns DataTables-compatible response")
    print(f"  - Status: {r.status_code} (not 500!)")
    print(f"  - Error: {data.get('error')}")
    print(f"  - Message: {data.get('message')}")
    
    print("\n[6/6] Testing Export Endpoint (/search/advanced/export)...")
    params = {
        'q': 'casa',
        'mode': 'forma',
        'format': 'csv'
    }
    r = requests.get('http://localhost:8000/search/advanced/export', params=params)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert 'text/csv' in r.headers.get('Content-Type', ''), "Expected text/csv content type"
    assert len(r.text) > 0, "Export returned empty response"
    lines = r.text.strip().split('\n')
    assert len(lines) > 1, "Export should have header + data"
    print("✓ Export endpoint works")
    print(f"  - Status: {r.status_code}")
    print(f"  - Content-Type: {r.headers.get('Content-Type')}")
    print(f"  - Lines: {len(lines)}")
    
    print("\n" + "=" * 70)
    print("✓ ALL SANITY CHECKS PASSED")
    print("=" * 70)
    print("\nSummary:")
    print("  1. ✓ Form loads without errors")
    print("  2. ✓ Form element #advanced-search-form exists")
    print("  3. ✓ API returns HTTP 200 (not 500)")
    print("  4. ✓ DataTables JSON schema correct")
    print("  5. ✓ Error handling returns 200 with proper JSON")
    print("  6. ✓ Export endpoint works")
    print("\nStatus: READY FOR PRODUCTION ✓")
    
except AssertionError as e:
    print(f"\n✗ ASSERTION FAILED: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    print("\n[Cleanup] Stopping servers...")
    bls_proc.terminate()
    flask_proc.terminate()
    try:
        bls_proc.wait(timeout=2)
        flask_proc.wait(timeout=2)
    except:
        bls_proc.kill()
        flask_proc.kill()
    print("✓ Servers stopped")
