# Data Inventory — Current State (2026-01-17)

Status: Baseline captured on `work/current`

---

## Overview

This document maps all data directories in the repository to their:
- **Purpose** (what data is stored)
- **Type** (lifecycle classification)
- **Size** (approximate)
- **Deployment** (included in Docker/production)
- **Git Status** (tracked vs. ignored)
- **Risk/Legacy Markers**

---

## A) Data Directories (`data/`)

**Note:** Entire `data/` directory is `.gitignore`d except `.gitkeep` (structure preservation only).

### `data/db/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | SQLite databases (auth, metadata indexes) |
| **Type** | `runtime` / `generated` |
| **Size** | ~50 MB (auth.db typically small; depends on metadata cache) |
| **Deployed?** | No (Docker uses separate PostgreSQL container) |
| **Readers** | Flask app, migration scripts |
| **Writers** | Flask app (ORM), auth migration scripts |
| **Context** | Local dev & SQLite fallback mode only (`-UseSQLite`) |
| **Risk** | 🟡 **RISK**: Contains user auth data; must be excluded from VCS; local dev only |
| **Legacy?** | No; required for dev (fallback) |

---

### `data/db_public/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Public/non-secret database exports or snapshots |
| **Type** | `build` / `export` |
| **Size** | ~10-100 MB (varies) |
| **Deployed?** | No |
| **Readers** | Analysis scripts, possibly deployment scripts |
| **Writers** | Export/backup scripts |
| **Context** | Development & local analysis |
| **Risk** | 🟡 **RISK**: Purpose unclear; check if still used |
| **Legacy?** | ⚠️ **LEGACY**: Appears vestigial; needs audit |

---

### `data/blacklab_export/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Intermediate exports for BlackLab indexing (TSV, JSON, docmeta) |
| **Type** | `build` / `generated` |
| **Size** | ~500 MB–2 GB (TSV files + metadata) |
| **Deployed?** | Yes (mounted in Docker for BlackLab indexing) |
| **Readers** | `build_blacklab_index.ps1`, `docmeta_to_metadata_dir.py` |
| **Writers** | `blacklab_index_creation.py`, `prepare_json_for_blacklab.py` |
| **Structure** | |
| · `tsv/` | Tab-separated corpus data (one file per recording date) |
| · `json_ready/` | JSON-formatted corpus ready for JSON indexing |
| · `docmeta.jsonl` | Document-level metadata (one JSON per line) |
| · `metadata/` | Expanded metadata directory (per-document JSONs) |
| **Context** | Build pipeline for BlackLab; critical for index creation |
| **Risk** | 🟢 OK: Clear purpose; actively used in build pipeline |
| **Legacy?** | No |

---

### `data/blacklab_index/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Live BlackLab Lucene search index |
| **Type** | `runtime` / `generated` |
| **Size** | ~5–20 GB (large; indexes tokenized corpus) |
| **Deployed?** | Yes (mounted in Docker as search backend) |
| **Readers** | BlackLab Server (Docker), search proxy (Flask) |
| **Writers** | `build_blacklab_index.ps1` (rebuilds on export change) |
| **Context** | Production use; critical for search functionality |
| **Risk** | 🟢 OK: Essential; protected by `build_blacklab_index.ps1` backup logic |
| **Notes** | Rebuilt from `blacklab_export/tsv/` via `build_blacklab_index.ps1` |
| **Legacy?** | No |

---

### `data/blacklab_index.backup/` + `.backup.*` variants

| Attribute | Value |
|-----------|-------|
| **Purpose** | Backup of previous/stable BlackLab indexes |
| **Type** | `backup` / `generated` |
| **Size** | ~5–20 GB per backup (multiple versions present) |
| **Deployed?** | No (not mounted; offline storage) |
| **Readers** | Manual restore operations (if needed) |
| **Writers** | `build_blacklab_index.ps1` (creates on rebuild) |
| **Variants** | `.backup/`, `.backup.bak_<timestamp>`, `.backup_<timestamp>` |
| **Context** | Safety net for index rebuilds; recovery mechanism |
| **Risk** | 🟡 **RISK**: Many backups accumulate; needs cleanup policy |
| **Legacy?** | No; useful but unmanaged; consider retention schedule |

