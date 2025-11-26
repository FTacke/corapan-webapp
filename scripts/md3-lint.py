#!/usr/bin/env python3
"""
md3-lint.py

Comprehensive MD3 structural compliance linter for CO.RA.PAN webapp.
Validates HTML templates against MD3 canonical structures (Card, Dialog, Sheet, Page).

Features:
- Structural validation (dialog/card/sheet components)
- ARIA compliance checks
- Legacy token/class detection
- Form field inventory
- JSON and Markdown reports

Usage:
    python scripts/md3-lint.py                           # Full scan
    python scripts/md3-lint.py --focus templates/auth    # Focus on auth templates
    python scripts/md3-lint.py --json-out report.json    # JSON output
    python scripts/md3-lint.py --exit-zero               # Allow errors (CI)

See: docs/md3/40_tooling_and_ci.md
"""
import re
import json
import sys
import io
from pathlib import Path
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Set
from datetime import datetime

# Fix Windows console encoding for emoji output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[1]

# ─────────────────────────────────────────────────────────────────────────────
# Rule Definitions
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LintIssue:
    rule_id: str
    severity: str  # ERROR, WARNING, INFO
    file: str
    line: int
    message: str
    match: str = ""
    
    def to_dict(self):
        return asdict(self)


# Rule registry: rule_id -> (severity, description)
RULES = {
    # Dialog structure rules
    "MD3-DIALOG-001": ("ERROR", "Dialog missing md3-dialog__surface"),
    "MD3-DIALOG-002": ("ERROR", "Dialog missing md3-dialog__content"),
    "MD3-DIALOG-003": ("ERROR", "Dialog missing md3-dialog__actions"),
    "MD3-DIALOG-004": ("ERROR", "Dialog missing md3-dialog__title"),
    "MD3-DIALOG-005": ("ERROR", "Dialog missing aria-modal=\"true\""),
    "MD3-DIALOG-006": ("ERROR", "Dialog missing aria-labelledby or aria-label"),
    
    # Card structure rules
    "MD3-CARD-001": ("ERROR", "Card missing md3-card__content"),
    "MD3-CARD-002": ("ERROR", "Card has actions/footer before content"),
    
    # Hero structure rules (new)
    "MD3-HERO-001": ("ERROR", "Hero missing canonical structure (md3-hero--card md3-hero__container)"),
    "MD3-HERO-002": ("ERROR", "Hero icon using <span> directly (use <div class='md3-hero__icon'><span>)"),
    "MD3-HERO-003": ("WARNING", "Hero eyebrow using <span> instead of <p>"),
    "MD3-HERO-004": ("WARNING", "Hero title missing md3-headline-medium class"),
    
    # Form rules
    "MD3-FORM-001": ("ERROR", "Submit button outside form without form attribute"),
    
    # Alert & Field Message rules (NEW)
    "MD3-ALERT-001": ("ERROR", "role=\"alert\" without .md3-alert or .md3-field-error"),
    "MD3-ALERT-002": ("WARNING", "Legacy alert class without MD3 equivalent"),
    "MD3-ALERT-003": ("WARNING", "Alert missing title (.md3-alert__title element)"),
    "MD3-ALERT-004": ("ERROR", "Error alert with wrong role (must be role=\"alert\")"),
    "MD3-ALERT-005": ("ERROR", "Alert icon class order wrong (material-symbols-rounded must come first)"),
    "MD3-FIELD-ERROR-001": ("WARNING", "Error text not directly after md3-outlined-textfield block"),
    "MD3-FIELD-ERROR-002": ("WARNING", "Input with aria-invalid=\"true\" without linked md3-field-error"),
    "MD3-FIELD-SUPPORT-001": ("INFO", "Field support/error inventory entry"),
    
    # Legacy patterns (ERROR)
    "MD3-LEGACY-001": ("ERROR", "Legacy card class usage (use md3-card)"),
    "MD3-LEGACY-002": ("ERROR", "Legacy --md3-* token (use --md-sys-* or --space-*)"),
    "MD3-LEGACY-003": ("ERROR", "Legacy md3-button--contained (use --filled)"),
    "MD3-LEGACY-004": ("ERROR", "Legacy md3-login-sheet (use md3-sheet)"),
    
    # CSS rules (WARNINGS - these are refinements, not structural issues)
    "MD3-CSS-001": ("WARNING", "Hex color in md3 components CSS (use tokens)"),
    "MD3-CSS-002": ("WARNING", "!important in md3 components CSS"),
    "MD3-CSS-003": ("ERROR", "Legacy selector in md3 components CSS"),
    
    # Warnings
    "MD3-SPACING-001": ("WARNING", "Inline pixel spacing (use --space-* tokens)"),
    "MD3-SPACING-002": ("WARNING", "Bootstrap spacing utility (m-*, mt-*, etc.)"),
    "MD3-TEXTFIELD-001": ("WARNING", "Non-standard textfield (use md3-outlined-textfield)"),
    "MD3-HEADER-001": ("WARNING", "Complex content in card/dialog header"),
    
    # Info (inventory)
    "MD3-INPUT-001": ("INFO", "Input field inventory entry"),
    
    # DataTables exception
    "MD3-DATATABLES-001": ("INFO", "MD3 violation in DataTables area (ignored)"),
}

