from pathlib import Path
import runpy
import sys


workspace_root = Path(__file__).resolve().parents[2]
implementation = workspace_root / "app" / "scripts" / "blacklab" / "run_export.py"
if not implementation.is_file():
	raise FileNotFoundError(f"Could not resolve BlackLab export implementation: {implementation}")

sys.argv[0] = str(implementation)
runpy.run_path(str(implementation), run_name="__main__")