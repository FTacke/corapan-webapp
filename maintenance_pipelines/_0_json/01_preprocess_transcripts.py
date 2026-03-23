#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
01_preprocess_transcripts.py

Bereitet Roh-JSONs für die Annotation vor.

EINGABEPFAD:  LOKAL/_1_json/json-pre/*.json
AUSGABEPFAD:  LOKAL/_1_json/json-ready/*.json

SCHRITTE:
    1. Entfernt irrelevante Felder: duration, conf, pristine
    2. Bereinigt Self-Corrections: "-," und "-." → "-"
    3. Markiert Fremdwörter: (foreign)-Tag → foreign="1"
    4. Speaker-Migration: speakers[] + segment.speaker → segment.speaker_code

VERWENDUNG:
    python 01_preprocess_transcripts.py
    python 01_preprocess_transcripts.py --limit 5
    python 01_preprocess_transcripts.py --strict

ERFORDERT:
    - Python >= 3.10
    - JSON-Dateien im Verzeichnis json-pre/

Copyright (c) 2025 CO.RA.PAN Project
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ==============================================================================
# KONFIGURATION
# ==============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DIR = SCRIPT_DIR / "json-pre"
OUTPUT_DIR = SCRIPT_DIR / "json-ready"

# Regex für (foreign)-Tag
FOREIGN_TAG_RE = re.compile(r"\(foreign\)", re.IGNORECASE)

# Regex für Self-Correction: -. oder -, → -
SELFCORRECTION_RE = re.compile(r"-(?:[,.])")

# Interpunktion für Trimming
PUNCTUATION = ".,?!¿¡"

# Default-Code für unbekannte Speaker
NONE_CODE = "none"

# Speaker-Mapping: Code → Attribute (gemäß README-pipeline_json.md)
SPEAKER_MAPPING: dict[str, dict[str, str]] = {
    "lib-pm": {
        "speaker_type": "pro",
        "speaker_sex": "m",
        "speaker_mode": "libre",
        "speaker_discourse": "general",
    },
    "lib-pf": {
        "speaker_type": "pro",
        "speaker_sex": "f",
        "speaker_mode": "libre",
        "speaker_discourse": "general",
    },
    "lib-om": {
        "speaker_type": "otro",
        "speaker_sex": "m",
        "speaker_mode": "libre",
        "speaker_discourse": "general",
    },
    "lib-of": {
        "speaker_type": "otro",
        "speaker_sex": "f",
        "speaker_mode": "libre",
        "speaker_discourse": "general",
    },
    "lec-pm": {
        "speaker_type": "pro",
        "speaker_sex": "m",
        "speaker_mode": "lectura",
        "speaker_discourse": "general",
    },
    "lec-pf": {
        "speaker_type": "pro",
        "speaker_sex": "f",
        "speaker_mode": "lectura",
        "speaker_discourse": "general",
    },
    "lec-om": {
        "speaker_type": "otro",
        "speaker_sex": "m",
        "speaker_mode": "lectura",
        "speaker_discourse": "general",
    },
    "lec-of": {
        "speaker_type": "otro",
        "speaker_sex": "f",
        "speaker_mode": "lectura",
        "speaker_discourse": "general",
    },
    "pre-pm": {
        "speaker_type": "pro",
        "speaker_sex": "m",
        "speaker_mode": "pre",
        "speaker_discourse": "general",
    },
    "pre-pf": {
        "speaker_type": "pro",
        "speaker_sex": "f",
        "speaker_mode": "pre",
        "speaker_discourse": "general",
    },
    "tie-pm": {
        "speaker_type": "pro",
        "speaker_sex": "m",
        "speaker_mode": "n/a",
        "speaker_discourse": "tiempo",
    },
    "tie-pf": {
        "speaker_type": "pro",
        "speaker_sex": "f",
        "speaker_mode": "n/a",
        "speaker_discourse": "tiempo",
    },
    "traf-pm": {
        "speaker_type": "pro",
        "speaker_sex": "m",
        "speaker_mode": "n/a",
        "speaker_discourse": "tránsito",
    },
    "traf-pf": {
        "speaker_type": "pro",
        "speaker_sex": "f",
        "speaker_mode": "n/a",
        "speaker_discourse": "tránsito",
    },
    "foreign": {
        "speaker_type": "n/a",
        "speaker_sex": "n/a",
        "speaker_mode": "n/a",
        "speaker_discourse": "foreign",
    },
    "none": {
        "speaker_type": "-",
        "speaker_sex": "-",
        "speaker_mode": "-",
        "speaker_discourse": "-",
    },
}

# Erlaubte Speaker-Codes (abgeleitet aus SPEAKER_MAPPING)
ALLOWED_SPEAKER_CODES = frozenset(SPEAKER_MAPPING.keys())

# Felder, die aus Wort-Objekten entfernt werden
UNWANTED_FIELDS = ("duration", "conf", "pristine")

# Bekannte Fremdwörter (Kleinschreibung)
CUSTOM_FOREIGN_WORDS = frozenset({
    "whatsapp", "google", "tiktok", "facebook", "twitter",
    "instagram", "youtube", "spotify", "uber", "zoom",
})

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
# STATISTIKEN
# ==============================================================================

class Statistics:
    """Erfasst Verarbeitungsstatistiken."""
    
    def __init__(self) -> None:
        self.files_processed = 0
        self.files_written = 0
        self.fields_removed = 0
        self.selfcorrections_fixed = 0
        self.foreign_tags_removed = 0
        self.custom_foreign_marked = 0
        self.speakers_migrated = 0
        self.speaker_codes_set = 0
        self.speaker_objects_set = 0
        self.unknown_codes: set[str] = set()
        self.validation_errors: list[str] = []
    
    def summary(self) -> str:
        """Gibt Zusammenfassung als String zurück."""
        lines = [
            "=" * 70,
            "ZUSAMMENFASSUNG",
            "=" * 70,
            f"Verarbeitete Dateien:         {self.files_processed}",
            f"Geschriebene Dateien:         {self.files_written}",
            f"Entfernte Felder (total):     {self.fields_removed}",
            f"Bereinigte Self-Corrections:  {self.selfcorrections_fixed}",
            f"Entfernte (foreign)-Tags:     {self.foreign_tags_removed}",
            f"Custom-Fremdwörter markiert:  {self.custom_foreign_marked}",
            f"Speaker-Blöcke migriert:      {self.speakers_migrated}",
            f"Speaker-Codes gesetzt:        {self.speaker_codes_set}",
            f"Speaker-Objekte erzeugt:      {self.speaker_objects_set}",
        ]
        
        if self.unknown_codes:
            lines.append("")
            lines.append("⚠️  Nicht erlaubte Speaker-Codes → auf 'none' gesetzt:")
            for code in sorted(self.unknown_codes):
                lines.append(f"    - {code}")
        
        if self.validation_errors:
            lines.append("")
            lines.append("❌ Validierungsfehler:")
            for err in self.validation_errors[:10]:
                lines.append(f"    - {err}")
            if len(self.validation_errors) > 10:
                lines.append(f"    ... und {len(self.validation_errors) - 10} weitere")
        
        lines.append("=" * 70)
        return "\n".join(lines)


# ==============================================================================
# HILFSFUNKTIONEN
# ==============================================================================

def nfc(s: str | None) -> str:
    """Normalisiert String zu Unicode NFC."""
    return unicodedata.normalize("NFC", s or "")


def build_speaker_object(code: str) -> dict[str, str]:
    """
    Erzeugt ein vollständiges Speaker-Objekt aus einem Speaker-Code.
    
    Args:
        code: Speaker-Code (z.B. 'lib-pm', 'foreign', 'none')
    
    Returns:
        Dict mit code, speaker_type, speaker_sex, speaker_mode, speaker_discourse
    """
    code = nfc((code or "").strip())
    if code not in SPEAKER_MAPPING:
        code = NONE_CODE
    info = SPEAKER_MAPPING[code]
    return {
        "code": code,
        "speaker_type": info["speaker_type"],
        "speaker_sex": info["speaker_sex"],
        "speaker_mode": info["speaker_mode"],
        "speaker_discourse": info["speaker_discourse"],
    }


def reorder_segment(seg: dict[str, Any]) -> dict[str, Any]:
    """
    Ordnet Segment-Keys so, dass Metadaten zuerst und 'words' am Ende steht.
    
    Reihenfolge:
        1. utt_start_ms, utt_end_ms, speaker_code, speaker (priorisiert)
        2. Alle anderen Segment-Keys (außer words)
        3. words (am Ende)
    
    Returns:
        Neues dict mit geordneten Keys (keine Daten gehen verloren)
    """
    ordered: dict[str, Any] = {}
    
    # Priorisierte Keys in dieser Reihenfolge
    priority_keys = ("utt_start_ms", "utt_end_ms", "speaker_code", "speaker")
    for key in priority_keys:
        if key in seg:
            ordered[key] = seg[key]
    
    # Andere Segment-Felder (außer 'words')
    for key, value in seg.items():
        if key not in ordered and key != "words":
            ordered[key] = value
    
    # 'words' ans Ende
    if "words" in seg:
        ordered["words"] = seg["words"]
    
    return ordered


def reorder_file_structure(data: dict[str, Any]) -> dict[str, Any]:
    """
    Ordnet Top-Level-Keys so, dass Metadaten vor 'segments' stehen.
    
    Reihenfolge:
        1. country_code, filename, radio, date, revision, audio, audio_path, ann_meta (priorisiert)
        2. segments (mit intern geordneten Segmenten)
        3. Alle übrigen Top-Level-Keys
    
    Returns:
        Neues dict mit geordneten Keys (keine Daten gehen verloren)
    """
    # Top-Level Reihenfolge
    top_order = (
        "country_code",
        "filename",
        "radio",
        "date",
        "revision",
        "audio",
        "audio_path",
        "ann_meta",
        "segments",
    )
    
    ordered: dict[str, Any] = {}
    
    # Priorisierte Keys
    for key in top_order:
        if key in data:
            if key == "segments" and isinstance(data.get("segments"), list):
                # Segmente einzeln ordnen
                ordered["segments"] = [reorder_segment(seg) for seg in data["segments"]]
            else:
                ordered[key] = data[key]
    
    # Übrige Keys anhängen
    for key, value in data.items():
        if key not in ordered:
            ordered[key] = value
    
    return ordered


def remove_unwanted_fields(word: dict[str, Any]) -> int:
    """
    Entfernt irrelevante Felder aus Wort-Dictionary.
    
    Returns:
        Anzahl entfernter Felder.
    """
    removed = 0
    for field in UNWANTED_FIELDS:
        if field in word:
            del word[field]
            removed += 1
    return removed


def fix_selfcorrection(text: str) -> tuple[str, bool]:
    """
    Bereinigt Self-Correction-Marker.
    
    "-," und "-." werden zu "-".
    
    Returns:
        Tuple (neuer_text, wurde_geändert)
    """
    new_text = SELFCORRECTION_RE.sub("-", text)
    return new_text, new_text != text


def remove_foreign_tag(text: str, keep_punctuation: bool = True) -> str:
    """
    Entfernt (foreign)-Tag aus Text.
    
    Args:
        text: Eingabetext
        keep_punctuation: Ob Satzzeichen am Ende behalten werden sollen
    
    Returns:
        Bereinigter Text
    """
    cleaned = FOREIGN_TAG_RE.sub("", text).strip()
    if not keep_punctuation:
        cleaned = cleaned.rstrip(PUNCTUATION).strip()
    return cleaned


def is_custom_foreign(text: str) -> bool:
    """Prüft, ob Text ein bekanntes Fremdwort ist."""
    normalized = text.lower().rstrip(PUNCTUATION)
    return normalized in CUSTOM_FOREIGN_WORDS


def is_allowed_speaker_code(code: str) -> bool:
    """Prüft, ob Speaker-Code erlaubt ist."""
    return code in ALLOWED_SPEAKER_CODES


def migrate_speakers(data: dict[str, Any], stats: Statistics) -> bool:
    """
    Migriert speakers[] Array zu speaker_code und speaker-Objekt pro Segment.
    
    Args:
        data: JSON-Daten
        stats: Statistik-Objekt
    
    Returns:
        True wenn Änderungen vorgenommen wurden
    """
    changed = False
    
    # 1) Baue Speaker-Map aus speakers[] Array
    speakers = data.get("speakers", [])
    spk_map: dict[str, str] = {}
    for s in speakers:
        spkid = s.get("spkid")
        if spkid:
            name = nfc((s.get("name") or "").strip())
            spk_map[spkid] = name
    
    # 2) Setze speaker_code und speaker-Objekt pro Segment
    for seg in data.get("segments", []):
        # Prüfe ob speaker_code bereits existiert
        code = seg.get("speaker_code")
        
        if not code:
            # Versuche von altem speaker-Feld zu migrieren (falls es eine ID ist)
            old_speaker = seg.get("speaker")
            if isinstance(old_speaker, str):
                code = spk_map.get(old_speaker, old_speaker)
        
        # Normalisiere
        code = nfc((code or "").strip())
        
        # Validiere
        if not is_allowed_speaker_code(code):
            if code:
                stats.unknown_codes.add(code)
            code = NONE_CODE
        
        # Setze neuen Code
        if seg.get("speaker_code") != code:
            seg["speaker_code"] = code
            stats.speaker_codes_set += 1
            changed = True
        
        # Erzeuge vollständiges speaker-Objekt
        speaker_obj = build_speaker_object(code)
        seg["speaker"] = speaker_obj
        stats.speaker_objects_set += 1
        changed = True
    
    # 3) Entferne speakers[] Array auf Root-Ebene
    if "speakers" in data:
        del data["speakers"]
        stats.speakers_migrated += 1
        changed = True
    
    # 4) Markiere Migration in ann_meta
    ann_meta = data.setdefault("ann_meta", {})
    if not ann_meta.get("speaker_code_migrated", False):
        ann_meta["speaker_code_migrated"] = True
        ann_meta["speaker_migration_timestamp"] = datetime.now(timezone.utc).isoformat()
        changed = True
    
    return changed


def validate_json(data: dict[str, Any], filename: str) -> list[str]:
    """
    Validiert JSON-Struktur.
    
    Returns:
        Liste von Fehlermeldungen (leer wenn valide)
    """
    errors = []
    
    if "segments" not in data:
        errors.append(f"{filename}: Fehlt 'segments' Array")
        return errors
    
    segments = data.get("segments", [])
    if not isinstance(segments, list):
        errors.append(f"{filename}: 'segments' ist kein Array")
        return errors
    
    for seg_idx, seg in enumerate(segments):
        if not isinstance(seg, dict):
            errors.append(f"{filename}: segment[{seg_idx}] ist kein Object")
            continue
        
        words = seg.get("words")
        if words is None:
            errors.append(f"{filename}: segment[{seg_idx}] fehlt 'words'")
        elif not isinstance(words, list):
            errors.append(f"{filename}: segment[{seg_idx}].words ist kein Array")
    
    return errors


def process_words(segment: dict[str, Any], stats: Statistics) -> bool:
    """
    Verarbeitet alle Wörter in einem Segment.
    
    Returns:
        True wenn Änderungen vorgenommen wurden
    """
    changed = False
    words = segment.get("words", [])
    
    for word in words:
        # 1) Unerwünschte Felder entfernen
        removed = remove_unwanted_fields(word)
        if removed > 0:
            stats.fields_removed += removed
            changed = True
        
        text = word.get("text", "")
        
        # 2) Self-Corrections bereinigen
        if text:
            new_text, was_fixed = fix_selfcorrection(text)
            if was_fixed:
                word["text"] = new_text
                stats.selfcorrections_fixed += 1
                changed = True
                text = new_text
        
        # 3a) (foreign)-Tag entfernen
        if text and "(foreign)" in text.lower():
            word["text"] = remove_foreign_tag(text, keep_punctuation=True)
            
            # Auch in lemma und head_text bereinigen
            if "lemma" in word:
                word["lemma"] = remove_foreign_tag(word["lemma"], keep_punctuation=False)
            if "head_text" in word:
                word["head_text"] = remove_foreign_tag(word["head_text"], keep_punctuation=False)
            
            # Als Fremdwort markieren
            if word.get("foreign") != "1":
                word["foreign"] = "1"
            
            stats.foreign_tags_removed += 1
            changed = True
            continue  # Bereits markiert, nicht nochmal prüfen
        
        # 3b) Bekannte Fremdwörter markieren
        if text and word.get("foreign") != "1":
            if is_custom_foreign(text):
                word["foreign"] = "1"
                stats.custom_foreign_marked += 1
                changed = True
    
    return changed


def process_file(
    input_path: Path,
    output_path: Path,
    stats: Statistics,
    strict: bool = False,
) -> bool:
    """
    Verarbeitet eine einzelne JSON-Datei.
    
    Returns:
        True wenn erfolgreich
    """
    try:
        with open(input_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        msg = f"{input_path.name}: JSON-Syntaxfehler: {e}"
        logger.error(msg)
        stats.validation_errors.append(msg)
        return False
    except Exception as e:
        msg = f"{input_path.name}: Lesefehler: {e}"
        logger.error(msg)
        stats.validation_errors.append(msg)
        return False
    
    # Validierung
    errors = validate_json(data, input_path.name)
    if errors:
        for err in errors:
            logger.warning(err)
            stats.validation_errors.append(err)
        if strict:
            return False
        # Im nicht-strikten Modus: Datei überspringen aber weitermachen
        return True
    
    stats.files_processed += 1
    
    # 4) Speaker-Migration (vor Word-Processing)
    migrate_speakers(data, stats)
    
    # Segmente verarbeiten
    for seg in data.get("segments", []):
        process_words(seg, stats)
    
    # Ausgabeverzeichnis erstellen
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Schlüsselreihenfolge erzwingen (Metadaten vor segments, words am Ende)
    data = reorder_file_structure(data)
    
    # Datei schreiben
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        stats.files_written += 1
        return True
    except Exception as e:
        msg = f"{input_path.name}: Schreibfehler: {e}"
        logger.error(msg)
        stats.validation_errors.append(msg)
        return False


# ==============================================================================
# CLI & MAIN
# ==============================================================================

def parse_args() -> argparse.Namespace:
    """Parst Kommandozeilenargumente."""
    parser = argparse.ArgumentParser(
        description="Bereitet Roh-JSONs für die Annotation vor.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python 01_preprocess_transcripts.py
  python 01_preprocess_transcripts.py --limit 5
  python 01_preprocess_transcripts.py --strict
  python 01_preprocess_transcripts.py --input ./custom-input --output ./custom-output
        """,
    )
    
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=None,
        help="Nur N Dateien verarbeiten",
    )
    
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Abbruch bei Validierungsfehlern",
    )
    
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=INPUT_DIR,
        help=f"Eingabeverzeichnis (Standard: {INPUT_DIR})",
    )
    
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Ausgabeverzeichnis (Standard: {OUTPUT_DIR})",
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
    logger.info("CO.RA.PAN - Preprocessing für JSON-Transkripte")
    logger.info("=" * 70)
    logger.info(f"Eingabeverzeichnis: {args.input}")
    logger.info(f"Ausgabeverzeichnis: {args.output}")
    if args.limit:
        logger.info(f"Limit: {args.limit} Dateien")
    if args.strict:
        logger.info("Modus: STRICT (Abbruch bei Fehlern)")
    logger.info("")
    
    # Eingabeverzeichnis prüfen
    if not args.input.exists():
        logger.error(f"Eingabeverzeichnis nicht gefunden: {args.input}")
        return 1
    
    # JSON-Dateien sammeln
    json_files = sorted(args.input.glob("*.json"))
    
    if not json_files:
        logger.error(f"Keine JSON-Dateien in '{args.input}' gefunden.")
        return 1
    
    # Limit anwenden
    if args.limit:
        json_files = json_files[:args.limit]
    
    logger.info(f"Gefundene Dateien: {len(json_files)}")
    logger.info("")
    
    # Verarbeitung
    stats = Statistics()
    
    for idx, input_path in enumerate(json_files, 1):
        output_path = args.output / input_path.name
        
        success = process_file(input_path, output_path, stats, strict=args.strict)
        
        status = "✓" if success else "✗"
        logger.info(f"  {status} [{idx}/{len(json_files)}] {input_path.name}")
        
        if not success and args.strict:
            logger.error("Abbruch wegen --strict Modus")
            break
    
    # Zusammenfassung
    logger.info("")
    print(stats.summary())
    
    if stats.validation_errors and args.strict:
        return 1
    
    logger.info("")
    logger.info("✅ Preprocessing abgeschlossen!")
    logger.info(f"   Ausgabeverzeichnis: {args.output}")
    logger.info("")
    logger.info("💡 Nächster Schritt:")
    logger.info("   1. Dateien aus json-ready/ nach media/transcripts/<country>/ kopieren")
    logger.info("   2. Dann: python 02_annotate_transcripts_v3.py --country=XX")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
