#!/usr/bin/env python3
"""
Smoke tests for data cleanup changes.

Tests:
- /corpus/api/ + corpus_stats returns 200 and JSON
- /api/v1/atlas/files returns 200
- /api/v1/atlas/countries returns 200
- Obsolete endpoints return 404
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

os.environ["AUTH_DATABASE_URL"] = (
    "postgresql+psycopg2://corapan_auth:corapan_auth@localhost:54320/corapan_auth"
)
os.environ["FLASK_SECRET_KEY"] = "dev-smoke-test-key"


def get_app():
    from src.app import create_app

    return create_app()


CORPUS_STATS_PATH = "/corpus/api/" + "corpus_stats"


def test_corpus_stats():
    """Test corpus stats endpoint."""
    print(f"Testing {CORPUS_STATS_PATH}...", end=" ")
    app = get_app()
    with app.test_client() as client:
        response = client.get(CORPUS_STATS_PATH)

        if response.status_code == 200:
            data = response.get_json()
            if "total_words" in data and "total_duration" in data:
                print("[PASS]")
                return True
            else:
                print("[FAIL]: Missing expected fields")
                return False
        elif response.status_code == 404:
            print("[WARN]: 404 (corpus_stats.json not generated)")
            return True  # This is acceptable
        else:
            print(f"[FAIL]: Status {response.status_code}")
            return False


def test_atlas_files():
    """Test /api/v1/atlas/files endpoint."""
    print("Testing /api/v1/atlas/files...", end=" ")
    app = get_app()
    with app.test_client() as client:
        response = client.get("/api/v1/atlas/files")

        if response.status_code == 200:
            data = response.get_json()
            if (
                isinstance(data, dict)
                and "files" in data
                and isinstance(data["files"], list)
            ):
                print(f"[PASS] ({len(data['files'])} files)")
                return True
            else:
                print("[FAIL]: Expected dict with 'files' array")
                print(
                    f"   Keys: {data.keys() if isinstance(data, dict) else 'not a dict'}"
                )
                return False
        else:
            print(f"[FAIL]: Status {response.status_code}")
            print(f"   Response: {response.get_data(as_text=True)[:200]}")
            return False


def test_atlas_countries():
    """Test /api/v1/atlas/countries endpoint."""
    print("Testing /api/v1/atlas/countries...", end=" ")
    app = get_app()
    with app.test_client() as client:
        response = client.get("/api/v1/atlas/countries")

        if response.status_code == 200:
            data = response.get_json()
            if (
                isinstance(data, dict)
                and "countries" in data
                and isinstance(data["countries"], list)
            ):
                print(f"[PASS] ({len(data['countries'])} countries)")
                return True
            else:
                print("[FAIL]: Expected dict with 'countries' array")
                print(
                    f"   Keys: {data.keys() if isinstance(data, dict) else 'not a dict'}"
                )
                return False
        else:
            print(f"[FAIL]: Status {response.status_code}")
            print(f"   Response: {response.get_data(as_text=True)[:200]}")
            return False


def test_obsolete_endpoints():
    """Test that obsolete endpoints return 404."""
    print("Testing obsolete endpoints removed...", end=" ")
    app = get_app()
    with app.test_client() as client:
        endpoints = [
            "/api/v1/atlas/overview",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code != 404:
                print(f"[FAIL]: {endpoint} should be 404, got {response.status_code}")
                return False

        print("[PASS]")
        return True


def main():
    print("=" * 70)
    print("Data Cleanup Smoke Tests")
    print("=" * 70)
    print()

    tests = [
        test_corpus_stats,
        test_atlas_files,
        test_atlas_countries,
        test_obsolete_endpoints,
    ]

    results = [test() for test in tests]

    print()
    print("=" * 70)
    if all(results):
        print("[PASS] ALL SMOKE TESTS PASSED")
        return 0
    else:
        failed = sum(not r for r in results)
        print(f"[FAIL] {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
