# BlackLab Operational Safety

## Scope

This document defines the operational safety rules for the dev BlackLab stack in the canonical local layout:

- Git root: `webapp/`
- Dev runtime root: sibling workspace root
- Active dev index: `data/blacklab/index`
- Active dev export: `data/blacklab/export`
- Active dev config: `config/blacklab`

These rules exist because the 2026-03-21 incident was not caused by CQL, BLF, or export metadata. The failure was an active Lucene/BlackLab index corruption (`InvalidIndex` / `CorruptIndexException`) inside the mounted dev index.

## Incident-Driven Rules

1. Never rebuild while `blacklab-server-v3` is running.
2. Never serve from repo-local `webapp/data` or `webapp/runtime/corapan` in dev.
3. Never keep parallel active BlackLab roots such as `data/blacklab_index` or `data/blacklab_export` once the canonical `data/blacklab/...` tree is in use.
4. Never activate a freshly built index before BlackLab has read it successfully in an isolated validation container.
5. Never treat an HTTP-ready BlackLab root page as sufficient proof that the mounted index is healthy.

## Risk Classes

### Dev Workflow Risk

- Starting the app while BlackLab is up but serving a corrupt index produces misleading application symptoms.
- Reusing stale local layouts increases the chance that Docker mounts or operators point at the wrong index/config tree.

### Build and Index Risk

- The critical failure mode is a partially invalid active Lucene/BlackLab index, not a schema mismatch.
- A successful index build log alone is insufficient; the built index must answer a real hits query before activation.

### Docker and Mount Risk

- BlackLab dev depends on the exact mount contract:
  - `data/blacklab/index -> /data/index/corapan`
  - `config/blacklab -> /etc/blacklab`
- Starting a container against the wrong host tree can mask or recreate corruption problems.

### Deploy Risk

- Dev and prod must remain separate.
- Prod deploys must never copy dev runtime data or assume dev rebuild state.
- A BlackLab index should be treated as an operational artifact that must be validated before serving traffic.

## Enforced Script Guardrails

### `scripts/blacklab/build_blacklab_index.ps1`

- Aborts if `blacklab-server-v3` is running.
- Builds only into `data/blacklab/quarantine/index.build`.
- Starts a temporary validation container against the staged index.
- Runs a real hits smoke query before activation.
- Activates only after validation succeeds.

### `scripts/blacklab/start_blacklab_docker_v3.ps1`

- Refuses repo-local `webapp/data` and legacy `data/blacklab_index` / `data/blacklab_export` layouts.
- Requires canonical `config/blacklab` files.
- Refuses to replace an existing container unless `-Restart` is explicit.
- After startup, runs a real hits smoke query against the active index.
- Stops with an error if the container is reachable but the index is unreadable.

### `scripts/dev-start.ps1`

- Refuses repo-local `webapp/data` in dev.
- Keeps the existing canonical layout migration check.
- Verifies the BlackLab root endpoint and a real hits query before starting Flask.
- Fails fast with rebuild instructions if the active index is unreadable.

### `scripts/dev-setup.ps1`

- Refuses repo-local `webapp/data` in dev.
- Keeps the existing canonical layout migration check.
- Verifies the BlackLab root endpoint and a real hits query before declaring setup successful.
- Fails fast with rebuild instructions if the active index is unreadable.

## Smoke Query Policy

The scripts derive a smoke query from the first non-empty token in the canonical TSV export when available. If no export token can be derived, they fall back to `[word="casa"]`.

This is intentional:

- the validation must read actual hits, not only the root status page
- a 200 on `/blacklab-server/` alone does not prove the active index can serve result windows
- the check must be cheap enough to run during normal local workflows

## Future Deploy Rules

1. Rebuild or replace a BlackLab index only while the serving container for that index is stopped.
2. Validate the replacement index with a real query before switching the serving path.
3. Keep backups of the previous active index before activation.
4. Treat mixed dev/prod mount roots as a configuration error, not a warning.
5. If BlackLab returns 500 for a valid CQL that previously worked, inspect container logs before touching app query code.

## Developer Checklist

1. Stop `blacklab-server-v3` before running `scripts/blacklab/build_blacklab_index.ps1`.
2. Rebuild only into the canonical `data/blacklab` tree.
3. Start BlackLab only from the canonical sibling workspace layout.
4. Treat any failed hits smoke query as an index-serving problem first.
5. Inspect `docker logs blacklab-server-v3 --tail 200` before changing CQL, BLF, or app code.