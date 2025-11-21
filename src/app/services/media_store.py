"""Media storage helpers with intelligent country subfolder detection."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import re

MEDIA_ROOT = Path(__file__).resolve().parents[3] / "media"
MP3_FULL_DIR = MEDIA_ROOT / "mp3-full"
MP3_SPLIT_DIR = MEDIA_ROOT / "mp3-split"
MP3_TEMP_DIR = MEDIA_ROOT / "mp3-temp"
TRANSCRIPTS_DIR = MEDIA_ROOT / "transcripts"

for directory in (MP3_FULL_DIR, MP3_SPLIT_DIR, MP3_TEMP_DIR, TRANSCRIPTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def extract_country_code(filename: str) -> Optional[str]:
    """
    Extract country code from filename.
    Examples:
        "2022-01-18_VEN_RCR.mp3" -> "VEN"
        "2023-08-10_ARG_Mitre.mp3" -> "ARG"
        "2024-08-15_ESP_CadenaSer.mp3" -> "ESP"
        "2024-01-10_ARG-CBA_LV3.mp3" -> "ARG-CBA"
        "2025-02-28_USA_Univision.mp3" -> "USA"
        "VEN/2022-01-18_VEN_RCR.mp3" -> "VEN" (already has path)
    """
    # If filename already contains a path separator, extract from path
    if "/" in filename or "\\" in filename:
        path_parts = Path(filename).parts
        if len(path_parts) > 1:
            return path_parts[0]

    # Extract from filename pattern: YYYY-MM-DD_CODE_*
    # Supports all normalized ISO 3166-1 alpha-3 codes:
    # - 3-letter codes: ARG, BOL, CHL, COL, CRI, CUB, DOM, ECU, ESP, GTM, HND,
    #                   MEX, NIC, PAN, PER, PRY, SLV, URY, VEN, USA
    # - Regional codes: ARG-CBA, ARG-CHU, ARG-SDE, ESP-CAN, ESP-SEV
    match = re.match(r"\d{4}-\d{2}-\d{2}_([A-Z]{3}(?:-[A-Z]{3})?)", Path(filename).name)
    if match:
        return match.group(1)

    return None


def audio_full_path(filename: str) -> Path:
    return (MP3_FULL_DIR / filename).resolve()


def audio_split_path(filename: str) -> Path:
    return (MP3_SPLIT_DIR / filename).resolve()


def transcript_path(filename: str) -> Path:
    return (TRANSCRIPTS_DIR / filename).resolve()


def ensure_within(base: Path, target: Path) -> None:
    """Raise ValueError if target is outside base directory."""
    base_resolved = base.resolve()
    target_resolved = target.resolve()
    if (
        base_resolved not in target_resolved.parents
        and target_resolved != base_resolved
    ):
        raise ValueError("Attempted path traversal outside of media root")


def safe_audio_full_path(filename: str) -> Optional[Path]:
    """
    Find audio file in mp3-full, with intelligent country subfolder detection.

    Tries:
    1. Direct path if filename contains '/' (e.g., "VEN/2022-01-18_VEN_RCR.mp3")
    2. With country code subfolder (e.g., "2022-01-18_VEN_RCR.mp3" -> "VEN/...")
    3. Without subfolder (fallback for flat structure)
    """
    try:
        # Try 1: Direct path
        candidate = audio_full_path(filename)
        ensure_within(MP3_FULL_DIR, candidate)
        if candidate.exists():
            return candidate

        # Try 2: With country subfolder
        country_code = extract_country_code(filename)
        if country_code:
            # Get just the filename without any existing path
            base_filename = Path(filename).name
            candidate_with_country = MP3_FULL_DIR / country_code / base_filename
            ensure_within(MP3_FULL_DIR, candidate_with_country)
            if candidate_with_country.exists():
                return candidate_with_country
    except ValueError:
        return None
    return None


def safe_audio_split_path(filename: str) -> Optional[Path]:
    """
    Find audio file in mp3-split, with intelligent country subfolder detection.
    Same logic as safe_audio_full_path but for split files.
    """
    try:
        # Try 1: Direct path
        candidate = audio_split_path(filename)
        ensure_within(MP3_SPLIT_DIR, candidate)
        if candidate.exists():
            return candidate

        # Try 2: With country subfolder
        country_code = extract_country_code(filename)
        if country_code:
            base_filename = Path(filename).name
            candidate_with_country = MP3_SPLIT_DIR / country_code / base_filename
            ensure_within(MP3_SPLIT_DIR, candidate_with_country)
            if candidate_with_country.exists():
                return candidate_with_country
    except ValueError:
        return None
    return None


def safe_transcript_path(filename: str) -> Optional[Path]:
    """
    Find transcript file in transcripts, with intelligent country subfolder detection.
    """
    try:
        # Try 1: Direct path
        candidate = transcript_path(filename)
        ensure_within(TRANSCRIPTS_DIR, candidate)
        if candidate.exists():
            return candidate

        # Try 2: With country subfolder
        country_code = extract_country_code(filename)
        if country_code:
            base_filename = Path(filename).name
            candidate_with_country = TRANSCRIPTS_DIR / country_code / base_filename
            ensure_within(TRANSCRIPTS_DIR, candidate_with_country)
            if candidate_with_country.exists():
                return candidate_with_country
    except ValueError:
        return None
    return None
