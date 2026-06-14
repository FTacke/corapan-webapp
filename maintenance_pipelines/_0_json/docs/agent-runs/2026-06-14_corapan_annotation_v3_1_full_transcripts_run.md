# Corapan Annotation v3.1 Full Transcripts Run

Date: 2026-06-14

Status: blocked before full annotation by the explicit single-file `--validate-only` gate after timestamp repair.

## 1. Goal

Reconstruct a true pre-change backup of `media/transcripts`, then start a full v3.1 reannotation of the live transcript folder with real spaCy annotation, immutable existing `token_id` values, corpus token-id collision checks, terminal-visible progress, and post-run audit/diff checks.

## 2. Pre-Change Backup Reconstruction

The backup was reconstructed, not copied as the current mixed live state.

Procedure:

1. Copied the current full live folder `media/transcripts`.
2. Identified files touched by the 2026-06-14 v3.1 modernization and smoke tests.
3. Replaced only those touched files in the backup staging folder with the earliest old smoke/test backup that did not contain `corapan-transcript-ann-v3.1`.
4. Left the live folder untouched during reconstruction.

## 3. Touched-Files List

Path:

`maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_touched_files_for_prechange_reconstruction.json`

Result:

- Live JSON files scanned: 146
- Today-touched v3.1 files found: 28
- Missing old backups: 0

## 4. Source Map

Path:

`maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_prechange_backup_source_map.json`

Result:

- Source-map entries: 28
- Each touched file has an old backup source.
- Chosen rule: earliest readable backup without `ann_meta.pipeline_version == "corapan-transcript-ann-v3.1"` and without 2026-06-14 `ann_meta.updated_at`.

## 5. Pre-Change Backup Path

Backup root:

`maintenance_pipelines/_0_json/backups/pre-v3_1-transcripts/20260614T080916Z`

Reconstructed transcripts:

`maintenance_pipelines/_0_json/backups/pre-v3_1-transcripts/20260614T080916Z/transcripts`

## 6. Manifest Summary

Manifest:

`maintenance_pipelines/_0_json/backups/pre-v3_1-transcripts/20260614T080916Z/MANIFEST.json`

Summary:

- Country folders: 25
- JSON files: 146
- Files copied from live unchanged: 118
- Files reconstructed from old smoke/test backups: 28
- JSON read errors: 0
- `v3_1_files_in_prechange_backup`: 0

## 7. Token-ID Snapshot

Path:

`maintenance_pipelines/_0_json/backups/pre-v3_1-transcripts/20260614T080916Z/TOKEN_ID_SNAPSHOT.json`

Result:

- Snapshot entries: 146 files
- Token-level mapping includes `segment_index`, `word_index`, `text`, `start_ms`, `end_ms`, and `token_id`.

## 8. Reconstruction Report

Path:

`maintenance_pipelines/_0_json/backups/pre-v3_1-transcripts/20260614T080916Z/RECONSTRUCTION_REPORT.md`

Verification:

- Live JSON count: 146
- Backup JSON count: 146
- All backup JSON files readable: yes
- Every touched file restored from old backup: yes
- Remaining v3.1 files in pre-change backup: none

## 9. Preflight Result

Preflight JSON:

`maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_full_annotation_preflight.json`

Summary:

- `TRANSCRIPTS_DIR`: `C:\dev\corapan\media\transcripts`
- Country folders: 25
- JSON files: 146
- Total words: 1488019
- Files with missing `token_id`: 0
- Files with duplicate `token_id`: 0
- JSON read errors: 0
- Structural errors: 1
- Free disk space: about 535 GB
- spaCy version: 3.8.14
- Model loaded: `es_dep_news_trf` / `dep_news_trf` 3.8.0

Hard failure:

`media/transcripts/ARG-SDE/2025-02-07_ARG-SDE_RPanorama.json`

Offending token:

```json
{
  "segment_index": 81,
  "word_index": 15,
  "text": "con",
  "token_id": "ARGSDE85c6d3522",
  "start_ms": 354840,
  "end_ms": 354450
}
```

Reason:

`start_ms > end_ms`.

Because this is a transcript structural validation error and was defined as a hard preflight failure, the full annotation was not started at this stage.

## 9a. Timestamp Repair

Repair docs:

- `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_ARG-SDE_2025-02-07_timestamp_repair.md`
- `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_ARG-SDE_2025-02-07_timestamp_repair.json`

Manual repair backup:

`maintenance_pipelines/_0_json/backups/manual-repairs/20260614T081443Z/ARG-SDE/2025-02-07_ARG-SDE_RPanorama.before_timestamp_repair.json`

Token-ID snapshot:

`maintenance_pipelines/_0_json/backups/manual-repairs/20260614T081443Z/ARG-SDE/2025-02-07_ARG-SDE_RPanorama.token_ids.before.json`

Repair:

```json
{
  "file": "media/transcripts/ARG-SDE/2025-02-07_ARG-SDE_RPanorama.json",
  "segment_index": 81,
  "word_index": 15,
  "text": "con",
  "token_id": "ARGSDE85c6d3522",
  "old_start_ms": 354840,
  "old_end_ms": 354450,
  "new_start_ms": 354840,
  "new_end_ms": 354840
}
```

