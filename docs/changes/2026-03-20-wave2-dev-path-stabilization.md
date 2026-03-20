# Wave 2 Dev Path Stabilization

Date: 2026-03-20
Scope: local development runtime paths, atlas metadata lookup, advanced-search docmeta wiring, and dev workflow documentation
Change type: dev-only path stabilization

## What Changed

- removed active dev fallback behavior to `runtime/corapan` from the shared runtime resolvers used by config, atlas metadata, stats cache, and SQLite side-database access
- added a shared runtime path helper that requires explicit canonical dev runtime wiring and rejects repo-local `runtime/corapan` in development
- updated `scripts/dev-start.ps1`, `scripts/dev-setup.ps1`, `scripts/trace_runtime_paths.py`, and `scripts/migrate_stats_to_runtime.ps1` so the active dev workflow uses the sibling workspace layout and no longer falls back to repo-local runtime paths
- copied `docmeta.jsonl` once from `webapp/data/blacklab_export` to the canonical dev path `C:\dev\corapan\data\blacklab_export\docmeta.jsonl`
- fixed atlas metadata lookup so dev first checks `metadata/latest/tei` and then explicitly falls back to `metadata/latest` when the recording JSON/TSV files live there
- changed the atlas files route to avoid persisting stale empty responses during development
- updated tests that import advanced search modules so they declare the required dev environment explicitly
- updated local dev documentation and the instance-structure plan to record the Wave 2 outcome

## Why It Changed

Wave 1 inventory showed that the dev web app was already running primarily against `C:\dev\corapan\data` and `C:\dev\corapan\media`, but several code paths still treated repo-local runtime as a hidden fallback.

That created three concrete problems:

- atlas file metadata could be empty even though canonical metadata files were present
- advanced search docmeta enrichment still depended on a repo-local export artifact
- dev verification could appear green while still depending on legacy repo-local paths

## Affected Files

- src/app/runtime_paths.py
- src/app/config/__init__.py
- src/app/services/database.py
- src/app/services/atlas.py
- src/app/routes/stats.py
- src/app/routes/atlas.py
- scripts/dev-start.ps1
- scripts/dev-setup.ps1
- scripts/trace_runtime_paths.py
- scripts/migrate_stats_to_runtime.ps1
- tests/test_atlas_files_endpoint.py
- tests/test_advanced_api_enrichment.py
- tests/test_advanced_api_docmeta_mapping.py
- tests/test_advanced_api_stats_csv.py
- tests/test_advanced_api_stats_json.py
- tests/test_docmeta_lookup.py
- docs/operations/local-dev.md
- startme.md
- docs/state/instance-structure-unification-plan.md

## Operational Impact

- the active dev web app now expects the canonical sibling workspace layout and no longer silently falls back to `runtime/corapan`
- atlas metadata now resolves correctly from `C:\dev\corapan\data\public\metadata\latest` when `tei/` only contains XML files
- advanced search docmeta cache now loads from `C:\dev\corapan\data\blacklab_export\docmeta.jsonl`
- stale empty atlas file responses are less likely to mask a fixed metadata tree during dev verification

## What Was Intentionally Not Changed

- PostgreSQL wiring and auth database state
- analytics or side-database schema
- production compose or deployment paths
- BlackLab index topology and container mounts
- repo-local `config/blacklab` usage in the canonical dev compose file
- repo-local `webapp/data/blacklab_index` usage by the dev BlackLab container

## Legacy Paths Intentionally Kept

- `webapp/config/blacklab` remains ACTIVE_LEGACY for the canonical dev BlackLab container and related helper scripts because Wave 2 did not change container topology
- `webapp/data/blacklab_index` remains ACTIVE_LEGACY for the dev BlackLab container because the index structure was explicitly out of scope
- `webapp/data/blacklab_export` remains as a legacy source artifact, but the web app no longer depends on it after the one-time docmeta copy

## Follow-Up

- classify and later clean up dev-only BlackLab config and index paths in a separate wave without mixing that work into the web-app runtime path stabilization
- consider a dedicated dev command to clear route-level caches before HTTP verification when an older process may still be listening on the default port