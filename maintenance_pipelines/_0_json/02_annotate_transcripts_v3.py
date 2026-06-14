#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Annotate Corapan transcript JSON files with the v3.1 token pipeline.

This script intentionally keeps the Corapan transcript model:

    root metadata -> segments[] -> words[]

It adapts the newer Coprepan annotation quality rules to transcript words, but
does not migrate files to the Coprepan article/text/title/body structure.
Existing token_id values are immutable, including in --force mode.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import os
import re
import shutil
import sqlite3
import string
import sys
import unicodedata
import warnings
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

warnings.filterwarnings("ignore", category=FutureWarning)

try:
    from tqdm import tqdm as _tqdm
except Exception:  # pragma: no cover - tqdm is optional
    _tqdm = None


# =============================================================================
# Paths and versions
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent


def find_project_root(start: Path = SCRIPT_DIR) -> Path:
    """Find the repository root from this script location."""
    candidates = [start, *start.parents]
    for candidate in candidates:
        if not (candidate / "media" / "transcripts").exists():
            continue
        if (candidate / ".git").exists() or (candidate / "app").exists() or (candidate / "maintenance_pipelines").exists():
            return candidate
    searched = ", ".join(str(path) for path in candidates)
    raise RuntimeError(f"Cannot locate Corapan project root from {start}. Searched: {searched}")


PROJECT_ROOT = find_project_root()
TRANSCRIPTS_DIR = PROJECT_ROOT / "media" / "transcripts"
COUNTRIES_PY_CANDIDATES = (
    PROJECT_ROOT / "src" / "app" / "config" / "countries.py",
    PROJECT_ROOT / "app" / "src" / "app" / "config" / "countries.py",
)
COUNTRIES_PY = next((path for path in COUNTRIES_PY_CANDIDATES if path.exists()), COUNTRIES_PY_CANDIDATES[-1])

LOG_DIR = SCRIPT_DIR / "logs" / "annotation"
PROGRESS_DIR = SCRIPT_DIR / "logs"
STATE_DB = SCRIPT_DIR / "state" / "annotation" / "annotation_state.sqlite"
SMOKE_BACKUP_DIR = SCRIPT_DIR / "backups" / "smoke-tests"

ANN_VERSION = "corapan-ann/v3"
SCHEMA_VERSION = "corapan-transcript-json/v3"
PIPELINE_VERSION = "corapan-transcript-ann-v3.1"
SCRIPT_NAME = "maintenance_pipelines/_0_json/02_annotate_transcripts_v3.py"
SPACY_MODEL = "es_dep_news_trf"
SPACY_STAGE_VERSION = "spacy-transcript-adapter-v2"
TENSE_RULES_VERSION = "tense-v3-corapan-adapter-v1"
VALIDATION_VERSION = "transcript-validation-v2"
TOKEN_ID_POLICY_VERSION = "token-id-preserve-v2"
TRANSCRIPT_SPECIAL_RULES_VERSION = "transcript-special-v2"

REQUIRED_TOKEN_FIELDS = (
    "token_id",
    "sentence_id",
    "utterance_id",
    "start_ms",
    "end_ms",
    "text",
    "norm",
    "lemma",
    "pos",
    "dep",
    "head_text",
    "morph",
)
REQUIRED_SEGMENT_FIELDS = ("utt_start_ms", "utt_end_ms", "speaker", "speaker_code")

SENTENCE_ENDS = frozenset({".", "?", "!", "¿", "¡"})
PUNCT_CHARS = string.punctuation + "¿¡"
FOREIGN_TAG_RE = re.compile(r"\(foreign\)", re.IGNORECASE)
SELF_CORRECTION_RE = re.compile(r".+-$")
FILLERS = frozenset({"eeh"})
CUSTOM_FOREIGN_WORDS = frozenset(
    {
        "whatsapp",
        "google",
        "tiktok",
        "facebook",
        "twitter",
        "instagram",
        "youtube",
        "spotify",
        "uber",
        "zoom",
        "hisbollah",
    }
)

IGNORED_POS_GAP = frozenset({"PRON", "ADV", "PART", "ADP", "SCONJ", "CCONJ", "PUNCT", "DET"})
IGNORED_TOKENS_GAP = frozenset({"no", "ya", "aun", "aún", "todavia", "todavía", "tambien", "también", "solo", "sólo"})

PAST_LABELS = frozenset(
    {
        "simplePast",
        "imperfectPast",
        "presentPerfect",
        "pastPerfect",
        "futurePerfect",
        "conditionalPerfect",
        "otherCompoundPast",
        "otherPast",
    }
)
FUTURE_LABELS = frozenset({"periphrasticFuture", "periphrasticFuturePast"})
VOICE_LABELS = frozenset({"passive", "resultative"})
TENSE_ROLE_LABELS = frozenset(
    {
        "finite_past",
        "auxiliary",
        "compound_participle",
        "future_infinitive",
        "lexical_participle",
    }
)
TENSE_FEATURES = ("PastType", "FutureType", "VoiceType", "TenseRole")

logger = logging.getLogger("corapan.annotation")
_NLP: Any | None = None
_SPACY_IMPORT_ATTEMPTED = False
_SPACY_VERSION: str | None = None
_SPACY_AVAILABLE = False


# =============================================================================
# General helpers
# =============================================================================

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def setup_logging(verbose: bool = False, dry_run: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if not dry_run:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(LOG_DIR / "annotate_transcripts.log", encoding="utf-8"))
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
        force=True,
    )


def load_country_normalizer():
    if not COUNTRIES_PY.exists():
        return lambda x: x.upper().strip() if x else ""
    spec = importlib.util.spec_from_file_location("countries_module", COUNTRIES_PY)
    if spec is None or getattr(spec, "loader", None) is None:
        return lambda x: x.upper().strip() if x else ""
    module = importlib.util.module_from_spec(spec)
    sys.modules["countries_module"] = module
    spec.loader.exec_module(module)
    return module.normalize_country_code


