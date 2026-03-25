# Sync Lane Refactor

This directory documents the refactor of the local Windows production sync lanes.

Use these documents in this order:

1. `live_validation_sync.md` for live operator-machine truth
2. `refactor_plan.md` for scope and sequencing
3. `transport_matrix.md` for the transport contract
4. `safety_contract.md` for guardrails
5. `logging_contract.md` for per-run summary expectations
6. `refactor_implementation_report.md` for what was actually changed
7. `post_refactor_validation_report.md` for the practical post-refactor proof, residual risks, and legacy classification
8. `blacklab_prod_fix_report.md` for the DEV-vs-PROD BlackLab drift, production repair, and canonical config mount contract
9. `blacklab_config_path_cleanup_audit.md` for the path-reference audit, active/stale classification, and outer-path evaluation
10. `blacklab_publish_proof_run.md` for the controlled BlackLab publish proof, storage preflight, cleanup decisions, and observed backup behavior

Source mapping note:

- the user-referenced `repo_rsync_audit.md` maps to `2026-03-25_server-sync-audit.md`
- the user-referenced `server_rsync_audit.md` maps to `server-agent_rsync_audit.md`