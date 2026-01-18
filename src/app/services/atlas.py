"""Atlas metadata services."""

from __future__ import annotations

import csv
import json
import logging
import os
import warnings
from pathlib import Path

from flask import current_app, has_app_context

from .database import open_db


def fetch_country_stats() -> list[dict[str, object]]:
    from ..config.countries import code_to_name

    with open_db("stats_country") as connection:
        cursor = connection.cursor()
        rows = cursor.execute(
            "SELECT country_code, total_word_count, total_duration_country FROM stats_country ORDER BY country_code"
        ).fetchall()
    return [
        {
            "country_code": row["country_code"],
            "country_name": code_to_name(
                row["country_code"], fallback=row["country_code"]
            ),
            "total_word_count": row["total_word_count"],
            "total_duration": row["total_duration_country"],
        }
        for row in rows
    ]


_FILES_CACHE: dict[str, object] = {"mtime": None, "files": []}


def _resolve_metadata_root() -> Path | None:
    env_name = (os.getenv("FLASK_ENV") or os.getenv("APP_ENV") or "production").lower()
    is_dev = env_name in ("development", "dev")
    runtime_root = os.getenv("CORAPAN_RUNTIME_ROOT")

    if runtime_root:
        return Path(runtime_root) / "data" / "public" / "metadata"

    if is_dev:
        data_root = Path(__file__).resolve().parents[3] / "runtime" / "corapan" / "data"
        warnings.warn(
            "CORAPAN_RUNTIME_ROOT not configured. Defaulting to repo-local runtime path for development: "
            f"{data_root}",
            RuntimeWarning,
        )
        return data_root / "public" / "metadata"

    return None


def _select_metadata_dir(root: Path) -> Path:
    return root / "tei"


def _metadata_dir_has_files(metadata_dir: Path) -> bool:
    if not metadata_dir.exists():
        return False
    candidates = list(metadata_dir.glob("corapan_recordings*.json"))
    candidates += list(metadata_dir.glob("corapan_recordings*.tsv"))
    candidates = [p for p in candidates if not p.name.endswith(".jsonld")]
    return len(candidates) > 0


def _get_metadata_mtime(metadata_dir: Path) -> float | None:
    if not metadata_dir.exists():
        return None
    candidates = list(metadata_dir.glob("corapan_recordings*.json"))
    candidates += list(metadata_dir.glob("corapan_recordings*.tsv"))
    candidates = [p for p in candidates if not p.name.endswith(".jsonld")]
    if not candidates:
        return metadata_dir.stat().st_mtime
    return max(p.stat().st_mtime for p in candidates)


def _safe_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _seconds_to_hms(seconds: int | None) -> str | None:
    if seconds is None:
        return None
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _normalize_recording(record: dict[str, object]) -> dict[str, object]:
    filename = record.get("filename") or record.get("file_id") or record.get("fileId")
    country_code = (
        record.get("country_code")
        or record.get("country_code_alpha3")
        or record.get("country")
    )
    radio = record.get("radio") or record.get("radio_name") or record.get("station")
    date = record.get("date") or record.get("recording_date")
    revision = record.get("revision") or record.get("annotation_version")
    word_count = (
        record.get("word_count")
        or record.get("words_transcribed")
        or record.get("wordCount")
    )
    duration = record.get("duration") or record.get("duration_hms")
    if not duration:
        duration_seconds = _safe_int(record.get("duration_seconds"))
        duration = _seconds_to_hms(duration_seconds)

    return {
        "filename": filename,
        "country_code": country_code,
        "radio": radio,
        "date": date,
        "revision": revision,
        "word_count": _safe_int(word_count),
        "duration": duration,
    }


def _load_recordings_from_json(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = payload.get("recordings") or payload.get("items") or []
    else:
        records = []
    return [record for record in records if isinstance(record, dict)]


def _load_recordings_from_tsv(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [row for row in reader]


def _collect_recordings(metadata_dir: Path) -> list[dict[str, object]]:
    json_master = metadata_dir / "corapan_recordings.json"
    if json_master.exists():
        return _load_recordings_from_json(json_master)

    json_candidates = sorted(
        [p for p in metadata_dir.glob("corapan_recordings_*.json") if not p.name.endswith(".jsonld")]
    )
    if json_candidates:
        records: list[dict[str, object]] = []
        for candidate in json_candidates:
            records.extend(_load_recordings_from_json(candidate))
        return records

    tsv_master = metadata_dir / "corapan_recordings.tsv"
    if tsv_master.exists():
        return _load_recordings_from_tsv(tsv_master)

    tsv_candidates = sorted(metadata_dir.glob("corapan_recordings_*.tsv"))
    records = []
    for candidate in tsv_candidates:
        records.extend(_load_recordings_from_tsv(candidate))
    return records


def fetch_file_metadata() -> list[dict[str, object]]:
    logger = current_app.logger if has_app_context() else logging.getLogger(__name__)
    metadata_root = _resolve_metadata_root()
    if not metadata_root or not metadata_root.exists():
        logger.warning(
            "Atlas metadata directory not available; returning empty files list."
        )
        return []

    metadata_dir = _select_metadata_dir(metadata_root)
    if not _metadata_dir_has_files(metadata_dir):
        logger.warning(
            "Atlas metadata directory missing or empty at %s; returning empty files list.",
            metadata_dir,
        )
        return []
    dir_mtime = _get_metadata_mtime(metadata_dir)
    if dir_mtime is not None and _FILES_CACHE.get("mtime") == dir_mtime:
        return list(_FILES_CACHE.get("files", []))

    try:
        recordings = _collect_recordings(metadata_dir)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load atlas metadata files: %s", exc)
        return []

    files = [_normalize_recording(record) for record in recordings]
    files.sort(key=lambda item: item.get("date") or "", reverse=True)

    _FILES_CACHE["mtime"] = dir_mtime
    _FILES_CACHE["files"] = files

    return list(files)
