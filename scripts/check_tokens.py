#!/usr/bin/env python3
"""
Check token IDs in BlackLab (via Flask BL proxy) and verify canonical mapping
and split-file snippet generation.

Usage:
  python scripts/check_tokens.py ven2252d1579 per957945154 uryf9b89293f

Requirements:
- Flask dev server running (python -m src.app.main) so /bls proxy is available
- BlackLab server running (Docker) and index built
"""

from __future__ import annotations

import sys
import os
import requests
from urllib.parse import urlencode
from pathlib import Path

# Use internal helpers

# Ensure project src package is importable when running as script
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.app.services.audio_snippets import SPLIT_TIMES, build_snippet, find_split_file  # noqa: E402
from src.app.services.blacklab_search import _hit_to_canonical  # noqa: E402

BL_PROXY_BASE = "http://127.0.0.1:8000/bls"
BLS_CORPUS = os.environ.get("BLS_CORPUS", "index")

LISTVALUES = (
    "tokid,start_ms,end_ms,filename,file_id,word,lemma,country,country_code,radio"
)


def query_blacklab(tokid: str):
    params = {
        "first": 0,
        "number": 10,
        "wordsaroundhit": 10,
        "listvalues": LISTVALUES,
        "patt": f'[tokid="{tokid}"]',
    }
    url = f"{BL_PROXY_BASE}/corpora/{BLS_CORPUS}/hits"
    print(f"Querying BL proxy: {url}?{urlencode(params)}")
    r = requests.get(
        url, params=params, timeout=10, headers={"Accept": "application/json"}
    )
    r.raise_for_status()
    data = r.json()
    hits = data.get("hits", [])
    docInfos = data.get("docInfos") or {}
    return hits, docInfos
    return hits


def main(tokens):
    for tok in tokens:
        print("\n" + "=" * 60)
        print("Token:", tok)
        try:
            hits, docInfos = query_blacklab(tok)
        except Exception as e:
            print("Error querying BL proxy:", e)
            continue
        if not hits:
            print("No hits returned for token", tok)
            continue
        pid_to_file_id = {}
        # Build mapping from docInfos if available (docPid -> file_id)
        for pid, info in (docInfos or {}).items():
            md = info.get("metadata", {}) or {}
            fname = md.get("file_id") or None
            if not fname and md.get("fromInputFile"):
                src = md.get("fromInputFile")
                if isinstance(src, list) and src:
                    src = src[0]
                base = Path(src).name if src else None
                if base:
                    fname = Path(base).stem
            if fname:
                pid_to_file_id[str(pid)] = fname

        for i, hit in enumerate(hits[:3]):
            canon = _hit_to_canonical(hit)
            print(f"Hit #{i + 1} canonical:")
            for k in [
                "token_id",
                "filename",
                "start_ms",
                "end_ms",
                "context_start",
                "context_end",
                "text",
                "country_code",
            ]:
                print(f"  {k}: {canon.get(k)}")

            filename = canon.get("filename")
            # If filename looks numeric or is a docPid, try to use docInfos mapping
            if filename and str(filename).isdigit() and str(filename) in pid_to_file_id:
                filename = pid_to_file_id[str(filename)]
            start_ms = canon.get("start_ms", 0)
            end_ms = canon.get("end_ms", 0)

            # Convert to seconds for find_split_file
            start_s = start_ms / 1000.0
            end_s = end_ms / 1000.0

            split_res = None
            if filename:
                split_res = find_split_file(
                    f"{filename}.mp3" if not filename.endswith(".mp3") else filename,
                    start_s,
                    end_s,
                )
            if split_res:
                split_path, suffix = split_res
                print(f"  Split file: {split_path} (suffix {suffix})")
                # Compute local offsets using SPLIT_TIMES mapping
                try:
                    split_start_time = SPLIT_TIMES[suffix][0]
                    local_start_ms = int(start_ms - (split_start_time * 1000))
                    local_end_ms = int(end_ms - (split_start_time * 1000))
                    print(f"  Local offset (ms): {local_start_ms} - {local_end_ms}")
                except Exception as e:
                    print("  Could not compute split offsets:", e)
            else:
                print("  No matching split file found; fallback to full audio likely")

            # Try to build snippet; will write into media/mp3-temp
            try:
                print("  Attempting to build snippet (this may be slow)")
                snippet = build_snippet(
                    f"{filename}.mp3" if not filename.endswith(".mp3") else filename,
                    start_s,
                    end_s,
                    token_id=tok,
                    snippet_type="pal",
                )
                print("  Snippet written:", snippet)
                print("  Exists in temp dir?", snippet.exists())
            except Exception as e:
                print("  Build snippet failed:", e)


def _parse_args():
    if len(sys.argv) <= 1:
        print("Usage: python scripts/check_tokens.py <token_id> [<token_id> ...]")
        sys.exit(1)
    return sys.argv[1:]


if __name__ == "__main__":
    main(_parse_args())
