#!/usr/bin/env python3
"""Compute the config hash for config/blacklab the same way as:
find "$CFG" -type f -print0 | sort -z | xargs -0 sha256sum > /tmp/blacklab_config_local.sha256
sha256sum /tmp/blacklab_config_local.sha256
"""

from pathlib import Path
import hashlib
import tempfile
import sys

expected = "1699dfa046e89a0a4f7af85909446b8ed090627994aa87b6eb1be998cca48df6"
repo_root = Path(__file__).resolve().parents[1]
cfg = repo_root / "config" / "blacklab"
if not cfg.exists():
    print(f"Config directory not found: {cfg}")
    sys.exit(3)

files = [p for p in cfg.rglob("*") if p.is_file()]
files.sort(key=lambda p: p.as_posix())
lines = []
for p in files:
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    # use repository-relative, POSIX-style paths to match the original find+sort output
    rel = p.relative_to(repo_root).as_posix()
    # mimic sha256sum format: "{hash}  {path}\n"
    lines.append(f"{h}  {rel}\n")

tmp = Path(tempfile.gettempdir()) / "blacklab_config_local.sha256"
# write as text with UTF-8
tmp.write_text("".join(lines), encoding="utf-8")
final = hashlib.sha256(tmp.read_bytes()).hexdigest()
print(f"wrote {tmp}")
print("==== sample (first 10 lines) ====")
print("".join(lines[:10]))
print(f"sha256({tmp}) = {final}")
print(f"expected = {expected}")
if final == expected:
    print("MATCH")
    sys.exit(0)
else:
    print("MISMATCH")
    sys.exit(2)
