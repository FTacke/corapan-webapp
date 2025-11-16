#!/usr/bin/env python3
"""
Wrapper for running the BlackLab export script
Handles path resolution and encoding issues
"""
import subprocess
import sys
from pathlib import Path

def run_export():
    """Run the export script from LOKAL directory."""
    repo_root = Path(__file__).parent.absolute()
    export_script = repo_root / "LOKAL" / "01 - Add New Transcriptions" / "03b build blacklab_index" / "blacklab_index_creation.py"
    
    if not export_script.exists():
        print(f"ERROR: Export script not found: {export_script}")
        return 1
    
    print(f"[INFO] Running export script from: {export_script}")
    print(f"[INFO] Working directory: {repo_root}")
    print("-" * 80)
    
    # Run with explicit python interpreter and capture output
    result = subprocess.run(
        [sys.executable, str(export_script)],
        cwd=str(repo_root),
        env={**subprocess.os.environ, "PYTHONIOENCODING": "utf-8"},
        text=True,
        capture_output=False  # Don't capture, let it print to console
    )
    
    print("-" * 80)
    print(f"[INFO] Export completed with exit code: {result.returncode}")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_export())
