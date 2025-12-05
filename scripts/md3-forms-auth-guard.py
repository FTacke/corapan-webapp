#!/usr/bin/env python3
"""
md3-forms-auth-guard.py

Quick guard for Forms / Auth / Dialog templates.
Scans templates/_md3_skeletons and templates/auth and reports issues such as:
 - inline styles (style="...")
 - legacy checkbox markup (checkbox input without md3-checkbox pattern)
 - incomplete md3-outlined-textfield blocks
 - incomplete md3-dialog blocks
 - legacy/btn button classes

Exit code 2 when issues found. Output includes file path, line number and code snippet.
"""
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

TARGET_DIRS = [ROOT / 'templates' / '_md3_skeletons', ROOT / 'templates' / 'auth']
IGNORED_DIRS = {'.venv', 'node_modules', '.git', 'build', '__pycache__'}

INLINE_STYLE_RE = re.compile(r'style\s*=\s*("[^"]*"|\'[^\']*\')', re.I)
CHECKBOX_RE = re.compile(r'<input[^>]+type\s*=\s*"checkbox"', re.I)
# Accept both md3-checkbox and md3-switch as valid MD3 patterns
MD3_CHECKBOX_PRESENT_RE = re.compile(r'md3-checkbox|md3-switch')
OUTLINED_FIELD_RE = re.compile(r'<(?P<tag>\w+)[^>]*class\s*=\s*"[^"]*md3-outlined-textfield[^"]*"[^>]*>(?P<body>.*?)</(?P=tag)>', re.I | re.S)
OUTLINED_INPUT_RE = re.compile(r'md3-outlined-textfield__input')
OUTLINED_LABEL_RE = re.compile(r'md3-outlined-textfield__label')
OUTLINED_OUTLINE_RE = re.compile(r'md3-outlined-textfield__outline')
DIALOG_RE = re.compile(r'class\s*=\s*"[^"]*md3-dialog[^"]*"', re.I)
DIALOG_SURFACE_RE = re.compile(r'md3-dialog__surface|md3-dialog__title', re.I)
# Only match legacy button CSS classes in class attributes, not JS variable names
# Match patterns like class="btn-primary" or class="btn_submit" but NOT JS vars like 'btn'
LEGACY_BUTTON_RE = re.compile(r'class\s*=\s*["\'][^"\']*\b(btn-|legacy-button|btn_)[^"\']*["\']', re.I)


def find_files():
    files = []
    for t in TARGET_DIRS:
        if not t.exists():
            continue
        for p in t.rglob('*.html'):
            if any(part in IGNORED_DIRS for part in p.parts):
                continue
            if p.is_file():
                files.append(p)
    return files


def report_issue(results, path, lineno, snippet, code):
    results.append((path, lineno, snippet.strip(), code))


def scan_file(path: Path):
    results = []
    try:
        text = path.read_text(encoding='utf8', errors='ignore')
    except Exception as e:
        report_issue(results, str(path), 0, f'Unable to read file: {e}', 'read_error')
        return results

    # Inline styles
    for m in INLINE_STYLE_RE.finditer(text):
        snippet = text[max(0, m.start()-40):m.end()+40].splitlines()[0]
        lineno = text[:m.start()].count('\n') + 1
        report_issue(results, str(path), lineno, snippet, 'inline_style')

    # Legacy checkbox usage: any checkbox input without md3-checkbox in the same file
    if CHECKBOX_RE.search(text) and not MD3_CHECKBOX_PRESENT_RE.search(text):
        for m in CHECKBOX_RE.finditer(text):
            snippet = text[max(0, m.start()-40):m.end()+40].splitlines()[0]
            lineno = text[:m.start()].count('\n') + 1
            report_issue(results, str(path), lineno, snippet, 'legacy_checkbox')

    # md3-outlined-textfield completeness checks
    # Find md3-outlined-textfield blocks and try to capture the whole element body
    # match only elements that contain the md3-outlined-textfield token (avoid matching __input/__outline child classes)
    for m in re.finditer(r'<(?P<tag>\w+)[^>]*class\s*=\s*"[^"]*\bmd3-outlined-textfield\b[^"]*"[^>]*>', text, re.I):
        tag = m.group('tag')
        # locate matching closing tag by scanning and balancing nested tags of same type
        search_re = re.compile(r'<(/?%s)\b[^>]*>' % re.escape(tag), re.I)
        start_pos = m.end()
        depth = 1
        end_pos = start_pos
        for mm in search_re.finditer(text, start_pos):
            if mm.group(1).startswith('/'):
                depth -= 1
            else:
                depth += 1
            end_pos = mm.end()
            if depth == 0:
                break
        body = text[start_pos:end_pos] if depth == 0 else text[start_pos:start_pos+600]
        has_input = bool(OUTLINED_INPUT_RE.search(body))
        has_label = bool(OUTLINED_LABEL_RE.search(body))
        has_outline = bool(OUTLINED_OUTLINE_RE.search(body))
        if not (has_input and has_label and has_outline):
            lineno = text[:m.start()].count('\n') + 1
            snippet = (text[m.start():end_pos][:160].replace('\n', ' '))
            report_issue(results, str(path), lineno, snippet, 'outlined_textfield_incomplete')

    # md3-dialog completeness
    if DIALOG_RE.search(text) and not DIALOG_SURFACE_RE.search(text):
        m = DIALOG_RE.search(text)
        lineno = text[:m.start()].count('\n') + 1
        snippet = text[m.start():m.start()+200].splitlines()[0]
        report_issue(results, str(path), lineno, snippet, 'dialog_missing_surface_or_title')

    # legacy button classes
    for m in LEGACY_BUTTON_RE.finditer(text):
        lineno = text[:m.start()].count('\n') + 1
        snippet = text[max(0, m.start()-40):m.end()+40].splitlines()[0]
        report_issue(results, str(path), lineno, snippet, 'legacy_button_class')

    return results


