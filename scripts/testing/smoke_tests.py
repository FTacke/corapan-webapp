#!/usr/bin/env python3
"""
Execute BlackLab Stage 2-3 smoke tests and capture results.
"""
import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path

def run_curl(name, url, expected_status=200):
    """Execute curl command and capture response."""
    print(f"\n[{name}]")
    print(f"  URL: {url}")
    
    try:
        result = subprocess.run(
            ["curl", "-s", "-w", "\n%{http_code}", url],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        lines = result.stdout.strip().split('\n')
        status_code = int(lines[-1]) if lines[-1].isdigit() else 0
        body = '\n'.join(lines[:-1])
        
        # Extract first 200 chars
        body_preview = body[:200] if body else "(empty)"
        
        print(f"  Status: {status_code} {'OK' if status_code == expected_status else 'FAIL'}")
        print(f"  Body (first 200 chars):")
        print(f"    {repr(body_preview)}")
        
        return {
            "name": name,
            "url": url,
            "status": status_code,
            "body": body,
            "body_preview": body_preview,
            "success": status_code == expected_status
        }
        
    except Exception as e:
        print(f"  FAIL Error: {e}")
        return {
            "name": name,
            "url": url,
            "status": 0,
            "body": str(e),
            "body_preview": str(e),
            "success": False
        }

def main():
    print("=" * 70)
    print("BlackLab Smoke Tests - Stage 2-3 Verification")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = []
    
    # Test 1: BLS Root endpoint
    results.append(run_curl(
        "Test 1: BLS Server Info",
        "http://localhost:8081/blacklab-server/",
        expected_status=200
    ))
    
    # Test 2: Proxy root
    results.append(run_curl(
        "Test 2: Flask Proxy /bls/",
        "http://localhost:8000/bls/",
        expected_status=200
    ))
    
    # Test 3: Proxy corpus search
    results.append(run_curl(
        "Test 3: Flask Proxy CQL Search",
        "http://localhost:8000/bls/corpus/corapan/1/hits?cql_query=[lemma=%22ser%22]",
        expected_status=200
    ))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    for r in results:
        status_icon = "OK" if r["success"] else "FAIL"
        print(f"{status_icon} {r['name']}: HTTP {r['status']}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[OK] ALL TESTS PASSED - Ready for UI Implementation")
        return 0
    else:
        print(f"\n[FAIL] {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