# Regex patterns
PATTERNS = {
    'legacy_token': re.compile(r'--md3-[A-Za-z0-9_-]+'),
    'legacy_contained': re.compile(r'md3-button--contained'),
    'legacy_login_sheet': re.compile(r'md3-login-sheet'),
    'spacing_utilities': re.compile(r'\b(?:m|mt|mb|ml|mr|mx|my|p|pt|pb|pl|pr|px|py)-\d+\b'),
    'mx_auto': re.compile(r'\b(mx-auto|m-auto)\b'),
    'inline_spacing': re.compile(r'style\s*=\s*"[^"]*(?:margin|padding)\s*:\s*\d+px[^"]*"', re.I),
    'hex_color': re.compile(r'#[0-9a-fA-F]{3,6}\b'),
    'important': re.compile(r'!important'),
    'legacy_selector': re.compile(r'\.legacy-(?:checkbox|button|form)'),
}

# Exceptions
DATATABLES_PATHS = {'templates/search/advanced'}
DATATABLES_CSS = {'static/css/md3/components/advanced-search.css'}  # DataTables styling
NON_CRITICAL_PATHS = {'LOKAL/', 'docs/', 'test-results/'}  # Design previews, docs, test outputs
LEGACY_MIGRATION_PATHS = {'static/css/player-mobile.css'}  # Player CSS (special zone)
SPECIAL_CSS_ZONE = {'static/css/player-mobile.css', 'static/css/editor.css', 'static/css/special/'}  # Special CSS zone
# Player/Editor pages excluded from structural changes
EXCLUDED_PAGES = {
    'templates/pages/player.html',
    'templates/pages/editor.html',
    'templates/pages/index.html',  # Homepage uses special card layout
}
ALLOWED_LEGACY_TOKEN_FILES = {'static/css/md3/tokens-legacy-shim.css'}
IGNORED_DIRS = {'.venv', 'node_modules', '.git', 'build', '__pycache__', 'data'}
# Pages excluded from Hero validation (login page has no Hero by design)
NO_HERO_PAGES = {'templates/auth/login.html'}


# ─────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_line_number(content: str, pos: int) -> int:
    """Return 1-based line number for a position in content."""
    return content[:pos].count('\n') + 1


def is_datatables_path(path: str) -> bool:
    """Check if path is in DataTables exception area."""
    normalized = path.replace('\\', '/')
    if any(normalized.startswith(dt) for dt in DATATABLES_PATHS):
        return True
    if normalized in DATATABLES_CSS:
        return True
    return False


def is_non_critical_path(path: str) -> bool:
    """Check if path is in non-critical area (LOKAL, docs, etc.)."""
    normalized = path.replace('\\', '/')
    return any(normalized.startswith(nc) for nc in NON_CRITICAL_PATHS)


def is_legacy_migration_path(path: str) -> bool:
    """Check if path is in legacy migration area (special CSS zone)."""
    normalized = path.replace('\\', '/')
    if normalized in LEGACY_MIGRATION_PATHS:
        return True
    return any(normalized.startswith(lm) for lm in LEGACY_MIGRATION_PATHS)


def is_special_css_zone(path: str) -> bool:
    """Check if path is in special CSS zone (player, editor - excluded from token checks)."""
    normalized = path.replace('\\', '/')
    return any(normalized.startswith(z.rstrip('/')) for z in SPECIAL_CSS_ZONE)


def should_skip_file(path: Path) -> bool:
    """Check if file should be skipped."""
    return any(part in IGNORED_DIRS for part in path.parts)


# ─────────────────────────────────────────────────────────────────────────────
# Structural Validators
# ─────────────────────────────────────────────────────────────────────────────

def lint_dialog_structure(content: str, rel_path: str) -> List[LintIssue]:
    """Validate MD3 dialog structure."""
    issues = []
    
    # Find all md3-dialog elements
    dialog_pattern = re.compile(r'<(?:dialog|div)[^>]*class\s*=\s*"[^"]*\bmd3-dialog\b[^"]*"[^>]*>', re.I)
    
    for match in dialog_pattern.finditer(content):
        line = get_line_number(content, match.start())
        tag = match.group(0)
        
        # Get the dialog block - find closing tag for better accuracy
        start_pos = match.start()
        # Determine if it's a <dialog> or <div>
        is_dialog_tag = tag.lower().startswith('<dialog')
        closing_tag = '</dialog>' if is_dialog_tag else '</div>'
        
        # Find the next closing tag (simplified - may not be perfect for nested divs)
        # Use a larger search window for complex dialogs with forms
        search_end = min(start_pos + 5000, len(content))
        dialog_block = content[start_pos:search_end]
        
        # Try to find the actual closing tag for more accuracy
        close_pos = dialog_block.find(closing_tag)
        if close_pos > 0:
            dialog_block = dialog_block[:close_pos + len(closing_tag)]
        
        # Check for required children
        if 'md3-dialog__surface' not in dialog_block:
            issues.append(LintIssue("MD3-DIALOG-001", "ERROR", rel_path, line, 
                                    "Dialog missing md3-dialog__surface", tag[:60]))
        
        if 'md3-dialog__content' not in dialog_block:
            issues.append(LintIssue("MD3-DIALOG-002", "ERROR", rel_path, line,
                                    "Dialog missing md3-dialog__content", tag[:60]))
        
        if 'md3-dialog__actions' not in dialog_block:
            issues.append(LintIssue("MD3-DIALOG-003", "ERROR", rel_path, line,
                                    "Dialog missing md3-dialog__actions", tag[:60]))
        
        if 'md3-dialog__title' not in dialog_block and 'md3-title-large' not in dialog_block:
            issues.append(LintIssue("MD3-DIALOG-004", "ERROR", rel_path, line,
                                    "Dialog missing md3-dialog__title", tag[:60]))
        
        # ARIA checks
        if 'aria-modal="true"' not in tag and 'aria-modal=\'true\'' not in tag:
            issues.append(LintIssue("MD3-DIALOG-005", "ERROR", rel_path, line,
                                    "Dialog missing aria-modal=\"true\"", tag[:60]))
        
        if 'aria-labelledby' not in tag and 'aria-label' not in tag:
            issues.append(LintIssue("MD3-DIALOG-006", "ERROR", rel_path, line,
                                    "Dialog missing aria-labelledby or aria-label", tag[:60]))
    
    return issues


