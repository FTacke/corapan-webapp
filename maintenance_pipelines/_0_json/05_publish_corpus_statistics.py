#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_publish_corpus_statistics.py

Pipeline-Schritt 05: Generates PUBLIC, Spanish-language corpus statistics visualizations for the website.
Uses pre-generated CSV files from 04_internal_country_statistics.py as input.

EINGABEPFAD:  LOKAL/_0_json/results/corpus_statistics.csv
              LOKAL/_0_json/results/corpus_statistics_across_countries.csv

AUSGABEVERZEICHNIS:
    - Default: RUNTIME (PUBLIC_STATS_DIR or CORAPAN_RUNTIME_ROOT/data/public/statistics)
    - Can be overridden with --out CLI argument for custom paths

Visualizations:
1. Composición del corpus (3 images):
   - viz_total_corpus.png: PRO vs OTRO pie chart
   - viz_genero_profesionales.png: M vs F bar chart
   - viz_modo_genero_profesionales.png: Mode × Gender stacked bar

2. Distribución por país (1 combined image per country):
   - viz_<COUNTRY>_resumen.png: Combined visualization with PRO/OTRO, Gender, Mode×Sex

Also generates: corpus_stats.json with all data for dynamic frontend use.

VERWENDUNG:
    python 05_publish_corpus_statistics.py                    # Default: Runtime statistics directory
    python 05_publish_corpus_statistics.py --out /custom/path # Override output directory

ENVIRONMENT VARIABLES:
    PUBLIC_STATS_DIR (preferred)
    CORAPAN_RUNTIME_ROOT (fallback to runtime/data/public/statistics)

