# CORAPAN Tense Schema CO.PRE.PAN Alignment

Date: 2026-06-14

## 1. Problem

CORAPAN transcripts were fully annotated, but their tense labels were not 1:1 compatible with CO.PRE.PAN. In particular, CORAPAN still used `TenseRole=finite_past`, generic `auxiliary`, `compound_participle`, `future_infinitive`, and `VoiceType=resultative`.

## 2. CO.PRE.PAN As Reference

CO.PRE.PAN was not changed. The reference code was read from:

- `C:/dev/coprepan/scripts/annotation/lib/tense_rules.py`
- `C:/dev/coprepan/scripts/annotation/annotate_articles.py`
- `C:/dev/coprepan/scripts/annotation/lib/validation.py`

The effective schema was extracted from `C:/dev/coprepan/json_annotated`.

## 3. Extracted CO.PRE.PAN Schema

Artifacts:

- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_coprepan_tense_reference_schema.json`
- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_coprepan_tense_reference_schema.md`

Files scanned: 926.

Reference roles observed include:

- `finite_verb`
- `copula_or_aux`
- `aux_passive`
- `aux_pass_chain`
- `copula_resultative`
- `aux_nonfinite_perfect`
- `nonfinite_perfect`
- `lexical_participle`

## 4. Before-Diff

Artifacts:

- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_corapan_vs_coprepan_tense_schema_diff_before.json`
- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_corapan_vs_coprepan_tense_schema_diff_before.md`

Hard failures before migration:

- `CORAPAN TenseRole=finite_past count 28483`
- CORAPAN-only roles: `auxiliary`, `compound_participle`, `finite_past`, `future_infinitive`
- `CORAPAN legacy TenseRole=auxiliary count 13847`

## 5. Pipeline Changes

Updated `maintenance_pipelines/_0_json/02_annotate_transcripts_v3.py`:

- `PIPELINE_VERSION = "corapan-transcript-ann-v3.2"`
- `TENSE_RULES_VERSION = "tense-v4-coprepan-compatible"`
- `VALIDATION_VERSION = "transcript-validation-v3"`
- finite past verbs now use `TenseRole=finite_verb` plus `VerbLemma`
- finite AUX past/imp forms use `TenseRole=copula_or_aux` plus `VerbLemma`
- `ser + Part` uses `aux_passive` and `VoiceType=passive`
- `estar + Part` uses `copula_resultative` and `VoiceType=resultative_or_state`
- passive chains use `aux_pass_chain` and `lexical_participle`
- perfect infinitives use `aux_nonfinite_perfect` and `nonfinite_perfect`
- old CORAPAN-only roles are rejected by validation
- progress JSON write failures are logged instead of aborting a skip run

## 6. Migration Script

Created:

`maintenance_pipelines/_0_json/tools/migrate_tense_to_coprepan_schema.py`

The script reruns only the tense adapter over existing token fields. It does not run spaCy and does not modify token IDs, text, timing, segment structure, speaker data, or core token fields.

## 7. Backup Before Migration

Created before `--apply --backup`:

`maintenance_pipelines/_0_json/backups/pre-tense-schema-migration/20260614T110946Z`

Includes:

- `transcripts/`
- `MANIFEST.json`
- `TOKEN_ID_SNAPSHOT.json`
- `README.md`

## 8. Migration Result

Dry-run sample:

`media/transcripts/BOL/2024-05-03_BOL_Erbol.json`

Result: `would_change`, 495 tokens changed, token-id changes 0.

Full dry-run:

- files selected: 146
- files would change: 146
- token-id changes: 0 in every file

Apply:

- command: `.venv\Scripts\python.exe maintenance_pipelines\_0_json\tools\migrate_tense_to_coprepan_schema.py --apply --backup --verbose`
- files changed: 146
- apply log: `maintenance_pipelines/_0_json/logs/tense_schema_migration/migration_20260614T110946Z.log`
- apply JSONL: `maintenance_pipelines/_0_json/logs/tense_schema_migration/migration_20260614T110946Z.jsonl`

## 9. After-Diff

Artifacts:

- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_corapan_vs_coprepan_tense_schema_diff_after.json`
- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_corapan_vs_coprepan_tense_schema_diff_after.md`

Result:

- hard failures: 0
- `TenseRole=finite_past`: 0
- CORAPAN-only `TenseRole` values: none

## 10. Full Audit

Artifacts:

- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_full_transcripts_annotation_audit_coprepan_tense_compatible.json`
- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_full_transcripts_annotation_audit_coprepan_tense_compatible.md`

Result:

- files audited: 146
- GREEN: 145
- YELLOW: 1
- RED: 0
- hard-gate failures: 0
- validation errors: 0

The single YELLOW is `media/transcripts/COL/2024-01-03_COL_Caracol.json` because of a suspicious email-like token. It is not a TenseRole, token-id, or structural failure.

## 11. Token-ID Safety

Token-ID diff:

- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_tense_schema_migration_token_id_diff.json`
- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_tense_schema_migration_token_id_diff.md`

Result:

- changed existing token IDs: 0
- deleted existing token IDs: 0
- added token IDs: 0
- duplicate token IDs: 0
- missing token IDs: 0

## 12. Idempotence And Tests

Idempotence command:

```powershell
.venv\Scripts\python.exe maintenance_pipelines\_0_json\02_annotate_transcripts_v3.py --require-spacy --verbose
```

Result:

- `skipped (up-to-date)`: 146

Tests:

```text
9 passed in 1.49s
```

## 13. Cleanup

Cleanup plan:

`maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_cleanup_plan_after_coprepan_tense_migration.md`

Cleanup report:

`maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_cleanup_after_coprepan_tense_migration.md`

No files were deleted. Safety-critical backups and final audit/diff artifacts were intentionally retained.

## 14. Remaining Notes

- One final audit YELLOW remains for an email-like token in `COL/2024-01-03_COL_Caracol.json`; it is non-blocking for tense compatibility.
- CO.PRE.PAN-only values that do not appear in CORAPAN are not treated as failures.
- The migration intentionally did not rerun spaCy.

## 15. Recommendation

Use the v3.2 transcripts for the next analysis workspace. Before publishing or indexing a derived corpus, run metadata/statistics verification and one downstream query sanity pass over PastType, FutureType, VoiceType, and TenseRole distributions.
