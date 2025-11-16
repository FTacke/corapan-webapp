#!/usr/bin/env python3
"""
Live test script for Advanced Search verification.
Tests CQL generation, filter effectiveness, and result rendering.
"""
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_query(name, params, expected_cql=None):
    """Test a single query and log results."""
    log(f"\n{'='*60}")
    log(f"TEST: {name}")
    log(f"{'='*60}")
    
    url = f"{BASE_URL}/search/advanced/results"
    log(f"URL: {url}")
    log(f"Params: {params}")
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(url, params=params)
            
            log(f"✅ HTTP {response.status_code}")
            
            # Check if HTML fragment (results) or JSON (direct BLS)
            content_type = response.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                data = response.json()
                summary = data.get('summary', {})
                hits = data.get('hits', [])
                
                log(f"Hits: {summary.get('numberOfHits', 0)}")
                log(f"Docs: {summary.get('numberOfDocs', 0)}")
                log(f"Docs Retrieved: {summary.get('docsRetrieved', 0)}")
                
                if hits:
                    first_hit = hits[0]
                    log(f"First hit docPid: {first_hit.get('docPid', 'N/A')}")
                    match_words = first_hit.get('match', {}).get('word', [])
                    log(f"Match: {' '.join(match_words)}")
                
            elif 'text/html' in content_type:
                html = response.text
                log(f"Content-Length: {len(html)} bytes")
                
                # Check for result indicators
                if 'md3-search-summary' in html:
                    log("✅ Results summary present")
                elif 'md3-alert--error' in html:
                    log("⚠️ Error alert present")
                    # Extract error message
                    if '<strong>Error:</strong>' in html:
                        start = html.find('<strong>Error:</strong>') + len('<strong>Error:</strong>')
                        end = html.find('</div>', start)
                        error_msg = html[start:end].strip()
                        log(f"Error: {error_msg}")
                elif 'No se encontraron resultados' in html:
                    log("⚠️ No results found")
                else:
                    log("⚠️ Unknown response format")
                    log(f"Preview: {html[:200]}")
            
            # Verify expected CQL pattern if provided
            if expected_cql:
                if expected_cql in response.text:
                    log(f"✅ Expected CQL pattern found: {expected_cql}")
                else:
                    log(f"❌ Expected CQL pattern NOT found: {expected_cql}")
            
            return response.status_code, response.text[:500]
            
    except httpx.HTTPStatusError as e:
        log(f"❌ HTTP Error: {e.response.status_code}")
        log(f"Response: {e.response.text[:300]}")
        return e.response.status_code, e.response.text[:500]
        
    except Exception as e:
        log(f"❌ Exception: {type(e).__name__}: {e}")
        return None, str(e)

def main():
    """Run all test scenarios."""
    log("="*60)
    log("ADVANCED SEARCH LIVE VERIFICATION")
    log("="*60)
    
    # Test 1: forma_exacta (exact case/diacritics)
    test_query(
        "Test 1: forma_exacta - México (exact)",
        {"q": "México", "mode": "forma_exacta"},
        expected_cql='[word="México"]'
    )
    
    # Test 2: forma + ci/da (normalized)
    test_query(
        "Test 2: forma - mexico (case/diacritic insensitive)",
        {"q": "mexico", "mode": "forma", "ci": "true", "da": "true"},
        expected_cql='[norm="mexico"]'
    )
    
    # Test 3: Sequence with POS
    test_query(
        "Test 3: Sequence + POS - ir a (VERB + ADP)",
        {"q": "ir a", "mode": "lemma", "pos": "VERB,ADP"},
        expected_cql='[lemma="ir" & pos="VERB"]'
    )
    
    # Test 4: Filter by country
    test_query(
        "Test 4: Filter - country_code=ARG",
        {"q": "test", "mode": "forma", "country_code": "ARG"}
    )
    
    # Test 5: Filter by radio
    test_query(
        "Test 5: Filter - radio=Radio Nacional",
        {"q": "test", "mode": "forma", "radio": "Radio Nacional"}
    )
    
    # Test 6: Date range filter
    test_query(
        "Test 6: Filter - date range March 2020",
        {"q": "test", "mode": "forma", "date_from": "2020-03-01", "date_to": "2020-03-31"}
    )
    
    log("\n" + "="*60)
    log("VERIFICATION COMPLETE")
    log("="*60)

if __name__ == "__main__":
    main()
