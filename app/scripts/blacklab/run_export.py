#!/usr/bin/env python3
"""Run the canonical BlackLab export entrypoint from the app script path."""

from pathlib import Path
import os
import subprocess
import sys


APP_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = APP_ROOT.parent


if __name__ == "__main__":
    cmd = [sys.executable, "-m", "src.scripts.blacklab_index_creation", *sys.argv[1:]]
    print(f"[INFO] Workspace root: {WORKSPACE_ROOT}")
    print(f"[INFO] App root: {APP_ROOT}")
    print(f"[INFO] Invoking: {' '.join(cmd)}")
    rc = subprocess.call(
        cmd,
        cwd=str(APP_ROOT),
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    sys.exit(rc)
