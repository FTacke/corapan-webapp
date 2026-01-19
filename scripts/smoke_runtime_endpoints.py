#!/usr/bin/env python3
"""Smoke checks for runtime endpoints.

Usage:
  python scripts/smoke_runtime_endpoints.py --base-url http://localhost:8000

Defaults:
  base URL = http://localhost:8000

Auth-protected endpoints are treated as PASS if they return 401 or 303.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import urllib.error
import urllib.parse


def _request(url: str, timeout: float) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.getcode(), resp.read(2000).decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(2000).decode("utf-8", errors="ignore")
    except urllib.error.URLError as exc:
        return 0, str(exc.reason)
    except Exception as exc:  # noqa: BLE001
        return 0, str(exc)


def _check(name: str, url: str, ok_statuses: set[int], timeout: float) -> bool:
    status, body = _request(url, timeout)
    if status in ok_statuses:
        print(f"[PASS] {name} -> {status}", flush=True)
        return True
    safe_url = urllib.parse.urlsplit(url).path or url
    print(f"[FAIL] {name} -> {status} ({safe_url})\n{body[:200]}", flush=True)
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    timeout = args.timeout

    print(f"Running smoke checks against {base} (timeout={timeout}s)", flush=True)

    checks = [
        ("Atlas countries", f"{base}/api/v1/atlas/countries", {200}),
        ("Atlas files", f"{base}/api/v1/atlas/files", {200}),
        ("Corpus stats", f"{base}/corpus/api/" + "corpus_stats", {200, 404}),
        ("Stats image", f"{base}/corpus/api/statistics/viz_total_corpus.png", {200, 404}),
        ("Metadata TSV", f"{base}/corpus/metadata/download/tsv", {200, 404}),
        ("Metadata JSON", f"{base}/corpus/metadata/download/json", {200, 404}),
    ]

    # Auth-protected endpoints: accept 401/303 in unauthenticated context.
    protected = [
        ("Player overview", f"{base}/corpus/player", {200, 303, 401, 204}),
        ("Player", f"{base}/player?transcription=/media/transcripts/TEST.json&audio=/media/full/TEST.mp3", {200, 303, 401}),
        ("Transcript", f"{base}/media/transcripts/TEST.json", {200, 401, 404}),
        ("Audio full", f"{base}/media/full/TEST.mp3", {200, 401, 404}),
    ]

    ok = True
    for name, url, statuses in checks + protected:
        ok = _check(name, url, statuses, timeout) and ok

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
