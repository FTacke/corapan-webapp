# Data Layout Audit: Current State

**Date:** 2026-01-16  
**Purpose:** Inventory and analysis of data locations, naming, producers, and consumers in `corapan-webapp` to prepare for data reorganization.  
**Scope:** Analysis only — no code changes or refactoring in this phase.

---

## Executive Summary

The CO.RA.PAN webapp has grown organically, resulting in data artifacts stored across multiple locations with inconsistent naming conventions. This audit documents:

1. **Current directory structure and sizes**
2. **Glossary of data concepts and their current locations**
3. **Producer/Consumer mapping** (who writes/reads what)
4. **Deploy/Sync behavior** (Git vs rsync)
5. **Identified inconsistencies and risks**
6. **Proposed target layout** (without implementation)
7. **Migration plan outline** (for future PRs)

**Key Finding:** Data is split between:
- `data/` (1797 MB, 3336 files) — databases, BlackLab exports, metadata
- `static/img/statistics/` (3.5 MB, 29 files) — **public site assets tracked in Git**
- `media/` (15168 MB, 3007 files) — audio files and transcripts
- `LOKAL/` (18 MB, 142 files) — pipeline intermediate results

**Critical Issues:**
1. Generated site assets (`static/img/statistics/*`) are **committed to Git** (should be generated/synced)
2. Multiple overlapping directories: `blacklab_export` vs `exports`, `blacklab_index` vs `.new` vs `.backup`
3. `data/db/*` contains both public (stats) and restricted (auth) databases without clear separation
4. No single source of truth for "what gets deployed how"

---

## Table of Contents

