#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = ROOT / "maintenance_pipelines" / "_0_json"
TRANSCRIPTS = ROOT / "media" / "transcripts"
ANNOTATOR_PATH = SCRIPT_DIR / "02_annotate_transcripts_v3.py"
LOG_ROOT = SCRIPT_DIR / "logs" / "tense_schema_migration"
BACKUP_ROOT = SCRIPT_DIR / "backups" / "pre-tense-schema-migration"

logger = logging.getLogger("corapan.tense_schema_migration")


def load_annotator():
    spec = importlib.util.spec_from_file_location("corapan_annotator_v3_2", ANNOTATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {ANNOTATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ann = load_annotator()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def setup_logging(verbose: bool, stamp: str) -> tuple[Path, Path]:
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    log_path = LOG_ROOT / f"migration_{stamp}.log"
    jsonl_path = LOG_ROOT / f"migration_{stamp}.jsonl"
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_path, encoding="utf-8")],
    )
    return log_path, jsonl_path


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def collect_files(country: str | None, file_arg: str | None, limit: int | None) -> list[Path]:
    if file_arg:
        path = Path(file_arg)
        if not path.is_absolute():
            path = ROOT / path
        files = [path]
    else:
        root = TRANSCRIPTS / country if country else TRANSCRIPTS
        files = sorted(root.rglob("*.json"))
    if limit is not None:
        files = files[:limit]
    return files


def token_id_snapshot(data: dict[str, Any]) -> dict[tuple[int, int], str]:
    return {
        (seg_idx, word_idx): str(word.get("token_id") or "")
        for seg_idx, word_idx, _seg, word in ann.iter_words(data)
    }


