#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib.cleaning import CLEANING_VERSION, clean_text
from lib.hashing import annotation_hash, clean_hash, sha256_file
from lib.segmentation import SEGMENTATION_VERSION, build_paragraph_segments
from lib.spacy_annotator import SPACY_MODEL, SPACY_STAGE_VERSION, SpacyModelError, annotate_segments, get_spacy_version
from lib.state import connect, delete_entry, get, mark_done, mark_failed, mark_running, mark_stale
from lib.tense_rules import TENSE_RULES_VERSION, apply_tense
from lib.token_ids import assign_token_ids
from lib.validation import VALIDATION_VERSION, validate_annotation, validate_state_done


try:
    import tqdm as _tqdm_mod
    _HAS_TQDM = True
except ImportError:
    _HAS_TQDM = False

SCHEMA_VERSION = "coprepan-ann/v1"
PIPELINE_VERSION = "coprepan-article-ann-v1.4"
LANGUAGE_GUARD_VERSION = "language-v1"
SCRIPT_NAME = "scripts/annotation/annotate_articles.py"
RAW_ROOT_CANDIDATES = ("json_raw", "json-raw")
ANNOTATED_ROOT = PROJECT_ROOT / "json_annotated"
LOG_DIR = PROJECT_ROOT / "logs" / "annotation"
PROGRESS_LOG_DIR = PROJECT_ROOT / "logs"
STAGE_ORDER = ("clean", "segment", "spacy", "tense", "validate")

logger = logging.getLogger("coprepan.annotation")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_section_index(path: Path) -> dict[str, dict[str, str]]:
    """Load section_articles_enriched.csv and index rows by article_id."""
    index: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            article_id = row.get("article_id", "")
            if article_id:
                index[article_id] = dict(row)
    return index


def _inject_section_metadata(
    data: dict[str, Any],
    section_index: dict[str, dict[str, str]],
    input_path: Path,
) -> None:
    """Join section metadata into each article by article_id."""
    for article in data.get("articles", []):
        article_id = str(article.get("metadata", {}).get("article_id") or "")
        metadata = article.setdefault("metadata", {})

        if article_id and article_id in section_index:
            row = section_index[article_id]
            raw_path = row.get("section_path", "")
            path_list = [p.strip() for p in raw_path.split(">") if p.strip()] if raw_path else []
            metadata["section"] = {
                "raw": row.get("section_raw", ""),
                "normalized": row.get("section_raw_normalized", ""),
                "path": path_list,
                "detection_method": row.get("section_detection_method", "missing"),
                "detection_confidence": row.get("section_detection_confidence", "missing"),
                "standard_section": row.get("standard_section", "other_unclear"),
                "standard_section_confidence": row.get("standard_section_confidence", "missing"),
                "is_opinion": row.get("is_opinion", "false").lower() == "true",
                "mapping_version": row.get("section_mapping_version", ""),
            }
        else:
            if article_id:
                logger.warning(
                    "No section metadata for article_id=%s in %s",
                    article_id,
                    input_path.name,
                )
            metadata["section"] = None


def setup_logging(verbose: bool = False) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_DIR / "annotate_articles.log", encoding="utf-8"),
        ],
    )


def find_raw_root() -> Path:
    for name in RAW_ROOT_CANDIDATES:
        path = PROJECT_ROOT / name
        if path.is_dir():
            return path
    return PROJECT_ROOT / "json_raw"


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if path.exists():
        return path
    text = str(path)
    alternates = []
    if "json-raw" in text:
        alternates.append(Path(text.replace("json-raw", "json_raw")))
    if "json_raw" in text:
        alternates.append(Path(text.replace("json_raw", "json-raw")))
    for alt in alternates:
        if alt.exists():
            return alt
    raw_root = find_raw_root()
    parts = Path(path_str.replace("\\", "/")).parts
    if len(parts) >= 3 and parts[-1].endswith(".json"):
        country = parts[-2] if parts[-2].upper() == parts[-2] else None
        search_root = raw_root / country if country and (raw_root / country).exists() else raw_root
        matches = sorted(search_root.rglob(parts[-1]))
        if len(matches) == 1:
            return matches[0]
    return path