def lint_card_structure(content: str, rel_path: str) -> List[LintIssue]:
    """Validate MD3 card structure."""
    issues = []
    
    # Find all md3-card elements
    card_pattern = re.compile(r'<(?:article|div|section)[^>]*class\s*=\s*"[^"]*\bmd3-card\b[^"]*"[^>]*>', re.I)
    
    for match in card_pattern.finditer(content):
        line = get_line_number(content, match.start())
        tag = match.group(0)
        
        start_pos = match.start()
        block_end = min(start_pos + 3000, len(content))
        card_block = content[start_pos:block_end]
        
        # Check for md3-card__content (or variant like md3-metric-card__content)
        has_content = 'md3-card__content' in card_block or '__content' in card_block
        if not has_content:
            issues.append(LintIssue("MD3-CARD-001", "ERROR", rel_path, line,
                                    "Card missing md3-card__content", tag[:60]))
        
        # Check order: actions/footer should come after content
        content_pos = card_block.find('md3-card__content')
        if content_pos == -1:
            content_pos = card_block.find('__content')  # Accept variant
        actions_pos = card_block.find('md3-card__actions')
        footer_pos = card_block.find('md3-card__footer')
        
        if content_pos > 0:
            if actions_pos > 0 and actions_pos < content_pos:
                issues.append(LintIssue("MD3-CARD-002", "ERROR", rel_path, line,
                                        "Card has __actions before __content", ""))
            if footer_pos > 0 and footer_pos < content_pos:
                issues.append(LintIssue("MD3-CARD-002", "ERROR", rel_path, line,
                                        "Card has __footer before __content", ""))
    
    return issues


def lint_hero_structure(content: str, rel_path: str) -> List[LintIssue]:
    """Validate MD3 Hero canonical structure.
    
    Canonical Hero pattern:
    <header class="md3-page__header">
      <div class="md3-hero md3-hero--card md3-hero__container">
        <div class="md3-hero__icon" aria-hidden="true"><span class="material-symbols-rounded">ICON</span></div>
        <div class="md3-hero__content">
          <p class="md3-body-small md3-hero__eyebrow">EYEBROW</p>
          <h1 class="md3-headline-medium md3-hero__title">TITLE</h1>
        </div>
      </div>
    </header>
    """
    issues = []
    
    # Skip pages that don't need Hero
    if rel_path.replace('\\', '/') in NO_HERO_PAGES:
        return issues
    
    # Find all md3-hero elements
    hero_pattern = re.compile(r'<(?:div|section)[^>]*class\s*=\s*"([^"]*\bmd3-hero\b[^"]*)"[^>]*>', re.I)
    
    for match in hero_pattern.finditer(content):
        line = get_line_number(content, match.start())
        tag = match.group(0)
        classes = match.group(1)
        
        start_pos = match.start()
        block_end = min(start_pos + 2000, len(content))
        hero_block = content[start_pos:block_end]
        
        # Check for canonical classes
        if 'md3-hero--card' not in classes or 'md3-hero__container' not in classes:
            # Check for old patterns
            if 'md3-hero--container' in classes or 'md3-hero--with-icon' in classes:
                issues.append(LintIssue("MD3-HERO-001", "ERROR", rel_path, line,
                                        "Hero using old pattern (md3-hero--container/--with-icon), use md3-hero--card md3-hero__container",
                                        tag[:80]))
        
        # Check icon structure: should be <div class="md3-hero__icon"><span>...</span></div>
        # Bad: <span class="md3-hero__icon">...</span> or <span class="material-symbols-rounded md3-hero__icon">
        bad_icon_patterns = [
            re.compile(r'<span[^>]*class\s*=\s*"[^"]*md3-hero__icon[^"]*"[^>]*>', re.I),
            re.compile(r'<span[^>]*class\s*=\s*"[^"]*material-symbols[^"]*md3-hero__icon[^"]*"[^>]*>', re.I),
        ]
        for bad_pattern in bad_icon_patterns:
            if bad_pattern.search(hero_block):
                issues.append(LintIssue("MD3-HERO-002", "ERROR", rel_path, line,
                                        "Hero icon using <span> directly, should use <div class='md3-hero__icon'><span>...</span></div>",
                                        ""))
                break
        
        # Check eyebrow: should use <p> not <span>
        eyebrow_span = re.search(r'<span[^>]*class\s*=\s*"[^"]*md3-hero__eyebrow[^"]*"[^>]*>', hero_block, re.I)
        if eyebrow_span:
            issues.append(LintIssue("MD3-HERO-003", "WARNING", rel_path, line,
                                    "Hero eyebrow using <span>, should use <p class='md3-body-small md3-hero__eyebrow'>",
                                    ""))
        
        # Check title has md3-headline-medium
        title_match = re.search(r'<h1[^>]*class\s*=\s*"([^"]*md3-hero__title[^"]*)"[^>]*>', hero_block, re.I)
        if title_match:
            title_classes = title_match.group(1)
            if 'md3-headline-medium' not in title_classes:
                issues.append(LintIssue("MD3-HERO-004", "WARNING", rel_path, line,
                                        "Hero title missing md3-headline-medium class",
                                        ""))
    
    return issues