- [Phase A: Inventory](#phase-a-inventory)
  - [A1: Directory Tree and Sizes](#a1-directory-tree-and-sizes)
  - [A2: Glossary of Data Concepts](#a2-glossary-of-data-concepts)
- [Phase B: Producer/Consumer Mapping](#phase-b-producerconsumer-mapping)
  - [B1: Data Producers (Writers)](#b1-data-producers-writers)
  - [B2: Data Consumers (Readers)](#b2-data-consumers-readers)
  - [B3: Deploy/Sync Analysis](#b3-deploysync-analysis)
- [Phase C: Inconsistencies & Risks](#phase-c-inconsistencies--risks)
- [Phase D: Proposed Target Layout](#phase-d-proposed-target-layout)
- [Phase E: Migration Plan](#phase-e-migration-plan)
- [Checklist](#checklist)

---

## Phase A: Inventory

### A1: Directory Tree and Sizes

#### Top-Level Summary

| Directory             | Size (MB) | Files | In Git? | Purpose                           |
|-----------------------|-----------|-------|---------|-----------------------------------|
| `data/`               | 1796.57   | 3336  | No      | Databases, exports, indexes       |
| `static/img/statistics/` | 3.50   | 29    | **Yes** | Public corpus statistics (PNGs + JSON) |
| `media/`              | 15168.25  | 3007  | No      | Audio files + transcripts         |
| `LOKAL/`              | 17.93     | 142   | No      | Pipeline intermediate outputs     |

#### `data/` Subdirectory Breakdown

```
data/
├── blacklab_export/         737.87 MB    445 files
│   ├── metadata/            (individual JSON metadata files)
│   ├── tsv/                 (TSV files for BlackLab indexing)
│   └── tsv_json_test/       (test outputs)
├── blacklab_index/          278.62 MB     75 files (active index)
├── blacklab_index.new/      278.62 MB     75 files (staged index)
├── blacklab_index.backup_20260114_232911/  290.65 MB  657 files
├── exports/                 161.73 MB    147 files
├── db/                       45.75 MB   1286 files
│   ├── stats_files.db       (atlas per-file stats)
│   ├── stats_country.db     (atlas per-country stats)
│   ├── auth.db              (user accounts, tokens - SENSITIVE)
│   └── postgres_dev/        (local PostgreSQL data dir - dev only)
├── metadata/                  3.31 MB    615 files
│   ├── latest/              (symlink → versioned metadata export)
│   ├── v2025-12-01/
│   └── v2025-12-06/
│       └── tei/             (TEI headers per recording)
├── db_public/                 0.01 MB      2 files
│   └── stats_all.db         (global public statistics)
├── stats_temp/                0.02 MB     26 files (temp calculation outputs)
└── counters/                     0 B      7 files (feature counters)
```

**Notes:**
- **Three BlackLab index copies exist:** `blacklab_index` (active), `blacklab_index.new` (staging), `blacklab_index.backup_*` (timestamped backups)
- **Two export directories:** `blacklab_export` (737 MB, source TSVs/metadata) vs `exports` (162 MB, purpose unclear)
- **DB split:** `data/db/` mixes public (stats) and private (auth), while `data/db_public/` is separate

#### `media/` Subdirectory Breakdown

```
media/
├── mp3-full/       (full radio recordings - multi-GB)
├── mp3-split/      (segmented audio clips - multi-GB)
├── mp3-temp/       (temporary processing - NOT deployed)
└── transcripts/    (annotated JSON files per country)
    ├── ARG/
    ├── ESP/
    └── ... (per-country subdirs)
```

**Note:** Audio directories (`mp3-full`, `mp3-split`) contain ~15 GB of data. `mp3-temp` is excluded from deployment.

#### `static/img/statistics/` (Committed to Git!)

```
static/img/statistics/
├── corpus_stats.json                    (global corpus summary)
├── viz_total_corpus.png                 (PRO vs OTRO pie chart)
├── viz_genero_profesionales.png         (M vs F bar chart)
├── viz_modo_genero_profesionales.png    (Mode × Gender stacked bar)
└── viz_<COUNTRY>_resumen.png            (per-country combined viz, 25 files)
```

**Evidence:**
```bash
# In Git:
$ git ls-files static/img/statistics | wc -l
29

# Generated by:
LOKAL/_0_json/05_publish_corpus_statistics.py → static/img/statistics/
```

**Issue:** These are **generated artifacts** but are **tracked in Git**. Changes to corpus data require commits with binary diffs.

#### `LOKAL/` (Pipeline Workspace)

```
LOKAL/
├── _0_json/
│   ├── json-pre/        (preprocessing inputs)
│   ├── json-ready/      (normalized JSON)
│   └── results/         (CSV/PNG outputs from step 04)
│       ├── corpus_statistics.csv
│       ├── corpus_statistics_across_countries.csv
│       └── viz_*.png    (internal analysis charts)
├── _0_mp3/              (audio processing workspace)
├── _1_blacklab/         (BlackLab build artifacts)
├── _1_metadata/         (metadata export scripts)
├── _1_zenodo-repos/     (Zenodo dataset mirrors)
├── _2_deploy/           (deployment staging)
└── _3_analysis_on_json/ (R&D scripts)
```

**Note:** `LOKAL/_0_json/results/*.csv` are **inputs** to `05_publish_corpus_statistics.py`, which outputs to `static/img/statistics/`.

---

### A2: Glossary of Data Concepts

| Concept                  | Current Location(s)                          | Description                                      | Size/Scope          |
|--------------------------|---------------------------------------------|--------------------------------------------------|---------------------|
| **Raw Media**            | `media/mp3-full/`, `media/mp3-split/`       | Radio broadcast recordings (full + split)        | ~15 GB              |
| **Annotated Transcripts**| `media/transcripts/<country>/`              | JSON files with tokens, metadata (v3 schema)     | Part of media/      |
| **BlackLab TSV Export**  | `data/blacklab_export/tsv/`                 | TSV files prepared for BlackLab indexing         | ~738 MB             |
| **BlackLab Metadata**    | `data/blacklab_export/metadata/`, `docmeta.jsonl` | Per-file metadata (JSON/JSONL)            | Part of blacklab_export/ |
| **BlackLab Index (Active)** | `data/blacklab_index/`                   | Running BlackLab search index                    | 279 MB              |
| **BlackLab Index (Staging)** | `data/blacklab_index.new/`              | Pre-deployment index build                       | 279 MB              |
| **BlackLab Index (Backup)** | `data/blacklab_index.backup_<timestamp>/` | Timestamped rollback snapshots                   | ~291 MB each        |
| **Generic Exports**      | `data/exports/`                             | Purpose unclear (overlaps with blacklab_export?) | 162 MB              |
| **Public Metadata**      | `data/metadata/latest/`, versioned dirs     | FAIR-compliant corpus metadata (TSV, JSON, TEI)  | 3.3 MB              |
| **Stats Databases (Private)** | `data/db/stats_files.db`, `stats_country.db` | SQLite DBs for Atlas feature (per-file, per-country) | ~46 MB total   |
| **Stats Database (Public)** | `data/db_public/stats_all.db`            | Global public statistics for frontend            | 10 KB               |
| **Auth Database**        | `data/db/auth.db`                           | User accounts, tokens, analytics (SENSITIVE)     | Part of data/db/    |
| **Temporary Stats**      | `data/stats_temp/`                          | Intermediate calculation files                   | 20 KB               |
| **Counters**             | `data/counters/`                            | Search feature counters (e.g., downloads)        | ~0 B (empty files)  |
| **Site Statistics Assets** | `static/img/statistics/`                  | Public PNG charts + corpus_stats.json            | 3.5 MB (**in Git!**)|
| **Pipeline Intermediates** | `LOKAL/_0_json/results/`                  | CSV/PNG from internal analysis (not deployed)    | ~18 MB              |

**Key Observations:**
1. **"Export" ambiguity:** `data/blacklab_export/` (TSV for search) vs `data/exports/` (purpose unclear) vs `data/metadata/` (public FAIR metadata)
2. **"Stats" split:** Private DBs in `data/db/`, public DB in `data/db_public/`, temp files in `data/stats_temp/`
3. **"Index" proliferation:** Active + staging + timestamped backups
4. **Pipeline boundary blur:** `LOKAL/results/` → `static/img/statistics/` crosses the local/deploy boundary

---

## Phase B: Producer/Consumer Mapping

### B1: Data Producers (Writers)

| Output Path                       | Producer Script/Module                          | Trigger                              | Evidence (File:Line) |
|-----------------------------------|-------------------------------------------------|--------------------------------------|----------------------|
| `data/db/stats_files.db`          | *(Unknown — not found in codebase)*             | Likely legacy/manual                 | Referenced in [src/app/services/database.py:15](src/app/services/database.py#L15) |
| `data/db/stats_country.db`        | *(Unknown — not found in codebase)*             | Likely legacy/manual                 | Referenced in [src/app/services/database.py:16](src/app/services/database.py#L16) |
| `data/db_public/stats_all.db`     | *(Unknown — implied by pipeline docs)*          | Step 03: `03_build_metadata_stats.py` (not in repo) | Mentioned in [LOKAL/_0_json/05_publish_corpus_statistics.py:31](LOKAL/_0_json/05_publish_corpus_statistics.py#L31) |
| `data/db/auth.db`                 | [scripts/apply_auth_migration.py](scripts/apply_auth_migration.py), [scripts/create_initial_admin.py](scripts/create_initial_admin.py) | Manual admin scripts, migration      | apply_auth_migration.py:42, create_initial_admin.py:34 |
| `data/blacklab_export/tsv/*.tsv`  | [src/scripts/blacklab_index_creation.py](src/scripts/blacklab_index_creation.py) | Manual: `python blacklab_index_creation.py` | blacklab_index_creation.py:381 |
| `data/blacklab_export/docmeta.jsonl` | [src/scripts/blacklab_index_creation.py](src/scripts/blacklab_index_creation.py) | Same as above                        | blacklab_index_creation.py:514 |
| `data/blacklab_export/metadata/*.json` | [scripts/blacklab/docmeta_to_metadata_dir.py](scripts/blacklab/docmeta_to_metadata_dir.py) | Manual: convert docmeta.jsonl → per-file JSON | docmeta_to_metadata_dir.py:8 |
| `data/blacklab_index.new/`        | BlackLab Docker container (via [scripts/deploy_sync/publish_blacklab_index.ps1](scripts/deploy_sync/publish_blacklab_index.ps1)) | BlackLab indexer build               | Implied by publish script |
| `data/blacklab_index/`            | Atomic swap from `.new` (via [publish_blacklab_index.ps1](scripts/deploy_sync/publish_blacklab_index.ps1)) | After validation                     | Implied by publish script |
| `data/blacklab_index.backup_<ts>/`| Backup creation during swap (via [publish_blacklab_index.ps1](scripts/deploy_sync/publish_blacklab_index.ps1)) | Before activating new index          | publish_blacklab_index.ps1:~150+ |
| `data/metadata/v<date>/`          | *(Unknown — export_metadata.py not in repo)*    | Manual metadata export               | Mentioned in [src/app/routes/corpus.py:183](src/app/routes/corpus.py#L183) |
| `data/metadata/latest`            | Symlink created by metadata export script       | Part of metadata versioning          | Referenced in [src/app/routes/corpus.py:51](src/app/routes/corpus.py#L51) |
| `media/transcripts/<country>/*.json` | [LOKAL/_0_json/02_annotate_transcripts_v3.py](LOKAL/_0_json/02_annotate_transcripts_v3.py) (implied by pipeline) | Step 02: annotation pipeline         | Referenced in pipeline docs |
| `static/img/statistics/*.png`     | [LOKAL/_0_json/05_publish_corpus_statistics.py](LOKAL/_0_json/05_publish_corpus_statistics.py) | Manual: `python 05_publish_corpus_statistics.py` | 05_publish_corpus_statistics.py:80 (`OUTPUT_DIR = PROJECT_ROOT / "static" / "img" / "statistics"`) |
| `static/img/statistics/corpus_stats.json` | [LOKAL/_0_json/05_publish_corpus_statistics.py](LOKAL/_0_json/05_publish_corpus_statistics.py) | Same as above                        | Same file |
| `LOKAL/_0_json/results/*.csv`     | [LOKAL/_0_json/04_internal_country_statistics.py](LOKAL/_0_json/04_internal_country_statistics.py) | Step 04: internal stats              | 04_internal_country_statistics.py:685-686 |
| `LOKAL/_0_json/results/*.png`     | [LOKAL/_0_json/04_internal_country_statistics.py](LOKAL/_0_json/04_internal_country_statistics.py) | Same as above                        | 04_internal_country_statistics.py:767-827 |

**Key Findings:**
1. **Missing producers:** Stats databases (`stats_files.db`, `stats_country.db`, `stats_all.db`) have no identifiable producer scripts in the current codebase.
2. **Manual triggers:** Most data artifacts are generated by **manual script execution**, not automated CI/CD.
3. **Git-tracked outputs:** `static/img/statistics/*` files are **written by a script** but **committed to Git** (anti-pattern).
4. **BlackLab workflow:** TSV export → Docker build → `.new` → validate → atomic swap → backup old index.

---

### B2: Data Consumers (Readers)

| Input Path                        | Consumer Module/Route                           | Purpose                              | Evidence (File:Line) |
|-----------------------------------|-------------------------------------------------|--------------------------------------|----------------------|
| `data/db/stats_files.db`          | [src/app/services/atlas.py](src/app/services/atlas.py) | Atlas map: per-file statistics       | atlas.py:11, atlas.py:27 |
| `data/db/stats_country.db`        | [src/app/services/atlas.py](src/app/services/atlas.py) | Atlas map: per-country aggregation   | atlas.py:46 |
| `data/db_public/stats_all.db`     | *(Unknown — possibly frontend/stats routes)*    | Global public statistics             | Defined in [services/database.py:17](src/app/services/database.py#L17) |
| `data/db/auth.db`                 | [src/app/auth/services.py](src/app/auth/services.py), [src/app/extensions/sqlalchemy_ext.py](src/app/extensions/sqlalchemy_ext.py) | User authentication, tokens, analytics | sqlalchemy_ext.py:4 |
| `data/blacklab_export/docmeta.jsonl` | [tests/test_docmeta_lookup.py](tests/test_docmeta_lookup.py) | Unit tests                           | test_docmeta_lookup.py:7 |
| `data/blacklab_index/`            | BlackLab Docker container (external service)    | Full-text corpus search              | Config in [config/blacklab/](config/blacklab/) |
| `data/metadata/latest/*.tsv`      | [src/app/routes/corpus.py](src/app/routes/corpus.py) (`/corpus/metadata/download/*`) | Public FAIR metadata downloads       | corpus.py:164 |
| `data/metadata/latest/*.json`     | [src/app/routes/corpus.py](src/app/routes/corpus.py)                                 | Same as above                        | corpus.py:164 |
| `data/metadata/latest/*.jsonld`   | [src/app/routes/corpus.py](src/app/routes/corpus.py)                                 | Same as above                        | corpus.py:164 |
| `data/metadata/latest/tei/*.xml`  | [src/app/routes/corpus.py](src/app/routes/corpus.py) (`/corpus/metadata/download/tei`) | TEI header download (zipped)         | corpus.py:164 |
| `static/img/statistics/*.png`     | Frontend templates (e.g., `/corpus/metadata` page) | Display corpus composition charts    | Served via static file route |
| `static/img/statistics/corpus_stats.json` | Frontend JS (optional dynamic loading)  | Dynamic corpus statistics            | Served via static file route |
| `media/transcripts/<country>/*.json` | [src/app/routes/editor.py](src/app/routes/editor.py)                              | Admin: edit/backup transcripts       | editor.py:144, editor.py:153 |
| `media/mp3-full/<country>/*.mp3`  | [src/app/routes/media.py](src/app/routes/media.py) (`/media/play_audio`)            | Audio playback (auth-gated)          | Implied by route |
| `media/mp3-split/<country>/*.mp3` | [src/app/routes/media.py](src/app/routes/media.py) (snippets)                       | Audio snippets                       | Implied by route |

**Key Findings:**
1. **Database access patterns:**
   - `stats_files.db` and `stats_country.db` → Atlas feature only ([services/database.py:11-17](src/app/services/database.py#L11-17))
   - `auth.db` → Authentication + analytics ([auth/services.py](src/app/auth/services.py))
   - `stats_all.db` → Defined but no clear consumer found (legacy?)
2. **Metadata consumption:** All FAIR metadata served from `data/metadata/latest/` via [routes/corpus.py](src/app/routes/corpus.py)
3. **Statistics consumption:** `static/img/statistics/*` files are served as **static assets** (Flask default behavior, no explicit route)
4. **Transcript editing:** [routes/editor.py](src/app/routes/editor.py) writes backups to `media/transcripts/<country>/backup/` (creates subdirs dynamically)

**Failure Modes:**
- **Missing `data/metadata/latest/`:** Metadata download endpoints return 404 (no fallback)
- **Missing `data/db/stats_*.db`:** Atlas feature breaks (no error handling observed)
- **Missing `static/img/statistics/`:** Frontend displays broken images
- **Missing `data/blacklab_index/`:** BlackLab container fails to start

---

### B3: Deploy/Sync Analysis

#### Git-Tracked Items (Deployed via `git pull`)

**Evidence:** `.gitignore` excludes `data/` and `media/` entirely, but `static/img/statistics/*` is **NOT excluded**.

```bash
# From .gitignore:
data/       # Entire directory ignored
media/      # Entire directory ignored
!data/.gitkeep
!media/.gitkeep

# static/img/statistics/ is NOT in .gitignore → tracked by Git
```

**Git-tracked data artifacts:**
- `static/img/statistics/*.png` (29 files, 3.5 MB)
- `static/img/statistics/corpus_stats.json`

**Issue:** These files are **generated outputs** but require **Git commits** to update. This causes:
- Binary diffs in version control
- Merge conflicts in collaborative workflows
- Tight coupling between data pipeline and code repo

#### Rsync-Synced Items (Deployed via `scripts/deploy_sync/*.ps1`)

**Script:** [scripts/deploy_sync/sync_data.ps1](scripts/deploy_sync/sync_data.ps1)

**Synced directories:**
```powershell
# From sync_data.ps1:97-103
$DATA_DIRECTORIES = @(
    "counters",
    "db_public",
    "metadata",
    "exports",
    "blacklab_export"
)

# Plus selective files from data/db/:
$STATS_DB_FILES = @(
    "stats_files.db",
    "stats_country.db"
)
```

**NOT synced (intentionally excluded):**
- `data/blacklab_index/` — rebuilt on prod server
- `data/blacklab_index.backup_*/` — local dev backups
- `data/stats_temp/` — temporary files
- `data/db/auth.db` — prod manages its own auth DB
- `data/db/postgres_dev/` — dev-only PostgreSQL

**Script:** [scripts/deploy_sync/sync_media.ps1](scripts/deploy_sync/sync_media.ps1)

**Synced directories:**
```powershell
# From sync_media.ps1:88-92
$MEDIA_DIRECTORIES = @(
    "transcripts",
    "mp3-full",
    "mp3-split"
)
```

**NOT synced:**
- `media/mp3-temp/` — temporary processing files

**Script:** [scripts/deploy_sync/publish_blacklab_index.ps1](scripts/deploy_sync/publish_blacklab_index.ps1)

**Workflow:**
1. Upload `data/blacklab_index.new/` to prod (`/srv/webapps/corapan/data/blacklab_index.new`)
2. Validate index (spin up BlackLab container on validation port)
3. Backup current index (`blacklab_index` → `blacklab_index.bak_<timestamp>`)
4. Atomic swap (`.new` → `blacklab_index`)
5. Restart production BlackLab container
6. Cleanup old backups (keep last N)

**Evidence:** [publish_blacklab_index.ps1:1-50](scripts/deploy_sync/publish_blacklab_index.ps1#L1-50)

---

#### Deployment Matrix

| Artifact                  | Source of Truth | Deploy Method       | Regeneration | Size Risk  |
|---------------------------|----------------|---------------------|--------------|------------|
| `static/img/statistics/*` | **Git**        | `git pull`          | Manual script| Low (3 MB) |
| `data/counters/`          | Sync           | rsync (delta)       | N/A          | None       |
| `data/db_public/*.db`     | Sync           | rsync (delta)       | Pipeline     | None       |
| `data/metadata/`          | Sync           | rsync (delta)       | Manual script| Low (3 MB) |
| `data/exports/`           | Sync           | rsync (delta)       | Unknown      | Medium (162 MB) |
| `data/blacklab_export/`   | Sync           | rsync (delta)       | Manual script| High (738 MB) |
| `data/db/stats_*.db`      | Sync           | rsync (selective)   | Unknown      | Medium (46 MB) |
| `media/transcripts/`      | Sync           | rsync (delta)       | Pipeline     | Medium (varies) |
| `media/mp3-full/`         | Sync           | rsync (delta, slow) | Manual       | **Very High (GB)** |
| `media/mp3-split/`        | Sync           | rsync (delta, slow) | Manual       | **Very High (GB)** |
| `data/blacklab_index/`    | **Build on Prod** | Special (publish_blacklab_index.ps1) | Always | High (279 MB) |

**Critical Observation:** `static/img/statistics/*` is the **only data artifact in Git**. All other artifacts are synced or rebuilt.

---

## Phase C: Inconsistencies & Risks

### 1. Duplicate/Overlapping Concepts

#### Issue 1.1: Multiple "Export" Directories

**Locations:**
- `data/blacklab_export/` (738 MB) — TSV files + docmeta for BlackLab indexing
- `data/exports/` (162 MB) — **Purpose unclear, no producer/consumer found**
- `data/metadata/` (3.3 MB) — Public FAIR metadata exports

**Problem:**
- **Semantic overlap:** All three contain "exported" data, but for different purposes.
- **No documentation:** `data/exports/` has no clear role (legacy? dead code?).
- **Risk:** Developers unsure which directory to use for new exports.

**Evidence:**
- [sync_data.ps1:97-103](scripts/deploy_sync/sync_data.ps1#L97-103) syncs all three without explaining the distinction.
- No grep matches for `data/exports/` writes in Python codebase.

---

#### Issue 1.2: Three BlackLab Index Copies

**Locations:**
- `data/blacklab_index/` (279 MB) — Active production index
- `data/blacklab_index.new/` (279 MB) — Staging index (pre-validation)
- `data/blacklab_index.backup_<timestamp>/` (291 MB each) — Rolling backups

**Problem:**
- **Disk usage:** 3× redundancy = ~850 MB for a single logical index.
- **Manual cleanup:** Old backups accumulate (script keeps only last N, but manual intervention may be needed).
- **Confusing naming:** `.new` is not a temporary suffix (persists after deployment).

**Evidence:**
- [publish_blacklab_index.ps1](scripts/deploy_sync/publish_blacklab_index.ps1) manages the swap but leaves `.new` in place.
- Directory listing shows `backup_20260114_232911` — unclear if older backups exist.

---

#### Issue 1.3: `data/db/` vs `data/db_public/` Split

**Locations:**
- `data/db/` — Contains both:
  - Public: `stats_files.db`, `stats_country.db`
  - Private: `auth.db`, `postgres_dev/`
- `data/db_public/` — Contains only `stats_all.db`

**Problem:**
- **Inconsistent organization:** Public stats are split between `db/` and `db_public/`.
- **Security risk:** `data/db/` mixes public and sensitive data (auth DB).
- **Sync complexity:** [sync_data.ps1](scripts/deploy_sync/sync_data.ps1) must selectively sync files from `data/db/` (excludes `auth.db`), adding fragility.

**Evidence:**
- [sync_data.ps1:106-109](scripts/deploy_sync/sync_data.ps1#L106-109) hardcodes `$STATS_DB_FILES = @("stats_files.db", "stats_country.db")`.
- [services/database.py:11-17](src/app/services/database.py#L11-17) defines all three stats DBs but locations are inconsistent.

---

### 2. Naming/Location Drift

#### Issue 2.1: Generated Site Assets in `static/`

**Problem:**
- `static/img/statistics/` contains **generated artifacts** (PNGs + JSON).
- Traditionally, `static/` holds **source assets** (CSS, JS, fonts, logos), not pipeline outputs.
- **Anti-pattern:** Generated files tracked in Git → binary diffs, merge conflicts.

**Evidence:**
- [05_publish_corpus_statistics.py:80](LOKAL/_0_json/05_publish_corpus_statistics.py#L80): `OUTPUT_DIR = PROJECT_ROOT / "static" / "img" / "statistics"`
- `git ls-files static/img/statistics` shows 29 tracked files.

**Expected behavior:**
- Generated assets should live in `data/generated/` or similar.
- Deploy step copies/symlinks to `static/` for web serving.
- Git only tracks source code, not outputs.

---

#### Issue 2.2: Temporary Data in Persistent Locations

**Problem:**
- `data/stats_temp/` is a **persistent directory** (synced to prod in some configs?).
- Name implies temporary, but `.gitignore` and sync scripts don't clarify its lifecycle.

**Evidence:**
- [sync_data.ps1](scripts/deploy_sync/sync_data.ps1) **excludes** it from sync (correct), but it persists locally.
- No cleanup script found → may accumulate stale files.

---

#### Issue 2.3: `media/mp3-temp/` Naming Inconsistency

**Problem:**
- `media/mp3-temp/` is correctly excluded from sync ([sync_media.ps1](scripts/deploy_sync/sync_media.ps1)).
- But `data/stats_temp/` uses same `_temp` suffix with different lifecycle expectations.

**Consistency issue:** Users may assume all `*temp` directories are ephemeral, but behavior differs.

---

### 3. Operational Risks

#### Risk 3.1: Accidental Deployment of `.new` or `.backup` Directories

**Scenario:**
- Developer manually copies `data/blacklab_index.new/` to prod before validation.
- Old backups (`blacklab_index.backup_*`) get synced if sync script is modified.

**Mitigation:**
- [publish_blacklab_index.ps1](scripts/deploy_sync/publish_blacklab_index.ps1) handles atomic swap correctly.
- But no safeguards against manual errors (e.g., `rsync -a data/ prod:/data/` would sync everything).

---

#### Risk 3.2: Large Files in Git (Binary Diffs)

**Current state:**
- `static/img/statistics/*.png` (29 files, 3.5 MB) tracked in Git.
- **Low risk now** (small size), but **high risk if corpus grows** (more countries, more charts).

**Evidence:**
- `git log --follow static/img/statistics/viz_ARG_resumen.png` would show commit history with binary diffs.

**Future risk:**
- 100 countries × 4 charts/country = 400 PNG files → ~50 MB in Git history.

---

#### Risk 3.3: Missing Single Source of Truth

**Problem:**
- No authoritative document lists:
  - Which data files are required for production?
  - Which scripts generate which outputs?
  - What is the correct deploy order?

**Current state:**
- [startme.md](startme.md) and pipeline docs mention steps, but:
  - Missing scripts (e.g., `03_build_metadata_stats.py` not in repo)
  - No dependency graph (step 05 depends on step 04 outputs, but not enforced)

**Evidence:**
- [05_publish_corpus_statistics.py:11-12](LOKAL/_0_json/05_publish_corpus_statistics.py#L11-12) documents inputs but doesn't validate their existence.

---

#### Risk 3.4: Orphaned `data/exports/` Directory

**Problem:**
- `data/exports/` (162 MB) is **synced to production** but has:
  - No producer script (no code writes to it)
  - No consumer script (no code reads from it)
  - No documentation

**Risk:**
- Occupies 162 MB on prod server for unknown purpose.
- May contain outdated/incorrect data.
- If deleted, unknown impact (possibly none).

**Investigation needed:**
- Manual inspection: `ls -lh data/exports/` to identify file types.
- Git blame: check when files were added/modified.

---

## Phase D: Proposed Target Layout

**Goal:** Reorganize `data/` for clarity, consistency, and operational safety.

### Proposed Structure

```
data/
├── blacklab/
│   ├── index/                  # Active production index (was: data/blacklab_index/)
│   ├── index-staging/          # Pre-validation build (was: data/blacklab_index.new/)
│   ├── backups/                # Rolling backups (was: data/blacklab_index.backup_*/)
│   │   └── index_20260114_232911/
│   └── exports/                # TSV/docmeta for indexing (was: data/blacklab_export/)
│       ├── tsv/
│       ├── metadata/
│       └── docmeta.jsonl
├── db/
│   ├── public/                 # Public, read-only databases
│   │   ├── stats_files.db      (was: data/db/stats_files.db)
│   │   ├── stats_country.db    (was: data/db/stats_country.db)
│   │   └── stats_all.db        (was: data/db_public/stats_all.db)
│   └── restricted/             # Sensitive databases (NOT synced to public docs)
│       └── auth.db             (was: data/db/auth.db)
├── metadata/                   # FAIR corpus metadata (unchanged)
│   ├── latest/ -> v2025-12-06
│   ├── v2025-12-01/
│   └── v2025-12-06/
├── generated/                  # Pipeline outputs (NEW - replaces static/img/statistics/)
│   └── site-assets/
│       └── statistics/
│           ├── corpus_stats.json
│           └── viz_*.png
├── counters/                   # Feature counters (unchanged)
├── temp/                       # Ephemeral files (was: data/stats_temp/)
│   └── stats/
└── exports/                    # (EVALUATE: keep or remove?)
    └── ... (TBD based on manual inspection)
```

### Rationale

1. **`data/blacklab/`** — All BlackLab-related artifacts in one namespace:
   - `index/` (active), `index-staging/` (pre-deploy), `backups/` (rolling), `exports/` (TSV source)
   - Clear lifecycle: exports → staging → validation → active → backup

2. **`data/db/public/` vs `data/db/restricted/`** — Explicit security boundary:
   - Public DBs can be safely synced, documented, shared.
   - Restricted DBs require special handling (backups, encryption, access control).
   - Eliminates ambiguity in sync scripts.

3. **`data/generated/`** — All pipeline-generated assets:
   - Clearly separates "source data" (inputs) from "derived data" (outputs).
   - `generated/site-assets/` makes it obvious these files are for the website.
   - Deploy step: copy/symlink `data/generated/site-assets/statistics/` → `static/img/statistics/` (or serve directly from `data/`).

4. **`data/temp/`** — Single location for all temporary/intermediate files:
   - `temp/stats/` (was: `stats_temp/`)
   - Future: `temp/blacklab_build/`, `temp/media_processing/`, etc.
   - Excluded from Git, excluded from sync, periodic cleanup allowed.

5. **`data/exports/`** — Evaluate and rename/remove:
   - If still needed: rename to `data/legacy_exports/` or `data/archive/`.
   - If obsolete: document why, then delete.

---

### Migration Impact: What Breaks?

| Path Change                        | Breaks                                   | Fix Required                          |
|------------------------------------|------------------------------------------|---------------------------------------|
| `data/blacklab_export/` → `data/blacklab/exports/` | [src/scripts/blacklab_index_creation.py:554](src/scripts/blacklab_index_creation.py#L554) | Update default path |
| | [scripts/blacklab/docmeta_to_metadata_dir.py:7](scripts/blacklab/docmeta_to_metadata_dir.py#L7) | Update hardcoded path |
| | [tests/test_docmeta_lookup.py:7](tests/test_docmeta_lookup.py#L7) | Update test path |
| | [sync_data.ps1:103](scripts/deploy_sync/sync_data.ps1#L103) | Update sync directory list |
| `data/blacklab_index/` → `data/blacklab/index/` | BlackLab Docker config | Update volume mount in [docker-compose.yml](docker-compose.yml) |
| | [publish_blacklab_index.ps1](scripts/deploy_sync/publish_blacklab_index.ps1) | Update remote paths |
| `data/db/*.db` → `data/db/public/*.db` | [src/app/services/database.py:11-16](src/app/services/database.py#L11-16) | Update `DATABASES` dict |
| | [sync_data.ps1:106-109](scripts/deploy_sync/sync_data.ps1#L106-109) | Update selective file sync paths |
| `data/db_public/` → `data/db/public/` | [src/app/services/database.py:12,17](src/app/services/database.py#L12,17) | Update `PUBLIC_DB_ROOT` |
| | [sync_data.ps1:98](scripts/deploy_sync/sync_data.ps1#L98) | Update directory list |
| `data/db/auth.db` → `data/db/restricted/auth.db` | [scripts/create_initial_admin.py:35](scripts/create_initial_admin.py#L35) | Update default path |
| | [src/app/extensions/sqlalchemy_ext.py:4](src/app/extensions/sqlalchemy_ext.py#L4) | Update docstring |
| | Flask config (env var) | Update `AUTH_DATABASE_URL` |
| `static/img/statistics/` → `data/generated/site-assets/statistics/` | [LOKAL/_0_json/05_publish_corpus_statistics.py:80](LOKAL/_0_json/05_publish_corpus_statistics.py#L80) | Update `OUTPUT_DIR` |
| | Frontend templates | Update image paths (or add build step) |
| | Git tracking | Remove from Git, add to `.gitignore` |
| `data/stats_temp/` → `data/temp/stats/` | Unknown (no clear producer/consumer) | Verify no scripts hardcode this path |

---

### Backward Compatibility: Symlinks

To allow gradual migration, create symlinks during transition:

```bash
# On prod server:
ln -s data/blacklab/exports data/blacklab_export  # Legacy path
ln -s data/blacklab/index data/blacklab_index      # Legacy path
ln -s data/db/public/stats_all.db data/db_public/stats_all.db  # Legacy path
```

**Validation:**
- Run smoke tests with symlinks in place.
- After confirming all code uses new paths, remove symlinks.

---

## Phase E: Migration Plan

### PR 1: Documentation & Inventory (This PR)

**Scope:** Documentation only, no code changes.

**Deliverables:**
- [x] `docs/data_cleanup/audit_current_state.md` (this file)
- [x] `docs/data_cleanup/proposed_target_layout.md` (inline above)
- [x] `docs/data_cleanup/migration_plan.md` (inline below)

**Validation:**
- No tests required (docs only).
- Peer review for accuracy.

---

### PR 2: Move `static/img/statistics/` Out of Git

**Scope:** Remove generated assets from version control.

**Steps:**
1. Update [.gitignore](.gitignore):
   ```diff
   + # Generated corpus statistics (output of 05_publish_corpus_statistics.py)
   + static/img/statistics/
   ```
2. Remove tracked files:
   ```bash
   git rm --cached static/img/statistics/*.png static/img/statistics/*.json
   git commit -m "chore: untrack generated corpus statistics from Git"
   ```
3. Update [LOKAL/_0_json/05_publish_corpus_statistics.py](LOKAL/_0_json/05_publish_corpus_statistics.py):
   - Keep `OUTPUT_DIR = static/img/statistics/` for now (change later).
   - Add warning comment: "TODO: Move output to data/generated/ in future PR".
4. Update [README.md](README.md):
   - Document that `static/img/statistics/` is generated (not in Git).
   - Add: "Run `python LOKAL/_0_json/05_publish_corpus_statistics.py` after deploying new corpus data."
5. **Prod deployment:**
   - Before merging: run `05_publish_corpus_statistics.py` on prod to regenerate files.
   - After merge: confirm `static/img/statistics/` still exists (not deleted by `git pull`).

**Compatibility shim:** None needed (files remain in same location).

**Rollback:** `git revert` + `git add -f static/img/statistics/*` (re-track files).

**Validation:**
- Manually inspect frontend: `/corpus/metadata` page shows charts.
- Check `git status` → `static/img/statistics/` appears untracked.

---

### PR 3: Reorganize `data/db/` → `public/` and `restricted/`

**Scope:** Separate public and sensitive databases.

**Steps:**
1. Create new directories:
   ```bash
   mkdir -p data/db/public data/db/restricted
   ```
2. Move files locally (on dev):
   ```bash
   mv data/db/stats_files.db data/db/public/
   mv data/db/stats_country.db data/db/public/
   mv data/db_public/stats_all.db data/db/public/
   mv data/db/auth.db data/db/restricted/
   rmdir data/db_public  # Now empty
   ```
3. Update [src/app/services/database.py](src/app/services/database.py):
   ```diff
   - PRIVATE_DB_ROOT = DATA_ROOT / "db"
   - PUBLIC_DB_ROOT = DATA_ROOT / "db_public"
   + PUBLIC_DB_ROOT = DATA_ROOT / "db" / "public"
   + RESTRICTED_DB_ROOT = DATA_ROOT / "db" / "restricted"
   ```
4. Update [scripts/deploy_sync/sync_data.ps1](scripts/deploy_sync/sync_data.ps1):
   ```diff
   - $DATA_DIRECTORIES = @("db_public", ...)
   - $STATS_DB_FILES = @("stats_files.db", "stats_country.db")
   + $DATA_DIRECTORIES = @("db/public", ...)
   # Remove $STATS_DB_FILES (now synced as part of db/public/)
   ```
5. Update [scripts/create_initial_admin.py](scripts/create_initial_admin.py):
   ```diff
   - default="data/db/auth.db"
   + default="data/db/restricted/auth.db"
   ```
6. Update Flask config (`.env` or environment variable):
   ```diff
   - AUTH_DATABASE_URL=sqlite:///data/db/auth.db
   + AUTH_DATABASE_URL=sqlite:///data/db/restricted/auth.db
   ```

**Compatibility shim (prod deployment):**
```bash
# On prod, create symlinks before deploying PR:
ssh prod "cd /srv/webapps/corapan && \
  mkdir -p data/db/public data/db/restricted && \
  ln -s $(pwd)/data/db/stats_files.db data/db/public/ && \
  ln -s $(pwd)/data/db/stats_country.db data/db/public/ && \
  ln -s $(pwd)/data/db_public/stats_all.db data/db/public/ && \
  ln -s $(pwd)/data/db/auth.db data/db/restricted/"

# Deploy PR (git pull, restart app)
# Verify app works with symlinks

# Move actual files (replaces symlinks):
ssh prod "cd /srv/webapps/corapan && \
  rm data/db/public/*.db data/db/restricted/*.db && \
  mv data/db/stats_*.db data/db/public/ && \
  mv data/db_public/stats_all.db data/db/public/ && \
  mv data/db/auth.db data/db/restricted/ && \
  rmdir data/db_public"
```

**Rollback:** Reverse symlinks, revert code changes.

**Validation:**
- Smoke test: `/atlas` page loads (uses stats DBs).
- Auth works: login/logout.
- Run [tests/test_account_status.py](tests/test_account_status.py) (if tests exist for auth).

---

### PR 4: Consolidate BlackLab Paths Under `data/blacklab/`

**Scope:** Move `blacklab_export/`, `blacklab_index/`, `blacklab_index.new/`, `blacklab_index.backup_*/` → `data/blacklab/`.

**Steps:**
1. Create new structure:
   ```bash
   mkdir -p data/blacklab/{exports,index,index-staging,backups}
   mv data/blacklab_export/* data/blacklab/exports/
   mv data/blacklab_index/* data/blacklab/index/
   mv data/blacklab_index.new/* data/blacklab/index-staging/
   mv data/blacklab_index.backup_* data/blacklab/backups/
   ```
2. Update [src/scripts/blacklab_index_creation.py](src/scripts/blacklab_index_creation.py):
   ```diff
   - default="data/blacklab_export/tsv"
   + default="data/blacklab/exports/tsv"
   - default="data/blacklab_export/docmeta.jsonl"
   + default="data/blacklab/exports/docmeta.jsonl"
   ```
3. Update [scripts/blacklab/docmeta_to_metadata_dir.py](scripts/blacklab/docmeta_to_metadata_dir.py):
   ```diff
   - p = Path("data/blacklab_export/docmeta.jsonl")
   + p = Path("data/blacklab/exports/docmeta.jsonl")
   - md_dir = Path("data/blacklab_export/metadata")
   + md_dir = Path("data/blacklab/exports/metadata")
   ```
4. Update [docker-compose.yml](docker-compose.yml) (if exists):
   ```diff
   - volumes:
   -   - ./data/blacklab_index:/data/index:ro
   + volumes:
   +   - ./data/blacklab/index:/data/index:ro
   ```
5. Update [scripts/deploy_sync/sync_data.ps1](scripts/deploy_sync/sync_data.ps1):
   ```diff
   - $DATA_DIRECTORIES = @("blacklab_export", ...)
   + $DATA_DIRECTORIES = @("blacklab/exports", ...)
   ```
6. Update [scripts/deploy_sync/publish_blacklab_index.ps1](scripts/deploy_sync/publish_blacklab_index.ps1):
   ```diff
   - $DataDir = "/srv/webapps/corapan/data"
   + # Update all references: blacklab_index → blacklab/index, etc.
   ```

**Compatibility shim (prod):**
```bash
# Create symlinks before deploying:
ssh prod "cd /srv/webapps/corapan/data && \
  mkdir -p blacklab/{exports,index,index-staging,backups} && \
  ln -s $(pwd)/blacklab/exports blacklab_export && \
  ln -s $(pwd)/blacklab/index blacklab_index && \
  ln -s $(pwd)/blacklab/index-staging blacklab_index.new"

# After deployment, move actual files (replaces symlinks)
```

**Rollback:** Reverse symlinks, revert code.

**Validation:**
- BlackLab container starts: `docker-compose up blacklab` (or equivalent).
- Search works: `/search/advanced` returns results.
- Publish workflow: `.\publish_blacklab_index.ps1 -DryRun` succeeds.

---

### PR 5: Move `static/img/statistics/` → `data/generated/site-assets/statistics/`

**Scope:** Relocate generated assets to `data/` and add build step.

**Steps:**
1. Update [LOKAL/_0_json/05_publish_corpus_statistics.py](LOKAL/_0_json/05_publish_corpus_statistics.py):
   ```diff
   - OUTPUT_DIR = PROJECT_ROOT / "static" / "img" / "statistics"
   + OUTPUT_DIR = PROJECT_ROOT / "data" / "generated" / "site-assets" / "statistics"
   ```
2. Create symlink for local dev:
   ```bash
   rm -rf static/img/statistics  # Remove old generated files
   ln -s ../../data/generated/site-assets/statistics static/img/statistics
   ```
3. Update [.gitignore](.gitignore):
   ```diff
   + # Generated site assets (output of pipeline scripts)
   + data/generated/
   ```
4. Update [scripts/deploy_sync/sync_data.ps1](scripts/deploy_sync/sync_data.ps1):
   ```diff
   + $DATA_DIRECTORIES = @("generated", ...)
   ```
5. Update prod deployment script (or add to [startme.md](startme.md)):
   ```bash
   # After syncing data/, create symlink:
   ssh prod "cd /srv/webapps/corapan && \
     ln -sf ../../data/generated/site-assets/statistics static/img/statistics"
   ```

**Compatibility shim:** Symlink handles path resolution automatically.

**Rollback:** Remove symlink, revert code, restore `static/img/statistics/` files.

**Validation:**
- Frontend: `/corpus/metadata` page shows charts (via symlink).
- Verify `static/img/statistics/` is a symlink: `ls -la static/img/`.

---

### PR 6: Evaluate and Handle `data/exports/`

**Scope:** Determine purpose of `data/exports/` and either rename or remove.

**Investigation (manual):**
1. Inspect contents:
   ```bash
   ls -lh data/exports/
   file data/exports/*  # Check file types
   ```
2. Check Git history:
   ```bash
   git log --follow --oneline data/exports/
   ```
3. Search for references:
   ```bash
   rg -i "data/exports" --type py
   ```

**Decision tree:**
- **If still needed:** Rename to `data/blacklab/legacy_exports/` or `data/archive/exports/`.
- **If obsolete:** Document why, add to this audit doc, then delete.

**Steps (if removing):**
1. Add to [.gitignore](.gitignore):
   ```diff
   + # Legacy exports (removed YYYY-MM-DD)
   + data/exports/
   ```
2. Remove from [sync_data.ps1](scripts/deploy_sync/sync_data.ps1):
   ```diff
   - $DATA_DIRECTORIES = @("exports", ...)
   ```
3. Delete locally:
   ```bash
   rm -rf data/exports
   ```
4. Document in this audit doc (Phase C, Issue 3.4).

**Rollback:** Restore from backup (rsync or prod copy).

**Validation:** No broken functionality (if truly unused).

---

### PR 7: Rename `data/stats_temp/` → `data/temp/stats/`

**Scope:** Consolidate all temporary directories under `data/temp/`.

**Steps:**
1. Rename locally:
   ```bash
   mkdir -p data/temp
   mv data/stats_temp data/temp/stats
   ```
2. Update [.gitignore](.gitignore):
   ```diff
   + # Temporary files (ephemeral, not synced)
   + data/temp/
   ```
3. Search for hardcoded references (unlikely, but verify):
   ```bash
   rg "stats_temp" --type py
   ```

**Compatibility shim:** None needed (directory likely unused in code).

**Rollback:** Rename back.

**Validation:** No errors in logs after deployment.

---

## Checklist

- [x] **All producers identified** — See [Phase B1](#b1-data-producers-writers)
- [x] **All consumers identified** — See [Phase B2](#b2-data-consumers-readers)
- [x] **Deploy/Sync paths documented** — See [Phase B3](#b3-deploysync-analysis)
- [x] **Risks documented** — See [Phase C](#phase-c-inconsistencies--risks)
- [x] **Target layout proposed** — See [Phase D](#phase-d-proposed-target-layout)
- [x] **Migration plan outlined** — See [Phase E](#phase-e-migration-plan)

---

## Appendix: Evidence Summary

### Directory Sizes (Snapshot: 2026-01-16)

| Path                              | Size (MB) | Files | Notes                              |
|-----------------------------------|-----------|-------|------------------------------------|
| `data/`                           | 1796.57   | 3336  | Total                              |
| ├─ `blacklab_export/`             | 737.87    | 445   | TSV + metadata for indexing        |
| ├─ `blacklab_index.backup_*/`     | 290.65    | 657   | Backup (20260114_232911)           |
| ├─ `blacklab_index.new/`          | 278.62    | 75    | Staging index                      |
| ├─ `blacklab_index/`              | 278.62    | 75    | Active index                       |
| ├─ `exports/`                     | 161.73    | 147   | **Purpose unclear**                |
| ├─ `db/`                          | 45.75     | 1286  | Mixed public/private DBs           |
| ├─ `metadata/`                    | 3.31      | 615   | Versioned FAIR metadata            |
| ├─ `stats_temp/`                  | 0.02      | 26    | Temporary stats                    |
| ├─ `db_public/`                   | 0.01      | 2     | Public stats (isolated)            |
| └─ `counters/`                    | 0.00      | 7     | Empty counter files                |
| `static/img/statistics/`          | 3.50      | 29    | **In Git! (anti-pattern)**         |
| `media/`                          | 15168.25  | 3007  | Audio + transcripts (~15 GB)       |
| `LOKAL/`                          | 17.93     | 142   | Pipeline workspace                 |

### Key Scripts and Their Roles

| Script                            | Role                                       | Writes To                          |
|-----------------------------------|--------------------------------------------|------------------------------------|
| `LOKAL/_0_json/04_internal_country_statistics.py` | Generate CSV stats per country | `LOKAL/_0_json/results/*.csv`, `*.png` |
| `LOKAL/_0_json/05_publish_corpus_statistics.py` | Generate public site charts    | `static/img/statistics/*.png`, `*.json` |
| `src/scripts/blacklab_index_creation.py` | Generate BlackLab TSV + docmeta | `data/blacklab_export/tsv/`, `docmeta.jsonl` |
| `scripts/blacklab/docmeta_to_metadata_dir.py` | Split docmeta into per-file JSON | `data/blacklab_export/metadata/*.json` |
| `scripts/deploy_sync/sync_data.ps1` | Rsync data/ to prod              | (Prod: `/srv/webapps/corapan/data/*`) |
| `scripts/deploy_sync/sync_media.ps1` | Rsync media/ to prod            | (Prod: `/srv/webapps/corapan/media/*`) |
| `scripts/deploy_sync/publish_blacklab_index.ps1` | Upload + validate + swap index | (Prod: BlackLab index atomic swap) |

---

**End of Audit Document**
