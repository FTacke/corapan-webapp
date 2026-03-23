#!/usr/bin/env python3
"""
mp3_prepare_and_split.py - Consolidated MP3 Preprocessing Pipeline

WORKFLOW OVERVIEW
=================
This script provides a standardized workflow for corpus MP3 preprocessing:

1. CBR Conversion (Constant Bitrate)
   - Analyzes each MP3 file for VBR (Variable Bitrate) encoding
   - Converts VBR files to CBR using the nearest standard bitrate
   - Replaces the original file in-place

2. Loudness Normalization (LUFS)
   - Applies 2-pass EBU R128 loudness normalization via ffmpeg's loudnorm filter
   - Default target: -18 LUFS (I), 11 LU (LRA), -1.0 dBTP
   - Ensures consistent playback volume across all corpus recordings

3. Splitting into 4-minute Chunks
   - Splits normalized files into 4-minute segments with 30-second overlap
   - Preserves directory structure from source to target
   - Pads final chunk with silence if needed

FOLDER STRUCTURE
================
- Source (mp3-full):      ../../media/mp3-full
- Target (mp3-split):     ../../media/mp3-split

The target directory mirrors the source directory structure.
Chunk filenames follow the pattern: BASENAME_01.mp3, BASENAME_02.mp3, etc.

DEPENDENCIES
============
Python packages (see requirements-corpus.txt):
- pydub: Audio manipulation
- eyed3: MP3 metadata reading

System requirements:
- ffmpeg: Must be installed and available in system PATH
  (used by pydub for encoding and loudnorm filter for normalization)

NOTE ON RE-ENCODING
===================
Both CBR conversion and loudness normalization involve re-encoding, which is
inherently lossy. However, for speech/radio corpus material, the combination
is acceptable in practice and significantly improves usability:
- Consistent bitrate enables precise seeking in audio players
- Uniform loudness levels improve transcription workflow

EXAMPLE USAGE
=============
# Process all files with defaults (normalize + split):
python mp3_prepare_and_split.py

# Dry-run to see what would be processed:
python mp3_prepare_and_split.py --dry-run

# Skip loudness normalization (CBR + split only):
python mp3_prepare_and_split.py --skip-normalize

# Custom loudness target:
python mp3_prepare_and_split.py --loudness-i -16.0 --loudness-lra 9.0

# Custom chunk duration and overlap:
python mp3_prepare_and_split.py --chunk-duration-seconds 300 --overlap-seconds 15

# Custom source and target directories:
python mp3_prepare_and_split.py --source ./my-source --target ./my-splits
"""

import argparse
import glob
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple

try:
    from pydub import AudioSegment
except ImportError:
    print("ERROR: pydub is required. Install with: pip install pydub")
    sys.exit(1)

try:
    import eyed3
except ImportError:
    print("ERROR: eyed3 is required. Install with: pip install eyed3")
    sys.exit(1)

# Suppress eyed3 warnings about missing tags
eyed3.log.setLevel(logging.ERROR)

# =============================================================================
# Constants (Defaults)
# =============================================================================

# Get the directory where this script is located
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Default paths relative to the script location
DEFAULT_SOURCE_DIR = os.path.normpath(os.path.join(_SCRIPT_DIR, "../../media/mp3-full"))
DEFAULT_TARGET_DIR = os.path.normpath(os.path.join(_SCRIPT_DIR, "../../media/mp3-split"))

DEFAULT_CHUNK_DURATION_MS = 4 * 60 * 1000  # 4 minutes in milliseconds
DEFAULT_OVERLAP_MS = 30 * 1000  # 30 seconds in milliseconds

# Loudness normalization defaults (EBU R128 speech-friendly)
DEFAULT_LOUDNESS_I = -18.0  # Integrated loudness target (LUFS)
DEFAULT_LOUDNESS_LRA = 11.0  # Loudness Range (LU)
DEFAULT_LOUDNESS_TP = -1.0  # True Peak (dBTP)

# Common CBR bitrates for selection
COMMON_BITRATES = [32, 64, 96, 128, 160, 192, 224, 256, 320]

