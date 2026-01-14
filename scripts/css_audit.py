#!/usr/bin/env python3
"""
CSS Audit Script - MD3 Token Conformity Validator

Validates that all CSS follows MD3 token-based design system rules:
- No hardcoded colors outside token definition files
- No inline styles in JavaScript (except data attributes)
- Documented !important usage with NEEDS_IMPORTANT comments
- Consolas prioritized over Courier New in font-family

Exit codes:
  0 = All checks passed
  1 = Violations found
  2 = Script error (file not found, etc.)

Usage:
  python scripts/css_audit.py              # Run all checks
  python scripts/css_audit.py --fix        # Auto-fix some violations (planned)
  python scripts/css_audit.py --ci         # CI mode (fail fast, no colors)
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Violation:
    """Represents a single CSS audit violation."""
    
    file_path: str
    line_number: int
    rule: str
    message: str
    severity: str = "error"  # "error", "warning", "info"
    
    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_number} [{self.severity.upper()}] {self.rule}: {self.message}"


class CSSAuditor:
    """Audits CSS files for MD3 token system conformity."""
    
    # Token definition files (allowed to have hardcoded colors)
    TOKEN_FILES = {
        "static/css/md3/tokens.css",
        "static/css/md3/tokens-legacy-shim.css",
        "static/css/app-tokens.css",
        "templates/base.html",  # Critical CSS fallbacks
    }
    
    # Files allowed to use !important (with documentation requirement)
    IMPORTANT_ALLOWED = {
        "static/css/md3/components/datatables.css",
        "static/css/md3/components/datatables-theme-lock.css",
        "static/css/md3/components/advanced-search.css",
        "static/css/md3/components/index.css",
        "static/css/md3/components/stats.css",
    }
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.violations: List[Violation] = []
    
    def audit_hardcoded_colors(self, file_path: Path, content: str) -> None:
        """Check for hardcoded hex colors or rgb(a) values outside token definitions."""
        if any(str(file_path).endswith(token_file) for token_file in self.TOKEN_FILES):
            return  # Skip token definition files
        
        # Regex for hex colors: #fff, #ffffff, #ffffffff (not in comments, not in var() definitions)
        hex_pattern = re.compile(
            r"""
            (?<!--)                      # Not after -- (CSS variable definition)
            (?<!/\*)                     # Not in block comment start
            (?<!:[ ])                    # Not after : (variable definition line)
            \#[0-9a-fA-F]{3,8}          # Hex color
            (?![^/]*\*/)                # Not before block comment end
            """,
            re.VERBOSE,
        )
        
        # Regex for rgb/rgba: rgb(0, 0, 0), rgba(255, 255, 255, 0.5)
        # EXCEPT: rgb(X X X / Y%) modern syntax in color-mix or elevation shadows
        rgb_pattern = re.compile(
            r"""
            rgba?\(
            \s*\d+\s*,\s*\d+\s*,\s*\d+  # rgb(X, X, X) with commas (old syntax)
            """,
            re.VERBOSE,
        )
        
        lines = content.splitlines()
        for line_num, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith("/*") or line.strip().startswith("*"):
                continue
            
            # Check for variable definitions (allowed)
            if re.match(r"\s*--[a-z-]+:", line):
                continue
            
            # Check hex colors
            hex_matches = hex_pattern.findall(line)
            if hex_matches:
                self.violations.append(
                    Violation(
                        file_path=str(file_path.relative_to(self.repo_root)),
                        line_number=line_num,
                        rule="hardcoded-color",
                        message=f"Hardcoded hex color found: {', '.join(hex_matches)}. Use MD3 tokens instead.",
                        severity="error",
                    )
                )
            
            # Check rgb/rgba (old comma syntax)
            rgb_matches = rgb_pattern.findall(line)
            if rgb_matches:
                # Exception: elevation shadows use rgb(X X X / Y%)
                if "rgb(" in line and "/" not in line and "color-mix" not in line:
                    self.violations.append(
                        Violation(
                            file_path=str(file_path.relative_to(self.repo_root)),
                            line_number=line_num,
                            rule="hardcoded-color",
                            message=f"Hardcoded rgb/rgba color found: {line.strip()}. Use MD3 tokens or color-mix instead.",
                            severity="error",
                        )
                    )
    
    def audit_important_usage(self, file_path: Path, content: str) -> None:
        """Check that !important usage is properly documented."""
        if not any(str(file_path).endswith(allowed) for allowed in self.IMPORTANT_ALLOWED):
            # Check if file uses !important at all
            if "!important" in content:
                self.violations.append(
                    Violation(
                        file_path=str(file_path.relative_to(self.repo_root)),
                        line_number=0,
                        rule="unauthorized-important",
                        message="File uses !important but is not in allowed list. Add to IMPORTANT_ALLOWED if legitimate.",
                        severity="warning",
                    )
                )
                return
        
        # For allowed files, check documentation
        lines = content.splitlines()
        for line_num, line in enumerate(lines, 1):
            if "!important" in line and "NEEDS_IMPORTANT" not in content[
                max(0, content.find(line) - 500) : content.find(line)
            ]:
                self.violations.append(
                    Violation(
                        file_path=str(file_path.relative_to(self.repo_root)),
                        line_number=line_num,
                        rule="undocumented-important",
                        message="!important usage without NEEDS_IMPORTANT comment. Add explanation.",
                        severity="warning",
                    )
                )
    
    def audit_font_family(self, file_path: Path, content: str) -> None:
        """Check that Consolas comes before Courier New in font-family declarations."""
        pattern = re.compile(r'font-family:\s*[^;]*"Courier New"[^;]*"Consolas"', re.IGNORECASE)
        
        lines = content.splitlines()
        for line_num, line in enumerate(lines, 1):
            if pattern.search(line):
                self.violations.append(
                    Violation(
                        file_path=str(file_path.relative_to(self.repo_root)),
                        line_number=line_num,
                        rule="courier-new-priority",
                        message='Courier New should come AFTER Consolas in font-family. Swap order.',
                        severity="error",
                    )
                )
    
    def audit_inline_styles_js(self, file_path: Path, content: str) -> None:
        """Check JavaScript files for inline style manipulation (discouraged)."""
        # Patterns indicating inline style setting
        patterns = [
            re.compile(r'\.style\.(background|color|border|padding|margin)\s*=', re.IGNORECASE),
            re.compile(r'\.setAttribute\(\s*["\']style["\']', re.IGNORECASE),
            re.compile(r'\.setProperty\(\s*["\']--[a-z-]+["\']', re.IGNORECASE),  # CSS var manipulation
        ]
        
        # Exceptions: data-* attributes, computed styles
        exception_patterns = [
            re.compile(r'getComputedStyle'),
            re.compile(r'data-[a-z-]+'),
        ]
        
        lines = content.splitlines()
        for line_num, line in enumerate(lines, 1):
            # Skip if line has exceptions
            if any(exc.search(line) for exc in exception_patterns):
                continue
            
            # Check for inline style patterns
            for pattern in patterns:
                if pattern.search(line):
                    self.violations.append(
                        Violation(
                            file_path=str(file_path.relative_to(self.repo_root)),
                            line_number=line_num,
                            rule="inline-styles-js",
                            message="Inline style manipulation in JS. Move styles to external CSS with classes.",
                            severity="warning",
                        )
                    )
                    break
    
    def audit_file(self, file_path: Path) -> None:
        """Run all audit checks on a single file."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.violations.append(
                Violation(
                    file_path=str(file_path.relative_to(self.repo_root)),
                    line_number=0,
                    rule="file-read-error",
                    message=f"Could not read file: {e}",
                    severity="error",
                )
            )
            return
        
        if file_path.suffix == ".css":
            self.audit_hardcoded_colors(file_path, content)
            self.audit_important_usage(file_path, content)
            self.audit_font_family(file_path, content)
        elif file_path.suffix == ".js":
            self.audit_inline_styles_js(file_path, content)
    
    def audit_all(self) -> None:
        """Run audit on all CSS and JS files in the project."""
        css_files = list((self.repo_root / "static" / "css").rglob("*.css"))
        js_files = list((self.repo_root / "static" / "js").rglob("*.js"))
        
        print(f"🔍 Auditing {len(css_files)} CSS files and {len(js_files)} JS files...")
        
        for file_path in css_files + js_files:
            self.audit_file(file_path)
        
        print(f"✓ Audit complete: {len(self.violations)} violation(s) found\n")
    
    def print_violations(self, ci_mode: bool = False) -> None:
        """Print all violations with optional color coding."""
        if not self.violations:
            if not ci_mode:
                print("✅ All checks passed! CSS conforms to MD3 token system.")
            else:
                print("PASS: All checks passed")
            return
        
        # Group by severity
        errors = [v for v in self.violations if v.severity == "error"]
        warnings = [v for v in self.violations if v.severity == "warning"]
        
        if errors:
            print(f"❌ {len(errors)} ERROR(S):")
            for violation in errors:
                print(f"  {violation}")
            print()
        
        if warnings:
            print(f"⚠️  {len(warnings)} WARNING(S):")
            for violation in warnings:
                print(f"  {violation}")
            print()
    
    def exit_code(self) -> int:
        """Return appropriate exit code based on violations."""
        if not self.violations:
            return 0
        
        # Errors cause failure
        if any(v.severity == "error" for v in self.violations):
            return 1
        
        # Warnings alone don't fail (but should be fixed)
        return 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Audit CSS files for MD3 token system conformity"
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: fail fast, no color output",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix violations where possible (not implemented yet)",
    )
    
    args = parser.parse_args()
    
    # Find repo root
    repo_root = Path(__file__).parent.parent
    if not (repo_root / "static" / "css").exists():
        print("ERROR: Could not find static/css directory", file=sys.stderr)
        return 2
    
    # Run audit
    auditor = CSSAuditor(repo_root)
    auditor.audit_all()
    auditor.print_violations(ci_mode=args.ci)
    
    return auditor.exit_code()


if __name__ == "__main__":
    sys.exit(main())
