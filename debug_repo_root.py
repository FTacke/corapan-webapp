#!/usr/bin/env python3
from pathlib import Path

script_dir = Path(r'C:\dev\corapan-webapp\LOKAL\_0_json')
current = script_dir

for i in range(10):
    print(f'{i}: {current}')
    print(f'   .git: {(current / ".git").exists()}')
    print(f'   pyproject.toml: {(current / "pyproject.toml").exists()}')
    print(f'   src: {(current / "src").is_dir()}')
    print(f'   templates: {(current / "templates").is_dir()}')
    
    parent = current.parent
    if parent == current:
        print('Reached root')
        break
    current = parent
