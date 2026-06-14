#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Audit Corapan transcript annotation quality.

The audit is transcript-native: it reads media/transcripts/<country>/*.json and
does not expect Coprepan article fields.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_AUDIT_DIR = SCRIPT_DIR / "docs" / "agent-runs" / "audits"
ANNOTATOR_PATH = SCRIPT_DIR / "02_annotate_transcripts_v3.py"


def load_annotator():
    spec = importlib.util.spec_from_file_location("corapan_annotator_v3_1", ANNOTATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {ANNOTATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ann = load_annotator()
PROJECT_ROOT = ann.PROJECT_ROOT
TRANSCRIPTS_DIR = ann.TRANSCRIPTS_DIR


def project_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def resolve_path(path_arg: str) -> Path:
    path = Path(path_arg)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def collect_files(country: str | None, file_args: list[str] | None, limit: int | None) -> list[Path]:
    if file_args:
        files = [resolve_path(file_arg) for file_arg in file_args]
    else:
        files = []
        if TRANSCRIPTS_DIR.exists():
            for country_dir in sorted(path for path in TRANSCRIPTS_DIR.iterdir() if path.is_dir()):
                if country and ann.normalize_country_code(country_dir.name) != ann.normalize_country_code(country):
                    continue
                files.extend(sorted(country_dir.glob("*.json")))
    return files[:limit] if limit is not None else files


def token_signature(token: dict[str, Any]) -> str:
    return f"{token.get('text', '')}[{token.get('token_id', '')}]"


def context_for(words: list[dict[str, Any]], idx: int, width: int = 5) -> str:
    return " ".join(str(word.get("text") or "") for word in words[max(0, idx - width) : idx + width + 1])


def count_duplicate_ids(data: dict[str, Any]) -> int:
    counts = ann.token_id_counts(data)
    return sum(1 for value in counts.values() if value > 1)


def special_status(word: dict[str, Any]) -> str | None:
    if ann.is_foreign_word_token(word):
        return "foreign"
    if ann.is_self_correction_token(word):
        return "self_correction"
    if ann.is_filler_token(word):
        return "filler"
    return None


def audit_file(path: Path, sample_tense: int = 10) -> dict[str, Any]:
    data = read_json(path)
    existing_ids = ann.token_id_snapshot(data)
    validation = ann.validate_transcript(data, existing_ids=existing_ids)
    ann_meta = data.get("ann_meta") if isinstance(data.get("ann_meta"), dict) else {}
    token_id_audit = ann_meta.get("token_id_audit") if isinstance(ann_meta.get("token_id_audit"), dict) else {}

    result: dict[str, Any] = {
        "file": project_rel(path),
        "country": data.get("country_code") or path.parent.name,
        "radio": data.get("radio", ""),
        "date": data.get("date", ""),
        "segments": len(data.get("segments", [])) if isinstance(data.get("segments"), list) else 0,
        "words": ann.get_word_count(data),
        "ann_meta": ann_meta,
        "token_id_status": {
            "total": sum(1 for _ in ann.iter_words(data)),
            "missing": 0,
            "duplicate": count_duplicate_ids(data),
            "existing_preserved": token_id_audit.get("unchanged_existing", 0),
            "existing_changed": token_id_audit.get("changed_existing", 0),
            "added": token_id_audit.get("added", 0),
        },
        "time_status": {
            "invalid_start_end": 0,
            "segment_time_mismatches": 0,
        },
        "special_tokens": Counter(),
        "annotation": {
            "pos_counts": Counter(),
            "PastType": Counter(),
            "FutureType": Counter(),
            "VoiceType": Counter(),
            "TenseRole": Counter(),
        },
        "samples": defaultdict(list),
        "suspicious_tokens": [],
        "legacy_fields": 0,
        "hard_gate_failures": [],
        "validation_errors": validation.errors,
        "validation_warnings": validation.warnings,
    }

    for err in validation.errors:
        if "start_ms > end_ms" in err:
            result["time_status"]["invalid_start_end"] += 1
        if "duplicate token_id" in err:
            result["token_id_status"]["duplicate"] += 1
        if "empty token_id" in err or "missing token_id" in err:
            result["token_id_status"]["missing"] += 1
    for warning in validation.warnings:
        if "word times outside utterance range" in warning:
            result["time_status"]["segment_time_mismatches"] += 1

    for _seg_idx, _word_idx, seg, word in ann.iter_words(data):
        token_id = str(word.get("token_id") or "").strip()
        if not token_id:
            result["token_id_status"]["missing"] += 1
        status = special_status(word)
        if status:
            result["special_tokens"][status] += 1
        morph = word.get("morph") if isinstance(word.get("morph"), dict) else {}
        pos = str(word.get("pos") or "")
        if pos:
            result["annotation"]["pos_counts"][pos] += 1
        for key in ("PastType", "FutureType", "VoiceType", "TenseRole"):
            if key in morph:
                result["annotation"][key][morph[key]] += 1

    for _seg_idx, _word_idx, seg, word in ann.iter_words(data):
        words = seg.get("words", []) if isinstance(seg, dict) else []
        try:
            idx = words.index(word)
        except ValueError:
            idx = 0
        morph = word.get("morph") if isinstance(word.get("morph"), dict) else {}
        for key in ("PastType", "FutureType"):
            if key in morph:
                label = morph[key]
                sample_key = f"{key}:{label}"
                if len(result["samples"][sample_key]) < sample_tense:
                    result["samples"][sample_key].append(
                        {"token": token_signature(word), "context": context_for(words, idx)}
                    )
        if morph.get("VoiceType") in {"passive", "resultative"}:
            key = "ser/estar + participle"
            if len(result["samples"][key]) < sample_tense:
                result["samples"][key].append({"token": token_signature(word), "context": context_for(words, idx)})
        if morph.get("TenseRole") == "lexical_participle":
            key = "lexical_participles"
            if len(result["samples"][key]) < sample_tense:
                result["samples"][key].append({"token": token_signature(word), "context": context_for(words, idx)})
        text = str(word.get("text") or "")
        norm = str(word.get("norm") or "")
        if "past_type" in word or "future_type" in word:
            result["legacy_fields"] += 1
        if len(norm) > 40 or "past_type" in word or "future_type" in word:
            result["suspicious_tokens"].append(
                {"token": token_signature(word), "norm": norm, "context": context_for(words, idx)}
            )

    for key in ("special_tokens",):
        result[key] = dict(result[key])
    for key, counts in result["annotation"].items():
        result["annotation"][key] = dict(counts)
    result["samples"] = dict(result["samples"])
    stages = ann_meta.get("stages") if isinstance(ann_meta.get("stages"), dict) else {}
    validation_meta = ann_meta.get("validation") if isinstance(ann_meta.get("validation"), dict) else {}
    token_tense_roles = dict(result["annotation"]["TenseRole"])
    meta_tense_audit = ann_meta.get("tense_audit") if isinstance(ann_meta.get("tense_audit"), dict) else {}
    meta_tense_roles = meta_tense_audit.get("TenseRole") if isinstance(meta_tense_audit.get("TenseRole"), dict) else {}
    special_meta = ann_meta.get("special_token_audit") if isinstance(ann_meta.get("special_token_audit"), dict) else {}

    hard_checks = {
        "pipeline_version": ann_meta.get("pipeline_version") == ann.PIPELINE_VERSION,
        "validation_status": validation_meta.get("status") == "passed",
        "spacy_stage_done": stages.get("spacy", {}).get("status") == "done",
        "tense_stage_done": stages.get("tense", {}).get("status") == "done",
        "validate_stage_done": stages.get("validate", {}).get("status") == "done",
        "token_ids_preserved": result["token_id_status"]["existing_changed"] == 0,
        "no_duplicate_token_ids": result["token_id_status"]["duplicate"] == 0,
        "no_legacy_tense_fields": result["legacy_fields"] == 0,
        "no_validation_errors": not validation.errors,
        "tense_role_meta_matches_tokens": meta_tense_roles == token_tense_roles,
    }
    result["hard_gate_failures"] = [name for name, ok in hard_checks.items() if not ok]
    spacy_real = (
        bool(ann_meta.get("spacy_version"))
        and ann_meta.get("spacy_version") != "not-installed"
        and special_meta.get("spacy_annotation_mode") == "model"
    )

    decision = "GREEN"
    recommendation = "Ready for the next staged run."
    red_failures = [
        failure
        for failure in result["hard_gate_failures"]
        if failure not in {"tense_role_meta_matches_tokens"}
    ]
    if red_failures or result["token_id_status"]["duplicate"] or result["token_id_status"]["existing_changed"]:
        decision = "RED"
        recommendation = "Fix structural or token-id errors before processing more files."
    elif not spacy_real:
        decision = "YELLOW"
        recommendation = "Install/verify spaCy model and rerun with --require-spacy."
    elif result["hard_gate_failures"] or validation.warnings or result["suspicious_tokens"]:
        decision = "YELLOW"
        recommendation = "Review warnings and samples, then run a small country-limited batch."
    result["quality_decision"] = decision
    result["recommendation"] = recommendation
    return result


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = ["# Corapan Transcript Annotation Audit", ""]
    for result in results:
        lines.extend(
            [
                f"## {result['file']}",
                "",
                f"- Country: `{result['country']}`",
                f"- Radio: {result['radio']}",
                f"- Date: {result['date']}",
                f"- Segments: {result['segments']}",
                f"- Words: {result['words']}",
                f"- Pipeline: `{result['ann_meta'].get('pipeline_version', '')}`",
                f"- spaCy version: `{result['ann_meta'].get('spacy_version', '')}`",
                f"- spaCy mode: `{result['ann_meta'].get('special_token_audit', {}).get('spacy_annotation_mode', '')}`",
                f"- Validation: `{result['ann_meta'].get('validation', {}).get('status', '')}`",
                f"- Legacy tense fields: {result['legacy_fields']}",
                "",
                "### Token IDs",
                "",
            ]
        )
        for key, value in result["token_id_status"].items():
            lines.append(f"- `{key}`: {value}")
        lines.extend(["", "### Times", ""])
        for key, value in result["time_status"].items():
            lines.append(f"- `{key}`: {value}")
        lines.extend(["", "### Special Tokens", ""])
        if result["special_tokens"]:
            for key, value in sorted(result["special_tokens"].items()):
                lines.append(f"- `{key}`: {value}")
        else:
            lines.append("- none")
        for title, key in (
            ("POS Counts", "pos_counts"),
            ("PastType Counts", "PastType"),
            ("FutureType Counts", "FutureType"),
            ("VoiceType Counts", "VoiceType"),
            ("TenseRole Counts", "TenseRole"),
        ):
            lines.extend(["", f"### {title}", ""])
            counts = result["annotation"].get(key, {})
            if counts:
                for name, value in sorted(counts.items()):
                    lines.append(f"- `{name}`: {value}")
            else:
                lines.append("- none")
        lines.extend(["", "### Samples", ""])
        if result["samples"]:
            for sample_key, samples in sorted(result["samples"].items()):
                lines.append(f"#### {sample_key}")
                for sample in samples[:10]:
                    lines.append(f"- `{sample['token']}`: {sample['context']}")
                lines.append("")
        else:
            lines.append("- none")
        lines.extend(["### Suspicious Tokens", ""])
        if result["suspicious_tokens"]:
            for item in result["suspicious_tokens"][:25]:
                lines.append(f"- `{item['token']}` norm=`{item['norm']}`: {item['context']}")
        else:
            lines.append("- none")
        lines.extend(["", "### Validation", ""])
        if result["validation_errors"]:
            for err in result["validation_errors"][:25]:
                lines.append(f"- ERROR: {err}")
        if result["validation_warnings"]:
            for warning in result["validation_warnings"][:25]:
                lines.append(f"- WARNING: {warning}")
        if not result["validation_errors"] and not result["validation_warnings"]:
            lines.append("- no errors or warnings")
        lines.extend(["", "### Hard Gate Failures", ""])
        if result["hard_gate_failures"]:
            for failure in result["hard_gate_failures"]:
                lines.append(f"- `{failure}`")
        else:
            lines.append("- none")
        lines.extend(
            [
                "",
                "### Quality Decision",
                "",
                f"**{result['quality_decision']}**",
                "",
                f"Recommendation: {result['recommendation']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Corapan transcript annotation quality.")
    parser.add_argument("--file", action="append", default=None, help="Transcript JSON to audit; can be repeated.")
    parser.add_argument("--country", type=str, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sample-tense", type=int, default=10)
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--json-out", type=str, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = collect_files(args.country, args.file, args.limit)
    if not files:
        print("No transcript files found.")
        return 1
    results = [audit_file(path, args.sample_tense) for path in files]
    markdown = render_markdown(results)
    if args.out:
        out = resolve_path(args.out)
    else:
        DEFAULT_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        out = DEFAULT_AUDIT_DIR / f"{datetime_stamp()}_transcript_annotation_audit.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    if args.json_out:
        json_out = resolve_path(args.json_out)
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        print(markdown)
    return 0


def datetime_stamp() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


if __name__ == "__main__":
    raise SystemExit(main())
