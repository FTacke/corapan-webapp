#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
RAW_ROOT = PROJECT_ROOT / "json_raw"
ANNOTATED_ROOT = PROJECT_ROOT / "json_annotated"
DOCS_ROOT = PROJECT_ROOT / "docs" / "agent-runs"
AUDIT_DIR = DOCS_ROOT / "audits"
STATE_DB = PROJECT_ROOT / "state" / "annotation" / "annotation_state.sqlite"
TODAY = date.today().isoformat()
BASELINE_FILES = (
    "json_raw/ARG/clarin/ARG_clarin_2025-12-13.json",
    "json_raw/COL/elpais/COL_elpais_2026-02-01.json",
)

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_annotation_quality import audit_file, render_markdown  # noqa: E402
from annotate_articles import find_raw_root, output_path_for  # noqa: E402
from lib.validation import validate_annotation  # noqa: E402


@dataclass(frozen=True)
class RawCandidate:
    path: Path
    country: str
    source: str
    date_text: str
    size_mb: float
    article_count: int
    total_words: int
    es_article_count: int = 0
    non_es_article_count: int = 0
    body_hashes: tuple[str, ...] = ()
    canonical_urls: tuple[str, ...] = ()
    selection_reason: str = ""


def project_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def parse_date_from_name(path: Path) -> str:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    return match.group(1) if match else ""


def inspect_raw(path: Path, max_size_mb: float, min_words: int = 250) -> RawCandidate | None:
    if not path.name.endswith(".json") or path.stat().st_size >= max_size_mb * 1024 * 1024:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    articles = data.get("articles")
    if not isinstance(articles, list) or not articles:
        return None
    valid_article = False
    total_words = 0
    es_article_count = 0
    non_es_article_count = 0
    body_hashes: list[str] = []
    canonical_urls: list[str] = []
    for article in articles:
        if not isinstance(article, dict):
            continue
        text_obj = article.get("text")
        if not isinstance(text_obj, dict):
            continue
        title_obj = text_obj.get("title")
        body_obj = text_obj.get("body")
        title = title_obj.get("raw", "") if isinstance(title_obj, dict) else ""
        body = body_obj.get("raw", "") if isinstance(body_obj, dict) else ""
        language = str(article.get("metadata", {}).get("language") or "es").strip().lower()
        if language == "es":
            es_article_count += 1
        else:
            non_es_article_count += 1
        metadata = article.get("metadata", {})
        if isinstance(metadata, dict) and metadata.get("canonical_url"):
            canonical_urls.append(str(metadata["canonical_url"]))
        if isinstance(title, str) and isinstance(body, str):
            total_words += len((title + " " + body).split())
            if title.strip() and body.strip():
                valid_article = True
            normalized_body = " ".join(body.lower().split())
            if normalized_body:
                body_hashes.append(hashlib.sha256(normalized_body.encode("utf-8")).hexdigest())
    if not valid_article or total_words < min_words:
        return None
    rel_parts = path.relative_to(RAW_ROOT).parts
    if len(rel_parts) < 3:
        return None
    return RawCandidate(
        path=path,
        country=rel_parts[0],
        source=rel_parts[1],
        date_text=parse_date_from_name(path),
        size_mb=path.stat().st_size / 1024 / 1024,
        article_count=len(articles),
        total_words=total_words,
        es_article_count=es_article_count,
        non_es_article_count=non_es_article_count,
        body_hashes=tuple(sorted(set(body_hashes))),
        canonical_urls=tuple(sorted(set(canonical_urls))),
    )


def candidate_score(candidate: RawCandidate) -> tuple[int, float, str]:
    tiny_penalty = 1 if candidate.total_words < 700 else 0
    huge_penalty = 1 if candidate.size_mb > 0.35 else 0
    return (tiny_penalty + huge_penalty, candidate.size_mb, project_rel(candidate.path))


def collect_candidates(max_size_mb: float) -> list[RawCandidate]:
    root = find_raw_root()
    global RAW_ROOT
    RAW_ROOT = root
    candidates = []
    for path in sorted(root.rglob("*.json")):
        candidate = inspect_raw(path, max_size_mb)
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def with_reason(candidate: RawCandidate, reason: str) -> RawCandidate:
    return RawCandidate(
        path=candidate.path,
        country=candidate.country,
        source=candidate.source,
        date_text=candidate.date_text,
        size_mb=candidate.size_mb,
        article_count=candidate.article_count,
        total_words=candidate.total_words,
        es_article_count=candidate.es_article_count,
        non_es_article_count=candidate.non_es_article_count,
        body_hashes=candidate.body_hashes,
        canonical_urls=candidate.canonical_urls,
        selection_reason=reason,
    )