---

### `data/blacklab_index.testbuild/` + `.testbuild.bak*`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Experimental or failed index builds (testing snapshots) |
| **Type** | `temp` / `experimental` |
| **Size** | ~5–20 GB (varies) |
| **Deployed?** | No |
| **Readers** | Manual inspection if index build debugging needed |
| **Writers** | `build_blacklab_index.ps1` (test mode) |
| **Context** | Development/debugging only |
| **Risk** | 🟠 **RISK**: Unmanaged test artifacts; candidates for deletion |
| **Legacy?** | ⚠️ **LEGACY**: Appears to be debug residue; unclear if still needed |

---

### `data/blacklab_index.bad_*`, `data/blacklab_index.new.bad_*`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Failed or problematic index builds (marked as corrupted) |
| **Type** | `temp` / `error` |
| **Size** | ~5–20 GB each |
| **Deployed?** | No |
| **Readers** | None (should be cleaned up) |
| **Writers** | `build_blacklab_index.ps1` (failure/corruption handling) |
| **Context** | Artifacts from index build failures |
| **Risk** | 🔴 **RISK**: Disk space waste; should be deleted |
| **Legacy?** | ⚠️ **LEGACY**: Explicit garbage; delete with approval |

---

### `data/counters/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Search result counters cache (for analytics/UI) |
| **Type** | `runtime` / `cache` |
| **Size** | ~10–50 MB |
| **Deployed?** | Yes (used by Flask app) |
| **Readers** | Flask search endpoints |
| **Writers** | Flask app (on-demand cache fill) |
| **Context** | Performance optimization; non-critical |
| **Risk** | 🟢 OK: Cache-like; safe to clear |
| **Legacy?** | No |

---

### `data/stats_temp/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Temporary statistics computation scratch space |
| **Type** | `temp` |
| **Size** | ~100–500 MB (depends on analysis) |
| **Deployed?** | No |
| **Readers** | Analysis/reporting scripts |
| **Writers** | Stats calculation scripts |
| **Context** | Development and report generation |
| **Risk** | 🟢 OK: Temp directory; safe to clear |
| **Legacy?** | No |

---

### `data/exports/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | User-triggered or automated corpus exports (JSON, CSV, TSV) |
| **Type** | `export` / `generated` |
| **Size** | ~100 MB–1 GB (varies by export scope) |
| **Deployed?** | Varies (may be mounted for download serving) |
| **Readers** | Web UI, export endpoint, analysis scripts |
| **Writers** | Flask app export endpoints, batch export scripts |
| **Context** | User-facing functionality |
| **Risk** | 🟢 OK: Purpose clear; regenerable |
| **Legacy?** | No |

---

### `data/metadata/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Metadata indexes/caches for search facets and document info |
| **Type** | `runtime` / `generated` |
| **Size** | ~50–200 MB |
| **Deployed?** | Yes (used by Flask app and BlackLab) |
| **Readers** | Flask search service, BlackLab Server |
| **Writers** | `blacklab_index_creation.py`, metadata sync scripts |
| **Context** | Search facet population, document detail pages |
| **Risk** | 🟢 OK: Regenerable from blacklab_export |
| **Legacy?** | No |

---

## B) Media Directories (`media/`)

**Note:** Entire `media/` directory is `.gitignore`d except `.gitkeep`.

### `media/transcripts/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Canonical transcript files (JSON v3 format) |
| **Type** | `runtime` / `source` |
| **Size** | ~100 MB–500 MB (corpus metadata + segment data) |
| **Deployed?** | Yes (source for BlackLab export; synced to production) |
| **Readers** | `blacklab_index_creation.py`, Flask search endpoints, analysis scripts |
| **Writers** | Data normalization scripts, user upload/import pipeline |
| **Context** | Core corpus data; foundation for search index |
| **Risk** | 🔴 **RISK**: Critical path; any corruption breaks search; versioned backup essential |
| **Legacy?** | No |

---

### `media/mp3-full/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Full-length MP3 recordings (one per transcript) |
| **Type** | `runtime` / `media` |
| **Size** | ~5–50 GB (large audio files) |
| **Deployed?** | Yes (served to UI for playback; synced to production) |
| **Readers** | Web UI audio player, analysis scripts |
| **Writers** | Media upload/import pipeline |
| **Context** | User-facing audio experience |
| **Risk** | 🟢 OK: Regenerable from source; backed up separately |
| **Legacy?** | No |

