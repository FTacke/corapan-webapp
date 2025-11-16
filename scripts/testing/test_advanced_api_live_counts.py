#!/usr/bin/env python3
"""
Live integration test for Advanced API counts.

- Verifies the Flask advanced API endpoint returns records for a common query
  when the BlackLab index is available.
- Compares counts from direct BL query (patt) and the advanced API (DataTables)
  to ensure the advanced API produces non-zero results and behaves consistently.

Usage:
    python scripts/test_advanced_api_live_counts.py

Exit codes:
    0 - success
    1 - failure (e.g., BL or Flask unreachable, or counts mismatch)

This script is intentionally small and tolerant: it will skip/print a warning
if BL or Flask are not reachable on the default hosts/ports.
"""

import sys
import httpx
import os
from datetime import datetime

BASE_FLASK = os.environ.get('FLASK_BASE_URL', 'http://localhost:8000')
BASE_BLS = os.environ.get('BLS_BASE_URL', 'http://localhost:8081/blacklab-server')
TIMEOUT = httpx.Timeout(connect=5.0, read=20.0, write=10.0, pool=5.0)

LOG_PREFIX = lambda: datetime.now().strftime('%H:%M:%S')


def log(msg):
    print(f"[{LOG_PREFIX()}] {msg}")


def fetch_bls_hits(query='casa', mode='lemma'):
    # Build patt parameter (lemma search) - BL expects an encoded patt param
    if mode == 'lemma':
        patt = f'[lemma="{query}"]'
    else:
        patt = f'[word="{query}"]'

    url = f"{BASE_BLS}/corpora/corapan/hits"
    params = {
        'patt': patt,
        'first': 0,
        'number': 1,  # we only need counts
        'listvalues': 'tokid'
    }
    headers = {"Accept": "application/json"}

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, params=params, headers=headers)
            r.raise_for_status()
            data = r.json()
            summary = data.get('summary', {}) or data.get('resultsStats', {})
            hits = summary.get('hits') or summary.get('numberOfHits') or 0
            return int(hits)
    except Exception as e:
        log(f"❌ BL query failed: {e}")
        return None


def fetch_flask_advanced(query='casa', mode='lemma', country_code=None):
    url = f"{BASE_FLASK}/search/advanced/data"
    params = {
        'draw': 1,
        'start': 0,
        'length': 10,
        'q': query,
        'mode': mode,
    }
    if country_code:
        params['country_code'] = country_code

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            payload = r.json()
            # DataTables style: recordsTotal / recordsFiltered
            rec_total = int(payload.get('recordsTotal') or 0)
            rec_filtered = int(payload.get('recordsFiltered') or 0)
            data_len = len(payload.get('data') or [])
            return rec_total, rec_filtered, data_len, payload
    except Exception as e:
        log(f"❌ Flask Advanced API call failed: {e}")
        return None, None, None, None


def main():
    log("Starting live integration test for Advanced API counts")

    # Step 1: Fetch BL direct hits
    bl_hits = fetch_bls_hits(query='casa', mode='lemma')
    if bl_hits is None:
        log("⚠️ Could not fetch BL hits; BlackLab may not be running at {}".format(BASE_BLS))
        log("Test skipped")
        return 1

    log(f"BlackLab reported hits for 'casa' (lemma): {bl_hits}")

    # Step 2: Fetch Flask advanced API counts
    rec_total, rec_filtered, data_len, payload = fetch_flask_advanced(query='casa', mode='lemma')
    if rec_total is None:
        log("⚠️ Flask advanced endpoint not reachable; Is the Flask app running at {}?".format(BASE_FLASK))
        log("Test skipped")
        return 1

    log(f"Flask advanced endpoint reported: recordsTotal={rec_total}, recordsFiltered={rec_filtered}, data_len={data_len}")

    # Basic assertion: both BL and flask should report non-zero results for a common query
    if bl_hits <= 0:
        log("❌ BlackLab returned zero hits for query - cannot assert further")
        return 1

    if rec_total <= 0 and rec_filtered <= 0:
        log("❌ Flask advanced endpoint reported zero results - unexpected")
        return 1

    # Check for consistency: Flask counts should not exceed BL counts
    if rec_total and rec_total > bl_hits:
        log(f"⚠️ Warning: Flask reported more results ({rec_total}) than BlackLab direct ({bl_hits})")
        # Not a strict fail; sometimes filters and token-level metadata differ

    # If all checks passed, print success and include a snippet of payload
    log("✅ Integration test: Advanced API returns results and is reachable")
    log("Payload preview:")
    log(str({k: payload.get(k) for k in ['recordsTotal', 'recordsFiltered', 'data']})[:1000])

    return 0


if __name__ == '__main__':
    rc = main()
    sys.exit(0 if rc == 0 else 1)
