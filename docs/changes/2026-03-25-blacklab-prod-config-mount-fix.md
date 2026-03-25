# 2026-03-25 BlackLab Prod Config Mount Fix

## Summary

Diagnosed and fixed a production BlackLab search outage caused by a stale config mount path after the root-lifted deploy layout.

## What Changed

- corrected the production BlackLab config path contract from `/srv/webapps/corapan/app/config/blacklab` to `/srv/webapps/corapan/app/app/config/blacklab`
- aligned `app/scripts/blacklab/run_bls_prod.sh` with the actual production checkout layout
- aligned `app/scripts/blacklab/build_blacklab_index_prod.sh` comments and config references with the same layout
- recorded the DEV-vs-PROD drift and repair outcome in `docs/rsync/blacklab_prod_fix_report.md`
- added skill/instruction guidance to require live DEV-vs-PROD mount comparison for BlackLab production failures

## Operational Impact

- production BlackLab search can fail even when the index mount is healthy if `/etc/blacklab` points at the stale outer checkout path
- a real hits query is required to validate recovery; root readiness alone is not enough

## Compatibility Notes

- this does not change the canonical local dev BlackLab model
- it documents and restores the production config mount contract for the current root-lifted checkout layout

## Follow-Up

- keep validating production search with a real hits query after BlackLab restarts or publish operations
- treat the stale outer checkout config path as dangerous until removed deliberately in a later cleanup