def protected_snapshot(data: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    protected = ("token_id", "text", "norm", "lemma", "pos", "dep", "head_text", "start_ms", "end_ms", "sentence_id", "utterance_id")
    return {
        (seg_idx, word_idx): {key: word.get(key) for key in protected}
        for seg_idx, word_idx, _seg, word in ann.iter_words(data)
    }


def count_morph(data: dict[str, Any], key: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for _seg_idx, _word_idx, _seg, word in ann.iter_words(data):
        morph = word.get("morph") if isinstance(word.get("morph"), dict) else {}
        if key in morph:
            counter[str(morph[key])] += 1
    return counter


def create_backup(stamp: str) -> Path:
    backup_dir = BACKUP_ROOT / stamp
    target = backup_dir / "transcripts"
    if backup_dir.exists():
        raise RuntimeError(f"Backup already exists: {backup_dir}")
    shutil.copytree(TRANSCRIPTS, target)
    files = sorted(target.rglob("*.json"))
    manifest = {"created_at": utc_now(), "source": rel(TRANSCRIPTS), "target": rel(target), "json_files": len(files), "files": []}
    token_snapshot = {"created_at": utc_now(), "files": []}
    for path in files:
        data = read_json(path)
        words = []
        ids = []
        for seg_idx, word_idx, _seg, word in ann.iter_words(data):
            tid = word.get("token_id")
            if tid:
                ids.append(str(tid))
            words.append(
                {
                    "segment_index": seg_idx,
                    "word_index": word_idx,
                    "text": word.get("text"),
                    "start_ms": word.get("start_ms"),
                    "end_ms": word.get("end_ms"),
                    "token_id": tid,
                }
            )
        manifest["files"].append({"relative_path": str(path.relative_to(target)).replace("\\", "/"), "words": len(words), "missing_token_id": sum(1 for item in words if not item["token_id"]), "duplicate_token_id": len(ids) - len(set(ids))})
        token_snapshot["files"].append({"relative_path": str(path.relative_to(target)).replace("\\", "/"), "tokens": words})
    write_json(backup_dir / "MANIFEST.json", manifest)
    write_json(backup_dir / "TOKEN_ID_SNAPSHOT.json", token_snapshot)
    (backup_dir / "README.md").write_text(
        "# Pre Tense Schema Migration Backup\n\n"
        "Post-full-run transcript backup created before migrating CORAPAN tense labels to the CO.PRE.PAN-compatible schema.\n",
        encoding="utf-8",
    )
    return backup_dir


def migrate_file(path: Path, apply: bool) -> dict[str, Any]:
    data = read_json(path)
    before_ids = token_id_snapshot(data)
    before_protected = protected_snapshot(data)
    old_counts = {key: dict(count_morph(data, key)) for key in ("TenseRole", "PastType", "VoiceType", "FutureType")}

    # Keep a compact per-position morph copy for change counting.
    old_morph_by_pos = {
        (seg_idx, word_idx): dict(word.get("morph") if isinstance(word.get("morph"), dict) else {})
        for seg_idx, word_idx, _seg, word in ann.iter_words(data)
    }

    tense_stats = ann.apply_tense(data)
    new_counts = {key: dict(count_morph(data, key)) for key in ("TenseRole", "PastType", "VoiceType", "FutureType")}
    changed_tokens = 0
    for seg_idx, word_idx, _seg, word in ann.iter_words(data):
        if old_morph_by_pos.get((seg_idx, word_idx), {}) != (word.get("morph") if isinstance(word.get("morph"), dict) else {}):
            changed_tokens += 1

    after_ids = token_id_snapshot(data)
    after_protected = protected_snapshot(data)
    token_id_changes = sum(1 for key, value in before_ids.items() if after_ids.get(key) != value)
    protected_changes = [
        {"segment_index": key[0], "word_index": key[1], "before": before_protected[key], "after": after_protected.get(key)}
        for key in before_protected
        if before_protected[key] != after_protected.get(key)
    ]

    ann_meta = data.setdefault("ann_meta", {})
    existing_created_at = ann_meta.get("created_at")
    ann_meta["pipeline_version"] = ann.PIPELINE_VERSION
    ann_meta["tense_rules_version"] = ann.TENSE_RULES_VERSION
    ann_meta["validation_version"] = ann.VALIDATION_VERSION
    ann_meta["updated_at"] = utc_now()
    if existing_created_at:
        ann_meta["created_at"] = existing_created_at
    ann_meta["tense_audit"] = tense_stats
    ann.mark_stage(ann_meta, "tense", ann.TENSE_RULES_VERSION)
    ann.mark_stage(ann_meta, "validate", ann.VALIDATION_VERSION)
    validation = ann.validate_transcript(data, existing_ids=before_ids)
    ann_meta["validation"] = {"status": "passed" if validation.ok else "failed", "errors": validation.errors, "warnings": validation.warnings}
    ann_meta["annotation_hash"] = ann.annotation_hash(data)

    status = "would_change" if changed_tokens else "unchanged"
    if token_id_changes or protected_changes or not validation.ok:
        status = "error"
    elif apply and changed_tokens:
        write_json(path, data)
        status = "changed"
    elif apply:
        write_json(path, data)
        status = "metadata_refreshed"

    return {
        "file": rel(path),
        "tokens_total": len(before_ids),
        "tokens_changed": changed_tokens,
        "old_counts": old_counts,
        "new_counts": new_counts,
        "token_id_changes": token_id_changes,
        "protected_field_changes": len(protected_changes),
        "validation_errors": validation.errors,
        "status": status,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file")
    parser.add_argument("--country")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    if args.dry_run == args.apply:
        parser.error("Use exactly one of --dry-run or --apply")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path, jsonl_path = setup_logging(args.verbose, stamp)
    backup_dir = None
    if args.apply and args.backup:
        backup_dir = create_backup(stamp)
        logger.info("Created backup: %s", backup_dir)

    files = collect_files(args.country, args.file, args.limit)
    logger.info("Files selected: %d", len(files))
    failures = 0
    summary = Counter()
    with jsonl_path.open("w", encoding="utf-8") as jsonl:
        for path in files:
            row = migrate_file(path, apply=args.apply)
            jsonl.write(json.dumps(row, ensure_ascii=False) + "\n")
            summary[row["status"]] += 1
            if row["status"] == "error":
                failures += 1
            logger.info("%s -> %s changed=%s token_id_changes=%s", row["file"], row["status"], row["tokens_changed"], row["token_id_changes"])
    logger.info("Summary: %s", dict(summary))
    print(json.dumps({"log": str(log_path), "jsonl": str(jsonl_path), "backup": str(backup_dir) if backup_dir else None, "summary": dict(summary)}, indent=2))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