Reason:

The next token exists but starts at `354450`, earlier than the target token `start_ms`, so it is not usable as a later endpoint. The repair sets `end_ms` equal to `start_ms`, creating a minimal valid zero-length interval. No token IDs, text, lemma, POS, dependency, or morphology fields were changed.

Token-ID check for the repaired file:

- Tokens before: 11237
- Tokens after: 11237
- Changed token IDs: 0

## 9b. Preflight After Timestamp Repair

Preflight JSON:

`maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_full_annotation_preflight_after_timestamp_repair.json`

Preflight MD:

`maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_full_annotation_preflight_after_timestamp_repair.md`

Summary:

- `TRANSCRIPTS_DIR`: `C:\dev\corapan\media\transcripts`
- Country folders: 25
- JSON files: 146
- Total words: 1488019
- Files with missing `token_id`: 0
- Files with duplicate `token_id`: 0
- JSON read errors: 0
- Structural errors: 0
- Free disk space: about 535 GB
- spaCy version: 3.8.14
- Model loaded: `es_dep_news_trf` / `dep_news_trf` 3.8.0

Structural preflight is clean after the timestamp repair.

## 9c. Single-File Validate-Only Gate

Command:

```powershell
.venv\Scripts\python.exe maintenance_pipelines\_0_json\02_annotate_transcripts_v3.py --file media\transcripts\ARG-SDE\2025-02-07_ARG-SDE_RPanorama.json --validate-only --require-spacy --verbose
```

Result: failed.

The failure is no longer the timestamp issue. The strict v3.1 validation reported missing annotation fields in the still pre-full-run file, for example:

```text
segment[22].words[3] missing lemma
segment[22].words[3] missing pos
segment[22].words[3] missing dep
segment[22].words[3] missing head_text
```

Per the hard abort rule "do not fully annotate if file validation fails", the full annotation was not started.

## 10. Start Script and Command

Start script created:

`maintenance_pipelines/_0_json/run_full_transcripts_annotation.ps1`

Helper command files:

- `maintenance_pipelines/_0_json/start_full_annotation.txt`
- `start_full_annotation.txt`

Command for a later approved run after resolving or explicitly waiving the single-file strict validation gate:

```powershell
cd C:\dev\corapan
powershell -ExecutionPolicy Bypass -File maintenance_pipelines\_0_json\run_full_transcripts_annotation.ps1
```

The script runs:

```powershell
.venv\Scripts\python.exe maintenance_pipelines\_0_json\02_annotate_transcripts_v3.py --force --require-spacy --check-corpus-token-ids --verbose
```

## 11. Full Annotation Result

Not started.

Reason:

The timestamp structural error was repaired and the full structural preflight became clean, but the explicit single-file `--validate-only --require-spacy` gate failed on missing v3.1 annotation fields in a not-yet-full-annotated transcript. The hard stop condition was therefore honored.

## 12. Token-ID Diff

Not generated, because the full annotation was not started.

The pre-change token-id snapshot exists and is ready for the post-run diff:

`maintenance_pipelines/_0_json/backups/pre-v3_1-transcripts/20260614T080916Z/TOKEN_ID_SNAPSHOT.json`

## 13. Full Audit

Not generated, because the full annotation was not started.

## 14. Idempotence

Not run for the full corpus, because the full annotation was not started.

## 15. Tests

```text
6 passed in 1.54s
```

## 16. Notable Changes Made Before Abort

- Added optional terminal-visible `tqdm` progress to `02_annotate_transcripts_v3.py`.
- Existing console logs remain the fallback when `tqdm` is unavailable or output is not attached to a terminal.
- Created the full-run PowerShell starter script and command helper files.
- Repaired exactly one timestamp field in the offending live transcript token after creating a manual backup and token-id snapshot.
- Verified that no token IDs changed in the repaired file.
- Re-ran structural preflight successfully with 0 structural errors.
- Did not start full corpus annotation because strict single-file validation failed on missing pre-v3.1 annotation fields.

## 17. Recommendation for App, BlackLab, and Stats Follow-Up

Before a full annotation run:

1. Decide whether the strict `--validate-only` gate should apply to a pre-full-run transcript whose missing annotation fields are expected to be filled by the full annotation itself.
2. If yes, perform a bounded pre-annotation of the single file or adjust validation sequencing with an explicit documented rule.
3. If waived, start the prepared full annotation run because the structural preflight is now clean.
4. After successful annotation, run token-id diff, full audit, idempotence, tests, then `03_build_metadata_stats.py` verification before any BlackLab or app-facing refresh.

## 18. Cleanup Plan

No cleanup was performed.

Keep:

- smoke backups
- multi-country smoke backups
- reconstructed pre-change backup
- source maps
- preflight report
- logs
- state database
- progress files
- run documentation

Potential later cleanup should only remove redundant generated logs after the full run has been reviewed and a separate backup-retention decision exists.
