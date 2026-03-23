# BlackLab repo path migration 2026-03-20

## Scope

This change migrates the active repo defaults for BlackLab from the old flat path model

- `data/blacklab_export`
- `data/blacklab_index`
- `blacklab_index.bak_*`
- `blacklab_index.bad_*`
- runtime-specific BlackLab docmeta paths

to the canonical target structure

- `data/blacklab/export`
- `data/blacklab/index`
- `data/blacklab/backups`
- `data/blacklab/quarantine`

This is a repo-level path migration. It prepares the runtime and deploy flows for the target model but does not execute any live server data moves.

## Files changed

### Active code and path resolution

- `src/app/runtime_paths.py`
  - `get_docmeta_path()` now resolves to `data/blacklab/export/docmeta.jsonl`
  - optional explicit override via `CORAPAN_BLACKLAB_DOCMETA_PATH`
  - no runtime-specific BlackLab fallback remains in the resolver
- `src/scripts/blacklab_index_creation.py`
  - default export target moved to `data/blacklab/export/tsv`
  - default docmeta target moved to `data/blacklab/export/docmeta.jsonl`

### Build and run scripts

- `scripts/blacklab/build_blacklab_index.ps1`
  - export root -> `data/blacklab/export`
  - active index -> `data/blacklab/index`
  - staging build -> `data/blacklab/quarantine/index.build`
  - backups -> `data/blacklab/backups/index_<timestamp>`
  - repo-local BlackLab runtime fallback removed
- `scripts/blacklab/build_blacklab_index.sh`
  - same canonical roots as PowerShell builder
  - atomic switch now writes backups into `data/blacklab/backups`
- `scripts/blacklab/start_blacklab_docker_v3.ps1`
  - reads index from `data/blacklab/index`
  - BlackLab runtime fallback removed
- `scripts/blacklab/run_bls_prod.sh`
  - production index path switched to `/srv/webapps/corapan/data/blacklab/index`
- `scripts/blacklab/retain_blacklab_backups_prod.sh`
  - retention now scans `.../data/blacklab/backups/index_*`
  - logs move under the BlackLab backup tree

### Publish and deploy-sync

- `scripts/deploy_sync/_lib/ssh.ps1`
  - canonical remote BlackLab root is now `/srv/webapps/corapan/data/blacklab`
- `scripts/deploy_sync/publish_blacklab_index.ps1`
  - local publish source -> `data/blacklab/quarantine/index.build`
  - remote active index -> `.../data/blacklab/index`
  - remote staging -> `.../data/blacklab/quarantine/index.upload_<timestamp>`
  - remote backups -> `.../data/blacklab/backups/index_<timestamp>`
  - rollback quarantine -> `.../data/blacklab/quarantine/index.failed_<timestamp>`
- `scripts/deploy_sync/sync_data.ps1`
  - BlackLab trees removed from runtime data sync scope
- `scripts/deploy_sync/sync_core.ps1`
  - rsync excludes updated from flat BlackLab names to `blacklab`

### CI and compose wiring

- `.github/workflows/ci.yml`
  - CI runtime now creates `data/blacklab/export/docmeta.jsonl`
- `docker-compose.dev-postgres.yml`
  - BlackLab container mounts `./data/blacklab/index`
- `infra/docker-compose.dev.yml`
  - BlackLab container mounts `./data/blacklab/index`
- `infra/docker-compose.prod.yml`
  - app keeps runtime data mount
  - canonical docmeta path is prepared by mounting `/srv/webapps/corapan/data/blacklab/export` to `/app/data/blacklab/export`

### Utility scripts and docs

- `scripts/check_tsv_schema.py`
- `scripts/check_docs_count.py`
- `scripts/inspect_tsvs.py`
- `scripts/blacklab/docmeta_to_metadata_dir.py`
- `scripts/blacklab/prepare_json_for_blacklab.py`
- `scripts/deploy_checklist.sh`
- `scripts/deploy_sync/README.md`
- `data/README.md`

All of these now reference the canonical `data/blacklab/...` structure.

## Classification of remaining old references

The repo still contains many references to `blacklab_export`, `blacklab_index`, and runtime BlackLab paths, but they are not all active defaults.

### Still present by design

- `docs/state/*`
  - historical forensic reports and migration plans
  - these describe old realities and must remain readable as evidence
- `scripts/deploy_sync/legacy/*`
  - intentionally preserved legacy deployment material
- `scripts/debug/*`
  - debug-only helpers not used by the canonical build/publish path
- deprecated or safety-blocked scripts such as `scripts/blacklab/build_blacklab_index_prod.sh`
  - partially updated where low-risk, but still legacy in purpose

### Explicit status

- active writer/build/publish/runtime defaults: migrated
- active BlackLab runtime fallback in app resolver: removed
- runtime-first data/media deploy model: still active for non-BlackLab data
- historical BlackLab references in reports: still present and intentionally historical

## Validation summary

Repo validation after the changes showed:

- no syntax or editor errors in the touched active files
- active BlackLab code paths now point to the canonical structure
- remaining old references are concentrated in historical docs, legacy subtrees, and debug helpers

## Result

The repo is on the target structure for the active BlackLab implementation path.
It is not yet fully free of old BlackLab references because historical documentation and legacy/debug material still contain them.
