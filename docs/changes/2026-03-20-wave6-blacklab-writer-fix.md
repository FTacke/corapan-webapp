# Wave 6 BlackLab Writer Fix

Date: 2026-03-20
Scope: production BlackLab publish default, deploy-sync path helper, and deploy-sync documentation
Change type: deployment-path correction without runtime topology change

## What Changed

- added an explicit `BlackLabDataRoot` to `scripts/deploy_sync/_lib/ssh.ps1`
- changed `scripts/deploy_sync/publish_blacklab_index.ps1` to default `-DataDir` to the live top-level BlackLab data root instead of the runtime-first `DataRoot`
- removed the implicit fallback that previously reused the runtime-first data deploy target for BlackLab publish
- updated `scripts/deploy_sync/README.md` to document the corrected default and the intentional separation from runtime-first data/media deploys
- documented the run and verification in `docs/state/Welle_6_blacklab_writer_fix_summary.md`

## Why It Changed

Wave 5 proved that production BlackLab reads `/srv/webapps/corapan/data/blacklab_index`, while the default BlackLab publish flow still targeted `/srv/webapps/corapan/runtime/corapan/data/blacklab_index`.

That left a dangerous default mismatch between the live reader and the standard writer, even though data and media deploys were correctly runtime-first.

## Affected Files

- scripts/deploy_sync/_lib/ssh.ps1
- scripts/deploy_sync/publish_blacklab_index.ps1
- scripts/deploy_sync/README.md
- docs/state/Welle_6_blacklab_writer_fix_summary.md
- docs/state/instance-structure-unification-plan.md

## Operational Impact

- default BlackLab publish now targets the same top-level path the live BlackLab container reads
- data deploy remains runtime-first via `Get-RemotePaths().DataRoot`
- media deploy remains runtime-first via `Get-RemotePaths().MediaRoot`
- no container mounts, restart behavior, or application runtime paths were changed

## Compatibility Notes

- an explicit `-DataDir` override still wins when an operator intentionally supplies it
- the change does not migrate, copy, delete, or modify any BlackLab index contents by itself
- no web-app deploy, PostgreSQL/auth, analytics, or compose changes were made

## Legacy Paths Intentionally Kept

- `/srv/webapps/corapan/runtime/corapan/data/blacklab_index` remains present as an existing duplicate path; this run only removes it as the standard publish target
- runtime-first data and media deploy roots remain canonical for non-BlackLab deploy flows

## Follow-Up

- execute a dedicated dry-run or controlled publish only when explicitly approved
- keep validating wrapper scripts and operator docs against the corrected top-level BlackLab default