def lint_form_structure(content: str, rel_path: str) -> List[LintIssue]:
    """Validate form and submit button structure."""
    issues = []
    
    # Find submit buttons
    submit_pattern = re.compile(r'<button[^>]*type\s*=\s*["\']submit["\'][^>]*>', re.I)
    form_pattern = re.compile(r'<form[^>]*>', re.I)
    
    forms = list(form_pattern.finditer(content))
    
    for match in submit_pattern.finditer(content):
        line = get_line_number(content, match.start())
        tag = match.group(0)
        
        # Check if button has form attribute
        if 'form=' in tag.lower():
            continue  # OK, explicitly linked
        
        # Check if button is inside a form
        pos = match.start()
        inside_form = False
        
        for form_match in forms:
            form_start = form_match.start()
            # Find closing </form>
            form_close = content.find('</form>', form_start)
            if form_close == -1:
                form_close = len(content)
            
            if form_start < pos < form_close:
                inside_form = True
                break
        
        if not inside_form:
            issues.append(LintIssue("MD3-FORM-001", "ERROR", rel_path, line,
                                    "Submit button outside form without form=\"id\" attribute",
                                    tag[:80]))
    
    return issues


def lint_legacy_patterns(content: str, rel_path: str) -> List[LintIssue]:
    """Check for legacy class and token usage."""
    issues = []
    
    # Legacy card class (class="card" without md3-card)
    # Matches: card, card-body, card-header, etc. but NOT md3-card, md3-hero--card, md3-metric-card, md3-admin-card
    for match in re.finditer(r'class\s*=\s*"([^"]*)"', content):
        cls = match.group(1)
        # Check for standalone 'card' class or Bootstrap card classes (card-body, card-header)
        card_pattern = re.compile(r'\bcard(?:-(?:body|header|footer|title))?\b')
        if card_pattern.search(cls):
            # Skip if it's an md3-* card pattern (valid)
            if 'md3-card' in cls or 'md3-hero--card' in cls or 'md3-metric-card' in cls or 'md3-admin-card' in cls:
                continue
            line = get_line_number(content, match.start())
            issues.append(LintIssue("MD3-LEGACY-001", "ERROR", rel_path, line,
                                    "Legacy card class usage (use md3-card)", match.group(0)[:60]))
    
    # Legacy --md3-* tokens
    for match in PATTERNS['legacy_token'].finditer(content):
        line = get_line_number(content, match.start())
        issues.append(LintIssue("MD3-LEGACY-002", "ERROR", rel_path, line,
                                f"Legacy token {match.group(0)} (use --md-sys-* or --space-*)",
                                match.group(0)))
    
    # Legacy md3-button--contained
    for match in PATTERNS['legacy_contained'].finditer(content):
        line = get_line_number(content, match.start())
        issues.append(LintIssue("MD3-LEGACY-003", "ERROR", rel_path, line,
                                "Legacy md3-button--contained (use md3-button--filled)",
                                match.group(0)))
    
    # Legacy md3-login-sheet
    for match in PATTERNS['legacy_login_sheet'].finditer(content):
        line = get_line_number(content, match.start())
        issues.append(LintIssue("MD3-LEGACY-004", "ERROR", rel_path, line,
                                "Legacy md3-login-sheet (use md3-sheet)",
                                match.group(0)))
    
    return issues


def lint_spacing_patterns(content: str, rel_path: str) -> List[LintIssue]:
    """Check for inline spacing and bootstrap utilities."""
    issues = []
    
    # Inline pixel spacing
    for match in PATTERNS['inline_spacing'].finditer(content):
        line = get_line_number(content, match.start())
        issues.append(LintIssue("MD3-SPACING-001", "WARNING", rel_path, line,
                                "Inline pixel spacing (use --space-* tokens)",
                                match.group(0)[:60]))
    
    # Bootstrap spacing utilities
    for match in PATTERNS['spacing_utilities'].finditer(content):
        line = get_line_number(content, match.start())
        issues.append(LintIssue("MD3-SPACING-002", "WARNING", rel_path, line,
                                f"Bootstrap spacing utility {match.group(0)}",
                                match.group(0)))
    
    for match in PATTERNS['mx_auto'].finditer(content):
        line = get_line_number(content, match.start())
        issues.append(LintIssue("MD3-SPACING-002", "WARNING", rel_path, line,
                                f"Bootstrap utility {match.group(0)}",
                                match.group(0)))
    
    return issues


def lint_textfield_patterns(content: str, rel_path: str) -> List[LintIssue]:
    """Check for non-standard textfield usage."""
    issues = []
    
    if 'md3-text-field' in content and 'md3-outlined-textfield' not in content:
        line = 1
        issues.append(LintIssue("MD3-TEXTFIELD-001", "WARNING", rel_path, line,
                                "Using md3-text-field (prefer md3-outlined-textfield)",
                                "md3-text-field"))
    
    return issues


