"""Audio snippet generation with split-file optimization."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Optional, Tuple

from pydub import AudioSegment

from .media_store import MP3_TEMP_DIR, safe_audio_full_path, safe_audio_split_path

CACHE_PREFIX = "snippet"
CLEANUP_THRESHOLD_SECONDS = 30 * 60  # 30 Minuten

# Split-file mapping from old webapp: 4-minute chunks with 30s overlap
SPLIT_TIMES = {
    "_01": (0.0, 240.0),
    "_02": (210.0, 450.0),
    "_03": (420.0, 660.0),
    "_04": (630.0, 870.0),
    "_05": (840.0, 1080.0),
    "_06": (1050.0, 1290.0),
    "_07": (1260.0, 1500.0),
    "_08": (1470.0, 1710.0),
    "_09": (1680.0, 1920.0),
    "_10": (1890.0, 2130.0),
    "_11": (2100.0, 2340.0),
    "_12": (2310.0, 2550.0),
    "_13": (2520.0, 2760.0),
    "_14": (2730.0, 2970.0),
    "_15": (2940.0, 3180.0),
    "_16": (3150.0, 3390.0),
    "_17": (3360.0, 3600.0),
    "_18": (3570.0, 3810.0),
    "_19": (3780.0, 4020.0),
    "_20": (3990.0, 4230.0),
    "_21": (4200.0, 4440.0),
    "_22": (4410.0, 4650.0),
    "_23": (4620.0, 4860.0),
    "_24": (4830.0, 5070.0),
    "_25": (5040.0, 5280.0),
    "_26": (5250.0, 5490.0),
    "_27": (5460.0, 5700.0),
    "_28": (5670.0, 5910.0),
    "_29": (5880.0, 6120.0),
}


def find_split_file(
    filename: str, start: float, end: float
) -> Optional[Tuple[Path, str]]:
    """
    Find the appropriate split file for the given time range.

    Returns:
        Tuple of (split_file_path, split_suffix) or None if no suitable split found.
        Example: (Path("mp3-split/VEN/2022-01-18_VEN_RCR_05.mp3"), "_05")
    """
    # Find the split segment that contains the entire time range
    for suffix, (split_start, split_end) in SPLIT_TIMES.items():
        if split_start <= start and end <= split_end:
            # Build split filename
            stem = Path(
                filename
            ).stem  # "2022-01-18_VEN_RCR" from "2022-01-18_VEN_RCR.mp3"
            split_filename = f"{stem}{suffix}.mp3"

            # Try to find the split file (with country subfolder support)
            split_path = safe_audio_split_path(split_filename)
            if split_path and split_path.exists():
                return (split_path, suffix)

    return None


def _cache_filename(
    filename: str,
    start: float,
    end: float,
    token_id: str | None = None,
    snippet_type: str | None = None,
) -> str:
    """
    Generate cache filename with token_id-based naming.

    Format:
    - Palabra/Resultado (type='pal'): corapan_{token_id}.mp3
    - Contexto (type='ctx'): corapan_{token_id}_contexto.mp3
    """
    if token_id and snippet_type:
        # Build filename based on snippet type (use explicit _pal/_ctx suffixes)
        if snippet_type == "ctx":
            # Contexto: corapan_{token_id}_ctx.mp3
            return f"corapan_{token_id}_ctx.mp3"
        elif (
            snippet_type == "pal"
            or snippet_type == "palabra"
            or snippet_type == "result"
        ):
            # Palabra/Resultado: corapan_{token_id}_pal.mp3
            return f"corapan_{token_id}_pal.mp3"
        else:
            # Unknown snippet type: include it plainly
            safe_type = "".join(
                ch for ch in snippet_type if ch.isalnum() or ch in ("_", "-")
            ).lower()
            return f"corapan_{token_id}_{safe_type}.mp3"
    else:
        # Fallback: Hash-basiert für Abwärtskompatibilität
        digest = hashlib.sha256(f"{filename}:{start}:{end}".encode()).hexdigest()
        return f"{CACHE_PREFIX}_{digest}.mp3"


def cleanup_old_snippets() -> int:
    """Delete audio snippets older than CLEANUP_THRESHOLD_SECONDS. Returns count of deleted files."""
    if not MP3_TEMP_DIR.exists():
        return 0

    current_time = time.time()
    deleted_count = 0

    for snippet_file in MP3_TEMP_DIR.glob("*.mp3"):
        try:
            file_age = current_time - snippet_file.stat().st_mtime
            if file_age > CLEANUP_THRESHOLD_SECONDS:
                snippet_file.unlink()
                deleted_count += 1
        except (OSError, FileNotFoundError):
            # File might have been deleted by another process
            pass

    return deleted_count


def build_snippet(
    filename: str,
    start: float,
    end: float,
    token_id: str | None = None,
    snippet_type: str | None = None,
) -> Path:
    """
    Create (or reuse) an audio snippet for the given window.

    Performance optimization: Tries to use pre-split files first (4-minute chunks),
    falls back to full audio file if no suitable split is found.

    This is ~6-10x faster than loading the full audio file!
    """
    if end <= start:
        raise ValueError("End time must be greater than start time")

    MP3_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Cleanup alte Snippets bei jedem 10. Aufruf (probabilistisch)
    import random

    if random.random() < 0.1:
        cleanup_old_snippets()

    cache_name = _cache_filename(filename, start, end, token_id, snippet_type)
    target_path = (MP3_TEMP_DIR / cache_name).resolve()

    # Return cached snippet if it exists
    if target_path.exists():
        return target_path

    # Strategy 1: Try to use split file (FAST ⚡)
    split_result = find_split_file(filename, start, end)

    if split_result is not None:
        split_path, split_suffix = split_result
        split_start, _ = SPLIT_TIMES[split_suffix]

        # Load only the ~4MB split file instead of ~30MB full file
        audio = AudioSegment.from_file(split_path)

        # Calculate local offsets within the split file
        local_start_ms = int((start - split_start) * 1000)
        local_end_ms = int((end - split_start) * 1000)

        snippet = audio[local_start_ms:local_end_ms]
    else:
        # Strategy 2: Fallback to full file (slower but always works)
        source = safe_audio_full_path(filename)
        if source is None:
            raise FileNotFoundError(f"Audio source not found for {filename}")

        audio = AudioSegment.from_file(source)
        snippet = audio[int(start * 1000) : int(end * 1000)]

    if len(snippet) == 0:
        raise ValueError("Snippet window produced empty audio")

    snippet.export(target_path, format="mp3")
    return target_path
