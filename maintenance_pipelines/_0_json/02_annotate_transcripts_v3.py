#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
02_annotate_transcripts_v3.py

Annotiert JSON-Transkripte mit dem v3-Schema.

ARBEITSPFAD:  media/transcripts/<country>/*.json

FEATURES:
    - Deterministische Token-IDs (MD5-Hash)
    - Zeiten in Millisekunden: start_ms, end_ms (int)
    - Normalisierte Suchformen: norm
    - spaCy-Annotation: pos, lemma, dep, head_text, morph
    - Zeitformen: morph.PastType, morph.FutureType (englische Labels)
    - Satz-/Utterance-IDs: sentence_id, utterance_id
    - Idempotenz: Überspringe bereits annotierte Dateien (safe-Modus)

SCHEMA-VERSION: corapan-ann/v3

VERWENDUNG:
    python 02_annotate_transcripts_v3.py
    python 02_annotate_transcripts_v3.py --country ARG
    python 02_annotate_transcripts_v3.py --force
    python 02_annotate_transcripts_v3.py --dry-run --limit 5

ERFORDERT:
    - Python >= 3.10
    - spaCy mit Modell es_dep_news_trf

Copyright (c) 2025 CO.RA.PAN Project
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import string
import sys
import unicodedata
import warnings
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Unterdrücke FutureWarnings von spaCy/transformers
warnings.filterwarnings("ignore", category=FutureWarning)

# ==============================================================================
# PFAD-KONFIGURATION
# ==============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # LOKAL/_1_json -> PROJECT_ROOT
TRANSCRIPTS_DIR = PROJECT_ROOT / "media" / "transcripts"

# Country-Code-Normalisierung importieren
COUNTRIES_PY = PROJECT_ROOT / "src" / "app" / "config" / "countries.py"

def load_country_normalizer():
    """Lädt normalize_country_code aus countries.py."""
    if not COUNTRIES_PY.exists():
        logging.warning(f"countries.py nicht gefunden: {COUNTRIES_PY}")
        return lambda x: x.upper().strip() if x else ""
    
    spec = importlib.util.spec_from_file_location("countries_module", COUNTRIES_PY)
    if spec is None or getattr(spec, 'loader', None) is None:
        logging.warning(f"countries.py spec/loader not available: {COUNTRIES_PY}")
        return lambda x: x.upper().strip() if x else ""

    module = importlib.util.module_from_spec(spec)
    sys.modules['countries_module'] = module
    spec.loader.exec_module(module)
    return module.normalize_country_code

normalize_country_code = load_country_normalizer()

# ==============================================================================
# KONSTANTEN
# ==============================================================================

ANN_VERSION = "corapan-ann/v3"
SPACY_MODEL = "es_dep_news_trf"

# Pflichtfelder pro Token (v3-Schema)
REQUIRED_TOKEN_FIELDS = (
    "token_id", "sentence_id", "utterance_id",
    "start_ms", "end_ms", "text", "lemma", "pos", "dep", "morph", "norm"
)

# Pflichtfelder pro Segment
REQUIRED_SEGMENT_FIELDS = ("utt_start_ms", "utt_end_ms")

# Satzgrenzen
SENTENCE_ENDS = frozenset({".", "?", "!"})

# Interpunktion
PUNCT_CHARS = string.punctuation + "¿¡"

# Ignorierte POS/Tokens für Zeitformen-Suche
IGNORED_POS_GAP = frozenset({"PRON", "ADV", "PART", "ADP", "SCONJ", "PUNCT"})
IGNORED_TOKENS_GAP = frozenset({"no", "ya", "aún", "todavía", "también", "solo", "sólo"})

# Ignorierte Tokens für ID-Generierung
IGNORED_TOKENS_ID = frozenset({
    "(", ")", "[", "]", "!", "(..)", "(.)", "(..", "(..).", "(..),", ").", ")]", ",", "."
})

# Tense-Mappings (intern → v3 englisch)
PAST_MAP = {
    "PerfectoSimple": "simplePast",
    "PerfectoCompuesto": "presentPerfect",
    "Pluscuamperfecto": "pastPerfect",
    "FuturoPerfecto": "futurePerfect",
    "CondicionalPerfecto": "conditionalPerfect",
    "OtroCompuesto": "otherCompoundPast",
    "PastOther": "otherPast",
}

FUTURE_MAP = {
    "analyticalFuture": "periphrasticFuture",
    "analyticalFuture_past": "periphrasticFuturePast",
}

# Tense-Erkennung für zusammengesetzte Formen
TENSE_MAP_INTERNAL = {
    "Pres": "PerfectoCompuesto",
    "Imp": "Pluscuamperfecto",
    "Fut": "FuturoPerfecto",
    "Cond": "CondicionalPerfecto",
}

# ==============================================================================
# LOGGING
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ==============================================================================
# SPACY-LADEN (LAZY)
# ==============================================================================

_nlp = None

def get_nlp():
    """Lädt spaCy-Modell (nur einmal)."""
    global _nlp
    if _nlp is None:
        import spacy
        logger.info(f"Lade spaCy-Modell: {SPACY_MODEL}")
        _nlp = spacy.load(SPACY_MODEL)
        logger.info("spaCy-Modell geladen")
    return _nlp

# ==============================================================================
# HASH & IDEMPOTENZ
# ==============================================================================

def compute_text_hash(data: dict[str, Any]) -> str:
    """Berechnet SHA1-Hash über alle Token-Texte."""
    texts = []
    for seg in data.get("segments", []):
        for w in seg.get("words", []):
            texts.append(w.get("text", ""))
    combined = "|".join(texts)
    return hashlib.sha1(combined.encode("utf-8")).hexdigest()


def check_required_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Prüft, ob alle Pflichtfelder vorhanden sind."""
    missing_token_fields: set[str] = set()
    missing_segment_fields: set[str] = set()
    tokens_checked = 0
    
    for seg_idx, seg in enumerate(data.get("segments", [])):
        for field in REQUIRED_SEGMENT_FIELDS:
            if field not in seg:
                missing_segment_fields.add(f"segment[{seg_idx}].{field}")
        
        for w in seg.get("words", []):
            tokens_checked += 1
            for field in REQUIRED_TOKEN_FIELDS:
                if field not in w:
                    missing_token_fields.add(field)
    
    return {
        "complete": len(missing_token_fields) == 0 and len(missing_segment_fields) == 0,
        "missing_token_fields": missing_token_fields,
        "missing_segment_fields": missing_segment_fields,
        "tokens_checked": tokens_checked,
    }


def should_skip_file(data: dict[str, Any], force: bool) -> tuple[bool, str]:
    """
    Entscheidet, ob Datei übersprungen werden kann.
    
    Returns:
        (skip, reason): True wenn überspringen, mit Begründung
    """
    if force:
        return False, "force mode"
    
    ann_meta = data.get("ann_meta", {})
    
    # Version prüfen
    if ann_meta.get("version") != ANN_VERSION:
        return False, f"version mismatch (expected {ANN_VERSION}, found {ann_meta.get('version')})"
    
    # Text-Hash prüfen
    current_hash = compute_text_hash(data)
    stored_hash = ann_meta.get("text_hash")
    if current_hash != stored_hash:
        return False, "text changed (hash mismatch)"
    
    # Pflichtfelder prüfen
    field_check = check_required_fields(data)
    if not field_check["complete"]:
        missing = field_check["missing_token_fields"] | field_check["missing_segment_fields"]
        return False, f"missing fields: {', '.join(sorted(missing)[:3])}..."
    
    return True, "up-to-date"

# ==============================================================================
# TOKEN-ID GENERIERUNG
# ==============================================================================

def canon_time(x: float) -> str:
    """Kanonisiert Zeit auf 2 Dezimalstellen."""
    return f"{float(x):.2f}"


def make_digest(
    cc: str,
    date_iso: str,
    start: float,
    end: float,
    text: str = "",
    global_idx: int = 0,
) -> tuple[str, str]:
    """
    Erstellt deterministischen MD5-Digest für Token-ID.
    
    Returns:
        (cc_normalized, digest)
    """
    cc_normalized = cc.replace("-", "").upper().strip()
    st2 = canon_time(start)
    et2 = canon_time(end)
    
    # Verwende Text + globalen Index für Eindeutigkeit bei gleichen Zeiten
    composite = f"{cc_normalized}|{date_iso}|{st2}|{et2}|{text}_{global_idx}"
    
    digest = hashlib.md5(composite.encode("utf-8")).hexdigest()
    return cc_normalized, digest


def assign_min_unique_prefix_lengths(
    digests: list[str],
    k_start: int = 9,
    k_max: int = 16,
) -> list[int]:
    """
    Weist minimale eindeutige Präfixlängen zu.
    
    Returns:
        Liste von Präfixlängen für jeden Digest
    """
    n = len(digests)
    k = [k_start] * n
    unresolved = set(range(n))
    
    iteration = 0
    while unresolved:
        iteration += 1
        buckets: dict[str, list[int]] = defaultdict(list)
        
        for i in unresolved:
            prefix = digests[i][:k[i]]
            buckets[prefix].append(i)
        
        clashes = [idxs for idxs in buckets.values() if len(idxs) > 1]
        
        if not clashes:
            break
        
        next_unresolved: set[int] = set()
        for idxs in clashes:
            for i in idxs:
                k[i] += 1
                if k[i] > k_max:
                    clash_info = [f"Token {idx}: {digests[idx][:k_max+2]}" for idx in idxs[:5]]
                    raise RuntimeError(
                        f"Hash-Präfix überschreitet {k_max} Hex-Zeichen bei Iteration {iteration}.\n"
                        f"Kollidierende Tokens: {clash_info}"
                    )
                next_unresolved.add(i)
        
        unresolved = next_unresolved
    
    return k


def make_token_id(cc_normalized: str, digest: str, prefix_length: int) -> str:
    """Baut Token-ID aus Country-Code und Digest-Präfix."""
    return f"{cc_normalized}{digest[:prefix_length]}"

# ==============================================================================
# NORMALISIERUNG
# ==============================================================================

def normalize_token(text: str) -> str:
    """
    Deterministische Normalisierung für Suchformen.
    
    - NFKD-Normalisierung
    - Entfernt Akzente (außer ñ)
    - Lowercase
    - Entfernt Interpunktion
    """
    if not text:
        return ""
    
    # NFKD-Normalisierung
    normalized = unicodedata.normalize("NFKD", text)
    
    # Entferne kombinierende Akzente, außer Tilde (U+0303) für ñ
    result = []
    for char in normalized:
        if unicodedata.category(char) != "Mn":  # Mn = Nonspacing Mark
            result.append(char)
        elif char == "\u0303":  # Tilde für ñ
            result.append(char)
    
    text = "".join(result)
    text = text.lower()
    text = text.strip(PUNCT_CHARS)
    text = " ".join(text.split())  # Whitespace normalisieren
    
    # NFC-Rekomposition (ñ wird zu precomposed U+00F1)
    text = unicodedata.normalize("NFC", text)
    
    return text

# ==============================================================================
# SATZBILDUNG
# ==============================================================================

def split_into_sentences(words: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Teilt Wort-Liste in Sätze auf Basis von Satzzeichen."""
    sentences = []
    current: list[dict[str, Any]] = []
    
    for w in words:
        current.append(w)
        txt = w.get("text", "").strip()
        if txt and any(txt.endswith(se) for se in SENTENCE_ENDS):
            sentences.append(current)
            current = []
    
    if current:
        sentences.append(current)
    
    return sentences


def strip_punct(text: str) -> str:
    """Entfernt Interpunktion am Anfang/Ende."""
    return text.strip(PUNCT_CHARS)

# ==============================================================================
# SPACY-ANNOTATION
# ==============================================================================

def fill_word_annotation(w_obj: dict[str, Any], spacy_token) -> None:
    """Überträgt POS, Lemma, Dep, Morph von spaCy-Token."""
    w_obj["pos"] = spacy_token.pos_
    w_obj["lemma"] = spacy_token.lemma_
    w_obj["dep"] = spacy_token.dep_
    w_obj["head_text"] = spacy_token.head.text if spacy_token.head else ""
    w_obj["morph"] = spacy_token.morph.to_dict()


def annotate_fallback(word_text: str, nlp) -> dict[str, Any]:
    """Fallback: Einzelnes Wort separat parsen."""
    doc = nlp(word_text)
    if len(doc) > 0:
        t = doc[0]
        return {
            "pos": t.pos_,
            "lemma": t.lemma_,
            "dep": t.dep_,
            "head_text": t.head.text if t.head else "",
            "morph": t.morph.to_dict(),
        }
    else:
        return {
            "pos": "",
            "lemma": word_text,
            "dep": "",
            "head_text": "",
            "morph": {},
        }

# ==============================================================================
# ZEITFORMEN-ERKENNUNG
# ==============================================================================

def set_past_tense_type(w_obj: dict[str, Any], label: str) -> None:
    """Setzt PastType im morph-Objekt mit englischen Labels."""
    if not isinstance(w_obj.get("morph"), dict):
        w_obj["morph"] = {}
    
    morph = w_obj["morph"]
    past_label = PAST_MAP.get(label)
    
    if past_label is not None:
        morph["PastType"] = past_label
    elif "PastType" in morph:
        del morph["PastType"]


def set_future_type(w_obj: dict[str, Any], label: str) -> None:
    """Setzt FutureType im morph-Objekt mit englischen Labels."""
    if not isinstance(w_obj.get("morph"), dict):
        w_obj["morph"] = {}
    
    morph = w_obj["morph"]
    future_label = FUTURE_MAP.get(label)
    
    if future_label is not None:
        morph["FutureType"] = future_label
    elif "FutureType" in morph:
        del morph["FutureType"]


def is_ignorable(w: dict[str, Any]) -> bool:
    """Prüft, ob Token bei Zeitformen-Suche ignoriert werden kann."""
    return (
        w.get("pos") in IGNORED_POS_GAP or
        w.get("text", "").lower() in IGNORED_TOKENS_GAP
    )


def find_near_aux_haber(
    seg_words: list[dict[str, Any]],
    idx_part: int,
    max_gap: int = 3,
) -> dict[str, Any] | None:
    """Sucht nahes AUX mit lemma='haber'."""
    def ok_gap(start_idx: int, end_idx: int) -> bool:
        gap_start = min(start_idx, end_idx) + 1
        gap_end = max(start_idx, end_idx)
        gap_tokens = seg_words[gap_start:gap_end]
        
        if not all(is_ignorable(w) for w in gap_tokens):
            return False
        return len(gap_tokens) <= max_gap
    
    for j, w in enumerate(seg_words):
        if j == idx_part:
            continue
        if w.get("pos") == "AUX" and w.get("lemma", "").lower() == "haber":
            if ok_gap(j, idx_part):
                return w
    
    return None


def classify_past_tense_form(
    w_obj: dict[str, Any],
    seg_words: list[dict[str, Any]],
    idx: int,
) -> None:
    """Klassifiziert Vergangenheitsformen."""
    morph = w_obj.get("morph", {})
    if not isinstance(morph, dict):
        return
    
    tense_vals = set(morph.get("Tense", []))
    verbform_vals = set(morph.get("VerbForm", []))
    lemma = w_obj.get("lemma", "").lower()
    pos = w_obj.get("pos")
    
    # PerfectoSimple: Past + Finite, nicht AUX
    if "Past" in tense_vals and "Fin" in verbform_vals and pos != "AUX":
        set_past_tense_type(w_obj, "PerfectoSimple")
        return
    
    # Partizip (nicht 'haber')
    if "Part" in verbform_vals and lemma != "haber":
        aux = find_near_aux_haber(seg_words, idx)
        if aux:
            aux_tense = set(aux.get("morph", {}).get("Tense", []))
            for tense_key, label in TENSE_MAP_INTERNAL.items():
                if tense_key in aux_tense:
                    set_past_tense_type(w_obj, label)
                    return
            set_past_tense_type(w_obj, "OtroCompuesto")
            return
    
    # Fallback
    if "Past" in tense_vals:
        set_past_tense_type(w_obj, "PastOther")


def post_process_compound_tenses(data: dict[str, Any]) -> None:
    """Durchläuft alle Segmente und klassifiziert Vergangenheitsformen."""
    for seg in data.get("segments", []):
        words = seg.get("words", [])
        for i, w in enumerate(words):
            morph = w.get("morph", {})
            if not isinstance(morph, dict):
                continue
            
            tense_vals = set(morph.get("Tense", []))
            verbform_vals = set(morph.get("VerbForm", []))
            
            if "Past" in tense_vals or "Part" in verbform_vals:
                classify_past_tense_form(w, words, i)


def post_process_compound_futures(data: dict[str, Any]) -> None:
    """Erkennt analytisches Futur (ir a + Inf)."""
    for seg in data.get("segments", []):
        words = seg.get("words", [])
        n = len(words)
        
        for i, w_ir in enumerate(words):
            if w_ir.get("lemma", "").lower() != "ir":
                continue
            if w_ir.get("pos") not in {"AUX", "VERB"}:
                continue
            
            tense = set(w_ir.get("morph", {}).get("Tense", []))
            
            non_ignorable_count = 0
            for j in range(i + 1, min(i + 7, n)):
                if not is_ignorable(words[j]):
                    non_ignorable_count += 1
                    if non_ignorable_count > 3:
                        break
                
                if words[j].get("text", "").lower() == "a" and words[j].get("pos") == "ADP":
                    non_ignorable_count2 = 0
                    for k in range(j + 1, min(j + 7, n)):
                        if not is_ignorable(words[k]):
                            non_ignorable_count2 += 1
                            if non_ignorable_count2 > 3:
                                break
                        
                        if (words[k].get("pos") == "VERB" and
                            "Inf" in words[k].get("morph", {}).get("VerbForm", [])):
                            
                            label = None
                            if "Pres" in tense:
                                label = "analyticalFuture"
                            elif "Imp" in tense:
                                label = "analyticalFuture_past"
                            
                            if label:
                                set_future_type(words[k], label)
                            break
                    break


def flatten_tense_features(data: dict[str, Any]) -> None:
    """Entfernt alte Token-Felder past_type/future_type."""
    for seg in data.get("segments", []):
        for w in seg.get("words", []):
            # Token-Ebene: alte Felder entfernen
            w.pop("past_type", None)
            w.pop("future_type", None)

# ==============================================================================
# FILE-ID GENERIERUNG
# ==============================================================================

def generate_file_id(relative_path: str) -> str:
    """Generiert stabile File-ID aus relativem Pfad."""
    parts = relative_path.replace("\\", "/").split("/")
    if len(parts) >= 2:
        country = parts[0]
        filename = parts[1].replace(".json", "")
        return f"{country}_{filename}"
    else:
        return hashlib.md5(relative_path.encode()).hexdigest()[:8]

# ==============================================================================
# TOKEN-ID-GENERIERUNG FÜR ALLE DATEIEN
# ==============================================================================

def collect_all_tokens(
    all_files: list[tuple[Path, str]],
) -> tuple[list[dict[str, Any]], dict[tuple[Path, int, int], int]]:
    """
    Sammelt alle Tokens aus allen Dateien für ID-Generierung.
    
    Returns:
        (all_tokens, token_index_map)
    """
    all_tokens: list[dict[str, Any]] = []
    token_index_map: dict[tuple[Path, int, int], int] = {}
    
    global_token_idx = 0
    
    for file_path, relative_name in all_files:
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            
            country_code = data.get("country_code", "")
            if not country_code:
                folder_name = file_path.parent.name
                country_code = normalize_country_code(folder_name)
            
            date_iso = data.get("date", "")
            
            for seg_idx, seg in enumerate(data.get("segments", [])):
                for tok_idx, w_obj in enumerate(seg.get("words", [])):
                    txt = w_obj.get("text", "").strip()
                    
                    # Ignorierte Tokens überspringen
                    if txt in IGNORED_TOKENS_ID or (txt and all(ch in string.punctuation for ch in txt)):
                        continue
                    
                    # Zeit auslesen (v3: ms, Fallback auf float)
                    st = w_obj.get("start")
                    if st is None:
                        st = w_obj.get("start_ms", 0) / 1000.0
                    
                    et = w_obj.get("end")
                    if et is None:
                        et = w_obj.get("end_ms", 0) / 1000.0
                    
                    existing_id = w_obj.get("token_id")
                    
                    token_data = {
                        "file_path": file_path,
                        "seg_idx": seg_idx,
                        "tok_idx": tok_idx,
                        "country_code": country_code,
                        "date": date_iso,
                        "text": txt,
                        "start": st,
                        "end": et,
                        "existing_id": existing_id,
                        "global_idx": global_token_idx,
                    }
                    
                    token_index_map[(file_path, seg_idx, tok_idx)] = len(all_tokens)
                    all_tokens.append(token_data)
                    global_token_idx += 1
        
        except Exception as e:
            logger.warning(f"Fehler beim Sammeln von {relative_name}: {e}")
            continue
    
    return all_tokens, token_index_map


def generate_all_token_ids(
    all_files: list[tuple[Path, str]],
    migrate: bool = True,
) -> dict[Path, list[tuple[int, int, str, str | None]]]:
    """
    Generiert deterministische Token-IDs für alle Dateien.
    
    Returns:
        Dict: file_path → [(seg_idx, tok_idx, new_id, existing_id), ...]
    """
    logger.info("=" * 70)
    logger.info("TOKEN-ID GENERIERUNG (Deterministisch)")
    logger.info("=" * 70)
    logger.info(f"Migrationsmodus: {'AKTIVIERT' if migrate else 'DEAKTIVIERT'}")
    
    # Phase A: Tokens sammeln
    logger.info("")
    logger.info("Phase A: Sammle alle Tokens...")
    all_tokens, _ = collect_all_tokens(all_files)
    logger.info(f"Gesammelt: {len(all_tokens):,} Tokens aus {len(all_files)} Dateien")
    
    if not all_tokens:
        return {}
    
    # Phase B: Digests berechnen
    logger.info("")
    logger.info("Phase B: Berechne Digests und Präfixlängen...")
    
    digests: list[str] = []
    cc_normalized_list: list[str] = []
    
    for token_data in all_tokens:
        cc_norm, digest = make_digest(
            token_data["country_code"],
            token_data["date"],
            token_data["start"],
            token_data["end"],
            token_data["text"],
            token_data["global_idx"],
        )
        digests.append(digest)
        cc_normalized_list.append(cc_norm)
    
    # Minimale Präfixlängen berechnen
    try:
        prefix_lengths = assign_min_unique_prefix_lengths(digests, k_start=9, k_max=16)
    except RuntimeError as e:
        logger.error(f"FEHLER: {e}")
        return {}
    
    # Token-IDs zuweisen
    for i, token_data in enumerate(all_tokens):
        token_id = make_token_id(cc_normalized_list[i], digests[i], prefix_lengths[i])
        token_data["token_id"] = token_id
        token_data["prefix_length"] = prefix_lengths[i]
    
    # Duplikatprüfung
    token_id_set: set[str] = set()
    duplicates: list[str] = []
    for token_data in all_tokens:
        tid = token_data["token_id"]
        if tid in token_id_set:
            duplicates.append(tid)
        token_id_set.add(tid)
    
    if duplicates:
        logger.error(f"FEHLER: {len(duplicates)} doppelte Token-IDs gefunden!")
        return {}
    
    # Statistik
    length_counts = Counter(prefix_lengths)
    logger.info("")
    logger.info("Token-ID Statistiken:")
    logger.info(f"  Gesamtzahl Tokens: {len(all_tokens):,}")
    logger.info(f"  Eindeutige IDs: {len(token_id_set):,}")
    logger.info("  Präfixlängen-Verteilung:")
    for length in sorted(length_counts.keys()):
        count = length_counts[length]
        pct = (count / len(all_tokens)) * 100
        logger.info(f"    {length} Hex: {count:,} ({pct:.1f}%)")
    
    # Phase C: ID-Mapping erstellen
    logger.info("")
    logger.info("Phase C: Erstelle ID-Mapping...")
    
    id_mapping: dict[Path, list[tuple[int, int, str, str | None]]] = {}
    
    for token_data in all_tokens:
        file_path = token_data["file_path"]
        if file_path not in id_mapping:
            id_mapping[file_path] = []
        
        id_mapping[file_path].append((
            token_data["seg_idx"],
            token_data["tok_idx"],
            token_data["token_id"],
            token_data["existing_id"],
        ))
    
    logger.info(f"ID-Mapping erstellt für {len(id_mapping)} Dateien")
    
    return id_mapping


def write_token_ids_to_json(
    file_path: Path,
    id_list: list[tuple[int, int, str, str | None]],
    migrate: bool = True,
) -> int:
    """
    Schreibt Token-IDs in JSON-Datei.
    
    Returns:
        Anzahl geschriebener IDs
    """
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        
        ids_written = 0
        json_modified = False
        
        for seg_idx, tok_idx, new_id, existing_id in id_list:
            if seg_idx >= len(data.get("segments", [])):
                continue
            
            words = data["segments"][seg_idx].get("words", [])
            if tok_idx >= len(words):
                continue
            
            should_write = migrate or (existing_id is None)
            
            if should_write and new_id != existing_id:
                words[tok_idx]["token_id"] = new_id
                ids_written += 1
                json_modified = True
        
        if json_modified:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        return ids_written
    
    except Exception as e:
        logger.warning(f"Fehler beim Schreiben von Token-IDs: {e}")
        return 0

# ==============================================================================
# HAUPT-ANNOTATION
# ==============================================================================

def annotate_file(
    file_path: Path,
    relative_name: str,
    force: bool,
    progress: dict[str, int],
) -> str:
    """
    Annotiert eine JSON-Datei mit v3-Schema.
    
    Returns:
        Status: "annotated", "skipped", "error"
    """
    nlp = get_nlp()
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        skip, reason = should_skip_file(data, force)
        if skip:
            return "skipped"
        
        file_id = generate_file_id(relative_name)
        
        # Alte Annotationen entfernen (behalte Basis-Felder)
        for seg in data.get("segments", []):
            for w in seg.get("words", []):
                keys_to_keep = {"text", "start", "end", "start_ms", "end_ms", "foreign", "token_id"}
                keys_to_remove = [k for k in w.keys() if k not in keys_to_keep]
                for k in keys_to_remove:
                    w.pop(k, None)
        
        # Setze sentence_id, utterance_id, start_ms, end_ms, norm
        for utt_idx, seg in enumerate(data.get("segments", [])):
            words = seg.get("words", [])
            
            utterance_id = f"{file_id}:{utt_idx}"
            
            # Berechne utt_start_ms/utt_end_ms
            if words:
                start_times: list[int] = []
                end_times: list[int] = []
                for w in words:
                    if "start" in w:
                        start_times.append(int(w["start"] * 1000))
                    elif "start_ms" in w:
                        start_times.append(w["start_ms"])
                    
                    if "end" in w:
                        end_times.append(int(w["end"] * 1000))
                    elif "end_ms" in w:
                        end_times.append(w["end_ms"])
                
                seg["utt_start_ms"] = min(start_times) if start_times else 0
                seg["utt_end_ms"] = max(end_times) if end_times else 0
            else:
                seg["utt_start_ms"] = 0
                seg["utt_end_ms"] = 0
            
            sentences = split_into_sentences(words)
            
            for sent_idx, sentence in enumerate(sentences):
                sentence_id = f"{utterance_id}:s{sent_idx}"
                
                for token in sentence:
                    token["sentence_id"] = sentence_id
                    token["utterance_id"] = utterance_id
                    
                    # Zeit in ms
                    if "start_ms" not in token:
                        token["start_ms"] = int(token.get("start", 0) * 1000)
                    if "end_ms" not in token:
                        token["end_ms"] = int(token.get("end", 0) * 1000)
                    
                    # Float-Felder entfernen (v3)
                    token.pop("start", None)
                    token.pop("end", None)
                    
                    token["norm"] = normalize_token(token.get("text", ""))
        
        # spaCy-Annotation
        for seg in data.get("segments", []):
            words = seg.get("words", [])
            if not words:
                continue
            
            sentences = split_into_sentences(words)
            
            for i, sent in enumerate(sentences):
                # Kontext für bessere Annotation
                context_words = (
                    (sentences[i-1] if i > 0 else []) +
                    sent +
                    (sentences[i+1] if i < len(sentences)-1 else [])
                )
                doc = nlp(" ".join(w.get("text", "").lower() for w in context_words))
                
                tok_idx = 0
                for w in sent:
                    txt = w.get("text", "")
                    
                    # Fremdwörter überspringen
                    if w.get("foreign") == "1":
                        w.setdefault("pos", "")
                        w.setdefault("lemma", txt)
                        w.setdefault("dep", "")
                        w.setdefault("head_text", "")
                        w.setdefault("morph", {})
                        progress["annotated"] += 1
                        continue
                    
                    # Self-Correction
                    if txt.endswith("-"):
                        w["pos"] = "self-correction"
                        w["lemma"] = txt
                        w["dep"] = ""
                        w["head_text"] = ""
                        w["morph"] = {}
                        progress["annotated"] += 1
                        continue
                    
                    # Interjektion "eeh"
                    if txt.lower() == "eeh":
                        w.update({
                            "pos": "INTJ",
                            "lemma": txt,
                            "dep": "",
                            "head_text": "",
                            "morph": {},
                        })
                        progress["annotated"] += 1
                        continue
                    
                    # Interpunktion/Whitespace überspringen
                    while tok_idx < len(doc) and (doc[tok_idx].is_punct or doc[tok_idx].is_space):
                        tok_idx += 1
                    
                    # Matching
                    if (tok_idx < len(doc) and
                        strip_punct(doc[tok_idx].text.lower()) == strip_punct(txt.lower())):
                        fill_word_annotation(w, doc[tok_idx])
                        tok_idx += 1
                    else:
                        # Suche nach Match
                        temp_idx = tok_idx
                        found = False
                        while temp_idx < len(doc):
                            if (not (doc[temp_idx].is_punct or doc[temp_idx].is_space) and
                                strip_punct(doc[temp_idx].text.lower()) == strip_punct(txt.lower())):
                                fill_word_annotation(w, doc[temp_idx])
                                temp_idx += 1
                                found = True
                                break
                            temp_idx += 1
                        tok_idx = temp_idx
                        
                        if not found:
                            # Fallback
                            fb = annotate_fallback(strip_punct(txt.lower()), nlp)
                            w.update({
                                "pos": fb["pos"],
                                "lemma": fb["lemma"],
                                "dep": fb["dep"],
                                "head_text": fb["head_text"],
                                "morph": fb["morph"],
                            })
                    
                    progress["annotated"] += 1
        
        # Post-Processing: Zeitformen
        post_process_compound_tenses(data)
        post_process_compound_futures(data)
        flatten_tense_features(data)
        
        # Metadaten
        data["ann_meta"] = {
            "version": ANN_VERSION,
            "spacy_model": SPACY_MODEL,
            "text_hash": compute_text_hash(data),
            "required": list(REQUIRED_TOKEN_FIELDS),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return "annotated"
    
    except Exception as e:
        logger.error(f"FEHLER in {relative_name}: {e}")
        return "error"

# ==============================================================================
# DATEI-SAMMLUNG
# ==============================================================================

def collect_json_files(
    country: str | None = None,
) -> list[tuple[Path, str]]:
    """
    Sammelt alle JSON-Dateien aus dem Transkript-Verzeichnis.
    
    Args:
        country: Optional, nur dieses Land verarbeiten
    
    Returns:
        Liste von (file_path, relative_name) Tupeln
    """
    all_files: list[tuple[Path, str]] = []
    
    if not TRANSCRIPTS_DIR.is_dir():
        logger.error(f"Verzeichnis nicht gefunden: {TRANSCRIPTS_DIR}")
        return []
    
    # Länderordner sammeln
    country_dirs = sorted([d for d in TRANSCRIPTS_DIR.iterdir() if d.is_dir()])
    
    for country_dir in country_dirs:
        # Filter auf Land
        if country and normalize_country_code(country_dir.name) != normalize_country_code(country):
            continue
        
        for json_file in sorted(country_dir.glob("*.json")):
            relative_name = f"{country_dir.name}/{json_file.name}"
            all_files.append((json_file, relative_name))
    
    return all_files

# ==============================================================================
# CLI & MAIN
# ==============================================================================

def parse_args() -> argparse.Namespace:
    """Parst Kommandozeilenargumente."""
    parser = argparse.ArgumentParser(
        description="Annotiert JSON-Transkripte mit dem v3-Schema.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python 02_annotate_transcripts_v3.py
  python 02_annotate_transcripts_v3.py --country ARG
  python 02_annotate_transcripts_v3.py --force --limit 10
  python 02_annotate_transcripts_v3.py --dry-run

Schema-Version: corapan-ann/v3
spaCy-Modell: es_dep_news_trf
        """,
    )
    
    parser.add_argument(
        "--country", "-c",
        type=str,
        default=None,
        help="Nur dieses Land verarbeiten (z.B. ARG, ESP)",
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Alle Dateien neu annotieren (ignoriere Idempotenz)",
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Simulation, keine Änderungen schreiben",
    )
    
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=None,
        help="Nur N Dateien annotieren",
    )
    
    parser.add_argument(
        "--skip-token-ids",
        action="store_true",
        help="Token-ID-Generierung überspringen",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Ausführliche Ausgabe",
    )
    
    return parser.parse_args()


def main() -> int:
    """Hauptfunktion."""
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Header
    logger.info("=" * 70)
    logger.info("CO.RA.PAN - Transkript-Annotation v3")
    logger.info("=" * 70)
    logger.info(f"Schema-Version: {ANN_VERSION}")
    logger.info(f"Transkript-Verzeichnis: {TRANSCRIPTS_DIR}")
    if args.country:
        logger.info(f"Filter: nur {args.country}")
    if args.force:
        logger.info("Modus: FORCE (alle neu annotieren)")
    else:
        logger.info("Modus: SAFE (Idempotenz aktiv)")
    if args.dry_run:
        logger.info("⚠️  DRY-RUN: Keine Änderungen werden geschrieben")
    logger.info("")
    
    # Dateien sammeln
    all_files = collect_json_files(country=args.country)
    
    if not all_files:
        logger.error("Keine JSON-Dateien gefunden.")
        return 1
    
    logger.info(f"Gefunden: {len(all_files)} JSON-Dateien")
    
    # Limit anwenden
    if args.limit:
        all_files = all_files[:args.limit]
        logger.info(f"Limit: verarbeite nur {args.limit} Dateien")
    
    logger.info("")
    
    # =========================================================================
    # TOKEN-ID GENERIERUNG
    # =========================================================================
    
    if not args.skip_token_ids and not args.dry_run:
        logger.info("Generiere Token-IDs für alle Dateien...")
        logger.info("(IDs werden für ALLE Dateien berechnet, nicht nur Auswahl)")
        logger.info("")
        
        # IDs für ALLE Dateien berechnen (für Konsistenz)
        all_files_full = collect_json_files(country=None)
        id_mapping = generate_all_token_ids(all_files_full, migrate=True)
        
        if not id_mapping:
            logger.error("Token-ID Generierung fehlgeschlagen.")
            return 1
        
        logger.info("")
        logger.info("Schreibe Token-IDs in JSON-Dateien...")
        
        files_modified = 0
        total_ids_written = 0
        
        for file_idx, (file_path, relative_name) in enumerate(all_files_full, 1):
            if file_idx % 20 == 0 or file_idx == len(all_files_full):
                logger.info(f"  Schreibe: {file_idx}/{len(all_files_full)} ({total_ids_written:,} IDs)")
            
            if file_path in id_mapping:
                ids_written = write_token_ids_to_json(file_path, id_mapping[file_path], migrate=True)
                if ids_written > 0:
                    files_modified += 1
                    total_ids_written += ids_written
        
        logger.info("")
        logger.info(f"Token-IDs geschrieben:")
        logger.info(f"  Dateien modifiziert: {files_modified}")
        logger.info(f"  IDs geschrieben: {total_ids_written:,}")
    
    # =========================================================================
    # ANNOTATION
    # =========================================================================
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("ANNOTATION")
    logger.info("=" * 70)
    
    # Analysiere Dateien
    logger.info("Analysiere Dateien (Idempotenz-Check)...")
    
    total_words_to_annotate = 0
    filtered_files: list[tuple[Path, str, int, str]] = []
    skip_reasons: dict[str, int] = {}
    
    for file_path, relative_name in all_files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        skip, reason = should_skip_file(data, args.force)
        
        if skip:
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            continue
        
        word_count = sum(len(seg.get("words", [])) for seg in data.get("segments", []))
        filtered_files.append((file_path, relative_name, word_count, reason))
        total_words_to_annotate += word_count
    
    logger.info("")
    logger.info(f"Zu annotieren: {len(filtered_files)} Dateien ({total_words_to_annotate:,} Wörter)")
    logger.info(f"Übersprungen: {len(all_files) - len(filtered_files)} Dateien")
    
    if skip_reasons:
        logger.info("Gründe für Überspringen:")
        for reason, count in sorted(skip_reasons.items()):
            logger.info(f"  • {reason}: {count} Dateien")
    
    if not filtered_files:
        logger.info("")
        logger.info("✅ Alle Dateien bereits aktuell (idempotent).")
        return 0
    
    if args.dry_run:
        logger.info("")
        logger.info("⚠️  DRY-RUN: Keine Annotation durchgeführt")
        return 0
    
    # Annotation durchführen
    logger.info("")
    progress = {"annotated": 0, "total": total_words_to_annotate}
    stats = {"annotated": 0, "skipped": 0, "error": 0}
    
    for idx, (file_path, relative_name, word_count, reason) in enumerate(filtered_files, 1):
        logger.info(f"[{idx}/{len(filtered_files)}] {relative_name} ({word_count:,} Wörter)")
        
        status = annotate_file(file_path, relative_name, args.force, progress)
        stats[status] = stats.get(status, 0) + 1
        
        pct = 100.0 * progress["annotated"] / progress["total"] if progress["total"] > 0 else 0
        logger.info(f"  → {status} | Fortschritt: {progress['annotated']:,}/{progress['total']:,} ({pct:.1f}%)")
    
    # Zusammenfassung
    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ ANNOTATION ABGESCHLOSSEN")
    logger.info("=" * 70)
    logger.info(f"Annotiert:    {stats['annotated']} Dateien")
    logger.info(f"Übersprungen: {stats['skipped']} Dateien")
    logger.info(f"Fehler:       {stats['error']} Dateien")
    logger.info(f"Wörter:       {progress['annotated']:,} / {progress['total']:,}")
    logger.info("")
    logger.info(f"Schema-Version: {ANN_VERSION}")
    logger.info(f"spaCy-Modell:   {SPACY_MODEL}")
    logger.info("")
    logger.info("💡 Nächster Schritt:")
    logger.info("   python 03_build_metadata_stats.py --rebuild")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
