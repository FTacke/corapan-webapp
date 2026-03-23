# BlackLab Index Corruption Incident 2026-03-21

## Summary

Advanced Search in dev returned HTTP 500 for valid BlackLab hits requests, including:

- `[word="casa"]`
- `[word="casa" & country_code="ARG"]`
- `[word="casa" & country_scope="national"]`

The exact root cause was not a missing annotation, not a CQL builder defect, and not a BLF/export mismatch. The active dev index mounted from `data/blacklab/index` was corrupt.

## Exact Failure Evidence

BlackLab container logs reported `InvalidIndex` and `CorruptIndexException`, including a file mismatch under the mounted index path:

- `/data/index/corapan/_2.blcs.fields`

This is decisive evidence that the failure lived in the active index contents, not in the application layer.

## Classification

### What It Was

- Active dev BlackLab index corruption
- Operational data integrity failure in the mounted index
- A runtime failure that surfaced through search queries

### What It Was Not

- Missing `country_code` or `country_scope` annotations
- Broken `src/app/search/cql.py`
- Missing fields in `config/blacklab/corapan-tsv.blf.yaml`
- Missing export columns in the TSV/docmeta input

## Why the Symptom Was Misleading

The user-visible failure first appeared on country-filtered advanced search queries. That made a field-model or CQL problem plausible.

The deeper checks disproved that interpretation:

1. Corpus metadata advertised the expected fields.
2. The BLF declared the fields correctly.
3. The export contained the relevant TSV/docmeta values.
4. BlackLab logs showed index corruption.

## Operational Fix Performed

1. Stop `blacklab-server-v3`.
2. Rebuild the index with `webapp/scripts/blacklab/build_blacklab_index.ps1 -Activate`.
3. Restart BlackLab.
4. Re-run direct hits requests and app-level advanced search requests.

The rebuild created a backup of the previous active index under:

- `data/blacklab/backups/index_2026-03-21_001627`

## Validation After Repair

The repaired stack returned HTTP 200 for:

- direct BlackLab hits query with `[word="casa"]`
- direct BlackLab hits query with `[word="casa" & country_code="ARG"]`
- direct BlackLab hits query with `[word="casa" & country_scope="national"]`
- active app endpoint `/search/advanced/data` with and without those filters

## Lessons Learned

1. A BlackLab 500 on a valid hits query must be classified as an index-serving problem until logs prove otherwise.
2. BlackLab root HTTP readiness is weaker than an actual hits query against the mounted index.
3. Build success alone is weaker than serving success; the staged index must be read by BlackLab before activation.
4. The active dev index must be treated as mutable operational state, not as a passive artifact.
5. Parallel or non-canonical mount roots increase the chance of validating one index and serving another.

## Preventive Changes Introduced

The follow-up hardening added these enforcement points:

- `build_blacklab_index.ps1` now refuses to rebuild while `blacklab-server-v3` is running and validates the staged index in an isolated BlackLab container before activation.
- `start_blacklab_docker_v3.ps1` now validates canonical paths, requires explicit `-Restart`, and runs a hits smoke query after startup.
- `dev-start.ps1` and `dev-setup.ps1` now fail fast if BlackLab is reachable but the active index cannot answer a real hits query.

## Residual Notes

The legacy HTML route `/search/advanced/results` still showed a separate 400 parsing problem after the index repair. That route was not the active DataTables search path and was not part of this incident's root cause.