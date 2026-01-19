# Runtime Data Contract (Single Source of Truth)

**Date:** 2026-01-19  
**Scope:** Editor / Player / Metadata / Atlas

## 1) Runtime Layout (Canonical)

```
runtime/
  corapan/
    data/
      public/
        metadata/
          latest/                 # Optional: preferred if present
            tei/                  # Atlas inputs: corapan_recordings*.json|tsv
            corapan_recordings.*  # FAIR exports (tsv/json/jsonld/tei zip)
          tei/                    # Fallback when latest/ is absent
          corapan_recordings.*    # Fallback when latest/ is absent
        statistics/
          corpus_stats.json
          viz_*.png
      db/
        public/
          stats_files.db
          stats_country.db
        restricted/               # auth + analytics + postgres_dev
    media/
      transcripts/
      mp3-full/
      mp3-split/
      mp3-temp/
```

## 2) Endpoint → Runtime Path Map

### Atlas API
- **GET /api/v1/atlas/countries** → `data/db/public/stats_country.db`
- **GET /api/v1/atlas/files** → `data/public/metadata/latest/tei/corapan_recordings*.{json,tsv}`

### Corpus Metadata
- **GET /corpus/metadata/download/tsv|json|jsonld|tei** → `data/public/metadata/latest/*` (if present) else `data/public/metadata/*`
- **GET /corpus/metadata/download/tsv/<country>** → `data/public/metadata/latest/corapan_recordings.json` (if present) else `data/public/metadata/corapan_recordings.json`
- **GET /corpus/metadata/download/json/<country>** → `data/public/metadata/latest/corapan_recordings.json` (if present) else `data/public/metadata/corapan_recordings.json`

### Corpus Statistics
- **GET /corpus/api/** + **corpus_stats** → `data/public/statistics/corpus_stats.json`
- **GET /corpus/api/statistics/<file>** → `data/public/statistics/{viz_*.png,*.json}`

### Media
- **GET /media/transcripts/<file>** → `media/transcripts/<file>`
- **GET /media/full/<file>** → `media/mp3-full/<file>`
- **GET /media/split/<file>** → `media/mp3-split/<file>`
- **GET /media/temp/<file>** → `media/mp3-temp/<file>`

### Editor
- **GET /editor/** → `media/transcripts/*` + `data/db/public/stats_files.db` + `media/transcripts/edit_log.jsonl`
- **POST /editor/save-edits** → `media/transcripts/<file>.json` + backups under `media/transcripts/<country>/backup/`
- **GET /editor/history/<country>/<file>** → `media/transcripts/<country>/backup/<stem>_diffs.jsonl`
- **POST /editor/undo** → `media/transcripts/<country>/backup/<stem>_original.json`

## 3) Required Environment Variables

- `CORAPAN_RUNTIME_ROOT` → base for `runtime/corapan/data`
- `CORAPAN_MEDIA_ROOT` → base for `runtime/corapan/media`
- `PUBLIC_STATS_DIR` (optional) → overrides statistics path; if set, must equal `runtime/corapan/data/public/statistics`
- `AUTH_DATABASE_URL` → restricted auth DB (Postgres in prod)
- `POSTGRES_DEV_DATA_DIR` (optional) → dev-only postgres data dir under `data/db/restricted/postgres_dev`

## 4) Legacy Removed

- Legacy stats DB and related endpoints are removed.
- Metadata root is `data/public/metadata/` with optional `latest/` (preferred if present).
- No data paths outside `runtime/corapan/data` and `runtime/corapan/media` are supported.

## 5) Notes

- Public data is strictly under `data/public` and `data/db/public`.
- Restricted data is strictly under `data/db/restricted` and `media/*`.
- All consumers must resolve runtime paths from env and fail fast when missing.
