# Corapan Annotation v3.1 Real spaCy Follow-up

- Date: 2026-06-14
- Scope: `maintenance_pipelines/_0_json`
- Pipeline: `corapan-transcript-ann-v3.1`
- Smoke file: `media/transcripts/ARG/2023-08-12_ARG_Mitre.json`

## Fixes Completed

- Added robust project-root detection in `02_annotate_transcripts_v3.py`.
- Added country normalizer candidate lookup for:
  - `PROJECT_ROOT/src/app/config/countries.py`
  - `PROJECT_ROOT/app/src/app/config/countries.py`
- Added startup logging for `SCRIPT_DIR`, `PROJECT_ROOT`, `TRANSCRIPTS_DIR`, `COUNTRIES_PY`, and `TRANSCRIPTS_DIR.exists()`.
- Added `--require-spacy`.
- Hardened audit GREEN rules so missing or preserved-only spaCy annotation cannot be GREEN.
- Changed `ann_meta.tense_audit.TenseRole` to final token-based counts so it matches the transcript audit exactly.

## Resolved Paths

- `SCRIPT_DIR`: `C:\dev\corapan\maintenance_pipelines\_0_json`
- `PROJECT_ROOT`: `C:\dev\corapan`
- `TRANSCRIPTS_DIR`: `C:\dev\corapan\media\transcripts`
- `COUNTRIES_PY`: `C:\dev\corapan\app\src\app\config\countries.py`
- `TRANSCRIPTS_DIR.exists()`: `True`

## spaCy Runtime

- spaCy version: `3.8.14`
- Model requested: `es_dep_news_trf`
- Model loaded: `dep_news_trf 3.8.0`
- Smoke `ann_meta.spacy_version`: `3.8.14`
- Smoke `ann_meta.spacy_model`: `es_dep_news_trf`
- Smoke `special_token_audit.spacy_annotation_mode`: `model`

## Backups and Snapshots

Smoke backup:

- `maintenance_pipelines/_0_json/backups/smoke-tests/20260614T070629Z/ARG/2023-08-12_ARG_Mitre.json`
- `maintenance_pipelines/_0_json/backups/smoke-tests/20260614T070629Z/ARG/2023-08-12_ARG_Mitre.token_ids.before.json`

The annotator also created its own file backup:

- `maintenance_pipelines/_0_json/backups/smoke-tests/20260614T070639Z/ARG/2023-08-12_ARG_Mitre.json`

Mini-batch backup:

- `maintenance_pipelines/_0_json/backups/smoke-tests/20260614T070749Z/ARG/2023-08-10_ARG_Mitre.json`
- `maintenance_pipelines/_0_json/backups/smoke-tests/20260614T070749Z/ARG/2023-08-10_ARG_Mitre.token_ids.before.json`
- `maintenance_pipelines/_0_json/backups/smoke-tests/20260614T070749Z/ARG/2023-08-12_ARG_Mitre.json`
- `maintenance_pipelines/_0_json/backups/smoke-tests/20260614T070749Z/ARG/2023-08-12_ARG_Mitre.token_ids.before.json`
- `maintenance_pipelines/_0_json/backups/smoke-tests/20260614T070749Z/ARG/2023-08-16_ARG_Mitre.json`
- `maintenance_pipelines/_0_json/backups/smoke-tests/20260614T070749Z/ARG/2023-08-16_ARG_Mitre.token_ids.before.json`

## Smoke Commands

Real spaCy annotation:

```powershell
.venv\Scripts\python.exe maintenance_pipelines\_0_json\02_annotate_transcripts_v3.py --file media\transcripts\ARG\2023-08-12_ARG_Mitre.json --force --require-spacy --verbose
```

Validation:

```powershell
.venv\Scripts\python.exe maintenance_pipelines\_0_json\02_annotate_transcripts_v3.py --file media\transcripts\ARG\2023-08-12_ARG_Mitre.json --validate-only --verbose
```

Audit:

```powershell
.venv\Scripts\python.exe maintenance_pipelines\_0_json\audit_transcript_annotation_quality.py --file media\transcripts\ARG\2023-08-12_ARG_Mitre.json --out maintenance_pipelines\_0_json\docs\agent-runs\audits\2026-06-14_ARG_Mitre_annotation_audit_spacy_real.md --json-out maintenance_pipelines\_0_json\docs\agent-runs\audits\2026-06-14_ARG_Mitre_annotation_audit_spacy_real.json
```

Idempotence:

```powershell
.venv\Scripts\python.exe maintenance_pipelines\_0_json\02_annotate_transcripts_v3.py --file media\transcripts\ARG\2023-08-12_ARG_Mitre.json --require-spacy --verbose
```

## Smoke Result

- Real spaCy loaded: yes.
- JSON validation: passed, 0 warnings.
- Existing token IDs changed: `0`.
- Duplicate token IDs: `0`.
- Missing token IDs: `0`.
- Legacy `past_type` / `future_type`: absent.
- Audit: `GREEN`.
- Audit hard gate failures: none.
- Idempotence: `skipped (up-to-date)`.
- Progress JSON/JSONL: written.
- State DB: written.

Smoke audit:

- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_Mitre_annotation_audit_spacy_real.md`
- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_Mitre_annotation_audit_spacy_real.json`

TenseRole consistency:

- `ann_meta.tense_audit.TenseRole`: `lexical_participle=46`, `finite_past=116`, `compound_participle=26`, `auxiliary=41`, `future_infinitive=9`
- Audit `TenseRole Counts`: same values.

## Optional Mini-Batch

Because the real spaCy smoke was GREEN, a limited batch was run:

```powershell
.venv\Scripts\python.exe maintenance_pipelines\_0_json\02_annotate_transcripts_v3.py --country ARG --limit 3 --force --require-spacy --check-corpus-token-ids --verbose
```

Selected files:

- `media/transcripts/ARG/2023-08-10_ARG_Mitre.json`
- `media/transcripts/ARG/2023-08-12_ARG_Mitre.json`
- `media/transcripts/ARG/2023-08-16_ARG_Mitre.json`

Batch result:

- Processed files: `3`.
- Existing token IDs changed: `0` for all three files.
- Duplicate token IDs: `0` for all three files.
- Missing token IDs: `0` for all three files.
- Audit decision: `GREEN` for all three files.
- Hard gate failures: none.
- TenseRole meta/token counts: matched for all three files.

Batch audit:

- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_limit3_annotation_audit_spacy_real.md`
- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_limit3_annotation_audit_spacy_real.json`

Batch idempotence:

```powershell
.venv\Scripts\python.exe maintenance_pipelines\_0_json\02_annotate_transcripts_v3.py --country ARG --limit 3 --require-spacy --verbose
```

Result: all three files `skipped (up-to-date)`.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest maintenance_pipelines\_0_json\tests -q
```

Result: `6 passed`.

Covered:

- Root detection finds `C:\dev\corapan`.
- `--require-spacy` path fails when the configured model cannot load.
- Audit does not mark `spacy_version == "not-installed"` as GREEN.
- TenseRole stats match final token counts.
- Existing token IDs remain unchanged under `--force`.

## Rest Problems

- The limited ARG batch changed three transcript JSON files by design. No corpus-wide processing was run.
- The current audit validates annotation quality and structural safety, but manual linguistic review of a larger multi-country sample is still recommended before a broad reannotation.

## Recommendation

Next staged run: choose a small multi-country sample with `--file` or country-specific `--limit`, require spaCy, audit every selected file, and only then plan a larger country-by-country run.
