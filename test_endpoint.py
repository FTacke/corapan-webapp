#!/usr/bin/env python3
"""Test the advanced search endpoint."""

import subprocess
import sys
import time
import os

# Start Flask app
env = os.environ.copy()
env['FLASK_APP'] = 'src.app'
env['FLASK_ENV'] = 'development'

# Start the Flask server in a subprocess
proc = subprocess.Popen(
    [sys.executable, '-m', 'flask', 'run', '--port', '8000'],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for server to start
time.sleep(3)

try:
    # Now test the endpoint
    import requests
    
    url = 'http://localhost:8000/search/advanced/data'
    params = {
        'q': 'casa',
        'mode': 'forma',
        'draw': 1,
        'start': 0,
        'length': 50
    }
    
    print(f"\nTesting {url}")
    print(f"Parameters: {params}\n")
    
    r = requests.get(url, params=params)
    print(f"Status Code: {r.status_code}")
    print(f"Response Headers: {dict(r.headers)}\n")
    print(f"Response Body (first 1000 chars):\n{r.text[:1000]}")
    
    # Check if response is valid DataTables JSON
    if r.status_code == 200:
        try:
            data = r.json()
            print(f"\n✓ Valid JSON response")
            print(f"  Keys: {list(data.keys())}")
            if 'error' in data:
                print(f"  Error: {data['error']}")
                print(f"  Message: {data.get('message', 'N/A')}")
            else:
                print(f"  Records returned: {len(data.get('data', []))}")
                print(f"  recordsTotal: {data.get('recordsTotal', '?')}")
                print(f"  recordsFiltered: {data.get('recordsFiltered', '?')}")
        except Exception as e:
            print(f"\n✗ Invalid JSON: {e}")
    else:
        print(f"\n✗ HTTP Error {r.status_code}")
        
finally:
    # Kill the Flask server
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("\n\nFlask server stopped.")
