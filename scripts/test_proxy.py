import httpx

# Test Flask BLS proxy
url = "http://localhost:8000/bls/corapan/hits"
params = {
    "patt": '[word="test"]',
    "first": 0,
    "number": 10
}

try:
    r = httpx.get(url, params=params, timeout=30.0)
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('content-type')}")
    print(f"Content length: {len(r.text)} bytes")
    print("\nFirst 500 chars:")
    print(r.text[:500])
except Exception as e:
    print(f"Error: {e}")