def lint_alert_patterns(content: str, rel_path: str) -> List[LintIssue]:
    """Check for MD3 alert and field message compliance.
    
    Rules:
    - MD3-ALERT-001: role="alert" without .md3-alert or .md3-field-error
    - MD3-ALERT-002: Legacy alert classes without MD3 equivalent
    - MD3-ALERT-003: Alert missing title (.md3-alert__title element)
    - MD3-ALERT-004: Error alert with wrong role (must be role="alert")
    - MD3-ALERT-005: Alert icon class order wrong (material-symbols-rounded must come first)
    - MD3-FIELD-ERROR-001: Error text not directly after textfield
    - MD3-FIELD-ERROR-002: Input with aria-invalid without linked error
    """
    issues = []
    
    # MD3-ALERT-001: role="alert" without proper MD3 class
    role_alert_pattern = re.compile(r'<[^>]*role\s*=\s*["\']alert["\'][^>]*>', re.I)
    for match in role_alert_pattern.finditer(content):
        tag = match.group(0)
        line = get_line_number(content, match.start())
        
        # Check if it has md3-alert or md3-field-error class
        has_md3_class = 'md3-alert' in tag or 'md3-field-error' in tag
        if not has_md3_class:
            issues.append(LintIssue("MD3-ALERT-001", "ERROR", rel_path, line,
                                    "role=\"alert\" without .md3-alert or .md3-field-error class",
                                    tag[:80]))
    
    # MD3-ALERT-002: Legacy alert classes
    legacy_alert_classes = ['alert-danger', 'alert-info', 'alert-warning', 'alert-success',
                            'form-error', 'help-block', 'hint']
    for legacy_class in legacy_alert_classes:
        pattern = re.compile(rf'\bclass\s*=\s*"[^"]*\b{legacy_class}\b[^"]*"', re.I)
        for match in pattern.finditer(content):
            tag = match.group(0)
            line = get_line_number(content, match.start())
            # Skip if it also has md3-alert
            if 'md3-alert' not in tag:
                issues.append(LintIssue("MD3-ALERT-002", "WARNING", rel_path, line,
                                        f"Legacy alert class '{legacy_class}' without MD3 equivalent",
                                        tag[:60]))
    
    # MD3-ALERT-003: Alert missing title
    # Find md3-alert elements and check if they have md3-alert__title inside
    alert_block_pattern = re.compile(
        r'<div[^>]*class\s*=\s*"[^"]*\bmd3-alert\b[^"]*"[^>]*>.*?</div>',
        re.I | re.DOTALL
    )
    for match in alert_block_pattern.finditer(content):
        block = match.group(0)
        line = get_line_number(content, match.start())
        # Check if it contains md3-alert__title
        if 'md3-alert__title' not in block:
            # Extract first line for context
            first_tag = re.match(r'<[^>]+>', block)
            context = first_tag.group(0)[:60] if first_tag else block[:60]
            issues.append(LintIssue("MD3-ALERT-003", "WARNING", rel_path, line,
                                    "Alert missing .md3-alert__title element",
                                    context))
    
    # MD3-ALERT-004: Error alert with wrong role
    error_alert_pattern = re.compile(
        r'<[^>]*class\s*=\s*"[^"]*\bmd3-alert--error\b[^"]*"[^>]*>',
        re.I
    )
    for match in error_alert_pattern.finditer(content):
        tag = match.group(0)
        line = get_line_number(content, match.start())
        # Check for role="alert"
        if 'role="alert"' not in tag and "role='alert'" not in tag:
            issues.append(LintIssue("MD3-ALERT-004", "ERROR", rel_path, line,
                                    "Error alert must have role=\"alert\"",
                                    tag[:80]))
    
    # MD3-ALERT-005: Icon class order wrong
    icon_wrong_order_pattern = re.compile(
        r'class\s*=\s*"md3-alert__icon\s+material-symbols-rounded"',
        re.I
    )
    for match in icon_wrong_order_pattern.finditer(content):
        line = get_line_number(content, match.start())
        issues.append(LintIssue("MD3-ALERT-005", "ERROR", rel_path, line,
                                "Icon class order wrong: 'material-symbols-rounded' must come FIRST",
                                match.group(0)))
    
    # MD3-FIELD-ERROR-002: aria-invalid="true" without linked md3-field-error
    aria_invalid_pattern = re.compile(r'<input[^>]*aria-invalid\s*=\s*["\']true["\'][^>]*>', re.I)
    for match in aria_invalid_pattern.finditer(content):
        tag = match.group(0)
        line = get_line_number(content, match.start())
        
        # Check for aria-describedby
        describedby_match = re.search(r'aria-describedby\s*=\s*["\']([^"\']+)["\']', tag)
        if describedby_match:
            # Check if any of the referenced IDs exist as md3-field-error
            ids = describedby_match.group(1).split()
            has_error_ref = False
            for ref_id in ids:
                # Look for md3-field-error with this ID nearby
                error_pattern = re.compile(rf'id\s*=\s*["\']?{re.escape(ref_id)}["\']?[^>]*class\s*=\s*"[^"]*md3-field-error', re.I)
                error_pattern_alt = re.compile(rf'class\s*=\s*"[^"]*md3-field-error[^"]*"[^>]*id\s*=\s*["\']?{re.escape(ref_id)}', re.I)
                if error_pattern.search(content) or error_pattern_alt.search(content):
                    has_error_ref = True
                    break
            if not has_error_ref:
                issues.append(LintIssue("MD3-FIELD-ERROR-002", "WARNING", rel_path, line,
                                        "Input with aria-invalid=\"true\" but aria-describedby doesn't reference md3-field-error",
                                        tag[:80]))
        else:
            issues.append(LintIssue("MD3-FIELD-ERROR-002", "WARNING", rel_path, line,
                                    "Input with aria-invalid=\"true\" without aria-describedby",
                                    tag[:80]))
    
    return issues