# =============================================================================
# Logging Setup
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# =============================================================================
# Progress Display
# =============================================================================

class ProgressTracker:
    """
    Tracks and displays progress for batch processing.
    Shows current file count, percentage, and current filename.
    """
    
    def __init__(self, total: int):
        self.total = total
        self.current = 0
        self.processed = 0
        self.skipped = 0
        self.errors = 0
    
    def _get_progress_bar(self, width: int = 30) -> str:
        """Generate a text-based progress bar."""
        if self.total == 0:
            return "[" + "=" * width + "]"
        filled = int(width * self.current / self.total)
        bar = "=" * filled + "-" * (width - filled)
        return f"[{bar}]"
    
    def _get_percentage(self) -> float:
        """Calculate current percentage."""
        if self.total == 0:
            return 100.0
        return (self.current / self.total) * 100
    
    def update(self, file_name: str, step: str = "") -> None:
        """
        Update and display progress for current file.
        
        Args:
            file_name: Name of the file being processed
            step: Current processing step (e.g., 'CBR', 'Normalize', 'Split')
        """
        self.current += 1
        pct = self._get_percentage()
        bar = self._get_progress_bar()
        step_info = f" [{step}]" if step else ""
        
        # Clear line and print progress
        print(f"\r{bar} {self.current}/{self.total} ({pct:5.1f}%){step_info} {file_name[:50]:<50}", 
              end="", flush=True)
    
    def update_step(self, step: str) -> None:
        """
        Update only the step indicator without incrementing count.
        
        Args:
            step: Current processing step
        """
        pct = self._get_percentage()
        bar = self._get_progress_bar()
        
        print(f"\r{bar} {self.current}/{self.total} ({pct:5.1f}%) [{step}]", 
              end="", flush=True)
    
    def finish_file(self, status: str = "ok") -> None:
        """Mark current file as complete with status."""
        if status == "ok":
            self.processed += 1
        elif status == "skip":
            self.skipped += 1
        elif status == "error":
            self.errors += 1
    
    def print_newline(self) -> None:
        """Print newline to move past progress bar."""
        print()  # Move to next line
    
    def print_summary(self) -> None:
        """Print final summary."""
        # Clear any remaining progress bar content with a carriage return and spaces
        print("\r" + " " * 100 + "\r", end="", flush=True)
        logger.info("=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total files:     {self.total}")
        logger.info(f"Processed:       {self.processed}")
        logger.info(f"Skipped:         {self.skipped}")
        logger.info(f"Errors:          {self.errors}")
        logger.info("Done!")


def count_mp3_files(source_dir: str) -> int:
    """
    Count all MP3 files in source directory recursively.
    
    Args:
        source_dir: Path to source directory
        
    Returns:
        Total number of MP3 files
    """
    count = 0
    for root, dirs, files in os.walk(source_dir):
        for file_name in files:
            if file_name.lower().endswith('.mp3'):
                count += 1
    return count


def collect_mp3_files(source_dir: str) -> list:
    """
    Collect all MP3 files with their paths and relative paths.
    
    Args:
        source_dir: Path to source directory
        
    Returns:
        List of tuples (file_path, relative_path, file_name)
    """
    files_list = []
    for root, dirs, files in os.walk(source_dir):
        relative_path = os.path.relpath(root, source_dir)
        if relative_path == '.':
            relative_path = ''
        
        for file_name in files:
            if file_name.lower().endswith('.mp3'):
                file_path = os.path.join(root, file_name)
                files_list.append((file_path, relative_path, file_name))
    
    return files_list

# =============================================================================
# Audio Properties Functions
# =============================================================================

