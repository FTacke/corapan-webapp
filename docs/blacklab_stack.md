# BlackLab Stack Inventory, Decisions & HowTo

This file documents the BlackLab / Lucene index stack used by the CO.RA.PAN project.

## 0. Context & Goals

- Goal: Consistent, documented BlackLab index pipeline and server configuration.
- Hard requirement: All TSV exports must be indexable (no skipping files as quick fixes).
- Reproducibility: One canonical script to build the index.

## 1. What exists (Inventory)

- Scripts:
  - `scripts/build_blacklab_index_v3.ps1` — Docker-based index builder for BlackLab 5.x (uses `data/blacklab_export/tsv/`).
  - `scripts/build_blacklab_index.ps1` — Current JAR-based index builder (legacy). Uses `data/blacklab_index.backup/tsv/` and local JAR fallback if `BLACKLAB_JAR` is set.
  - `scripts/build_blacklab_index.old.ps1` — older legacy script.
  - `scripts/start_blacklab_docker_v3.ps1` — Start BlackLab 5.x Docker server (expects `data/blacklab_index` mounted under `/data/index/corapan`).
  - `scripts/start_blacklab_docker.ps1` — Start Docker server (older variations, currently uses `instituutnederlandsetaal/blacklab:latest`).
  - `src/scripts/blacklab_index_creation.py` — JSON → TSV exporter used to create `data/blacklab_export/tsv/*.tsv` and `data/blacklab_export/docmeta.jsonl`.
  - Various README, LOKAL scripts and troubleshooting docs referencing `data/blacklab_index.backup`.

- Config and Index:
  - BLF config: `config/blacklab/corapan-tsv.blf.yaml` — defines TSV format and fields.
  - Server config: `config/blacklab/blacklab-server.yaml` — comments indicate "BlackLab 5.0.0-SNAPSHOT (Lucene 9.11.1)".
  - Index directory: `data/blacklab_index/` (active index used by server), `data/blacklab_index.backup/` (historical snapshots — DO NOT use for new index builds).
  - TSV source: `data/blacklab_export/tsv/` and `data/blacklab_export/docmeta.jsonl` (expected inputs from the `blacklab_index_creation.py` exporter).

## 2. Recommended & Selected Target Stack (Final)

- BlackLab Server & Index Format:
  - BlackLab major version: 5.x (Lucene 9.x)
  - Observed/Reference build in repository: `5.0.0-SNAPSHOT` (see `test_corpus_info.json`)

  
  - Docker Image (pinned): `instituutnederlandsetaal/blacklab:5.0.0` (replaceable with an exact validated release).
  - Index Format: Lucene 9 (BlackLab 5.x compatible)

- Paths & Inputs (Canonical):
  - JSON source: `media/transcripts/` (input to exporter)
  - TSV: `data/blacklab_export/tsv/*.tsv`
  - Docmeta: `data/blacklab_export/docmeta.jsonl`
  - Target index: `data/blacklab_index/` (active index)
  - Backups: `data/blacklab_index.old_YYYYMMDD_HHMMSS/` for timestamped backups, and `data/blacklab_index.backup/` kept read-only as historical snapshot only.

- Canonical Scripts:
  - Build Index: `scripts/build_blacklab_index.ps1` — this is the canonical entrypoint. It will run the Docker-based IndexTool and be designed to be safe and reproducible.
  - Start Server: `scripts/start_blacklab_docker_v3.ps1` — starts the pinned Docker image and mounts `data/blacklab_index` as the active index.

## 3. Troubleshooting: `FileAlreadyExistsException (_1.fdt / _2.fdt)`

- Likely causes:
  - Parallel `IndexTool` threads writing same Lucene files (Windows/OneDrive FS causing race conditions) — `IndexTool` with default threads may trigger collisions.
  - Malformed TSVs causing indexer to write or reindex the same field id twice.

- Short answer fix:
  - Run IndexTool with `--threads 1` to avoid concurrency issues on Windows + OneDrive.
  - If the error persists with `--threads 1`: isolate the problematic TSV(s), run a minimal debug index, examine column names and special characters, and fix either the exporter code or the BLF config.

## 4. HowTo: Build the Index (Canonical, Reproducible)

1. Prepare: Export TSVs & docmeta using the exporter:
   - `python -m src.scripts.blacklab_index_creation --in media/transcripts --out data/blacklab_export/tsv --docmeta data/blacklab_export/docmeta.jsonl --workers 4`
2. Run the canonical build script (power shell):
   - `.uild_blacklab_index.ps1` (script includes validation and `--threads 1` by default)
3. Start the BlackLab server:
   - `.uild_blacklab_index.ps1 -Force` (if rebuilding without prompts), then `.uild_blacklab_index.ps1` will have logged the completed build; start the server with `.uild_blacklab_index.ps1` (I will ensure `start...` scripts match the chosen image tag.)
4. Validate:
   - Start server: `.uild_blacklab_index.ps1` (i.e., updated start script), then `curl http://localhost:8081/blacklab-server/` should return JSON with server version and index info.

## 5. Debugging VEN TSV FileAlreadyExistsException (Steps)

To isolate and debug the VEN errors (`2022-01-18_VEN_RCR.tsv` and `2022-03-14_VEN_RCR.tsv`):

1. Create a temporary index dir and run only the VEN files with `--threads 1` using the `scripts/debug_blacklab_ven_index.ps1` script created in `scripts/`.
2. Inspect the TSVs for format anomalies:
   - Verify headers match exactly the BLF config column names.
   - Check for BOM, stray control characters, and token_id duplication.
   - Compare column presence vs. other TSV files.
3. If the error persists, reduce the file to only first half or second half and run the build again to find the failing row.
4. Fix the exporter or BLF config (e.g., ensure columns are correct and properly typed).
5. Use `scripts/check_tsv_schema.py` to quickly validate that all TSV files share the same header schema; this is a fast check to detect structural differences across the 146 files.

## 6. Logging & Safety

- Build logs are written to `data/blacklab_index/build.log` with command, timestamp, image version, TSV count, docmeta count, and exit codes.
- `--threads 1` is the default to avoid Windows/OneDrive concurrency issues: Index builds should be deterministic.
- No script will skip problematic files by default. If a file is problematic, the build fails and the issue must be fixed, documented, and retested.

## 7. Next Steps & Notes

- Update `scripts/build_blacklab_index.ps1` (done) to be canonical; `build_blacklab_index_v3.ps1` will become a small shim that forwards to the canonical script and prints a deprecation message.
- Update `scripts/start_blacklab_docker*.ps1` to use the pinned Docker image and consistent mount points.
- Add `scripts/debug_blacklab_ven_index.ps1` for targeted debugging.
- Once these changes are validated (locally by running index build), update `docs/blacklab_stack.md` if any assumptions change.

----

PLEASE NOTE: This repository contains several legacy files and historic snapshots (including `data/blacklab_index.backup/`) — these are for historical purposes only and SHOULD NOT be used as the source of truth for new index builds. The canonical path is `data/blacklab_export/tsv/`.
