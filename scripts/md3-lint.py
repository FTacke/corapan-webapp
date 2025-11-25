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

See: docs/md3-template/md3-structural-compliance.md
"""
import re
import json
from pathlib import Path
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Set
from datetime import datetime

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
    
    # Form rules
    "MD3-FORM-001": ("ERROR", "Submit button outside form without form attribute"),
    
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
LEGACY_MIGRATION_PATHS = {'static/css/player-mobile.css', 'templates/pages/'}  # Legacy pages in migration
ALLOWED_LEGACY_TOKEN_FILES = {'static/css/md3/tokens-legacy-shim.css'}
IGNORED_DIRS = {'.venv', 'node_modules', '.git', 'build', '__pycache__', 'data'}


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
    """Check if path is in legacy migration area (player, pages)."""
    normalized = path.replace('\\', '/')
    if normalized in LEGACY_MIGRATION_PATHS:
        return True
    return any(normalized.startswith(lm) for lm in LEGACY_MIGRATION_PATHS)


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
        
        # Check for md3-card__content
        if 'md3-card__content' not in card_block:
            issues.append(LintIssue("MD3-CARD-001", "ERROR", rel_path, line,
                                    "Card missing md3-card__content", tag[:60]))
        
        # Check order: actions/footer should come after content
        content_pos = card_block.find('md3-card__content')
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
    # Exclude md3-hero--card which is a valid hero modifier, not a legacy card
    for match in re.finditer(r'class\s*=\s*"([^"]*\bcard\b[^"]*)"', content):
        cls = match.group(1)
        # Skip if it's an md3-card or md3-hero--card (valid patterns)
        if 'md3-card' in cls or 'md3-hero--card' in cls:
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
    
    # Check file type
    is_html = path.suffix.lower() in {'.html', '.jinja', '.jinja2'}
    is_css = path.suffix.lower() == '.css'
    is_md3_component_css = rel_path.startswith('static/css/md3/components/')
    is_allowed_legacy = rel_path in ALLOWED_LEGACY_TOKEN_FILES
    
    # HTML template checks
    if is_html:
        # Structural checks
        file_issues = []
        file_issues.extend(lint_dialog_structure(content, rel_path))
        file_issues.extend(lint_card_structure(content, rel_path))
        file_issues.extend(lint_form_structure(content, rel_path))
        file_issues.extend(lint_legacy_patterns(content, rel_path))
        file_issues.extend(lint_spacing_patterns(content, rel_path))
        file_issues.extend(lint_textfield_patterns(content, rel_path))
        
        # Inventory (if requested)
        if options.get('inventory'):
            file_issues.extend(inventory_form_fields(content, rel_path))
        
        # DataTables exception: convert errors to INFO
        if is_datatables:
            for issue in file_issues:
                if issue.severity == "ERROR":
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
    parser.add_argument('--out', default='docs/md3-template/md3_lint_report_auto.md',
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
