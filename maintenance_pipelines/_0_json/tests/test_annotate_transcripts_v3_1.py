from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "02_annotate_transcripts_v3.py"
AUDIT_SCRIPT = Path(__file__).resolve().parents[1] / "audit_transcript_annotation_quality.py"


def load_module():
    spec = importlib.util.spec_from_file_location("corapan_annotator_v3_1", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_audit_module():
    spec = importlib.util.spec_from_file_location("corapan_transcript_audit", AUDIT_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_data() -> dict:
    return {
        "file_id": "TEST_2026-01-01",
        "filename": "TEST_2026-01-01.mp3",
        "date": "2026-01-01",
        "country_code": "ARG",
        "radio": "Unit Test Radio",
        "segments": [
            {
                "utt_start_ms": 1000,
                "utt_end_ms": 2600,
                "speaker_code": "none",
                "speaker": {"code": "none"},
                "words": [
                    {
                        "text": "habia",
                        "token_id": "ARGexisting001",
                        "start_ms": 1000,
                        "end_ms": 1200,
                        "norm": "habia",
                        "lemma": "haber",
                        "pos": "AUX",
                        "dep": "aux",
                        "head_text": "pedido",
                        "morph": {"Tense": "Imp", "VerbForm": "Fin"},
                    },
                    {
                        "text": "pedido",
                        "start_ms": 1210,
                        "end_ms": 1500,
                        "norm": "pedido",
                        "lemma": "pedir",
                        "pos": "VERB",
                        "dep": "ROOT",
                        "head_text": "pedido",
                        "morph": {"VerbForm": "Part"},
                        "past_type": "legacy",
                    },
                    {
                        "text": "seg-",
                        "token_id": "ARGself001",
                        "start_ms": 1510,
                        "end_ms": 1600,
                        "norm": "seg",
                        "lemma": "seg-",
                        "pos": "X",
                        "dep": "dep",
                        "head_text": "",
                        "morph": {},
                    },
                    {
                        "text": "Google",
                        "token_id": "ARGforeign001",
                        "start_ms": 1610,
                        "end_ms": 1800,
                        "foreign": "1",
                        "norm": "google",
                        "lemma": "Google",
                        "pos": "PROPN",
                        "dep": "flat",
                        "head_text": "",
                        "morph": {},
                    },
                    {
                        "text": "eeh.",
                        "token_id": "ARGfiller001",
                        "start_ms": 1810,
                        "end_ms": 1900,
                        "norm": "eeh",
                        "lemma": "eeh",
                        "pos": "INTJ",
                        "dep": "dep",
                        "head_text": "",
                        "morph": {},
                        "future_type": "legacy",
                    },
                ],
            }
        ],
    }


def test_process_preserves_existing_ids_adds_missing_and_skips_second_run(tmp_path: Path) -> None:
    mod = load_module()
    mod._NLP = None
    mod.get_nlp = lambda required=False: None
    path = tmp_path / "sample.json"
    path.write_text(json.dumps(sample_data(), ensure_ascii=False, indent=2), encoding="utf-8")

    status, _count, token_stats, _tense_stats = mod.process_file(
        path,
        "sample.json",
        force=True,
        dry_run=False,
        backup_before_write=False,
    )
    assert status == "processed"
    assert token_stats["changed_existing"] == 0
    assert token_stats["added"] == 1

    data = mod.read_json(path)
    words = data["segments"][0]["words"]
    assert words[0]["token_id"] == "ARGexisting001"
    assert words[2]["token_id"] == "ARGself001"
    assert words[3]["token_id"] == "ARGforeign001"
    assert len({word["token_id"] for word in words}) == len(words)
    assert all(isinstance(word["start_ms"], int) and isinstance(word["end_ms"], int) for word in words)
    assert all("past_type" not in word and "future_type" not in word for word in words)

    assert words[1]["morph"]["PastType"] == "pastPerfect"
    assert words[1]["morph"]["TenseRole"] == "compound_participle"
    assert words[2]["pos"] == "X"
    assert words[2]["morph"]["TranscriptSpecial"] == "self_correction"
    assert words[3]["foreign"] == "1"
    assert words[4]["pos"] == "INTJ"

    meta = data["ann_meta"]
    assert meta["stages"]["tense"]["version"] == mod.TENSE_RULES_VERSION
    assert meta["validation"]["status"] == "passed"
    assert mod.should_skip_file(data, force=False) == (True, "up-to-date")


def test_validation_rejects_duplicate_token_ids() -> None:
    mod = load_module()
    data = sample_data()
    data["segments"][0]["words"][1]["token_id"] = "ARGexisting001"
    result = mod.validate_transcript(data, existing_ids=mod.token_id_snapshot(data))
    assert any("duplicate token_id" in error for error in result.errors)


def test_root_detection_finds_repo_root() -> None:
    mod = load_module()
    assert mod.PROJECT_ROOT == Path(__file__).resolve().parents[3]
    assert mod.TRANSCRIPTS_DIR == mod.PROJECT_ROOT / "media" / "transcripts"
    assert mod.TRANSCRIPTS_DIR.exists()


def test_require_spacy_raises_when_model_cannot_load() -> None:
    mod = load_module()
    mod._NLP = None
    mod.SPACY_MODEL = "__missing_model_for_unit_test__"
    with pytest.raises(RuntimeError):
        mod.get_nlp(required=True)


def test_audit_not_green_when_spacy_not_installed(tmp_path: Path) -> None:
    audit = load_audit_module()
    mod = audit.ann
    path = tmp_path / "sample.json"
    data = sample_data()
    data["segments"][0]["words"][1]["token_id"] = "ARGadded001"
    for word in data["segments"][0]["words"]:
        word.pop("past_type", None)
        word.pop("future_type", None)
    mod.prepare_transcript_structure(path, data)
    data["ann_meta"] = {
        "version": mod.ANN_VERSION,
        "pipeline_version": mod.PIPELINE_VERSION,
        "spacy_version": "not-installed",
        "spacy_model": mod.SPACY_MODEL,
        "validation": {"status": "passed", "errors": [], "warnings": []},
        "stages": {
            "spacy": {"status": "done", "version": mod.SPACY_STAGE_VERSION},
            "tense": {"status": "done", "version": mod.TENSE_RULES_VERSION},
            "validate": {"status": "done", "version": mod.VALIDATION_VERSION},
        },
        "token_id_audit": {
            "unchanged_existing": 5,
            "changed_existing": 0,
            "added": 0,
        },
        "tense_audit": {"TenseRole": {}},
        "special_token_audit": {"spacy_annotation_mode": "preserved"},
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    result = audit.audit_file(path)
    assert result["quality_decision"] != "GREEN"
    assert "Install/verify spaCy model" in result["recommendation"]


def test_tense_role_stats_match_final_token_counts() -> None:
    mod = load_module()
    data = sample_data()
    stats = mod.apply_tense(data)
    final_counts = {}
    for _seg_idx, _word_idx, _seg, word in mod.iter_words(data):
        morph = word.get("morph") if isinstance(word.get("morph"), dict) else {}
        if "TenseRole" in morph:
            final_counts[morph["TenseRole"]] = final_counts.get(morph["TenseRole"], 0) + 1
    assert stats["TenseRole"] == final_counts
