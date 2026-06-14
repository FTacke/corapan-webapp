#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
ANNOTATED_ROOT = PROJECT_ROOT / "json_annotated"

KNOWN_FALSE_MERGES = {"creatividado", "dispuestosa", "Peddial"}
KNOWN_SPLIT_ARTIFACTS = {
    "Internacion al",
    "constitucion al",
    "obligatori o",
    "Pragmatism o",
    "presidenci al",
    "construyend o",
    "confrontativ o",
    "multicultur al",
    "Constantin o",
    "iconográfic o",
}
SPLIT_SUFFIX_CANDIDATE_RE = re.compile(
    r"\b(?P<prefix>[0-9A-Za-zÀ-ÖØ-öø-ÿÑñÜü]{4,})\s+(?P<suffix>o|a|al|lo|la)\b"
)
SUSPICIOUS_O_ENDINGS = (
    "ari",
    "atori",
    "ism",
    "tiv",
    "siv",
    "ctiv",
    "iv",
    "ient",
    "amient",
    "imient",
    "ambi",
    "ciend",
    "giend",
    "yend",
    "end",
    "and",
    "ad",
    "id",
    "est",
    "arl",
    "erl",
    "irl",
    "fic",
    "grafic",
    "gráfic",
    "ografic",
    "ográfic",
)
SUSPICIOUS_AL_ENDINGS = (
    "cion",
    "ción",
    "ci",
    "nci",
    "enci",
    "anci",
    "ici",
    "oci",
    "uci",
    "cultur",
    "estructur",
    "natur",
    "tur",
    "ur",
)


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def collect_files(country: str | None, file_arg: str | None, limit: int | None) -> list[Path]:
    if file_arg:
        files = [resolve_path(file_arg)]
    else:
        root = ANNOTATED_ROOT / country.upper() if country else ANNOTATED_ROOT
        files = sorted(root.rglob("*.ann.json")) if root.exists() else []
    return files[:limit] if limit is not None else files


def article_language(article: dict[str, Any]) -> str:
    return str(article.get("metadata", {}).get("language") or "es").strip().lower()


def is_unsupported(article: dict[str, Any]) -> bool:
    return article_language(article) != "es" or article.get("annotation_status") == "skipped_unsupported_language"


def article_title(article: dict[str, Any]) -> str:
    title = article.get("text", {}).get("title", {})
    if isinstance(title, dict):
        return str(title.get("raw") or title.get("clean") or "")[:160]
    return ""


def article_url(article: dict[str, Any]) -> str:
    metadata = article.get("metadata", {})
    for key in ("canonical_url", "url", "source_url"):
        if metadata.get(key):
            return str(metadata[key])
    return ""


def iter_field_objects(data: dict[str, Any], *, include_unsupported: bool = False):
    for a_idx, article in enumerate(data.get("articles", [])):
        if is_unsupported(article) and not include_unsupported:
            continue
        for field in ("title", "body"):
            field_obj = article.get("text", {}).get(field, {})
            if isinstance(field_obj, dict):
                yield a_idx, field, field_obj


def iter_sentences(data: dict[str, Any]):
    for a_idx, field, field_obj in iter_field_objects(data):
        for segment in field_obj.get("segments") or []:
            for sentence in segment.get("sentences") or []:
                yield a_idx, field, field_obj, segment, sentence


def iter_tokens_with_context(data: dict[str, Any]):
    for a_idx, field, field_obj, segment, sentence in iter_sentences(data):
        tokens = sentence.get("tokens") or []
        context = " ".join(token.get("text", "") for token in tokens)
        for idx, token in enumerate(tokens):
            yield a_idx, field, field_obj, segment, sentence, idx, token, context


def token_signature(token: dict[str, Any]) -> str:
    return f"{token.get('text')}[{token.get('token_id', '')}]"


def is_remaining_split_artifact(prefix: str, suffix: str) -> bool:
    prefix_l = prefix.lower()
    if suffix == "o":
        return prefix_l.endswith(SUSPICIOUS_O_ENDINGS) and not prefix_l.endswith("idad")
    if suffix == "al":
        return prefix_l.endswith(SUSPICIOUS_AL_ENDINGS)
    if suffix in {"lo", "la"}:
        return prefix_l.endswith(("arl", "erl", "irl"))
    return False


