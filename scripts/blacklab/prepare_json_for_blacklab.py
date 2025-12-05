#!/usr/bin/env python3
"""Prepare production v3 JSON transcripts for BlackLab JSON indexing.

For each JSON in media/transcripts/**, this script writes a file to
data/blacklab_export/json_ready/<basename>.json with a top-level 'tokens'
array where each token contains the flattened fields that the BLF expects.

This preserves document-level metadata at top-level and copies speaker info
from segment objects into each token.

Usage: python scripts/prepare_json_for_blacklab.py --in media/transcripts --out data/blacklab_export/json_ready
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def flatten_doc(infile: Path) -> Dict[str, Any]:
    with infile.open(encoding="utf-8") as fh:
        doc = json.load(fh)

    # Keep top-level metadata
    out = {
        k: doc.get(k, "")
        for k in (
            "file_id",
            "filename",
            "date",
            "country_code",
            "country_scope",
            "country_parent_code",
            "country_region_code",
            "city",
            "radio",
            "audio_path",
        )
    }

    tokens = []

    for segment in doc.get("segments", []):
        # speaker info might be in segment['speaker'] or separate keys
        seg_speaker = segment.get("speaker") or {}
        speaker_code = seg_speaker.get("code") or segment.get("speaker_code", "")
        speaker_type = seg_speaker.get("speaker_type") or segment.get(
            "speaker_type", ""
        )
        speaker_sex = seg_speaker.get("speaker_sex") or segment.get("speaker_sex", "")
        speaker_mode = seg_speaker.get("speaker_mode") or segment.get(
            "speaker_mode", ""
        )
        speaker_discourse = seg_speaker.get("speaker_discourse") or segment.get(
            "speaker_discourse", ""
        )

        for w in segment.get("words", []):
            morph = w.get("morph") or {}

            # Support legacy PastType/FutureType in morph or top-level token
            past = (
                morph.get("PastType")
                or morph.get("past_type")
                or w.get("past_type")
                or morph.get("Past_Tense_Type")
                or w.get("Past_Tense_Type")
                or ""
            )
            future = (
                morph.get("FutureType")
                or morph.get("future_type")
                or w.get("future_type")
                or morph.get("Future_Type")
                or w.get("FutureType")
                or ""
            )

            token = {
                "word": w.get("text", ""),
                "norm": w.get("norm", ""),
                "lemma": w.get("lemma", ""),
                "pos": w.get("pos", ""),
                "tense": morph.get("Tense", "") or morph.get("tense", ""),
                "mood": morph.get("Mood", "") or morph.get("mood", ""),
                "person": morph.get("Person", "") or morph.get("person", ""),
                "number": morph.get("Number", "") or morph.get("number", ""),
                "aspect": morph.get("Aspect", "") or morph.get("aspect", ""),
                "PastType": past,
                "FutureType": future,
                "tokid": w.get("token_id", ""),
                "start_ms": w.get("start_ms", ""),
                "end_ms": w.get("end_ms", ""),
                "sentence_id": w.get("sentence_id", ""),
                "utterance_id": w.get("utterance_id", ""),
                "speaker_code": speaker_code,
                "speaker_type": speaker_type,
                "speaker_sex": speaker_sex,
                "speaker_mode": speaker_mode,
                "speaker_discourse": speaker_discourse,
                # copy some doc-level fields into each token so BLF can forward-index
                "file_id": out.get("file_id", ""),
                "country_code": out.get("country_code", ""),
                "country_scope": out.get("country_scope", ""),
                "country_parent_code": out.get("country_parent_code", ""),
                "country_region_code": out.get("country_region_code", ""),
                "city": out.get("city", ""),
                "radio": out.get("radio", ""),
                "date": out.get("date", ""),
                "audio_path": out.get("audio_path", ""),
            }
            tokens.append(token)

    out["tokens"] = tokens
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_dir", required=True)
    parser.add_argument("--out", dest="out_dir", required=True)
    parser.add_argument(
        "--limit", type=int, default=0, help="optional limit of files to process"
    )
    args = parser.parse_args()

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(in_dir.rglob("*.json"))
    if args.limit and args.limit > 0:
        json_files = json_files[: args.limit]

    print(f"Found {len(json_files)} json files, writing to {out_dir}")

    processed = 0
    for jf in json_files:
        try:
            flattened = flatten_doc(jf)
            out_path = out_dir / (jf.stem + ".json")
            with out_path.open("w", encoding="utf-8") as of:
                json.dump(flattened, of, ensure_ascii=False)
            processed += 1
        except Exception as e:
            print("ERROR", jf, e)

    print(f"Wrote {processed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