def rel_to_raw(path: Path, raw_root: Path) -> Path:
    try:
        return path.resolve().relative_to(raw_root.resolve())
    except ValueError:
        return Path(path.name)


def output_path_for(input_path: Path, raw_root: Path) -> Path:
    rel = rel_to_raw(input_path, raw_root)
    name = rel.name[:-5] + ".ann.json" if rel.name.endswith(".json") else rel.name + ".ann.json"
    return ANNOTATED_ROOT / rel.parent / name


def collect_input_files(raw_root: Path, country: str | None, file_arg: str | None) -> list[Path]:
    if file_arg:
        path = resolve_path(file_arg)
        return [path]
    pattern_root = raw_root / country.upper() if country else raw_root
    if not pattern_root.exists():
        return []
    return sorted(path for path in pattern_root.rglob("*.json") if not path.name.endswith(".tmp"))


def article_ref(input_path: Path, article: dict[str, Any], idx: int) -> str:
    article_id = str(article.get("metadata", {}).get("article_id") or f"a{idx}")
    short = article_id.split(":", 1)[-1][:12]
    return f"{input_path.stem}:a{idx}_{short}"


def stage_versions() -> dict[str, str]:
    return {
        "pipeline_version": PIPELINE_VERSION,
        "cleaning_version": CLEANING_VERSION,
        "segmentation_version": SEGMENTATION_VERSION,
        "spacy_version": get_spacy_version(),
        "spacy_model": SPACY_MODEL,
        "tense_rules_version": TENSE_RULES_VERSION,
        "validation_version": VALIDATION_VERSION,
    }


def target_stages(stage: str | None) -> tuple[str, ...]:
    if stage is None:
        return STAGE_ORDER
    idx = STAGE_ORDER.index(stage)
    return STAGE_ORDER[: idx + 1]


def mark_stage(ann_meta: dict[str, Any], stage: str, version: str, status: str = "done") -> None:
    ann_meta.setdefault("stages", {})[stage] = {
        "version": version,
        "status": status,
        "timestamp": utc_now(),
    }


def build_initial_annotation(raw_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "meta": raw_data.get("meta", {}),
        "articles": raw_data.get("articles", []),
    }


def article_language(article: dict[str, Any]) -> str:
    return str(article.get("metadata", {}).get("language") or "es").strip().lower()


def is_spanish_article(article: dict[str, Any]) -> bool:
    return article_language(article) == "es"


def apply_language_guard(data: dict[str, Any]) -> dict[str, int]:
    stats = {"annotated_articles": 0, "unsupported_language_articles": 0}
    for article in data.get("articles", []):
        language = article_language(article)
        article["annotation_language"] = language
        if language != "es":
            article["annotation_status"] = "skipped_unsupported_language"
            article["annotation_skip_reason"] = "metadata.language != es"
            stats["unsupported_language_articles"] += 1
            text_obj = article.setdefault("text", {})
            for field in ("title", "body"):
                field_obj = text_obj.setdefault(field, {})
                field_obj.setdefault("clean", field_obj.get("raw", ""))
                field_obj["segments"] = []
                field_obj["cleaning_report"] = {
                    "version": CLEANING_VERSION,
                    "status": "skipped_unsupported_language",
                    "corrections": [],
                    "flagged": [],
                    "correction_count": 0,
                    "flagged_count": 0,
                }
        else:
            article["annotation_status"] = "annotated"
            article.pop("annotation_skip_reason", None)
            stats["annotated_articles"] += 1
    return stats


