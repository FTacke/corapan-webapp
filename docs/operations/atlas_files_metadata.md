# Atlas Files Metadata Source

## Problem Summary

In production, `/api/v1/atlas/files` returned an empty list because the legacy
SQLite source (`stats_files.db`) was missing the `metadata` table. Development
worked because the local runtime DB still contained the table.

## Current Source of Truth

Atlas reads runtime metadata files exclusively from:

```
${CORAPAN_RUNTIME_ROOT}/data/public/metadata/tei
```

Priority order:
1. `corapan_recordings.json` (single file)
2. `corapan_recordings_*.json` (per-country)
3. `corapan_recordings.tsv`
4. `corapan_recordings_*.tsv`

Only the `tei/` directory is used. Other metadata directories are ignored.

## Required Fields

Each recording is normalized to:

- `filename`
- `country_code`
- `radio`
- `date`
- `revision`
- `word_count`
- `duration`

Missing fields fall back to `null` without dropping the record.

## Runtime Paths

- Metadata directory: `/app/data/public/metadata/tei`
- Stats DBs (still used elsewhere): `/app/data/db/public/*.db`

## Notes

- The Atlas endpoint no longer depends on `stats_files.db`.
- Caching is based on the metadata directory mtime to avoid frequent disk reads.
