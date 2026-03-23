#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
04_internal_country_statistics.py

Pipeline-Schritt 04: Erstellt detaillierte Korpus-Statistiken PRO LAND aus JSON-Transkripten.

EINGABEPFAD:  media/transcripts/<country>/*.json (v3-Schema)

KATEGORIEN:
- Speaker Type (pro/otro)
- Sex (m/f)
- Mode (lectura/libre/pre/n/a)
- Discourse (general/tiempo/tránsito)

OUTPUT:
- CSV mit allen Statistiken (Word Count, Duration, Percentages)
- Visualisierungen für pro+general Kombinationen
- Alle Ergebnisse in: LOKAL/_1_json/results/

VERWENDUNG:
    python 04_internal_country_statistics.py
    python 04_internal_country_statistics.py --country USA --limit 5
    python 04_internal_country_statistics.py --country ARG,ESP

PIPELINE-REIHENFOLGE:
    01_preprocess_transcripts.py  → json-ready/
    02_annotate_transcripts_v3.py → media/transcripts/<country>/
    03_build_metadata_stats.py    → data/db/*.db
    04_internal_country_statistics.py → results/*.csv, results/*.png (this script)

Copyright (c) 2025 CO.RA.PAN Project
"""

import sys
import io
import json
import argparse
import importlib.util
try:
    import pandas as pd
    HAS_PANDAS = True
except Exception:
    pd = None
    HAS_PANDAS = False
import string
import traceback
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

# Force UTF-8 encoding for console output (Windows compatibility)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # LOKAL/_1_json -> PROJECT_ROOT
TRANSCRIPTS_DIR = PROJECT_ROOT / "media" / "transcripts"
OUTPUT_DIR = SCRIPT_DIR / "results"

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Country-Code-Normalisierung importieren
COUNTRIES_PY = PROJECT_ROOT / "src" / "app" / "config" / "countries.py"

def load_country_normalizer():
    """Lädt normalize_country_code aus countries.py."""
    if not COUNTRIES_PY.exists():
        # Fallback wenn Modul nicht gefunden
        return lambda x: x.upper().strip() if x else ""
    
    spec = importlib.util.spec_from_file_location("countries_module", COUNTRIES_PY)
    if spec is None or getattr(spec, 'loader', None) is None:
        # Fallback wenn Modul nicht geladen werden kann
        return lambda x: x.upper().strip() if x else ""

    try:
        module = importlib.util.module_from_spec(spec)
        sys.modules['countries_module'] = module
        spec.loader.exec_module(module)
        return module.normalize_country_code
    except Exception:
        return lambda x: x.upper().strip() if x else ""

normalize_country_code = load_country_normalizer()

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def seconds_to_hms(seconds):
    """Convert seconds to HH:MM:SS format."""
    if seconds is None or seconds < 0:
        seconds = 0
    hrs, r = divmod(seconds, 3600)
    mins, secs = divmod(r, 60)
    return f"{int(hrs):02d}:{int(mins):02d}:{int(secs):02d}"

def is_valid_token(text):
    """Check if token should be counted (exclude punctuation)."""
    ignored_tokens = {"(", ")", "[", "]", "!", "(..)", "(.)", "(..", "(..).", "(..),", ").", ")]", ",", "."}
    
    if not text or text in ignored_tokens:
        return False
    
    # Ignore pure punctuation
    if all(ch in string.punctuation for ch in text):
        return False
    
    return True

# ==============================================================================
# JSON DATA LOADING
# ==============================================================================

def collect_json_files(countries: list[str] | None = None, limit_files: int | None = None) -> list[Path]:
    """
    Sammelt alle JSON-Dateien aus dem Transkript-Verzeichnis.
    
    Args:
        countries: Optional, Liste von Ländercodes (z.B. ["ARG", "ESP"])
        limit_files: Optional, maximale Anzahl Dateien (für Tests)
    
    Returns:
        Liste von Pfaden
    """
    if not TRANSCRIPTS_DIR.exists():
        print(f"[ERROR] Transcripts directory not found: {TRANSCRIPTS_DIR}")
        return []
    
    json_files: list[Path] = []
    
    # Sortierte Länderverzeichnisse
    country_dirs = sorted([d for d in TRANSCRIPTS_DIR.iterdir() if d.is_dir()])
    
    for country_dir in country_dirs:
        # Filter auf Länder
        if countries:
            normalized_countries = [normalize_country_code(c) for c in countries]
            if normalize_country_code(country_dir.name) not in normalized_countries:
                continue
        
        # Sortierte JSON-Dateien
        country_files = sorted(country_dir.glob("*.json"))
        json_files.extend(country_files)
    
    # Limit anwenden
    if limit_files and limit_files > 0:
        json_files = json_files[:limit_files]
    
    return json_files


def load_data_from_json(countries: list[str] | None = None, limit_files: int | None = None) -> pd.DataFrame | None: # pyright: ignore[reportInvalidTypeForm]
    """
    Load all relevant data from JSON transcript files.
    
    Args:
        countries: Optional, Liste von Ländercodes zum Filtern
        limit_files: Optional, maximale Anzahl Dateien (für Tests)
    
    Returns:
        DataFrame mit Spalten: country_code, speaker_type, sex, mode, discourse, text, start, end, duration
        oder None bei Fehler
    """
    print("\n[*] Loading data from JSON transcripts...")
    
    json_files = collect_json_files(countries=countries, limit_files=limit_files)
    
    if not json_files:
        print("[ERROR] No JSON files found!")
        return None
    
    print(f"[OK] Found {len(json_files)} JSON files")
    
    rows = []
    files_processed = 0
    files_skipped = 0
    
    for jf in json_files:
        try:
            with open(jf, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            
            # Country code bestimmen
            country_code = data.get("country_code")
            if not country_code:
                country_code = jf.parent.name
            country_code = normalize_country_code(country_code)
            
            # Segmente iterieren
            for seg in data.get("segments", []):
                speaker = seg.get("speaker", {})
                
                # Sprecherattribute
                speaker_type = speaker.get("speaker_type", "")
                sex = speaker.get("speaker_sex", "")
                mode = speaker.get("speaker_mode", "")
                discourse = speaker.get("speaker_discourse", "")
                
                # Wörter iterieren
                for w in seg.get("words", []):
                    text = w.get("text", "")
                    
                    # Zeit bestimmen (v3: start_ms/end_ms, v2 fallback: start/end)
                    if "start_ms" in w:
                        start_ms = w.get("start_ms", 0)
                        end_ms = w.get("end_ms", 0)
                        start_sec = start_ms / 1000.0
                        end_sec = end_ms / 1000.0
                    else:
                        # v2 Fallback: start/end sind bereits in Sekunden
                        start_sec = float(w.get("start", 0))
                        end_sec = float(w.get("end", 0))
                    
                    duration_sec = end_sec - start_sec
                    
                    rows.append({
                        "country_code": country_code,
                        "speaker_type": speaker_type,
                        "sex": sex,
                        "mode": mode,
                        "discourse": discourse,
                        "text": text,
                        "start": start_sec,
                        "end": end_sec,
                        "duration": duration_sec
                    })
            
            files_processed += 1
            
        except json.JSONDecodeError as e:
            print(f"  [WARN] JSON decode error in {jf.name}: {e}")
            files_skipped += 1
        except Exception as e:
            print(f"  [WARN] Error processing {jf.name}: {e}")
            files_skipped += 1
    
    print(f"  Processed: {files_processed} files")
    if files_skipped > 0:
        print(f"  Skipped: {files_skipped} files (errors)")
    
    if not rows:
        print("[ERROR] No tokens extracted from JSON files!")
        return None
    
    df = pd.DataFrame(rows)
    print(f"[OK] Loaded {len(df):,} tokens from JSON files")
    
    # Filter valid tokens
    df['is_valid'] = df['text'].apply(is_valid_token)
    df_filtered = df[df['is_valid']].copy()
    
    excluded = len(df) - len(df_filtered)
    print(f"  Excluded {excluded:,} punctuation tokens")
    print(f"  Valid tokens: {len(df_filtered):,}")
    
    return df_filtered

# ==============================================================================
# STATISTICS GENERATION
# ==============================================================================

def generate_statistics(df):
    """Generate all statistics combinations per country."""
    print("\n[*] Generating statistics...")
    
    results = []
    countries = sorted(df['country_code'].unique())
    
    for country in countries:
        df_country = df[df['country_code'] == country]
        total_words = len(df_country)
        total_duration = df_country['duration'].sum()
        
        print(f"\n  Processing: {country}")
        print(f"    Total: {total_words:,} words, {seconds_to_hms(total_duration)}")
        
        # 1. TOTAL per country
        results.append({
            'country_code': country,
            'category': 'TOTAL',
            'speaker_type': '',
            'sex': '',
            'mode': '',
            'discourse': '',
            'word_count': total_words,
            'duration_sec': round(total_duration, 2),
            'duration_hms': seconds_to_hms(total_duration),
            'percent': 100.0
        })
        
        # 2. BY SPEAKER TYPE
        for speaker_type in df_country['speaker_type'].unique():
            if pd.isna(speaker_type) or speaker_type == '':
                continue
            df_sp = df_country[df_country['speaker_type'] == speaker_type]
            wc = len(df_sp)
            dur = df_sp['duration'].sum()
            results.append({
                'country_code': country,
                'category': speaker_type,
                'speaker_type': speaker_type,
                'sex': '',
                'mode': '',
                'discourse': '',
                'word_count': wc,
                'duration_sec': round(dur, 2),
                'duration_hms': seconds_to_hms(dur),
                'percent': round(100 * wc / total_words, 2)
            })
        
        # 3. BY SEX
        for sex in df_country['sex'].unique():
            if pd.isna(sex) or sex == '':
                continue
            df_sex = df_country[df_country['sex'] == sex]
            wc = len(df_sex)
            dur = df_sex['duration'].sum()
            results.append({
                'country_code': country,
                'category': f'sex_{sex}',
                'speaker_type': '',
                'sex': sex,
                'mode': '',
                'discourse': '',
                'word_count': wc,
                'duration_sec': round(dur, 2),
                'duration_hms': seconds_to_hms(dur),
                'percent': round(100 * wc / total_words, 2)
            })
        
        # 4. BY MODE
        for mode in df_country['mode'].unique():
            if pd.isna(mode) or mode == '':
                continue
            df_mode = df_country[df_country['mode'] == mode]
            wc = len(df_mode)
            dur = df_mode['duration'].sum()
            results.append({
                'country_code': country,
                'category': f'mode_{mode}',
                'speaker_type': '',
                'sex': '',
                'mode': mode,
                'discourse': '',
                'word_count': wc,
                'duration_sec': round(dur, 2),
                'duration_hms': seconds_to_hms(dur),
                'percent': round(100 * wc / total_words, 2)
            })
        
        # 5. BY DISCOURSE
        for discourse in df_country['discourse'].unique():
            if pd.isna(discourse) or discourse == '':
                continue
            df_disc = df_country[df_country['discourse'] == discourse]
            wc = len(df_disc)
            dur = df_disc['duration'].sum()
            results.append({
                'country_code': country,
                'category': f'discourse_{discourse}',
                'speaker_type': '',
                'sex': '',
                'mode': '',
                'discourse': discourse,
                'word_count': wc,
                'duration_sec': round(dur, 2),
                'duration_hms': seconds_to_hms(dur),
                'percent': round(100 * wc / total_words, 2)
            })
        
        # 6. SPEAKER_TYPE + SEX
        for speaker_type in df_country['speaker_type'].unique():
            if pd.isna(speaker_type) or speaker_type == '':
                continue
            for sex in df_country['sex'].unique():
                if pd.isna(sex) or sex == '':
                    continue
                df_comb = df_country[
                    (df_country['speaker_type'] == speaker_type) &
                    (df_country['sex'] == sex)
                ]
                if len(df_comb) == 0:
                    continue
                wc = len(df_comb)
                dur = df_comb['duration'].sum()
                results.append({
                    'country_code': country,
                    'category': f'{speaker_type}_{sex}',
                    'speaker_type': speaker_type,
                    'sex': sex,
                    'mode': '',
                    'discourse': '',
                    'word_count': wc,
                    'duration_sec': round(dur, 2),
                    'duration_hms': seconds_to_hms(dur),
                    'percent': round(100 * wc / total_words, 2)
                })
        
        # 7. SPEAKER_TYPE + MODE
        for speaker_type in df_country['speaker_type'].unique():
            if pd.isna(speaker_type) or speaker_type == '':
                continue
            for mode in df_country['mode'].unique():
                if pd.isna(mode) or mode == '':
                    continue
                df_comb = df_country[
                    (df_country['speaker_type'] == speaker_type) &
                    (df_country['mode'] == mode)
                ]
                if len(df_comb) == 0:
                    continue
                wc = len(df_comb)
                dur = df_comb['duration'].sum()
                results.append({
                    'country_code': country,
                    'category': f'{speaker_type}_{mode}',
                    'speaker_type': speaker_type,
                    'sex': '',
                    'mode': mode,
                    'discourse': '',
                    'word_count': wc,
                    'duration_sec': round(dur, 2),
                    'duration_hms': seconds_to_hms(dur),
                    'percent': round(100 * wc / total_words, 2)
                })
        
        # 8. SPEAKER_TYPE + SEX + MODE (most detailed)
        for speaker_type in df_country['speaker_type'].unique():
            if pd.isna(speaker_type) or speaker_type == '':
                continue
            for sex in df_country['sex'].unique():
                if pd.isna(sex) or sex == '':
                    continue
                for mode in df_country['mode'].unique():
                    if pd.isna(mode) or mode == '':
                        continue
                    df_comb = df_country[
                        (df_country['speaker_type'] == speaker_type) &
                        (df_country['sex'] == sex) &
                        (df_country['mode'] == mode)
                    ]
                    if len(df_comb) == 0:
                        continue
                    wc = len(df_comb)
                    dur = df_comb['duration'].sum()
                    results.append({
                        'country_code': country,
                        'category': f'{speaker_type}_{sex}_{mode}',
                        'speaker_type': speaker_type,
                        'sex': sex,
                        'mode': mode,
                        'discourse': '',
                        'word_count': wc,
                        'duration_sec': round(dur, 2),
                        'duration_hms': seconds_to_hms(dur),
                        'percent': round(100 * wc / total_words, 2)
                    })
        
        # 9. SPEAKER_TYPE + DISCOURSE
        for speaker_type in df_country['speaker_type'].unique():
            if pd.isna(speaker_type) or speaker_type == '':
                continue
            for discourse in df_country['discourse'].unique():
                if pd.isna(discourse) or discourse == '':
                    continue
                df_comb = df_country[
                    (df_country['speaker_type'] == speaker_type) &
                    (df_country['discourse'] == discourse)
                ]
                if len(df_comb) == 0:
                    continue
                wc = len(df_comb)
                dur = df_comb['duration'].sum()
                results.append({
                    'country_code': country,
                    'category': f'{speaker_type}_{discourse}',
                    'speaker_type': speaker_type,
                    'sex': '',
                    'mode': '',
                    'discourse': discourse,
                    'word_count': wc,
                    'duration_sec': round(dur, 2),
                    'duration_hms': seconds_to_hms(dur),
                    'percent': round(100 * wc / total_words, 2)
                })
        
        # 10. SPEAKER_TYPE + SEX + DISCOURSE
        for speaker_type in df_country['speaker_type'].unique():
            if pd.isna(speaker_type) or speaker_type == '':
                continue
            for sex in df_country['sex'].unique():
                if pd.isna(sex) or sex == '':
                    continue
                for discourse in df_country['discourse'].unique():
                    if pd.isna(discourse) or discourse == '':
                        continue
                    df_comb = df_country[
                        (df_country['speaker_type'] == speaker_type) &
                        (df_country['sex'] == sex) &
                        (df_country['discourse'] == discourse)
                    ]
                    if len(df_comb) == 0:
                        continue
                    wc = len(df_comb)
                    dur = df_comb['duration'].sum()
                    results.append({
                        'country_code': country,
                        'category': f'{speaker_type}_{sex}_{discourse}',
                        'speaker_type': speaker_type,
                        'sex': sex,
                        'mode': '',
                        'discourse': discourse,
                        'word_count': wc,
                        'duration_sec': round(dur, 2),
                        'duration_hms': seconds_to_hms(dur),
                        'percent': round(100 * wc / total_words, 2)
                    })
    
    df_results = pd.DataFrame(results)
    print(f"\n[OK] Generated {len(df_results)} statistical entries")
    
    return df_results

# ==============================================================================
# ACROSS-COUNTRY STATISTICS
# ==============================================================================

def generate_across_country_statistics(df):
    """Generate statistics across all countries."""
    print("\n[*] Generating across-country statistics...")
    
    results = []
    
    # Total across all countries
    total_words = len(df)
    total_duration = df['duration'].sum()
    
    results.append({
        'category': 'TOTAL_ALL_COUNTRIES',
        'speaker_type': '',
        'sex': '',
        'mode': '',
        'word_count': total_words,
        'duration_sec': round(total_duration, 2),
        'duration_hms': seconds_to_hms(total_duration),
        'percent': 100.0
    })
    
    # 1. PRO vs. OTRO across all countries
    for speaker_type in df['speaker_type'].unique():
        if pd.isna(speaker_type) or speaker_type == '':
            continue
        df_sp = df[df['speaker_type'] == speaker_type]
        wc = len(df_sp)
        dur = df_sp['duration'].sum()
        results.append({
            'category': speaker_type,
            'speaker_type': speaker_type,
            'sex': '',
            'mode': '',
            'word_count': wc,
            'duration_sec': round(dur, 2),
            'duration_hms': seconds_to_hms(dur),
            'percent': round(100 * wc / total_words, 2)
        })
    
    # 2. PRO-F vs. PRO-M (sum of all lectura+libre)
    for sex in ['m', 'f']:
        df_pro_sex = df[(df['speaker_type'] == 'pro') & (df['sex'] == sex)]
        wc = len(df_pro_sex)
        dur = df_pro_sex['duration'].sum()
        results.append({
            'category': f'pro_{sex}',
            'speaker_type': 'pro',
            'sex': sex,
            'mode': '',
            'word_count': wc,
            'duration_sec': round(dur, 2),
            'duration_hms': seconds_to_hms(dur),
            'percent': round(100 * wc / total_words, 2)
        })
    
    # 3. PRO-LECTURA-F vs. PRO-LECTURA-M
    for sex in ['m', 'f']:
        df_lec = df[
            (df['speaker_type'] == 'pro') & 
            (df['sex'] == sex) & 
            (df['mode'] == 'lectura')
        ]
        wc = len(df_lec)
        dur = df_lec['duration'].sum()
        results.append({
            'category': f'pro_lectura_{sex}',
            'speaker_type': 'pro',
            'sex': sex,
            'mode': 'lectura',
            'word_count': wc,
            'duration_sec': round(dur, 2),
            'duration_hms': seconds_to_hms(dur),
            'percent': round(100 * wc / total_words, 2)
        })
    
    # 4. PRO-LIBRE-F vs. PRO-LIBRE-M
    for sex in ['m', 'f']:
        df_lib = df[
            (df['speaker_type'] == 'pro') & 
            (df['sex'] == sex) & 
            (df['mode'] == 'libre')
        ]
        wc = len(df_lib)
        dur = df_lib['duration'].sum()
        results.append({
            'category': f'pro_libre_{sex}',
            'speaker_type': 'pro',
            'sex': sex,
            'mode': 'libre',
            'word_count': wc,
            'duration_sec': round(dur, 2),
            'duration_hms': seconds_to_hms(dur),
            'percent': round(100 * wc / total_words, 2)
        })
    
    # 5. PRO-PRE-F vs. PRO-PRE-M
    for sex in ['m', 'f']:
        df_pre = df[
            (df['speaker_type'] == 'pro') & 
            (df['sex'] == sex) & 
            (df['mode'] == 'pre')
        ]
        wc = len(df_pre)
        dur = df_pre['duration'].sum()
        results.append({
            'category': f'pro_pre_{sex}',
            'speaker_type': 'pro',
            'sex': sex,
            'mode': 'pre',
            'word_count': wc,
            'duration_sec': round(dur, 2),
            'duration_hms': seconds_to_hms(dur),
            'percent': round(100 * wc / total_words, 2)
        })
    
    # 6. PRO-N/A-F vs. PRO-N/A-M (tiempo + tránsito discourse types)
    for sex in ['m', 'f']:
        df_na = df[
            (df['speaker_type'] == 'pro') & 
            (df['sex'] == sex) & 
            (df['mode'] == 'n/a')
        ]
        wc = len(df_na)
        dur = df_na['duration'].sum()
        results.append({
            'category': f'pro_na_{sex}',
            'speaker_type': 'pro',
            'sex': sex,
            'mode': 'n/a',
            'word_count': wc,
            'duration_sec': round(dur, 2),
            'duration_hms': seconds_to_hms(dur),
            'percent': round(100 * wc / total_words, 2)
        })
    
    df_across = pd.DataFrame(results)
    print(f"[OK] Generated {len(df_across)} across-country entries")
    
    return df_across

# ==============================================================================
# CSV EXPORT
# ==============================================================================

def export_to_csv(df_results, df_across):
    """Export results to CSV (overwrite existing)."""
    csv_path = OUTPUT_DIR / "corpus_statistics.csv"
    csv_across_path = OUTPUT_DIR / "corpus_statistics_across_countries.csv"
    
    df_results.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"\n[SAVE] CSV saved: {csv_path}")
    
    df_across.to_csv(csv_across_path, index=False, encoding='utf-8-sig')
    print(f"[SAVE] Across-country CSV saved: {csv_across_path}")
    
    return csv_path, csv_across_path

# ==============================================================================
# VISUALIZATION
# ==============================================================================

def create_visualizations(df_results):
    """Create visualizations for pro speakers with mode breakdown."""
    print("\n[*] Creating visualizations (pro speakers, mode breakdown)...")
    
    # Filter: Only entries with speaker_type='pro'
    # We want the detailed sex+mode combinations (e.g., pro_m_lectura, pro_f_libre)
    # These have sex and mode filled, but discourse is empty (they are mode-focused stats)
    df_viz = df_results[
        (df_results['speaker_type'] == 'pro') &
        (df_results['sex'] != '') &
        (df_results['mode'] != '') &
        (df_results['discourse'] == '')  # These are the sex+mode combinations
    ].copy()
    
    if len(df_viz) == 0:
        print("[WARN] No pro+sex+mode data found for visualization")
        return
    
    print(f"  Visualizing {len(df_viz)} pro entries")
    
    countries = sorted(df_viz['country_code'].unique())
    
    for country in countries:
        df_country = df_viz[df_viz['country_code'] == country]
        
        if len(df_country) == 0:
            continue
        
        # Sort by word count
        df_country = df_country.sort_values('word_count', ascending=True)
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle(f'{country} - PRO Speakers (Mode Breakdown)', fontsize=16, fontweight='bold')
        
        # Plot 1: Word Count
        categories = df_country['category'].values
        word_counts = df_country['word_count'].values
        
        ax1.barh(range(len(categories)), word_counts, color='steelblue')
        ax1.set_yticks(range(len(categories)))
        ax1.set_yticklabels(categories)
        ax1.set_xlabel('Word Count')
        ax1.set_title('Words per Category')
        ax1.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, v in enumerate(word_counts):
            ax1.text(v + max(word_counts)*0.01, i, f'{v:,}', va='center')
        
        # Plot 2: Duration
        durations = df_country['duration_sec'].values
        
        ax2.barh(range(len(categories)), durations, color='coral')
        ax2.set_yticks(range(len(categories)))
        ax2.set_yticklabels(categories)
        ax2.set_xlabel('Duration (seconds)')
        ax2.set_title('Audio Duration per Category')
        ax2.grid(axis='x', alpha=0.3)
        
        # Add value labels with HH:MM:SS
        for i, (v, hms) in enumerate(zip(durations, df_country['duration_hms'].values)):
            ax2.text(v + max(durations)*0.01, i, hms, va='center')
        
        plt.tight_layout()
        
        # Save figure (overwrite existing)
        fig_path = OUTPUT_DIR / f"viz_{country}_pro_modes.png"
        plt.savefig(fig_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  [OK] Saved: {fig_path.name}")

def create_across_country_visualizations(df_across):
    """Create visualizations for across-country statistics."""
    print("\n[*] Creating across-country visualizations...")
    
    # Filter for pro speakers with sex and mode specified
    df_viz = df_across[
        (df_across['speaker_type'] == 'pro') &
        (df_across['sex'] != '') &
        (df_across['mode'] != '')
    ].copy()
    
    if len(df_viz) == 0:
        print("[WARN] No across-country pro data for visualization")
        return
    
    # Sort by word count
    df_viz = df_viz.sort_values('word_count', ascending=True)
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle('ALL COUNTRIES - PRO Speakers (Mode Breakdown)', fontsize=16, fontweight='bold')
    
    # Plot 1: Word Count
    categories = df_viz['category'].values
    word_counts = df_viz['word_count'].values
    
    ax1.barh(range(len(categories)), word_counts, color='steelblue')
    ax1.set_yticks(range(len(categories)))
    ax1.set_yticklabels(categories)
    ax1.set_xlabel('Word Count')
    ax1.set_title('Words per Category')
    ax1.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, v in enumerate(word_counts):
        ax1.text(v + max(word_counts)*0.01, i, f'{v:,}', va='center', fontsize=9)
    
    # Plot 2: Duration
    durations = df_viz['duration_sec'].values
    
    ax2.barh(range(len(categories)), durations, color='coral')
    ax2.set_yticks(range(len(categories)))
    ax2.set_yticklabels(categories)
    ax2.set_xlabel('Duration (seconds)')
    ax2.set_title('Audio Duration per Category')
    ax2.grid(axis='x', alpha=0.3)
    
    # Add value labels with HH:MM:SS
    for i, (v, hms) in enumerate(zip(durations, df_viz['duration_hms'].values)):
        ax2.text(v + max(durations)*0.01, i, hms, va='center', fontsize=9)
    
    plt.tight_layout()
    
    # Save figure
    fig_path = OUTPUT_DIR / "viz_ALL_COUNTRIES_pro_modes.png"
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  [OK] Saved: {fig_path.name}")

def create_gender_gap_analysis(df_results):
    """Create gender gap analysis and visualizations per country."""
    print("\n[*] Creating gender gap analysis...")
    
    results = []
    countries = sorted(df_results['country_code'].unique())
    
    for country in countries:
        df_country = df_results[df_results['country_code'] == country]
        
        # Get PRO-M and PRO-F (all modes)
        pro_m = df_country[df_country['category'] == 'pro_m']
        pro_f = df_country[df_country['category'] == 'pro_f']
        
        if not pro_m.empty and not pro_f.empty:
            m_count = pro_m.iloc[0]['word_count']
            f_count = pro_f.iloc[0]['word_count']
            
            if f_count > 0:
                gap_percent = ((m_count - f_count) / f_count) * 100
                dominant = 'M' if m_count > f_count else 'F'
            else:
                gap_percent = 100.0 if m_count > 0 else 0.0
                dominant = 'M' if m_count > 0 else 'F'
            
            results.append({
                'country': country,
                'category': 'PRO (all modes)',
                'pro_m': m_count,
                'pro_f': f_count,
                'gap_percent': round(gap_percent, 1),
                'dominant': dominant
            })
        
        # Get PRO-LECTURA-M and PRO-LECTURA-F
        lec_m = df_country[df_country['category'] == 'pro_m_lectura']
        lec_f = df_country[df_country['category'] == 'pro_f_lectura']
        
        if not lec_m.empty and not lec_f.empty:
            m_count = lec_m.iloc[0]['word_count']
            f_count = lec_f.iloc[0]['word_count']
            
            if f_count > 0:
                gap_percent = ((m_count - f_count) / f_count) * 100
                dominant = 'M' if m_count > f_count else 'F'
            else:
                gap_percent = 100.0 if m_count > 0 else 0.0
                dominant = 'M' if m_count > 0 else 'F'
            
            results.append({
                'country': country,
                'category': 'PRO-LECTURA',
                'pro_m': m_count,
                'pro_f': f_count,
                'gap_percent': round(gap_percent, 1),
                'dominant': dominant
            })
        
        # Get PRO-LIBRE-M and PRO-LIBRE-F
        lib_m = df_country[df_country['category'] == 'pro_m_libre']
        lib_f = df_country[df_country['category'] == 'pro_f_libre']
        
        if not lib_m.empty and not lib_f.empty:
            m_count = lib_m.iloc[0]['word_count']
            f_count = lib_f.iloc[0]['word_count']
            
            if f_count > 0:
                gap_percent = ((m_count - f_count) / f_count) * 100
                dominant = 'M' if m_count > f_count else 'F'
            else:
                gap_percent = 100.0 if m_count > 0 else 0.0
                dominant = 'M' if m_count > 0 else 'F'
            
            results.append({
                'country': country,
                'category': 'PRO-LIBRE',
                'pro_m': m_count,
                'pro_f': f_count,
                'gap_percent': round(gap_percent, 1),
                'dominant': dominant
            })
    
    df_gap = pd.DataFrame(results)
    
    # Save to CSV
    csv_path = OUTPUT_DIR / "gender_gap_analysis.csv"
    df_gap.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"  [SAVE] Gender gap CSV saved: {csv_path}")
    
    # Create visualizations for each category
    categories = ['PRO (all modes)', 'PRO-LECTURA', 'PRO-LIBRE']
    
    for cat in categories:
        df_cat = df_gap[df_gap['category'] == cat].copy()
        
        if len(df_cat) == 0:
            continue
        
        # Sort by gap percent
        df_cat = df_cat.sort_values('gap_percent', ascending=True)
        
        # Create color map (red for M-dominant, blue for F-dominant)
        colors = ['#d62728' if d == 'M' else '#1f77b4' for d in df_cat['dominant']]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 10))
        
        countries_list = df_cat['country'].values
        gaps = df_cat['gap_percent'].values
        
        bars = ax.barh(range(len(countries_list)), gaps, color=colors, alpha=0.7)
        ax.set_yticks(range(len(countries_list)))
        ax.set_yticklabels(countries_list)
        ax.set_xlabel('Gender Gap (% Difference)', fontsize=12)
        ax.set_title(f'{cat} - Gender Gap Analysis\n(Positive = M > F, Negative = F > M)', 
                     fontsize=14, fontweight='bold')
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
        ax.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, v in enumerate(gaps):
            label = f"{v:+.1f}%"
            x_pos = v + (max(abs(gaps)) * 0.02 if v >= 0 else -max(abs(gaps)) * 0.02)
            ha = 'left' if v >= 0 else 'right'
            ax.text(x_pos, i, label, va='center', ha=ha, fontsize=8)
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#d62728', alpha=0.7, label='M > F'),
            Patch(facecolor='#1f77b4', alpha=0.7, label='F > M')
        ]
        ax.legend(handles=legend_elements, loc='best')
        
        plt.tight_layout()
        
        # Save figure
        safe_cat = cat.replace(' ', '_').replace('(', '').replace(')', '')
        fig_path = OUTPUT_DIR / f"viz_gender_gap_{safe_cat}.png"
        plt.savefig(fig_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  [OK] Saved: {fig_path.name}")
    
    return df_gap

# ==============================================================================
# SUMMARY REPORT
# ==============================================================================

def create_summary_report(df_results, df_across):
    """Create human-readable summary report (overwrite existing)."""
    report_path = OUTPUT_DIR / "summary_report.txt"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("CO.RA.PAN CORPUS STATISTICS SUMMARY (JSON-basiert)\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: media/transcripts/*/*.json\n")
        f.write("=" * 80 + "\n\n")
        
        # ACROSS-COUNTRY STATISTICS FIRST
        f.write("\n" + "=" * 80 + "\n")
        f.write("ACROSS ALL COUNTRIES - SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        
        total_across = df_across[df_across['category'] == 'TOTAL_ALL_COUNTRIES'].iloc[0]
        f.write(f"TOTAL ALL COUNTRIES: {total_across['word_count']:,} words | {total_across['duration_hms']}\n")
        f.write(f"{'-'*80}\n\n")
        
        # PRO vs. OTRO
        pro_across = df_across[df_across['category'] == 'pro']
        otro_across = df_across[df_across['category'] == 'otro']
        
        if not pro_across.empty:
            pro = pro_across.iloc[0]
            f.write(f"PRO (all countries):   {pro['word_count']:9,} words ({pro['percent']:5.1f}%) | {pro['duration_hms']}\n")
        
        if not otro_across.empty:
            otro = otro_across.iloc[0]
            f.write(f"OTRO (all countries):  {otro['word_count']:9,} words ({otro['percent']:5.1f}%) | {otro['duration_hms']}\n")
        
        f.write(f"\n{'-'*80}\n")
        f.write("PRO SPEAKERS - GENDER COMPARISON (all countries):\n")
        f.write(f"{'-'*80}\n\n")
        
        # PRO-M vs. PRO-F (across all countries) - relative percentages
        pro_m = df_across[df_across['category'] == 'pro_m']
        pro_f = df_across[df_across['category'] == 'pro_f']
        
        if not pro_m.empty and not pro_f.empty:
            pm = pro_m.iloc[0]
            pf = pro_f.iloc[0]
            pro_total = pm['word_count'] + pf['word_count']
            pm_pct = (pm['word_count'] / pro_total) * 100 if pro_total > 0 else 0
            pf_pct = (pf['word_count'] / pro_total) * 100 if pro_total > 0 else 0
            f.write(f"PRO-M (all modes):     {pm['word_count']:9,} words ({pm_pct:5.1f}%) | {pm['duration_hms']}\n")
            f.write(f"PRO-F (all modes):     {pf['word_count']:9,} words ({pf_pct:5.1f}%) | {pf['duration_hms']}\n")
        
        f.write(f"\n{'-'*80}\n")
        f.write("PRO SPEAKERS - MODE & GENDER BREAKDOWN (all countries):\n")
        f.write(f"{'-'*80}\n\n")
        
        # LECTURA: M vs. F - relative percentages
        lec_m = df_across[df_across['category'] == 'pro_lectura_m']
        lec_f = df_across[df_across['category'] == 'pro_lectura_f']
        
        if not lec_m.empty and not lec_f.empty:
            lm = lec_m.iloc[0]
            lf = lec_f.iloc[0]
            lec_total = lm['word_count'] + lf['word_count']
            lm_pct = (lm['word_count'] / lec_total) * 100 if lec_total > 0 else 0
            lf_pct = (lf['word_count'] / lec_total) * 100 if lec_total > 0 else 0
            f.write(f"PRO-LECTURA-M:         {lm['word_count']:9,} words ({lm_pct:5.1f}%) | {lm['duration_hms']}\n")
            f.write(f"PRO-LECTURA-F:         {lf['word_count']:9,} words ({lf_pct:5.1f}%) | {lf['duration_hms']}\n")
        
        f.write("\n")
        
        # LIBRE: M vs. F - relative percentages
        lib_m = df_across[df_across['category'] == 'pro_libre_m']
        lib_f = df_across[df_across['category'] == 'pro_libre_f']
        
        if not lib_m.empty and not lib_f.empty:
            lm = lib_m.iloc[0]
            lf = lib_f.iloc[0]
            lib_total = lm['word_count'] + lf['word_count']
            lm_pct = (lm['word_count'] / lib_total) * 100 if lib_total > 0 else 0
            lf_pct = (lf['word_count'] / lib_total) * 100 if lib_total > 0 else 0
            f.write(f"PRO-LIBRE-M:           {lm['word_count']:9,} words ({lm_pct:5.1f}%) | {lm['duration_hms']}\n")
            f.write(f"PRO-LIBRE-F:           {lf['word_count']:9,} words ({lf_pct:5.1f}%) | {lf['duration_hms']}\n")
        
        f.write("\n")
        
        # PRE: M vs. F - relative percentages
        pre_m = df_across[df_across['category'] == 'pro_pre_m']
        pre_f = df_across[df_across['category'] == 'pro_pre_f']
        
        if not pre_m.empty and not pre_f.empty:
            pm = pre_m.iloc[0]
            pf = pre_f.iloc[0]
            pre_total = pm['word_count'] + pf['word_count']
            pm_pct = (pm['word_count'] / pre_total) * 100 if pre_total > 0 else 0
            pf_pct = (pf['word_count'] / pre_total) * 100 if pre_total > 0 else 0
            f.write(f"PRO-PRE-M:             {pm['word_count']:9,} words ({pm_pct:5.1f}%) | {pm['duration_hms']}\n")
            f.write(f"PRO-PRE-F:             {pf['word_count']:9,} words ({pf_pct:5.1f}%) | {pf['duration_hms']}\n")
        
        f.write("\n")
        
        # N/A: M vs. F (tiempo/tránsito discourse types) - relative percentages
        na_m = df_across[df_across['category'] == 'pro_na_m']
        na_f = df_across[df_across['category'] == 'pro_na_f']
        
        if not na_m.empty and not na_f.empty:
            nm = na_m.iloc[0]
            nf = na_f.iloc[0]
            na_total = nm['word_count'] + nf['word_count']
            nm_pct = (nm['word_count'] / na_total) * 100 if na_total > 0 else 0
            nf_pct = (nf['word_count'] / na_total) * 100 if na_total > 0 else 0
            f.write(f"PRO-N/A-M:             {nm['word_count']:9,} words ({nm_pct:5.1f}%) | {nm['duration_hms']}\n")
            f.write(f"PRO-N/A-F:             {nf['word_count']:9,} words ({nf_pct:5.1f}%) | {nf['duration_hms']}\n")
        
        # PER-COUNTRY STATISTICS
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("PER-COUNTRY STATISTICS\n")
        f.write("=" * 80 + "\n")
        
        countries = sorted(df_results['country_code'].unique())
        
        for country in countries:
            df_country = df_results[df_results['country_code'] == country]
            
            # Get total
            total_row = df_country[df_country['category'] == 'TOTAL']
            if total_row.empty:
                continue
            total = total_row.iloc[0]
            
            f.write(f"\n{'='*80}\n")
            f.write(f"{country}\n")
            f.write(f"{'='*80}\n")
            f.write(f"TOTAL: {total['word_count']:,} words | {total['duration_hms']}\n")
            f.write(f"{'-'*80}\n\n")
            
            # Get pro vs otro
            pro_data = df_country[df_country['category'] == 'pro']
            otro_data = df_country[df_country['category'] == 'otro']
            
            if not pro_data.empty:
                pro = pro_data.iloc[0]
                f.write(f"PRO:   {pro['word_count']:7,} words ({pro['percent']:5.1f}%) | {pro['duration_hms']}\n")
            
            if not otro_data.empty:
                otro = otro_data.iloc[0]
                f.write(f"OTRO:  {otro['word_count']:7,} words ({otro['percent']:5.1f}%) | {otro['duration_hms']}\n")
            
            # PRO-M vs. PRO-F comparison - relative percentages
            f.write(f"\n{'-'*80}\n")
            f.write("PRO GENDER COMPARISON:\n")
            f.write(f"{'-'*80}\n\n")
            
            pro_m_data = df_country[df_country['category'] == 'pro_m']
            pro_f_data = df_country[df_country['category'] == 'pro_f']
            
            if not pro_m_data.empty and not pro_f_data.empty:
                pm = pro_m_data.iloc[0]
                pf = pro_f_data.iloc[0]
                pro_gender_total = pm['word_count'] + pf['word_count']
                pm_pct = (pm['word_count'] / pro_gender_total) * 100 if pro_gender_total > 0 else 0
                pf_pct = (pf['word_count'] / pro_gender_total) * 100 if pro_gender_total > 0 else 0
                f.write(f"PRO-M (all modes): {pm['word_count']:7,} words ({pm_pct:5.1f}%) | {pm['duration_hms']}\n")
                f.write(f"PRO-F (all modes): {pf['word_count']:7,} words ({pf_pct:5.1f}%) | {pf['duration_hms']}\n")
            
            f.write(f"\n{'-'*80}\n")
            f.write("PRO SPEAKER BREAKDOWN (by Mode & Sex):\n")
            f.write(f"{'-'*80}\n\n")
            
            # Get pro detailed combinations (sex + mode)
            pro_detailed = df_country[
                (df_country['speaker_type'] == 'pro') &
                (df_country['sex'] != '') &
                (df_country['mode'] != '') &
                (df_country['discourse'] == '')
            ].sort_values('word_count', ascending=False)
            
            if not pro_detailed.empty:
                # Calculate total PRO word count for relative percentages
                pro_total_wc = pro_detailed['word_count'].sum()
                
                for _, row in pro_detailed.iterrows():
                    # Calculate percentage relative to PRO total instead of country total
                    pct = (row['word_count'] / pro_total_wc * 100) if pro_total_wc > 0 else 0
                    f.write(f"  {row['category']:20} {row['word_count']:7,} words ({pct:5.1f}%) | {row['duration_hms']}\n")
            else:
                f.write("  No pro detailed data available\n")
            
            f.write("\n")
    
    print(f"\n[SAVE] Summary report saved: {report_path}")

# ==============================================================================
# CLI ARGUMENT PARSING
# ==============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate internal corpus statistics from JSON transcripts (Pipeline Step 04)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python 04_internal_country_statistics.py                    # Process all countries
  python 04_internal_country_statistics.py --country USA      # Process only USA
  python 04_internal_country_statistics.py --country ARG,ESP  # Process multiple countries
  python 04_internal_country_statistics.py --limit 10         # Limit to 10 files (for testing)
        """
    )
    
    parser.add_argument(
        '--country', '-c',
        type=str,
        default=None,
        help='Comma-separated list of country codes to process (e.g., "ARG,ESP,USA"). Default: all countries.'
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=None,
        help='Limit number of JSON files to process (for testing). Default: no limit.'
    )
    
    return parser.parse_args()

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    # Ensure pandas is available before doing heavy data processing
    if not HAS_PANDAS:
        print("[ERROR] 'pandas' is required to run this script.\nPlease install the LOKAL requirements: pip install -r ../requirements-lokal.txt")
        return 1
    """Main execution function."""
    # Parse CLI arguments
    args = parse_args()
    
    # Parse countries
    countries = None
    if args.country:
        countries = [c.strip() for c in args.country.split(',')]
    
    print("=" * 80)
    print("CO.RA.PAN Internal Country Statistics (JSON-basiert)")
    print("=" * 80)
    print(f"Transcripts: {TRANSCRIPTS_DIR}")
    print(f"Output Dir:  {OUTPUT_DIR}")
    if countries:
        print(f"Countries:   {', '.join(countries)}")
    else:
        print(f"Countries:   ALL")
    if args.limit:
        print(f"Limit:       {args.limit} files")
    print("=" * 80)
    
    try:
        # 1. Load data from JSON
        df = load_data_from_json(countries=countries, limit_files=args.limit)
        if df is None or df.empty:
            print("[ERROR] No valid tokens found. Exiting.")
            return
        
        # 2. Generate per-country statistics
        df_results = generate_statistics(df)
        
        # 3. Generate across-country statistics
        df_across = generate_across_country_statistics(df)
        
        # 4. Export to CSV (overwrite existing)
        export_to_csv(df_results, df_across)
        
        # 5. Create visualizations (overwrite existing)
        create_visualizations(df_results)
        
        # 6. Create across-country visualizations
        create_across_country_visualizations(df_across)
        
        # 7. Create gender gap analysis
        df_gap = create_gender_gap_analysis(df_results)
        
        # 8. Create summary report (overwrite existing)
        create_summary_report(df_results, df_across)
        
        # Final summary
        print("\n" + "=" * 80)
        print("[OK] STATISTICS GENERATION COMPLETED (JSON-basiert)")
        print("=" * 80)
        print(f"Output directory: {OUTPUT_DIR}")
        print(f"  - CSV (per-country): corpus_statistics.csv")
        print(f"  - CSV (across-country): corpus_statistics_across_countries.csv")
        print(f"  - CSV (gender gap): gender_gap_analysis.csv")
        print(f"  - Visualizations: viz_*_pro_modes.png")
        print(f"  - Across-country viz: viz_ALL_COUNTRIES_pro_modes.png")
        print(f"  - Gender gap viz: viz_gender_gap_*.png")
        print(f"  - Summary: summary_report.txt")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n[WARN] Process interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
