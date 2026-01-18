"""Editor overview and management routes."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from flask import Blueprint, abort, current_app, render_template, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..auth import Role
from ..auth.decorators import require_role
from ..services.database import open_db

blueprint = Blueprint("editor", __name__, url_prefix="/editor")


def _transcripts_dir() -> Path:
    return Path(current_app.config["TRANSCRIPTS_DIR"])


def _edit_log_file() -> Path:
    return _transcripts_dir() / "edit_log.jsonl"


def _ensure_edit_log() -> Path:
    edit_log = _edit_log_file()
    edit_log.parent.mkdir(parents=True, exist_ok=True)
    if not edit_log.exists():
        edit_log.touch()
    return edit_log


@blueprint.get("/")
@jwt_required()
@require_role(Role.EDITOR)
def overview():
    """
    Editor overview page: Liste aller Transcript-Files mit Metadata.

    Zeigt pro Land/Region:
    - Filename
    - Duración (aus stats_files.db)
    - Palabras (aus stats_files.db)
    - Last Edited (aus edit_log.jsonl)
    - Last Editor (aus edit_log.jsonl)
    - Edit-Button
    """
    # Dynamische Liste: Alle Länder und Regionen im TRANSCRIPTS_DIR
    transcripts_dir = _transcripts_dir()
    countries = sorted(
        [
            d.name
            for d in transcripts_dir.iterdir()
            if d.is_dir() and d.name != ".gitkeep"
        ]
    )

    files_by_country = {}

    for country in countries:
        country_dir = transcripts_dir / country
        if not country_dir.exists():
            continue

        files = []
        for json_file in sorted(country_dir.glob("*.json")):
            file_info = _get_file_info(country, json_file.name)
            files.append(file_info)

        if files:
            files_by_country[country] = files

    return render_template(
        "pages/editor_overview.html",
        files_by_country=files_by_country,
        countries=countries,
    )


@blueprint.get("/edit")
@jwt_required()
@require_role(Role.EDITOR)
def edit_file():
    """
    JSON Editor page (erweiterte Player-Seite).

    Query-Parameter:
    - file: Relativer Pfad, z.B. "ARG/2023-08-10_ARG_Mitre.json"
    """
    file_path = request.args.get("file")
    if not file_path:
        abort(400, "Missing 'file' parameter")

    # Security: Path traversal prevention
    if ".." in file_path or file_path.startswith("/"):
        abort(400, "Invalid file path")

    # Verify file exists
    full_path = _transcripts_dir() / file_path
    if not full_path.exists() or not full_path.is_file():
        abort(404, "File not found")

    # Extrahiere Audio-Pfad
    country = file_path.split("/")[0]
    mp3_filename = full_path.stem + ".mp3"
    audio_path = f"{country}/{mp3_filename}"

    return render_template(
        "pages/editor.html",
        transcript_file=file_path,
        audio_file=audio_path,
        country=country,
        filename=full_path.name,
        page_name="editor",
    )


@blueprint.post("/save-edits")
@jwt_required()
@require_role(Role.EDITOR)
def save_edits():
    """
    Speichert Word-Edits in das Transcript JSON.

    POST /editor/save-edits
    Body: {
        "file": "ARG/2023-08-10_ARG_Mitre.json",
        "changes": [{...}],
        "transcript_data": {...}
    }
    """
    data = request.get_json()

    if not data or "file" not in data or "transcript_data" not in data:
        return {"success": False, "message": "Missing required fields"}, 400

    file_path = data["file"]
    changes = data.get("changes", [])
    transcript_data = data["transcript_data"]

    # Security: Path traversal prevention
    if ".." in file_path or file_path.startswith("/"):
        return {"success": False, "message": "Invalid file path"}, 400

    full_path = _transcripts_dir() / file_path
    if not full_path.exists():
        return {"success": False, "message": "File not found"}, 404

    try:
        # 1. Create backup directory in transcript folder (media/transcripts/ARG/backup)
        backup_dir = full_path.parent / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 2. Create/maintain _original backup (never deleted, never overwritten)
        original_backup_path = backup_dir / f"{full_path.stem}_original.json"
        if not original_backup_path.exists():
            with open(full_path, "r", encoding="utf-8") as f:
                original_data = f.read()
            with open(original_backup_path, "w", encoding="utf-8") as f:
                f.write(original_data)
            current_app.logger.info(
                f"[Backup] Created permanent original: {original_backup_path}"
            )

        # 3. SAVE DIFFS instead of timestamped backups (NEW SYSTEM)
        # Dieser Schritt speichert nur die Changes, nicht die komplette Datei
        _save_diff_to_history(backup_dir, full_path.stem, changes)

        # NOTE: Alte Logik (_cleanup_old_backups) ist nicht mehr nötig
        # Diffs sind minimal klein, wir speichern sie alle

        # 2. Write updated transcript atomically
        temp_path = full_path.with_suffix(".json.tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)

        # Atomic replace
        temp_path.replace(full_path)

        # 3. Log to edit_log.jsonl
        identity = get_jwt_identity()
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": identity,
            "file": file_path,
            "action": "word_edit",
            "changes_count": len(changes),
            "changes": changes,
        }

        edit_log = _ensure_edit_log()
        with open(edit_log, "a", encoding="utf-8") as log:
            log.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return {
            "success": True,
            "message": f"{len(changes)} changes saved",
            "backup": "diff-based",  # Changed to diff-based system
        }, 200

    except Exception as e:
        return {"success": False, "message": f"Save failed: {str(e)}"}, 500


@blueprint.post("/bookmarks/add")
@jwt_required()
@require_role(Role.EDITOR)
def add_bookmark():
    """
    Adds a bookmark to a segment.

    POST /editor/bookmarks/add
    Body: {
        "file": "ARG/2023-08-10_ARG_Mitre.json",
        "segment_index": 5,
        "note": "Important moment"
    }
    """
    data = request.get_json()

    if not data or "file" not in data or "segment_index" not in data:
        return {"success": False, "message": "Missing required fields"}, 400

    file_path = data["file"]
    segment_index = data.get("segment_index")
    note = data.get("note", "")

    # Security: Path traversal prevention
    if ".." in file_path or file_path.startswith("/"):
        return {"success": False, "message": "Invalid file path"}, 400

    full_path = _transcripts_dir() / file_path
    if not full_path.exists():
        return {"success": False, "message": "File not found"}, 404

    try:
        # Read current transcript
        with open(full_path, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)

        # Initialize bookmarks array if not exists
        if "bookmarks" not in transcript_data:
            transcript_data["bookmarks"] = []

        # Check if bookmark already exists for this segment
        existing = next(
            (
                b
                for b in transcript_data["bookmarks"]
                if b.get("segment_index") == segment_index
            ),
            None,
        )
        if existing:
            return {
                "success": False,
                "message": "Bookmark already exists for this segment",
            }, 400

        # Add bookmark
        bookmark = {
            "segment_index": segment_index,
            "note": note,
            "created_at": datetime.now().isoformat(),
            "created_by": get_jwt_identity(),
        }
        transcript_data["bookmarks"].append(bookmark)

        # Save
        temp_path = full_path.with_suffix(".json.tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)
        temp_path.replace(full_path)

        return {"success": True, "message": "Bookmark added", "bookmark": bookmark}, 200

    except Exception as e:
        return {"success": False, "message": f"Failed to add bookmark: {str(e)}"}, 500


@blueprint.post("/bookmarks/remove")
@jwt_required()
@require_role(Role.EDITOR)
def remove_bookmark():
    """
    Removes a bookmark from a segment.

    POST /editor/bookmarks/remove
    Body: {
        "file": "ARG/2023-08-10_ARG_Mitre.json",
        "segment_index": 5
    }
    """
    data = request.get_json()

    if not data or "file" not in data or "segment_index" not in data:
        return {"success": False, "message": "Missing required fields"}, 400

    file_path = data["file"]
    segment_index = data.get("segment_index")

    # Security: Path traversal prevention
    if ".." in file_path or file_path.startswith("/"):
        return {"success": False, "message": "Invalid file path"}, 400

    full_path = _transcripts_dir() / file_path
    if not full_path.exists():
        return {"success": False, "message": "File not found"}, 404

    try:
        # Read current transcript
        with open(full_path, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)

        # Remove bookmark if exists
        if "bookmarks" in transcript_data:
            transcript_data["bookmarks"] = [
                b
                for b in transcript_data["bookmarks"]
                if b.get("segment_index") != segment_index
            ]

        # Save
        temp_path = full_path.with_suffix(".json.tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)
        temp_path.replace(full_path)

        return {"success": True, "message": "Bookmark removed"}, 200

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to remove bookmark: {str(e)}",
        }, 500


@blueprint.get("/history/<country>/<path:filename>")
@jwt_required()
@require_role(Role.EDITOR)
def get_history(country: str, filename: str):
    """
    Gets change history for a transcript file.

    GET /editor/history/ARG/2023-08-10_ARG_Mitre.json

    Returns all changes chronologically with metadata from diffs.jsonl
    """
    file_path = f"{country}/{filename}"

    # Security: Path traversal prevention
    if ".." in file_path or file_path.startswith("/"):
        return {"success": False, "message": "Invalid file path"}, 400

    full_path = _transcripts_dir() / file_path
    if not full_path.exists():
        return {"success": False, "message": "File not found"}, 404

    try:
        diffs_file = full_path.parent / "backup" / f"{full_path.stem}_diffs.jsonl"

        history = []
        if diffs_file.exists():
            with open(diffs_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    history.append(entry)

        return {"success": True, "history": history, "count": len(history)}, 200

    except Exception as e:
        return {"success": False, "message": f"Failed to get history: {str(e)}"}, 500


@blueprint.post("/undo")
@jwt_required()
@require_role(Role.EDITOR)
def undo_change():
    """
    Revert a specific change from history.

    POST /editor/undo
    Body: {
        "file": "ARG/2023-08-10_ARG_Mitre.json",
        "undo_index": 3
    }
    """
    data = request.get_json()

    if not data or "file" not in data or "undo_index" not in data:
        return {"success": False, "message": "Missing required fields"}, 400

    file_path = data["file"]
    undo_index = data.get("undo_index")

    # Security: Path traversal prevention
    if ".." in file_path or file_path.startswith("/"):
        return {"success": False, "message": "Invalid file path"}, 400

    full_path = _transcripts_dir() / file_path
    if not full_path.exists():
        return {"success": False, "message": "File not found"}, 404

    try:
        backup_dir = full_path.parent / "backup"
        original_backup_path = backup_dir / f"{full_path.stem}_original.json"
        diffs_file = backup_dir / f"{full_path.stem}_diffs.jsonl"

        if not original_backup_path.exists():
            return {"success": False, "message": "Original backup not found"}, 500

        # Rekonstruiere State OHNE die zu undoende Change
        # Wir bauen den State auf bis zur undo_index - 1
        state = _reconstruct_from_diffs(
            original_backup_path, diffs_file, until_index=undo_index - 1
        )

        # Speichere neue State
        temp_path = full_path.with_suffix(".json.tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        temp_path.replace(full_path)

        # Log den Undo als neuer Eintrag in diffs.jsonl
        undo_entry = {
            "index": _get_next_diff_index(diffs_file),
            "timestamp": datetime.now().isoformat(),
            "type": "undo",
            "user": get_jwt_identity(),
            "reversed_index": undo_index,
            "message": f"Reverted change #{undo_index}",
        }

        with open(diffs_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(undo_entry, ensure_ascii=False) + "\n")

        # Log zu edit_log
        identity = get_jwt_identity()
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": identity,
            "file": file_path,
            "action": "undo_change",
            "undo_index": undo_index,
        }

        edit_log = _ensure_edit_log()
        with open(edit_log, "a", encoding="utf-8") as log:
            log.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return {
            "success": True,
            "message": f"Change #{undo_index} reverted successfully",
        }, 200

    except Exception as e:
        return {"success": False, "message": f"Failed to undo change: {str(e)}"}, 500


@blueprint.get("/bookmarks/<country>/<path:filename>")
@jwt_required()
@require_role(Role.EDITOR)
def get_bookmarks(country: str, filename: str):
    """
    Gets all bookmarks for a transcript file.

    GET /editor/bookmarks/ARG/2023-08-10_ARG_Mitre.json
    """
    file_path = f"{country}/{filename}"

    # Security: Path traversal prevention
    if ".." in file_path or file_path.startswith("/"):
        return {"success": False, "message": "Invalid file path"}, 400

    full_path = _transcripts_dir() / file_path
    if not full_path.exists():
        return {"success": False, "message": "File not found"}, 404

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)

        bookmarks = transcript_data.get("bookmarks", [])

        return {"success": True, "bookmarks": bookmarks, "count": len(bookmarks)}, 200

    except Exception as e:
        return {"success": False, "message": f"Failed to get bookmarks: {str(e)}"}, 500


def _get_file_info(country: str, filename: str) -> dict:
    """
    Sammelt alle Metadaten für ein Transcript-File.

    Returns:
        {
            'country': 'ARG',
            'filename': '2023-08-10_ARG_Mitre.json',
            'duration': '02:34:12',
            'word_count': 8432,
            'last_edited': '2025-10-20T14:32:15' or None,
            'last_editor': 'editor_test' or None
        }
    """
    # Hole Duración und Palabras aus stats_files.db
    duration = "N/A"
    word_count = 0

    try:
        with open_db("stats_files") as conn:
            cursor = conn.execute(
                "SELECT duration, word_count FROM metadata WHERE filename = ? AND country_code = ?",
                (filename, country),
            )
            row = cursor.fetchone()
            if row:
                duration = row["duration"] or "N/A"
                word_count = row["word_count"] or 0
    except Exception as e:
        current_app.logger.error(f"[Editor] Error loading stats for {filename}: {e}")

    # Hole Last Edited aus edit_log.jsonl
    last_edited = None
    last_editor = None

    edit_log = _edit_log_file()
    if edit_log.exists():
        try:
            # Lies Log rückwärts und finde letzten Eintrag für dieses File
            with edit_log.open("r", encoding="utf-8") as log:
                lines = log.readlines()

            for line in reversed(lines):
                if not line.strip():
                    continue
                entry = json.loads(line)
                if entry.get("file") == f"{country}/{filename}":
                    last_edited = entry.get("timestamp")
                    last_editor = entry.get("user")
                    break
        except Exception as e:
            print(f"[Editor] Error reading edit log: {e}")

    return {
        "country": country,
        "filename": filename,
        "duration": duration or "N/A",
        "word_count": word_count or 0,
        "last_edited": last_edited,
        "last_editor": last_editor,
    }


def _cleanup_old_backups(backup_dir: Path, stem: str, max_backups: int = 10) -> None:
    """
    Cleanup old timestamped backups, keeping only the latest N versions.
    Never deletes the _original backup.

    Args:
        backup_dir: Directory containing backups
        stem: Filename stem (e.g., "2023-08-10_ARG_Mitre")
        max_backups: Maximum number of timestamped backups to keep (default: 10)
    """
    try:
        # Find all timestamped backups for this file (not _original)
        backups = sorted(
            [
                f
                for f in backup_dir.glob(f"{stem}_*.json")
                if f.name != f"{stem}_original.json"
            ],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        # Delete older backups beyond max_backups
        if len(backups) > max_backups:
            for old_backup in backups[max_backups:]:
                old_backup.unlink()
                print(f"[Backup] Deleted old: {old_backup.name}")

        print(
            f"[Backup] Kept {min(len(backups), max_backups)} timestamped backups + 1 original"
        )

    except Exception as e:
        print(f"[Backup] Error cleaning up old backups: {e}")


def _save_diff_to_history(backup_dir: Path, stem: str, changes: list) -> None:
    """
    Speichert Changes als Diffs in diffs.jsonl statt kompletter Backups.
    Jede Zeile ist ein selbständiger Change-Eintrag (JSONL Format).

    Args:
        backup_dir: Backup-Verzeichnis
        stem: Filename stem (z.B. "2023-08-10_ARG_Mitre")
        changes: Array von {segmentIndex, wordIndex, oldVal, newVal}
    """
    try:
        diffs_file = backup_dir / f"{stem}_diffs.jsonl"

        # Finde letzten Index
        last_index = 0
        if diffs_file.exists():
            with open(diffs_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if lines:
                last_entry = json.loads(lines[-1])
                last_index = last_entry.get("index", 0)

        # Erstelle neuen Entry
        entry = {
            "index": last_index + 1,
            "timestamp": datetime.now().isoformat(),
            "user": get_jwt_identity(),
            "changes": changes,
        }

        # Append zu diffs.jsonl
        with open(diffs_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print(f"[Diff] Saved change #{entry['index']}: {len(changes)} changes")

    except Exception as e:
        print(f"[Diff] Error saving diff: {e}")


def _get_next_diff_index(diffs_file: Path) -> int:
    """Finde nächsten Index in diffs.jsonl"""
    if not diffs_file.exists():
        return 1

    with open(diffs_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        return 1

    last_entry = json.loads(lines[-1])
    return last_entry.get("index", 0) + 1


def _reconstruct_from_diffs(
    original_path: Path, diffs_file: Path, until_index: int = None
) -> dict:
    """
    Rekonstruiere JSON-State von Original + Diffs bis zu einem bestimmten Index.

    Args:
        original_path: Path zur _original.json
        diffs_file: Path zur _diffs.jsonl
        until_index: Rekonstruiere bis zu diesem Index (inclusive). None = alle

    Returns:
        Rekonstruierter JSON als Dictionary
    """
    try:
        # Lade Original
        with open(original_path, "r", encoding="utf-8") as f:
            state = json.load(f)

        # Wende Diffs an
        if diffs_file.exists():
            with open(diffs_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    entry = json.loads(line)

                    # Skip wenn wir bis_index erreicht haben
                    if until_index is not None and entry.get("index", 0) > until_index:
                        break

                    # Skip wenn es ein Undo ist (type: "undo") - diese werden nicht angewendet
                    if entry.get("type") == "undo":
                        continue

                    # Wende Changes an
                    changes = entry.get("changes", [])
                    for change in changes:
                        seg_idx = change.get("segment_index")
                        word_idx = change.get("word_index")
                        new_val = change.get("new_value")

                        if (
                            seg_idx is not None
                            and word_idx is not None
                            and seg_idx < len(state.get("segments", []))
                            and word_idx
                            < len(state["segments"][seg_idx].get("words", []))
                        ):
                            state["segments"][seg_idx]["words"][word_idx]["value"] = (
                                new_val
                            )

        return state

    except Exception as e:
        print(f"[Diff] Error reconstructing from diffs: {e}")
        raise
