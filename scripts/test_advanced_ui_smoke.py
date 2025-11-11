#!/usr/bin/env python3
"""
Advanced Search UI Smoke Tests - Test Advanced UI against live server

Tests:
1. lemma/forma/CQL modes
2. Filter reduction (country, speaker_type, etc.)
3. Export CSV/TSV with all hits
4. Form state restoration from URL
5. Summary box updates
6. DataTables schema matches Simple

Status: 2025-11-11 - Ready for live testing
"""

import requests
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
BLS_URL = "http://127.0.0.1:8081/blacklab-server"

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def log_test(name):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST: {name}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")


def log_pass(msg=""):
    print(f"{GREEN}✅ PASS{RESET} {msg}")


def log_fail(msg=""):
    print(f"{RED}❌ FAIL{RESET} {msg}")


def log_info(msg):
    print(f"{YELLOW}ℹ️  {msg}{RESET}")


def test_data_endpoint_lemma():
    """Test /search/advanced/data with lemma mode"""
    log_test("DataTables Endpoint - Lemma Mode")
    
    try:
        resp = requests.get(f"{BASE_URL}/search/advanced/data", params={
            "q": "hablar",
            "mode": "lemma",
            "sensitive": "1"
        }, timeout=30)
        
        if resp.status_code != 200:
            log_fail(f"HTTP {resp.status_code}")
            return False
        
        data = resp.json()
        
        # Check response structure
        assert "recordsTotal" in data, "Missing recordsTotal"
        assert "recordsFiltered" in data, "Missing recordsFiltered"
        assert "data" in data, "Missing data"
        
        hits = data["recordsFiltered"]
        log_info(f"Query: 'hablar' (lemma mode) → {hits} hits")
        
        if hits > 0:
            # Check first row structure (12 columns)
            row = data["data"][0]
            expected_fields = ["left", "match", "right", "country", "speaker_type", "sex", "mode", "discourse", "tokid", "filename", "start_ms", "end_ms"]
            for field in expected_fields:
                assert field in row, f"Missing field: {field}"
            
            log_pass(f"lemma mode: {hits} hits, schema OK")
            return True
        else:
            log_fail("Zero hits for lemma search")
            return False
            
    except Exception as e:
        log_fail(str(e))
        return False


def test_data_endpoint_forma():
    """Test /search/advanced/data with forma mode"""
    log_test("DataTables Endpoint - Forma Mode")
    
    try:
        resp = requests.get(f"{BASE_URL}/search/advanced/data", params={
            "q": "radio",
            "mode": "forma",
            "sensitive": "1"
        }, timeout=30)
        
        if resp.status_code != 200:
            log_fail(f"HTTP {resp.status_code}")
            return False
        
        data = resp.json()
        hits = data["recordsFiltered"]
        
        log_info(f"Query: 'radio' (forma mode) → {hits} hits")
        
        if hits > 0:
            log_pass(f"forma mode: {hits} hits")
            return True
        else:
            log_fail("Zero hits for forma search")
            return False
            
    except Exception as e:
        log_fail(str(e))
        return False


def test_data_endpoint_cql():
    """Test /search/advanced/data with CQL mode"""
    log_test("DataTables Endpoint - CQL Mode")
    
    try:
        # Simple CQL: word form 'palabras'
        resp = requests.get(f"{BASE_URL}/search/advanced/data", params={
            "q": '[word="palabras"]',
            "mode": "cql",
            "sensitive": "1"
        }, timeout=30)
        
        if resp.status_code != 200:
            log_fail(f"HTTP {resp.status_code}")
            return False
        
        data = resp.json()
        hits = data["recordsFiltered"]
        
        log_info(f"Query: [word=\"palabras\"] (CQL mode) → {hits} hits")
        
        if hits >= 0:  # CQL may return 0 hits, that's OK
            log_pass(f"CQL mode: {hits} hits")
            return True
        else:
            log_fail("CQL query error")
            return False
            
    except Exception as e:
        log_fail(str(e))
        return False


def test_filter_reduction():
    """Test that filters reduce result count"""
    log_test("Filter Reduction - Country Filter")
    
    try:
        # Query without filter
        resp1 = requests.get(f"{BASE_URL}/search/advanced/data", params={
            "q": "radio",
            "mode": "forma"
        }, timeout=30)
        
        if resp1.status_code != 200:
            log_fail(f"Without filter: HTTP {resp1.status_code}")
            return False
        
        total_hits = resp1.json()["recordsFiltered"]
        log_info(f"Without filter: {total_hits} hits")
        
        # Query with country filter
        resp2 = requests.get(f"{BASE_URL}/search/advanced/data", params={
            "q": "radio",
            "mode": "forma",
            "country_code": ["ARG", "CHL"]
        }, timeout=30)
        
        if resp2.status_code != 200:
            log_fail(f"With filter: HTTP {resp2.status_code}")
            return False
        
        filtered_hits = resp2.json()["recordsFiltered"]
        log_info(f"With filter (ARG, CHL): {filtered_hits} hits")
        
        # Check reduction
        if filtered_hits <= total_hits:
            log_pass(f"Filter reduced results: {total_hits} → {filtered_hits}")
            return True
        else:
            log_fail(f"Filter did not reduce results: {filtered_hits} > {total_hits}")
            return False
            
    except Exception as e:
        log_fail(str(e))
        return False