def get_audio_properties(file_path: str) -> Tuple[int, str, bool]:
    """
    Read audio properties from an MP3 file using eyed3.
    
    Returns:
        Tuple of (bitrate_kbps, channel_mode, is_vbr)
        - bitrate_kbps: Detected bitrate in kbps (default 128 if unknown)
        - channel_mode: "mono" or "stereo"
        - is_vbr: True if Variable Bitrate, False if Constant Bitrate
    """
    try:
        audiofile = eyed3.load(file_path)
        if audiofile is None or audiofile.info is None:
            logger.warning(f"Could not read metadata from {file_path}, using defaults")
            return 128, "stereo", True
        
        # Extract bitrate (tuple: (is_vbr, bitrate_kbps))
        if audiofile.info.bit_rate:
            is_vbr_flag, bitrate = audiofile.info.bit_rate
            bitrate_kbps = int(bitrate) if bitrate else 128
            is_vbr = bool(is_vbr_flag)
        else:
            bitrate_kbps = 128
            is_vbr = True
            logger.warning(f"Could not determine bitrate for {file_path}, assuming VBR")
        
        # Extract channel mode
        mode = audiofile.info.mode if hasattr(audiofile.info, 'mode') else "stereo"
        if mode and isinstance(mode, str):
            channel_mode = "mono" if mode.lower() == "mono" else "stereo"
        else:
            channel_mode = "stereo"
        
        return bitrate_kbps, channel_mode, is_vbr
    
    except Exception as e:
        logger.warning(f"Error reading properties from {file_path}: {e}")
        return 128, "stereo", True


def get_audio_properties_from_segment(audio: AudioSegment) -> Tuple[int, str]:
    """
    Extract properties from a pydub AudioSegment.
    
    Returns:
        Tuple of (channels, channel_mode)
        - channels: Number of channels (1 or 2)
        - channel_mode: "mono" or "stereo"
    """
    channels = audio.channels
    channel_mode = "mono" if channels == 1 else "stereo"
    return channels, channel_mode


def choose_target_bitrate(dynamic_bitrate: int) -> int:
    """
    Select the highest standard bitrate that is <= the dynamic bitrate.
    
    Args:
        dynamic_bitrate: The detected/dynamic bitrate in kbps
        
    Returns:
        The selected target bitrate in kbps
    """
    target = COMMON_BITRATES[0]
    for br in COMMON_BITRATES:
        if dynamic_bitrate >= br:
            target = br
        else:
            break
    return target

# =============================================================================
# CBR Conversion Functions
# =============================================================================

def atomic_replace(temp_path: str, target_path: str) -> None:
    """
    Atomically replace target_path with temp_path.
    Works cross-platform (Windows requires removing target first).
    """
    try:
        os.replace(temp_path, target_path)
    except OSError:
        # On some Windows configurations, os.replace fails if target exists
        if os.path.exists(target_path):
            os.remove(target_path)
        shutil.move(temp_path, target_path)


def convert_to_cbr(
    file_path: str,
    dry_run: bool = False
) -> Tuple[bool, int, str]:
    """
    Check if file is VBR and convert to CBR if needed.
    
    Args:
        file_path: Path to the MP3 file
        dry_run: If True, only log what would be done
        
    Returns:
        Tuple of (was_converted, bitrate_kbps, channel_mode)
    """
    bitrate_kbps, channel_mode, is_vbr = get_audio_properties(file_path)
    
    if not is_vbr:
        logger.debug(f"File already CBR ({bitrate_kbps} kbps): {file_path}")
        return False, bitrate_kbps, channel_mode
    
    target_bitrate = choose_target_bitrate(bitrate_kbps)
    
    if dry_run:
        logger.debug(f"[DRY-RUN] Would convert VBR->CBR: {file_path} "
                   f"({bitrate_kbps} kbps -> {target_bitrate} kbps CBR)")
        return True, target_bitrate, channel_mode
    
    logger.debug(f"Converting VBR->CBR: {file_path} "
               f"({bitrate_kbps} kbps -> {target_bitrate} kbps)")
    
    try:
        # Load audio
        audio = AudioSegment.from_mp3(file_path)
        
        # Create temp file for atomic replacement
        fd, temp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        
        try:
            # Export with CBR
            ac_param = "1" if channel_mode == "mono" else "2"
            audio.export(
                temp_path,
                format="mp3",
                bitrate=f"{target_bitrate}k",
                parameters=["-ac", ac_param]
            )
            
            # Atomic replace
            atomic_replace(temp_path, file_path)
            logger.debug(f"CBR conversion complete: {file_path}")
            
        except Exception:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
        
        return True, target_bitrate, channel_mode
        
    except Exception as e:
        logger.error(f"CBR conversion failed for {file_path}: {e}")
        raise

