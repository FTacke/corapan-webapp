# BlackLab

BlackLab is an operational dependency, not a static asset.

## Canonical Inputs

- versioned config: `app/config/blacklab/`
- DEV container mount contract: `app/config/blacklab -> /etc/blacklab`
- PROD container mount contract in the current root-lifted checkout layout: `/srv/webapps/corapan/app/app/config/blacklab -> /etc/blacklab`
- local dev compose: `docker-compose.dev-postgres.yml`
- production app wiring: `app/infra/docker-compose.prod.yml`
- runtime export path: `data/blacklab/export/docmeta.jsonl`

Do not infer the production config path from the DEV repository path. The stale outer production path `/srv/webapps/corapan/app/config/blacklab` is not the active config source.

## Canonical Variables

- `BLS_BASE_URL`
- `BLS_CORPUS`

`BLACKLAB_BASE_URL` is legacy compatibility only.

## Safety Rules

- do not rebuild or replace the active index while BlackLab is serving it
- validate with a real hits query, not only `/blacklab-server/`
- if a valid hits query returns HTTP 500, inspect logs and active mounts before changing backend logic
- treat `data/blacklab/index` as mutable runtime state

## Maintainer Docs

- `../operations/blacklab_dev_health.md`
- `../architecture/blacklab_operational_safety.md`
- `../rsync/blacklab_prod_fix_report.md`
- `../rsync/blacklab_config_path_cleanup_audit.md`