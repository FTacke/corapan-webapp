# Cleanup Plan After CO.PRE.PAN Tense Migration

Date: 2026-06-14

No files are deleted in this cleanup pass. The migration touched live transcript annotations and produced several safety artifacts; retaining intermediate smoke artifacts is lower risk until the next analysis workspace confirms the new v3.2 schema.

| Path | Decision | Reason | Risk | Replacement artifact |
| --- | --- | --- | --- | --- |
| `maintenance_pipelines/_0_json/backups/pre-v3_1-transcripts/20260614T080916Z` | keep | true reconstructed pre-v3.1 backup | high if deleted | none |
| `maintenance_pipelines/_0_json/backups/pre-tense-schema-migration/20260614T110946Z` | keep | post-full-run/pre-tense-migration backup | high if deleted | none |
| `maintenance_pipelines/_0_json/backups/manual-repairs/20260614T081443Z` | keep | documents one live timestamp repair | high if deleted | repair docs only, not sufficient |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_coprepan_tense_reference_schema.*` | keep | reference schema extraction | low | final alignment doc |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_corapan_vs_coprepan_tense_schema_diff_before.*` | keep | before evidence | low | final alignment doc |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_corapan_vs_coprepan_tense_schema_diff_after.*` | keep | after evidence | low | final alignment doc |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_full_transcripts_annotation_audit_coprepan_tense_compatible.*` | keep | final full audit | low | none |
| `maintenance_pipelines/_0_json/logs/tense_schema_migration/migration_20260614T110946Z.*` | keep | apply log | low | final alignment doc |
| older smoke-test audits and progress files | keep for now | useful rollback/debug context while v3.2 is fresh | medium if prematurely deleted | final audit only partially replaces them |

Recommended later cleanup: after one downstream analysis run and one metadata/statistics verification, remove only redundant smoke-only Markdown/JSON reports that are superseded by the final full audit and schema-diff artifacts.
