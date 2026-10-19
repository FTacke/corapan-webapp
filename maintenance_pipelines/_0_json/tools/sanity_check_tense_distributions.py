#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
TRANSCRIPTS = ROOT / "media" / "transcripts"
REF_SCHEMA = ROOT / "maintenance_pipelines" / "_0_json" / "docs" / "agent-runs" / "audits" / "2026-06-14_coprepan_tense_reference_schema.json"
OUT_JSON = ROOT / "maintenance_pipelines" / "_0_json" / "docs" / "agent-runs" / "2026-06-14_tense_distribution_sanity_after_v3_2.json"
OUT_MD = ROOT / "maintenance_pipelines" / "_0_json" / "docs" / "agent-runs" / "2026-06-14_tense_distribution_sanity_after_v3_2.md"

ROLE_KEYS_REQUIRING_VERBLEMMA = {"finite_verb", "copula_or_aux", "aux_passive", "copula_resultative"}
OLD_CORAPAN_ROLES = {"finite_past", "auxiliary", "compound_participle", "future_infinitive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def context(words: list[dict[str, Any]], idx: int) -> str:
    return " ".join(str(w.get("text") or "") for w in words[max(0, idx - 5): idx + 6])


def add_example(examples: dict[str, list[dict[str, Any]]], key: str, value: str, file_rel: str, word: dict[str, Any], words: list[dict[str, Any]], idx: int) -> None:
    slot = f"{key}={value}"
    if len(examples[slot]) >= 5:
        return
    examples[slot].append(
        {
            "file": file_rel,
            "token": word.get("text"),
            "lemma": word.get("lemma"),
            "token_id": word.get("token_id"),
            "context": context(words, idx),
        }
    )


def main() -> int:
    ref = load_json(REF_SCHEMA)
    allowed = ref.get("allowed_values", {})
    allowed_roles = set(allowed.get("TenseRole", []))
    allowed_voice = set(allowed.get("VoiceType", []))
    allowed_past = set(allowed.get("PastType", []))
    allowed_future = set(allowed.get("FutureType", []))

    counts = {
        "PastType": Counter(),
        "FutureType": Counter(),
        "VoiceType": Counter(),
        "TenseRole": Counter(),
        "VerbLemma": Counter(),
    }
    combos = {
        "Tense+VerbForm+PastType+TenseRole": Counter(),
        "Tense+VerbForm+VoiceType+TenseRole": Counter(),
        "FutureType+TenseRole": Counter(),
        "PastType+VoiceType+TenseRole": Counter(),
    }
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    hard_failures: list[str] = []
    files_with_empty_tense_meta: list[str] = []
    files_with_no_tense_tokens: list[str] = []
    missing_verblemma: list[dict[str, Any]] = []
    old_role_tokens: list[dict[str, Any]] = []
    resultative_old: list[dict[str, Any]] = []
    passive_aux_legacy: list[dict[str, Any]] = []
    corapan_only_roles = Counter()
    incompatible_values = defaultdict(Counter)

    files = sorted(TRANSCRIPTS.rglob("*.json"))
    total_tokens = 0
    tense_tokens = 0
    for path in files:
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        data = load_json(path)
        file_tense_tokens = 0
        for seg in data.get("segments") or []:
            if not isinstance(seg, dict):
                continue
            words = seg.get("words") if isinstance(seg.get("words"), list) else []
            for idx, word in enumerate(words):
                total_tokens += 1
                morph = word.get("morph") if isinstance(word.get("morph"), dict) else {}
                if not any(key in morph for key in ("PastType", "FutureType", "VoiceType", "TenseRole", "VerbLemma")):
                    continue
                tense_tokens += 1
                file_tense_tokens += 1
                for key in counts:
                    if key in morph:
                        value = str(morph[key])
                        counts[key][value] += 1
                        add_example(examples, key, value, rel, word, words, idx)
                role = str(morph.get("TenseRole", ""))
                voice = str(morph.get("VoiceType", ""))
                past = str(morph.get("PastType", ""))
                future = str(morph.get("FutureType", ""))
                tense = str(morph.get("Tense", ""))
                verbform = str(morph.get("VerbForm", ""))
                if past or role:
                    combos["Tense+VerbForm+PastType+TenseRole"][json.dumps({"Tense": tense, "VerbForm": verbform, "PastType": past, "TenseRole": role}, sort_keys=True)] += 1
                if voice or role:
                    combos["Tense+VerbForm+VoiceType+TenseRole"][json.dumps({"Tense": tense, "VerbForm": verbform, "VoiceType": voice, "TenseRole": role}, sort_keys=True)] += 1
                if future:
                    combos["FutureType+TenseRole"][json.dumps({"FutureType": future, "TenseRole": role}, sort_keys=True)] += 1
                if past or voice or role:
                    combos["PastType+VoiceType+TenseRole"][json.dumps({"PastType": past, "VoiceType": voice, "TenseRole": role}, sort_keys=True)] += 1

                if role in OLD_CORAPAN_ROLES:
                    old_role_tokens.append({"file": rel, "token_id": word.get("token_id"), "role": role, "token": word.get("text")})
                if role and role not in allowed_roles:
                    corapan_only_roles[role] += 1
                if voice == "resultative":
                    resultative_old.append({"file": rel, "token_id": word.get("token_id"), "token": word.get("text")})
                if voice and voice not in allowed_voice:
                    incompatible_values["VoiceType"][voice] += 1
                if past and past not in allowed_past:
                    incompatible_values["PastType"][past] += 1
                if future and future not in allowed_future:
                    incompatible_values["FutureType"][future] += 1
                if role in ROLE_KEYS_REQUIRING_VERBLEMMA and not morph.get("VerbLemma"):
                    missing_verblemma.append({"file": rel, "token_id": word.get("token_id"), "role": role, "token": word.get("text")})
                if role == "auxiliary" and voice == "passive":
                    passive_aux_legacy.append({"file": rel, "token_id": word.get("token_id"), "token": word.get("text")})
        if file_tense_tokens == 0:
            files_with_no_tense_tokens.append(rel)
        if file_tense_tokens < 5:
            files_with_empty_tense_meta.append(rel)

    if old_role_tokens:
        hard_failures.append(f"old CORAPAN TenseRole tokens: {len(old_role_tokens)}")
    if corapan_only_roles:
        hard_failures.append(f"CORAPAN-only TenseRole values: {dict(corapan_only_roles)}")
    if missing_verblemma:
        hard_failures.append(f"missing VerbLemma on CO.PRE.PAN-style tense roles: {len(missing_verblemma)}")
    if passive_aux_legacy:
        hard_failures.append(f"legacy passive auxiliary labels: {len(passive_aux_legacy)}")
    if resultative_old:
        hard_failures.append(f"legacy VoiceType=resultative tokens: {len(resultative_old)}")
    for key, counter in incompatible_values.items():
        if counter:
            hard_failures.append(f"incompatible {key} values: {dict(counter)}")

    result = {
        "files": len(files),
        "tokens_total": total_tokens,
        "tense_tokens": tense_tokens,
        "counts": {key: dict(counter.most_common()) for key, counter in counts.items()},
        "combinations": {key: dict(counter.most_common(100)) for key, counter in combos.items()},
        "examples": examples,
        "files_with_no_tense_tokens": files_with_no_tense_tokens,
        "files_with_sparse_tense_meta": files_with_empty_tense_meta,
        "old_role_tokens_sample": old_role_tokens[:20],
        "missing_verblemma_sample": missing_verblemma[:20],
        "hard_failures": hard_failures,
        "shared_filters_usable": not hard_failures,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Tense Distribution Sanity After v3.2",
        "",
        f"Files: {len(files)}",
        f"Tokens: {total_tokens}",
        f"Tense-bearing tokens: {tense_tokens}",
        "",
        "## Counts",
        "",
    ]
    for key in ("PastType", "FutureType", "VoiceType", "TenseRole"):
        lines.append(f"### {key}")
        for value, count in counts[key].most_common():
            lines.append(f"- `{value}`: {count}")
        lines.append("")
    lines.extend(["## Hard Failures", ""])
    lines.append("None." if not hard_failures else "\n".join(f"- {failure}" for failure in hard_failures))
    lines.extend([
        "",
        "## Shared Filter Decision",
        "",
        "The same morph filters can be used for CO.PRE.PAN and CORAPAN." if not hard_failures else "Shared filters need review because hard failures were detected.",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON), "md": str(OUT_MD), "hard_failures": hard_failures}, indent=2))
    return 0 if not hard_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
