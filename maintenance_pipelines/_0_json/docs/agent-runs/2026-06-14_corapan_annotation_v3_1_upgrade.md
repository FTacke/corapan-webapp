# Corapan Annotation v3.1 Upgrade

- Date: 2026-06-14
- Scope: `maintenance_pipelines/_0_json`
- Smoke file: `media/transcripts/ARG/2023-08-12_ARG_Mitre.json`
- Pipeline target: `corapan-transcript-ann-v3.1`

## What Changed

- Reworked `02_annotate_transcripts_v3.py` as a transcript-native v3.1 annotator.
- Kept the Corapan data model: top-level metadata, `segments[]`, `segments[].words[]`, speaker fields, utterance timing, and word timing.
- Removed the global corpus-wide token-ID rewrite path.
- Added local-only generation for missing `token_id` values using:
  `country_code | date | file_id/filename | segment_index | word_index | start_ms | end_ms | text`.
- Added collision checks for generated IDs within the processed file, plus optional corpus-wide checking with `--check-corpus-token-ids`.
- Added modern `ann_meta` fields: `schema_version`, `pipeline_version`, `script`, `input_hash`, `annotation_hash`, timestamps, spaCy/model versions, tense/validation versions, stage metadata, token-ID policy, and transcript-special rules version.
- Added transcript validation, SQLite state, progress JSON/JSONL, and file logging under `_0_json`.
- Added `audit_transcript_annotation_quality.py` for transcript-native Markdown/JSON audits.
- Added focused pytest coverage under `maintenance_pipelines/_0_json/tests/`.

## Coprepan References Adapted

- Versioned stage metadata and idempotence checks from `docs/annotation_coprepan/annotate_articles.py`.
- State/progress/log layout patterns from the Coprepan annotation runner, relocated under `maintenance_pipelines/_0_json`.
- Tense audit categories from `docs/annotation_coprepan/audit_annotation_quality.py`.
- Tense labels compatible with Coprepan tokens:
  `PastType`, `FutureType`, `VoiceType`, `TenseRole`.

The Coprepan article structure was not copied. Corapan remains a transcript corpus.

## Corapan Specifics Preserved

- `segments[]` and `segments[].words[]` remain the processing surface.
- Existing `speaker`, `speaker_code`, `utt_start_ms`, `utt_end_ms`, `start_ms`, and `end_ms` are retained.
- Self-corrections ending in `-` are handled by `annotate_special_transcript_token`.
- `foreign == "1"` and known foreign tokens are not normal spaCy-overwritten.
- Filler `eeh` is controlled as `INTJ`.
- Fragmentary transcript sentences still use punctuation-based sentence IDs and fallback annotation.

## Token-ID Safety Rule

- Existing `token_id` values are immutable, including in `--force`.
- Only missing IDs are filled.
- Existing IDs before smoke: `4755`.
- Existing IDs after smoke: `4755`.
- Unchanged existing IDs: `4755`.
- Added IDs: `0`.
- Changed existing IDs: `0`.
- Duplicate IDs after smoke: `0`.

## New CLI Options

- `--file <path>`: process exactly one JSON.
- `--resume`: idempotent resume mode.
- `--retry-failed`: select files marked failed in state DB.
- `--validate-only`: validate selected files without annotation writes.
- `--check-corpus-token-ids`: include all other transcript IDs in collision avoidance for newly generated IDs.

Existing `--country`, `--limit`, `--force`, `--dry-run`, and `--verbose` remain.

## New Artifacts

- Log: `maintenance_pipelines/_0_json/logs/annotation/annotate_transcripts.log`
- Progress JSON: `maintenance_pipelines/_0_json/logs/annotation_progress.json`
- Progress JSONL: `maintenance_pipelines/_0_json/logs/annotation_progress.jsonl`
- State DB: `maintenance_pipelines/_0_json/state/annotation/annotation_state.sqlite`
- Docs: `maintenance_pipelines/_0_json/docs/agent-runs/`
- Audits: `maintenance_pipelines/_0_json/docs/agent-runs/audits/`
- Smoke backups: `maintenance_pipelines/_0_json/backups/smoke-tests/`

## Smoke-Test Commands

Backup and token-ID snapshot were created before the writing run:

```powershell
media/transcripts/ARG/2023-08-12_ARG_Mitre.json
maintenance_pipelines/_0_json/backups/smoke-tests/20260614T065220Z/ARG/2023-08-12_ARG_Mitre.json
maintenance_pipelines/_0_json/backups/smoke-tests/20260614T065220Z/ARG/2023-08-12_ARG_Mitre.token_ids.before.json
```

Annotator smoke:

```powershell
python maintenance_pipelines/_0_json/02_annotate_transcripts_v3.py --file media/transcripts/ARG/2023-08-12_ARG_Mitre.json --force --verbose
```

Validation:

```powershell
python maintenance_pipelines/_0_json/02_annotate_transcripts_v3.py --file media/transcripts/ARG/2023-08-12_ARG_Mitre.json --validate-only --verbose
```

Audit:

```powershell
python maintenance_pipelines/_0_json/audit_transcript_annotation_quality.py --file media/transcripts/ARG/2023-08-12_ARG_Mitre.json --out maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_Mitre_annotation_audit.md --json-out maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_Mitre_annotation_audit.json
```

Idempotence:

```powershell
python maintenance_pipelines/_0_json/02_annotate_transcripts_v3.py --file media/transcripts/ARG/2023-08-12_ARG_Mitre.json
```

Focused tests:

```powershell
.venv/Scripts/python.exe -m pytest maintenance_pipelines/_0_json/tests/test_annotate_transcripts_v3_1.py -q
```

## Smoke-Test Result

- JSON syntax: passed.
- Transcript validation: passed, 0 warnings.
- Duplicate token IDs: 0.
- Existing token IDs changed: 0.
- Legacy `past_type` / `future_type`: absent.
- `ann_meta`: modernized and still has `version: corapan-ann/v3`.
- Tense fields: present in `morph` where detected.
- Progress files: written.
- State DB: written, row status `done`.
- Audit report: generated.
- Audit decision: `GREEN`.
- Second non-force run: `skipped (up-to-date)`.

`03_build_metadata_stats.py --country ARG --verify-only` was not run because `CORAPAN_RUNTIME_ROOT` is not configured in this shell. That script requires runtime data configuration at import time.

## Known Rest Problems

- Local Python and the repo venv do not have spaCy installed, so the smoke run preserved existing spaCy token annotations instead of recomputing them. The code path is ready to use `es_dep_news_trf` when installed.
- The first larger run should be staged and reviewed because Tense rules are now stricter about lexical participles and passive/resultative constructions.
- `docs/annotation_coprepan/` is untracked reference material in this workspace.

## Recommendation

Next step: install/verify `spacy` plus `es_dep_news_trf`, then run one small country-limited batch with an explicit limit, for example `--country ARG --limit 3 --force`, followed by audit review before any larger corpus run.
