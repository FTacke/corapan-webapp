# 2026-03-24 Dev Start Root-Lift BlackLab Recovery

## What Changed

- Hardened `app/scripts/dev-start.ps1` to detect a still-running `blacklab-server-v3` container that is mounted from the legacy root-lift path `webapp/config/blacklab` instead of the canonical `app/config/blacklab`.
- The dev start flow now force-recreates that BlackLab container before the live hits smoke query runs.
- Updated `app/startme.md` to make the workspace-root entrypoint explicit and to document that the script uses the workspace virtual environment at `CORAPAN/.venv`.

## Why

After the repository root was lifted from `webapp/` to `CORAPAN/` with `app/` as the active implementation subtree, an already-running BlackLab container could survive with stale bind mounts.

That stale container still answered the generic root endpoint, but real hits queries failed with HTTP 500 because `/etc/blacklab` was mounted from `webapp/config/blacklab`, which no longer contained the canonical `blacklab-server.yaml`.

## Environment

- development / local workspace only
- no production workflow changed

## Operational Impact

- `./scripts/dev-start.ps1` from the workspace root remains the canonical daily start command.
- A stale BlackLab container is now classified as legacy runtime state and automatically replaced with the canonical compose mount before startup continues.
- The active config source for local dev BlackLab remains `app/config/blacklab`; `webapp/config/blacklab` is legacy.

## Compatibility Notes

- This change does not rebuild the active BlackLab index.
- It only recreates the BlackLab container when the mounted config path is wrong.
- Users already starting from `app/` can keep using `app/scripts/dev-start.ps1`; the wrapper path is documented as the preferred entrypoint.