"""Media storage helpers with intelligent country subfolder detection."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from flask import current_app, has_app_context

from ..config import BaseConfig


def _config_path(key: str, fallback_attr: str) -> Path:
    if has_app_context():
        return Path(current_app.config[key])
    return Path(getattr(BaseConfig, fallback_attr))


def media_root() -> Path:
    return _config_path("MEDIA_ROOT", "MEDIA_ROOT")


def audio_full_dir() -> Path:
    return _config_path("AUDIO_FULL_DIR", "AUDIO_FULL_DIR")


def audio_split_dir() -> Path:
    return _config_path("AUDIO_SPLIT_DIR", "AUDIO_SPLIT_DIR")


def audio_temp_dir() -> Path:
    return _config_path("AUDIO_TEMP_DIR", "AUDIO_TEMP_DIR")


def transcripts_dir() -> Path:
    return _config_path("TRANSCRIPTS_DIR", "TRANSCRIPTS_DIR")


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
    return (audio_full_dir() / filename).resolve()


def audio_split_path(filename: str) -> Path:
    return (audio_split_dir() / filename).resolve()


def transcript_path(filename: str) -> Path:
    return (transcripts_dir() / filename).resolve()


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
        base_dir = audio_full_dir()
        ensure_within(base_dir, candidate)
        if candidate.exists():
            return candidate

        # Try 2: With country subfolder
        country_code = extract_country_code(filename)
        if country_code:
            # Get just the filename without any existing path
            base_filename = Path(filename).name
            candidate_with_country = base_dir / country_code / base_filename
            ensure_within(base_dir, candidate_with_country)
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
        base_dir = audio_split_dir()
        ensure_within(base_dir, candidate)
        if candidate.exists():
            return candidate

        # Try 2: With country subfolder
        country_code = extract_country_code(filename)
        if country_code:
            base_filename = Path(filename).name
            candidate_with_country = base_dir / country_code / base_filename
            ensure_within(base_dir, candidate_with_country)
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
        base_dir = transcripts_dir()
        ensure_within(base_dir, candidate)
        if candidate.exists():
            return candidate

        # Try 2: With country subfolder
        country_code = extract_country_code(filename)
        if country_code:
            base_filename = Path(filename).name
            candidate_with_country = base_dir / country_code / base_filename
            ensure_within(base_dir, candidate_with_country)
            if candidate_with_country.exists():
                return candidate_with_country
    except ValueError:
        return None
    return None