def language_stats(data: dict[str, Any]) -> dict[str, int]:
    stats = {"annotated_articles": 0, "unsupported_language_articles": 0}
    for article in data.get("articles", []):
        if article.get("annotation_status") == "skipped_unsupported_language" or article_language(article) != "es":
            stats["unsupported_language_articles"] += 1
        else:
            stats["annotated_articles"] += 1
    return stats


def file_status_from_language_stats(stats: dict[str, int]) -> str:
    annotated = stats.get("annotated_articles", 0)
    unsupported = stats.get("unsupported_language_articles", 0)
    if annotated == 0 and unsupported > 0:
        return "skipped_unsupported_language"
    if unsupported > 0:
        return "done_with_skips"
    return "done"


def clean_stage(data: dict[str, Any]) -> None:
    for article in data.get("articles", []):
        if not is_spanish_article(article):
            continue
        text_obj = article.setdefault("text", {})
        for field in ("title", "body"):
            field_obj = text_obj.setdefault(field, {})
            result = clean_text(field_obj.get("raw", ""))
            field_obj["clean"] = result.clean
            field_obj["cleaning_report"] = result.report


def segment_stage(data: dict[str, Any], input_path: Path) -> None:
    for idx, article in enumerate(data.get("articles", [])):
        if not is_spanish_article(article):
            continue
        ref = article_ref(input_path, article, idx)
        text_obj = article.setdefault("text", {})
        for field in ("title", "body"):
            field_obj = text_obj.setdefault(field, {})
            field_obj["segments"] = build_paragraph_segments(field_obj.get("clean", ""), ref, field)


def count_tokens(data: dict[str, Any]) -> int:
    total = 0
    for article in data.get("articles", []):
        for field in ("title", "body"):
            for segment in article.get("text", {}).get(field, {}).get("segments") or []:
                for sentence in segment.get("sentences") or []:
                    total += len(sentence.get("tokens") or [])
    return total


def make_ann_meta(
    *,
    input_hash: str,
    clean_hash_value: str,
    annotation_hash_value: str,
    existing_created_at: str | None = None,
) -> dict[str, Any]:
    now = utc_now()
    return {
        "schema_version": SCHEMA_VERSION,
        "pipeline_version": PIPELINE_VERSION,
        "script": SCRIPT_NAME,
        "input_hash": input_hash,
        "clean_hash": clean_hash_value,
        "annotation_hash": annotation_hash_value,
        "created_at": existing_created_at or now,
        "updated_at": now,
        "spacy_model": SPACY_MODEL,
        "spacy_version": get_spacy_version(),
        "validation_version": VALIDATION_VERSION,
        "language_guard_version": LANGUAGE_GUARD_VERSION,
        "stages": {},
    }


def finalize_meta(data: dict[str, Any], input_hash: str, existing_created_at: str | None = None) -> None:
    clean_hash_value = clean_hash(data)
    stats = language_stats(data)
    data["ann_meta"] = make_ann_meta(
        input_hash=input_hash,
        clean_hash_value=clean_hash_value,
        annotation_hash_value="sha256:pending",
        existing_created_at=existing_created_at,
    )
    mark_stage(data["ann_meta"], "clean", CLEANING_VERSION)
    mark_stage(data["ann_meta"], "language_guard", LANGUAGE_GUARD_VERSION)
    mark_stage(data["ann_meta"], "segment", SEGMENTATION_VERSION)
    mark_stage(data["ann_meta"], "spacy", SPACY_STAGE_VERSION)
    mark_stage(data["ann_meta"], "tense", TENSE_RULES_VERSION)
    mark_stage(data["ann_meta"], "validate", VALIDATION_VERSION)
    data["ann_meta"]["file_status"] = file_status_from_language_stats(stats)
    data["ann_meta"]["annotated_articles"] = stats["annotated_articles"]
    data["ann_meta"]["unsupported_language_articles"] = stats["unsupported_language_articles"]
    data["ann_meta"]["annotation_hash"] = annotation_hash(data)


