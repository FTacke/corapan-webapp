#!/usr/bin/env python3
"""
md3-lint.py

Simple lint utility that scans the repo for legacy MD3 tokens and utility classes.
Exits with non-zero if any matches are found (useful for CI) unless --allow-warnings passed.

Writes a small markdown file `docs/md3-template/md3_lint_report_auto.md` when run.
"""
import re
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = {
    'legacy_token_md3': re.compile(r'--md3-[A-Za-z0-9_-]+'),
    'spacing_utilities': re.compile(r'\b(?:m|mt|mb|mx|my)-\d+\b'),
    'mx_auto': re.compile(r'\b(mx-auto|m-auto)\b'),
    'button_contained': re.compile(r'\bmd3-button--contained\b'),
    'card_class': re.compile(r'\bcard\b'),
    'inline_margin_padding': re.compile(r'style\s*=\s*"[^"]*(?:margin|padding)\s*:\s*[^;"]+"', re.I),
}

IGNORED_DIRS = {'.venv', 'node_modules', '.git', 'build', '__pycache__'}


def scan_files(root: Path, include_exts=None):
    include_exts = include_exts or {'.html', '.css', '.js', '.py', '.md', '.jinja'}
    results = []
    for p in root.rglob('*'):
        if any(part in IGNORED_DIRS for part in p.parts):
            continue
        if p.is_file() and p.suffix.lower() in include_exts:
            try:
                content = p.read_text(encoding='utf8', errors='ignore')
            except Exception:
                continue
            for key, pat in PATTERNS.items():
                for m in pat.finditer(content):
                    results.append((key, str(p.relative_to(ROOT)), m.group(0), content.count(m.group(0))))
    return results

def summarize(results):
    by_key = {}
    for key, path, match, count in results:
        by_key.setdefault(key, []).append((path, match))
    return by_key

def write_report(by_key, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', encoding='utf8') as f:
        f.write('# MD3 Lint Auto-Report\n\n')
        if not by_key:
            f.write('No issues found (md3 legacy patterns) — good job.\n')
            return
        for key, items in by_key.items():
            f.write(f'## {key}\n\n')
            for path, match in items:
                f.write(f'- `{path}` — occurrence: `{match}`\n')
            f.write('\n')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=str(ROOT))
    ap.add_argument('--out', default='docs/md3-template/md3_lint_report_auto.md')
    ap.add_argument('--exit-zero', action='store_true', help='Do not exit with non-zero status')
    args = ap.parse_args()

    root = Path(args.root)
    results = scan_files(root)
    grouped = summarize(results)
    write_report(grouped, Path(args.out))

    if grouped and not args.exit_zero:
        print('Legacy MD3 usage found — see:', args.out)
        raise SystemExit(2)
    print('md3-lint: clean (no legacy usages found)' if not grouped else 'md3-lint: report written (legacy usages found)')

if __name__ == '__main__':
    main()
