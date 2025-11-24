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
