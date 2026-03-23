# 2026-03-20 BlackLab repo path migration

## What changed

Active BlackLab repo defaults were migrated from flat legacy paths to the canonical structure under `data/blacklab`.

- exports: `data/blacklab/export`
- active index: `data/blacklab/index`
- backups: `data/blacklab/backups`
- quarantine and staging: `data/blacklab/quarantine`

The app docmeta resolver now targets `data/blacklab/export/docmeta.jsonl` and supports an explicit override via `CORAPAN_BLACKLAB_DOCMETA_PATH`.

## Why

The repo previously mixed several BlackLab path models:

- flat repo paths such as `data/blacklab_export` and `data/blacklab_index`
- runtime-specific app docmeta paths
- top-level production BlackLab paths used by separate operational scripts

That mismatch made build, publish, retention, compose, and app reads disagree about the intended structure.

## Scope

Updated:

- active path resolution in app code
- BlackLab export/build/start/publish/retention scripts
- deploy-sync exclusions
- CI runtime preparation
- dev/prod compose BlackLab-related mounts
- selected operational docs and helper scripts

Not rewritten automatically:

- historical forensic reports under `docs/state`
- preserved legacy material under `scripts/deploy_sync/legacy`
- debug helpers outside the canonical build/publish path

## Operational note

This change prepares the repo and container mounts for the target structure but does not itself move live production data trees on the server.
