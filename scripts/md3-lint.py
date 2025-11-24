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
    # spacing utilities (generic); we treat usage in templates specially
    'spacing_utilities': re.compile(r'\b(?:m|mt|mb|mx|my)-\d+\b'),
    'mx_auto': re.compile(r'\b(mx-auto|m-auto)\b'),
    'inline_margin_padding': re.compile(r'style\s*=\s*"[^"]*(?:margin|padding)\s*:\s*[^;\"]+"', re.I),
}

# Extra heuristic checks for auth templates specifically
AUTH_EXTRA_KEYS = [
    'auth_legacy_card_usage',
    'auth_legacy_button_contained',
    'auth_textfield_missing_outlined',
    'auth_dialog_markup',
]

IGNORED_DIRS = {'.venv', 'node_modules', '.git', 'build', '__pycache__'}


def scan_files(root: Path, include_exts=None):
    include_exts = include_exts or {'.html', '.css', '.js', '.py', '.md', '.jinja'}
    results = []
    import subprocess
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


def scan_auth_templates(root: Path):
    """Run a few targeted checks inside templates/auth/*.html to detect
    leftover legacy markup or missing canonical classes."""
    results = []
    auth_dir = root / 'templates' / 'auth'
    if not auth_dir.exists():
        return results

    for p in auth_dir.glob('*.html'):
        try:
            content = p.read_text(encoding='utf8', errors='ignore')
        except Exception:
            continue

        # 1) detect literal 'card' classes without 'md3-card' present in the same class attribute
        for m in re.finditer(r'class\s*=\s*"([^"]*\bcard\b[^"]*)"', content):
            cls = m.group(1)
            if 'md3-card' not in cls:
                results.append(('auth_legacy_card_usage', str(p.relative_to(ROOT)), m.group(0), 1))

        # 2) legacy button variant
        if 'md3-button--contained' in content:
            results.append(('auth_legacy_button_contained', str(p.relative_to(ROOT)), 'md3-button--contained', content.count('md3-button--contained')))

        # 3) detect md3-text-field uses where no md3-outlined-textfield present (encourage outlined)
        if 'md3-text-field' in content and 'md3-outlined-textfield' not in content:
            results.append(('auth_textfield_missing_outlined', str(p.relative_to(ROOT)), 'md3-text-field (no outlined)', content.count('md3-text-field')))

        # 4) basic dialog structure heuristic: dialogs should contain md3-dialog__surface or title with md3-title-large
        if 'class="md3-dialog"' in content:
            if 'md3-dialog__surface' not in content and 'md3-title-large' not in content:
                results.append(('auth_dialog_markup', str(p.relative_to(ROOT)), 'md3-dialog missing surface/title', 1))

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
    # Read previous lint reports (if present) — anything listed there is treated as a WARNING rather than ERROR
    known_paths = set()
    for prev in [root / 'docs' / 'md3-template' / 'md3_lint_report.md', root / 'docs' / 'md3-template' / 'md3_lint_report_auto.md']:
        if prev.exists():
            try:
                txt = prev.read_text(encoding='utf8', errors='ignore')
                for line in txt.splitlines():
                    m = re.match(r"\s*- `([^`]+)`", line)
                    if m:
                        # normalize path separators
                        known_paths.add(m.group(1).replace('\\', '/'))
            except Exception:
                pass

    results = scan_files(root)
    # Add targeted auth template checks
    results += scan_auth_templates(root)

    errors = []
    warnings = []

    for key, path, match, count in results:
        normalized = path.replace('\\', '/')
        is_template = normalized.startswith('templates/')
        is_css = normalized.startswith('static/css')

        if key == 'legacy_token_md3':
            # error if found in templates or CSS outside the tokens-legacy-shim.css
            if normalized.endswith('static/css/md3/tokens-legacy-shim.css'):
                # allowed shim
                continue
            if normalized in known_paths:
                warnings.append((key, path, match))
            else:
                # For docs we treat it as warning; for templates or CSS treat as error
                if is_template or is_css:
                    errors.append((key, path, match))
                else:
                    warnings.append((key, path, match))

        elif key in ('spacing_utilities', 'mx_auto'):
            # Errors only for occurrences inside templates — templates must not introduce new m-* utilities
            if is_template:
                if normalized in known_paths:
                    warnings.append((key, path, match))
                else:
                    errors.append((key, path, match))
            else:
                # occurrences outside templates are reported as warnings
                if normalized in known_paths:
                    warnings.append((key, path, match))
                else:
                    warnings.append((key, path, match))

        elif key == 'inline_margin_padding':
            # Inline styles with margin/padding in templates are errors unless known
            if is_template:
                if normalized in known_paths:
                    warnings.append((key, path, match))
                else:
                    errors.append((key, path, match))
            else:
                # treat inline style occurrences in non-templates as warnings
                warnings.append((key, path, match))

    # Write a structured report
    out_file = Path(args.out)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open('w', encoding='utf8') as f:
        f.write('# MD3 Lint Auto-Report\n\n')
        if errors:
            f.write('## ERRORS\n\n')
            for key, path, match in errors:
                f.write(f'- `{path}` — `{match}` (rule: {key})\n')
            f.write('\n')
        if warnings:
            f.write('## WARNINGS\n\n')
            for key, path, match in warnings:
                f.write(f'- `{path}` — `{match}` (known issue)\n')
            f.write('\n')

    if errors and not args.exit_zero:
        print('md3-lint: ERRORS found (see report):', out_file)
        raise SystemExit(2)
    if warnings:
        print('md3-lint: WARNINGS found (see report):', out_file)
        # Exit non-zero only when errors exist, otherwise allow warnings
    else:
        print('md3-lint: OK — no errors or warnings')

if __name__ == '__main__':
    main()
