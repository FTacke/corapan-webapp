#!/usr/bin/env python3
"""
md3-textpages-guard.py

Guard script that enforces the Text Pages standard described in
docs/md3-template/textpages_standard.md.

Produces docs/md3-template/md3_textpages_guard_report.md with a per-file
summary. Exit code:
 - 0 => only OK/WARN (no structural/heading failures)
 - 2 => STRUCTURE_FAIL or HEADINGS_FAIL found

This script intentionally avoids heavy HTML parsing to remain dependency-free
and uses robust regex matching suitable for Jinja templates.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT / "templates" / "pages"
REPORT_PATH = ROOT / "docs" / "md3-template" / "md3_textpages_guard_report.md"

DEFAULT_TEXTPAGE_NAMES = {"impressum", "privacy", "datenschutz"}


def find_textpage_templates():
    files = []
    EXCLUDE_KEYWORDS = ("admin", "dashboard", "editor", "player", "atlas", "index")
    for p in sorted(PAGES_DIR.glob("*.html")):
        try:
            txt = p.read_text(encoding="utf8", errors="ignore")
        except Exception:
            continue
        basename = p.stem.lower()
        if any(k in basename for k in EXCLUDE_KEYWORDS):
            # skip admin/search/editor/dashboard-like pages which are not content text pages
            continue
        is_named = basename in DEFAULT_TEXTPAGE_NAMES or basename.startswith(
            "proyecto_"
        )
        contains_textpage = "md3-text-page" in txt
        if is_named or contains_textpage:
            files.append((p, txt))
    return files


def extract_main_block(text):
    m = re.search(
        r"<main[^>]*class=['\"][^'\"]*md3-text-page[^'\"]*['\"][^>]*>(.*?)</main>",
        text,
        re.S | re.I,
    )
    return m.group(1) if m else ""


def check_file(path, text):
    issues = {"structure": [], "headings": [], "dividers": []}

    # Structure checks
    if 'class="md3-page"' not in text and "class='md3-page'" not in text:
        issues["structure"].append("missing md3-page")
    if (
        'class="md3-page__header"' not in text
        and "class='md3-page__header'" not in text
    ):
        issues["structure"].append("missing md3-page__header")
    if "<main" not in text or "md3-text-page" not in text:
        issues["structure"].append('missing <main class="md3-text-page">')

    main = extract_main_block(text)
    if not main:
        issues["structure"].append("could not locate main(md3-text-page) block")

    # Content sections: prefer md3-text-section
    section_matches = (
        re.findall(r"<section[^>]*class=['\"]([^'\"]*)['\"][^>]*>", main, re.I | re.S)
        if main
        else []
    )
    if main and not any("md3-text-section" in cls for cls in section_matches):
        issues["structure"].append(
            'no section with class="md3-text-section" found in main'
        )

    # Headings checks inside main
    if main:
        # H1 should not appear inside main
        if re.search(r"<h1\b", main, re.I):
            issues["headings"].append("found <h1> inside <main> — not allowed")

        # H2 checks
        h2s = list(re.finditer(r"(<h2[^>]*>)(.*?)</h2>", main, re.S | re.I))
        for h2_match in h2s:
            tag = h2_match.group(1)
            cls_m = re.search(r"class=['\"]([^'\"]*)['\"]", tag)
            classes = cls_m.group(1) if cls_m else ""
            if "md3-title-large" not in classes or "md3-section-title" not in classes:
                issues["headings"].append(
                    f'H2 missing required classes (found: "{classes}")'
                )

        # H3 checks
        h3s = list(re.finditer(r"(<h3[^>]*>)(.*?)</h3>", main, re.S | re.I))
        for h3_match in h3s:
            tag = h3_match.group(1)
            cls_m = re.search(r"class=['\"]([^'\"]*)['\"]", tag)
            classes = cls_m.group(1) if cls_m else ""
            if (
                "md3-title-medium" not in classes
                or "md3-subsection-title" not in classes
            ):
                issues["headings"].append(
                    f'H3 missing required classes (found: "{classes}")'
                )

        # No H4-H6
        if re.search(r"<h[4-6]\b", main, re.I):
            issues["headings"].append("found H4/H5/H6 in main — not allowed")

    # Dividers — systematic only
    # count top-level <hr> or sections with md3-text-section--divider
    divider_positions = []
    for m in re.finditer(r"<hr\b[^>]*>", text, re.I):
        divider_positions.append(("hr", m.start()))
    for m in re.finditer(
        r"<section[^>]*class=['\"][^'\"]*md3-text-section--divider[^'\"]*['\"][^>]*>",
        text,
        re.I | re.S,
    ):
        divider_positions.append(("section-divider", m.start()))

    h2_positions = [m.start() for m in re.finditer(r"<h2\b", text, re.I)]
    if divider_positions:
        # Check that number of dividers equals number of H2s
        if len(divider_positions) != len(h2_positions):
            issues["dividers"].append(
                f"divider count ({len(divider_positions)}) != h2 count ({len(h2_positions)})"
            )
        # Check direct adjacency: each divider should be followed by an H2
        for kind, pos in divider_positions:
            # find first h2 position greater than divider position
            next_h2 = next((hp for hp in h2_positions if hp > pos), None)
            if next_h2 is None:
                issues["dividers"].append(f"divider at pos {pos} not followed by H2")
            else:
                # allow only whitespace/comment between them
                between = text[pos:next_h2]
                if not re.match(r"^[\s\n\r\t\{\%\#]*$", between):
                    issues["dividers"].append(
                        f"divider at pos {pos} not immediately followed by H2 (contains other content)"
                    )

    # Finalize classifications
    status = {
        "STRUCTURE_FAIL": bool(issues["structure"]),
        "HEADINGS_FAIL": bool(issues["headings"]),
        "DIVIDERS_WARN": bool(issues["dividers"]),
    }

    return issues, status


def main():
    files = find_textpage_templates()
    report_lines = []
    overall = {"STRUCTURE_FAIL": 0, "HEADINGS_FAIL": 0, "DIVIDERS_WARN": 0}

    report_lines.append("# MD3 Text Pages Guard Report\n")
    if not files:
        report_lines.append("No text-page templates found under templates/pages/.\n")

    for p, txt in files:
        rel = str(p.relative_to(ROOT))
        issues, status = check_file(p, txt)
        report_lines.append(f"## {rel}\n")
        if status["STRUCTURE_FAIL"]:
            overall["STRUCTURE_FAIL"] += 1
            report_lines.append("STRUCTURE_FAIL\n")
            for i in issues["structure"]:
                report_lines.append(f"- {i}\n")
        else:
            report_lines.append("STRUCTURE_OK\n")

        if status["HEADINGS_FAIL"]:
            overall["HEADINGS_FAIL"] += 1
            report_lines.append("HEADINGS_FAIL\n")
            for i in issues["headings"]:
                report_lines.append(f"- {i}\n")
        else:
            report_lines.append("HEADINGS_OK\n")

        if status["DIVIDERS_WARN"]:
            overall["DIVIDERS_WARN"] += 1
            report_lines.append("DIVIDERS_WARN\n")
            for i in issues["dividers"]:
                report_lines.append(f"- {i}\n")
        else:
            report_lines.append("DIVIDERS_OK\n")

        report_lines.append("\n")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf8")

    # Exit semantics
    if overall["STRUCTURE_FAIL"] or overall["HEADINGS_FAIL"]:
        print(
            "md3-textpages-guard: STRUCTURE/HEADING failures found (see report):",
            REPORT_PATH,
        )
        raise SystemExit(2)
    elif overall["DIVIDERS_WARN"]:
        print(
            "md3-textpages-guard: Warnings found (dividers) — see report:", REPORT_PATH
        )
        raise SystemExit(0)
    else:
        print("md3-textpages-guard: OK — no structural or heading failures")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
