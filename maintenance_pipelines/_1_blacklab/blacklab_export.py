#!/usr/bin/env python3
"""
BlackLab Export Runner
======================
This script triggers the versioned BlackLab export pipeline from the active app
repository and writes to the canonical export tree under data/blacklab/export.

Usage:
    python blacklab_export.py
    python blacklab_export.py --app-repo-path C:\dev\corapan\app

Output:
    - TSV files in: data/blacklab/export/tsv/
    - DocMeta in:   data/blacklab/export/docmeta.jsonl
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def resolve_workspace_root(default_root: Path, override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return default_root


def resolve_app_repo_root(workspace_root: Path, override: str | None) -> Path:
    candidates = []
    if override:
        candidates.append(Path(override).expanduser().resolve())
    else:
        candidates.append(workspace_root / "app")

    for candidate in candidates:
        script_path = candidate / "src" / "scripts" / "blacklab_index_creation.py"
        build_path = candidate / "scripts" / "blacklab" / "build_blacklab_index.ps1"
        if script_path.is_file() and build_path.is_file():
            return candidate

    search_hint = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(
        "Could not resolve the active app repository. Checked: " + search_hint
    )


def parse_args() -> argparse.Namespace:
    default_workspace_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Run the canonical BlackLab export")
    parser.add_argument(
        "--workspace-root",
        help="Workspace root containing app/, data/, media/, and maintenance_pipelines/",
    )
    parser.add_argument(
        "--app-repo-path",
        help="Path to the active versioned app repository. Defaults to <workspace>/app.",
    )
    return parser.parse_args(), default_workspace_root


def main() -> int:
    args, default_workspace_root = parse_args()
    workspace_root = resolve_workspace_root(default_workspace_root, args.workspace_root)
    app_repo_root = resolve_app_repo_root(workspace_root, args.app_repo_path)

    export_script = app_repo_root / "src" / "scripts" / "blacklab_index_creation.py"
    input_dir = workspace_root / "media" / "transcripts"
    output_dir = workspace_root / "data" / "blacklab" / "export" / "tsv"
    docmeta_file = workspace_root / "data" / "blacklab" / "export" / "docmeta.jsonl"

    print(f"[INFO] Workspace Root: {workspace_root}")
    print(f"[INFO] App Repo Root:  {app_repo_root}")
    print(f"[INFO] Input Dir:      {input_dir}")
    print(f"[INFO] Output Dir:     {output_dir}")
    print(f"[INFO] DocMeta:        {docmeta_file}")

    cmd = [
        sys.executable,
        str(export_script),
        "--in",
        str(input_dir),
        "--out",
        str(output_dir),
        "--format",
        "tsv",
        "--docmeta",
        str(docmeta_file),
    ]

    print(f"[INFO] Running command: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(app_repo_root),
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            text=True,
        )

        if result.returncode == 0:
            print("-" * 60)
            print("[SUCCESS] Export completed successfully.")
            print(
                "Next step: build and publish the staged index before any data/media deploy."
            )
            return 0

        print("-" * 60)
        print(f"[ERROR] Export failed with exit code {result.returncode}")
        return result.returncode

    except KeyboardInterrupt:
        print("\n[INFO] Process interrupted by user.")
        return 130
    except Exception as exc:
        print(f"[ERROR] Unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
