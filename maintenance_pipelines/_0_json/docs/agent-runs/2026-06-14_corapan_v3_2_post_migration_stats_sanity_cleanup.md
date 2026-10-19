# CORAPAN v3.2 Post-Migration Stats, Sanity, Cleanup

Date: 2026-06-14

## 1. Ausgangslage

CORAPAN transcripts were migrated to the CO.PRE.PAN-compatible tense schema:

- `pipeline_version`: `corapan-transcript-ann-v3.2`
- `tense_rules_version`: `tense-v4-coprepan-compatible`
- `TenseRole=finite_past`: 0
- token-id migration diff: 0 changes

Reference run doc:

`maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_corapan_tense_schema_coprepan_alignment.md`

## 2. v3.2-Bestandsprüfung

Artifacts:

- `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_corapan_v3_2_inventory_check.json`
- `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_corapan_v3_2_inventory_check.md`

Result:

- Country folders: 25
- JSON files: 146
- Total words: 1488019
- All files readable: yes
- All files `pipeline_version == corapan-transcript-ann-v3.2`: yes
- All files `tense_rules_version == tense-v4-coprepan-compatible`: yes
- All files `ann_meta.validation.status == passed`: yes
- `TenseRole=finite_past`: 0
- Missing token IDs: 0
- Duplicate token IDs: 0
- Token-ID digest: `sha256:4c3baf7987e666ff0423bffe8f50e16ca9b7cbe836362b2cdf89235dd9d7c956`

Known YELLOW:

- `media/transcripts/COL/2024-01-03_COL_Caracol.json`
- Reason remains non-blocking: suspicious email-like token, not a tense/token-id/structure failure.

## 3. Metadata-/Stats-Verifikation

Stats script checked:

`maintenance_pipelines/_0_json/03_build_metadata_stats.py`

Minimal compatibility fix made:

- robust project-root detection
- `countries.py` candidate list including `app/src/app/config/countries.py`

The script does not depend on old TenseRole names. It reads top-level metadata, `segments[].words[]`, `end_ms`, and file/country/radio/date fields.

Command:

```powershell
$env:CORAPAN_RUNTIME_ROOT="C:\dev\corapan"
.venv\Scripts\python.exe maintenance_pipelines\_0_json\03_build_metadata_stats.py --verbose
```

Verification command:

```powershell
$env:CORAPAN_RUNTIME_ROOT="C:\dev\corapan"
.venv\Scripts\python.exe maintenance_pipelines\_0_json\03_build_metadata_stats.py --verify-only
```

Artifacts:

- `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_metadata_stats_verification_after_v3_2.json`
- `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_metadata_stats_verification_after_v3_2.md`

Generated/updated:

- `data/db/public/stats_country.db`
- `data/db/public/stats_files.db`

Counts:

- Files: 146
- Countries: 25
- Radios: 25
- Tokens/words: 1488019
- Segments: 28816
- Speaker codes: 15

Token-ID digest before and after stats was identical:

`sha256:4c3baf7987e666ff0423bffe8f50e16ca9b7cbe836362b2cdf89235dd9d7c956`

## 4. Tense-Distribution-Sanity

Tool:

`maintenance_pipelines/_0_json/tools/sanity_check_tense_distributions.py`

Artifacts:

- `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_tense_distribution_sanity_after_v3_2.json`
- `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_tense_distribution_sanity_after_v3_2.md`

Result:

- Hard failures: 0
- No old CORAPAN-only roles
- No `TenseRole=finite_past`
- No `VoiceType=resultative`
- No incompatible CO.PRE.PAN reference values
- Shared filters are usable for CO.PRE.PAN and CORAPAN.

## 5. Shared-Filter-Sanity CO.PRE.PAN/CORAPAN

Artifacts:

- `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_coprepan_corapan_shared_filter_sanity.json`
- `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_coprepan_corapan_shared_filter_sanity.md`

Filters tested without corpus-specific aliases:

| Filter | CO.PRE.PAN count | CORAPAN count |
| --- | ---: | ---: |
| `morph.TenseRole == "finite_verb"` | 414395 | 28506 |
| `morph.PastType == "simplePast"` | 420702 | 27658 |
| `morph.TenseRole == "aux_passive"` | 20790 | 1495 |
| `morph.VoiceType == "passive"` | 46535 | 3412 |
| `morph.FutureType == "periphrasticFuture"` | 6918 | 4655 |
| `morph.TenseRole == "lexical_participle"` | 28907 | 2198 |
| `morph.VerbLemma exists` | 497351 | 36984 |

Hard failures: 0.

Decision: the same morph filters can be used in both corpora without label aliases.

## 6. Cleanup-Entscheidung

Artifacts:

- `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_cleanup_plan_after_stats_and_sanity.md`
- `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_cleanup_after_stats_and_sanity.md`

Decision: no deletion.

Reason: the full backup/audit/debug chain is still valuable until a downstream analysis workspace has consumed v3.2 and a separate retention decision exists.

## 7. Gelöschte/Behaltene Artefakte

Deleted files: none.

Deleted folders: none.

Consciously retained:

- `maintenance_pipelines/_0_json/backups/pre-v3_1-transcripts/20260614T080916Z`
- `maintenance_pipelines/_0_json/backups/pre-tense-schema-migration/20260614T110946Z`
- `maintenance_pipelines/_0_json/backups/manual-repairs/20260614T081443Z`
- final full audits
- before/after schema diffs
- CO.PRE.PAN reference schema
- token-id snapshots
- migration logs
- state DB and progress files

## 8. Verbleibende Auffälligkeiten

- One non-blocking YELLOW remains in the final full audit: an email-like token in `COL/2024-01-03_COL_Caracol.json`.
- `03_build_metadata_stats.py` writes aggregate DBs only; speaker-code count was derived from transcripts for this report, not stored in the DB schema.

## 9. Empfehlung

Proceed to the analysis workspace using the v3.2 JSONs and shared CO.PRE.PAN/CORAPAN morph filters.

Do not refresh BlackLab or app-facing indexes without explicit approval.

Keep all three backup tiers for now:

- pre-v3.1 reconstruction
- pre-tense-schema migration backup
- manual timestamp repair backup

Review backup retention only after downstream analysis and DB consumers have confirmed the v3.2 corpus.
