# Final CORAPAN internal cleanup plan

Scope: remove only redundant v3.1 smoke artifacts, repo-local caches, empty temporary folders, and archive manual full-run launch helpers. No transcript JSONs, backups, final audits, stats DBs, or annotation scripts are touched.

| Path | Action | Reason | Protected? | Replacement/final artifact |
| --- | --- | --- | --- | --- |
| `maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_corapan_annotation_v3_1_multicountry_1percountry.md` | delete | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports | False | `final v3.2 audit/diff reports` |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_limit3_annotation_audit_spacy_real.json` | delete | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports | False | `final v3.2 audit/diff reports` |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_limit3_annotation_audit_spacy_real.md` | delete | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports | False | `final v3.2 audit/diff reports` |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_Mitre_annotation_audit.json` | delete | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports | False | `final v3.2 audit/diff reports` |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_Mitre_annotation_audit.md` | delete | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports | False | `final v3.2 audit/diff reports` |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_Mitre_annotation_audit_spacy_real.json` | delete | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports | False | `final v3.2 audit/diff reports` |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_ARG_Mitre_annotation_audit_spacy_real.md` | delete | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports | False | `final v3.2 audit/diff reports` |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_annotation_audit_spacy_real.json` | delete | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports | False | `final v3.2 audit/diff reports` |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_annotation_audit_spacy_real.md` | delete | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports | False | `final v3.2 audit/diff reports` |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_annotation_run_results.json` | delete | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports | False | `final v3.2 audit/diff reports` |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_idempotence_results.json` | delete | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports | False | `final v3.2 audit/diff reports` |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_token_id_check.json` | delete | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports | False | `final v3.2 audit/diff reports` |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/pre_smoke_test_audit.json` | delete | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports | False | `final v3.2 audit/diff reports` |
| `maintenance_pipelines/_0_json/docs/agent-runs/audits/pre_smoke_test_audit.md` | delete | redundant v3.1 smoke/mini-batch interim audit superseded by final v3.2 audits and reports | False | `final v3.2 audit/diff reports` |
| `start_full_annotation.txt -> maintenance_pipelines/_0_json/docs/agent-runs/archive_commands/root_start_full_annotation.txt` | move | manual full-run launcher kept as command archive instead of active root helper | False | `maintenance_pipelines/_0_json/docs/agent-runs/archive_commands/root_start_full_annotation.txt` |
| `maintenance_pipelines/_0_json/start_full_annotation.txt -> maintenance_pipelines/_0_json/docs/agent-runs/archive_commands/_0_json_start_full_annotation.txt` | move | manual full-run launcher kept as command archive instead of active root helper | False | `maintenance_pipelines/_0_json/docs/agent-runs/archive_commands/_0_json_start_full_annotation.txt` |
| `maintenance_pipelines/_0_json/run_full_transcripts_annotation.ps1 -> maintenance_pipelines/_0_json/docs/agent-runs/archive_commands/run_full_transcripts_annotation.ps1` | move | manual full-run launcher kept as command archive instead of active root helper | False | `maintenance_pipelines/_0_json/docs/agent-runs/archive_commands/run_full_transcripts_annotation.ps1` |
| `app/scripts/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `app/tests/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `app/src/app/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `app/src/scripts/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `app/src/app/auth/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `app/src/app/config/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `app/src/app/extensions/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `app/src/app/routes/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `app/src/app/search/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `app/src/app/services/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `maintenance_pipelines/_0_json/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `maintenance_pipelines/_0_mp3/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `maintenance_pipelines/_1_blacklab/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `maintenance_pipelines/_1_metadata/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `maintenance_pipelines/_1_zenodo-repos/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `maintenance_pipelines/_3_analysis_on_json/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `maintenance_pipelines/_0_json/tests/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `maintenance_pipelines/_0_json/tools/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `maintenance_pipelines/_3_analysis_on_json/alte Scripte/__pycache__` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `.pytest_cache` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `app/.pytest_cache` | delete | repo-local Python/pytest cache, reproducible | False | `none` |
| `maintenance_pipelines/_0_json/json-pre` | delete | empty temporary pipeline directory | False | `none` |
| `maintenance_pipelines/_0_json/json-ready` | delete | empty temporary pipeline directory | False | `none` |
