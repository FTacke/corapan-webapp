# Final cleanup inventory before

Created: 2026-06-14T12:27:33.377691+00:00

- agent_runs: 48 files, 1 dirs, 24057964 bytes
- backups: 398 files, 153 dirs, 2493156060 bytes
- logs: 10 files, 2 dirs, 744960 bytes
- Planned cleanup candidates: 40 items, 2868618 bytes

## Planned actions

| Path | Action | Size bytes | Reason |
| --- | --- | ---: | --- |
| `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_corapan_annotation_v3_1_multicountry_1percountry.md` | delete | 10192 | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_limit3_annotation_audit_spacy_real.json` | delete | 99373 | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_limit3_annotation_audit_spacy_real.md` | delete | 26949 | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_Mitre_annotation_audit.json` | delete | 30833 | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_Mitre_annotation_audit.md` | delete | 8409 | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_Mitre_annotation_audit_spacy_real.json` | delete | 31332 | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_Mitre_annotation_audit_spacy_real.md` | delete | 8593 | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_annotation_audit_spacy_real.json` | delete | 753567 | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_annotation_audit_spacy_real.md` | delete | 209012 | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_annotation_run_results.json` | delete | 60409 | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_idempotence_results.json` | delete | 23820 | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_token_id_check.json` | delete | 4235 | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/pre_smoke_test_audit.json` | delete | 10080 | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/pre_smoke_test_audit.md` | delete | 6053 | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports |
| `start_full_annotation.txt` -> maintenance_pipelines/_0_json/docs/agent-runs/archive_commands/root_start_full_annotation.txt | move | 125 | manual full-run launcher kept as command archive instead of active root helper |
| `maintenance_pipelines/_0_json/start_full_annotation.txt` -> maintenance_pipelines/_0_json/docs/agent-runs/archive_commands/_0_json_start_full_annotation.txt | move | 125 | manual full-run launcher kept as command archive instead of active root helper |
| `maintenance_pipelines/_0_json/run_full_transcripts_annotation.ps1` -> maintenance_pipelines/_0_json/docs/agent-runs/archive_commands/run_full_transcripts_annotation.ps1 | move | 631 | manual full-run launcher kept as command archive instead of active root helper |
| `app/scripts/__pycache__` | delete | 4213 | repo-local Python/pytest cache, reproducible |
| `app/tests/__pycache__` | delete | 605461 | repo-local Python/pytest cache, reproducible |
| `app/src/app/__pycache__` | delete | 32153 | repo-local Python/pytest cache, reproducible |
| `app/src/scripts/__pycache__` | delete | 25570 | repo-local Python/pytest cache, reproducible |
| `app/src/app/auth/__pycache__` | delete | 32871 | repo-local Python/pytest cache, reproducible |
| `app/src/app/config/__pycache__` | delete | 30114 | repo-local Python/pytest cache, reproducible |
| `app/src/app/extensions/__pycache__` | delete | 17921 | repo-local Python/pytest cache, reproducible |
| `app/src/app/routes/__pycache__` | delete | 164580 | repo-local Python/pytest cache, reproducible |
| `app/src/app/search/__pycache__` | delete | 95557 | repo-local Python/pytest cache, reproducible |
| `app/src/app/services/__pycache__` | delete | 60738 | repo-local Python/pytest cache, reproducible |
| `maintenance_pipelines/_0_json/__pycache__` | delete | 275810 | repo-local Python/pytest cache, reproducible |
| `maintenance_pipelines/_0_mp3/__pycache__` | delete | 36379 | repo-local Python/pytest cache, reproducible |
| `maintenance_pipelines/_1_blacklab/__pycache__` | delete | 2689 | repo-local Python/pytest cache, reproducible |
| `maintenance_pipelines/_1_metadata/__pycache__` | delete | 37222 | repo-local Python/pytest cache, reproducible |
| `maintenance_pipelines/_1_zenodo-repos/__pycache__` | delete | 17720 | repo-local Python/pytest cache, reproducible |
| `maintenance_pipelines/_3_analysis_on_json/__pycache__` | delete | 17978 | repo-local Python/pytest cache, reproducible |
| `maintenance_pipelines/_0_json/tests/__pycache__` | delete | 31080 | repo-local Python/pytest cache, reproducible |
| `maintenance_pipelines/_0_json/tools/__pycache__` | delete | 45322 | repo-local Python/pytest cache, reproducible |
| `maintenance_pipelines/_3_analysis_on_json/alte Scripte/__pycache__` | delete | 30531 | repo-local Python/pytest cache, reproducible |
| `.pytest_cache` | delete | 1666 | repo-local Python/pytest cache, reproducible |
| `app/.pytest_cache` | delete | 19305 | repo-local Python/pytest cache, reproducible |
| `maintenance_pipelines/_0_json/json-pre` | delete | 0 | empty temporary pipeline directory |
| `maintenance_pipelines/_0_json/json-ready` | delete | 0 | empty temporary pipeline directory |

## Protected artifacts

| Path | Exists |
| --- | --- |
| `media/transcripts` | True |
| `data/db/public/stats_country.db` | True |
| `data/db/public/stats_files.db` | True |
| `maintenance_pipelines/_0_json/backups/pre-v3_1-transcripts/20260614T080916Z` | True |
| `maintenance_pipelines/_0_json/backups/pre-tense-schema-migration/20260614T110946Z` | True |
| `maintenance_pipelines/_0_json/backups/manual-repairs/20260614T081443Z` | True |
| `maintenance_pipelines/_0_json/02_annotate_transcripts_v3.py` | True |
| `maintenance_pipelines/_0_json/03_build_metadata_stats.py` | True |
| `maintenance_pipelines/_0_json/tools/migrate_tense_to_coprepan_schema.py` | True |
| `maintenance_pipelines/_0_json/tools/extract_coprepan_tense_schema.py` | True |
| `maintenance_pipelines/_0_json/tools/compare_tense_schema_with_coprepan.py` | True |
| `maintenance_pipelines/_0_json/tools/sanity_check_tense_distributions.py` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_corapan_annotation_v3_1_full_transcripts_run.md` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_corapan_tense_schema_coprepan_alignment.md` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_corapan_v3_2_post_migration_stats_sanity_cleanup.md` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_corapan_v3_2_inventory_check.md` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_corapan_v3_2_inventory_check.json` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_metadata_stats_verification_after_v3_2.md` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_metadata_stats_verification_after_v3_2.json` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_tense_distribution_sanity_after_v3_2.md` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_tense_distribution_sanity_after_v3_2.json` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_coprepan_tense_reference_schema.json` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_coprepan_tense_reference_schema.md` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_corapan_vs_coprepan_tense_schema_diff_before.json` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_corapan_vs_coprepan_tense_schema_diff_before.md` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_corapan_vs_coprepan_tense_schema_diff_after.json` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_corapan_vs_coprepan_tense_schema_diff_after.md` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_full_transcripts_annotation_audit_coprepan_tense_compatible.json` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_full_transcripts_annotation_audit_coprepan_tense_compatible.md` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_tense_schema_migration_token_id_diff.json` | True |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_tense_schema_migration_token_id_diff.md` | True |
| `maintenance_pipelines/_0_json/logs/tense_schema_migration/migration_20260614T110946Z.jsonl` | True |
| `maintenance_pipelines/_0_json/logs/tense_schema_migration/migration_20260614T110946Z.log` | True |
