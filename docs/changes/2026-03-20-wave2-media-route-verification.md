# Wave 2.1 Media Route Verification

Date: 2026-03-20
Scope: development-only media route verification and regression hardening
Change type: dev-only media diagnostics and regression coverage

## What Changed

- added explicit transcript resolution debug logging in the media blueprint so request filename, transcript base directory, and resolved transcript path are visible during dev verification
- added focused regression tests for `/media/full/...` and `/media/transcripts/...` covering both flat request paths and explicit country-subfolder request paths
- documented the runtime evidence and conclusion in `docs/state/Welle_2.1_summary.md`

## Why It Changed

After Wave 2, a media regression was reported for development.

Fresh-process verification against the canonical dev media root showed that the current media resolver already serves content correctly from `C:\dev\corapan\media`, including the subfolder-aware fallback from flat filenames like `2023-08-10_ARG_Mitre.mp3` to `mp3-full/ARG/2023-08-10_ARG_Mitre.mp3`.

Because the failure did not reproduce on the current code, the safe fix was to improve observability and lock the verified behavior in tests instead of changing path semantics that were already correct.

## Affected Files

- src/app/routes/media.py
- tests/test_media_routes.py
- docs/state/Welle_2.1_summary.md

## Operational Impact

- no production behavior changed
- no media storage paths changed
- dev verification now has clearer transcript-path evidence in logs
- future regressions in flat-versus-subfolder media routing should fail fast in tests

## What Was Intentionally Not Changed

- media root selection
- auth behavior
- BlackLab behavior
- production scripts and compose wiring
- existing media directory structure under `C:\dev\corapan\media`