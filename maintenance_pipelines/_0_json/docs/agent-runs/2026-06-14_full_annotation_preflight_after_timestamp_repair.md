# Full Annotation Preflight After Timestamp Repair

Date: 2026-06-14

## Summary

- `TRANSCRIPTS_DIR`: `C:\dev\corapan\media\transcripts`
- Exists: `True`
- Country folders: 25
- JSON files: 146
- Total words: 1488019
- Files with missing token_id: 0
- Files with duplicate token_id: 0
- JSON read errors: 0
- Structural errors: 0
- spaCy version: `3.8.14`
- spaCy model: `es_dep_news_trf` / `dep_news_trf` 3.8.0
- Free disk space: 535.09 GB

## Structural Errors

None.

## Decision

The structural preflight is clean. However, the required single-file `--validate-only --require-spacy` check failed because the file is still pre-full-run and contains tokens missing v3.1 annotation fields (`lemma`, `pos`, `dep`, `head_text`). Per hard stop rules, the full annotation was not started.
