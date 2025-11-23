#!/usr/bin/env python3
"""
Central wrapper to run the canonical BlackLab export runner under LOKAL
This allows starting the export from a central `scripts` path while keeping the
single source-of-truth script at `LOKAL/01 - Add New Transcriptions/03b_generate_blacklab_export.py`.
"""

from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
LOKAL_RUNNER = REPO_ROOT / 'LOKAL' / '01 - Add New Transcriptions' / '03b_generate_blacklab_export.py'

if __name__ == '__main__':
    if not LOKAL_RUNNER.exists():
        print(f"ERROR: LOKAL runner not found: {LOKAL_RUNNER}")
        sys.exit(1)

    cmd = [sys.executable, str(LOKAL_RUNNER)]
    print(f"[INFO] Invoking: {' '.join(cmd)}")
    rc = subprocess.call(cmd, cwd=str(REPO_ROOT), env={**subprocess.os.environ, 'PYTHONIOENCODING': 'utf-8'})
    sys.exit(rc)