def is_current(output_path: Path, input_hash_value: str, force: bool) -> tuple[bool, str]:
    if force or not output_path.exists():
        return False, "force" if force else "missing output"
    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"unreadable output: {exc}"
    ann_meta = data.get("ann_meta", {})
    checks = {
        "schema_version": SCHEMA_VERSION,
        "pipeline_version": PIPELINE_VERSION,
        "input_hash": input_hash_value,
        "spacy_model": SPACY_MODEL,
        "validation_version": VALIDATION_VERSION,
        "language_guard_version": LANGUAGE_GUARD_VERSION,
    }
    for key, expected in checks.items():
        if ann_meta.get(key) != expected:
            return False, f"{key} mismatch"
    stages = ann_meta.get("stages", {})
    required_versions = {
        "clean": CLEANING_VERSION,
        "language_guard": LANGUAGE_GUARD_VERSION,
        "segment": SEGMENTATION_VERSION,
        "spacy": SPACY_STAGE_VERSION,
        "tense": TENSE_RULES_VERSION,
        "validate": VALIDATION_VERSION,
    }
    for stage, version in required_versions.items():
        if stages.get(stage, {}).get("version") != version:
            return False, f"{stage} version mismatch"
    errors = validate_annotation(data)
    if errors:
        return False, f"validation failed: {errors[0]}"
    return True, "up-to-date"


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def process_file(
    input_path: Path,
    output_path: Path,
    stages: tuple[str, ...],
    *,
    force: bool,
    dry_run: bool,
    section_index: dict[str, dict[str, str]] | None = None,
) -> tuple[str, int]:
    input_hash_value = sha256_file(input_path)
    current, reason = is_current(output_path, input_hash_value, force)
    if current and "validate" in stages:
        return f"skipped ({reason})", 0
    if current and not force:
        return f"skipped ({reason})", 0

    if dry_run:
        return f"would process ({reason})", 0

    conn = connect(PROJECT_ROOT / "state" / "annotation" / "annotation_state.sqlite")
    input_state_path = str(input_path.relative_to(PROJECT_ROOT) if input_path.is_relative_to(PROJECT_ROOT) else input_path)
    output_state_path = str(output_path.relative_to(PROJECT_ROOT) if output_path.is_relative_to(PROJECT_ROOT) else output_path)
    mark_running(
        conn,
        input_path=input_state_path,
        output_path=output_state_path,
        input_hash=input_hash_value,
        versions=stage_versions(),
    )
    try:
        raw_data = json.loads(input_path.read_text(encoding="utf-8-sig"))
        data = build_initial_annotation(raw_data)
        apply_language_guard(data)
        if "clean" in stages:
            clean_stage(data)
        if "segment" in stages:
            segment_stage(data, input_path)
        if "spacy" in stages:
            annotate_segments(data, SPACY_MODEL)
            assign_token_ids(data)
        if "tense" in stages:
            apply_tense(data)

        if "validate" in stages or "tense" in stages:
            finalize_meta(data, input_hash_value)
            errors = validate_annotation(data)
            if errors:
                raise ValueError("; ".join(errors[:10]))
        else:
            clean_hash_value = clean_hash(data)
            data["ann_meta"] = make_ann_meta(
                input_hash=input_hash_value,
                clean_hash_value=clean_hash_value,
                annotation_hash_value="sha256:partial",
            )
            for stage in stages:
                version = {
                    "clean": CLEANING_VERSION,
                    "segment": SEGMENTATION_VERSION,
                    "spacy": SPACY_STAGE_VERSION,
                }[stage]
                mark_stage(data["ann_meta"], stage, version)
            stats = language_stats(data)
            mark_stage(data["ann_meta"], "language_guard", LANGUAGE_GUARD_VERSION)
            data["ann_meta"]["file_status"] = file_status_from_language_stats(stats)
            data["ann_meta"]["annotated_articles"] = stats["annotated_articles"]
            data["ann_meta"]["unsupported_language_articles"] = stats["unsupported_language_articles"]

        if section_index is not None:
            _inject_section_metadata(data, section_index, input_path)

        atomic_write_json(output_path, data)
        stats = language_stats(data)
        file_status = file_status_from_language_stats(stats)
        mark_done(
            conn,
            input_path=input_state_path,
            clean_hash=data["ann_meta"]["clean_hash"],
            annotation_hash=data["ann_meta"]["annotation_hash"],
            article_count=len(data.get("articles", [])),
            token_count=count_tokens(data),
            status=file_status,
            annotated_articles=stats["annotated_articles"],
            unsupported_language_articles=stats["unsupported_language_articles"],
        )
        state_errors = validate_state_done(conn, input_state_path)
        if state_errors:
            raise ValueError("; ".join(state_errors))
        _token_count = count_tokens(data)
        return "processed", _token_count
    except Exception as exc:
        mark_failed(conn, input_path=input_state_path, error=str(exc))
        raise
    finally:
        conn.close()


