import httpx

# Test Mock BLS directly
url = "http://localhost:8081/blacklab-server/corapan/hits"
params = {
    "patt": '[word="test"]',
    "first": 0,
    "number": 10
}

try:
    r = httpx.get(url, params=params, timeout=30.0)
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('content-type')}")
    print(f"\nJSON Response:")
    data = r.json()
    print(f"Hits: {data['summary']['numberOfHits']}")
    print(f"Docs: {data['summary']['numberOfDocs']}")
    print(f"Docs Retrieved: {data['summary']['docsRetrieved']}")
    print(f"\nFirst hit: {data['hits'][0]['docPid']}")
except Exception as e:
    print(f"Error: {e}")
