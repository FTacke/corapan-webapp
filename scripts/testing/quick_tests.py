#!/usr/bin/env python3
"""
Quick Live Tests for CO.RA.PAN (no Flask dependency).
Testet nur Endpoints, Flask muss separat laufen.
"""
import sys
import requests
import json
from typing import Dict, Any

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

def print_header(text):
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")

def test_1_proxy():
    """Test 1: Proxy Health"""
    print(f"{Colors.YELLOW}[1/4] Proxy Health Check...{Colors.RESET}")
    try:
        r = requests.get("http://localhost:8000/bls/", timeout=5)
        r.raise_for_status()
        data = r.json()
        if "blacklabBuildTime" in data:
            print(f"{Colors.GREEN}✅ Proxy OK - BlackLab BuildTime: {data['blacklabBuildTime']}{Colors.RESET}\n")
            return True
        else:
            print(f"{Colors.RED}❌ Response missing 'blacklabBuildTime'{Colors.RESET}\n")
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ Proxy FAIL: {e}{Colors.RESET}\n")
        return False

def test_2_cql():
    """Test 2: CQL Autodetect"""
    print(f"{Colors.YELLOW}[2/4] CQL Autodetect (patt/cql/cql_query)...{Colors.RESET}")
    params = ["patt", "cql", "cql_query"]
    all_passed = True
    
    for param in params:
        try:
            url = "http://localhost:8000/bls/corapan/hits"
            p = {param: '[lemma="ser"]', "maxhits": 3}
            r = requests.get(url, params=p, timeout=10)
            r.raise_for_status()
            data = r.json()
            hits = data.get("summary", {}).get("numberOfHits", 0)
            if hits > 0:
                print(f"{Colors.GREEN}✅ {param} → {hits} hits{Colors.RESET}")
            else:
                print(f"{Colors.RED}❌ {param} → 0 hits (expected >0){Colors.RESET}")
                all_passed = False
        except Exception as e:
            print(f"{Colors.RED}❌ {param} → FAIL: {e}{Colors.RESET}")
            all_passed = False
    
    print()
    return all_passed

def test_3_filter():
    """Test 3: Serverfilter"""
    print(f"{Colors.YELLOW}[3/4] Serverfilter (with/without country filter)...{Colors.RESET}")
    try:
        # No filter
        r1 = requests.get("http://localhost:8000/bls/corapan/hits", 
                         params={"patt": '[word="test"]', "maxhits": 1}, timeout=10)
        r1.raise_for_status()
        d1 = r1.json()
        docs_no_filter = d1["summary"]["docsRetrieved"]
        total_docs = d1["summary"]["numberOfDocs"]
        
        print(f"{Colors.GREEN}✅ No filter: docsRetrieved={docs_no_filter} / numberOfDocs={total_docs}{Colors.RESET}")
        
        # With filter
        r2 = requests.get("http://localhost:8000/bls/corapan/hits",
                         params={"filter": 'country:"ARG"', "patt": '[word="test"]', "maxhits": 1}, timeout=10)
        r2.raise_for_status()
        d2 = r2.json()
        docs_with_filter = d2["summary"]["docsRetrieved"]
        
        print(f"{Colors.GREEN}✅ ARG filter: docsRetrieved={docs_with_filter} / numberOfDocs={total_docs}{Colors.RESET}")
        
        if docs_with_filter < docs_no_filter:
            print(f"{Colors.GREEN}✅ Filter reduction confirmed (server-side filtering active){Colors.RESET}\n")
            return True
        else:
            print(f"{Colors.RED}❌ Filter NOT reducing (expected {docs_with_filter} < {docs_no_filter}){Colors.RESET}\n")
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ Serverfilter test FAIL: {e}{Colors.RESET}\n")
        return False

def test_4_ui():
    """Test 4: Advanced Search UI"""
    print(f"{Colors.YELLOW}[4/4] Advanced Search UI (HTML with A11y)...{Colors.RESET}")
    try:
        r = requests.get("http://localhost:8000/search/advanced/results",
                        params={"q": "México", "mode": "forma_exacta"}, timeout=10)
        r.raise_for_status()
        html = r.text
        
        has_summary = "md3-search-summary" in html
        has_a11y = 'aria-live' in html
        
        if has_summary:
            print(f"{Colors.GREEN}✅ UI renders with md3-search-summary{Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ UI missing md3-search-summary{Colors.RESET}")
            return False
        
        if has_a11y:
            print(f"{Colors.GREEN}✅ A11y attributes present (aria-live){Colors.RESET}\n")
            return True
        else:
            print(f"{Colors.RED}❌ A11y attributes missing (aria-live){Colors.RESET}\n")
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ UI test FAIL: {e}{Colors.RESET}\n")
        return False

def main():
    print_header("CO.RA.PAN Live Tests - Advanced Search")
    print(f"Flask URL: http://localhost:8000")
    print(f"BLS URL: http://localhost:8081/blacklab-server\n")
    
    results = []
    results.append(("Proxy Health", test_1_proxy()))
    results.append(("CQL Autodetect", test_2_cql()))
    results.append(("Serverfilter", test_3_filter()))
    results.append(("UI Rendering", test_4_ui()))
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {name}: {status}")
    
    print(f"\n{Colors.CYAN}Total: {passed}/{total} tests passed{Colors.RESET}\n")
    
    if passed == total:
        print(f"{Colors.GREEN}✅ All tests passed! System is production-ready.{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.RED}❌ Some tests failed. Check logs and retry.{Colors.RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