def reprocess_tense_for_output(output_path: Path, *, dry_run: bool, force: bool) -> str:
    if not output_path.exists():
        return "missing annotated output"
    data = json.loads(output_path.read_text(encoding="utf-8"))
    ann_meta = data.get("ann_meta", {})
    current = ann_meta.get("stages", {}).get("tense", {}).get("version") == TENSE_RULES_VERSION
    if current and not force:
        return "skipped (tense up-to-date)"
    if dry_run:
        return "would reprocess tense"
    existing_created_at = ann_meta.get("created_at")
    apply_tense(data)
    ann_meta["updated_at"] = utc_now()
    ann_meta["spacy_version"] = get_spacy_version()
    mark_stage(ann_meta, "tense", TENSE_RULES_VERSION)
    ann_meta["annotation_hash"] = annotation_hash(data)
    data["ann_meta"] = ann_meta
    errors = validate_annotation(data)
    if errors:
        raise ValueError("; ".join(errors[:10]))
    atomic_write_json(output_path, data)
    data["ann_meta"]["created_at"] = existing_created_at or data["ann_meta"].get("created_at")
    update_state_after_tense_reprocess(output_path, data)
    return "reprocessed tense"


def input_path_for_output(output_path: Path) -> Path:
    rel = output_path.resolve().relative_to(ANNOTATED_ROOT.resolve())
    raw_name = rel.name[:-9] + ".json" if rel.name.endswith(".ann.json") else rel.name
    return find_raw_root() / rel.parent / raw_name


