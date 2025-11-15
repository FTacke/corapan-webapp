#!/usr/bin/env python3
"""
BlackLab Index Creation: Export JSON v2 corpus to TSV/WPL + docmeta.jsonl.

Usage:
    python -m src.scripts.blacklab_index_creation \
        --in media/transcripts \
        --out /data/bl_input \
        --format tsv \
        --docmeta /data/bl_input/docmeta.jsonl \
        --workers 4

Features:
    - Idempotent: skips unchanged files (hash-based)
    - Validates mandatory token fields
    - Unicode NFKC normalization
    - Handles optional fields gracefully
    - Logs errors/skipped files to export_errors.jsonl
    - Supports dry-run mode
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class TokenMeta:
    """Mandatory token metadata."""

    token_id: str
    start_ms: int
    end_ms: int
    lemma: str
    pos: str
    norm: str
    sentence_id: str
    utterance_id: str


@dataclass
class TokenFull:
    """Full token with optional fields."""

    meta: TokenMeta
    past_type: str = ""
    future_type: str = ""
    tense: str = ""
    mood: str = ""
    person: str = ""
    number: str = ""
    aspect: str = ""
    text: str = ""
    speaker_code: str = ""
    speaker_type: str = ""
    sex: str = ""
    mode: str = ""
    discourse: str = ""

    def to_tsv_row(self) -> str:
        """Export to TSV row."""
        return "\t".join(
            [
                self.text,
                self.meta.norm,
                self.meta.lemma,
                self.meta.pos,
                self.past_type,
                self.future_type,
                self.tense,
                self.mood,
                self.person,
                self.number,
                self.aspect,
                self.meta.token_id,
                str(self.meta.start_ms),
                str(self.meta.end_ms),
                self.meta.sentence_id,
                self.meta.utterance_id,
                self.speaker_code,
                self.speaker_type,
                self.sex,
                self.mode,
                self.discourse,
            ]
        )


def _normalize_unicode(s: str) -> str:
    """Normalize to NFKC."""
    if not s:
        return s
    return unicodedata.normalize("NFKC", s)


def map_speaker_attributes(code: str) -> tuple[str, str, str, str]:
    """
    Map speaker_code to (speaker_type, sex, mode, discourse) tuple.
    
    Aligned with database_creation_v3.py for consistency.
    
    Args:
        code: Standardized speaker code (e.g. 'lib-pm', 'foreign', 'none')
    
    Returns:
        Tuple of (speaker_type, sex, mode, discourse)
        
    Speaker codes follow pattern: {role}-{person}{sex}
    - role: lib, lec, pre, tie, traf, foreign
    - person: p (politician), o (other)
    - sex: m (masculino), f (femenino)
    """
    mapping = {
        'lib-pm':  ('pro', 'm', 'libre', 'general'),
        'lib-pf':  ('pro', 'f', 'libre', 'general'),
        'lib-om':  ('otro','m', 'libre', 'general'),
        'lib-of':  ('otro','f', 'libre', 'general'),
        'lec-pm':  ('pro', 'm', 'lectura', 'general'),
        'lec-pf':  ('pro', 'f', 'lectura', 'general'),
        'lec-om':  ('otro','m', 'lectura', 'general'),
        'lec-of':  ('otro','f', 'lectura', 'general'),
        'pre-pm':  ('pro', 'm', 'pre', 'general'),
        'pre-pf':  ('pro', 'f', 'pre', 'general'),
        'tie-pm':  ('pro', 'm', 'n/a', 'tiempo'),
        'tie-pf':  ('pro', 'f', 'n/a', 'tiempo'),
        'traf-pm': ('pro', 'm', 'n/a', 'tránsito'),
        'traf-pf': ('pro', 'f', 'n/a', 'tránsito'),
        'foreign': ('n/a', 'n/a', 'n/a', 'foreign'),
        'none':    ('', '', '', '')
    }
    return mapping.get(code, ('', '', '', ''))


def _escape_xml(s: str) -> str:
    """Minimal XML escaping."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _extract_mandatory_token(token_dict: dict[str, Any]) -> Optional[TokenMeta]:
    """Extract mandatory fields; return None if any missing."""
    required = ["token_id", "start_ms", "end_ms", "lemma", "pos", "norm", "sentence_id", "utterance_id"]
    for field in required:
        if field not in token_dict or token_dict[field] is None:
            logger.warning(f"Token missing mandatory field '{field}': {token_dict.get('token_id', '?')}")
            return None

    try:
        return TokenMeta(
            token_id=str(token_dict["token_id"]),
            start_ms=int(token_dict["start_ms"]),
            end_ms=int(token_dict["end_ms"]),
            lemma=_normalize_unicode(str(token_dict["lemma"])),
            pos=str(token_dict["pos"]),
            norm=_normalize_unicode(str(token_dict["norm"])),
            sentence_id=str(token_dict["sentence_id"]),
            utterance_id=str(token_dict["utterance_id"]),
        )
    except (ValueError, TypeError) as e:
        logger.warning(f"Token field conversion error: {e}")
        return None


