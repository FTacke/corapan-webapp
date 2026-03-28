# 2026-03-28 BlackLab Index Path Guardrails

## Summary

Added minimal guardrails to the BlackLab production publish and restart lanes so path aliases such as `index\r`, leading/trailing-whitespace variants, or other control-character variants cannot silently become or mask the active index path.

## What Changed

- hardened `app/scripts/deploy_sync/publish_blacklab_index.ps1` with strict canonical-path validation before the final swap
- added post-publish host-path verification so the active host path must exist, be non-empty, and have no suspicious `index`-alias siblings before publish is treated as healthy
- hardened `app/scripts/blacklab/build_blacklab_index_prod.sh` before and after the final activation rename
- hardened `app/scripts/blacklab/run_bls_prod.sh` so production restart aborts if the canonical index path is missing, empty, or shadowed by suspicious sibling directories that normalize to `index`
- updated the maintenance wrapper to reject malformed remote BlackLab roots early and to log critical paths in visible escaped form

## Operational Impact

- a path like `index\r` now causes a hard failure before the active index path is renamed or BlackLab is restarted
- a restart no longer proceeds when the canonical host mount path is empty or when suspicious sibling paths indicate hidden path drift
- publish and restart logs now render critical paths in escaped form so control characters are visible during incident response

## Compatibility Notes

- no search logic changed
- no automatic repair or path normalization was introduced
- the canonical production active index path remains `/srv/webapps/corapan/data/blacklab/index`

## Follow-Up

- if one of these guards fires on the production host, inspect the reported escaped path literally before any manual rename or restart