def select_sample(
    candidates: list[RawCandidate],
    *,
    max_files: int,
    min_countries: int,
    include_baseline: bool,
) -> list[RawCandidate]:
    candidates = [candidate for candidate in candidates if candidate.es_article_count > 0]
    by_path = {candidate.path.resolve(): candidate for candidate in candidates}
    selected: list[RawCandidate] = []
    selected_paths: set[Path] = set()

    if include_baseline:
        for baseline in BASELINE_FILES:
            path = (PROJECT_ROOT / baseline).resolve()
            candidate = by_path.get(path)
            if candidate is None and path.exists():
                candidate = inspect_raw(path, max_size_mb=999999, min_words=1)
            if candidate is not None:
                selected.append(with_reason(candidate, "baseline"))
                selected_paths.add(path)

    def add(candidate: RawCandidate, reason: str) -> bool:
        if len(selected) >= max_files:
            return False
        resolved = candidate.path.resolve()
        if resolved in selected_paths:
            return False
        selected.append(with_reason(candidate, reason))
        selected_paths.add(resolved)
        return True

    country_groups: dict[str, list[RawCandidate]] = defaultdict(list)
    source_groups: dict[tuple[str, str], list[RawCandidate]] = defaultdict(list)
    for candidate in candidates:
        country_groups[candidate.country].append(candidate)
        source_groups[(candidate.country, candidate.source)].append(candidate)
    for values in country_groups.values():
        values.sort(key=candidate_score)
    for values in source_groups.values():
        values.sort(key=candidate_score)

    for country in sorted(country_groups):
        if len({item.country for item in selected}) >= min_countries:
            break
        if country in {item.country for item in selected}:
            continue
        add(country_groups[country][0], "country_diversity")

    for key in sorted(source_groups):
        if len(selected) >= max_files:
            break
        if len({(item.country, item.source) for item in selected}) >= min(8, max_files):
            break
        if key in {(item.country, item.source) for item in selected}:
            continue
        add(source_groups[key][0], "source_diversity")

    for candidate in sorted(candidates, key=candidate_score):
        if len(selected) >= max_files:
            break
        add(candidate, "fill_small_valid_file")

    return selected


def output_for_raw(path: Path) -> Path:
    return output_path_for(path, find_raw_root())