def _extract_full_token(token_dict: dict[str, Any]) -> Optional[TokenFull]:
    """Extract full token with optional fields."""
    meta = _extract_mandatory_token(token_dict)
    if not meta:
        return None

    # Extract speaker_code and map to speaker attributes
    speaker_code = str(token_dict.get("speaker_code", "")).strip()
    speaker_type, sex, mode, discourse = map_speaker_attributes(speaker_code)

    return TokenFull(
        meta=meta,
        past_type=str(token_dict.get("past_type", "")).strip(),
        future_type=str(token_dict.get("future_type", "")).strip(),
        tense=str(token_dict.get("tense", "")).strip(),
        mood=str(token_dict.get("mood", "")).strip(),
        person=str(token_dict.get("person", "")).strip(),
        number=str(token_dict.get("number", "")).strip(),
        aspect=str(token_dict.get("aspect", "")).strip(),
        text=_normalize_unicode(str(token_dict.get("text", ""))),
        speaker_code=speaker_code,
        speaker_type=speaker_type,
        sex=sex,
        mode=mode,
        discourse=discourse,
    )


def _compute_content_hash(corpus_doc: dict[str, Any]) -> str:
    """Compute deterministic hash over content-relevant fields."""
    # Hash: country + date + radio + segments count + first 3 token texts
    hashable = {
        "country_code": corpus_doc.get("country_code"),
        "date": corpus_doc.get("date"),
        "radio": corpus_doc.get("radio"),
        "seg_count": len(corpus_doc.get("segments", [])),
    }
    if corpus_doc.get("segments"):
        first_tokens = []
        for seg in corpus_doc.get("segments", [])[:3]:
            for word in seg.get("words", [])[:3]:
                first_tokens.append(word.get("text"))
        hashable["first_tokens"] = first_tokens[:9]

    h = hashlib.sha256(json.dumps(hashable, sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def _load_json_corpus(json_file: Path) -> Optional[dict[str, Any]]:
    """Load JSON corpus document."""
    try:
        with open(json_file, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"Failed to load {json_file}: {e}")
        return None


def export_to_tsv(
    corpus_doc: dict[str, Any],
    json_file: Path,
    output_dir: Path,
    skip_cache: dict[str, str],
) -> tuple[bool, str]:
    """Export corpus document to TSV; return (success, message)."""
    file_id = json_file.stem  # e.g., "2023-08-10_ARG_Mitre"

    # Check idempotency
    content_hash = _compute_content_hash(corpus_doc)
    if file_id in skip_cache and skip_cache[file_id] == content_hash:
        return (True, f"Skipped {file_id} (unchanged)")

    # Extract tokens
    tokens: list[TokenFull] = []
    for segment in corpus_doc.get("segments", []):
        for token_dict in segment.get("words", []):
            token = _extract_full_token(token_dict)
            if token:
                tokens.append(token)
            else:
                logger.warning(f"Skipping malformed token in {file_id}")

    if not tokens:
        logger.error(f"No valid tokens in {file_id}")
        return (False, f"No valid tokens in {file_id}")

    # Write TSV
    tsv_file = output_dir / f"{file_id}.tsv"
    try:
        with open(tsv_file, "w", encoding="utf-8") as f:
            # Header (added speaker_type, sex, mode, discourse)
            f.write(
                "word\tnorm\tlemma\tpos\tpast_type\tfuture_type\ttense\tmood\tperson\tnumber\taspect\ttokid\tstart_ms\tend_ms\tsentence_id\tutterance_id\tspeaker_code\tspeaker_type\tsex\tmode\tdiscourse\n"
            )
            # Data rows
            for token in tokens:
                f.write(token.to_tsv_row() + "\n")

        skip_cache[file_id] = content_hash
        logger.info(f"Created {tsv_file} ({len(tokens)} tokens)")
        return (True, f"Created {file_id}.tsv ({len(tokens)} tokens)")

    except Exception as e:
        logger.error(f"Failed to write {tsv_file}: {e}")
        return (False, f"Write error: {e}")


def collect_json_files(in_dir: Path) -> list[Path]:
    """Collect all *.json files recursively (sorted alphabetically)."""
    # Resolve relative paths from project root
    in_dir = Path(in_dir).resolve()
    
    json_files = sorted(in_dir.rglob("*.json"))
    logger.info(f"Found {len(json_files)} JSON files in {in_dir}")
    return json_files


def run_export(
    in_dir: Path,
    out_dir: Path,
    docmeta_file: Path,
    format_: str,
    workers: int,
    limit: Optional[int],
    dry_run: bool,
) -> dict[str, Any]:
    """Run export; return summary."""
    out_dir.mkdir(parents=True, exist_ok=True)

    json_files = collect_json_files(in_dir)
    if limit:
        json_files = json_files[:limit]

    logger.info(f"Processing {len(json_files)} files (format={format_}, dry_run={dry_run})")

    created = 0
    skipped = 0
    errors = 0
    skip_cache: dict[str, str] = {}
    error_log: list[dict[str, Any]] = []
    docmeta_list: list[dict[str, Any]] = []

    def process_file(json_file: Path) -> tuple[bool, str, Optional[dict[str, Any]]]:
        corpus_doc = _load_json_corpus(json_file)
        if not corpus_doc:
            return (False, f"Failed to load {json_file}", None)

        # TSV export (TSV-only format)
        success, msg = export_to_tsv(corpus_doc, json_file, out_dir, skip_cache)

        # Build docmeta
        file_id = json_file.stem
        docmeta = {
            "doc": file_id,
            "country_code": corpus_doc.get("country_code", ""),
            "date": corpus_doc.get("date", ""),
            "radio": corpus_doc.get("radio", ""),
            "city": corpus_doc.get("city", ""),
            "audio_path": corpus_doc.get("filename", ""),
        }

        if success and "Skipped" in msg:
            return (True, msg, None)  # No docmeta update for skipped

        if success:
            return (True, msg, docmeta)
        else:
            error_log.append({"file": str(json_file), "error": msg})
            return (False, msg, None)

    if dry_run:
        logger.info("DRY RUN: showing first 3 files...")
        for json_file in json_files[:3]:
            corpus_doc = _load_json_corpus(json_file)
            if corpus_doc:
                logger.info(f"  {json_file.stem}: {len(corpus_doc.get('segments', []))} segments")
                if corpus_doc.get("segments"):
                    tokens = corpus_doc["segments"][0].get("words", [])[:3]
                    for token in tokens:
                        logger.info(f"    - {token.get('text')} ({token.get('lemma')})")
        return {
            "dry_run": True,
            "created": 0,
            "skipped": 0,
            "errors": 0,
            "files_scanned": len(json_files),
        }

    # Parallel processing
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_file, f): f for f in json_files}

        for future in as_completed(futures):
            success, msg, docmeta = future.result()
            logger.info(msg)

            if "Skipped" in msg:
                skipped += 1
            elif success:
                created += 1
                if docmeta:
                    docmeta_list.append(docmeta)
            else:
                errors += 1

    # Write docmeta.jsonl
    if docmeta_list:
        docmeta_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(docmeta_file, "w", encoding="utf-8") as f:
                for doc in docmeta_list:
                    f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            logger.info(f"Wrote {len(docmeta_list)} docmeta entries to {docmeta_file}")
        except Exception as e:
            logger.error(f"Failed to write docmeta: {e}")
            errors += 1

    # Write error log if any
    if error_log:
        error_file = out_dir / "export_errors.jsonl"
        try:
            with open(error_file, "w", encoding="utf-8") as f:
                for err in error_log:
                    f.write(json.dumps(err, ensure_ascii=False) + "\n")
            logger.info(f"Wrote {len(error_log)} error entries to {error_file}")
        except Exception as e:
            logger.error(f"Failed to write error log: {e}")

    return {
        "created": created,
        "skipped": skipped,
        "errors": errors,
        "total": len(json_files),
        "format": format_,
    }


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="BlackLab Index Export Tool")
    parser.add_argument("--in", dest="in_dir", default="media/transcripts", help="Input JSON directory (relative to project root)")
    parser.add_argument("--out", dest="out_dir", default="data/blacklab_index/tsv", help="Output directory (relative to project root)")
    parser.add_argument("--format", choices=["tsv"], default="tsv", help="Export format (TSV-only)")
    parser.add_argument("--docmeta", dest="docmeta_file", default="data/blacklab_index/docmeta.jsonl", help="Docmeta output file")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker threads")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of files (for testing)")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode (no writes)")

    args = parser.parse_args()

    # Resolve paths from project root (where src/ and media/ exist)
    project_root = Path(__file__).resolve().parent.parent.parent  # src/scripts/... → project_root
    in_dir = project_root / args.in_dir
    out_dir = project_root / args.out_dir
    docmeta_file = project_root / args.docmeta_file

    if not in_dir.exists():
        logger.error(f"Input directory not found: {in_dir}")
        logger.error(f"  (relative: {args.in_dir})")
        logger.error(f"  (project root: {project_root})")
        return 1

    result = run_export(
        in_dir=in_dir,
        out_dir=out_dir,
        docmeta_file=docmeta_file,
        format_=args.format,
        workers=args.workers,
        limit=args.limit,
        dry_run=args.dry_run,
    )

    logger.info(f"Export complete: {result}")
    return 0 if result["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
