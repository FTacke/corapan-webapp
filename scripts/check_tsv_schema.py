#!/usr/bin/env python3
"""
Check that all TSV files in data/blacklab_export/tsv/ share the same header and schema.

Usage: python scripts/check_tsv_schema.py
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
TSV_DIR = ROOT / "data" / "blacklab_export" / "tsv"

if not TSV_DIR.exists():
    print(f"TSV directory not found: {TSV_DIR}")
    sys.exit(2)

headers = {}
bad = []

for p in sorted(TSV_DIR.glob("*.tsv")):
    try:
        with p.open("r", encoding="utf-8") as fh:
            header = fh.readline().strip()
            headers.setdefault(header, []).append(p.name)
    except Exception as e:
        print(f"Failed to read {p}: {e}")
        bad.append(p.name)

print("Found %s distinct headers" % len(headers))
for h, files in headers.items():
    print("--- HEADER ---")
    print(h)
    print("Files:")
    for f in files[:5]:
        print("  ", f)
    if len(files) > 5:
        print(f"  ... and {len(files) - 5} more files")
    print()

if bad:
    print("Errors reading files:")
    for f in bad:
        print(f" - {f}")
    sys.exit(1)

if len(headers) > 1:
    print(
        "ERROR: Multiple distinct TSV headers found. Please fix exporter or specific TSVs."
    )
    sys.exit(1)

print("All TSV files share identical header schema.")
sys.exit(0)
