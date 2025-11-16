#!/usr/bin/env python3
"""
Automated Live Tests for CO.RA.PAN Advanced Search (Production).

Prerequisites:
    - BlackLab Server running on http://localhost:8081/blacklab-server
    - Flask running on http://localhost:8000 (Gunicorn/Waitress)

Usage:
    python scripts/live_tests.py [--flask-url URL] [--bls-url URL]

Tests:
    1. Proxy Health Check
    2. CQL Autodetect (patt/cql/cql_query)
    3. Serverfilter (with/without filter)
    4. Advanced Search UI (HTML rendering)
"""
import sys
import argparse
import requests
from typing import Dict, Any, Optional


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"


def print_header(text: str) -> None:
    """Print colored header."""
    print(f"\n{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}\n")


def print_test(number: int, total: int, name: str) -> None:
    """Print test number and name."""
    print(f"{Colors.YELLOW}[{number}/{total}] {name}...{Colors.RESET}")


def print_success(message: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def print_error(message: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")


def test_proxy_health(flask_url: str) -> bool:
    """Test 1: Proxy Health Check."""
    print_test(1, 4, "Proxy Health Check")
    try:
        response = requests.get(f"{flask_url}/bls/", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "blacklabBuildTime" in data:
            print_success(f"Proxy OK - BlackLab BuildTime: {data['blacklabBuildTime']}")
            return True
        else:
            print_error("Response missing 'blacklabBuildTime'")
            return False
    except requests.RequestException as e:
        print_error(f"Proxy FAIL: {e}")
        return False


def test_cql_autodetect(flask_url: str) -> bool:
    """Test 2: CQL Autodetect (patt/cql/cql_query)."""
    print_test(2, 4, "CQL Autodetect (patt/cql/cql_query)")
    
    params_to_test = ["patt", "cql", "cql_query"]
    all_passed = True
    
    for param in params_to_test:
        try:
            url = f"{flask_url}/bls/corapan/hits"
            params = {param: '[lemma="ser"]', "maxhits": 3}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            hits = data.get("summary", {}).get("numberOfHits", 0)
            if hits > 0:
                print_success(f"{param} → {hits} hits")
            else:
                print_error(f"{param} → 0 hits (expected >0)")
                all_passed = False
        except requests.RequestException as e:
            print_error(f"{param} → FAIL: {e}")
            all_passed = False
    
    return all_passed


def test_serverfilter(flask_url: str) -> bool:
    """Test 3: Serverfilter (with/without filter)."""
    print_test(3, 4, "Serverfilter (with/without country filter)")
    
    try:
        # Without filter
        url_no_filter = f"{flask_url}/bls/corapan/hits"
        params_no_filter = {"patt": '[word="test"]', "maxhits": 1}
        response_no_filter = requests.get(url_no_filter, params=params_no_filter, timeout=10)
        response_no_filter.raise_for_status()
        data_no_filter = response_no_filter.json()
        
        docs_retrieved_no_filter = data_no_filter["summary"]["docsRetrieved"]
        number_of_docs = data_no_filter["summary"]["numberOfDocs"]
        print_success(f"No filter: docsRetrieved={docs_retrieved_no_filter} / numberOfDocs={number_of_docs}")
        
        # With filter
        url_with_filter = f"{flask_url}/bls/corapan/hits"
        params_with_filter = {"filter": 'country:"ARG"', "patt": '[word="test"]', "maxhits": 1}
        response_with_filter = requests.get(url_with_filter, params=params_with_filter, timeout=10)
        response_with_filter.raise_for_status()
        data_with_filter = response_with_filter.json()
        
        docs_retrieved_with_filter = data_with_filter["summary"]["docsRetrieved"]
        print_success(f"ARG filter: docsRetrieved={docs_retrieved_with_filter} / numberOfDocs={number_of_docs}")
        
        # Verify filter reduces docs
        if docs_retrieved_with_filter < docs_retrieved_no_filter:
            print_success("Filter reduction confirmed (server-side filtering active)")
            return True
        else:
            print_error(f"Filter NOT reducing documents (expected {docs_retrieved_with_filter} < {docs_retrieved_no_filter})")
            return False
    except requests.RequestException as e:
        print_error(f"Serverfilter test FAIL: {e}")
        return False
    except KeyError as e:
        print_error(f"Response missing key: {e}")
        return False


def test_ui_rendering(flask_url: str) -> bool:
    """Test 4: Advanced Search UI (HTML rendering)."""
    print_test(4, 4, "Advanced Search UI (HTML with A11y)")
    
    try:
        url = f"{flask_url}/search/advanced/results"
        params = {"q": "México", "mode": "forma_exacta"}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        html = response.text
        
        # Check for results summary
        if "md3-search-summary" in html:
            print_success("UI renders with md3-search-summary")
        else:
            print_error("UI missing md3-search-summary div")
            return False
        
        # Check for A11y attributes
        if 'aria-live="polite"' in html or 'aria-live' in html:
            print_success("A11y attributes present (aria-live)")
            return True
        else:
            print_error("A11y attributes missing (aria-live)")
            return False
    except requests.RequestException as e:
        print_error(f"UI test FAIL: {e}")
        return False


def main():
    """Run all live tests."""
    parser = argparse.ArgumentParser(description="CO.RA.PAN Live Tests")
    parser.add_argument(
        "--flask-url",
        default="http://localhost:8000",
        help="Flask app URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--bls-url",
        default="http://localhost:8081/blacklab-server",
        help="BlackLab Server URL (default: http://localhost:8081/blacklab-server)"
    )
    args = parser.parse_args()
    
    print_header("CO.RA.PAN Live Tests - Advanced Search")
    print(f"Flask URL: {args.flask_url}")
    print(f"BLS URL: {args.bls_url}")
    
    results = []
    
    # Run tests
    results.append(("Proxy Health", test_proxy_health(args.flask_url)))
    results.append(("CQL Autodetect", test_cql_autodetect(args.flask_url)))
    results.append(("Serverfilter", test_serverfilter(args.flask_url)))
    results.append(("UI Rendering", test_ui_rendering(args.flask_url)))
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {name}: {status}")
    
    print(f"\n{Colors.CYAN}Total: {passed}/{total} tests passed{Colors.RESET}\n")
    
    if passed == total:
        print(f"{Colors.GREEN}✅ All tests passed! System is production-ready.{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"{Colors.RED}❌ Some tests failed. Please check logs and retry.{Colors.RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
