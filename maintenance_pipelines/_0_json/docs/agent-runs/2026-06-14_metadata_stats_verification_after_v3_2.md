# Metadata/Stats Verification After v3.2

Command: `$env:CORAPAN_RUNTIME_ROOT="C:\dev\corapan"; .venv\Scripts\python.exe maintenance_pipelines\_0_json\03_build_metadata_stats.py --verbose`

Exitcode: 0
Verify exitcode: 0

## Updated Files

- `data/db/public/stats_country.db`
- `data/db/public/stats_files.db`

## Counts

- Files: 146
- Countries: 25
- Radios: 25
- Tokens/words: 1488019
- Segments: 28816
- Speaker codes: 15

## Compatibility

- v3.2 fields: 03_build_metadata_stats.py ignores tense/v3.2 morph fields and reads segments[].words[], top-level country/radio/date/revision, and word end_ms for duration.
- Old TenseRole names expected in code/output: `False`
- Token-ID digest before stats: `sha256:4c3baf7987e666ff0423bffe8f50e16ca9b7cbe836362b2cdf89235dd9d7c956`
- Token-ID digest after stats: `sha256:4c3baf7987e666ff0423bffe8f50e16ca9b7cbe836362b2cdf89235dd9d7c956`

## Recommendation

Stats DBs are compatible with v3.2. Proceed to analysis sanity checks before any app/BlackLab refresh.
