# Maintenance Pipeline Alignment to Dev/Prod Target Design

Date: 2026-03-21
Scope: local maintenance/orchestrator layer under `maintenance_pipelines/` plus the deploy-sync defaults it depends on under `webapp/scripts/deploy_sync/`
Applies to: local workspace `CORAPAN/` and versioned app/deploy repo `webapp/`

## Goal

Align the maintenance pipeline scripts to the current target model instead of the older `corapan-webapp`, `LOKAL`, and `data/blacklab_export` assumptions.

Target model:

- Local workspace root: `CORAPAN/`
- Active versioned app repo: currently `CORAPAN/webapp/`, later allowed to move to `CORAPAN/`
- Production app root: `/srv/webapps/corapan/app`
- Production data root: `/srv/webapps/corapan/data`
- Production media root: `/srv/webapps/corapan/media`
- Production BlackLab data root: `/srv/webapps/corapan/data/blacklab`
- Canonical local BlackLab export root: `data/blacklab/export`

## Implemented Changes

### 1. BlackLab export wrapper now uses canonical paths

Updated `maintenance_pipelines/_1_blacklab/blacklab_export.py`:

- no longer assumes the export target is `data/blacklab_export`
- now writes explicitly to:
  - `data/blacklab/export/tsv`
  - `data/blacklab/export/docmeta.jsonl`
- no longer relies on running `python -m src...` from a guessed root
- resolves the active app repo dynamically:
  - first `CORAPAN/webapp`
  - then `CORAPAN/`
- calls the versioned export script by absolute path

Reason:

- the maintenance wrapper lives outside the app repo, so implicit module execution from a guessed cwd was brittle
- canonical export paths must match the app runtime and BlackLab build scripts

### 2. BlackLab publish wrapper no longer hardcodes `WebappRepoPath`

Updated `maintenance_pipelines/_2_deploy/publish_blacklab.ps1`:

- parameter renamed to `AppRepoPath` with compatibility alias `WebappRepoPath`
- auto-detects the active app repo under the workspace
- fixes the default export script path to the real maintenance script location
- passes canonical remote targets explicitly to `publish_blacklab_index.ps1`:
  - `DataDir=/srv/webapps/corapan/data/blacklab`
  - `ConfigDir=/srv/webapps/corapan/app/config/blacklab`
- logs the required serial order: `export -> build -> publish`

Reason:

- the wrapper must survive the planned `webapp/ -> app/` rename and eventual git-root move
- remote BlackLab paths must be explicit and consistent with the current production target design

### 3. Data/media orchestrators now resolve the active app repo generically

Updated:

- `maintenance_pipelines/_2_deploy/deploy_data.ps1`
- `maintenance_pipelines/_2_deploy/deploy_media.ps1`

Changes:

- `AppRepoPath` is now the primary parameter, with `WebappRepoPath` kept as alias
- default repo resolution is workspace-aware instead of name-bound to `webapp`
- operator messaging now reflects the real workflow ordering

Additional correction in `deploy_data.ps1`:

- removed the outdated claim that the script deploys `data/blacklab_export`
- clarified that BlackLab export/publish is a separate wave handled by `publish_blacklab.ps1`

Reason:

- the old output suggested a BlackLab deploy happened during normal data sync, which was false and operationally dangerous

### 4. Deploy-sync defaults were aligned to the current prod root model

Updated:

- `webapp/scripts/deploy_sync/_lib/ssh.ps1`
- `webapp/scripts/deploy_sync/sync_core.ps1`
- `webapp/scripts/deploy_sync/sync_data.ps1`

Changes:

- remote default roots now resolve to:
  - `RuntimeRoot=/srv/webapps/corapan`
  - `DataRoot=/srv/webapps/corapan/data`
  - `MediaRoot=/srv/webapps/corapan/media`
  - `BlackLabDataRoot=/srv/webapps/corapan/data/blacklab`
- `sync_core.ps1` no longer hardcodes `C:\dev\corapan-webapp\tools\cwrsync\bin`
- the statistics generation hint now points to `maintenance_pipelines/_0_json/...`

Reason:

- the maintenance orchestrators depend on these shared defaults
- without changing them, the wrappers would still deploy against the legacy runtime subtree

## Final Operator Order

Required sequence, no parallel execution:

1. `maintenance_pipelines/_1_blacklab/blacklab_export.py`
2. `maintenance_pipelines/_2_deploy/publish_blacklab.ps1`
3. `maintenance_pipelines/_2_deploy/deploy_data.ps1`
4. `maintenance_pipelines/_2_deploy/deploy_media.ps1`

Interpretation:

- Step 1 produces canonical export artifacts under `data/blacklab/export`
- Step 2 builds and publishes the BlackLab index from that export wave
- Step 3 deploys runtime data and statistics, but not BlackLab index/export state
- Step 4 deploys media after the application and BlackLab data plane are aligned

## Explicit Non-Goals

Not changed here:

- CI/deploy workflows under `webapp/.github/workflows`
- server-side operator secrets
- production deploy script determinism issues already documented elsewhere

## Result

The maintenance/orchestrator layer now matches the intended dev/prod boundary model:

- no new `blacklab_export` path usage
- no wrapper-level dependency on the repo being literally named `webapp`
- remote targets aligned to `/srv/webapps/corapan/{app,data,media}`
- operator order made explicit and serial