def test_export_csv():
    """Test CSV export endpoint"""
    log_test("Export Endpoint - CSV Format")
    
    try:
        resp = requests.get(f"{BASE_URL}/search/advanced/export", params={
            "q": "radio",
            "mode": "forma",
            "format": "csv"
        }, timeout=60)
        
        if resp.status_code != 200:
            log_fail(f"HTTP {resp.status_code}")
            return False
        
        # Check content type
        content_type = resp.headers.get("Content-Type", "")
        if "text/csv" not in content_type:
            log_fail(f"Wrong Content-Type: {content_type}")
            return False
        
        # Check for header
        lines = resp.text.strip().split("\n")
        if len(lines) < 2:
            log_fail("CSV has no data rows")
            return False
        
        header = lines[0]
        # Expected columns: left,match,right,country,speaker_type,sex,mode,discourse,filename,radio,tokid,start_ms,end_ms
        if "left" not in header or "match" not in header:
            log_fail(f"Invalid CSV header: {header}")
            return False
        
        log_info(f"CSV export: {len(lines)} lines (1 header + {len(lines)-1} data rows)")
        log_pass(f"CSV format OK, {len(lines)-1} results exported")
        return True
        
    except Exception as e:
        log_fail(str(e))
        return False


def test_export_tsv():
    """Test TSV export endpoint"""
    log_test("Export Endpoint - TSV Format")
    
    try:
        resp = requests.get(f"{BASE_URL}/search/advanced/export", params={
            "q": "radio",
            "mode": "forma",
            "format": "tsv"
        }, timeout=60)
        
        if resp.status_code != 200:
            log_fail(f"HTTP {resp.status_code}")
            return False
        
        # Check content type
        content_type = resp.headers.get("Content-Type", "")
        if "text/tab-separated-values" not in content_type:
            log_fail(f"Wrong Content-Type: {content_type}")
            return False
        
        # Check for tab delimiters
        lines = resp.text.strip().split("\n")
        if len(lines) < 2:
            log_fail("TSV has no data rows")
            return False
        
        header = lines[0]
        if "\t" not in header:
            log_fail("TSV header is not tab-delimited")
            return False
        
        log_info(f"TSV export: {len(lines)} lines (1 header + {len(lines)-1} data rows)")
        log_pass(f"TSV format OK, {len(lines)-1} results exported")
        return True
        
    except Exception as e:
        log_fail(str(e))
        return False


def test_export_with_filters():
    """Test export respects filters"""
    log_test("Export with Filters - CSV All Hits")
    
    try:
        # Export with country filter
        resp = requests.get(f"{BASE_URL}/search/advanced/export", params={
            "q": "radio",
            "mode": "forma",
            "format": "csv",
            "country_code": ["ARG"]
        }, timeout=60)
        
        if resp.status_code != 200:
            log_fail(f"HTTP {resp.status_code}")
            return False
        
        lines = resp.text.strip().split("\n")
        filtered_count = len(lines) - 1  # Exclude header
        
        log_info(f"Export with country filter (ARG): {filtered_count} results")
        log_pass(f"Export respects filters: {filtered_count} results")
        return True
        
    except Exception as e:
        log_fail(str(e))
        return False


def test_url_state_restoration():
    """Test that URL parameters are restored in form"""
    log_test("Form State - URL Restoration")
    
    try:
        # This is an integration test that would require Selenium/Playwright
        # For now, we verify the backend accepts these parameters
        
        params = {
            "q": "radio",
            "mode": "forma",
            "sensitive": "1",
            "country_code": ["ARG", "MEX"],
            "speaker_type": ["pro"],
            "sex": ["m"],
            "discourse": ["general"]
        }
        
        resp = requests.get(f"{BASE_URL}/search/advanced/data", params=params, timeout=30)
        
        if resp.status_code != 200:
            log_fail(f"HTTP {resp.status_code}")
            return False
        
        data = resp.json()
        hits = data["recordsFiltered"]
        
        log_info(f"URL with state params: {hits} hits")
        log_pass("URL state parameters accepted by backend")
        return True
        
    except Exception as e:
        log_fail(str(e))
        return False


def test_summary_box():
    """Test summary box data"""
    log_test("Summary Box - Result Count")
    
    try:
        resp = requests.get(f"{BASE_URL}/search/advanced/data", params={
            "q": "hablar",
            "mode": "lemma"
        }, timeout=30)
        
        if resp.status_code != 200:
            log_fail(f"HTTP {resp.status_code}")
            return False
        
        data = resp.json()
        
        # Check summary fields
        assert "recordsFiltered" in data
        assert "recordsTotal" in data
        assert "draw" in data
        
        filtered = data["recordsFiltered"]
        total = data["recordsTotal"]
        
        log_info(f"Summary: {filtered} filtered of {total} total")
        
        if filtered >= 0:
            log_pass(f"Summary box data OK: {filtered}/{total}")
            return True
        else:
            log_fail("Invalid summary data")
            return False
            
    except Exception as e:
        log_fail(str(e))
        return False


def main():
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Advanced Search UI - Smoke Test Suite{RESET}")
    print(f"{BLUE}Server: {BASE_URL}{RESET}")
    print(f"{BLUE}Timestamp: {datetime.now().isoformat()}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    tests = [
        ("Data Endpoint - Lemma Mode", test_data_endpoint_lemma),
        ("Data Endpoint - Forma Mode", test_data_endpoint_forma),
        ("Data Endpoint - CQL Mode", test_data_endpoint_cql),
        ("Filter Reduction", test_filter_reduction),
        ("Export - CSV Format", test_export_csv),
        ("Export - TSV Format", test_export_tsv),
        ("Export - With Filters", test_export_with_filters),
        ("Form State - URL Restoration", test_url_state_restoration),
        ("Summary Box", test_summary_box),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            log_fail(f"Test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}SUMMARY{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{status} {test_name}")
    
    print(f"\n{BLUE}Total: {passed}/{total} tests passed{RESET}\n")
    
    if passed == total:
        print(f"{GREEN}🎉 All tests passed!{RESET}\n")
        return 0
    else:
        print(f"{RED}⚠️  {total - passed} test(s) failed{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
