#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
03_build_metadata_stats.py

Erstellt Metadaten-Datenbanken aus annotierten JSON-Transkripten.

EINGABEPFAD:  media/transcripts/<country>/*.json

AUSGABEDATEIEN:
    data/db/public/stats_country.db        - Statistiken pro Land
    data/db/public/stats_files.db          - Metadaten pro Datei

HINWEIS:
    transcription.db wird NICHT mehr erstellt.
    Die Token-Suche erfolgt über BlackLab direkt aus den JSONs.

VERWENDUNG:
    python 03_build_metadata_stats.py
    python 03_build_metadata_stats.py --rebuild
    python 03_build_metadata_stats.py --country ARG
    python 03_build_metadata_stats.py --verify-only

ERFORDERT:
    - Python >= 3.10
    - Annotierte JSON-Dateien (v3-Schema)

Copyright (c) 2025 CO.RA.PAN Project
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# ==============================================================================
# PFAD-KONFIGURATION
# ==============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # LOKAL/_1_json -> PROJECT_ROOT
TRANSCRIPTS_DIR = PROJECT_ROOT / "media" / "transcripts"

def resolve_data_root() -> Path:
    runtime_root = os.getenv("CORAPAN_RUNTIME_ROOT")
    if not runtime_root:
        raise RuntimeError(
            "CORAPAN_RUNTIME_ROOT not configured. "
            "Runtime data is required for stats database generation."
        )
    return Path(runtime_root) / "data"

DATA_ROOT = resolve_data_root()
PUBLIC_DB_DIR = DATA_ROOT / "db" / "public"
PUBLIC_DB_DIR.mkdir(parents=True, exist_ok=True)

# Country-Code-Normalisierung importieren
COUNTRIES_PY = PROJECT_ROOT / "src" / "app" / "config" / "countries.py"

def load_country_normalizer():
    """Lädt normalize_country_code aus countries.py."""
    if not COUNTRIES_PY.exists():
        logging.warning(f"countries.py nicht gefunden: {COUNTRIES_PY}")
        return lambda x: x.upper().strip() if x else ""
    
    spec = importlib.util.spec_from_file_location("countries_module", COUNTRIES_PY)
    # spec may be None (if file invalid). Guard and provide fallback to keep static analyzers happy
    if spec is None or getattr(spec, 'loader', None) is None:
        logging.warning(f"Failed to create module spec for countries.py: {COUNTRIES_PY}")
        return lambda x: x.upper().strip() if x else ""

    module = importlib.util.module_from_spec(spec)  # spec is not None here
    sys.modules['countries_module'] = module
    # spec.loader is guaranteed non-None due to check above
    spec.loader.exec_module(module)
    return module.normalize_country_code

normalize_country_code = load_country_normalizer()

# ==============================================================================
# LOGGING
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ==============================================================================
# HILFSFUNKTIONEN
# ==============================================================================

def seconds_to_hms(seconds: float) -> str:
    """Konvertiert Sekunden zu HH:MM:SS."""
    hrs, r = divmod(int(seconds), 3600)
    mins, secs = divmod(r, 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"


def seconds_to_hms_files(seconds: float) -> str:
    """Konvertiert Sekunden zu HH:MM:SS.ss."""
    hrs, r = divmod(seconds, 3600)
    mins, secs = divmod(r, 60)
    return f"{int(hrs):02d}:{int(mins):02d}:{secs:.2f}"


def ms_to_seconds(ms: int) -> float:
    """Konvertiert Millisekunden zu Sekunden."""
    return ms / 1000.0


def get_duration_from_words(words: list[dict[str, Any]]) -> float:
    """
    Berechnet Dauer aus Wortliste.
    
    Unterstützt v3 (end_ms) und v2 (end).
    
    Returns:
        Dauer in Sekunden
    """
    if not words:
        return 0.0
    
    last_word = words[-1]
    
    # v3: end_ms (int, Millisekunden)
    if "end_ms" in last_word:
        return ms_to_seconds(last_word["end_ms"])
    
    # v2 Fallback: end (float, Sekunden)
    return float(last_word.get("end", 0.0))


def get_file_duration(data: dict[str, Any]) -> float:
    """
    Berechnet Gesamtdauer einer Datei.
    
    Returns:
        Dauer in Sekunden
    """
    max_end = 0.0
    
    for seg in data.get("segments", []):
        words = seg.get("words", [])
        if words:
            end = get_duration_from_words(words)
            if end > max_end:
                max_end = end
    
    return max_end


def get_word_count(data: dict[str, Any]) -> int:
    """Zählt alle Wörter in einer Datei."""
    return sum(len(seg.get("words", [])) for seg in data.get("segments", []))


def optimize_database(conn: sqlite3.Connection) -> None:
    """Wendet Performance-Optimierungen auf Datenbank an."""
    cursor = conn.cursor()
    
    pragmas = [
        ("cache_size", "-64000"),      # 64 MB Cache
        ("temp_store", "MEMORY"),      # Temp-Tabellen im RAM
        ("journal_mode", "WAL"),       # Write-Ahead Logging
        ("synchronous", "NORMAL"),     # Balanced Safety/Speed
    ]
    
    for pragma, value in pragmas:
        cursor.execute(f"PRAGMA {pragma} = {value}")
    
    conn.commit()


def collect_json_files(country: str | None = None) -> list[Path]:
    """
    Sammelt alle JSON-Dateien aus dem Transkript-Verzeichnis.
    
    Args:
        country: Optional, nur dieses Land
    
    Returns:
        Sortierte Liste von Pfaden
    """
    if not TRANSCRIPTS_DIR.exists():
        logger.error(f"Verzeichnis nicht gefunden: {TRANSCRIPTS_DIR}")
        return []
    
    json_files: list[Path] = []
    
    # Sortierte Länderverzeichnisse
    country_dirs = sorted([d for d in TRANSCRIPTS_DIR.iterdir() if d.is_dir()])
    
    for country_dir in country_dirs:
        # Filter auf Land
        if country and normalize_country_code(country_dir.name) != normalize_country_code(country):
            continue
        
        # Sortierte JSON-Dateien
        country_files = sorted(country_dir.glob("*.json"))
        json_files.extend(country_files)
    
    logger.info(f"Gefunden: {len(json_files)} JSON-Dateien in {len(country_dirs)} Ländern")
    return json_files

# ==============================================================================
# 1) stats_country.db - Statistiken pro Land
# ==============================================================================

def build_stats_country(json_files: list[Path]) -> bool:
    """
    Erstellt stats_country.db mit Statistiken pro Land.
    
    Tabelle stats_country:
        - country_code: Ländercode (z.B. ARG, ESP)
        - total_word_count: Wortzahl pro Land
        - total_duration_country: Dauer pro Land als HH:MM:SS
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("1/2 → Erstelle stats_country.db")
    logger.info("=" * 70)
    
    PUBLIC_DB_DIR.mkdir(parents=True, exist_ok=True)
    db_path = PUBLIC_DB_DIR / "stats_country.db"
    
    conn = sqlite3.connect(str(db_path))
    optimize_database(conn)
    cursor = conn.cursor()
    
    # Tabelle erstellen
    cursor.execute("DROP TABLE IF EXISTS stats_country")
    cursor.execute("""
        CREATE TABLE stats_country (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT UNIQUE,
            total_word_count INTEGER,
            total_duration_country TEXT
        )
    """)
    
    if not json_files:
        logger.warning("Keine JSON-Dateien gefunden")
        conn.close()
        return True
    
    # Aggregiere pro Land
    country_stats: dict[str, dict[str, Any]] = {}
    errors = 0
    
    logger.info("Verarbeite Dateien nach Land...")
    
    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            
            # Land aus JSON oder Ordnername
            country_code = data.get("country_code", "")
            if not country_code:
                country_code = normalize_country_code(jf.parent.name)
            
            if country_code not in country_stats:
                country_stats[country_code] = {"word_count": 0, "duration": 0.0}
            
            country_stats[country_code]["word_count"] += get_word_count(data)
            country_stats[country_code]["duration"] += get_file_duration(data)
        
        except Exception as e:
            logger.warning(f"Fehler bei {jf.name}: {e}")
            errors += 1
            continue
    
    # In DB einfügen
    for country_code, stats in sorted(country_stats.items()):
        duration_str = seconds_to_hms(stats["duration"])
        cursor.execute(
            """INSERT INTO stats_country (country_code, total_word_count, total_duration_country)
               VALUES (?, ?, ?)""",
            (country_code, stats["word_count"], duration_str)
        )
    
    conn.commit()
    conn.close()
    
    logger.info("")
    logger.info(f"✅ stats_country.db erstellt:")
    logger.info(f"   Länder: {len(country_stats)}")
    for cc, st in sorted(country_stats.items()):
        logger.info(f"     {cc}: {st['word_count']:,} Wörter, {seconds_to_hms(st['duration'])}")
    if errors > 0:
        logger.warning(f"   Fehler: {errors} Dateien übersprungen")
    
    return True

# ==============================================================================
# 2) stats_files.db - Metadaten pro Datei
# ==============================================================================

def build_stats_files(json_files: list[Path]) -> bool:
    """
    Erstellt stats_files.db mit Metadaten pro Datei.
    
    Tabelle metadata:
        - filename: MP3-Dateiname (aus JSON-Metadaten)
        - country_code: Ländercode
        - radio: Radiosender
        - date: Datum (YYYY-MM-DD)
        - revision: Revisionsinfo
        - word_count: Wortzahl
        - duration: Dauer als HH:MM:SS.ss
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("2/2 → Erstelle stats_files.db")
    logger.info("=" * 70)
    
    PUBLIC_DB_DIR.mkdir(parents=True, exist_ok=True)
    db_path = PUBLIC_DB_DIR / "stats_files.db"
    
    conn = sqlite3.connect(str(db_path))
    optimize_database(conn)
    cursor = conn.cursor()
    
    # Tabelle erstellen
    cursor.execute("DROP TABLE IF EXISTS metadata")
    cursor.execute("""
        CREATE TABLE metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            country_code TEXT,
            radio TEXT,
            date TEXT,
            revision TEXT,
            word_count INTEGER,
            duration TEXT
        )
    """)
    
    if not json_files:
        logger.warning("Keine JSON-Dateien gefunden")
        conn.close()
        return True
    
    inserted = 0
    errors = 0
    
    logger.info("Verarbeite Datei-Metadaten...")
    
    for idx, jf in enumerate(json_files, 1):
        try:
            with open(jf, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            
            # Country-Code
            country_code = data.get("country_code", "")
            if not country_code:
                country_code = normalize_country_code(jf.parent.name)
            
            # Filename (MP3, nicht JSON)
            filename = data.get("filename", "")
            if not filename:
                file_id = data.get("file_id") or f"{country_code}_{jf.stem}"
                filename = f"{file_id}.mp3"
            
            # Metadaten
            radio = data.get("radio", "")
            date = data.get("date", "")
            revision = data.get("revision", "")
            
            # Statistiken
            word_count = get_word_count(data)
            duration = get_file_duration(data)
            duration_str = seconds_to_hms_files(duration)
            
            cursor.execute(
                """INSERT INTO metadata (filename, country_code, radio, date, revision, word_count, duration)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (filename, country_code, radio, date, revision, word_count, duration_str)
            )
            inserted += 1
        
        except sqlite3.IntegrityError:
            logger.warning(f"Duplikat: {jf.name} übersprungen")
            continue
        except Exception as e:
            logger.warning(f"Fehler bei {jf.name}: {e}")
            errors += 1
            continue
        
        if idx % 50 == 0 or idx == len(json_files):
            logger.info(f"  {idx}/{len(json_files)} Dateien verarbeitet")
    
    conn.commit()
    conn.close()
    
    logger.info("")
    logger.info(f"✅ stats_files.db erstellt:")
    logger.info(f"   Einträge: {inserted}")
    if errors > 0:
        logger.warning(f"   Fehler: {errors} Dateien übersprungen")
    
    return True

# ==============================================================================
# VERIFY-ONLY MODE
# ==============================================================================

def verify_databases() -> bool:
    """
    Überprüft Existenz und Inhalt der Datenbanken.
    
    Returns:
        True wenn alle Prüfungen bestanden
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("DATENBANK-VERIFIZIERUNG")
    logger.info("=" * 70)
    
    all_ok = True
    
    # stats_country.db
    stats_country_path = PUBLIC_DB_DIR / "stats_country.db"
    if stats_country_path.exists():
        conn = sqlite3.connect(str(stats_country_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stats_country")
        count = cursor.fetchone()[0]
        conn.close()
        logger.info(f"✅ stats_country.db: {count} Länder")
    else:
        logger.error(f"❌ stats_country.db nicht gefunden: {stats_country_path}")
        all_ok = False
    
    # stats_files.db
    stats_files_path = PUBLIC_DB_DIR / "stats_files.db"
    if stats_files_path.exists():
        conn = sqlite3.connect(str(stats_files_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM metadata")
        count = cursor.fetchone()[0]
        conn.close()
        logger.info(f"✅ stats_files.db: {count} Dateien")
    else:
        logger.error(f"❌ stats_files.db nicht gefunden: {stats_files_path}")
        all_ok = False
    
    # Hinweis auf transcription.db
    transcription_path = PUBLIC_DB_DIR / "transcription.db"
    if transcription_path.exists():
        logger.info("")
        logger.info("ℹ️  transcription.db existiert (Legacy)")
        logger.info("   Diese Datei wird von der neuen Pipeline nicht mehr erzeugt.")
        logger.info("   Token-Suche erfolgt über BlackLab direkt aus den JSONs.")
    
    logger.info("")
    if all_ok:
        logger.info("✅ Alle Datenbanken verifiziert!")
    else:
        logger.error("❌ Einige Prüfungen fehlgeschlagen")
    
    return all_ok

# ==============================================================================
# CLI & MAIN
# ==============================================================================

def parse_args() -> argparse.Namespace:
    """Parst Kommandozeilenargumente."""
    parser = argparse.ArgumentParser(
        description="Erstellt Metadaten-Datenbanken aus annotierten JSON-Transkripten.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python 03_build_metadata_stats.py
  python 03_build_metadata_stats.py --rebuild
  python 03_build_metadata_stats.py --country ARG
  python 03_build_metadata_stats.py --verify-only

Ausgabedateien:
    data/db/public/stats_country.db        - Statistiken pro Land
    data/db/public/stats_files.db          - Metadaten pro Datei

HINWEIS: transcription.db wird NICHT mehr erstellt!
         Token-Suche erfolgt über BlackLab direkt aus den JSONs.
        """,
    )
    
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Datenbanken neu erstellen (Standard)",
    )
    
    parser.add_argument(
        "--country", "-c",
        type=str,
        default=None,
        help="Nur dieses Land verarbeiten (z.B. ARG, ESP)",
    )
    
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Nur Datenbanken prüfen, nicht neu erstellen",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Ausführliche Ausgabe",
    )
    
    return parser.parse_args()


def main() -> int:
    """Hauptfunktion."""
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Header
    logger.info("=" * 70)
    logger.info("CO.RA.PAN - Metadaten-Datenbank Builder")
    logger.info("=" * 70)
    logger.info(f"Projekt-Root:       {PROJECT_ROOT}")
    logger.info(f"Transkript-Pfad:    {TRANSCRIPTS_DIR}")
    logger.info(f"DB-Public:          {PUBLIC_DB_DIR}")
    if args.country:
        logger.info(f"Filter:             nur {args.country}")
    logger.info("")
    
    # Verify-Only Mode
    if args.verify_only:
        success = verify_databases()
        return 0 if success else 1
    
    # Zeitmessung starten
    start_time = time.time()
    
    # Transkript-Verzeichnis prüfen
    if not TRANSCRIPTS_DIR.exists():
        logger.error(f"Verzeichnis nicht gefunden: {TRANSCRIPTS_DIR}")
        return 1
    
    # JSON-Dateien sammeln
    json_files = collect_json_files(country=args.country)
    
    if not json_files:
        logger.error("Keine JSON-Dateien gefunden")
        return 1
    
    # Datenbanken erstellen
    success = True
    
    if not build_stats_country(json_files):
        success = False
    
    if not build_stats_files(json_files):
        success = False
    
    # Zeitmessung
    elapsed = time.time() - start_time
    
    # Zusammenfassung
    logger.info("")
    logger.info("=" * 70)
    if success:
        logger.info("✅ DATENBANK-ERSTELLUNG ABGESCHLOSSEN")
    else:
        logger.info("⚠️  DATENBANK-ERSTELLUNG MIT WARNUNGEN")
    logger.info("=" * 70)
    logger.info(f"Laufzeit: {elapsed:.2f}s ({elapsed/60:.1f} Minuten)")
    logger.info("")
    logger.info("Erstellte DBs:")
    logger.info(f"  • {PUBLIC_DB_DIR / 'stats_country.db'}")
    logger.info(f"  • {PUBLIC_DB_DIR / 'stats_files.db'}")
    logger.info("")
    logger.info("ℹ️  HINWEISE:")
    logger.info("   • transcription.db wird nicht mehr erstellt (BlackLab nutzt JSONs direkt)")
    logger.info("   Token-Suche erfolgt über BlackLab direkt aus den JSONs.")
    logger.info("")
    logger.info("💡 Verifizierung:")
    logger.info("   python 03_build_metadata_stats.py --verify-only")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
