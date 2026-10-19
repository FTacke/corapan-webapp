# Final CORAPAN internal cleanup

## Ausgangslage
CORAPAN v3.2 and the CO.PRE.PAN-compatible tense migration were already complete. This cleanup only removed redundant internal intermediate artifacts and local caches.

## Gesch?tzt

- `media/transcripts` was not modified.
- Stats DBs under `data/db/public` were not deleted.
- Protected pre-v3.1, pre-tense-migration, and manual-repair backups remain present.
- Final v3.2 reports, final audits/diffs, migration logs, and maintenance scripts remain present.

## Gel?scht

- Deleted files/directories: 41
- Removed redundant v3.1 smoke and mini-batch audit artifacts.
- Removed repo-local Python/pytest caches and empty temporary `_0_json` directories.
- Removed regenerated pytest caches after the safety test.

## Verschoben

- Moved files: 3
- `maintenance_pipelines/_0_json/docs/agent-runs/archive_commands/root_start_full_annotation.txt`
- `maintenance_pipelines/_0_json/docs/agent-runs/archive_commands/run_full_transcripts_annotation.ps1`
- `maintenance_pipelines/_0_json/docs/agent-runs/archive_commands/_0_json_start_full_annotation.txt`

## Bewusst behalten

- All backup directories, including old smoke backups.
- Current annotation/state/progress logs where useful for reproducibility.
- Migration tools and final documentation chain.

## Speicherplatz

- Freed bytes: 3025923 (2.89 MiB).

## Tests nach Cleanup

- Command: `.venv\Scripts\python.exe -m pytest maintenance_pipelines\_0_json\tests -q`
- Result: 9 passed.

## v3.2-Integrit?tspr?fung

- JSON files: 146
- Country folders: 25
- Total words: 1488019
- Pipeline versions: `{'corapan-transcript-ann-v3.2': 146}`
- Tense rules versions: `{'tense-v4-coprepan-compatible': 146}`
- `TenseRole=finite_past`: 0
- Missing token IDs: 0
- Duplicate token IDs: 0
- Hard failures: 0

## Verbleibende Artefaktstruktur

- Final docs remain under `maintenance_pipelines/_0_json/docs/agent-runs`.
- Final audits/diffs remain under `maintenance_pipelines/_0_json/docs/agent-runs/audits`.
- Archived manual full-run commands are under `maintenance_pipelines/_0_json/docs/agent-runs/archive_commands`.
- Protected backups remain under `maintenance_pipelines/_0_json/backups`.

## Hinweis
Analyse- und Studienentscheidungen liegen au?erhalb dieses CORAPAN-Cleanup-Laufs.