def inventory_alert_patterns(content: str, rel_path: str) -> List[LintIssue]:
    """Inventory all md3-field-support and md3-field-error elements."""
    issues = []
    
    # Find md3-field-support
    support_pattern = re.compile(r'<[^>]*class\s*=\s*"[^"]*md3-field-support[^"]*"[^>]*>', re.I)
    for match in support_pattern.finditer(content):
        line = get_line_number(content, match.start())
        tag = match.group(0)
        # Extract ID if present
        id_match = re.search(r'id\s*=\s*["\']([^"\']+)["\']', tag)
        field_id = id_match.group(1) if id_match else "(no-id)"
        issues.append(LintIssue("MD3-FIELD-SUPPORT-001", "INFO", rel_path, line,
                                f"Field support: id={field_id}",
                                tag[:60]))
    
    # Find md3-field-error
    error_pattern = re.compile(r'<[^>]*class\s*=\s*"[^"]*md3-field-error[^"]*"[^>]*>', re.I)
    for match in error_pattern.finditer(content):
        line = get_line_number(content, match.start())
        tag = match.group(0)
        # Extract ID if present
        id_match = re.search(r'id\s*=\s*["\']([^"\']+)["\']', tag)
        field_id = id_match.group(1) if id_match else "(no-id)"
        issues.append(LintIssue("MD3-FIELD-SUPPORT-001", "INFO", rel_path, line,
                                f"Field error: id={field_id}",
                                tag[:60]))
    
    # Find md3-alert
    alert_pattern = re.compile(r'<[^>]*class\s*=\s*"[^"]*md3-alert[^"]*"[^>]*>', re.I)
    for match in alert_pattern.finditer(content):
        line = get_line_number(content, match.start())
        tag = match.group(0)
        # Determine variant
        variant = "default"
        if 'md3-alert--error' in tag:
            variant = "error"
        elif 'md3-alert--warning' in tag:
            variant = "warning"
        elif 'md3-alert--info' in tag:
            variant = "info"
        elif 'md3-alert--success' in tag:
            variant = "success"
        inline = "inline" if 'md3-alert--inline' in tag else "full"
        issues.append(LintIssue("MD3-FIELD-SUPPORT-001", "INFO", rel_path, line,
                                f"Alert: variant={variant}, type={inline}",
                                tag[:60]))
    
    return issues


def lint_css_components(content: str, rel_path: str) -> List[LintIssue]:
    """Lint MD3 component CSS files."""
    issues = []
    
    # Hex colors (WARNING - refinement, not breaking)
    for match in PATTERNS['hex_color'].finditer(content):
        line = get_line_number(content, match.start())
        issues.append(LintIssue("MD3-CSS-001", "WARNING", rel_path, line,
                                f"Hex color {match.group(0)} (use CSS tokens)",
                                match.group(0)))
    
    # !important (WARNING - refinement, not breaking)
    for match in PATTERNS['important'].finditer(content):
        line = get_line_number(content, match.start())
        issues.append(LintIssue("MD3-CSS-002", "WARNING", rel_path, line,
                                "!important usage (remove)",
                                match.group(0)))
    
    # Legacy selectors (ERROR - these should be removed)
    for match in PATTERNS['legacy_selector'].finditer(content):
        line = get_line_number(content, match.start())
        issues.append(LintIssue("MD3-CSS-003", "ERROR", rel_path, line,
                                f"Legacy selector {match.group(0)}",
                                match.group(0)))
    
    return issues


def inventory_form_fields(content: str, rel_path: str) -> List[LintIssue]:
    """Inventory all form input fields for uniformity analysis."""
    issues = []
    
    # Find all input, select, textarea elements
    input_pattern = re.compile(r'<(input|select|textarea)[^>]*>', re.I)
    
    for match in input_pattern.finditer(content):
        line = get_line_number(content, match.start())
        tag = match.group(0)
        tag_type = match.group(1).lower()
        
        # Extract name and type attributes
        name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', tag)
        type_match = re.search(r'type\s*=\s*["\']([^"\']+)["\']', tag)
        
        name = name_match.group(1) if name_match else "(unnamed)"
        input_type = type_match.group(1) if type_match else tag_type
        
        # Check wrapper class
        wrapper_class = "unknown"
        if 'md3-outlined-textfield' in content[max(0, match.start()-200):match.start()]:
            wrapper_class = "md3-outlined-textfield"
        elif 'md3-text-field' in content[max(0, match.start()-200):match.start()]:
            wrapper_class = "md3-text-field"
        
        issues.append(LintIssue("MD3-INPUT-001", "INFO", rel_path, line,
                                f"Input: name={name}, type={input_type}, wrapper={wrapper_class}",
                                tag[:80]))
    
    return issues


# ─────────────────────────────────────────────────────────────────────────────
# Main Scanner
# ─────────────────────────────────────────────────────────────────────────────

