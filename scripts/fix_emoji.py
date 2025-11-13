#!/usr/bin/env python3
import sys
from pathlib import Path

file_path = r"LOKAL\01 - Add New Transcriptions\03b build blacklab_index\blacklab_index_creation.py"
file_path = Path(file_path)

if file_path.exists():
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace all emoji with ASCII
    replacements = {
        '📁': '[FILES]',
        '📊': '[PROCESS]',
        '✅': '[OK]',
        '❌': '[ERR]',
        '⚠️': '[WARN]',
    }

    for emoji, ascii_char in replacements.items():
        content = content.replace(emoji, ascii_char)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Replaced emoji characters in {file_path}")
else:
    print(f"File not found: {file_path}", file=sys.stderr)
    sys.exit(1)