---

### `media/mp3-split/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Segment-level MP3 clips (one per transcript segment/token) |
| **Type** | `runtime` / `generated` |
| **Size** | ~10–100 GB (many small files; higher total than full) |
| **Deployed?** | Yes (served for segment-level playback; synced to production) |
| **Readers** | Web UI segment player, analysis |
| **Writers** | `split_audio.py` (or similar segmentation script) |
| **Context** | Fine-grained audio alignment |
| **Risk** | 🟡 **RISK**: Regenerable but time-consuming; production copy is canonical |
| **Legacy?** | No |

---

### `media/mp3-temp/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Temporary MP3 processing (transcoding, splitting, staging) |
| **Type** | `temp` |
| **Size** | ~1–10 GB (depends on active processing) |
| **Deployed?** | No |
| **Readers** | Processing scripts |
| **Writers** | MP3 pipeline scripts |
| **Context** | Build/processing scratch space |
| **Risk** | 🟢 OK: Temp directory; safe to clear |
| **Legacy?** | No |

---

## C) Static Assets (`static/`)

| Attribute | Value |
|-----------|-------|
| **Purpose** | CSS, JavaScript, images, fonts (web UI) |
| **Type** | `source` / `committed` |
| **Size** | ~10–50 MB |
| **Deployed?** | Yes (served by Flask / CDN) |
| **Readers** | Web UI, browser |
| **Writers** | Frontend development (rarely during runtime) |
| **Context** | Web interface styling & behavior |
| **Risk** | 🟢 OK: Tracked in Git; version-controlled |
| **Legacy?** | No |

### `static/img/statistics/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generated statistics charts/images (if any) |
| **Type** | `generated` |
| **Deployed?** | Depends (if served) |
| **Risk** | 🟡 **RISK**: Unclear if actively used; audit needed |

---

## D) LOKAL Directory (`LOKAL/`)

Contains local development & deployment orchestration tools (not deployed to production).

### `LOKAL/_2_deploy/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Deployment orchestration scripts (data/media sync to production) |
| **Type** | `tool` / `script` |
| **Size** | ~1 MB |
| **Deployed?** | No (dev machine only) |
| **Readers** | DevOps/Release engineer |
| **Writers** | Repository maintainer |
| **Scripts** | `deploy_data.ps1`, `deploy_media.ps1`, `publish_blacklab.ps1` |
| **Context** | Production synchronization (rsync-based, delta updates) |
| **Risk** | 🟢 OK: Tracked in Git; configuration-based |
| **Legacy?** | No |

---

### `LOKAL/_1_blacklab/`, `_1_metadata/`, `_0_json/`, etc.

| Attribute | Value |
|-----------|-------|
| **Purpose** | Local workflow directories (extraction, normalization, staging) |
| **Type** | `tool` / `workspace` |
| **Size** | Varies (often gigabytes of working data) |
| **Deployed?** | No |
| **Context** | Developer/analyst workspace for data prep |
| **Risk** | 🟡 **RISK**: Manual; untracked workflow state; not part of CI/CD |
| **Legacy?** | ⚠️ **LEGACY**: Appears to be semi-manual; should have structured pipeline |

---

## E) Logs (`logs/`)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Application and service logs |
| **Type** | `runtime` / `temp` |
| **Size** | ~100 MB–1 GB (depending on verbosity & retention) |
| **Deployed?** | No (logs stay on running servers) |
| **Readers** | Operators, debugging |
| **Writers** | Flask app, BlackLab, PostgreSQL (via Docker) |
| **Context** | Observability & troubleshooting |
| **Risk** | 🟢 OK: Should be log-rotated; monitored |
| **Legacy?** | No |

---

## F) Config (`config/`)

