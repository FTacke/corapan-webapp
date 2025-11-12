#!/usr/bin/env python3
"""Quick test of HTTP client fix."""

import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from src.app.extensions.http_client import BLS_BASE_URL, get_http_client, _http_client

print(f"BLS_BASE_URL: {BLS_BASE_URL}")

client = get_http_client()
print(f"Client created: {type(client)}")

# Test building a full URL
path = "/corapan/hits"
if path.startswith("/bls/"):
    path = path[4:]  # Remove "/bls" prefix, keep "/"
elif path.startswith("bls/"):
    path = "/" + path[4:]  # Convert "bls/..." to "/..."
elif not path.startswith("/"):
    path = "/" + path  # Ensure leading slash

full_url = f"{BLS_BASE_URL}{path}"
print(f"Full URL would be: {full_url}")

# Try a real request to see if it fails on protocol
try:
    resp = client.get(full_url, params={"patt": "test"})
    print(f"Request succeeded: {resp.status_code}")
except Exception as e:
    print(f"Request failed: {type(e).__name__}: {str(e)}")
