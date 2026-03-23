#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
99_check_pipeline_json.py

QA/Regression-Skript für die JSON-Pipeline.
Testet die Schritte 01–05 auf einem kleinen Sample-Szenario und gibt
eine klare Zusammenfassung aller Checks aus.

PIPELINE-SCHRITTE:
    01_preprocess_transcripts.py    → json-ready/
    02_annotate_transcripts_v3.py   → media/transcripts/<country>/
    03_build_metadata_stats.py      → data/db/*.db
    04_internal_country_statistics.py → results/*.csv
    05_publish_corpus_statistics.py  → static/img/statistics/

VERWENDUNG:
    python 99_check_pipeline_json.py
    python 99_check_pipeline_json.py --country ARG --limit 2
    python 99_check_pipeline_json.py --skip-steps  # Only run checks, skip pipeline execution

Copyright (c) 2025 CO.RA.PAN Project
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Optional: pandas for CSV reading
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # LOKAL/_1_json -> PROJECT_ROOT

# Pipeline directories
JSON_PRE_DIR = SCRIPT_DIR / "json-pre"
JSON_READY_DIR = SCRIPT_DIR / "json-ready"
TRANSCRIPTS_DIR = PROJECT_ROOT / "media" / "transcripts"
RESULTS_DIR = SCRIPT_DIR / "results"
STATS_IMG_DIR = PROJECT_ROOT / "static" / "img" / "statistics"

# Database paths
DB_COUNTRY = PROJECT_ROOT / "data" / "db" / "public" / "stats_country.db"
DB_FILES = PROJECT_ROOT / "data" / "db" / "public" / "stats_files.db"

# Report output
REPORT_PATH = SCRIPT_DIR / "99_check_pipeline_report.json"

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def log_ok(message: str) -> None:
    """Print OK message."""
    print(f"[OK]   {message}")


def log_fail(message: str) -> None:
    """Print FAIL message."""
    print(f"[FAIL] {message}")


def log_info(message: str) -> None:
    """Print info message."""
    print(f"[INFO] {message}")


def log_warn(message: str) -> None:
    """Print warning message."""
    print(f"[WARN] {message}")


def check_exists(path: Path, description: str, results: list[dict], min_size: int = 0) -> bool:
    """
    Check if a path exists (and optionally has minimum size).
    
    Args:
        path: Path to check
        description: Human-readable description of the check
        results: List to append check result to
        min_size: Minimum file size in bytes (0 = only check existence)
    
    Returns:
        True if check passed, False otherwise
    """
    exists = path.exists()
    size_ok = True
    actual_size = 0
    
    if exists and min_size > 0:
        actual_size = path.stat().st_size
        size_ok = actual_size >= min_size
    
    ok = exists and size_ok
    
    result = {
        "check": description,
        "path": str(path),
        "ok": ok,
        "details": ""
    }
    
    if not exists:
        result["details"] = "File does not exist"
        log_fail(f"{description}: File not found - {path}")
    elif not size_ok:
        result["details"] = f"File too small ({actual_size} bytes, min {min_size})"
        log_fail(f"{description}: File too small ({actual_size} bytes) - {path}")
    else:
        log_ok(f"{description}")
    
    results.append(result)
    return ok


def load_json(path: Path) -> dict | None:
    """
    Load JSON file with UTF-8-sig encoding.
    
    Returns:
        Parsed JSON dict or None on error
    """
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except FileNotFoundError:
        log_warn(f"JSON file not found: {path}")
        return None
    except json.JSONDecodeError as e:
        log_warn(f"JSON parse error in {path}: {e}")
        return None
    except Exception as e:
        log_warn(f"Error loading {path}: {e}")
        return None


def load_csv_simple(path: Path) -> list[dict] | None:
    """
    Load CSV file as list of dicts (simple implementation without pandas).
    
    Returns:
        List of row dicts or None on error
    """
    try:
        import csv
        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        log_warn(f"Error loading CSV {path}: {e}")
        return None


def run_step(step_name: str, cmd: list[str], results: list[dict]) -> bool:
    """
    Run a pipeline step via subprocess.
    
    Args:
        step_name: Human-readable step name
        cmd: Command to run
        results: List to append result to
    
    Returns:
        True if successful, False otherwise
    """
    result = {
        "check": f"Step {step_name}",
        "path": "",
        "ok": False,
        "details": ""
    }
    
    try:
        log_info(f"Running: {' '.join(cmd)}")
        proc = subprocess.run(
            cmd,
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if proc.returncode == 0:
            result["ok"] = True
            result["details"] = "Completed successfully"
            log_ok(f"Step {step_name} completed")
        else:
            result["details"] = f"Exit code {proc.returncode}: {proc.stderr[:500]}"
            log_fail(f"Step {step_name} failed (exit {proc.returncode})")
            if proc.stderr:
                print(f"       STDERR: {proc.stderr[:200]}...")
    
    except subprocess.TimeoutExpired:
        result["details"] = "Timeout after 300s"
        log_fail(f"Step {step_name} timed out")
    
    except Exception as e:
        result["details"] = str(e)
        log_fail(f"Step {step_name} error: {e}")
    
    results.append(result)
    return result["ok"]


def find_first_country_with_data() -> str | None:
    """Find the first country code that has data in json-pre."""
    if not JSON_PRE_DIR.exists():
        return None
    
    # Look for any JSON files
    for jf in JSON_PRE_DIR.glob("*.json"):
        data = load_json(jf)
        if data:
            # Try to extract country code from filename or data
            country = data.get("country_code")
            if country:
                return country
            # Parse from filename: YYYY-MM-DD_COUNTRY_Radio.json
            parts = jf.stem.split("_")
            if len(parts) >= 2:
                return parts[1]
    
    # Fallback: check transcripts directory
    if TRANSCRIPTS_DIR.exists():
        for d in TRANSCRIPTS_DIR.iterdir():
            if d.is_dir() and d.name != ".gitkeep":
                return d.name
    
    return None


def query_db(db_path: Path, query: str) -> list[tuple] | None:
    """Execute a query on SQLite database."""
    if not db_path.exists():
        return None
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        log_warn(f"DB query error ({db_path}): {e}")
        return None


def count_words_in_json(json_path: Path) -> int:
    """Count total words in a JSON transcript file."""
    data = load_json(json_path)
    if not data:
        return 0
    
    total = 0
    for seg in data.get("segments", []):
        total += len(seg.get("words", []))
    return total


def get_max_end_ms_in_json(json_path: Path) -> int:
    """Get the maximum end_ms value from a JSON transcript file."""
    data = load_json(json_path)
    if not data:
        return 0
    
    max_end = 0
    for seg in data.get("segments", []):
        for w in seg.get("words", []):
            end_ms = w.get("end_ms", 0)
            if end_ms > max_end:
                max_end = end_ms
    return max_end


# ==============================================================================
# PIPELINE STEP RUNNERS
# ==============================================================================

def run_pipeline_steps(country: str, limit: int, results: list[dict], 
                       skip_steps: list[str] = None, continue_on_error: bool = False) -> None:
    """Run all pipeline steps."""
    
    skip_steps = skip_steps or []
    
    print("\n" + "=" * 70)
    print("EXECUTING PIPELINE STEPS")
    print("=" * 70)
    
    steps = [
        ("01", "01 (preprocess)", 
         [sys.executable, "01_preprocess_transcripts.py", "--limit", str(limit)]),
        ("02", "02 (annotate)", 
         [sys.executable, "02_annotate_transcripts_v3.py", "--country", country, "--limit", str(limit), "--force"]),
        ("03", "03 (metadata DB)", 
         [sys.executable, "03_build_metadata_stats.py", "--country", country]),
        ("04", "04 (internal stats)", 
         [sys.executable, "04_internal_country_statistics.py", "--country", country, "--limit", str(limit)]),
        ("05", "05 (publish stats)", 
         [sys.executable, "05_publish_corpus_statistics.py"]),
    ]
    
    for step_id, step_name, cmd in steps:
        if step_id in skip_steps:
            log_info(f"Skipping step {step_name} (--skip-step)")
            results.append({
                "check": f"Step {step_name}",
                "path": "",
                "ok": True,
                "details": "Skipped by user"
            })
            continue
        
        success = run_step(step_name, cmd, results)
        
        if not success and not continue_on_error:
            log_warn(f"Stopping pipeline due to step failure. Use --continue-on-error to continue.")
            break


# ==============================================================================
# CONSISTENCY CHECKS
# ==============================================================================

def check_json_structure(country: str, results: list[dict]) -> None:
    """Check JSON file structure after steps 01 and 02."""
    
    print("\n" + "-" * 70)
    print("CHECK: JSON Structure (Steps 01 + 02)")
    print("-" * 70)
    
    # Find a sample JSON file in json-ready
    sample_ready = None
    for jf in JSON_READY_DIR.glob("*.json"):
        sample_ready = jf
        break
    
    if not sample_ready:
        results.append({
            "check": "JSON Structure - json-ready sample",
            "path": str(JSON_READY_DIR),
            "ok": False,
            "details": "No JSON files found in json-ready"
        })
        log_fail("No JSON files in json-ready to check")
        return
    
    # Load json-ready file
    data = load_json(sample_ready)
    if not data:
        results.append({
            "check": "JSON Structure - load json-ready",
            "path": str(sample_ready),
            "ok": False,
            "details": "Failed to load JSON"
        })
        return
    
    # Check basic structure
    checks = [
        ("segments" in data, "segments field exists"),
        (isinstance(data.get("segments", []), list), "segments is a list"),
    ]
    
    for ok, desc in checks:
        results.append({
            "check": f"JSON Structure - {desc}",
            "path": str(sample_ready),
            "ok": ok,
            "details": ""
        })
        if ok:
            log_ok(f"json-ready: {desc}")
        else:
            log_fail(f"json-ready: {desc}")
    
    # Check first segment structure
    segments = data.get("segments", [])
    if segments:
        seg = segments[0]
        seg_checks = [
            ("speaker_code" in seg or "speaker" in seg, "segment has speaker info"),
            ("words" in seg, "segment has words"),
            (isinstance(seg.get("words", []), list), "words is a list"),
        ]
        
        for ok, desc in seg_checks:
            results.append({
                "check": f"JSON Structure - {desc}",
                "path": str(sample_ready),
                "ok": ok,
                "details": ""
            })
            if ok:
                log_ok(f"json-ready: {desc}")
            else:
                log_fail(f"json-ready: {desc}")
    
    # Check annotated file in transcripts
    transcript_dir = TRANSCRIPTS_DIR / country
    sample_annotated = None
    
    if transcript_dir.exists():
        for jf in transcript_dir.glob("*.json"):
            sample_annotated = jf
            break
    
    if not sample_annotated:
        results.append({
            "check": "JSON Structure - annotated sample",
            "path": str(transcript_dir),
            "ok": False,
            "details": f"No annotated JSONs found for {country}"
        })
        log_fail(f"No annotated JSONs for {country}")
        return
    
    ann_data = load_json(sample_annotated)
    if not ann_data:
        results.append({
            "check": "JSON Structure - load annotated",
            "path": str(sample_annotated),
            "ok": False,
            "details": "Failed to load annotated JSON"
        })
        return
    
    # Check v3 annotation
    ann_meta = ann_data.get("ann_meta", {})
    version = ann_meta.get("version", "")
    
    version_ok = version == "corapan-ann/v3"
    results.append({
        "check": "JSON Structure - v3 annotation version",
        "path": str(sample_annotated),
        "ok": version_ok,
        "details": f"Found: {version}"
    })
    if version_ok:
        log_ok(f"Annotated: version = {version}")
    else:
        log_fail(f"Annotated: expected corapan-ann/v3, got {version}")
    
    # Check word structure in annotated file
    ann_segments = ann_data.get("segments", [])
    if ann_segments:
        ann_seg = ann_segments[0]
        ann_words = ann_seg.get("words", [])
        
        if ann_words:
            word = ann_words[0]
            word_checks = [
                ("start_ms" in word, "word has start_ms"),
                ("end_ms" in word, "word has end_ms"),
                (isinstance(word.get("start_ms", ""), int), "start_ms is int"),
                ("text" in word, "word has text"),
            ]
            
            for ok, desc in word_checks:
                results.append({
                    "check": f"JSON Structure - {desc}",
                    "path": str(sample_annotated),
                    "ok": ok,
                    "details": ""
                })
                if ok:
                    log_ok(f"Annotated: {desc}")
                else:
                    log_fail(f"Annotated: {desc}")
        
        # Check speaker structure
        speaker = ann_seg.get("speaker", {})
        speaker_fields = ["code", "speaker_type", "speaker_sex", "speaker_mode", "speaker_discourse"]
        
        for field in speaker_fields:
            ok = field in speaker
            results.append({
                "check": f"JSON Structure - speaker.{field} exists",
                "path": str(sample_annotated),
                "ok": ok,
                "details": ""
            })
            if ok:
                log_ok(f"Annotated: speaker.{field} exists")
            else:
                log_fail(f"Annotated: speaker.{field} missing")


def check_db_vs_json(country: str, results: list[dict]) -> None:
    """Check database consistency with JSON files."""
    
    print("\n" + "-" * 70)
    print("CHECK: Database vs JSON Consistency (Step 03)")
    print("-" * 70)
    
    # Aggregate from JSON files
    transcript_dir = TRANSCRIPTS_DIR / country
    if not transcript_dir.exists():
        results.append({
            "check": "DB vs JSON - transcript directory",
            "path": str(transcript_dir),
            "ok": False,
            "details": f"Directory not found: {transcript_dir}"
        })
        log_fail(f"Transcript directory not found: {transcript_dir}")
        return
    
    json_word_count = 0
    json_files = list(transcript_dir.glob("*.json"))
    
    for jf in json_files:
        json_word_count += count_words_in_json(jf)
    
    log_info(f"JSON word count for {country}: {json_word_count:,} (from {len(json_files)} files)")
    
    # Query stats_country.db
    if not DB_COUNTRY.exists():
        results.append({
            "check": "DB vs JSON - stats_country.db exists",
            "path": str(DB_COUNTRY),
            "ok": False,
            "details": "Database not found"
        })
        log_fail(f"stats_country.db not found")
        return
    
    # Try to get word count from database
    db_word_count = None
    
    # Try different possible column names / table names
    queries = [
        f"SELECT total_word_count FROM stats_country WHERE country_code = '{country}'",
        f"SELECT total_words FROM stats WHERE country_code = '{country}'",
        f"SELECT word_count FROM stats WHERE country_code = '{country}'",
        f"SELECT word_count FROM country_stats WHERE country_code = '{country}'",
        f"SELECT total_word_count FROM stats WHERE country_code = '{country}'",
    ]
    
    for query in queries:
        try:
            rows = query_db(DB_COUNTRY, query)
            if rows and len(rows) > 0 and rows[0][0]:
                db_word_count = int(rows[0][0])
                break
        except:
            continue
    
    if db_word_count is None:
        # Try to get schema info
        schema_rows = query_db(DB_COUNTRY, "SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in (schema_rows or [])]
        
        results.append({
            "check": "DB vs JSON - query word count from DB",
            "path": str(DB_COUNTRY),
            "ok": False,
            "details": f"Could not query word count. Tables: {tables}"
        })
        log_warn(f"Could not query word count from stats_country.db. Tables: {tables}")
        return
    
    log_info(f"DB word count for {country}: {db_word_count:,}")
    
    # Compare with tolerance
    if json_word_count > 0:
        delta_pct = abs(db_word_count - json_word_count) / json_word_count * 100
    else:
        delta_pct = 100 if db_word_count > 0 else 0
    
    ok = delta_pct <= 1.0  # 1% tolerance
    
    results.append({
        "check": f"DB vs JSON - word count consistency ({country})",
        "path": str(DB_COUNTRY),
        "ok": ok,
        "details": f"JSON: {json_word_count:,}, DB: {db_word_count:,}, Δ {delta_pct:.2f}%"
    })
    
    if ok:
        log_ok(f"Word count consistent (Δ {delta_pct:.2f}%)")
    else:
        log_fail(f"Word count mismatch: JSON={json_word_count:,}, DB={db_word_count:,}, Δ {delta_pct:.2f}%")


def check_csv_consistency(country: str, results: list[dict]) -> None:
    """Check CSV file consistency with other data sources."""
    
    print("\n" + "-" * 70)
    print("CHECK: CSV Consistency (Step 04)")
    print("-" * 70)
    
    # Check CSV files exist
    per_country_csv = RESULTS_DIR / "corpus_statistics.csv"
    across_csv = RESULTS_DIR / "corpus_statistics_across_countries.csv"
    
    check_exists(per_country_csv, "CSV - corpus_statistics.csv", results, min_size=100)
    check_exists(across_csv, "CSV - corpus_statistics_across_countries.csv", results, min_size=100)
    
    if not per_country_csv.exists() or not across_csv.exists():
        return
    
    # Load CSVs
    per_country_rows = load_csv_simple(per_country_csv)
    across_rows = load_csv_simple(across_csv)
    
    if not per_country_rows or not across_rows:
        results.append({
            "check": "CSV - load data",
            "path": str(RESULTS_DIR),
            "ok": False,
            "details": "Failed to load CSV files"
        })
        return
    
    # Find TOTAL_ALL_COUNTRIES
    total_all = None
    for row in across_rows:
        if row.get("category") == "TOTAL_ALL_COUNTRIES":
            total_all = int(row.get("word_count", 0))
            break
    
    # Find TOTAL for country
    country_total = None
    for row in per_country_rows:
        if row.get("category") == "TOTAL" and row.get("country_code") == country:
            country_total = int(row.get("word_count", 0))
            break
    
    log_info(f"CSV TOTAL_ALL_COUNTRIES: {total_all:,}" if total_all else "TOTAL_ALL_COUNTRIES not found")
    log_info(f"CSV TOTAL for {country}: {country_total:,}" if country_total else f"TOTAL for {country} not found")
    
    # Check TOTAL_ALL_COUNTRIES consistency
    if total_all is not None:
        # Sum all country TOTALs
        sum_country_totals = 0
        for row in per_country_rows:
            if row.get("category") == "TOTAL":
                sum_country_totals += int(row.get("word_count", 0))
        
        if sum_country_totals > 0:
            delta_pct = abs(total_all - sum_country_totals) / sum_country_totals * 100
            ok = delta_pct <= 1.0
            
            results.append({
                "check": "CSV - TOTAL_ALL_COUNTRIES vs sum of TOTALs",
                "path": str(across_csv),
                "ok": ok,
                "details": f"All: {total_all:,}, Sum: {sum_country_totals:,}, Δ {delta_pct:.2f}%"
            })
            
            if ok:
                log_ok(f"TOTAL_ALL_COUNTRIES consistent (Δ {delta_pct:.2f}%)")
            else:
                log_fail(f"TOTAL_ALL_COUNTRIES mismatch: {total_all:,} vs sum {sum_country_totals:,}")
    
    # Check country total vs JSON
    if country_total:
        transcript_dir = TRANSCRIPTS_DIR / country
        json_word_count = 0
        
        if transcript_dir.exists():
            for jf in transcript_dir.glob("*.json"):
                json_word_count += count_words_in_json(jf)
        
        if json_word_count > 0:
            delta_pct = abs(country_total - json_word_count) / json_word_count * 100
            ok = delta_pct <= 5.0  # 5% tolerance (due to punctuation filtering)
            
            results.append({
                "check": f"CSV - {country} TOTAL vs JSON word count",
                "path": str(per_country_csv),
                "ok": ok,
                "details": f"CSV: {country_total:,}, JSON: {json_word_count:,}, Δ {delta_pct:.2f}%"
            })
            
            if ok:
                log_ok(f"CSV vs JSON word count consistent (Δ {delta_pct:.2f}%)")
            else:
                log_fail(f"CSV vs JSON mismatch: CSV={country_total:,}, JSON={json_word_count:,}, Δ {delta_pct:.2f}%")


def check_published_outputs(country: str, results: list[dict]) -> None:
    """Check published visualization outputs (Step 05)."""
    
    print("\n" + "-" * 70)
    print("CHECK: Published Outputs (Step 05)")
    print("-" * 70)
    
    # Expected files
    expected_files = [
        ("viz_total_corpus.png", 1000),
        ("viz_genero_profesionales.png", 1000),
        ("viz_modo_genero_profesionales.png", 1000),
        (f"viz_{country}_resumen.png", 1000),
        ("corpus_stats.json", 100),
    ]
    
    for filename, min_size in expected_files:
        path = STATS_IMG_DIR / filename
        check_exists(path, f"Published - {filename}", results, min_size=min_size)
    
    # Load and verify corpus_stats.json
    stats_json_path = STATS_IMG_DIR / "corpus_stats.json"
    if stats_json_path.exists():
        stats_data = load_json(stats_json_path)
        
        if stats_data:
            # Check structure
            all_countries = stats_data.get("all_countries", {})
            countries_data = stats_data.get("countries", {})
            
            # Check all_countries.total exists
            total_word_count = all_countries.get("total", {}).get("word_count", 0)
            
            ok = total_word_count > 0
            results.append({
                "check": "Published - corpus_stats.json has total word count",
                "path": str(stats_json_path),
                "ok": ok,
                "details": f"word_count: {total_word_count:,}"
            })
            if ok:
                log_ok(f"corpus_stats.json total: {total_word_count:,}")
            else:
                log_fail("corpus_stats.json missing total word count")
            
            # Check country exists in JSON
            country_data = countries_data.get(country, {})
            country_wc = country_data.get("total", {}).get("word_count", 0)
            
            ok = country_wc > 0
            results.append({
                "check": f"Published - corpus_stats.json has {country} data",
                "path": str(stats_json_path),
                "ok": ok,
                "details": f"word_count: {country_wc:,}"
            })
            if ok:
                log_ok(f"corpus_stats.json {country}: {country_wc:,}")
            else:
                log_fail(f"corpus_stats.json missing {country} data")
            
            # Cross-check with CSV
            across_csv = RESULTS_DIR / "corpus_statistics_across_countries.csv"
            if across_csv.exists():
                across_rows = load_csv_simple(across_csv)
                if across_rows:
                    csv_total = None
                    for row in across_rows:
                        if row.get("category") == "TOTAL_ALL_COUNTRIES":
                            csv_total = int(row.get("word_count", 0))
                            break
                    
                    if csv_total and total_word_count:
                        delta_pct = abs(csv_total - total_word_count) / csv_total * 100 if csv_total > 0 else 0
                        ok = delta_pct <= 1.0
                        
                        results.append({
                            "check": "Published - corpus_stats.json matches CSV total",
                            "path": str(stats_json_path),
                            "ok": ok,
                            "details": f"JSON: {total_word_count:,}, CSV: {csv_total:,}, Δ {delta_pct:.2f}%"
                        })
                        if ok:
                            log_ok(f"corpus_stats.json matches CSV (Δ {delta_pct:.2f}%)")
                        else:
                            log_fail(f"corpus_stats.json vs CSV mismatch: {total_word_count:,} vs {csv_total:,}")
        else:
            results.append({
                "check": "Published - corpus_stats.json loadable",
                "path": str(stats_json_path),
                "ok": False,
                "details": "Failed to parse JSON"
            })


# ==============================================================================
# REPORT GENERATION
# ==============================================================================

def summarize_results(results: list[dict], country: str, limit: int) -> None:
    """Print and save results summary."""
    
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count
    
    print("\n" + "=" * 70)
    print("JSON-PIPELINE QA REPORT")
    print("=" * 70)
    print(f"Country:      {country}")
    print(f"Limit:        {limit}")
    print(f"Total checks: {len(results)}")
    print(f"OK:           {ok_count}")
    print(f"FAIL:         {fail_count}")
    print("-" * 70)
    
    # Print failed checks
    if fail_count > 0:
        print("\nFAILED CHECKS:")
        for r in results:
            if not r["ok"]:
                print(f"  [FAIL] {r['check']}")
                if r["details"]:
                    print(f"         {r['details']}")
    
    # Print summary status
    print("\n" + "-" * 70)
    if fail_count == 0:
        print("STATUS: ALL CHECKS PASSED ✓")
    else:
        print(f"STATUS: {fail_count} CHECK(S) FAILED ✗")
    print("=" * 70)
    
    # Save JSON report
    report = {
        "generated": datetime.now().isoformat(),
        "country": country,
        "limit": limit,
        "total_checks": len(results),
        "ok_count": ok_count,
        "fail_count": fail_count,
        "checks": results
    }
    
    try:
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\nReport saved to: {REPORT_PATH}")
    except Exception as e:
        print(f"\nFailed to save report: {e}")


# ==============================================================================
# CLI ARGUMENT PARSING
# ==============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="QA/Regression script for the JSON pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python 99_check_pipeline_json.py                     # Auto-detect country, limit=2
  python 99_check_pipeline_json.py --country ARG      # Use ARG with limit=2
  python 99_check_pipeline_json.py --country USA --limit 5
  python 99_check_pipeline_json.py --skip-steps        # Only run checks, skip pipeline
        """
    )
    
    parser.add_argument(
        "--country", "-c",
        type=str,
        default=None,
        help="Country code to test (default: auto-detect first available)"
    )
    
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=2,
        help="Number of files to process per step (default: 2)"
    )
    
    parser.add_argument(
        "--skip-steps",
        action="store_true",
        help="Skip running pipeline steps, only run checks on existing data"
    )
    
    parser.add_argument(
        "--run-all",
        action="store_true",
        default=True,
        help="Run all pipeline steps (default: True)"
    )
    
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue running steps even if one fails"
    )
    
    parser.add_argument(
        "--skip-step",
        type=str,
        action="append",
        default=[],
        help="Skip specific steps (e.g., --skip-step 01 --skip-step 02)"
    )
    
    return parser.parse_args()


# ==============================================================================
# MAIN
# ==============================================================================

def main() -> int:
    """Main execution function."""
    args = parse_args()
    
    # Determine country
    country = args.country
    if not country:
        country = find_first_country_with_data()
        if not country:
            # Fallback to a known country from transcripts
            for d in TRANSCRIPTS_DIR.iterdir():
                if d.is_dir() and d.name not in [".gitkeep", "edit_log.jsonl"]:
                    country = d.name
                    break
    
    if not country:
        print("[ERROR] No country could be determined. Please specify --country")
        return 1
    
    print("=" * 70)
    print("CO.RA.PAN JSON-PIPELINE QA CHECK")
    print("=" * 70)
    print(f"Script dir:   {SCRIPT_DIR}")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Country:      {country}")
    print(f"Limit:        {args.limit}")
    print(f"Skip steps:   {args.skip_steps}")
    print("=" * 70)
    
    results: list[dict] = []
    
    # Run pipeline steps (unless skipped)
    if not args.skip_steps:
        run_pipeline_steps(country, args.limit, results, 
                          skip_steps=args.skip_step,
                          continue_on_error=args.continue_on_error)
    else:
        log_info("Skipping pipeline execution (--skip-steps)")
    
    # Run consistency checks
    print("\n" + "=" * 70)
    print("RUNNING CONSISTENCY CHECKS")
    print("=" * 70)
    
    check_json_structure(country, results)
    check_db_vs_json(country, results)
    check_csv_consistency(country, results)
    check_published_outputs(country, results)
    
    # Generate summary
    summarize_results(results, country, args.limit)
    
    # Return exit code
    fail_count = sum(1 for r in results if not r["ok"])
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
