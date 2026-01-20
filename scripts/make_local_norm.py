#!/usr/bin/env python3
from pathlib import Path

p = Path("/tmp/blacklab_config_local.manifest.sha256")
out = Path("/tmp/local.norm")
if not p.exists():
    print("missing source:", p)
    raise SystemExit(2)
lines = p.read_text().splitlines()
out_lines = []
for line in lines:
    if not line.strip():
        continue
    parts = line.split(None, 1)
    h = parts[0]
    path = parts[1] if len(parts) > 1 else ""
    name = path.split("/")[-1]
    out_lines.append(f"{h}  {name}")
out.write_text("\n".join(sorted(out_lines)) + "\n")
print("wrote", out)