def main():
    files = find_files()
    issues = []
    for f in files:
        issues += scan_file(f)

    if not issues:
        print('md3-forms-auth-guard: OK — no issues found')
        return 0

    # Print a clear issue list
    print('md3-forms-auth-guard: Issues found')
    for path, ln, snippet, code in issues:
        print(f'[{code}] {path}:{ln} — {snippet}')

    # Non-zero exit for CI break
    return 2


if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
#!/usr/bin/env python3
"""
md3-forms-auth-guard.py

Guard-Skript für MD3 Forms / Auth / Dialog:
- prüft Canonical Outlined Textfields
- prüft Canonical Dialog-Markup
- prüft Verbot bestimmter Muster (Legacy-Checkbox, Inline-Styles etc.)
"""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

# Welche Verzeichnisse/Dateien werden geprüft?
HTML_PATHS = [
    ROOT / "templates" / "auth",
    ROOT / "templates" / "_md3_skeletons",
    ROOT / "templates" / "admin",
]

# Einfache Regex-Patterns für bekannte Anti-Patterns
INLINE_STYLE_RE = re.compile(r'style\s*=')
LEGACY_CHECKBOX_RE = re.compile(r'<input[^>]+type=["\']checkbox["\'][^>]*(class=["\'][^"\']*legacy-checkbox[^"\']*["\'])?', re.IGNORECASE)
ALT_TEXTFIELD_RE = re.compile(r'<input[^>]+type=["\'](?:text|email|password)["\'][^>]*>(?!\s*</div\s*>)', re.IGNORECASE)

# Canonical-Signaturen
OUTLINED_TEXTFIELD_SIGNATURES = [
    re.compile(r'class=["\'][^"\']*md3-outlined-textfield[^"\']*["\']', re.IGNORECASE),
    re.compile(r'class=["\'][^"\']*md3-outlined-textfield__input[^"\']*["\']', re.IGNORECASE),
    re.compile(r'class=["\'][^"\']*md3-outlined-textfield__label[^"\']*["\']', re.IGNORECASE),
    re.compile(r'class=["\'][^"\']*md3-outlined-textfield__outline[^"\']*["\']', re.IGNORECASE),
]

DIALOG_SIGNATURES = [
    re.compile(r'<dialog[^>]+class=["\'][^"\']*md3-dialog[^"\']*["\']', re.IGNORECASE),
    re.compile(r'class=["\'][^"\']*md3-dialog__surface[^"\']*["\']', re.IGNORECASE),
    re.compile(r'class=["\'][^"\']*md3-dialog__title[^"\']*["\']', re.IGNORECASE),
    re.compile(r'class=["\'][^"\']*md3-dialog__content[^"\']*["\']', re.IGNORECASE),
    re.compile(r'class=["\'][^"\']*md3-dialog__actions[^"\']*["\']', re.IGNORECASE),
]

BUTTON_FORBIDDEN_RE = re.compile(r'<button[^>]+class=["\'][^"\']*(btn-|btn-primary|btn-secondary)[^"\']*["\']', re.IGNORECASE)


def iter_html_files():
    for base in HTML_PATHS:
        if not base.exists():
            continue
        for path in base.rglob("*.html"):
            yield path


def check_inline_styles(path, text, errors):
    for m in INLINE_STYLE_RE.finditer(text):
        errors.append((path, "INLINE_STYLE", "Inline style in HTML ist verboten (MD3-Komponenten)."))


def check_legacy_checkbox(path, text, errors):
    if LEGACY_CHECKBOX_RE.search(text):
        errors.append((path, "LEGACY_CHECKBOX", 'Legacy-Checkbox-Markup gefunden. Verwende <label class="md3-checkbox">…'))


def check_canonical_textfields(path, text, errors):
    if 'md3-outlined-textfield' in text:
        for sig in OUTLINED_TEXTFIELD_SIGNATURES:
            if not sig.search(text):
                errors.append((path, "TEXTFIELD_INCOMPLETE", "md3-outlined-textfield ohne vollständiges Canonical-Markup."))


def check_dialogs(path, text, errors):
    if 'md3-dialog' in text:
        for sig in DIALOG_SIGNATURES:
            if not sig.search(text):
                errors.append((path, "DIALOG_INCOMPLETE", "md3-dialog ohne vollständige Canonical-Struktur."))


def check_buttons(path, text, errors):
    for m in BUTTON_FORBIDDEN_RE.finditer(text):
        errors.append((path, "BUTTON_LEGACY_CLASS", "Legacy-Button-Klasse gefunden (btn-…). Nutze md3-button*."))


def main() -> int:
    errors = []

    for path in iter_html_files():
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        check_inline_styles(path, text, errors)
        check_legacy_checkbox(path, text, errors)
        check_canonical_textfields(path, text, errors)
        check_dialogs(path, text, errors)
        check_buttons(path, text, errors)

    if errors:
        print("MD3 Forms/Auth Guard: Fehler gefunden:")
        for path, code, msg in errors:
            print(f"- [{code}] {path}: {msg}")
        return 1

    print("MD3 Forms/Auth Guard: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