def run_command(args: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        args,
        cwd=PROJECT_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return completed.returncode, completed.stdout


def audit_name(candidate: RawCandidate) -> str:
    return f"{TODAY}_{candidate.country}_{candidate.source}_{candidate.date_text}_annotation_audit.md"


def write_sample_doc(sample: list[RawCandidate], path: Path, excluded_non_es: list[RawCandidate] | None = None) -> None:
    excluded_non_es = excluded_non_es or []
    countries = sorted({item.country for item in sample})
    sources = sorted({f"{item.country}/{item.source}" for item in sample})
    lines = [
        "# Coprepan Annotation Multi-Land Sample",
        "",
        f"- Date: {TODAY}",
        f"- selected_files: {len(sample)}",
        f"- excluded_non_es_files: {len(excluded_non_es)}",
        f"- mixed_language_files: {sum(1 for item in sample if item.non_es_article_count > 0)}",
        f"- selected_articles_es: {sum(item.es_article_count for item in sample)}",
        f"- skipped_articles_non_es: {sum(item.non_es_article_count for item in sample)}",
        f"- Countries: {', '.join(countries)}",
        f"- Sources: {', '.join(sources)}",
        "",
        "| country | source | date | size MB | articles | es articles | non-es articles | total words | reason | path |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for item in sample:
        lines.append(
            "| "
            + " | ".join(
                [
                    item.country,
                    item.source,
                    item.date_text,
                    f"{item.size_mb:.3f}",
                    str(item.article_count),
                    str(item.es_article_count),
                    str(item.non_es_article_count),
                    str(item.total_words),
                    item.selection_reason,
                    f"`{project_rel(item.path)}`",
                ]
            )
            + " |"
        )
    if excluded_non_es:
        lines.extend(["", "## Excluded Non-ES Files", "", "| country | source | date | articles | path |", "|---|---|---:|---:|---|"])
        for item in excluded_non_es[:50]:
            lines.append(
                f"| {item.country} | {item.source} | {item.date_text} | {item.article_count} | `{project_rel(item.path)}` |"
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def body_segment_range(data: dict[str, Any]) -> tuple[int, int]:
    counts = []
    for article in data.get("articles", []):
        body = article.get("text", {}).get("body", {})
        if isinstance(body, dict):
            counts.append(len(body.get("segments") or []))
    return (min(counts), max(counts)) if counts else (0, 0)


def iter_tokens(data: dict[str, Any]):
    for article in data.get("articles", []):
        for field in ("title", "body"):
            field_obj = article.get("text", {}).get(field, {})
            for segment in field_obj.get("segments") or []:
                for sentence in segment.get("sentences") or []:
                    tokens = sentence.get("tokens") or []
                    context = " ".join(token.get("text", "") for token in tokens)
                    for token in tokens:
                        yield token, context


def collect_correction_types(data: dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for article in data.get("articles", []):
        for field in ("title", "body"):
            report = article.get("text", {}).get(field, {}).get("cleaning_report") or {}
            for item in report.get("corrections") or []:
                key = item.get("type", "unknown")
                subtype = item.get("subtype")
                if subtype:
                    key = f"{key}/{subtype}"
                counts[key] += 1
    return counts


def collect_tense_review(data: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    review = {
        "other_compound_past": [],
        "future_type": [],
        "unmarked_ser_estar_candidates": [],
    }
    for article in data.get("articles", []):
        for field in ("title", "body"):
            field_obj = article.get("text", {}).get(field, {})
            for segment in field_obj.get("segments") or []:
                for sentence in segment.get("sentences") or []:
                    tokens = sentence.get("tokens") or []
                    context = " ".join(token.get("text", "") for token in tokens)
                    for idx, token in enumerate(tokens):
                        morph = token.get("morph") if isinstance(token.get("morph"), dict) else {}
                        if morph.get("PastType") == "otherCompoundPast":
                            review["other_compound_past"].append({"token": token.get("text", ""), "context": context})
                        if "FutureType" in morph:
                            review["future_type"].append({"token": token.get("text", ""), "context": context})
                        if token.get("lemma", "").lower() not in {"ser", "estar"}:
                            continue
                        if "Fin" not in set(morph.get("VerbForm") if isinstance(morph.get("VerbForm"), list) else [morph.get("VerbForm")]):
                            continue
                        for j in range(idx + 1, min(len(tokens), idx + 6)):
                            candidate_morph = tokens[j].get("morph") if isinstance(tokens[j].get("morph"), dict) else {}
                            if "Fin" in set(candidate_morph.get("VerbForm") if isinstance(candidate_morph.get("VerbForm"), list) else [candidate_morph.get("VerbForm")]):
                                break
                            if "Part" not in set(candidate_morph.get("VerbForm") if isinstance(candidate_morph.get("VerbForm"), list) else [candidate_morph.get("VerbForm")]):
                                continue
                            if candidate_morph.get("TenseRole") != "lexical_participle":
                                review["unmarked_ser_estar_candidates"].append(
                                    {"token": f"{token.get('text', '')} + {tokens[j].get('text', '')}", "context": context}
                                )
                            break
    return review


def collect_duplicate_groups(sample: list[RawCandidate]) -> dict[str, list[list[str]]]:
    by_body_hash: dict[str, list[str]] = defaultdict(list)
    by_url: dict[str, list[str]] = defaultdict(list)
    for item in sample:
        rel = project_rel(item.path)
        for body_hash in item.body_hashes:
            by_body_hash[body_hash].append(rel)
        for url in item.canonical_urls:
            by_url[url].append(rel)
    return {
        "body_hash": [sorted(set(paths)) for paths in by_body_hash.values() if len(set(paths)) > 1],
        "canonical_url": [sorted(set(paths)) for paths in by_url.values() if len(set(paths)) > 1],
    }


def state_row(input_path: Path) -> dict[str, Any] | None:
    if not STATE_DB.exists():
        return None
    conn = sqlite3.connect(STATE_DB)
    conn.row_factory = sqlite3.Row
    try:
        key = project_rel(input_path)
        row = conn.execute("SELECT * FROM annotation_state WHERE input_path = ?", (key,)).fetchone()
        if row is None:
            row = conn.execute("SELECT * FROM annotation_state WHERE input_path = ?", (key.replace("/", "\\"),)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def load_ann(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_file(candidate: RawCandidate, ann_path: Path, audit: dict[str, Any], skip_ok: bool) -> dict[str, Any]:
    data = load_ann(ann_path)
    validation_errors = validate_annotation(data) if data else ["annotation output missing"]
    row = state_row(candidate.path)
    body_min, body_max = body_segment_range(data) if data else (0, 0)
    return {
        "file": project_rel(ann_path),
        "raw_file": project_rel(candidate.path),
        "country": candidate.country,
        "source": candidate.source,
        "articles": audit.get("articles", 0),
        "tokens": audit.get("tokens", 0),
        "sentences": audit.get("sentences", 0),
        "empty_sentences": audit.get("empty_sentences", 0),
        "offset_errors": sum(1 for err in validation_errors if "offset mismatch" in err),
        "duplicate_token_ids": sum(1 for err in validation_errors if "duplicate token_id" in err),
        "body_segments_min": body_min,
        "body_segments_max": body_max,
        "ann_status": row.get("status") if ann_path.exists() and row and row.get("status") in {"done", "done_with_skips", "skipped_unsupported_language"} else "failed",
        "skip_status_second_run": "up-to-date" if skip_ok else "not confirmed",
        "validation_errors": validation_errors,
        "tmp_exists": Path(str(ann_path) + ".tmp").exists(),
    }


def render_aggregate(
    sample: list[RawCandidate],
    file_summaries: list[dict[str, Any]],
    audits: list[dict[str, Any]],
    correction_counts: Counter[str],
    tense_review: dict[str, list[dict[str, str]]],
    duplicate_groups: dict[str, list[list[str]]] | None = None,
) -> str:
    duplicate_groups = duplicate_groups or {"body_hash": [], "canonical_url": []}
    total_articles = sum(item["articles"] for item in file_summaries)
    total_tokens = sum(item["tokens"] for item in file_summaries)
    total_sentences = sum(item["sentences"] for item in file_summaries)
    countries = sorted({item.country for item in sample})
    sources = sorted({f"{item.country}/{item.source}" for item in sample})
    past_counts: Counter[str] = Counter()
    future_counts: Counter[str] = Counter()
    voice_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    other_past = []
    remaining_artifacts = []
    samples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for audit in audits:
        past_counts.update(audit.get("past_type_counts", {}))
        future_counts.update(audit.get("future_type_counts", {}))
        voice_counts.update(audit.get("voice_type_counts", {}))
        role_counts.update(audit.get("tense_role_counts", {}))
        other_past.extend(audit.get("other_past_tokens", []))
        remaining_artifacts.extend(audit.get("remaining_split_suffix_artifacts", []))
        for key, values in (audit.get("samples") or {}).items():
            samples[key].extend(values)

    has_red = any(
        item["empty_sentences"]
        or item["offset_errors"]
        or item["duplicate_token_ids"]
        or item["tmp_exists"]
        or item["ann_status"] not in {"done", "done_with_skips", "skipped_unsupported_language"}
        or item["skip_status_second_run"] != "up-to-date"
        for item in file_summaries
    ) or any(audit.get("known_false_merges") for audit in audits)
    has_yellow = bool(remaining_artifacts or other_past or tense_review["other_compound_past"])
    decision = "RED" if has_red else "YELLOW" if has_yellow else "GREEN"
    reason = (
        "strukturelle oder technische Fehler gefunden"
        if decision == "RED"
        else "prüfbare Restfälle in Cleaning/Tense vorhanden"
        if decision == "YELLOW"
        else "technische Integrität erfüllt, keine systematischen Restprobleme im Sample"
    )

    lines = [
        "# Coprepan Multi-Land Annotation Audit",
        "",
        f"- Date: {TODAY}",
        f"- Pipeline target: `coprepan-article-ann-v1.4` / `clean-v5` / `tense-v3` / `validation-v4`",
        "",
        "## 1. Sample",
        "",
        f"- number_of_files: {len(sample)}",
        f"- countries: {', '.join(countries)}",
        f"- sources: {', '.join(sources)}",
        f"- total_articles: {total_articles}",
        f"- annotated_articles: {sum(audit.get('annotated_articles', 0) for audit in audits)}",
        f"- skipped_unsupported_language_articles: {sum(audit.get('unsupported_language_articles', 0) for audit in audits)}",
        f"- total_tokens: {total_tokens}",
        f"- total_sentences: {total_sentences}",
        f"- duplicate_article_groups: {sum(len(groups) for groups in duplicate_groups.values())}",
        f"- duplicate_file_pairs: {sum(max(0, len(group) - 1) for groups in duplicate_groups.values() for group in groups)}",
        "",
        "## 2. Technical Integrity Per File",
        "",
        "| file | country | source | articles | tokens | sentences | empty_sentences | offset_errors | duplicate_token_ids | body_segments_min/max | ann_status | skip_status_second_run |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for item in file_summaries:
        lines.append(
            f"| `{item['file']}` | {item['country']} | {item['source']} | {item['articles']} | {item['tokens']} | "
            f"{item['sentences']} | {item['empty_sentences']} | {item['offset_errors']} | {item['duplicate_token_ids']} | "
            f"{item['body_segments_min']}/{item['body_segments_max']} | {item['ann_status']} | {item['skip_status_second_run']} |"
        )
    lines.extend(
        [
            "",
            "## 3. Cleaning Quality",
            "",
            "| file | cleaning_corrections | cleaning_flags | blocked_split_suffix_flags | remaining_split_suffix_artifacts | known_false_merges | known_split_artifacts | suspicious_tokens |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for summary, audit in zip(file_summaries, audits):
        lines.append(
            f"| `{summary['file']}` | {audit['cleaning_corrections']} | {audit['cleaning_flags']} | "
            f"{audit['blocked_split_suffix_flags']} | {len(audit['remaining_split_suffix_artifacts'])} | "
            f"{len(audit['known_false_merges'])} | {len(audit['known_split_artifacts'])} | {len(audit['suspicious_tokens'])} |"
        )
    lines.extend(["", "### Cleaning Correction Types", ""])
    if correction_counts:
        for key, value in correction_counts.most_common():
            lines.append(f"- `{key}`: {value}")
    else:
        lines.append("- none")
    lines.extend(["", "### New Unknown Artifacts", ""])
    if remaining_artifacts:
        for item in remaining_artifacts[:50]:
            lines.append(f"- `{item.get('text')}`: {item.get('context')}")
    else:
        lines.append("- none")
    lines.extend(["", "### Duplicate Article Groups", ""])
    any_dupes = False
    for kind, groups in duplicate_groups.items():
        for group in groups:
            any_dupes = True
            lines.append(f"- `{kind}`: " + ", ".join(f"`{path}`" for path in group))
    if not any_dupes:
        lines.append("- none")
    lines.extend(["", "## 4. Tense Quality", ""])
    for title, counts in (
        ("PastType", past_counts),
        ("FutureType", future_counts),
        ("VoiceType", voice_counts),
        ("TenseRole", role_counts),
    ):
        lines.extend([f"### {title}", ""])
        if counts:
            for key, value in sorted(counts.items()):
                lines.append(f"- `{key}`: {value}")
        else:
            lines.append("- none")
        lines.append("")
    lines.extend(["### all otherPast tokens", ""])
    if other_past:
        for item in other_past[:100]:
            lines.append(f"- `{item.get('token')}`: {item.get('context')}")
    else:
        lines.append("- none")
    lines.extend(["", "### all otherCompoundPast tokens", ""])
    if tense_review["other_compound_past"]:
        for item in tense_review["other_compound_past"][:100]:
            lines.append(f"- `{item['token']}`: {item['context']}")
    else:
        lines.append("- none")
    lines.extend(["", "### all FutureType hits", ""])
    if tense_review["future_type"]:
        for item in tense_review["future_type"][:100]:
            lines.append(f"- `{item['token']}`: {item['context']}")
    else:
        lines.append("- none")
    lines.extend(["", "### ser/estar + participle candidates not marked", ""])
    if tense_review["unmarked_ser_estar_candidates"]:
        for item in tense_review["unmarked_ser_estar_candidates"][:100]:
            lines.append(f"- `{item['token']}`: {item['context']}")
    else:
        lines.append("- none")
    lines.extend(["", "### Tense Samples", ""])
    for category in ("presentPerfect", "pastPerfect", "perfectInfinitive", "simplePast", "imperfectPast", "FutureType"):
        lines.extend([f"#### {category}", ""])
        values = samples.get(category, [])
        if values:
            for item in values[:12]:
                lines.append(f"- `{item.get('token')}`: {item.get('context')}")
        else:
            lines.append("- none")
        lines.append("")
    lines.extend(["## 5. Quality Decision", "", f"**{decision}**: {reason}", ""])
    if decision != "GREEN":
        lines.append("Empfehlung: vor dem großen Lauf die oben gelisteten Restfälle prüfen.")
    else:
        lines.append("Empfehlung: nächster Schritt kann ein größerer, weiterhin gestufter Lauf sein.")
    return "\n".join(lines).rstrip() + "\n"


def render_run_doc(
    sample_doc: Path,
    aggregate_doc: Path,
    audit_paths: list[Path],
    sample: list[RawCandidate],
    test_results: list[str],
    decision: str,
) -> str:
    rendered_tests = test_results or ["not run in this helper invocation"]
    return (
        "# Annotation Multi-Land Audit Run\n\n"
        f"- Date: {TODAY}\n"
        "- Changed files: `scripts/annotation/run_multiland_audit.py`\n"
        "- Helper script: yes\n"
        f"- Sample: {len(sample)} files, {len({item.country for item in sample})} countries, "
        f"{len({(item.country, item.source) for item in sample})} sources\n"
        "- Reset method: `annotate_articles.py --reset-state --file <raw_file>` per selected file\n"
        "- Annotation method: `annotate_articles.py --file <raw_file> --force`\n"
        "- Skip check: second run without `--force` per selected file\n"
        f"- Sample document: `{project_rel(sample_doc)}`\n"
        f"- Aggregate report: `{project_rel(aggregate_doc)}`\n"
        "- Individual audits:\n"
        + "".join(f"  - `{project_rel(path)}`\n" for path in audit_paths)
        + "\n## Tests\n\n"
        + "".join(f"- {line}\n" for line in rendered_tests)
        + "\n## Decision\n\n"
        + f"- Traffic light: **{decision}**\n"
        "- Remaining limitations: sample is intentionally small; it does not prove 15M-token runtime behavior.\n"
        "- Recommended next step: inspect any listed YELLOW/RED contexts, then run a larger staged country batch.\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a controlled multi-land Coprepan annotation audit.")
    parser.add_argument("--max-files", type=int, default=20)
    parser.add_argument("--max-size-mb", type=float, default=2.0)
    parser.add_argument("--min-countries", type=int, default=5)
    parser.add_argument("--include-baseline", action="store_true")
    parser.add_argument("--file", action="append", default=None, help="Explicit raw file to include; can be repeated.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sample-tense", type=int, default=10)
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-reset", action="store_true")
    parser.add_argument("--aggregate-out", type=str, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    candidates = collect_candidates(args.max_size_mb)
    excluded_non_es = [candidate for candidate in candidates if candidate.es_article_count == 0 and candidate.non_es_article_count > 0]
    if args.file:
        sample = []
        for file_arg in args.file:
            path = Path(file_arg)
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            candidate = inspect_raw(path, max_size_mb=999999, min_words=1)
            if candidate is None:
                raise SystemExit(f"Cannot inspect selected raw file: {file_arg}")
            sample.append(with_reason(candidate, "explicit_file"))
    else:
        sample = select_sample(
            candidates,
            max_files=args.max_files,
            min_countries=args.min_countries,
            include_baseline=args.include_baseline,
        )
    sample_doc = DOCS_ROOT / f"{TODAY}_annotation_multiland_sample.md"
    write_sample_doc(sample, sample_doc, excluded_non_es)
    print(f"Selected {len(sample)} files across {len({item.country for item in sample})} countries.")
    print(f"Sample doc: {project_rel(sample_doc)}")
    for item in sample:
        print(f"- {project_rel(item.path)} ({item.selection_reason}, {item.size_mb:.3f} MB)")

    if args.dry_run:
        return 0

    test_results: list[str] = []
    if not args.skip_tests:
        test_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_annotation_cleaning_quality.py",
            "tests/test_annotation_validation_quality.py",
            "tests/test_annotation_audit_quality.py",
            "tests/test_annotation_tense_rules_quality.py",
            "-q",
        ]
        code, output = run_command(test_cmd)
        tail = " ".join(output.strip().splitlines()[-3:]) if output.strip() else "no output"
        test_results.append(f"`{' '.join(test_cmd)}` -> exit {code}; {tail}")
        print(test_results[-1])
        if code != 0:
            return code

    raw_root = find_raw_root()
    run_status: dict[str, dict[str, Any]] = {}
    for item in sample:
        rel = project_rel(item.path)
        run_status[rel] = {}
        if not args.skip_reset:
            code, output = run_command([sys.executable, "scripts/annotation/annotate_articles.py", "--reset-state", "--file", rel])
            run_status[rel]["reset"] = {"code": code, "output": output}
            print(f"reset {rel}: {code}")
        code, output = run_command([sys.executable, "scripts/annotation/annotate_articles.py", "--file", rel, "--force"])
        run_status[rel]["force"] = {"code": code, "output": output}
        print(f"force {rel}: {code}")
        code, output = run_command([sys.executable, "scripts/annotation/annotate_articles.py", "--file", rel])
        skip_ok = code == 0 and ("skipped (up-to-date)" in output or "Nothing to do." in output)
        run_status[rel]["skip"] = {"code": code, "output": output, "ok": skip_ok}
        print(f"skip {rel}: {code}, up-to-date={skip_ok}")

    audits = []
    audit_paths = []
    file_summaries = []
    correction_counts: Counter[str] = Counter()
    tense_review = {"other_compound_past": [], "future_type": [], "unmarked_ser_estar_candidates": []}
    for item in sample:
        ann_path = output_path_for(item.path, raw_root)
        audit_path = AUDIT_DIR / audit_name(item)
        audit_paths.append(audit_path)
        if ann_path.exists():
            audit = audit_file(ann_path, args.sample_tense)
            audits.append(audit)
            audit_path.write_text(render_markdown([audit]), encoding="utf-8")
            data = load_ann(ann_path) or {}
            correction_counts.update(collect_correction_types(data))
            review = collect_tense_review(data)
            for key, values in review.items():
                tense_review[key].extend(values)
            file_summaries.append(
                summarize_file(
                    item,
                    ann_path,
                    audit,
                    bool(run_status.get(project_rel(item.path), {}).get("skip", {}).get("ok")),
                )
            )
        else:
            audits.append(
                {
                    "articles": 0,
                    "tokens": 0,
                    "sentences": 0,
                    "empty_sentences": 0,
                    "cleaning_corrections": 0,
                    "cleaning_flags": 0,
                    "blocked_split_suffix_flags": 0,
                    "remaining_split_suffix_artifacts": [],
                    "known_false_merges": [],
                    "known_split_artifacts": [],
                    "suspicious_tokens": [],
                    "past_type_counts": {},
                    "future_type_counts": {},
                    "voice_type_counts": {},
                    "tense_role_counts": {},
                    "other_past_tokens": [],
                    "samples": {},
                }
            )
            file_summaries.append(summarize_file(item, ann_path, audits[-1], False))

    aggregate_doc = PROJECT_ROOT / args.aggregate_out if args.aggregate_out else DOCS_ROOT / f"{TODAY}_annotation_multiland_audit.md"
    duplicate_groups = collect_duplicate_groups(sample)
    aggregate = render_aggregate(sample, file_summaries, audits, correction_counts, tense_review, duplicate_groups)
    aggregate_doc.parent.mkdir(parents=True, exist_ok=True)
    aggregate_doc.write_text(aggregate, encoding="utf-8")
    decision_match = re.search(r"\*\*(GREEN|YELLOW|RED)\*\*", aggregate)
    decision = decision_match.group(1) if decision_match else "UNKNOWN"
    run_doc = DOCS_ROOT / f"{TODAY}_annotation_multiland_audit_run.md"
    run_doc.write_text(render_run_doc(sample_doc, aggregate_doc, audit_paths, sample, test_results, decision), encoding="utf-8")
    print(f"Aggregate report: {project_rel(aggregate_doc)}")
    print(f"Run doc: {project_rel(run_doc)}")
    print(f"Decision: {decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