normalize_country_code = load_country_normalizer()


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
    with path.open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def stable_json_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def strip_accents_keep_enye(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    result = []
    for char in normalized:
        if unicodedata.category(char) != "Mn":
            result.append(char)
        elif char == "\u0303":
            result.append(char)
    return unicodedata.normalize("NFC", "".join(result))


def normalize_token(text: str) -> str:
    text = strip_accents_keep_enye(text or "")
    text = text.lower().strip(PUNCT_CHARS)
    return " ".join(text.split())


def strip_punct(text: str) -> str:
    return (text or "").strip(PUNCT_CHARS)


def clean_foreign_tag(text: str) -> str:
    return FOREIGN_TAG_RE.sub("", text or "").strip()


def as_int_ms(value: Any, fallback: int = 0) -> int:
    if value is None:
        return fallback
    try:
        if isinstance(value, str) and not value.strip():
            return fallback
        return int(round(float(value)))
    except (TypeError, ValueError):
        return fallback


def get_word_count(data: dict[str, Any]) -> int:
    return sum(len(seg.get("words", [])) for seg in data.get("segments", []) if isinstance(seg, dict))


def get_file_duration(data: dict[str, Any]) -> float:
    max_end_ms = 0
    for seg in data.get("segments", []):
        if not isinstance(seg, dict):
            continue
        for word in seg.get("words", []):
            if isinstance(word, dict):
                max_end_ms = max(max_end_ms, as_int_ms(word.get("end_ms"), 0))
    return max_end_ms / 1000.0


def file_country_code(path: Path, data: dict[str, Any]) -> str:
    code = str(data.get("country_code") or "").strip()
    if not code:
        code = path.parent.name
    return normalize_country_code(code) or code.upper()


def file_id_for(path: Path, data: dict[str, Any]) -> str:
    return str(data.get("file_id") or data.get("filename") or path.stem).replace(".mp3", "").replace(".json", "")


def sentence_chunks(words: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for word in words:
        current.append(word)
        text = str(word.get("text") or "").strip()
        if text and any(text.endswith(end) for end in SENTENCE_ENDS):
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return chunks


def iter_words(data: dict[str, Any]):
    for seg_idx, seg in enumerate(data.get("segments", [])):
        if not isinstance(seg, dict):
            continue
        words = seg.get("words", [])
        if not isinstance(words, list):
            continue
        for word_idx, word in enumerate(words):
            if isinstance(word, dict):
                yield seg_idx, word_idx, seg, word


# =============================================================================
# spaCy
# =============================================================================

def get_spacy_version() -> str:
    global _SPACY_VERSION, _SPACY_IMPORT_ATTEMPTED, _SPACY_AVAILABLE
    if _SPACY_VERSION is not None:
        return _SPACY_VERSION
    _SPACY_IMPORT_ATTEMPTED = True
    try:
        import spacy  # type: ignore

        _SPACY_VERSION = str(spacy.__version__)
        _SPACY_AVAILABLE = True
    except Exception:
        _SPACY_VERSION = "not-installed"
        _SPACY_AVAILABLE = False
    return _SPACY_VERSION


def get_nlp(required: bool = False) -> Any | None:
    global _NLP, _SPACY_AVAILABLE, _SPACY_IMPORT_ATTEMPTED, _SPACY_VERSION
    if _NLP is not None:
        return _NLP
    _SPACY_IMPORT_ATTEMPTED = True
    try:
        import spacy  # type: ignore

        _SPACY_VERSION = str(spacy.__version__)
        logger.info("spaCy version: %s", _SPACY_VERSION)
        logger.info("Loading spaCy model: %s", SPACY_MODEL)
        _NLP = spacy.load(SPACY_MODEL)
        logger.info(
            "spaCy model loaded: %s %s",
            _NLP.meta.get("name", SPACY_MODEL),
            _NLP.meta.get("version", ""),
        )
        _SPACY_AVAILABLE = True
        return _NLP
    except Exception as exc:
        _SPACY_AVAILABLE = False
        message = f"spaCy model unavailable: {exc}"
        if required:
            logger.error(message)
            raise RuntimeError(message) from exc
        logger.warning("%s; preserving existing annotations where possible", message)
        return None


def morph_to_plain(token: Any) -> dict[str, Any]:
    morph = token.morph.to_dict()
    return {str(k): v for k, v in morph.items()}


def fill_word_annotation(word: dict[str, Any], token: Any) -> None:
    word["pos"] = token.pos_
    word["lemma"] = token.lemma_
    word["dep"] = token.dep_
    word["head_text"] = token.head.text if token.head is not None else ""
    word["morph"] = morph_to_plain(token)


def simple_fallback_annotation(text: str) -> dict[str, Any]:
    clean = strip_punct(text)
    if not clean and text:
        return {"pos": "PUNCT", "lemma": text, "dep": "punct", "head_text": "", "morph": {}}
    return {"pos": "X", "lemma": clean or text, "dep": "dep", "head_text": "", "morph": {}}


def annotate_fallback(word: dict[str, Any], nlp: Any | None, fallback_counter: Counter[str]) -> None:
    text = strip_punct(str(word.get("text") or ""))
    if nlp is not None and text:
        doc = nlp(text.lower())
        if len(doc):
            fill_word_annotation(word, doc[0])
            fallback_counter["single_token_spacy"] += 1
            return
    existing = {
        key: word.get(key)
        for key in ("pos", "lemma", "dep", "head_text", "morph")
        if word.get(key) not in (None, "")
    }
    if all(key in existing for key in ("pos", "lemma", "dep", "head_text", "morph")) and isinstance(existing.get("morph"), dict):
        word["morph"] = dict(existing["morph"])
        fallback_counter["preserved_existing"] += 1
        return
    word.update(simple_fallback_annotation(str(word.get("text") or "")))
    fallback_counter["simple"] += 1


# =============================================================================
# Transcript special cases
# =============================================================================

def is_foreign_word_token(word: dict[str, Any]) -> bool:
    text = str(word.get("text") or "")
    norm = normalize_token(clean_foreign_tag(text))
    return word.get("foreign") == "1" or bool(FOREIGN_TAG_RE.search(text)) or norm in CUSTOM_FOREIGN_WORDS


def is_self_correction_token(word: dict[str, Any]) -> bool:
    text = str(word.get("text") or "").strip()
    return bool(SELF_CORRECTION_RE.match(text))


def is_filler_token(word: dict[str, Any]) -> bool:
    return normalize_token(str(word.get("text") or "")) in FILLERS


def annotate_special_transcript_token(word: dict[str, Any]) -> bool:
    text = str(word.get("text") or "")
    if is_foreign_word_token(word):
        word["foreign"] = "1"
        word["pos"] = word.get("pos") or "X"
        word["lemma"] = word.get("lemma") or clean_foreign_tag(strip_punct(text)) or text
        word["dep"] = word.get("dep") or "dep"
        word["head_text"] = word.get("head_text") or ""
        morph = word.get("morph") if isinstance(word.get("morph"), dict) else {}
        word["morph"] = dict(morph)
        return True
    if is_self_correction_token(word):
        word["pos"] = "X"
        word["lemma"] = text
        word["dep"] = "dep"
        word["head_text"] = ""
        word["morph"] = {"TranscriptSpecial": "self_correction"}
        return True
    if is_filler_token(word):
        word["pos"] = "INTJ"
        word["lemma"] = normalize_token(text) or text
        word["dep"] = "dep"
        word["head_text"] = ""
        word["morph"] = {"TranscriptSpecial": "filler"}
        return True
    clean = strip_punct(text)
    if text and not clean:
        word["pos"] = "PUNCT"
        word["lemma"] = text
        word["dep"] = "punct"
        word["head_text"] = ""
        word["morph"] = {}
        return True
    return False


def annotate_regular_token_with_spacy(
    word: dict[str, Any],
    doc: Any,
    tok_idx: int,
    nlp: Any | None,
    fallback_counter: Counter[str],
) -> int:
    text = str(word.get("text") or "")
    if doc is None:
        annotate_fallback(word, nlp, fallback_counter)
        return tok_idx

    while tok_idx < len(doc) and (doc[tok_idx].is_punct or doc[tok_idx].is_space):
        tok_idx += 1
    target = strip_punct(text.lower())
    if tok_idx < len(doc) and strip_punct(doc[tok_idx].text.lower()) == target:
        fill_word_annotation(word, doc[tok_idx])
        return tok_idx + 1

    scan = tok_idx
    while scan < len(doc):
        if not (doc[scan].is_punct or doc[scan].is_space) and strip_punct(doc[scan].text.lower()) == target:
            fill_word_annotation(word, doc[scan])
            return scan + 1
        scan += 1

    annotate_fallback(word, nlp, fallback_counter)
    return tok_idx


# =============================================================================
# Token IDs
# =============================================================================

def token_id_snapshot(data: dict[str, Any]) -> dict[tuple[int, int], str]:
    snapshot: dict[tuple[int, int], str] = {}
    for seg_idx, word_idx, _seg, word in iter_words(data):
        token_id = str(word.get("token_id") or "").strip()
        if token_id:
            snapshot[(seg_idx, word_idx)] = token_id
    return snapshot


def token_id_counts(data: dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for _seg_idx, _word_idx, _seg, word in iter_words(data):
        token_id = str(word.get("token_id") or "").strip()
        if token_id:
            counts[token_id] += 1
    return counts


def token_base_for_missing_id(
    path: Path,
    data: dict[str, Any],
    seg_idx: int,
    word_idx: int,
    word: dict[str, Any],
) -> tuple[str, str]:
    cc = file_country_code(path, data).replace("-", "").upper()
    base = "|".join(
        [
            cc,
            str(data.get("date") or ""),
            file_id_for(path, data),
            str(seg_idx),
            str(word_idx),
            str(as_int_ms(word.get("start_ms"), 0)),
            str(as_int_ms(word.get("end_ms"), 0)),
            str(word.get("text") or ""),
        ]
    )
    return cc, base


def make_missing_token_id(
    cc: str,
    base: str,
    used_ids: set[str],
    corpus_ids: set[str] | None = None,
) -> str:
    blocked = set(used_ids)
    if corpus_ids:
        blocked.update(corpus_ids)
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()
    for prefix_len in range(10, 25):
        candidate = f"{cc}{digest[:prefix_len]}"
        if candidate not in blocked:
            return candidate
    for local_idx in range(1, 10000):
        digest = hashlib.sha256(f"{base}|local|{local_idx}".encode("utf-8")).hexdigest()
        candidate = f"{cc}{digest[:24]}"
        if candidate not in blocked:
            return candidate
    raise RuntimeError("unable to generate collision-free token_id")


def collect_corpus_token_ids(selected_files: list[tuple[Path, str]]) -> set[str]:
    selected = {path.resolve() for path, _rel in selected_files}
    corpus_ids: set[str] = set()
    for path, _rel in collect_json_files(None, None):
        if path.resolve() in selected:
            continue
        try:
            data = read_json(path)
        except Exception:
            continue
        corpus_ids.update(token_id_counts(data).keys())
    return corpus_ids


def ensure_token_ids(
    path: Path,
    data: dict[str, Any],
    before: dict[tuple[int, int], str],
    corpus_ids: set[str] | None = None,
) -> dict[str, int]:
    used_ids = set(token_id_counts(data).keys())
    added = 0
    unchanged = 0
    changed_existing = 0
    for seg_idx, word_idx, _seg, word in iter_words(data):
        existing_before = before.get((seg_idx, word_idx))
        current = str(word.get("token_id") or "").strip()
        if existing_before:
            if current != existing_before:
                word["token_id"] = existing_before
                changed_existing += 1
            unchanged += 1
            used_ids.add(existing_before)
            continue
        if current:
            used_ids.add(current)
            continue
        cc, base = token_base_for_missing_id(path, data, seg_idx, word_idx, word)
        new_id = make_missing_token_id(cc, base, used_ids, corpus_ids)
        word["token_id"] = new_id
        used_ids.add(new_id)
        added += 1
    after = token_id_snapshot(data)
    changed_existing_after = sum(1 for key, token_id in before.items() if after.get(key) != token_id)
    return {
        "existing_before": len(before),
        "existing_after": sum(1 for token_id in after.values() if token_id),
        "unchanged_existing": unchanged,
        "added": added,
        "changed_existing": changed_existing_after,
        "restored_existing": changed_existing,
    }


# =============================================================================
# Hashing and idempotence
# =============================================================================

def transcript_input_view(data: dict[str, Any]) -> dict[str, Any]:
    view: dict[str, Any] = {}
    for key, value in data.items():
        if key in {"ann_meta", "segments"}:
            continue
        view[key] = value
    segments = []
    for seg in data.get("segments", []):
        if not isinstance(seg, dict):
            continue
        seg_view = {
            "speaker_code": seg.get("speaker_code"),
            "utt_start_ms": seg.get("utt_start_ms"),
            "utt_end_ms": seg.get("utt_end_ms"),
            "words": [],
        }
        for word in seg.get("words", []):
            if not isinstance(word, dict):
                continue
            seg_view["words"].append(
                {
                    "text": word.get("text"),
                    "start_ms": word.get("start_ms"),
                    "end_ms": word.get("end_ms"),
                    "start": word.get("start"),
                    "end": word.get("end"),
                }
            )
        segments.append(seg_view)
    view["segments"] = segments
    return view


def compute_input_hash(data: dict[str, Any]) -> str:
    return stable_json_hash(transcript_input_view(data))


def annotation_hash(data: dict[str, Any]) -> str:
    clone = json.loads(json.dumps(data, ensure_ascii=False))
    if isinstance(clone.get("ann_meta"), dict):
        clone["ann_meta"]["annotation_hash"] = "sha256:pending"
    return stable_json_hash(clone)


def required_stage_versions() -> dict[str, str]:
    return {
        "spacy": SPACY_STAGE_VERSION,
        "tense": TENSE_RULES_VERSION,
        "validate": VALIDATION_VERSION,
    }


def should_skip_file(data: dict[str, Any], force: bool) -> tuple[bool, str]:
    if force:
        return False, "force"
    ann_meta = data.get("ann_meta") if isinstance(data.get("ann_meta"), dict) else {}
    if ann_meta.get("version") != ANN_VERSION:
        return False, "ann version mismatch"
    if ann_meta.get("pipeline_version") != PIPELINE_VERSION:
        return False, "pipeline version mismatch"
    if ann_meta.get("input_hash") != compute_input_hash(data):
        return False, "input hash mismatch"
    if ann_meta.get("spacy_model") != SPACY_MODEL:
        return False, "spaCy model mismatch"
    if ann_meta.get("spacy_version") != get_spacy_version():
        return False, "spaCy version mismatch"
    if ann_meta.get("tense_rules_version") != TENSE_RULES_VERSION:
        return False, "tense rules version mismatch"
    if ann_meta.get("validation_version") != VALIDATION_VERSION:
        return False, "validation version mismatch"
    stages = ann_meta.get("stages") if isinstance(ann_meta.get("stages"), dict) else {}
    for stage, version in required_stage_versions().items():
        if stages.get(stage, {}).get("version") != version or stages.get(stage, {}).get("status") != "done":
            return False, f"{stage} stage mismatch"
    validation = ann_meta.get("validation") if isinstance(ann_meta.get("validation"), dict) else {}
    if validation.get("status") != "passed":
        return False, "validation not passed"
    errors = validate_transcript(data, existing_ids=token_id_snapshot(data)).errors
    if errors:
        return False, f"validation failed: {errors[0]}"
    return True, "up-to-date"


# =============================================================================
# Tense rules
# =============================================================================

def morph_values(morph: dict[str, Any], key: str) -> set[str]:
    value = morph.get(key)
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(item) for item in value if item is not None}
    if isinstance(value, tuple):
        return {str(item) for item in value if item is not None}
    if isinstance(value, str):
        return {part.strip() for part in value.split(",") if part.strip()}
    return {str(value)}


def token_morph(word: dict[str, Any]) -> dict[str, Any]:
    morph = word.get("morph")
    if not isinstance(morph, dict):
        morph = {}
        word["morph"] = morph
    return morph


def clear_tense_features(word: dict[str, Any]) -> None:
    word.pop("past_type", None)
    word.pop("future_type", None)
    morph = token_morph(word)
    for key in TENSE_FEATURES:
        morph.pop(key, None)


def set_tense_feature(word: dict[str, Any], key: str, value: str) -> None:
    token_morph(word)[key] = value


def is_ignorable_gap_token(word: dict[str, Any]) -> bool:
    return word.get("pos") in IGNORED_POS_GAP or normalize_token(str(word.get("text") or "")) in IGNORED_TOKENS_GAP


def has_finite_verb(word: dict[str, Any]) -> bool:
    morph = token_morph(word)
    return "Fin" in morph_values(morph, "VerbForm") and word.get("pos") in {"VERB", "AUX"}


def find_near_haber_aux(words: list[dict[str, Any]], idx_part: int, max_gap: int = 4) -> dict[str, Any] | None:
    for direction in (-1, 1):
        skipped = 0
        j = idx_part + direction
        while 0 <= j < len(words) and abs(j - idx_part) <= max_gap + 1:
            candidate = words[j]
            if str(candidate.get("lemma") or "").lower() == "haber" and candidate.get("pos") in {"AUX", "VERB"}:
                return candidate
            if not is_ignorable_gap_token(candidate):
                skipped += 1
                if skipped > max_gap:
                    break
            j += direction
    return None


def compound_past_label_from_haber(aux: dict[str, Any]) -> str:
    morph = token_morph(aux)
    tense = morph_values(morph, "Tense")
    verbform = morph_values(morph, "VerbForm")
    if "Pres" in tense:
        return "presentPerfect"
    if "Imp" in tense:
        return "pastPerfect"
    if "Fut" in tense:
        return "futurePerfect"
    if "Cond" in tense or "Cnd" in tense:
        return "conditionalPerfect"
    if "Inf" in verbform or "Ger" in verbform:
        return "otherCompoundPast"
    return "otherCompoundPast"


def find_ser_estar_participle_aux(words: list[dict[str, Any]], idx_part: int, max_gap: int = 5) -> dict[str, Any] | None:
    j = idx_part - 1
    while j >= 0 and idx_part - j <= max_gap:
        candidate = words[j]
        lemma = str(candidate.get("lemma") or "").lower()
        if lemma in {"ser", "estar"} and has_finite_verb(candidate):
            return candidate
        if has_finite_verb(candidate):
            break
        j -= 1
    return None


def apply_compound_futures(words: list[dict[str, Any]], stats: dict[str, Any]) -> None:
    for idx, word in enumerate(words):
        if str(word.get("lemma") or "").lower() != "ir":
            continue
        if word.get("pos") not in {"AUX", "VERB"}:
            continue
        tense = morph_values(token_morph(word), "Tense")
        label = None
        if "Pres" in tense:
            label = "periphrasticFuture"
        elif tense.intersection({"Imp", "Past"}):
            label = "periphrasticFuturePast"
        if label is None:
            continue
        for j in range(idx + 1, min(len(words), idx + 8)):
            if normalize_token(str(words[j].get("text") or "")) != "a":
                if not is_ignorable_gap_token(words[j]):
                    break
                continue
            for k in range(j + 1, min(len(words), j + 8)):
                candidate = words[k]
                if "Inf" in morph_values(token_morph(candidate), "VerbForm") and candidate.get("pos") == "VERB":
                    set_tense_feature(candidate, "FutureType", label)
                    set_tense_feature(candidate, "TenseRole", "future_infinitive")
                    stats["FutureType"][label] += 1
                    add_tense_sample(stats, "FutureType", candidate, words)
                    break
                if not is_ignorable_gap_token(candidate):
                    break
            break


def add_tense_sample(stats: dict[str, Any], key: str, word: dict[str, Any], words: list[dict[str, Any]]) -> None:
    samples = stats.setdefault("samples", defaultdict(list))
    if len(samples[key]) >= 10:
        return
    try:
        idx = words.index(word)
    except ValueError:
        idx = 0
    context = " ".join(str(w.get("text") or "") for w in words[max(0, idx - 5) : idx + 6])
    samples[key].append({"token": word.get("text", ""), "token_id": word.get("token_id", ""), "context": context})


def apply_tense_to_words(words: list[dict[str, Any]], stats: dict[str, Any]) -> None:
    for word in words:
        clear_tense_features(word)

    for idx, word in enumerate(words):
        morph = token_morph(word)
        tense = morph_values(morph, "Tense")
        verbform = morph_values(morph, "VerbForm")
        lemma = str(word.get("lemma") or "").lower()
        pos = word.get("pos")

        if "Part" in verbform and lemma != "haber":
            aux = find_near_haber_aux(words, idx)
            if aux is not None:
                label = compound_past_label_from_haber(aux)
                set_tense_feature(word, "PastType", label)
                set_tense_feature(word, "TenseRole", "compound_participle")
                set_tense_feature(aux, "TenseRole", "auxiliary")
                stats["PastType"][label] += 1
                add_tense_sample(stats, label, word, words)
                continue
            se_aux = find_ser_estar_participle_aux(words, idx)
            if se_aux is not None:
                voice = "resultative" if str(se_aux.get("lemma") or "").lower() == "estar" else "passive"
                set_tense_feature(word, "VoiceType", voice)
                set_tense_feature(word, "TenseRole", "lexical_participle")
                set_tense_feature(se_aux, "TenseRole", "auxiliary")
                stats["VoiceType"][voice] += 1
                stats["TenseRole"]["lexical_participle"] += 1
                add_tense_sample(stats, f"{voice}_participle", word, words)
                continue
            set_tense_feature(word, "TenseRole", "lexical_participle")
            stats["TenseRole"]["lexical_participle"] += 1
            continue

        if "Fin" in verbform and pos == "VERB":
            label = None
            if "Past" in tense:
                label = "simplePast"
            elif "Imp" in tense:
                label = "imperfectPast"
            if label:
                set_tense_feature(word, "PastType", label)
                set_tense_feature(word, "TenseRole", "finite_past")
                stats["PastType"][label] += 1
                add_tense_sample(stats, label, word, words)
            elif "Past" in tense or "Imp" in tense:
                set_tense_feature(word, "PastType", "otherPast")
                set_tense_feature(word, "TenseRole", "finite_past")
                stats["PastType"]["otherPast"] += 1
                add_tense_sample(stats, "otherPast", word, words)

    apply_compound_futures(words, stats)


def apply_tense(data: dict[str, Any]) -> dict[str, Any]:
    stats: dict[str, Any] = {
        "PastType": Counter(),
        "FutureType": Counter(),
        "VoiceType": Counter(),
        "TenseRole": Counter(),
        "samples": defaultdict(list),
    }
    for seg in data.get("segments", []):
        if isinstance(seg, dict) and isinstance(seg.get("words"), list):
            apply_tense_to_words(seg["words"], stats)
    final_tense_roles: Counter[str] = Counter()
    for _seg_idx, _word_idx, _seg, word in iter_words(data):
        morph = word.get("morph") if isinstance(word.get("morph"), dict) else {}
        if "TenseRole" in morph:
            final_tense_roles[str(morph["TenseRole"])] += 1
    stats["TenseRole"] = final_tense_roles
    return {
        "PastType": dict(stats["PastType"]),
        "FutureType": dict(stats["FutureType"]),
        "VoiceType": dict(stats["VoiceType"]),
        "TenseRole": dict(stats["TenseRole"]),
        "samples": {key: list(value) for key, value in stats["samples"].items()},
    }


# =============================================================================
# Validation
# =============================================================================

class ValidationResult:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_transcript(data: dict[str, Any], existing_ids: dict[tuple[int, int], str] | None = None) -> ValidationResult:
    result = ValidationResult()
    existing_ids = existing_ids or {}
    segments = data.get("segments")
    if not isinstance(segments, list):
        result.errors.append("segments is not a list")
        return result

    seen_ids: set[str] = set()
    duplicates: set[str] = set()
    for seg_idx, seg in enumerate(segments):
        if not isinstance(seg, dict):
            result.errors.append(f"segment[{seg_idx}] is not an object")
            continue
        words = seg.get("words")
        if not isinstance(words, list):
            result.errors.append(f"segment[{seg_idx}].words is not a list")
            continue
        for field in REQUIRED_SEGMENT_FIELDS:
            if field not in seg:
                result.warnings.append(f"segment[{seg_idx}] missing {field}")
        utt_start = as_int_ms(seg.get("utt_start_ms"), 0)
        utt_end = as_int_ms(seg.get("utt_end_ms"), 0)
        if utt_start > utt_end:
            result.errors.append(f"segment[{seg_idx}] utt_start_ms > utt_end_ms")
        word_starts = []
        word_ends = []
        for word_idx, word in enumerate(words):
            if not isinstance(word, dict):
                result.errors.append(f"segment[{seg_idx}].words[{word_idx}] is not an object")
                continue
            for field in REQUIRED_TOKEN_FIELDS:
                if field not in word:
                    result.errors.append(f"segment[{seg_idx}].words[{word_idx}] missing {field}")
            token_id = str(word.get("token_id") or "").strip()
            if not token_id:
                result.errors.append(f"segment[{seg_idx}].words[{word_idx}] empty token_id")
            elif token_id in seen_ids:
                duplicates.add(token_id)
            seen_ids.add(token_id)
            before_id = existing_ids.get((seg_idx, word_idx))
            if before_id and token_id != before_id:
                result.errors.append(f"existing token_id changed at segment[{seg_idx}].words[{word_idx}]")
            for legacy in ("past_type", "future_type"):
                if legacy in word:
                    result.errors.append(f"segment[{seg_idx}].words[{word_idx}] has legacy {legacy}")
            start_ms = word.get("start_ms")
            end_ms = word.get("end_ms")
            if not isinstance(start_ms, int) or not isinstance(end_ms, int):
                result.errors.append(f"segment[{seg_idx}].words[{word_idx}] start_ms/end_ms are not int")
            else:
                word_starts.append(start_ms)
                word_ends.append(end_ms)
                if start_ms > end_ms:
                    result.errors.append(f"segment[{seg_idx}].words[{word_idx}] start_ms > end_ms")
            morph = word.get("morph")
            if not isinstance(morph, dict):
                result.errors.append(f"segment[{seg_idx}].words[{word_idx}] morph is not dict")
                morph = {}
            labels = {
                "PastType": PAST_LABELS,
                "FutureType": FUTURE_LABELS,
                "VoiceType": VOICE_LABELS,
                "TenseRole": TENSE_ROLE_LABELS,
            }
            for key, allowed in labels.items():
                if key in morph and morph[key] not in allowed:
                    result.errors.append(f"segment[{seg_idx}].words[{word_idx}] invalid {key}={morph[key]}")
        if word_starts and word_ends:
            if min(word_starts) < utt_start - 2000 or max(word_ends) > utt_end + 2000:
                result.warnings.append(f"segment[{seg_idx}] word times outside utterance range")
    for token_id in sorted(duplicates):
        result.errors.append(f"duplicate token_id {token_id}")
    try:
        _ = get_word_count(data)
        _ = get_file_duration(data)
    except Exception as exc:
        result.errors.append(f"03 compatibility check failed: {exc}")
    return result


# =============================================================================
# State and progress
# =============================================================================

def connect_state() -> sqlite3.Connection:
    STATE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(STATE_DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS annotation_state (
            input_path TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT,
            updated_at TEXT,
            error TEXT,
            input_hash TEXT,
            annotation_hash TEXT,
            token_count INTEGER DEFAULT 0,
            pipeline_version TEXT,
            spacy_version TEXT,
            spacy_model TEXT,
            tense_rules_version TEXT,
            validation_version TEXT,
            token_id_existing_before INTEGER DEFAULT 0,
            token_id_existing_after INTEGER DEFAULT 0,
            token_id_unchanged_existing INTEGER DEFAULT 0,
            token_id_added INTEGER DEFAULT 0,
            token_id_changed_existing INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    return conn


def state_get(conn: sqlite3.Connection, path: Path) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM annotation_state WHERE input_path = ?", (project_rel(path),)).fetchone()
    return dict(row) if row else None


def state_mark_running(conn: sqlite3.Connection, path: Path, input_hash: str) -> None:
    now = utc_now()
    conn.execute(
        """
        INSERT INTO annotation_state (
            input_path, status, started_at, updated_at, input_hash, pipeline_version,
            spacy_version, spacy_model, tense_rules_version, validation_version
        ) VALUES (?, 'running', ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(input_path) DO UPDATE SET
            status='running', started_at=excluded.started_at, updated_at=excluded.updated_at,
            error=NULL, input_hash=excluded.input_hash, pipeline_version=excluded.pipeline_version,
            spacy_version=excluded.spacy_version, spacy_model=excluded.spacy_model,
            tense_rules_version=excluded.tense_rules_version, validation_version=excluded.validation_version
        """,
        (
            project_rel(path),
            now,
            now,
            input_hash,
            PIPELINE_VERSION,
            get_spacy_version(),
            SPACY_MODEL,
            TENSE_RULES_VERSION,
            VALIDATION_VERSION,
        ),
    )
    conn.commit()


def state_mark_done(
    conn: sqlite3.Connection,
    path: Path,
    data: dict[str, Any],
    token_stats: dict[str, int],
) -> None:
    ann_meta = data.get("ann_meta", {})
    conn.execute(
        """
        UPDATE annotation_state SET
            status='done', finished_at=?, updated_at=?, error=NULL, annotation_hash=?,
            token_count=?, token_id_existing_before=?, token_id_existing_after=?,
            token_id_unchanged_existing=?, token_id_added=?, token_id_changed_existing=?
        WHERE input_path=?
        """,
        (
            utc_now(),
            utc_now(),
            ann_meta.get("annotation_hash"),
            get_word_count(data),
            token_stats.get("existing_before", 0),
            token_stats.get("existing_after", 0),
            token_stats.get("unchanged_existing", 0),
            token_stats.get("added", 0),
            token_stats.get("changed_existing", 0),
            project_rel(path),
        ),
    )
    conn.commit()


def state_mark_failed(conn: sqlite3.Connection, path: Path, error: str) -> None:
    conn.execute(
        """
        INSERT INTO annotation_state (input_path, status, updated_at, error)
        VALUES (?, 'failed', ?, ?)
        ON CONFLICT(input_path) DO UPDATE SET status='failed', updated_at=excluded.updated_at, error=excluded.error
        """,
        (project_rel(path), utc_now(), error),
    )
    conn.commit()


class ProgressTracker:
    def __init__(self, total_files: int, total_tokens: int, dry_run: bool) -> None:
        self.dry_run = dry_run
        self.started_at = utc_now()
        self.total_files = total_files
        self.total_tokens = total_tokens
        self.processed_files = 0
        self.skipped_files = 0
        self.failed_files = 0
        self.processed_tokens = 0
        self.current_file = ""
        self.last_output_file = ""
        self.errors_total = 0
        self.last_error: str | None = None
        self.token_id_changed_existing_total = 0
        self.token_id_added_total = 0
        self.progress_json = PROGRESS_DIR / "annotation_progress.json"
        self.progress_jsonl = PROGRESS_DIR / "annotation_progress.jsonl"

    def start(self) -> None:
        if not self.dry_run:
            PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
            self.write("running")

    def file_started(self, path: Path) -> None:
        self.current_file = project_rel(path)
        self.write("running")

    def file_done(self, path: Path, token_count: int, token_stats: dict[str, int], skipped: bool = False) -> None:
        if skipped:
            self.skipped_files += 1
        else:
            self.processed_files += 1
            self.processed_tokens += token_count
        self.last_output_file = project_rel(path)
        self.token_id_changed_existing_total += token_stats.get("changed_existing", 0)
        self.token_id_added_total += token_stats.get("added", 0)
        self.write("running")
        self.append_jsonl()

    def file_failed(self, path: Path, error: str) -> None:
        self.failed_files += 1
        self.errors_total += 1
        self.current_file = project_rel(path)
        self.last_error = error
        self.write("running")
        self.append_jsonl()

    def finish(self, status: str) -> None:
        self.write(status)

    def snapshot(self, status: str) -> dict[str, Any]:
        return {
            "status": status,
            "started_at": self.started_at,
            "updated_at": utc_now(),
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "skipped_files": self.skipped_files,
            "failed_files": self.failed_files,
            "total_words": self.total_tokens,
            "total_tokens": self.total_tokens,
            "processed_words": self.processed_tokens,
            "processed_tokens": self.processed_tokens,
            "current_file": self.current_file,
            "last_output_file": self.last_output_file,
            "errors_total": self.errors_total,
            "last_error": self.last_error,
            "token_id_changed_existing_total": self.token_id_changed_existing_total,
            "token_id_added_total": self.token_id_added_total,
        }

    def write(self, status: str) -> None:
        if self.dry_run:
            return
        atomic_write_json(self.progress_json, self.snapshot(status))

    def append_jsonl(self) -> None:
        if self.dry_run:
            return
        with self.progress_jsonl.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(self.snapshot("running"), ensure_ascii=False) + "\n")


# =============================================================================
# Annotation
# =============================================================================

def prepare_transcript_structure(path: Path, data: dict[str, Any]) -> None:
    file_id = file_id_for(path, data)
    for seg_idx, seg in enumerate(data.get("segments", [])):
        if not isinstance(seg, dict):
            continue
        words = seg.get("words")
        if not isinstance(words, list):
            seg["words"] = []
            words = seg["words"]
        start_times = []
        end_times = []
        for word in words:
            if not isinstance(word, dict):
                continue
            if "start_ms" not in word and "start" in word:
                word["start_ms"] = as_int_ms(float(word.get("start", 0)) * 1000)
            else:
                word["start_ms"] = as_int_ms(word.get("start_ms"), 0)
            if "end_ms" not in word and "end" in word:
                word["end_ms"] = as_int_ms(float(word.get("end", 0)) * 1000)
            else:
                word["end_ms"] = as_int_ms(word.get("end_ms"), word["start_ms"])
            word.pop("start", None)
            word.pop("end", None)
            word["norm"] = normalize_token(str(word.get("text") or ""))
            start_times.append(word["start_ms"])
            end_times.append(word["end_ms"])
        if start_times and end_times:
            seg["utt_start_ms"] = as_int_ms(seg.get("utt_start_ms"), min(start_times))
            seg["utt_end_ms"] = as_int_ms(seg.get("utt_end_ms"), max(end_times))
        else:
            seg["utt_start_ms"] = as_int_ms(seg.get("utt_start_ms"), 0)
            seg["utt_end_ms"] = as_int_ms(seg.get("utt_end_ms"), 0)
        utterance_id = f"{file_id}:{seg_idx}"
        for sent_idx, sentence in enumerate(sentence_chunks(words)):
            sentence_id = f"{utterance_id}:s{sent_idx}"
            for word in sentence:
                word["utterance_id"] = utterance_id
                word["sentence_id"] = sentence_id


def remove_annotation_fields_for_refresh(data: dict[str, Any]) -> None:
    preserve = {
        "text",
        "token_id",
        "sentence_id",
        "utterance_id",
        "start_ms",
        "end_ms",
        "foreign",
        "speaker",
        "speaker_code",
    }
    for _seg_idx, _word_idx, _seg, word in iter_words(data):
        for key in list(word.keys()):
            if key not in preserve and key not in {"start", "end"}:
                word.pop(key, None)


def annotate_spacy_stage(data: dict[str, Any], *, require_spacy: bool = False) -> dict[str, int]:
    nlp = get_nlp(required=require_spacy)
    fallback_counter: Counter[str] = Counter()
    special_counter: Counter[str] = Counter()
    for seg in data.get("segments", []):
        if not isinstance(seg, dict) or not isinstance(seg.get("words"), list):
            continue
        words: list[dict[str, Any]] = seg["words"]
        for sentence in sentence_chunks(words):
            doc = None
            if nlp is not None:
                text = " ".join(str(word.get("text") or "").lower() for word in sentence)
                doc = nlp(text)
            tok_idx = 0
            for word in sentence:
                if annotate_special_transcript_token(word):
                    if is_foreign_word_token(word):
                        special_counter["foreign"] += 1
                    elif is_self_correction_token(word):
                        special_counter["self_correction"] += 1
                    elif is_filler_token(word):
                        special_counter["filler"] += 1
                    else:
                        special_counter["punct"] += 1
                    continue
                tok_idx = annotate_regular_token_with_spacy(word, doc, tok_idx, nlp, fallback_counter)
    return dict(fallback_counter + special_counter)


def mark_stage(ann_meta: dict[str, Any], stage: str, version: str, status: str = "done") -> None:
    ann_meta.setdefault("stages", {})[stage] = {
        "version": version,
        "status": status,
        "timestamp": utc_now(),
    }


def modernize_ann_meta(
    data: dict[str, Any],
    *,
    input_hash: str,
    existing_created_at: str | None,
    validation: ValidationResult,
    token_stats: dict[str, int],
    tense_stats: dict[str, Any],
    special_stats: dict[str, int],
) -> None:
    previous = data.get("ann_meta") if isinstance(data.get("ann_meta"), dict) else {}
    now = utc_now()
    ann_meta = dict(previous)
    ann_meta.update(
        {
            "version": ANN_VERSION,
            "schema_version": SCHEMA_VERSION,
            "pipeline_version": PIPELINE_VERSION,
            "script": SCRIPT_NAME,
            "input_hash": input_hash,
            "annotation_hash": "sha256:pending",
            "created_at": existing_created_at or previous.get("created_at") or previous.get("timestamp") or now,
            "updated_at": now,
            "spacy_model": SPACY_MODEL,
            "spacy_version": get_spacy_version(),
            "tense_rules_version": TENSE_RULES_VERSION,
            "validation_version": VALIDATION_VERSION,
            "token_id_policy_version": TOKEN_ID_POLICY_VERSION,
            "transcript_special_rules_version": TRANSCRIPT_SPECIAL_RULES_VERSION,
            "text_hash": compute_input_hash(data),
            "required": list(REQUIRED_TOKEN_FIELDS),
            "token_id_audit": token_stats,
            "tense_audit": tense_stats,
            "special_token_audit": special_stats,
            "validation": {
                "status": "passed" if validation.ok else "failed",
                "errors": validation.errors[:50],
                "warnings": validation.warnings[:50],
            },
        }
    )
    mark_stage(ann_meta, "spacy", SPACY_STAGE_VERSION)
    mark_stage(ann_meta, "tense", TENSE_RULES_VERSION)
    mark_stage(ann_meta, "validate", VALIDATION_VERSION, "done" if validation.ok else "failed")
    data["ann_meta"] = ann_meta
    data["ann_meta"]["annotation_hash"] = annotation_hash(data)


def create_single_file_backup(path: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    try:
        rel = path.resolve().relative_to(TRANSCRIPTS_DIR.resolve())
    except ValueError:
        rel = Path(path.name)
    backup_path = SMOKE_BACKUP_DIR / timestamp / rel
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_path)
    return backup_path


def process_file(
    path: Path,
    relative_name: str,
    *,
    force: bool,
    dry_run: bool,
    corpus_ids: set[str] | None = None,
    backup_before_write: bool = False,
    require_spacy: bool = False,
) -> tuple[str, int, dict[str, int], dict[str, Any]]:
    data = read_json(path)
    input_hash = compute_input_hash(data)
    skip, reason = should_skip_file(data, force)
    if skip:
        ann_meta = data.get("ann_meta") if isinstance(data.get("ann_meta"), dict) else {}
        token_stats = ann_meta.get("token_id_audit") if isinstance(ann_meta.get("token_id_audit"), dict) else {}
        return f"skipped ({reason})", get_word_count(data), dict(token_stats), {}
    if dry_run:
        return f"would process ({reason})", get_word_count(data), {"added": 0, "changed_existing": 0}, {}

    backup_path = create_single_file_backup(path) if backup_before_write else None
    if backup_path:
        logger.info("Backup created: %s", project_rel(backup_path))

    before_ids = token_id_snapshot(data)
    existing_created_at = data.get("ann_meta", {}).get("created_at") if isinstance(data.get("ann_meta"), dict) else None
    nlp_available = get_nlp(required=require_spacy) is not None
    if nlp_available:
        remove_annotation_fields_for_refresh(data)
    else:
        logger.warning("Keeping existing token annotations for %s because spaCy is unavailable.", relative_name)
    prepare_transcript_structure(path, data)
    token_stats = ensure_token_ids(path, data, before_ids, corpus_ids)
    special_stats = annotate_spacy_stage(data, require_spacy=require_spacy)
    special_stats["spacy_annotation_mode"] = "model" if nlp_available else "preserved"
    tense_stats = apply_tense(data)
    validation = validate_transcript(data, existing_ids=before_ids)
    modernize_ann_meta(
        data,
        input_hash=input_hash,
        existing_created_at=existing_created_at,
        validation=validation,
        token_stats=token_stats,
        tense_stats=tense_stats,
        special_stats=special_stats,
    )
    if not validation.ok:
        raise ValueError("; ".join(validation.errors[:10]))
    atomic_write_json(path, data)
    if token_stats.get("changed_existing", 0) != 0:
        raise ValueError("existing token_id changed during write")
    logger.info(
        "Token IDs for %s: before=%s after=%s unchanged=%s added=%s changed_existing=%s",
        relative_name,
        token_stats.get("existing_before", 0),
        token_stats.get("existing_after", 0),
        token_stats.get("unchanged_existing", 0),
        token_stats.get("added", 0),
        token_stats.get("changed_existing", 0),
    )
    return "processed", get_word_count(data), token_stats, tense_stats


# =============================================================================
# File collection and CLI
# =============================================================================

def collect_json_files(country: str | None = None, file_arg: str | None = None) -> list[tuple[Path, str]]:
    if file_arg:
        path = resolve_path(file_arg)
        return [(path, project_rel(path))]
    files: list[tuple[Path, str]] = []
    if not TRANSCRIPTS_DIR.is_dir():
        return files
    for country_dir in sorted(path for path in TRANSCRIPTS_DIR.iterdir() if path.is_dir()):
        if country and normalize_country_code(country_dir.name) != normalize_country_code(country):
            continue
        for json_file in sorted(country_dir.glob("*.json")):
            files.append((json_file, project_rel(json_file)))
    return files


def select_retry_failed(files: list[tuple[Path, str]]) -> list[tuple[Path, str]]:
    if not STATE_DB.exists():
        return []
    conn = connect_state()
    try:
        selected = []
        for path, rel in files:
            row = state_get(conn, path)
            if row and row.get("status") == "failed":
                selected.append((path, rel))
        return selected
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Annotate Corapan transcript JSON files.")
    parser.add_argument("--country", "-c", type=str, default=None, help="Process one country code.")
    parser.add_argument("--file", type=str, default=None, help="Process exactly one transcript JSON.")
    parser.add_argument("--limit", "-n", type=int, default=None, help="Process at most N files.")
    parser.add_argument("--force", "-f", action="store_true", help="Recompute annotation, preserving existing token_id values.")
    parser.add_argument("--resume", action="store_true", help="Resume normal idempotent processing.")
    parser.add_argument("--retry-failed", action="store_true", help="Only retry files marked failed in state DB.")
    parser.add_argument("--dry-run", action="store_true", help="Plan work without writing transcripts/state/progress.")
    parser.add_argument("--validate-only", action="store_true", help="Validate selected files without annotation writes.")
    parser.add_argument("--check-corpus-token-ids", action="store_true", help="Avoid new token_id collisions with the rest of the corpus.")
    parser.add_argument("--require-spacy", action="store_true", help="Fail if spaCy or the configured model cannot be loaded.")
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging(args.verbose, args.dry_run)
    logger.info("CO.RA.PAN transcript annotation %s", PIPELINE_VERSION)
    logger.info("SCRIPT_DIR: %s", SCRIPT_DIR)
    logger.info("PROJECT_ROOT: %s", PROJECT_ROOT)
    logger.info("TRANSCRIPTS_DIR: %s", TRANSCRIPTS_DIR)
    logger.info("COUNTRIES_PY: %s", COUNTRIES_PY)
    logger.info("TRANSCRIPTS_DIR exists: %s", TRANSCRIPTS_DIR.exists())

    if args.require_spacy:
        get_nlp(required=True)

    files = collect_json_files(args.country, args.file)
    if args.retry_failed:
        files = select_retry_failed(files)
    if args.limit is not None:
        files = files[: args.limit]
    if not files:
        logger.error("No JSON files selected.")
        return 1

    total_tokens = 0
    for path, _rel in files:
        try:
            total_tokens += get_word_count(read_json(path))
        except Exception:
            pass

    if args.validate_only:
        failures = 0
        for path, rel in files:
            try:
                data = read_json(path)
                result = validate_transcript(data, existing_ids=token_id_snapshot(data))
                if result.ok:
                    logger.info("%s -> validation passed (%d warnings)", rel, len(result.warnings))
                else:
                    failures += 1
                    logger.error("%s -> validation failed: %s", rel, "; ".join(result.errors[:10]))
            except Exception as exc:
                failures += 1
                logger.error("%s -> validation error: %s", rel, exc)
        return 0 if failures == 0 else 1

    corpus_ids = collect_corpus_token_ids(files) if args.check_corpus_token_ids and not args.dry_run else None
    tracker = ProgressTracker(len(files), total_tokens, args.dry_run)
    tracker.start()
    stats: Counter[str] = Counter()
    conn = None if args.dry_run else connect_state()
    progress_bar = None
    progress_iter = files
    if _tqdm is not None and sys.stderr.isatty():
        progress_bar = _tqdm(files, total=len(files), unit="file", desc="Annotating transcripts", dynamic_ncols=True)
        progress_iter = progress_bar
    try:
        for path, rel in progress_iter:
            if progress_bar is not None:
                progress_bar.set_postfix_str(rel[-60:])
            tracker.file_started(path)
            try:
                data = read_json(path)
                input_hash = compute_input_hash(data)
                if conn is not None:
                    state_mark_running(conn, path, input_hash)
                backup_before_write = bool(args.file and not args.dry_run)
                status, token_count, token_stats, tense_stats = process_file(
                    path,
                    rel,
                    force=args.force,
                    dry_run=args.dry_run,
                    corpus_ids=corpus_ids,
                    backup_before_write=backup_before_write,
                    require_spacy=args.require_spacy,
                )
                stats[status] += 1
                if conn is not None and (status == "processed" or status.startswith("skipped")):
                    state_mark_done(conn, path, read_json(path), token_stats)
                tracker.file_done(path, token_count, token_stats, skipped=status.startswith("skipped"))
                logger.info("%s -> %s", rel, status)
                if progress_bar is not None:
                    progress_bar.set_postfix(
                        processed=tracker.processed_files,
                        skipped=tracker.skipped_files,
                        failed=tracker.failed_files,
                    )
                if tense_stats:
                    logger.info("Tense counts: %s", {k: v for k, v in tense_stats.items() if k != "samples"})
            except Exception as exc:
                stats["error"] += 1
                if conn is not None:
                    state_mark_failed(conn, path, str(exc))
                tracker.file_failed(path, str(exc))
                logger.exception("%s -> error: %s", rel, exc)
                if progress_bar is not None:
                    progress_bar.set_postfix(
                        processed=tracker.processed_files,
                        skipped=tracker.skipped_files,
                        failed=tracker.failed_files,
                    )
                if args.file:
                    tracker.finish("failed")
                    return 1
    finally:
        if progress_bar is not None:
            progress_bar.close()
        if conn is not None:
            conn.close()

    final_status = "completed" if stats.get("error", 0) == 0 else "completed_with_errors"
    tracker.finish(final_status)
    logger.info("Summary: %s", dict(stats))
    return 0 if stats.get("error", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