def update_state_after_tense_reprocess(output_path: Path, data: dict[str, Any]) -> None:
    input_path = input_path_for_output(output_path)
    input_state_path = str(input_path.relative_to(PROJECT_ROOT) if input_path.is_relative_to(PROJECT_ROOT) else input_path)
    output_state_path = str(output_path.relative_to(PROJECT_ROOT) if output_path.is_relative_to(PROJECT_ROOT) else output_path)
    ann_meta = data.get("ann_meta", {})
    conn = connect(PROJECT_ROOT / "state" / "annotation" / "annotation_state.sqlite")
    try:
        conn.execute(
            """
            INSERT INTO annotation_state (
                input_path, output_path, input_hash, clean_hash, annotation_hash, status,
                started_at, finished_at, error, article_count, token_count,
                pipeline_version, cleaning_version, segmentation_version, spacy_version,
                spacy_model, tense_rules_version
            ) VALUES (?, ?, ?, ?, ?, 'done', ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(input_path) DO UPDATE SET
                output_path=excluded.output_path,
                input_hash=excluded.input_hash,
                clean_hash=excluded.clean_hash,
                annotation_hash=excluded.annotation_hash,
                status='done',
                finished_at=excluded.finished_at,
                error=NULL,
                article_count=excluded.article_count,
                token_count=excluded.token_count,
                pipeline_version=excluded.pipeline_version,
                cleaning_version=excluded.cleaning_version,
                segmentation_version=excluded.segmentation_version,
                spacy_version=excluded.spacy_version,
                spacy_model=excluded.spacy_model,
                tense_rules_version=excluded.tense_rules_version
            """,
            (
                input_state_path,
                output_state_path,
                ann_meta.get("input_hash"),
                ann_meta.get("clean_hash"),
                ann_meta.get("annotation_hash"),
                utc_now(),
                utc_now(),
                len(data.get("articles", [])),
                count_tokens(data),
                ann_meta.get("pipeline_version"),
                CLEANING_VERSION,
                SEGMENTATION_VERSION,
                ann_meta.get("spacy_version"),
                ann_meta.get("spacy_model"),
                TENSE_RULES_VERSION,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def pre_scan_articles(files: list[Path]) -> dict[Path, int]:
    """Count articles in each input file for progress tracking (pre-run pass)."""
    counts: dict[Path, int] = {}
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            counts[path] = len(data.get("articles", []))
        except Exception:
            counts[path] = 0
    return counts


class ProgressTracker:
    """Tracks annotation progress; writes logs/annotation_progress.json and .jsonl."""

    def __init__(
        self,
        files_total: int,
        articles_by_file: dict[Path, int],
        raw_root: Path,
        annotated_root: Path,
        section_metadata: str | None,
    ) -> None:
        self.files_total = files_total
        self._articles_by_file = articles_by_file
        self.articles_total = sum(articles_by_file.values())

        self.files_done = 0
        self.files_skipped = 0
        self.files_failed = 0
        self.articles_done = 0
        self.articles_skipped = 0
        self.tokens_done = 0
        self.errors_total = 0
        self.current_file: str = ""
        self.last_output_file: str = ""
        self.last_error: str | None = None

        self.started_at = utc_now()
        self._input_root = _relstr(raw_root)
        self._output_root = _relstr(annotated_root)
        self._section_metadata = section_metadata
        self._progress_path = PROGRESS_LOG_DIR / "annotation_progress.json"
        self._progress_jsonl = PROGRESS_LOG_DIR / "annotation_progress.jsonl"
        self._tqdm_bar: Any = None

    def start(self) -> None:
        PROGRESS_LOG_DIR.mkdir(parents=True, exist_ok=True)
        if _HAS_TQDM:
            self._tqdm_bar = _tqdm_mod.tqdm(
                total=self.files_total,
                unit="file",
                desc="annotating",
                dynamic_ncols=True,
            )
        self._write_progress("running")

    def file_started(self, input_path: Path) -> None:
        self.current_file = _relstr(input_path)

    def file_done(self, input_path: Path, output_path: Path, status: str, token_count: int) -> None:
        n_articles = self._articles_by_file.get(input_path, 0)
        if "skipped" in status:
            self.files_skipped += 1
            self.articles_skipped += n_articles
        else:
            self.files_done += 1
            self.articles_done += n_articles
            self.tokens_done += token_count
        self.last_output_file = _relstr(output_path)

        files_processed = self.files_done + self.files_skipped + self.files_failed
        if self._tqdm_bar is not None:
            self._tqdm_bar.set_postfix(
                articles=self.articles_done + self.articles_skipped,
                tokens=f"{self.tokens_done:,}",
                err=self.errors_total,
                refresh=False,
            )
            self._tqdm_bar.update(1)
        elif files_processed % 10 == 0:
            logger.info(
                "Progress: files=%d/%d articles=%d/%d tokens=%d errors=%d",
                files_processed, self.files_total,
                self.articles_done + self.articles_skipped, self.articles_total,
                self.tokens_done, self.errors_total,
            )
        self._write_progress("running")
        self._append_jsonl()

    def file_error(self, input_path: Path, error: str) -> None:
        self.files_failed += 1
        self.errors_total += 1
        self.last_error = error
        self._write_progress("running")
        self._append_jsonl()

    def finish(self, status: str = "completed") -> None:
        if self._tqdm_bar is not None:
            self._tqdm_bar.close()
        self._write_progress(status)

    def _snapshot(self, status: str) -> dict[str, Any]:
        return {
            "status": status,
            "started_at": self.started_at,
            "updated_at": utc_now(),
            "input_root": self._input_root,
            "output_root": self._output_root,
            "section_metadata": self._section_metadata,
            "files_total": self.files_total,
            "files_done": self.files_done,
            "files_skipped": self.files_skipped,
            "files_failed": self.files_failed,
            "articles_total": self.articles_total,
            "articles_done": self.articles_done,
            "articles_skipped": self.articles_skipped,
            "tokens_total": None,
            "tokens_done": self.tokens_done,
            "current_file": self.current_file,
            "last_output_file": self.last_output_file,
            "errors_total": self.errors_total,
            "last_error": self.last_error,
        }

    def _write_progress(self, status: str) -> None:
        snap = self._snapshot(status)
        try:
            atomic_write_json(self._progress_path, snap)
        except Exception:
            pass

    def _append_jsonl(self) -> None:
        line = {
            "updated_at": utc_now(),
            "files_done": self.files_done,
            "files_skipped": self.files_skipped,
            "files_failed": self.files_failed,
            "articles_done": self.articles_done,
            "articles_skipped": self.articles_skipped,
            "tokens_done": self.tokens_done,
            "current_file": self.current_file,
            "errors_total": self.errors_total,
        }
        try:
            with self._progress_jsonl.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(line, ensure_ascii=False) + "\n")
        except Exception:
            pass


def _relstr(path: Path) -> str:
    """Return path relative to PROJECT_ROOT as a forward-slash string."""
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Annotate Coprepan article JSON files.")
    parser.add_argument("--resume", action="store_true", help="Resume pending/running/stale work.")
    parser.add_argument("--force", action="store_true", help="Recreate annotation outputs.")
    parser.add_argument("--country", type=str, default=None, help="Process one country code, e.g. COL.")
    parser.add_argument("--file", type=str, default=None, help="Process one raw JSON file.")
    parser.add_argument("--limit", type=int, default=None, help="Process at most N files.")
    parser.add_argument("--dry-run", action="store_true", help="List work without writing.")
    parser.add_argument("--retry-failed", action="store_true", help="Only retry files marked failed in SQLite state.")
    parser.add_argument("--reset-state", action="store_true", help="Delete selected outputs, tmp files, and SQLite state rows.")
    parser.add_argument("--stage", choices=STAGE_ORDER, default=None, help="Run through this stage.")
    parser.add_argument("--force-stage", choices=("tense",), default=None, help="Force a cheap single-stage reprocess.")
    parser.add_argument(
        "--section-metadata",
        type=Path,
        default=None,
        metavar="CSV",
        help="Path to section_articles_enriched.csv; joined per article_id into annotation output.",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)
    raw_root = find_raw_root()
    files = collect_input_files(raw_root, args.country, args.file)

    section_index: dict[str, dict[str, str]] | None = None
    if args.section_metadata is not None:
        meta_path = args.section_metadata
        if not meta_path.is_absolute():
            meta_path = PROJECT_ROOT / meta_path
        if meta_path.exists():
            section_index = load_section_index(meta_path)
            logger.info("Loaded section metadata: %d entries from %s", len(section_index), meta_path)
        else:
            logger.warning("--section-metadata path not found: %s", meta_path)
    if args.limit is not None:
        files = files[: args.limit]

    for directory in (
        PROJECT_ROOT / "scripts" / "annotation",
        PROJECT_ROOT / "state" / "annotation",
        PROJECT_ROOT / "logs" / "annotation",
        PROJECT_ROOT / "json_annotated",
        PROJECT_ROOT / "docs" / "agent-runs",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    if not files:
        logger.error("No input JSON files found under %s", raw_root)
        return 1

    if args.reset_state:
        conn = connect(PROJECT_ROOT / "state" / "annotation" / "annotation_state.sqlite")
        try:
            for input_path in files:
                output_path = output_path_for(input_path, raw_root)
                tmp_path = Path(str(output_path) + ".tmp")
                for artifact in (output_path, tmp_path):
                    if artifact.exists():
                        artifact.unlink()
                        logger.info("Deleted %s", artifact.relative_to(PROJECT_ROOT))
                input_state_path = str(input_path.relative_to(PROJECT_ROOT) if input_path.is_relative_to(PROJECT_ROOT) else input_path)
                delete_entry(conn, input_path=input_state_path)
                logger.info("Deleted state row for %s", input_state_path)
        finally:
            conn.close()
        return 0

    conn = connect(PROJECT_ROOT / "state" / "annotation" / "annotation_state.sqlite")
    selected: list[Path] = []
    for input_path in files:
        output_path = output_path_for(input_path, raw_root)
        input_hash_value = sha256_file(input_path)
        input_state_path = str(input_path.relative_to(PROJECT_ROOT) if input_path.is_relative_to(PROJECT_ROOT) else input_path)
        row = get(conn, input_state_path)
        if row and row.get("status") in {"done", "done_with_skips", "skipped_unsupported_language"} and row.get("input_hash") != input_hash_value:
            mark_stale(conn, input_path=input_state_path)
            row = get(conn, input_state_path)
        if args.retry_failed and (not row or row.get("status") != "failed"):
            continue
        if args.resume and row and row.get("status") in {"done", "done_with_skips", "skipped_unsupported_language"} and not args.force:
            current, _reason = is_current(output_path, input_hash_value, False)
            if current:
                continue
        selected.append(input_path)
    conn.close()

    if not selected:
        logger.info("Nothing to do.")
        return 0

    logger.info("Raw root: %s", raw_root)
    logger.info("Files selected: %s", len(selected))

    articles_by_file = pre_scan_articles(selected)
    tracker = ProgressTracker(
        files_total=len(selected),
        articles_by_file=articles_by_file,
        raw_root=raw_root,
        annotated_root=ANNOTATED_ROOT,
        section_metadata=str(args.section_metadata) if args.section_metadata else None,
    )
    tracker.start()

    stats: dict[str, int] = {}
    try:
        if args.force_stage == "tense":
            for input_path in selected:
                output_path = output_path_for(input_path, raw_root)
                status = reprocess_tense_for_output(output_path, dry_run=args.dry_run, force=True)
                stats[status] = stats.get(status, 0) + 1
                logger.info("%s -> %s", output_path.relative_to(PROJECT_ROOT), status)
        else:
            stages = target_stages(args.stage)
            for input_path in selected:
                output_path = output_path_for(input_path, raw_root)
                tracker.file_started(input_path)
                try:
                    status, token_count = process_file(
                        input_path,
                        output_path,
                        stages,
                        force=args.force,
                        dry_run=args.dry_run,
                        section_index=section_index,
                    )
                except Exception as exc:
                    tracker.file_error(input_path, str(exc))
                    raise
                stats[status] = stats.get(status, 0) + 1
                logger.info("%s -> %s", input_path.relative_to(PROJECT_ROOT), status)
                tracker.file_done(input_path, output_path, status, token_count)
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        tracker.finish("interrupted")
        logger.info("Summary: %s", stats)
        return 130
    except SpacyModelError as exc:
        logger.error(str(exc))
        tracker.finish("failed")
        return 2
    except Exception as exc:
        logger.exception("Annotation failed: %s", exc)
        tracker.finish("failed")
        return 1

    tracker.finish("completed")
    logger.info("Summary: %s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