def scan_file(path: Path, root: Path, options: dict) -> List[LintIssue]:
    """Scan a single file and return issues."""
    issues = []
    
    try:
        content = path.read_text(encoding='utf8', errors='ignore')
    except Exception:
        return issues
    
    rel_path = str(path.relative_to(root)).replace('\\', '/')
    
    # Check if this is a DataTables or non-critical exception
    is_datatables = is_datatables_path(rel_path)
    is_non_critical = is_non_critical_path(rel_path)
    is_legacy_migration = is_legacy_migration_path(rel_path)
    is_excluded_page = rel_path in EXCLUDED_PAGES
    
    # Check file type
    is_html = path.suffix.lower() in {'.html', '.jinja', '.jinja2'}
    is_css = path.suffix.lower() == '.css'
    is_md3_component_css = rel_path.startswith('static/css/md3/components/')
    is_allowed_legacy = rel_path in ALLOWED_LEGACY_TOKEN_FILES
    is_special_css_zone = any(rel_path.startswith(z.rstrip('/')) for z in SPECIAL_CSS_ZONE)
    
    # HTML template checks
    if is_html:
        # Skip excluded pages (player, editor, etc.)
        if is_excluded_page:
            return issues
        
        # Structural checks
        file_issues = []
        file_issues.extend(lint_dialog_structure(content, rel_path))
        file_issues.extend(lint_card_structure(content, rel_path))
        file_issues.extend(lint_hero_structure(content, rel_path))  # Hero validation
        file_issues.extend(lint_form_structure(content, rel_path))
        file_issues.extend(lint_legacy_patterns(content, rel_path))
        file_issues.extend(lint_spacing_patterns(content, rel_path))
        file_issues.extend(lint_textfield_patterns(content, rel_path))
        
        # Alert & field message checks (NEW - always run, even for DataTables)
        file_issues.extend(lint_alert_patterns(content, rel_path))
        
        # Inventory (if requested)
        if options.get('inventory'):
            file_issues.extend(inventory_form_fields(content, rel_path))
            file_issues.extend(inventory_alert_patterns(content, rel_path))
        
        # DataTables exception: convert STRUCTURAL errors to INFO, but keep alert errors
        if is_datatables:
            for issue in file_issues:
                # Only downgrade structural rules, not alert rules
                if issue.severity == "ERROR" and not issue.rule_id.startswith("MD3-ALERT"):
                    issue.severity = "INFO"
                    issue.rule_id = "MD3-DATATABLES-001"
                    issue.message = f"[DataTables] {issue.message}"
        
        # Non-critical paths (LOKAL, docs): convert errors to INFO
        if is_non_critical:
            for issue in file_issues:
                if issue.severity == "ERROR":
                    issue.severity = "INFO"
                    issue.message = f"[Non-critical] {issue.message}"
        
        # Legacy migration paths (pages, player): convert errors to WARNINGS
        if is_legacy_migration:
            for issue in file_issues:
                if issue.severity == "ERROR":
                    issue.severity = "WARNING"
                    issue.message = f"[Legacy migration] {issue.message}"
        
        issues.extend(file_issues)
    
    # CSS checks
    if is_css:
        css_issues = []
        if is_allowed_legacy:
            # Skip legacy shim file
            pass
        elif is_md3_component_css:
            css_issues.extend(lint_css_components(content, rel_path))
        else:
            # Check for legacy tokens in other CSS
            css_issues.extend(lint_legacy_patterns(content, rel_path))
        
        # DataTables CSS: convert errors to INFO
        if is_datatables:
            for issue in css_issues:
                if issue.severity == "ERROR":
                    issue.severity = "INFO"
                    issue.rule_id = "MD3-DATATABLES-001"
                    issue.message = f"[DataTables] {issue.message}"
        
        # Non-critical CSS (LOKAL, docs): convert errors to INFO
        if is_non_critical:
            for issue in css_issues:
                if issue.severity == "ERROR":
                    issue.severity = "INFO"
                    issue.message = f"[Non-critical] {issue.message}"
        
        # Legacy migration CSS (player): convert errors to WARNINGS
        if is_legacy_migration:
            for issue in css_issues:
                if issue.severity == "ERROR":
                    issue.severity = "WARNING"
                    issue.message = f"[Legacy migration] {issue.message}"
        
        issues.extend(css_issues)
    
    return issues


def scan_directory(root: Path, focus_paths: Optional[List[str]] = None, 
                   options: Optional[dict] = None) -> List[LintIssue]:
    """Scan directory tree for MD3 compliance issues."""
    options = options or {}
    all_issues = []
    include_exts = {'.html', '.css', '.jinja', '.jinja2'}
    
    if focus_paths:
        # Scan only focused paths
        for focus in focus_paths:
            focus_path = root / focus
            if focus_path.is_file():
                all_issues.extend(scan_file(focus_path, root, options))
            elif focus_path.is_dir():
                for p in focus_path.rglob('*'):
                    if should_skip_file(p):
                        continue
                    if p.is_file() and p.suffix.lower() in include_exts:
                        all_issues.extend(scan_file(p, root, options))
    else:
        # Full scan
        for p in root.rglob('*'):
            if should_skip_file(p):
                continue
            if p.is_file() and p.suffix.lower() in include_exts:
                all_issues.extend(scan_file(p, root, options))
    
    return all_issues


