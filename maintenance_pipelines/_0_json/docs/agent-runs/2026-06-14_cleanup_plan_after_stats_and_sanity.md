# Cleanup Plan After Stats And Sanity

Date: 2026-06-14

Decision: no deletion recommended now.

Reason: v3.2 inventory, stats verification, tense sanity, and shared-filter sanity all passed. The artifact chain is still fresh and useful for debugging downstream analysis. Removing smoke/intermediate files now would save little space relative to the value of retaining the audit trail.

| Path / Pattern | Decision | Reason | Risk If Deleted | Replacement |
| --- | --- | --- | --- | --- |
| `maintenance_pipelines/_0_json/backups/pre-v3_1-transcripts/20260614T080916Z` | keep | true pre-v3.1 reconstruction | high | none |
| `maintenance_pipelines/_0_json/backups/pre-tense-schema-migration/20260614T110946Z` | keep | post-full/pre-tense backup | high | none |
| `maintenance_pipelines/_0_json/backups/manual-repairs/20260614T081443Z` | keep | timestamp repair rollback/evidence | high | repair docs are not enough |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_*` | keep | final audits/diffs plus smoke evidence | medium | final reports partially replace smoke docs |
| `maintenance_pipelines/_0_json/logs/tense_schema_migration/*` | keep | migration apply/dry-run logs | medium | final report summarizes but does not replace JSONL |
| `maintenance_pipelines/_0_json/logs/annotation_progress.*` | keep | current progress/state breadcrumbs | low | state DB and final docs |
| old single-smoke Markdown/JSON reports | keep for now | useful as chronology of v3.1 to v3.2 transition | low | final full audit |
| empty temp folders / `*.tmp` | delete only if found | no value | low | none |

No `*.tmp` files were found during the final check, so no deletion action is proposed.
