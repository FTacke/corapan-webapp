# Wave 3 Centralized Runtime Resolvers

Date: 2026-03-20
Scope: shared runtime path resolution, app-level metadata/statistics/docmeta consumers, and legacy classification for remaining BlackLab repo paths
Change type: runtime-path centralization and clarity hardening

## What Changed

- replaced the remaining module-local runtime path derivations with a centralized `get_*` resolver set in `src/app/runtime_paths.py`
- introduced canonical getters for runtime, data, media, config, metadata, statistics, statistics temp, logs, docmeta, and media subdirectories
- updated `config`, `corpus`, `atlas`, `database`, `advanced_api`, `stats`, `media_store`, `editor`, and `audio_snippets` to use the centralized runtime getters
- removed the last active metadata-path divergence by making app metadata consumers resolve directly to `data/public/metadata/latest`
- added initialization and access logging for resolved data, media, metadata, and statistics paths
- marked the remaining repo-local BlackLab paths as `ACTIVE_LEGACY` in the canonical dev compose file and BlackLab export helper

## Why It Changed

Wave 2 stabilized development on the canonical sibling runtime structure, but some app modules still derived paths locally or kept import-time runtime constants.

That left three risks:

- path ambiguity between modules that should have shared one source of truth
- stale import-time path binding for docmeta and stats-related code
- hidden repo-local BlackLab path usage that was still active but not yet classified strongly enough

Wave 3 removes that ambiguity in the web-app runtime layer without changing PostgreSQL, auth, analytics, production deployment, or BlackLab index topology.

## Affected Files

- src/app/runtime_paths.py
- src/app/config/__init__.py
- src/app/__init__.py
- src/app/routes/corpus.py
- src/app/routes/stats.py
- src/app/services/atlas.py
- src/app/services/database.py
- src/app/services/media_store.py
- src/app/services/audio_snippets.py
- src/app/routes/editor.py
- src/app/search/advanced_api.py
- tests/test_runtime_paths.py
- tests/test_corpus_paths.py
- tests/test_media_routes.py
- tests/test_atlas_files_endpoint.py
- docker-compose.dev-postgres.yml
- src/scripts/blacklab_index_creation.py
- docs/state/Welle_3_summary.md

## Operational Impact

- the app now resolves runtime data and media paths through one shared getter layer
- metadata and statistics consumers no longer maintain separate path logic
- runtime path logs now show the active data, media, config, metadata, stats, and log directories during initialization
- media, atlas, metadata-download, statistics, and advanced-search verification can now be tied back to one deterministic resolver path set

## Compatibility Notes

- PostgreSQL wiring was not changed
- auth behavior was not changed
- analytics logic was not changed
- production compose topology was not changed
- BlackLab index mounts and export helper defaults were intentionally kept as `ACTIVE_LEGACY`

## Legacy Paths Intentionally Kept

- `docker-compose.dev-postgres.yml`: `./data/blacklab_index` and `./config/blacklab`
- `src/scripts/blacklab_index_creation.py`: `media/transcripts`, `data/blacklab_export/tsv`, and `data/blacklab_export/docmeta.jsonl`

## Follow-Up

- perform the BlackLab-specific path wave separately so repo-local BlackLab config and index paths can be reclassified or migrated without mixing that work into the web-app runtime layer
- if `CONFIG_ROOT` becomes operationally relevant for the web app itself, wire it through the same centralized getter layer instead of reintroducing local path joins