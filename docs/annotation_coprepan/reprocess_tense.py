#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib.hashing import annotation_hash
from lib.tense_rules import TENSE_RULES_VERSION, apply_tense
from lib.validation import VALIDATION_VERSION, validate_annotation


ANNOTATED_ROOT = PROJECT_ROOT / "json_annotated"
LOG_DIR = PROJECT_ROOT / "logs" / "annotation"
STATE_DB = PROJECT_ROOT / "state" / "annotation" / "annotation_state.sqlite"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_DIR / "reprocess_tense.log", encoding="utf-8"),
        ],
    )


def atomic_write_json(path: Path, data: dict) -> None:
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def count_tokens(data: dict) -> int:
    total = 0
    for article in data.get("articles", []):
        for field in ("title", "body"):
            for segment in article.get("text", {}).get(field, {}).get("segments") or []:
                for sentence in segment.get("sentences") or []:
                    total += len(sentence.get("tokens") or [])
    return total


def input_path_for_output(output_path: Path) -> Path:
    rel = output_path.resolve().relative_to(ANNOTATED_ROOT.resolve())
    raw_name = rel.name[:-9] + ".json" if rel.name.endswith(".ann.json") else rel.name
    raw_root = PROJECT_ROOT / "json_raw"
    if not raw_root.exists():
        raw_root = PROJECT_ROOT / "json-raw"
    return raw_root / rel.parent / raw_name


def update_state(path: Path, data: dict) -> None:
    STATE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(STATE_DB)
    ann_meta = data.get("ann_meta", {})
    input_path = input_path_for_output(path)
    input_state_path = str(input_path.relative_to(PROJECT_ROOT) if input_path.is_relative_to(PROJECT_ROOT) else input_path)
    output_state_path = str(path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS annotation_state (
                input_path TEXT PRIMARY KEY,
                output_path TEXT NOT NULL,
                input_hash TEXT,
                clean_hash TEXT,
                annotation_hash TEXT,
                status TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                error TEXT,
                article_count INTEGER DEFAULT 0,
                token_count INTEGER DEFAULT 0,
                pipeline_version TEXT,
                cleaning_version TEXT,
                segmentation_version TEXT,
                spacy_version TEXT,
                spacy_model TEXT,
                tense_rules_version TEXT
            )
            """
        )
        now = utc_now()
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
                now,
                now,
                len(data.get("articles", [])),
                count_tokens(data),
                ann_meta.get("pipeline_version"),
                ann_meta.get("stages", {}).get("clean", {}).get("version"),
                ann_meta.get("stages", {}).get("segment", {}).get("version"),
                ann_meta.get("spacy_version"),
                ann_meta.get("spacy_model"),
                TENSE_RULES_VERSION,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def collect_files(country: str | None, file_arg: str | None) -> list[Path]:
    if file_arg:
        return [resolve_path(file_arg)]
    root = ANNOTATED_ROOT / country.upper() if country else ANNOTATED_ROOT
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.ann.json") if not path.name.endswith(".tmp"))


def mark_tense_stage(ann_meta: dict) -> None:
    ann_meta.setdefault("stages", {})["tense"] = {
        "version": TENSE_RULES_VERSION,
        "status": "done",
        "timestamp": utc_now(),
    }


def process(path: Path, *, force: bool, dry_run: bool) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    ann_meta = data.get("ann_meta", {})
    current = ann_meta.get("stages", {}).get("tense", {}).get("version") == TENSE_RULES_VERSION
    if current and not force:
        return "skipped (tense up-to-date)"
    if dry_run:
        return "would reprocess tense"

    apply_tense(data)
    ann_meta["updated_at"] = utc_now()
    ann_meta["validation_version"] = VALIDATION_VERSION
    mark_tense_stage(ann_meta)
    ann_meta.setdefault("stages", {})["validate"] = {
        "version": VALIDATION_VERSION,
        "status": "done",
        "timestamp": utc_now(),
    }
    ann_meta["annotation_hash"] = annotation_hash(data)
    data["ann_meta"] = ann_meta

    errors = validate_annotation(data)
    if errors:
        raise ValueError("; ".join(errors[:10]))
    atomic_write_json(path, data)
    update_state(path, data)
    return "reprocessed tense"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reprocess PastType/FutureType in Coprepan annotations.")
    parser.add_argument("--country", type=str, default=None)
    parser.add_argument("--file", type=str, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    setup_logging()
    args = parse_args()
    files = collect_files(args.country, args.file)
    if args.limit is not None:
        files = files[: args.limit]
    if not files:
        logging.error("No annotated files found.")
        return 1
    stats: dict[str, int] = {}
    for path in files:
        status = process(path, force=args.force, dry_run=args.dry_run)
        stats[status] = stats.get(status, 0) + 1
        logging.info("%s -> %s", path.relative_to(PROJECT_ROOT), status)
    logging.info("Summary: %s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