### `config/blacklab/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | BlackLab field & index configuration (YAML/XML) |
| **Type** | `source` / `committed` |
| **Size** | ~1 MB |
| **Deployed?** | Yes (mounted in Docker container) |
| **Readers** | BlackLab Server (Docker), `calc_blacklab_config_hash.py` |
| **Writers** | Repository maintainer |
| **Context** | Corpus indexing rules; critical for search behavior |
| **Risk** | 🟢 OK: Tracked in Git; version-controlled |
| **Legacy?** | No |

---

### `config/keys/`

| Attribute | Value |
|-----------|-------|
| **Purpose** | JWT, TLS, and other cryptographic keys (CRITICAL) |
| **Type** | `secret` |
| **Size** | ~10 KB |
| **Deployed?** | Yes (secrets mounted separately, not in repo) |
| **Status** | 🔴 `.gitignore`d; never committed |
| **Risk** | 🔴 **CRITICAL**: If ever committed, rotate immediately |
| **Legacy?** | No |

---

## Summary Table (Deployment & Risk)

| Path | Type | Deployed? | Tracked? | Risk/Legacy | Action |
|------|------|-----------|----------|-------------|--------|
| `data/db/` | runtime | No | ❌ ignored | 🟡 Contains user data | Keep ignored; use separate auth DB in prod |
| `data/db_public/` | build | No | ❌ ignored | 🟡 **LEGACY**: Purpose unclear | Audit & delete if unused |
| `data/blacklab_export/` | build | Yes | ❌ ignored | 🟢 OK | Critical to build pipeline |
| `data/blacklab_index/` | runtime | Yes | ❌ ignored | 🟢 OK | Protected by backup logic |
| `data/blacklab_index.backup*` | backup | No | ❌ ignored | 🟡 Accumulates | Establish retention policy |
| `data/blacklab_index.testbuild*` | temp | No | ❌ ignored | 🟠 Debug artifacts | Delete with approval |
| `data/blacklab_index.bad*` | error | No | ❌ ignored | 🔴 Garbage | Delete |
| `data/counters/` | cache | Yes | ❌ ignored | 🟢 OK | Safe to clear |
| `data/stats_temp/` | temp | No | ❌ ignored | 🟢 OK | Safe to clear |
| `data/exports/` | export | Varies | ❌ ignored | 🟢 OK | Regenerable |
| `data/metadata/` | generated | Yes | ❌ ignored | 🟢 OK | Regenerable from export |
| `media/transcripts/` | source | Yes | ❌ ignored | 🔴 Critical | Backup essential; core corpus |
| `media/mp3-full/` | media | Yes | ❌ ignored | 🟢 OK | Large but regenerable |
| `media/mp3-split/` | generated | Yes | ❌ ignored | 🟡 Time-consuming to rebuild | Backup production copy |
| `media/mp3-temp/` | temp | No | ❌ ignored | 🟢 OK | Safe to clear |
| `static/` | source | Yes | ✅ tracked | 🟢 OK | Version controlled |
| `config/blacklab/` | source | Yes | ✅ tracked | 🟢 OK | Version controlled |
| `config/keys/` | secret | Yes | ❌ ignored | 🔴 CRITICAL | Never commit; secure separately |
| `logs/` | runtime | No | ❌ ignored | 🟢 OK | Log-rotate; monitor |
| `LOKAL/_2_deploy/` | tool | No | ✅ tracked | 🟢 OK | Deployment orchestration |

---

## Notes

1. **All `data/` and `media/` paths are `.gitignore`d** — structure preserved only via `.gitkeep`.
2. **Backup Strategy Needed:**
   - `media/transcripts/` — Core source; critical backup
   - `data/blacklab_index/` — Regenerable but time-consuming
   - Backup frequency & retention policy missing
3. **Disk Space Issues:**
   - Multiple `.backup*` and `.bad*` directories accumulate automatically
   - Need cleanup/retention script
4. **Legacy/Unclear Paths:**
   - `data/db_public/` — Unclear purpose
   - `LOKAL/_*_*` directories — Semi-manual workflow
   - `static/img/statistics/` — Check if used
5. **Production vs. Development:**
   - Dev uses SQLite (`data/db/`) or Docker PostgreSQL
   - Prod uses separate secrets management (keys not in repo)
   - Deployment syncs `media/` and `data/blacklab_export/` to production

---

**Generated:** 2026-01-17 | **Branch:** `work/current` | **Status:** Baseline inventory
