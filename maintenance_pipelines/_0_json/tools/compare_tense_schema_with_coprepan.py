#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
COPREPAN_ROOT = Path(r"C:\dev\coprepan")
COPREPAN_ANNOTATED = COPREPAN_ROOT / "json_annotated"
CORAPAN_TRANSCRIPTS = ROOT / "media" / "transcripts"
OUT_DIR = ROOT / "maintenance_pipelines" / "_0_json" / "docs" / "agent-runs" / "audits"
TENSE_KEYS = ("PastType", "FutureType", "VoiceType", "TenseRole", "VerbLemma", "TenseSubtype", "LinkedInfinitiveLemma")


def iter_coprepan_tokens(data: dict[str, Any]):
    for article in data.get("articles", []):
        for field in ("title", "body"):
            for segment in article.get("text", {}).get(field, {}).get("segments") or []:
                for sentence in segment.get("sentences") or []:
                    for token in sentence.get("tokens") or []:
                        yield token


def iter_corapan_tokens(data: dict[str, Any]):
    for segment in data.get("segments", []):
        if not isinstance(segment, dict):
            continue
        for token in segment.get("words") or []:
            if isinstance(token, dict):
                yield token


def scan(root: Path, mode: str) -> dict[str, Any]:
    values: dict[str, Counter[str]] = defaultdict(Counter)
    combos: Counter[str] = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    files = 0
    tokens = 0
    for path in sorted(root.rglob("*.json")):
        files += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        iterator = iter_coprepan_tokens(data) if mode == "coprepan" else iter_corapan_tokens(data)
        for token in iterator:
            tokens += 1
            morph = token.get("morph") if isinstance(token.get("morph"), dict) else {}
            for key in TENSE_KEYS:
                if key in morph:
                    values[key][str(morph[key])] += 1
            if any(key in morph for key in TENSE_KEYS[:4]):
                combo = {key: str(morph[key]) for key in TENSE_KEYS if key in morph}
                combo_key = json.dumps(combo, ensure_ascii=False, sort_keys=True)
                combos[combo_key] += 1
                if len(examples[combo_key]) < 3:
                    examples[combo_key].append(
                        {
                            "file": str(path.relative_to(root)).replace("\\", "/"),
                            "token": token.get("text"),
                            "lemma": token.get("lemma"),
                            "token_id": token.get("token_id"),
                        }
                    )
    return {
        "files": files,
        "tokens": tokens,
        "values": {key: dict(counter.most_common()) for key, counter in values.items()},
        "combinations": {key: count for key, count in combos.most_common()},
        "examples": examples,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("before", "after"), required=True)
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    cop = scan(COPREPAN_ANNOTATED, "coprepan")
    cor = scan(CORAPAN_TRANSCRIPTS, "corapan")
    diff: dict[str, Any] = {
        "phase": args.phase,
        "coprepan": {"source": str(COPREPAN_ANNOTATED), "files": cop["files"], "tokens": cop["tokens"]},
        "corapan": {"source": str(CORAPAN_TRANSCRIPTS), "files": cor["files"], "tokens": cor["tokens"]},
        "keys": {},
        "hard_failures": [],
    }
    for key in ("PastType", "FutureType", "VoiceType", "TenseRole"):
        cop_values = set(cop["values"].get(key, {}))
        cor_values = set(cor["values"].get(key, {}))
        diff["keys"][key] = {
            "coprepan_values": cop["values"].get(key, {}),
            "corapan_values": cor["values"].get(key, {}),
            "corapan_only": sorted(cor_values - cop_values),
            "coprepan_only": sorted(cop_values - cor_values),
        }

    cor_roles = cor["values"].get("TenseRole", {})
    if cor_roles.get("finite_past", 0) > 0:
        diff["hard_failures"].append(f"CORAPAN TenseRole=finite_past count {cor_roles['finite_past']}")
    if diff["keys"]["TenseRole"]["corapan_only"]:
        diff["hard_failures"].append(f"CORAPAN-only TenseRole values: {diff['keys']['TenseRole']['corapan_only']}")
    if cor_roles.get("auxiliary", 0) > 0:
        diff["hard_failures"].append(f"CORAPAN legacy TenseRole=auxiliary count {cor_roles['auxiliary']}")

    out_json = OUT_DIR / f"2026-06-14_corapan_vs_coprepan_tense_schema_diff_{args.phase}.json"
    out_md = OUT_DIR / f"2026-06-14_corapan_vs_coprepan_tense_schema_diff_{args.phase}.md"
    out_json.write_text(json.dumps(diff, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        f"# CORAPAN vs CO.PRE.PAN Tense Schema Diff ({args.phase})",
        "",
        f"CO.PRE.PAN files: {cop['files']}",
        f"CORAPAN files: {cor['files']}",
        "",
        "## Values",
        "",
    ]
    for key, row in diff["keys"].items():
        lines.append(f"### {key}")
        lines.append(f"- CORAPAN-only: `{row['corapan_only']}`")
        lines.append(f"- CO.PRE.PAN-only: `{row['coprepan_only']}`")
        lines.append("")
    lines.append("## Hard Failures")
    lines.append("")
    if diff["hard_failures"]:
        lines.extend(f"- {failure}" for failure in diff["hard_failures"])
    else:
        lines.append("None.")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"json": str(out_json), "md": str(out_md), "hard_failures": diff["hard_failures"]}, indent=2))
    return 0 if not diff["hard_failures"] or args.phase == "before" else 1


if __name__ == "__main__":
    raise SystemExit(main())
