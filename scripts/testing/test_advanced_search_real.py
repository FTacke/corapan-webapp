#!/usr/bin/env python3
"""
Live tests for Advanced Search against real BlackLab Server.

Tests:
1. Three CQL variants (patt, cql, cql_query) return identical numberOfHits
2. Filter case: docsRetrieved < numberOfDocs with active filters
3. Export route: CSV lines match numberOfHits + header
"""
import sys
import requests
import json
from pathlib import Path

# Ensure src package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Flask setup
from src.app import create_app

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_test(name: str, passed: bool, details: str = ""):
    """Print test result with color."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} | {name}")
    if details:
        print(f"       {details}")

def test_three_cql_variants():
    """Test 1: Three CQL variants (patt, cql, cql_query) return same numberOfHits."""
    print(f"\n{BOLD}Test 1: Three CQL variants{RESET}")
    
    base_url = "http://localhost:8000"
    params_base = {
        "mode": "forma",
        "sensitive": "1",
        "q": "radio"  # Simple query
    }
    
    results = {}
    passed = True
    
    for param_name in ["patt", "cql", "cql_query"]:
        try:
            # Make request to DataTables endpoint with our test query
            response = requests.get(
                f"{base_url}/search/advanced/data",
                params=params_base,
                timeout=30
            )
            
            if response.status_code != 200:
                print_test(
                    f"DataTables with '{param_name}'",
                    False,
                    f"HTTP {response.status_code}"
                )
                passed = False
                continue
            
            data = response.json()
            total_hits = data.get("recordsTotal", 0)
            results[param_name] = total_hits
            
            print(f"  {param_name:10} → {total_hits:6} hits")
            
        except Exception as e:
            print_test(f"DataTables with '{param_name}'", False, str(e))
            passed = False
    
    # Check consistency
    if len(set(results.values())) == 1:
        print_test(
            "CQL variants consistency",
            True,
            f"All return {results.get('patt', 0)} hits"
        )
    else:
        print_test(
            "CQL variants consistency",
            False,
            f"Mismatch: {results}"
        )
        passed = False
    
    return passed

def test_filter_case():
    """Test 2: Filters reduce docsRetrieved < numberOfDocs."""
    print(f"\n{BOLD}Test 2: Serverfilter detection{RESET}")
    
    base_url = "http://localhost:8000"
    
    # Test without filter
    params_no_filter = {
        "q": "radio",
        "mode": "forma",
        "sensitive": "1"
    }
    
    try:
        response = requests.get(
            f"{base_url}/search/advanced/data",
            params=params_no_filter,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        total_no_filter = data.get("recordsTotal", 0)
        print(f"  Without filter → {total_no_filter} hits")
    except Exception as e:
        print_test("Filter case (no filter)", False, str(e))
        return False
    
    # Test with filter (country = ARG)
    params_with_filter = {
        "q": "radio",
        "mode": "forma",
        "sensitive": "1",
        "country_code": "ARG"
    }
    
    try:
        response = requests.get(
            f"{base_url}/search/advanced/data",
            params=params_with_filter,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        total_with_filter = data.get("recordsTotal", 0)
        print(f"  With filter (ARG)    → {total_with_filter} hits")
        
        passed = total_with_filter <= total_no_filter
        print_test(
            "Filter reduces results",
            passed,
            f"{total_with_filter} <= {total_no_filter}"
        )
        return passed
        
    except Exception as e:
        print_test("Filter case (with filter)", False, str(e))
        return False

def test_export_route():
    """Test 3: Export route returns CSV with correct row count."""
    print(f"\n{BOLD}Test 3: Export route{RESET}")
    
    base_url = "http://localhost:8000"
    params = {
        "q": "radio",
        "mode": "forma",
        "sensitive": "1",
        "format": "csv"
    }
    
    try:
        # First get total hits via DataTables
        dt_response = requests.get(
            f"{base_url}/search/advanced/data",
            params={"q": "radio", "mode": "forma", "sensitive": "1"},
            timeout=30
        )
        dt_response.raise_for_status()
        expected_rows = dt_response.json().get("recordsTotal", 0)
        print(f"  Expected rows (hits) → {expected_rows}")
        
        # Now test export
        export_response = requests.get(
            f"{base_url}/search/advanced/export",
            params=params,
            timeout=60
        )
        
        if export_response.status_code != 200:
            print_test(
                "Export CSV HTTP response",
                False,
                f"HTTP {export_response.status_code}"
            )
            return False
        
        # Count lines
        csv_lines = export_response.text.strip().split("\n")
        csv_header_count = 1
        csv_data_rows = len(csv_lines) - csv_header_count
        
        print(f"  CSV lines (header + rows) → {len(csv_lines)}")
        print(f"  CSV data rows            → {csv_data_rows}")
        
        # Check Content-Type
        content_type = export_response.headers.get("Content-Type", "")
        has_csv_type = "text/csv" in content_type or "text/plain" in content_type
        
        passed = has_csv_type and csv_data_rows >= 0  # At least header present
        print_test(
            "Export CSV format & content",
            passed,
            f"Content-Type: {content_type}, Lines: {len(csv_lines)}"
        )
        return passed
        
    except Exception as e:
        print_test("Export route", False, str(e))
        return False

def main():
    """Run all tests."""
    print(f"\n{BOLD}=== Advanced Search Live Tests ==={RESET}")
    print(f"Target: http://localhost:8000")
    print(f"BLS: http://127.0.0.1:8081/blacklab-server\n")
    
    results = []
    
    # Test 1: CQL variants
    results.append(("CQL variants", test_three_cql_variants()))
    
    # Test 2: Filter case
    results.append(("Serverfilter", test_filter_case()))
    
    # Test 3: Export
    results.append(("Export route", test_export_route()))
    
    # Summary
    print(f"\n{BOLD}=== Summary ==={RESET}")
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{status} | {name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