# ─────────────────────────────────────────────────────────────────────────────
# Report Generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_json_report(issues: List[LintIssue], output_path: Path):
    """Generate machine-readable JSON report."""
    report = {
        "generated": datetime.now().isoformat(),
        "summary": {
            "total": len(issues),
            "errors": len([i for i in issues if i.severity == "ERROR"]),
            "warnings": len([i for i in issues if i.severity == "WARNING"]),
            "info": len([i for i in issues if i.severity == "INFO"]),
        },
        "by_rule": {},
        "issues": [i.to_dict() for i in issues],
    }
    
    # Group by rule
    for issue in issues:
        if issue.rule_id not in report["by_rule"]:
            report["by_rule"][issue.rule_id] = {
                "count": 0,
                "severity": issue.severity,
                "description": RULES.get(issue.rule_id, ("", ""))[1],
            }
        report["by_rule"][issue.rule_id]["count"] += 1
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf8') as f:
        json.dump(report, f, indent=2)


def generate_markdown_report(issues: List[LintIssue], output_path: Path):
    """Generate human-readable Markdown report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    errors = [i for i in issues if i.severity == "ERROR"]
    warnings = [i for i in issues if i.severity == "WARNING"]
    info = [i for i in issues if i.severity == "INFO"]
    
    with output_path.open('w', encoding='utf8') as f:
        f.write('# MD3 Lint Report\n\n')
        f.write(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
        
        f.write('## Summary\n\n')
        f.write(f'- **Errors**: {len(errors)}\n')
        f.write(f'- **Warnings**: {len(warnings)}\n')
        f.write(f'- **Info**: {len(info)}\n')
        f.write(f'- **Total**: {len(issues)}\n\n')
        
        if errors:
            f.write('## Errors\n\n')
            f.write('| File | Line | Rule | Message |\n')
            f.write('|------|------|------|--------|\n')
            for issue in errors:
                f.write(f'| `{issue.file}` | {issue.line} | {issue.rule_id} | {issue.message} |\n')
            f.write('\n')
        
        if warnings:
            f.write('## Warnings\n\n')
            f.write('| File | Line | Rule | Message |\n')
            f.write('|------|------|------|--------|\n')
            for issue in warnings:
                f.write(f'| `{issue.file}` | {issue.line} | {issue.rule_id} | {issue.message} |\n')
            f.write('\n')
        
        if info:
            f.write('## Info\n\n')
            f.write('<details><summary>Click to expand ({} items)</summary>\n\n'.format(len(info)))
            f.write('| File | Line | Rule | Message |\n')
            f.write('|------|------|------|--------|\n')
            for issue in info:
                f.write(f'| `{issue.file}` | {issue.line} | {issue.rule_id} | {issue.message} |\n')
            f.write('\n</details>\n\n')
        
        # Rule breakdown
        f.write('## Rules Triggered\n\n')
        rule_counts = {}
        for issue in issues:
            if issue.rule_id not in rule_counts:
                rule_counts[issue.rule_id] = {"count": 0, "severity": issue.severity}
            rule_counts[issue.rule_id]["count"] += 1
        
        f.write('| Rule | Severity | Count | Description |\n')
        f.write('|------|----------|-------|-------------|\n')
        for rule_id, data in sorted(rule_counts.items()):
            desc = RULES.get(rule_id, ("", "Unknown rule"))[1]
            f.write(f'| {rule_id} | {data["severity"]} | {data["count"]} | {desc} |\n')
        f.write('\n')
        
        if not issues:
            f.write('✅ No issues found — great job!\n')


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='MD3 Structural Compliance Linter for CO.RA.PAN webapp'
    )
    parser.add_argument('--root', default=str(ROOT),
                        help='Root directory to scan')
    parser.add_argument('--focus', nargs='+',
                        help='Focus scan on specific paths (relative to root)')
    parser.add_argument('--out', default='reports/md3-lint-auto.md',
                        help='Markdown report output path')
    parser.add_argument('--json-out', 
                        help='JSON report output path')
    parser.add_argument('--inventory', action='store_true',
                        help='Include form field inventory (INFO level)')
    parser.add_argument('--exit-zero', action='store_true',
                        help='Always exit with status 0 (useful for CI)')
    parser.add_argument('--errors-only', action='store_true',
                        help='Only show errors (not warnings/info)')
    
    args = parser.parse_args()
    root = Path(args.root)
    
    options = {
        'inventory': args.inventory,
    }
    
    # Run scan
    print(f"🔍 Scanning: {root}")
    if args.focus:
        print(f"   Focus: {', '.join(args.focus)}")
    
    issues = scan_directory(root, args.focus, options)
    
    # Filter if errors-only
    if args.errors_only:
        issues = [i for i in issues if i.severity == "ERROR"]
    
    # Generate reports
    md_path = root / args.out
    generate_markdown_report(issues, md_path)
    print(f"📄 Markdown report: {md_path}")
    
    if args.json_out:
        json_path = Path(args.json_out)
        if not json_path.is_absolute():
            json_path = root / json_path
        generate_json_report(issues, json_path)
        print(f"📊 JSON report: {json_path}")
    
    # Summary
    errors = [i for i in issues if i.severity == "ERROR"]
    warnings = [i for i in issues if i.severity == "WARNING"]
    info = [i for i in issues if i.severity == "INFO"]
    
    print(f"\n📋 Summary:")
    print(f"   Errors:   {len(errors)}")
    print(f"   Warnings: {len(warnings)}")
    print(f"   Info:     {len(info)}")
    
    if errors:
        print(f"\n❌ {len(errors)} error(s) found")
        if not args.exit_zero:
            raise SystemExit(2)
    elif warnings:
        print(f"\n⚠️  {len(warnings)} warning(s) found")
    else:
        print(f"\n✅ No errors or warnings")


if __name__ == '__main__':
    main()