PIPELINE-REIHENFOLGE:
    01_preprocess_transcripts.py  → json-ready/
    02_annotate_transcripts_v3.py → media/transcripts/<country>/
    03_build_metadata_stats.py    → data/db/*.db
    04_internal_country_statistics.py → results/*.csv
    05_publish_corpus_statistics.py → statistics output directory (this script)

Copyright (c) 2025 CO.RA.PAN Project
"""

import json
import sys
import argparse
try:
    import pandas as pd
    HAS_PANDAS = True
except Exception:
    pd = None
    HAS_PANDAS = False
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Set matplotlib backend to non-interactive
plt.switch_backend('Agg')

# Configure matplotlib for modern, elegant styling
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Noto Sans', 'DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 16

# Modern styling parameters
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.labelcolor'] = '#333333'
plt.rcParams['xtick.color'] = '#666666'
plt.rcParams['ytick.color'] = '#666666'
plt.rcParams['text.color'] = '#333333'
plt.rcParams['axes.facecolor'] = '#FAFAFA'
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['grid.color'] = '#E0E0E0'
plt.rcParams['grid.linewidth'] = 0.5
plt.rcParams['grid.alpha'] = 0.6

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent

INPUT_DIR = SCRIPT_DIR / "results"

# Determine output directory - DEFAULT to repo data/public/statistics
def _find_repo_root():
    """
    Find the CO.RA.PAN repository root using git command (most reliable).
    
    Fallback to filesystem markers if git is not available.
    
    Returns:
        Path: Repository root directory
        
    Raises:
        RuntimeError: If repo root not found or invalid
    """
    import subprocess
    
    # First try: use git rev-parse (most reliable)
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(SCRIPT_DIR)
        )
        if result.returncode == 0:
            repo_root = Path(result.stdout.strip())
            # Validate repo name
            if repo_root.name.endswith("corapan-webapp"):
                return repo_root
    except FileNotFoundError:
        pass  # git not available, fall through to filesystem search
    
    # Fallback: search filesystem for markers (prioritize pyproject.toml, then .git)
    current = SCRIPT_DIR
    
    for _ in range(10):  # max 10 levels up to avoid infinite loop
        # Check for pyproject.toml (most specific repo root marker)
        if (current / "pyproject.toml").exists():
            # Validate repo name
            if current.name.endswith("corapan-webapp"):
                return current
        
        # Check for .git (but only at appropriate depth)
        if (current / ".git").exists() and (current / ".git").is_dir():
            # Extra validation: .git should be at repo root, not in LOKAL subdir
            # Check if pyproject.toml exists at this level or package.json
            if (current / "pyproject.toml").exists() or (current / "package.json").exists():
                if current.name.endswith("corapan-webapp"):
                    return current
        
        # Check for combination of src/ and templates/ (indicates repo root)
        if (current / "src").is_dir() and (current / "templates").is_dir():
            if (current / "pyproject.toml").exists():  # confirm it's repo root
                if current.name.endswith("corapan-webapp"):
                    return current
        
        parent = current.parent
        if parent == current:  # reached root filesystem
            raise RuntimeError(
                f"[ERROR] Could not find repository root starting from {SCRIPT_DIR}\n"
                "        Expected to find pyproject.toml in parent directory.\n"
                "        This script must be run from within the corapan-webapp repository."
            )
        current = parent
    
    # Should not reach here
    raise RuntimeError(
        f"[ERROR] Repository root validation failed\n"
        f"        Starting directory: {SCRIPT_DIR}\n"
        f"        This script must run from the CO.RA.PAN webapp repository."
    )


def _get_output_dir():
    """
    Determine output directory for statistics.
    
    Priority:
    1. CLI --out argument (if provided) → use exactly that path
    2. PUBLIC_STATS_DIR env var (if provided)
    3. CORAPAN_RUNTIME_ROOT env var → ${CORAPAN_RUNTIME_ROOT}/data/public/statistics
    4. Fail fast if none are set
    
    Returns:
        Path: Output directory for statistics
        
    Raises:
        RuntimeError: If repository root cannot be determined
    """
    import os
    
    # Check for --out argument in command line
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--out', type=str, default=None, help='Custom output directory')
    args, _ = parser.parse_known_args()
    
    if args.out:
        out_path = Path(args.out)
        return out_path
    
    public_stats_dir = os.getenv("PUBLIC_STATS_DIR")
    runtime_root = os.getenv("CORAPAN_RUNTIME_ROOT")

    if public_stats_dir:
        return Path(public_stats_dir)

    if runtime_root:
        return Path(runtime_root) / "data" / "public" / "statistics"

    raise RuntimeError(
        "[ERROR] No output directory configured.\n"
        "Set PUBLIC_STATS_DIR or CORAPAN_RUNTIME_ROOT, or pass --out <dir>.\n"
        "Example:\n"
        "  $env:CORAPAN_RUNTIME_ROOT=\"C:\\path\\to\\runtime\\corapan\"\n"
        "  python 05_publish_corpus_statistics.py\n"
    )

OUTPUT_DIR = _get_output_dir()


def _ensure_stats_permissions(path: Path) -> None:
    """Best-effort chmod to keep statistics assets world-readable."""
    try:
        if path.is_dir():
            path.chmod(0o755)
            for child in path.iterdir():
                if child.is_file():
                    child.chmod(0o644)
        elif path.is_file():
            path.chmod(0o644)
            if path.parent.exists():
                path.parent.chmod(0o755)
    except Exception:
        # Ignore permission errors (e.g., Windows or non-owner files)
        return

# Input CSV files
CSV_PER_COUNTRY = INPUT_DIR / "corpus_statistics.csv"
CSV_ACROSS_COUNTRIES = INPUT_DIR / "corpus_statistics_across_countries.csv"

# Spanish Labels
LABELS_ES = {
    # Speaker types
    'pro': 'Profesional',
    'otro': 'No profesional',
    
    # Gender
    'm': 'Masculino',
    'f': 'Femenino',
    
    # Modes
    'lectura': 'Leído',
    'libre': 'Libre',
    'pre': 'Pregrabado',
    'n/a': 'Tiempo/Tránsito',
    
    # Combined labels
    'pro_m': 'Profesional - Masculino',
    'pro_f': 'Profesional - Femenino',
    'otro_m': 'No profesional - Masculino',
    'otro_f': 'No profesional - Femenino',
}

# Color scheme - Modern, accessible colors
COLORS = {
    'pro': '#2E7D32',      # Deep Green (professional)
    'otro': '#1565C0',     # Deep Blue (non-professional)
    'm': '#1976D2',        # Blue (masculine)
    'f': '#C62828',        # Red (feminine)
    'lectura': '#388E3C',  # Green
    'libre': '#7B1FA2',    # Purple
    'pre': '#E64A19',      # Deep Orange
    'na': '#455A64',       # Blue Grey
}

# Visualization Constants (for consistency across all plots)
VIZ_CONFIG = {
    'dpi': 150,
    'title_fontsize': 15,
    'subtitle_fontsize': 13,
    'label_fontsize': 12,
    'tick_fontsize': 10,
    'legend_fontsize': 10,
    'value_fontsize': 11,
    'percentage_fontsize': 12,
    'title_pad': 18,
    'label_pad': 10,
}

# ==============================================================================
# DATA LOADING
# ==============================================================================

def load_data_from_csv():
    """Load corpus data from pre-generated CSV files."""
    print("\n[*] Cargando datos desde archivos CSV...")
    
    # Check if CSV files exist
    if not CSV_PER_COUNTRY.exists():
        print(f"[ERROR] Archivo no encontrado: {CSV_PER_COUNTRY}")
        print("Por favor, ejecuta primero: 04_internal_country_statistics.py")
        exit(1)
    
    if not CSV_ACROSS_COUNTRIES.exists():
        print(f"[ERROR] Archivo no encontrado: {CSV_ACROSS_COUNTRIES}")
        print("Por favor, ejecuta primero: 04_internal_country_statistics.py")
        exit(1)
    
    # Load CSV files
    df_per_country = pd.read_csv(CSV_PER_COUNTRY, encoding='utf-8-sig')
    df_across = pd.read_csv(CSV_ACROSS_COUNTRIES, encoding='utf-8-sig')
    
    print(f"[OK] {len(df_per_country)} registros por país cargados")
    print(f"[OK] {len(df_across)} registros across-countries cargados")
    
    return df_per_country, df_across

# ==============================================================================
# STATISTICS AGGREGATION
# ==============================================================================

def parse_duration_hms(hms_str):
    """Parse HH:MM:SS string to seconds."""
    if not hms_str or pd.isna(hms_str):
        return 0
    try:
        parts = hms_str.split(':')
        if len(parts) == 3:
            h, m, s = map(int, parts)
            return h * 3600 + m * 60 + s
        return 0
    except:
        return 0

def seconds_to_hms(seconds):
    """Convert seconds to HH:MM:SS format."""
    if seconds is None or seconds == 0:
        return "00:00:00"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def aggregate_statistics(df_per_country, df_across):
    """Aggregate statistics from CSV data."""
    print("\n[*] Agregando estadísticas...")
    
    # Helper function to get row by category
    def get_row(df, category):
        rows = df[df['category'] == category]
        if len(rows) > 0:
            row = rows.iloc[0]
            return {
                'word_count': int(row['word_count']),
                'duration': parse_duration_hms(row['duration_hms'])
            }
        return {'word_count': 0, 'duration': 0}
    
    # Initialize structure
    stats = {
        'all_countries': {
            'total': get_row(df_across, 'TOTAL_ALL_COUNTRIES'),
            'pro': get_row(df_across, 'pro'),
            'otro': get_row(df_across, 'otro'),
            'pro_gender': {
                'm': get_row(df_across, 'pro_m'),
                'f': get_row(df_across, 'pro_f')
            },
            'pro_mode_gender': {
                'lectura_m': get_row(df_across, 'pro_lectura_m'),
                'lectura_f': get_row(df_across, 'pro_lectura_f'),
                'libre_m': get_row(df_across, 'pro_libre_m'),
                'libre_f': get_row(df_across, 'pro_libre_f'),
                'pre_m': get_row(df_across, 'pro_pre_m'),
                'pre_f': get_row(df_across, 'pro_pre_f'),
                'na_m': get_row(df_across, 'pro_na_m'),
                'na_f': get_row(df_across, 'pro_na_f'),
            },
        },
        'countries': {}
    }
    
    # Process per-country data
    countries = df_per_country['country_code'].unique()
    
    for country in countries:
        df_country = df_per_country[df_per_country['country_code'] == country]
        
        stats['countries'][country] = {
            'total': get_row(df_country, 'TOTAL'),
            'pro': get_row(df_country, 'pro'),
            'otro': get_row(df_country, 'otro'),
            'pro_gender': {
                'm': get_row(df_country, 'pro_m'),
                'f': get_row(df_country, 'pro_f')
            },
            'pro_mode_gender': {}
        }
        
        # Get all pro_*_* categories for mode×gender breakdown
        # Filter out NaN values first
        valid_cats = df_country['category'].dropna()
        pro_detail_rows = df_country[df_country['category'].isin(
            valid_cats[valid_cats.str.startswith('pro_')]
        )]
        for _, row in pro_detail_rows.iterrows():
            cat = row['category']
            # Parse "pro_m_libre" -> "libre_m"
            parts = cat.split('_', 2)  # Split into ['pro', 'm', 'libre']
            if len(parts) == 3:
                sex = parts[1]  # m or f
                mode = parts[2].replace('/', '')  # libre, lectura, pre, na (remove slash from n/a)
                key = f"{mode}_{sex}"
                stats['countries'][country]['pro_mode_gender'][key] = {
                    'word_count': int(row['word_count']),
                    'duration': parse_duration_hms(row['duration_hms'])
                }
    
    print(f"[OK] Estadísticas agregadas para {len(stats['countries'])} países")
    
    return stats

# ==============================================================================
# VISUALIZATION 1: TOTAL CORPUS (PRO vs OTRO)
# ==============================================================================

def create_viz_total_corpus(stats):
    """Create modern donut chart: PRO vs OTRO."""
    print("\n[*] Creando visualización: Total del corpus...")
    
    pro_count = stats['all_countries']['pro']['word_count']
    otro_count = stats['all_countries']['otro']['word_count']
    total = pro_count + otro_count
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    sizes = [pro_count, otro_count]
    labels = [LABELS_ES['pro'], LABELS_ES['otro']]
    colors = [COLORS['pro'], COLORS['otro']]
    explode = (0.03, 0)
    
    # Create donut chart (modern style)
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,  # We'll add custom labels
        colors=colors,
        explode=explode,
        autopct='',  # We'll add custom percentages
        startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2, 'antialiased': True},
        pctdistance=0.75
    )
    
    # Add custom percentage labels
    for i, (wedge, autotext) in enumerate(zip(wedges, autotexts)):
        ang = (wedge.theta2 - wedge.theta1) / 2. + wedge.theta1
        x = np.cos(np.deg2rad(ang)) * 0.75
        y = np.sin(np.deg2rad(ang)) * 0.75
        pct = sizes[i] / total * 100
        ax.text(x, y, f'{pct:.1f}%', ha='center', va='center', 
                fontsize=VIZ_CONFIG['percentage_fontsize'], fontweight='bold', color='white')
    
    # Create center circle for donut effect
    centre_circle = plt.Circle((0, 0), 0.50, fc='white', linewidth=0)
    ax.add_artist(centre_circle)
    
    ax.set_title('Composición del Corpus\nTipo de Hablante', 
                 fontsize=VIZ_CONFIG['title_fontsize'], fontweight='600', 
                 pad=VIZ_CONFIG['title_pad'], color='#333333')
    
    # Modern legend with word counts
    legend_labels = [
        f"{LABELS_ES['pro']}: {pro_count:,} palabras",
        f"{LABELS_ES['otro']}: {otro_count:,} palabras"
    ]
    ax.legend(wedges, legend_labels, loc='lower center', bbox_to_anchor=(0.5, -0.05), 
              ncol=2, frameon=False, fontsize=VIZ_CONFIG['legend_fontsize'])
    
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / "viz_total_corpus.png"
    plt.savefig(output_path, dpi=VIZ_CONFIG['dpi'], bbox_inches='tight', facecolor='white')
    _ensure_stats_permissions(output_path)
    plt.close()
    
    print(f"[OK] Guardado: {output_path.name}")


# ==============================================================================
# VISUALIZATION 2: PRO GENDER COMPARISON
# ==============================================================================

def create_viz_genero_profesionales(stats):
    """Create modern bar chart: M vs F for PRO speakers."""
    print("\n[*] Creando visualización: Género (profesionales)...")
    
    m_count = stats['all_countries']['pro_gender']['m']['word_count']
    f_count = stats['all_countries']['pro_gender']['f']['word_count']
    total = m_count + f_count
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    categories = [LABELS_ES['m'], LABELS_ES['f']]
    counts = [m_count, f_count]
    colors_list = [COLORS['m'], COLORS['f']]
    
    bars = ax.bar(categories, counts, color=colors_list, alpha=0.85, 
                   edgecolor='white', linewidth=2, width=0.6)
    
    # Add value labels above bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        pct = (count / total) * 100
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count):,}\n({pct:.1f}%)',
                ha='center', va='bottom', fontsize=VIZ_CONFIG['value_fontsize'], 
                fontweight='600', color='#333333')
    
    ax.set_ylabel('Número de Palabras', fontsize=VIZ_CONFIG['label_fontsize'], 
                  fontweight='600', labelpad=VIZ_CONFIG['label_pad'], color='#333333')
    ax.set_title('Hablantes Profesionales\nDistribución por Sexo', 
                 fontsize=VIZ_CONFIG['title_fontsize'], fontweight='600', 
                 pad=VIZ_CONFIG['title_pad'], color='#333333')
    ax.tick_params(axis='both', labelsize=VIZ_CONFIG['tick_fontsize'])
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Remove top and right spines for cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / "viz_genero_profesionales.png"
    plt.savefig(output_path, dpi=VIZ_CONFIG['dpi'], bbox_inches='tight', facecolor='white')
    _ensure_stats_permissions(output_path)
    plt.close()
    
    print(f"[OK] Guardado: {output_path.name}")

# ==============================================================================
# VISUALIZATION 3: PRO MODE × GENDER BREAKDOWN
# ==============================================================================

def create_viz_modo_genero_profesionales(stats):
    """Create modern grouped bar chart: Mode × Gender for PRO speakers."""
    print("\n[*] Creando visualización: Modo × Género (profesionales)...")
    
    mode_gender = stats['all_countries']['pro_mode_gender']
    
    # Prepare data
    modes = ['lectura', 'libre', 'pre', 'n/a']
    m_counts = []
    f_counts = []
    
    for mode in modes:
        m_key = f"{mode}_m"
        f_key = f"{mode}_f"
        m_counts.append(mode_gender.get(m_key, {}).get('word_count', 0))
        f_counts.append(mode_gender.get(f_key, {}).get('word_count', 0))
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 7))
    
    x = np.arange(len(modes))
    width = 0.38
    
    bars1 = ax.bar(x - width/2, m_counts, width, label=LABELS_ES['m'], 
                   color=COLORS['m'], alpha=0.85, edgecolor='white', linewidth=2)
    bars2 = ax.bar(x + width/2, f_counts, width, label=LABELS_ES['f'], 
                   color=COLORS['f'], alpha=0.85, edgecolor='white', linewidth=2)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height):,}',
                        ha='center', va='bottom', fontsize=VIZ_CONFIG['value_fontsize']-1,
                        fontweight='600', color='#333333')
    
    ax.set_xlabel('Modo de Producción', fontsize=VIZ_CONFIG['label_fontsize'], 
                  fontweight='600', labelpad=VIZ_CONFIG['label_pad'], color='#333333')
    ax.set_ylabel('Número de Palabras', fontsize=VIZ_CONFIG['label_fontsize'], 
                  fontweight='600', labelpad=VIZ_CONFIG['label_pad'], color='#333333')
    ax.set_title('Hablantes Profesionales\nDistribución por Modo de Producción y Sexo', 
                 fontsize=VIZ_CONFIG['title_fontsize'], fontweight='600', 
                 pad=VIZ_CONFIG['title_pad'], color='#333333')
    ax.set_xticks(x)
    ax.set_xticklabels([LABELS_ES[m] for m in modes], fontsize=VIZ_CONFIG['tick_fontsize'])
    ax.tick_params(axis='y', labelsize=VIZ_CONFIG['tick_fontsize'])
    ax.legend(fontsize=VIZ_CONFIG['legend_fontsize'], loc='upper right', frameon=False)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / "viz_modo_genero_profesionales.png"
    plt.savefig(output_path, dpi=VIZ_CONFIG['dpi'], bbox_inches='tight', facecolor='white')
    _ensure_stats_permissions(output_path)
    plt.close()
    
    print(f"[OK] Guardado: {output_path.name}")

# ==============================================================================
# VISUALIZATION 4: PER-COUNTRY COMBINED
# ==============================================================================

def create_viz_country_resumen(country, country_stats):
    """Create combined visualization for one country."""
    
    total = country_stats['total']['word_count']
    pro = country_stats['pro']['word_count']
    otro = country_stats['otro']['word_count']
    
    # Skip if no data
    if total == 0:
        return
    
    # PRO gender
    pro_m = country_stats['pro_gender']['m']['word_count']
    pro_f = country_stats['pro_gender']['f']['word_count']
    pro_total = pro_m + pro_f
    
    pro_m_pct = (pro_m / pro_total * 100) if pro_total > 0 else 0
    pro_f_pct = (pro_f / pro_total * 100) if pro_total > 0 else 0
    
    # Create figure with 2 rows: row 1 = 2 donut charts, row 2 = 1 bar chart
    fig = plt.figure(figsize=(14, 11), facecolor='white')
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.2], hspace=0.38, wspace=0.35)
    
    # Subplot 1: PRO vs OTRO (donut chart, top left)
    ax1 = fig.add_subplot(gs[0, 0])
    if otro > 0:
        sizes = [pro, otro]
        colors_list = [COLORS['pro'], COLORS['otro']]
        explode = (0.03, 0)
    else:
        sizes = [pro]
        colors_list = [COLORS['pro']]
        explode = None
    
    wedges1, _, _ = ax1.pie(sizes, colors=colors_list, explode=explode,
                             autopct='%1.1f%%', startangle=90, 
                             wedgeprops={'edgecolor': 'white', 'linewidth': 2},
                             textprops={'fontsize': VIZ_CONFIG['percentage_fontsize'], 
                                       'weight': 'bold', 'color': 'white'})
    
    # Create center circle for donut
    centre_circle1 = plt.Circle((0, 0), 0.50, fc='white', linewidth=0)
    ax1.add_artist(centre_circle1)
    
    ax1.set_title('Tipo de Hablante', fontsize=VIZ_CONFIG['subtitle_fontsize'], 
                  fontweight='600', pad=12, color='#333333')
    
    # Add legend for Tipo de Hablante
    if otro > 0:
        legend_labels1 = [
            f"{LABELS_ES['pro']}: {pro:,}",
            f"{LABELS_ES['otro']}: {otro:,}"
        ]
        ax1.legend(wedges1, legend_labels1, loc='lower center', bbox_to_anchor=(0.5, -0.15),
                   ncol=2, frameon=False, fontsize=VIZ_CONFIG['legend_fontsize'])
    else:
        legend_labels1 = [f"{LABELS_ES['pro']}: {pro:,}"]
        ax1.legend(wedges1, legend_labels1, loc='lower center', bbox_to_anchor=(0.5, -0.15),
                   frameon=False, fontsize=VIZ_CONFIG['legend_fontsize'])
    
    # Subplot 2: PRO Gender (donut chart, top right)
    ax2 = fig.add_subplot(gs[0, 1])
    
    sizes2 = [pro_m, pro_f]
    colors_list2 = [COLORS['m'], COLORS['f']]
    explode2 = (0.03, 0)
    
    wedges2, _, _ = ax2.pie(sizes2, colors=colors_list2, explode=explode2,
                             autopct='%1.1f%%', startangle=90, 
                             wedgeprops={'edgecolor': 'white', 'linewidth': 2},
                             textprops={'fontsize': VIZ_CONFIG['percentage_fontsize'], 
                                       'weight': 'bold', 'color': 'white'})
    
    # Create center circle for donut
    centre_circle2 = plt.Circle((0, 0), 0.50, fc='white', linewidth=0)
    ax2.add_artist(centre_circle2)
    
    ax2.set_title('Comparación de Sexo\n(Hablantes Profesionales)', 
                 fontsize=VIZ_CONFIG['subtitle_fontsize'], fontweight='600', 
                 pad=12, color='#333333')
    
    # Add legend for Gender comparison
    legend_labels2 = [
        f"{LABELS_ES['m']}: {pro_m:,} ({pro_m_pct:.1f}%)",
        f"{LABELS_ES['f']}: {pro_f:,} ({pro_f_pct:.1f}%)"
    ]
    ax2.legend(wedges2, legend_labels2, loc='lower center', bbox_to_anchor=(0.5, -0.15),
               ncol=2, frameon=False, fontsize=VIZ_CONFIG['legend_fontsize'])
    
    # Subplot 3: PRO Mode × Gender (modern grouped bars, bottom)
    ax3 = fig.add_subplot(gs[1, :])
    
    mode_gender = country_stats['pro_mode_gender']
    modes = ['lectura', 'libre', 'pre', 'n/a']
    
    # Prepare data for grouped bars
    mode_labels = []
    m_values = []
    f_values = []
    
    for mode in modes:
        m_key = f"{mode}_m"
        f_key = f"{mode}_f"
        m_val = mode_gender.get(m_key, {}).get('word_count', 0)
        f_val = mode_gender.get(f_key, {}).get('word_count', 0)
        
        if m_val > 0 or f_val > 0:
            mode_labels.append(LABELS_ES[mode])
            m_values.append(m_val)
            f_values.append(f_val)
    
    if mode_labels:
        x = np.arange(len(mode_labels))
        width = 0.38
        
        bars_m = ax3.bar(x - width/2, m_values, width, 
                         label=LABELS_ES['m'], color=COLORS['m'], alpha=0.85, 
                         edgecolor='white', linewidth=2)
        bars_f = ax3.bar(x + width/2, f_values, width, 
                         label=LABELS_ES['f'], color=COLORS['f'], alpha=0.85, 
                         edgecolor='white', linewidth=2)
        
        # Add value labels on bars
        for bars, values in [(bars_m, m_values), (bars_f, f_values)]:
            for bar, val in zip(bars, values):
                if val > 0:
                    height = bar.get_height()
                    ax3.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(val):,}',
                            ha='center', va='bottom', fontsize=VIZ_CONFIG['value_fontsize']-1, 
                            fontweight='600', color='#333333')
        
        ax3.set_xlabel('Modo de Producción', fontsize=VIZ_CONFIG['label_fontsize'], 
                      fontweight='600', labelpad=VIZ_CONFIG['label_pad'], color='#333333')
        ax3.set_ylabel('Número de Palabras', fontsize=VIZ_CONFIG['label_fontsize'], 
                      fontweight='600', labelpad=VIZ_CONFIG['label_pad'], color='#333333')
        ax3.set_title('Desglose de Hablantes Profesionales por Modo × Sexo', 
                     fontsize=VIZ_CONFIG['subtitle_fontsize'], fontweight='600', 
                     pad=12, color='#333333')
        ax3.set_xticks(x)
        ax3.set_xticklabels(mode_labels, fontsize=VIZ_CONFIG['tick_fontsize'])
        ax3.tick_params(axis='y', labelsize=VIZ_CONFIG['tick_fontsize'])
        ax3.legend(fontsize=VIZ_CONFIG['legend_fontsize'], loc='upper right', frameon=False)
        ax3.grid(axis='y', alpha=0.3, linestyle='--')
        ax3.set_axisbelow(True)
        
        # Remove top and right spines
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
    
    plt.suptitle(f'Resumen Estadístico: {country}', 
                 fontsize=VIZ_CONFIG['title_fontsize'], fontweight='700', 
                 y=0.98, color='#222222')
    
    output_path = OUTPUT_DIR / f"viz_{country}_resumen.png"
    plt.savefig(output_path, dpi=VIZ_CONFIG['dpi'], bbox_inches='tight', facecolor='white')
    _ensure_stats_permissions(output_path)
    plt.close()

def create_all_country_visualizations(stats):
    """Create combined visualizations for all countries."""
    print("\n[*] Creando visualizaciones por país...")
    
    countries = sorted(stats['countries'].keys())
    
    for country in countries:
        create_viz_country_resumen(country, stats['countries'][country])
        print(f"  [OK] {country}")
    
    print(f"[OK] {len(countries)} visualizaciones de países creadas")

# ==============================================================================
# JSON EXPORT
# ==============================================================================

def export_json(stats):
    """Export statistics to JSON for frontend use."""
    print("\n[*] Exportando datos a JSON...")
    
    # Prepare JSON structure
    json_data = {
        'generated': datetime.now().isoformat(),
        'all_countries': {
            'total': {
                'word_count': stats['all_countries']['total']['word_count'],
                'duration': seconds_to_hms(stats['all_countries']['total']['duration'])
            },
            'pro': {
                'word_count': stats['all_countries']['pro']['word_count'],
                'duration': seconds_to_hms(stats['all_countries']['pro']['duration']),
                'percentage': round((stats['all_countries']['pro']['word_count'] / 
                                   stats['all_countries']['total']['word_count'] * 100), 1)
            },
            'otro': {
                'word_count': stats['all_countries']['otro']['word_count'],
                'duration': seconds_to_hms(stats['all_countries']['otro']['duration']),
                'percentage': round((stats['all_countries']['otro']['word_count'] / 
                                   stats['all_countries']['total']['word_count'] * 100), 1)
            },
            'pro_gender': {},
            'pro_mode_gender': {}
        },
        'countries': {}
    }
    
    # PRO gender (all countries)
    pro_total = stats['all_countries']['pro']['word_count']
    for sex in ['m', 'f']:
        json_data['all_countries']['pro_gender'][sex] = {
            'word_count': stats['all_countries']['pro_gender'][sex]['word_count'],
            'duration': seconds_to_hms(stats['all_countries']['pro_gender'][sex]['duration']),
            'percentage': round((stats['all_countries']['pro_gender'][sex]['word_count'] / 
                               pro_total * 100), 1) if pro_total > 0 else 0
        }
    
    # PRO mode × gender (all countries)
    for key, val in stats['all_countries']['pro_mode_gender'].items():
        json_data['all_countries']['pro_mode_gender'][key] = {
            'word_count': val['word_count'],
            'duration': seconds_to_hms(val['duration'])
        }
    
    # Per country
    for country, country_stats in stats['countries'].items():
        total = country_stats['total']['word_count']
        pro = country_stats['pro']['word_count']
        
        json_data['countries'][country] = {
            'total': {
                'word_count': total,
                'duration': seconds_to_hms(country_stats['total']['duration'])
            },
            'pro': {
                'word_count': pro,
                'duration': seconds_to_hms(country_stats['pro']['duration']),
                'percentage': round((pro / total * 100), 1) if total > 0 else 0
            },
            'otro': {
                'word_count': country_stats['otro']['word_count'],
                'duration': seconds_to_hms(country_stats['otro']['duration']),
                'percentage': round((country_stats['otro']['word_count'] / total * 100), 1) if total > 0 else 0
            },
            'pro_gender': {},
            'pro_mode_gender': {}
        }
        
        # PRO gender per country
        pro_gender_total = country_stats['pro_gender']['m']['word_count'] + country_stats['pro_gender']['f']['word_count']
        for sex in ['m', 'f']:
            json_data['countries'][country]['pro_gender'][sex] = {
                'word_count': country_stats['pro_gender'][sex]['word_count'],
                'duration': seconds_to_hms(country_stats['pro_gender'][sex]['duration']),
                'percentage': round((country_stats['pro_gender'][sex]['word_count'] / 
                                   pro_gender_total * 100), 1) if pro_gender_total > 0 else 0
            }
        
        # PRO mode × gender per country
        for key, val in country_stats['pro_mode_gender'].items():
            json_data['countries'][country]['pro_mode_gender'][key] = {
                'word_count': val['word_count'],
                'duration': seconds_to_hms(val['duration'])
            }
    
    # Save JSON
    output_path = OUTPUT_DIR / "corpus_stats.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    _ensure_stats_permissions(output_path)
    
    print(f"[OK] JSON guardado: {output_path.name}")

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    # require pandas at runtime
    if not HAS_PANDAS:
        print("[ERROR] 'pandas' is required to run this script.\nPlease install dependencies: pip install -r ../requirements-lokal.txt")
        return 1
    """Main execution function."""
    
    # Find and validate repo root
    try:
        repo_root = _find_repo_root()
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 2
    
    print("=" * 80)
    print("CO.RA.PAN - Publicación de Estadísticas del Corpus")
    print("=" * 80)
    print(f"Repository Root:              {repo_root}")
    print(f"Input CSV (per-country):      {CSV_PER_COUNTRY}")
    print(f"Input CSV (across-countries): {CSV_ACROSS_COUNTRIES}")
    print(f"Output Directory:             {OUTPUT_DIR}")
    print(f"Resolved corpus_stats.json:   {OUTPUT_DIR / 'corpus_stats.json'}")
    print("=" * 80)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _ensure_stats_permissions(OUTPUT_DIR)
    
    # Load data from CSV
    df_per_country, df_across = load_data_from_csv()
    
    # Aggregate statistics
    stats = aggregate_statistics(df_per_country, df_across)
    
    # Create visualizations
    print("\n" + "=" * 80)
    print("GENERANDO VISUALIZACIONES")
    print("=" * 80)
    
    # Composición del corpus
    create_viz_total_corpus(stats)
    create_viz_genero_profesionales(stats)
    create_viz_modo_genero_profesionales(stats)
    
    # Per country
    create_all_country_visualizations(stats)
    
    # Export JSON
    export_json(stats)
    
    print("\n" + "=" * 80)
    print("[OK] PUBLICACIÓN COMPLETADA")
    print("=" * 80)
    print(f"Directorio de salida: {OUTPUT_DIR}")
    print(f"  - 3 visualizaciones del corpus completo")
    print(f"  - {len(stats['countries'])} visualizaciones por país")
    print(f"  - 1 archivo JSON con todos los datos")
    print("=" * 80)

if __name__ == "__main__":
    main()