def is_likely_normal_proper_name_al(text: str) -> bool:
    parts = text.split()
    return len(parts) == 2 and parts[1].lower() == "al" and parts[0][:1].isupper()


def context_for_match(text: str, start: int, end: int, width: int = 60) -> str:
    left = max(0, start - width)
    right = min(len(text), end + width)
    prefix = "..." if left > 0 else ""
    suffix = "..." if right < len(text) else ""
    return prefix + " ".join(text[left:right].split()) + suffix


def find_remaining_split_artifacts(clean: str) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for match in SPLIT_SUFFIX_CANDIDATE_RE.finditer(clean):
        prefix = match.group("prefix")
        suffix = match.group("suffix")
        if not is_remaining_split_artifact(prefix, suffix):
            continue
        artifacts.append(
            {
                "text": match.group(0),
                "char_start": match.start(),
                "char_end": match.end(),
                "context": context_for_match(clean, match.start(), match.end()),
            }
        )
    return artifacts


def _vals(morph: dict[str, Any], key: str) -> set[str]:
    value = morph.get(key)
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(v) for v in value}
    return {str(value)}


def audit_file(path: Path, sample_tense: int) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, Any] = {
        "file": str(path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path),
        "articles": len(data.get("articles", [])),
        "annotated_articles": 0,
        "unsupported_language_articles": 0,
        "skipped_articles": 0,
        "mixed_language_file": False,
        "skipped_unsupported_language_articles": [],
        "tokens": 0,
        "sentences": 0,
        "empty_sentences": 0,
        "body_segment_counts": [],
        "cleaning_corrections": 0,
        "cleaning_flags": 0,
        "blocked_split_suffix_flags": 0,
        "blocked_likely_normal_proper_name_al": 0,
        "flag_warnings": [],
        "known_false_merges": [],
        "known_split_artifacts": [],
        "remaining_split_suffix_artifacts": [],
        "suspicious_tokens": [],
        "past_type_counts": Counter(),
        "future_type_counts": Counter(),
        "voice_type_counts": Counter(),
        "tense_role_counts": Counter(),
        "samples": defaultdict(list),
        "possible_misclassifications": [],
        "other_past_tokens": [],
        "passive_lexical_participles": [],
        "ser_estar_participle_candidates": [],
        "ann_meta": data.get("ann_meta", {}),
    }

    languages = []
    for a_idx, article in enumerate(data.get("articles", [])):
        language = article_language(article)
        languages.append(language)
        if is_unsupported(article):
            result["unsupported_language_articles"] += 1
            result["skipped_articles"] += 1
            result["skipped_unsupported_language_articles"].append(
                {
                    "article_index": a_idx,
                    "language": language,
                    "title": article_title(article),
                    "url": article_url(article),
                }
            )
        else:
            result["annotated_articles"] += 1
    result["mixed_language_file"] = len(set(languages)) > 1

    for _a_idx, field, field_obj in iter_field_objects(data):
        if field == "body":
            result["body_segment_counts"].append(len(field_obj.get("segments") or []))
        report = field_obj.get("cleaning_report") or {}
        corrections = report.get("corrections") or []
        flagged = report.get("flagged") or []
        result["cleaning_corrections"] += len(corrections)
        result["cleaning_flags"] += len(flagged)
        for item in flagged:
            if item.get("type") != "blocked_split_suffix_merge":
                continue
            if is_likely_normal_proper_name_al(str(item.get("text", ""))):
                result["blocked_likely_normal_proper_name_al"] += 1
            else:
                result["blocked_split_suffix_flags"] += 1
        clean = field_obj.get("clean", "")
        for bad in KNOWN_FALSE_MERGES:
            if bad in clean:
                result["known_false_merges"].append({"field": field, "text": bad})
        for artifact in KNOWN_SPLIT_ARTIFACTS:
            if artifact in clean:
                result["known_split_artifacts"].append({"field": field, "text": artifact})
        for artifact in find_remaining_split_artifacts(clean):
            artifact["field"] = field
            result["remaining_split_suffix_artifacts"].append(artifact)

    for _a_idx, _field, _field_obj, _segment, sentence in iter_sentences(data):
        result["sentences"] += 1
        tokens = sentence.get("tokens") or []
        if not tokens:
            result["empty_sentences"] += 1
            continue
        context = " ".join(token.get("text", "") for token in tokens)
        for idx, token in enumerate(tokens):
            morph = token.get("morph") if isinstance(token.get("morph"), dict) else {}
            lemma = token.get("lemma", "").lower()
            if lemma not in {"ser", "estar"} or "Fin" not in _vals(morph, "VerbForm"):
                continue
            for j in range(idx + 1, min(len(tokens), idx + 6)):
                gap = tokens[idx + 1 : j]
                if any("Fin" in _vals((g.get("morph") if isinstance(g.get("morph"), dict) else {}), "VerbForm") for g in gap):
                    break
                candidate_morph = tokens[j].get("morph") if isinstance(tokens[j].get("morph"), dict) else {}
                if "Part" in _vals(candidate_morph, "VerbForm"):
                    result["ser_estar_participle_candidates"].append(
                        {
                            "aux": token_signature(token),
                            "participle": token_signature(tokens[j]),
                            "context": context,
                        }
                    )
                    break

    for _a_idx, field, _field_obj, _segment, _sentence, _idx, token, context in iter_tokens_with_context(data):
        result["tokens"] += 1
        text = token.get("text", "")
        norm = token.get("norm", "")
        lemma = token.get("lemma", "")
        morph = token.get("morph") if isinstance(token.get("morph"), dict) else {}
        if any(bad.lower() == text.lower() for bad in KNOWN_FALSE_MERGES) or (norm and len(norm) > 35):
            result["suspicious_tokens"].append({"token": token_signature(token), "norm": norm, "lemma": lemma, "field": field})
        if "PastType" in morph:
            past_type = morph["PastType"]
            result["past_type_counts"][past_type] += 1
            if past_type == "otherPast":
                result["other_past_tokens"].append({"token": token_signature(token), "context": context})
            if len(result["samples"][past_type]) < sample_tense:
                result["samples"][past_type].append({"token": token_signature(token), "context": context})
        if "FutureType" in morph:
            future_type = morph["FutureType"]
            result["future_type_counts"][future_type] += 1
            if len(result["samples"]["FutureType"]) < sample_tense:
                result["samples"]["FutureType"].append({"token": token_signature(token), "context": context})
        if "VoiceType" in morph:
            result["voice_type_counts"][morph["VoiceType"]] += 1
        if "TenseRole" in morph:
            result["tense_role_counts"][morph["TenseRole"]] += 1
        if morph.get("TenseRole") == "lexical_participle" and morph.get("VoiceType"):
            result["passive_lexical_participles"].append({"token": token_signature(token), "context": context})
        if text.lower() in {"fue", "fueron"} and morph.get("PastType") == "otherPast":
            result["possible_misclassifications"].append(
                {"type": "finite_ser_otherPast", "token": token_signature(token), "context": context}
            )

    for key in ("past_type_counts", "future_type_counts", "voice_type_counts", "tense_role_counts"):
        result[key] = dict(result[key])
    result["samples"] = dict(result["samples"])
    flag_threshold = max(10, int(result["tokens"] * 0.05))
    if result["blocked_split_suffix_flags"] > flag_threshold:
        result["flag_warnings"].append(
            f"blocked_split_suffix_merge high: {result['blocked_split_suffix_flags']} > {flag_threshold}"
        )
    return result


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = ["# Annotation Quality Audit", ""]
    for result in results:
        lines.extend(
            [
                f"## {result['file']}",
                "",
                f"- Articles: {result['articles']}",
                f"- Annotated articles: {result['annotated_articles']}",
                f"- Unsupported-language articles: {result['unsupported_language_articles']}",
                f"- Skipped articles: {result['skipped_articles']}",
                f"- Mixed language file: {str(result['mixed_language_file']).lower()}",
                f"- Sentences: {result['sentences']}",
                f"- Empty sentences: {result['empty_sentences']}",
                f"- Tokens: {result['tokens']}",
                f"- Body segment counts: {result['body_segment_counts']}",
                f"- Cleaning corrections: {result['cleaning_corrections']}",
                f"- Cleaning flags: {result['cleaning_flags']}",
                f"- Blocked split-suffix flags: {result['blocked_split_suffix_flags']}",
                f"- Blocked likely normal proper-name + al: {result['blocked_likely_normal_proper_name_al']}",
                f"- Known false merges: {len(result['known_false_merges'])}",
                f"- Known split artifacts: {len(result['known_split_artifacts'])}",
                f"- Remaining split-suffix artifacts: {len(result['remaining_split_suffix_artifacts'])}",
                f"- Pipeline version: `{result['ann_meta'].get('pipeline_version', '')}`",
                f"- Clean version: `{result['ann_meta'].get('stages', {}).get('clean', {}).get('version', '')}`",
                f"- Validation version: `{result['ann_meta'].get('validation_version', '')}`",
                "",
            ]
        )
        if result["skipped_unsupported_language_articles"]:
            lines.extend(["### Skipped Unsupported-Language Articles", ""])
            for item in result["skipped_unsupported_language_articles"]:
                lines.append(
                    f"- article {item['article_index']}, language `{item['language']}`: {item['title']} {item['url']}".rstrip()
                )
            lines.append("")
        if result["flag_warnings"]:
            lines.extend(["### Flag Warnings", ""])
            for warning in result["flag_warnings"]:
                lines.append(f"- {warning}")
            lines.append("")
        lines.extend(["### Remaining Split-Suffix Artifacts", ""])
        if result["remaining_split_suffix_artifacts"]:
            for item in result["remaining_split_suffix_artifacts"][:25]:
                lines.append(f"- `{item['text']}`: {item['context']}")
        else:
            lines.append("- none")
        for title, key in (
            ("PastType Counts", "past_type_counts"),
            ("FutureType Counts", "future_type_counts"),
            ("VoiceType Counts", "voice_type_counts"),
            ("TenseRole Counts", "tense_role_counts"),
        ):
            lines.extend(["", f"### {title}", ""])
            if result[key]:
                for name, value in sorted(result[key].items()):
                    lines.append(f"- `{name}`: {value}")
            else:
                lines.append("- none")
        lines.extend(["", "### ser/estar + Participle Candidates", ""])
        for item in result["ser_estar_participle_candidates"][:25]:
            lines.append(f"- `{item['aux']}` + `{item['participle']}`: {item['context']}")
        if not result["ser_estar_participle_candidates"]:
            lines.append("- none")
        lines.extend(["", "### Passive/Resultative Lexical Participles", ""])
        for item in result["passive_lexical_participles"][:25]:
            lines.append(f"- `{item['token']}`: {item['context']}")
        if not result["passive_lexical_participles"]:
            lines.append("- none")
        lines.extend(["", "### Remaining otherPast Tokens", ""])
        for item in result["other_past_tokens"][:25]:
            lines.append(f"- `{item['token']}`: {item['context']}")
        if not result["other_past_tokens"]:
            lines.append("- none")
        lines.extend(["", "### Suspicious Tokens", ""])
        for item in result["suspicious_tokens"][:25]:
            lines.append(f"- `{item['token']}` norm=`{item['norm']}` lemma=`{item['lemma']}`")
        if not result["suspicious_tokens"]:
            lines.append("- none")
        lines.extend(["", "### Possible Misclassifications", ""])
        for item in result["possible_misclassifications"][:25]:
            lines.append(f"- `{item['type']}` at `{item['token']}`: {item['context']}")
        if not result["possible_misclassifications"]:
            lines.append("- none")
        lines.extend(["", "### Tense Samples", ""])
        for category, samples in sorted(result["samples"].items()):
            lines.append(f"#### {category}")
            for sample in samples[:10]:
                lines.append(f"- `{sample['token']}`: {sample['context']}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Coprepan annotation quality.")
    parser.add_argument("--file", type=str, default=None)
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
        print("No annotated files found.")
        return 1
    results = [audit_file(path, args.sample_tense) for path in files]
    markdown = render_markdown(results)
    if args.out:
        out = resolve_path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    if args.json_out:
        out_json = resolve_path(args.json_out)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