# =============================================================================
# Loudness Normalization Functions
# =============================================================================

def check_ffmpeg_available() -> bool:
    """Check if ffmpeg is available in the system PATH."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def parse_loudnorm_output(stderr: str) -> Optional[dict]:
    """
    Parse the JSON output from ffmpeg's loudnorm filter (first pass).
    
    Returns:
        Dictionary with measured values or None if parsing fails
    """
    # The loudnorm filter outputs JSON in stderr, look for it
    # It appears after "Parsed_loudnorm" line
    json_match = re.search(r'\{[^{}]*"input_i"[^{}]*\}', stderr, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Alternative pattern - sometimes the JSON is on multiple lines
    lines = stderr.split('\n')
    json_lines = []
    in_json = False
    for line in lines:
        if '{' in line and '"input_' in line:
            in_json = True
        if in_json:
            json_lines.append(line)
            if '}' in line:
                break
    
    if json_lines:
        try:
            json_str = ''.join(json_lines)
            # Clean up the JSON string
            json_str = re.sub(r'^\[.*?\]', '', json_str)  # Remove any prefix
            json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    return None


def normalize_loudness(
    input_path: str,
    output_path: str,
    *,
    target_i: float = DEFAULT_LOUDNESS_I,
    target_lra: float = DEFAULT_LOUDNESS_LRA,
    target_tp: float = DEFAULT_LOUDNESS_TP,
    dry_run: bool = False
) -> bool:
    """
    Apply 2-pass EBU R128 loudness normalization using ffmpeg's loudnorm filter.
    
    Args:
        input_path: Path to input MP3 file
        output_path: Path to output MP3 file
        target_i: Target integrated loudness (LUFS)
        target_lra: Target loudness range (LU)
        target_tp: Target true peak (dBTP)
        dry_run: If True, only log what would be done
        
    Returns:
        True if normalization was successful
    """
    if dry_run:
        logger.debug(f"[DRY-RUN] Would normalize loudness: {input_path} "
                   f"(I={target_i}, LRA={target_lra}, TP={target_tp})")
        return True
    
    logger.debug(f"Normalizing loudness: {input_path}")
    
    # Pass 1: Measure loudness
    pass1_filter = (
        f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:"
        f"print_format=json"
    )
    
    pass1_cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-af", pass1_filter,
        "-f", "null", "-"
    ]
    
    try:
        result = subprocess.run(
            pass1_cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Loudness measurement failed for {input_path}")
            logger.error(f"ffmpeg stderr: {result.stderr}")
            return False
        
        # Parse measured values
        measured = parse_loudnorm_output(result.stderr)
        
        if not measured:
            logger.warning(f"Could not parse loudnorm output for {input_path}, "
                          "using single-pass normalization")
            # Fallback to single-pass
            pass2_filter = (
                f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}"
            )
        else:
            # Build pass 2 filter with measured values
            pass2_filter = (
                f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:"
                f"measured_I={measured.get('input_i', target_i)}:"
                f"measured_TP={measured.get('input_tp', target_tp)}:"
                f"measured_LRA={measured.get('input_lra', target_lra)}:"
                f"measured_thresh={measured.get('input_thresh', -24.0)}:"
                f"offset={measured.get('target_offset', 0.0)}:"
                f"linear=true:print_format=summary"
            )
            logger.debug(f"Measured values: I={measured.get('input_i')}, "
                        f"TP={measured.get('input_tp')}, LRA={measured.get('input_lra')}")
        
        # Pass 2: Apply normalization
        fd, temp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        
        # Get bitrate from input for consistent output
        bitrate_kbps, channel_mode, _ = get_audio_properties(input_path)
        ac_param = "1" if channel_mode == "mono" else "2"
        
        pass2_cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-af", pass2_filter,
            "-ac", ac_param,
            "-b:a", f"{bitrate_kbps}k",
            temp_path
        ]
        
        result = subprocess.run(
            pass2_cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Loudness normalization failed for {input_path}")
            logger.error(f"ffmpeg stderr: {result.stderr}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
        
        # Atomic replace
        atomic_replace(temp_path, output_path)
        logger.debug(f"Loudness normalization complete: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Loudness normalization error for {input_path}: {e}")
        return False

# =============================================================================
# Split Functions
# =============================================================================

def get_existing_chunks(target_dir: str, basename: str) -> list:
    """
    Find existing chunk files matching the pattern BASENAME_XX.mp3
    
    Returns:
        List of existing chunk file paths
    """
    pattern = os.path.join(target_dir, f"{basename}_*.mp3")
    return glob.glob(pattern)


def split_audio(
    file_path: str,
    relative_path: str,
    file_name: str,
    target_dir: str,
    chunk_duration_ms: int,
    overlap_ms: int,
    bitrate_kbps: int,
    dry_run: bool = False
) -> bool:
    """
    Split an MP3 file into chunks with overlap.
    
    Args:
        file_path: Full path to the source file
        relative_path: Relative path from source dir (for target structure)
        file_name: Original filename
        target_dir: Base target directory
        chunk_duration_ms: Duration of each chunk in milliseconds
        overlap_ms: Overlap between chunks in milliseconds
        bitrate_kbps: Target bitrate for export
        dry_run: If True, only log what would be done
        
    Returns:
        True if splitting was successful
    """
    basename = os.path.splitext(file_name)[0]
    
    # Create target subdirectory
    target_subdir = os.path.join(target_dir, relative_path) if relative_path else target_dir
    
    if dry_run:
        logger.debug(f"[DRY-RUN] Would split: {file_path} -> {target_subdir}/{basename}_XX.mp3")
        return True
    
    try:
        os.makedirs(target_subdir, exist_ok=True)
        
        # Load audio
        audio = AudioSegment.from_mp3(file_path)
        _, channel_mode = get_audio_properties_from_segment(audio)
        
        start_time = 0
        part_num = 1
        
        while start_time < len(audio):
            end_time = min(start_time + chunk_duration_ms, len(audio))
            chunk = audio[start_time:end_time]
            
            # Pad last chunk with silence if needed
            if end_time == len(audio) and len(chunk) < chunk_duration_ms:
                silence_duration = chunk_duration_ms - len(chunk)
                silence = AudioSegment.silent(duration=silence_duration)
                chunk += silence
                logger.debug(f"Padded last chunk with {silence_duration}ms silence")
            
            new_file_name = f"{basename}_{str(part_num).zfill(2)}.mp3"
            new_file_path = os.path.join(target_subdir, new_file_name)
            
            # Export chunk
            ac_param = "1" if channel_mode == "mono" else "2"
            chunk.export(
                new_file_path,
                format="mp3",
                bitrate=f"{bitrate_kbps}k",
                parameters=["-ac", ac_param]
            )
            logger.debug(f"Exported: {new_file_path} ({bitrate_kbps} kbps, {channel_mode})")
            
            start_time += chunk_duration_ms - overlap_ms
            part_num += 1
        
        return True
        
    except Exception as e:
        logger.error(f"Splitting failed for {file_path}: {e}")
        return False

# =============================================================================
# Overwrite Check Functions
# =============================================================================

class OverwriteHandler:
    """
    Handles user interaction for overwrite decisions.
    Caches 'all' and 'skip-all' decisions for the session.
    """
    
    def __init__(self):
        self.global_decision: Optional[str] = None  # 'a' = all, 's' = skip-all
    
    def should_process(
        self,
        file_path: str,
        relative_path: str,
        file_name: str,
        target_dir: str
    ) -> bool:
        """
        Check if file should be processed, prompting user if chunks exist.
        
        Returns:
            True if file should be processed, False if skipped
        """
        basename = os.path.splitext(file_name)[0]
        target_subdir = os.path.join(target_dir, relative_path) if relative_path else target_dir
        
        existing_chunks = get_existing_chunks(target_subdir, basename)
        
        if not existing_chunks:
            # No existing chunks, process without asking
            return True
        
        # Check cached decision
        if self.global_decision == 'a':
            # Delete existing chunks and process
            self._delete_chunks(existing_chunks)
            return True
        elif self.global_decision == 's':
            logger.debug(f"Skipping (global skip): {file_path}")
            return False
        
        # Prompt user
        display_path = os.path.join(relative_path, file_name) if relative_path else file_name
        print(f"\nSplits for '{display_path}' already exist ({len(existing_chunks)} chunks).")
        print("Overwrite? [y]es / [n]o / [a]ll / [s]kip-all: ", end="", flush=True)
        
        while True:
            try:
                response = input().strip().lower()
            except EOFError:
                response = 'n'
            
            if response in ('y', 'yes'):
                self._delete_chunks(existing_chunks)
                return True
            elif response in ('n', 'no'):
                logger.debug(f"Skipping: {file_path}")
                return False
            elif response in ('a', 'all'):
                self.global_decision = 'a'
                self._delete_chunks(existing_chunks)
                return True
            elif response in ('s', 'skip-all', 'skip'):
                self.global_decision = 's'
                logger.debug(f"Skipping (skip-all): {file_path}")
                return False
            else:
                print("Please enter y/n/a/s: ", end="", flush=True)
    
    def _delete_chunks(self, chunks: list) -> None:
        """Delete existing chunk files."""
        for chunk_path in chunks:
            try:
                os.remove(chunk_path)
                logger.debug(f"Deleted existing chunk: {chunk_path}")
            except OSError as e:
                logger.warning(f"Could not delete {chunk_path}: {e}")

# =============================================================================
# Main Processing Function
# =============================================================================

def process_mp3_files(
    source_dir: str,
    target_dir: str,
    chunk_duration_ms: int,
    overlap_ms: int,
    loudness_i: float,
    loudness_lra: float,
    loudness_tp: float,
    skip_normalize: bool,
    dry_run: bool
) -> None:
    """
    Main processing function that orchestrates the entire pipeline.
    """
    source_dir = os.path.abspath(source_dir)
    target_dir = os.path.abspath(target_dir)
    
    if not os.path.exists(source_dir):
        logger.error(f"Source directory does not exist: {source_dir}")
        return
    
    # Check ffmpeg availability
    if not check_ffmpeg_available():
        logger.error("ffmpeg is not available in PATH. Please install ffmpeg.")
        return
    
    # Collect all MP3 files first for progress tracking
    logger.info("Scanning for MP3 files...")
    mp3_files = collect_mp3_files(source_dir)
    total_files = len(mp3_files)
    
    if total_files == 0:
        logger.warning("No MP3 files found in source directory.")
        return
    
    logger.info("=" * 60)
    logger.info("MP3 Prepare and Split Pipeline")
    logger.info("=" * 60)
    logger.info(f"Source:         {source_dir}")
    logger.info(f"Target:         {target_dir}")
    logger.info(f"Total files:    {total_files}")
    logger.info(f"Chunk duration: {chunk_duration_ms / 1000}s")
    logger.info(f"Overlap:        {overlap_ms / 1000}s")
    logger.info(f"Loudness:       I={loudness_i}, LRA={loudness_lra}, TP={loudness_tp}")
    logger.info(f"Skip normalize: {skip_normalize}")
    logger.info(f"Dry run:        {dry_run}")
    logger.info("=" * 60)
    
    if dry_run:
        logger.info("[DRY-RUN MODE] No files will be modified.")
    
    print()  # Empty line before progress bar
    
    overwrite_handler = OverwriteHandler()
    progress = ProgressTracker(total_files)
    
    # Process each file
    for file_path, relative_path, file_name in mp3_files:
        # Update progress display
        progress.update(file_name, "Check")
        
        # Check if we should process this file (overwrite check)
        if not dry_run:
            # Need to print newline before prompting user
            if overwrite_handler.global_decision is None:
                # Check if chunks exist before potentially prompting
                basename = os.path.splitext(file_name)[0]
                target_subdir = os.path.join(target_dir, relative_path) if relative_path else target_dir
                existing_chunks = get_existing_chunks(target_subdir, basename)
                if existing_chunks:
                    progress.print_newline()
            
            if not overwrite_handler.should_process(
                file_path, relative_path, file_name, target_dir
            ):
                progress.finish_file("skip")
                continue
        
        try:
            # Step 1: CBR conversion
            progress.update_step("CBR")
            was_converted, bitrate_kbps, channel_mode = convert_to_cbr(
                file_path, dry_run
            )
            
            # Step 2: Loudness normalization
            if not skip_normalize:
                progress.update_step("Normalize")
                success = normalize_loudness(
                    file_path, file_path,
                    target_i=loudness_i,
                    target_lra=loudness_lra,
                    target_tp=loudness_tp,
                    dry_run=dry_run
                )
                if not success and not dry_run:
                    logger.error(f"Skipping split due to normalization failure: {file_path}")
                    progress.finish_file("error")
                    continue
            
            # Step 3: Split
            progress.update_step("Split")
            success = split_audio(
                file_path, relative_path, file_name, target_dir,
                chunk_duration_ms, overlap_ms, bitrate_kbps, dry_run
            )
            
            if success:
                progress.finish_file("ok")
            else:
                progress.finish_file("error")
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            progress.finish_file("error")
    
    # Print final summary
    progress.print_summary()

# =============================================================================
# CLI Argument Parser
# =============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="MP3 Preprocessing Pipeline: CBR conversion, loudness normalization, and splitting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Process all files with defaults
  %(prog)s --dry-run                # Show what would be done
  %(prog)s --skip-normalize         # Skip loudness normalization
  %(prog)s --loudness-i -16.0       # Custom loudness target
        """
    )
    
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE_DIR,
        help=f"Source directory (default: {DEFAULT_SOURCE_DIR})"
    )
    
    parser.add_argument(
        "--target",
        default=DEFAULT_TARGET_DIR,
        help=f"Target directory for splits (default: {DEFAULT_TARGET_DIR})"
    )
    
    parser.add_argument(
        "--chunk-duration-seconds",
        type=int,
        default=240,
        help="Chunk duration in seconds (default: 240 = 4 minutes)"
    )
    
    parser.add_argument(
        "--overlap-seconds",
        type=int,
        default=30,
        help="Overlap between chunks in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--loudness-i",
        type=float,
        default=DEFAULT_LOUDNESS_I,
        help=f"Target integrated loudness in LUFS (default: {DEFAULT_LOUDNESS_I})"
    )
    
    parser.add_argument(
        "--loudness-lra",
        type=float,
        default=DEFAULT_LOUDNESS_LRA,
        help=f"Target loudness range in LU (default: {DEFAULT_LOUDNESS_LRA})"
    )
    
    parser.add_argument(
        "--loudness-tp",
        type=float,
        default=DEFAULT_LOUDNESS_TP,
        help=f"Target true peak in dBTP (default: {DEFAULT_LOUDNESS_TP})"
    )
    
    parser.add_argument(
        "--skip-normalize",
        action="store_true",
        help="Skip loudness normalization (only CBR conversion + split)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without modifying any files"
    )
    
    return parser.parse_args()

# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    args = parse_args()
    
    # Convert seconds to milliseconds
    chunk_duration_ms = args.chunk_duration_seconds * 1000
    overlap_ms = args.overlap_seconds * 1000
    
    process_mp3_files(
        source_dir=args.source,
        target_dir=args.target,
        chunk_duration_ms=chunk_duration_ms,
        overlap_ms=overlap_ms,
        loudness_i=args.loudness_i,
        loudness_lra=args.loudness_lra,
        loudness_tp=args.loudness_tp,
        skip_normalize=args.skip_normalize,
        dry_run=args.dry_run
    )
