#!/usr/bin/env python3
"""
Project structure validator.

Checks that files are in the correct locations according to project conventions.
Run this in CI or locally to catch structure violations.

Usage:
    python scripts/check_structure.py
    python scripts/check_structure.py --fix  # (future: auto-move files)
"""

import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parents[1]

# Files allowed in root directory
ALLOWED_ROOT_FILES = {
    # Documentation
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "startme.md",
    "CONTRIBUTING.md",
    "CITATION.cff",  # GitHub/Zenodo citation metadata (must be in root)
    # Build/Config
    "pyproject.toml",
    "setup.cfg",
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",  # Main compose file stays in root
    "docker-compose.dev-postgres.yml",  # PostgreSQL dev variant
    ".dockerignore",
    ".gitignore",
    ".gitattributes",
    ".env",
    ".env.example",
    "playwright.config.js",
    # Deprecated but allowed for transition
    "passwords.env",
    "passwords.env.template",
    # Database files (development only, should be gitignored)
    "auth.db",
}

# Directories allowed in root
ALLOWED_ROOT_DIRS = {
    # Version control & CI
    ".git",
    ".github",
    # IDE & Editor
    ".vscode",
    # Development environments & caches (all gitignored)
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "__pycache__",
    # Core project directories
    "src",
    "templates",
    "static",
    "docs",
    "scripts",
    "tests",
    "config",
    "migrations",
    "infra",  # DevOps: docker-compose.dev.yml, docker-compose.prod.yml
    # Data directories (gitignored, structure preserved via .gitkeep)
    "data",
    "media",
    "logs",
    "reports",  # Generated lint reports (gitignored, created by md3-lint.py)
    # Local-only directories (gitignored - for user's local binaries/tools)
    "opt",  # External tools/binaries (e.g., blacklab-server.war)
    "tools",  # cwRsync and other Windows utilities for rsync-based sync
    "LOKAL",  # Local workflow scripts (separate git repo)
}


def check_root_files() -> list[str]:
    """Check that no unexpected files are in the root directory."""
    violations = []

    for item in ROOT.iterdir():
        name = item.name

        if item.is_file():
            if name not in ALLOWED_ROOT_FILES:
                if name.endswith(".md") and name not in ALLOWED_ROOT_FILES:
                    violations.append(
                        f"Markdown file '{name}' in root should be in docs/"
                    )
                elif name.endswith(".py"):
                    violations.append(
                        f"Python script '{name}' in root should be in scripts/"
                    )
                elif not name.startswith("."):
                    violations.append(f"Unexpected file '{name}' in root directory")

        elif item.is_dir():
            if name not in ALLOWED_ROOT_DIRS:
                violations.append(f"Unexpected directory '{name}' in root")

    return violations


def check_no_docs_in_templates() -> list[str]:
    """Ensure no markdown or documentation files in templates/."""
    violations = []
    templates_dir = ROOT / "templates"

    if not templates_dir.exists():
        return violations

    for md_file in templates_dir.rglob("*.md"):
        violations.append(
            f"Markdown file found in templates/: {md_file.relative_to(ROOT)}"
        )

    return violations


def check_no_scripts_outside_scripts() -> list[str]:
    """Ensure Python scripts are in scripts/ directory."""
    violations = []

    # Check common wrong locations
    for py_file in ROOT.glob("*.py"):
        # Allow setup.py at root
        if py_file.name in {"setup.py", "conftest.py"}:
            continue
        violations.append(
            f"Python script '{py_file.name}' in root should be in scripts/"
        )

    return violations


def check_no_data_committed() -> list[str]:
    """Warn about data files that might be accidentally committed."""
    violations = []

    # These should be in .gitignore

    # Just check if data directories have content (warning, not error)
    data_dir = ROOT / "data"
    if data_dir.exists():
        for db in data_dir.rglob("*.db"):
            # These are runtime files, should be gitignored
            pass  # Don't fail, just note

    return violations


def check_test_structure() -> list[str]:
    """Ensure tests follow proper structure."""
    violations = []
    tests_dir = ROOT / "tests"

    if not tests_dir.exists():
        violations.append("tests/ directory not found")
        return violations

    # Check test files have proper prefix
    for py_file in tests_dir.glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        if py_file.name == "__init__.py":
            continue
        if py_file.name == "conftest.py":
            continue
        if not py_file.name.startswith("test_"):
            violations.append(f"Test file '{py_file.name}' should start with 'test_'")

    return violations


def main() -> int:
    """Run all structure checks."""
    all_violations = []

    print("Checking project structure...\n")

    # Run checks
    checks = [
        ("Root files", check_root_files),
        ("Templates directory", check_no_docs_in_templates),
        ("Script locations", check_no_scripts_outside_scripts),
        ("Test structure", check_test_structure),
    ]

    for name, check_fn in checks:
        violations = check_fn()
        if violations:
            print(f"❌ {name}:")
            for v in violations:
                print(f"   - {v}")
            all_violations.extend(violations)
        else:
            print(f"✅ {name}: OK")

    print()

    if all_violations:
        print(f"Found {len(all_violations)} structure violation(s).")
        print("\nSee docs/reference/project_structure.md for guidelines.")
        return 1

    print("Project structure is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
