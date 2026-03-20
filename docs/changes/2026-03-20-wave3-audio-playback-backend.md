# Wave 3.1 Audio Playback Backend Fix

Date: 2026-03-20
Scope: development audio snippet extraction and playback endpoint diagnostics
Change type: audio playback backend fix

## What Changed

- replaced implicit pydub/ffprobe-based snippet extraction with explicit ffmpeg command execution in `src/app/services/audio_snippets.py`
- added deterministic ffmpeg backend resolution via `CORAPAN_FFMPEG_PATH`, system `ffmpeg`, or bundled `imageio-ffmpeg`
- changed `/media/play_audio/...` and `/media/snippet` to return `503` when the audio processing backend is unavailable instead of misreporting a missing source file as `404`
- added focused regression tests for nested country-path playback and the ffmpeg-backend-unavailable case
- added `imageio-ffmpeg` to the runtime dependency set and refreshed `requirements.txt`
- documented the verified result in `docs/state/Welle_3.1_audio_playback_summary.md`

## Why It Changed

Wave 3 verification had already shown that canonical media paths worked for `/media/full/...` and `/media/transcripts/...`, but the Search UI still failed on `/media/play_audio/...`.

Fresh reproduction against the real DOM request showed that the route resolved the correct split source file and only failed when pydub tried to invoke missing `ffmpeg` and `ffprobe` binaries.

That made the real cause an audio backend dependency problem rather than a path-resolution bug.

## Affected Files

- src/app/services/audio_snippets.py
- src/app/routes/media.py
- tests/test_audio_snippet_integration.py
- tests/test_media_routes.py
- requirements.in
- requirements.txt
- docs/state/Welle_3.1_audio_playback_summary.md

## Operational Impact

- the canonical dev Search UI audio player no longer depends on a separately installed system ffmpeg binary when `imageio-ffmpeg` is present
- live playback snippets now return audio successfully for the verified DOM request
- backend-unavailable failures are now classified and surfaced correctly as service availability issues instead of false missing-file errors
- source selection and ffmpeg backend path are now visible in debug logs for playback verification

## Compatibility Notes

- media path resolution was not changed
- auth behavior was not changed
- PostgreSQL and BlackLab wiring were not changed
- production topology was not changed

## Follow-Up

- if production or container playback should avoid Python-level bundled binaries, validate whether container images already provide a preferred system ffmpeg and optionally set `CORAPAN_FFMPEG_PATH` explicitly there
- keep `/media/play_audio/...` in future media verification runs even when `/media/full/...` is already green