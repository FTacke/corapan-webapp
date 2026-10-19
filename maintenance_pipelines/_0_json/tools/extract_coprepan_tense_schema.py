#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

CORAPAN_ROOT = Path(__file__).resolve().parents[3]
COPREPAN_ROOT = Path(r"C:\dev\coprepan")
COPREPAN_ANNOTATED = COPREPAN_ROOT / "json_annotated"
OUT_DIR = CORAPAN_ROOT / "maintenance_pipelines" / "_0_json" / "docs" / "agent-runs" / "audits"
OUT_JSON = OUT_DIR / "2026-06-14_coprepan_tense_reference_schema.json"
OUT_MD = OUT_DIR / "2026-06-14_coprepan_tense_reference_schema.md"

TENSE_KEYS = (
    "Tense",
    "VerbForm",
    "Mood",
    "PastType",
    "FutureType",
    "VoiceType",
    "TenseRole",
    "VerbLemma",
    "TenseSubtype",
    "LinkedInfinitive",
    "LinkedInfinitiveLemma",
    "LinkedInfinitiveTokenId",
)


def iter_tokens(data: dict[str, Any]):
    for article in data.get("articles", []):
        for field in ("title", "body"):
            for segment in article.get("text", {}).get(field, {}).get("segments") or []:
                for sentence in segment.get("sentences") or []:
                    tokens = sentence.get("tokens") or []
                    for idx, token in enumerate(tokens):
                        yield token, tokens, idx


def context(tokens: list[dict[str, Any]], idx: int) -> str:
    return " ".join(str(tok.get("text") or "") for tok in tokens[max(0, idx - 5) : idx + 6])


def scan() -> dict[str, Any]:
    morph_keys: dict[str, Counter[str]] = defaultdict(Counter)
    combos: Counter[str] = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    files = 0
    tokens_total = 0
    tense_tokens = 0
    read_errors: list[dict[str, str]] = []

    for path in sorted(COPREPAN_ANNOTATED.rglob("*.json")):
        files += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            read_errors.append({"file": str(path), "error": str(exc)})
            continue
        for token, tokens, idx in iter_tokens(data):
            tokens_total += 1
            morph = token.get("morph") if isinstance(token.get("morph"), dict) else {}
            for key, value in morph.items():
                morph_keys[key][str(value)] += 1
            if not any(key in morph for key in TENSE_KEYS[3:]):
                continue
            tense_tokens += 1
            combo_obj = {key: str(morph[key]) for key in TENSE_KEYS if key in morph}
            combo_key = json.dumps(combo_obj, ensure_ascii=False, sort_keys=True)
            combos[combo_key] += 1
            if len(examples[combo_key]) < 5:
                examples[combo_key].append(
                    {
                        "token": token.get("text"),
                        "lemma": token.get("lemma"),
                        "token_id": token.get("token_id"),
                        "context": context(tokens, idx),
                        "file": str(path.relative_to(COPREPAN_ROOT)).replace("\\", "/"),
                    }
                )

    combo_rows = []
    for combo_key, count in combos.most_common():
        combo_rows.append(
            {
                "count": count,
                "features": json.loads(combo_key),
                "examples": examples[combo_key],
            }
        )

    return {
        "source": str(COPREPAN_ANNOTATED),
        "files": files,
        "tokens_total": tokens_total,
        "tense_tokens": tense_tokens,
        "read_errors": read_errors,
        "morph_keys": {key: dict(counter.most_common()) for key, counter in sorted(morph_keys.items())},
        "allowed_values": {
            key: sorted(morph_keys.get(key, {}).keys())
            for key in ("PastType", "FutureType", "VoiceType", "TenseRole")
        },
        "combinations": combo_rows,
    }


def write_md(schema: dict[str, Any]) -> None:
    lines = [
        "# CO.PRE.PAN Tense Reference Schema",
        "",
        f"Source: `{schema['source']}`",
        "",
        f"Files scanned: {schema['files']}",
        f"Tokens scanned: {schema['tokens_total']}",
        f"Tense-bearing tokens: {schema['tense_tokens']}",
        "",
        "## Allowed Values",
        "",
    ]
    for key in ("PastType", "FutureType", "VoiceType", "TenseRole"):
        lines.append(f"### {key}")
        values = schema["morph_keys"].get(key, {})
        if not values:
            lines.append("")
            lines.append("None.")
            lines.append("")
            continue
        for value, count in values.items():
            lines.append(f"- `{value}`: {count}")
        lines.append("")

    lines.extend(["## Typical Combinations", ""])
    for row in schema["combinations"][:80]:
        features = ", ".join(f"`{k}={v}`" for k, v in row["features"].items())
        sample = row["examples"][0] if row["examples"] else {}
        lines.append(f"- {row['count']}: {features}")
        if sample:
            lines.append(f"  Example: `{sample.get('token')}` / `{sample.get('lemma')}` in `{sample.get('file')}`")
    lines.append("")
    lines.append("## Code Reference")
    lines.append("")
    lines.append("Rules were checked against `C:/dev/coprepan/scripts/annotation/lib/tense_rules.py`.")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    schema = scan()
    OUT_JSON.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(schema)
    print(json.dumps({"json": str(OUT_JSON), "md": str(OUT_MD), "files": schema["files"]}, indent=2))
    return 0 if not schema["read_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
