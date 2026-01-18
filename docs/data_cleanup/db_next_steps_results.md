# Data Cleanup: Next Steps Results (Consolidated)

This document has been consolidated to reflect the current state after the public DB and metadata path updates.

## Summary

## Current Actions
# Database Next Steps: Results & Decisions

**Date:** 2026-01-16  
**Purpose:** Document findings from Phase 0-4 investigations and provide actionable decisions  
**Status:** ✅ Complete — All investigations finished, ready for implementation

---

## Executive Summary

This document presents **hard evidence** from systematic investigation of:
1. ✅ **Producer scripts** — Found in LOKAL/, can be moved to production path
2. ✅ **Frontend API usage** — Mapped all Atlas/stats consumers
3. ✅ **`stats_all.db` usage** — **PROVEN OBSOLETE** (dead endpoint, replaced by JSON)
4. ✅ **Dev Postgres migration** — Safe to make default (SQLite code can be removed)

**Key Decisions:**
- **Remove `stats_all.db`** — Unused, replaced by `corpus_stats.json`
- **Keep `stats_files.db` + `stats_country.db`** — Active consumers (Atlas, Editor)
- **Move producer to `scripts/`** — Make stats DB generation reproducible
- **Migrate dev to Postgres-only** — Remove SQLite auth fallback

---

## Table of Contents

- [Phase 0: Producer Scripts Found](#phase-0-producer-scripts-found)
- [Phase 1: Dev Postgres Migration Plan](#phase-1-dev-postgres-migration-plan)
- [Phase 2: Producer Integration Plan](#phase-2-producer-integration-plan)
- [Phase 3: Consumer Matrix (Complete Evidence)](#phase-3-consumer-matrix-complete-evidence)
- [Phase 4: stats_all.db — PROVEN OBSOLETE](#phase-4-stats_alldb--proven-obsolete)
- [Phase 5: Implementation Roadmap](#phase-5-implementation-roadmap)

---

## Phase 0: Producer Scripts Found

### 0.1 Discovery

**Script Location:** [LOKAL/_0_json/03_build_metadata_stats.py](../../LOKAL/_0_json/03_build_metadata_stats.py)

**Evidence from LOKAL/README.md:**

> | 03 | `03_build_metadata_stats.py` | Erzeugt Metadaten DBs (data/db_public/stats_all.db, data/db/stats_country.db, data/db/stats_files.db)

**Script Header (Lines 1-32):**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
03_build_metadata_stats.py

Erstellt Metadaten-Datenbanken aus annotierten JSON-Transkripten.

EINGABEPFAD:  media/transcripts/<country>/*.json

AUSGABEDATEIEN:
    data/db_public/stats_all.db     - Globale Statistiken
    data/db/stats_country.db        - Statistiken pro Land
    data/db/stats_files.db          - Metadaten pro Datei

HINWEIS:
    transcription.db wird NICHT mehr erstellt.
    Die Token-Suche erfolgt über BlackLab direkt aus den JSONs.

VERWENDUNG:
    python 03_build_metadata_stats.py
    python 03_build_metadata_stats.py --rebuild
    python 03_build_metadata_stats.py --country ARG
    python 03_build_metadata_stats.py --verify-only
```

**Proof:** Script exists, is documented, and writes to exact paths expected by runtime code.

---

### 0.2 Git Repository Context

**Question:** Is LOKAL/ a separate Git repository?

**Evidence:**

```bash
$ git remote -v
origin  https://github.com/FTacke/corapan-webapp (fetch)
origin  https://github.com/FTacke/corapan-webapp (push)

$ ls -la LOKAL/.git
# Result: No .git directory found
```

**Conclusion:** LOKAL/ is **part of the main repo** (subdirectory, not submodule).

**Implication:** Producer script can be **moved to `scripts/`** without cross-repo complexity.

---

## Phase 1: Dev Postgres Migration Plan

### 1.1 Current State: Dual SQLite/Postgres Support

**Default Dev Config:** [.env.example:48](../../.env.example#L48)

```bash
# Which DB to use for auth (SQLAlchemy URL). Defaults to sqlite data/db/auth.db
AUTH_DATABASE_URL=sqlite:///data/db/auth.db
```

**SQLite Fallback in Code:** [src/app/config/__init__.py:89-91](../../src/app/config/__init__.py#L89-L91)

```python
AUTH_DATABASE_URL = os.getenv(
    "AUTH_DATABASE_URL",
    f"sqlite:///{(Path(PROJECT_ROOT) / 'data' / 'db' / 'auth.db').as_posix()}",
)
```

**Postgres Dev Compose:** [docker-compose.dev-postgres.yml](../../docker-compose.dev-postgres.yml)

**Status:** Postgres is **optional** (requires explicit docker-compose invocation).

---

### 1.2 Migration Goal: Postgres-Only Dev

**Objective:** Make Postgres the **mandatory** dev database (remove SQLite fallback).

**Rationale:**
1. **Prod uses Postgres** — dev should match prod environment
2. **Fewer code paths** — eliminates SQLite-specific bugs
3. **Better testing** — catches Postgres-specific issues early
4. **Simpler onboarding** — one DB setup, not two

**Breaking Changes:**
- Devs **must** run `docker-compose.dev-postgres.yml` (or set `AUTH_DATABASE_URL` manually)
- Scripts referencing `auth.db` must be updated (see [1.3](#13-required-code-changes))

---

### 1.3 Required Code Changes

| File | Change | Reason |
|------|--------|--------|
| [.env.example:48](../../.env.example#L48) | Change default to `postgresql+psycopg2://corapan_auth:corapan_auth@localhost:54320/corapan_auth` | Postgres-first |
| [src/app/config/__init__.py:89-91](../../src/app/config/__init__.py#L89-L91) | Remove fallback, require `AUTH_DATABASE_URL` env var | Fail-fast if not set |
| [README.md](../../README.md) (dev setup) | Document mandatory Postgres setup | Onboarding |
| [scripts/create_initial_admin.py:34](../../scripts/create_initial_admin.py#L34) | Remove default `data/db/auth.db` path | Force explicit config |
| [scripts/apply_auth_migration.py:25](../../scripts/apply_auth_migration.py#L25) | Remove default path | Force explicit config |

**Testing:**
- Dev start without Postgres → **should fail with clear error**
- Dev start with Postgres → auth works (login/register)
- Tests still pass (use in-memory SQLite for unit tests)

---

### 1.4 Git Ignore Updates

**Add to `.gitignore`:**

```gitignore
# Auth databases (dev artifacts, never commit)
data/db/auth.db
data/db/auth_e2e.db
data/db/postgres_dev/
```

**Proof these files exist locally:**

```bash
$ ls -lh data/db/*.db
-rw-r--r-- 1 user user  45M Jan 14 23:29 auth.db
-rw-r--r-- 1 user user  12K Jan 10 14:22 auth_e2e.db
```

---

## Phase 2: Producer Integration Plan

### 2.1 Current Location vs Target

| Property | Value |
|----------|-------|
| **Current Path** | `LOKAL/_0_json/03_build_metadata_stats.py` |
| **Target Path** | `scripts/stats_db/build_metadata_stats.py` |
| **Output Paths** | Unchanged (write to existing `data/db/*.db` locations) |

**Rationale for `scripts/stats_db/` namespace:**
- Groups stats-related utilities (future: rebuild, verify, schema docs)
- Keeps LOKAL/ for exploratory/research scripts
- Makes stats DB generation "first-class" (not hidden in LOKAL/)

---

### 2.2 Migration Steps

1. **Copy script to new location:**
   ```bash
   mkdir -p scripts/stats_db
   cp LOKAL/_0_json/03_build_metadata_stats.py scripts/stats_db/build_metadata_stats.py
   ```

2. **Add README in `scripts/stats_db/`:**
   - Document inputs (annotated JSONs from `media/transcripts/`)
   - Document outputs (3 SQLite DBs)
   - Document usage (CLI flags)
   - Link to schema (see [2.3](#23-schema-documentation))

3. **Update deployment docs:**
   - [startme.md](../../startme.md) — mention stats DB regeneration step
   - [CONTRIBUTING.md](../../CONTRIBUTING.md) — data pipeline overview

4. **Test regeneration:**
   ```bash
   python scripts/stats_db/build_metadata_stats.py --rebuild
   # Verify: ls -lh data/db/stats_*.db data/db_public/stats_all.db
   ```

5. **Keep original in LOKAL/** (for now):
   - Add deprecation notice in LOKAL/README.md
   - Point to new canonical location
   - Remove after next release (when new path is proven)

---

### 2.3 Schema Documentation

**Create:** `scripts/stats_db/SCHEMA.md`

**Content (extract from script lines 217-697):**

#### `data/db_public/stats_all.db`

**Table:** `stats`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Always 1 (single-row table) |
| `total_word_count` | INTEGER | Total words across all transcripts |
| `total_duration_all` | TEXT | Total duration as HH:MM:SS |

**Example:**
```sql
SELECT * FROM stats;
-- id | total_word_count | total_duration_all
-- 1  | 1234567          | 123:45:67
```

#### `data/db/stats_country.db`

**Table:** `stats_country`

| Column | Type | Description |
|--------|------|-------------|
| `country_code` | TEXT PRIMARY KEY | 3-letter code (ARG, ESP, MEX) |
| `total_word_count` | INTEGER | Words for this country |
| `total_duration_country` | TEXT | Duration as HH:MM:SS |

#### `data/db/stats_files.db`

**Table:** `metadata`

| Column | Type | Description |
|--------|------|-------------|
| `filename` | TEXT PRIMARY KEY | e.g., `2023-08-10_ARG_Mitre.json` |
| `country_code` | TEXT | 3-letter code |
| `radio` | TEXT | Station name |
| `date` | TEXT | Recording date (YYYY-MM-DD) |
| `revision` | TEXT | Version (v1, v2, v3) |
| `word_count` | INTEGER | Words in this file |
| `duration` | TEXT | File duration (HH:MM:SS.ss) |

---

## Phase 3: Consumer Matrix (Complete Evidence)

### 3.1 Active Consumers (KEEP)

#### 3.1.1 Atlas Feature (Map + API)

**Frontend:** [static/js/modules/atlas/index.js](../../static/js/modules/atlas/index.js)

**API Calls:**
```javascript
// Line 515
fetch("/api/v1/atlas/countries")  // → stats_country.db

// Line 535
fetch("/api/v1/atlas/files")  // → stats_files.db
```

**Backend:** [src/app/routes/atlas.py](../../src/app/routes/atlas.py)

**Endpoints:**
- `/api/v1/atlas/countries` → [atlas.py:27-30](../../src/app/routes/atlas.py#L27-L30)
- `/api/v1/atlas/files` → [atlas.py:33-36](../../src/app/routes/atlas.py#L33-L36)

**Service Layer:** [src/app/services/atlas.py](../../src/app/services/atlas.py)

**DB Reads:**
```python
# Line 21-43: fetch_country_stats()
with open_db("stats_country") as connection:
    rows = cursor.execute("SELECT country_code, total_word_count, total_duration_country FROM stats_country ...")

# Line 46-65: fetch_file_metadata()
with open_db("stats_files") as connection:
    rows = cursor.execute("SELECT filename, country_code, radio, date, revision, word_count, duration FROM metadata ...")
```

**Evidence:** Atlas page (`/atlas`) loads Leaflet map, fetches country + file stats, displays markers.

**Status:** ✅ **ACTIVE** — Atlas feature in production use.

---

#### 3.1.2 Editor File Info

**Backend:** [src/app/routes/editor.py:501-517](../../src/app/routes/editor.py#L501-L517)

```python
def _get_file_info(country: str, filename: str) -> dict:
    """Sammelt alle Metadaten für ein Transcript-File."""
    # Hole Duración und Palabras aus stats_files.db
    try:
        with open_db("stats_files") as conn:
            cursor = conn.execute(
                "SELECT duration, word_count FROM metadata WHERE filename = ? AND country_code = ?",
                (filename, country),
            )
            row = cursor.fetchone()
            if row:
                duration = row["duration"] or "N/A"
                word_count = row["word_count"] or 0
    except Exception as e:
        current_app.logger.error(f"[Editor] Error loading stats for {filename}: {e}")
```

**Purpose:** Editor UI displays file duration + word count in metadata panel.

**Status:** ✅ **ACTIVE** — Editor feature in production use.

---

#### 3.1.3 Player Overview (File Metadata)

**Frontend:** [static/js/modules/player-overview.js:411](../../static/js/modules/player-overview.js#L411)

```javascript
const response = await fetch("/api/v1/atlas/files", { /* ... */ });
```

**Backend:** Same as Atlas (`/api/v1/atlas/files` → `stats_files.db`)

**Purpose:** Player overview page lists all available recordings with metadata.

**Status:** ✅ **ACTIVE** — Player feature in production use.

---

#### 3.1.4 Corpus Metadata Page (File Metadata)

**Frontend:** [static/js/modules/corpus-metadata.js:673](../../static/js/modules/corpus-metadata.js#L673)

```javascript
const response = await fetch("/api/v1/atlas/files", { /* ... */ });
```

**Backend:** Same as Atlas (`/api/v1/atlas/files` → `stats_files.db`)

**Purpose:** Corpus metadata page displays downloadable file list with stats.

**Status:** ✅ **ACTIVE** — Corpus metadata feature in production use.

---

### 3.2 Obsolete Consumers (REMOVE)

#### 3.2.1 Legacy Player Footer (stats_all.db)

**Code:** [static/js/player_script.js:961](../../static/js/player_script.js#L961)

```javascript
function loadFooterStats() {
    // ...
    fetch("/get_stats_all_from_db")
      .then((response) => response.json())
      .then((data) => {
        updateTotalStats(data.total_word_count, data.total_duration_all);
      })
```

**Backend:** [src/app/routes/public.py:343-351](../../src/app/routes/public.py#L343-L351)

```python
@blueprint.get("/get_stats_all_from_db")
def get_stats_all_from_db():
    from ..services.atlas import fetch_overview
    response = jsonify(fetch_overview())
    return response
```

**Evidence of OBSOLESCENCE:**

1. **No templates reference this code:**
   ```bash
   $ rg "loadFooterStats|totalWordCount|totalDuration" templates/
   # Result: NO MATCHES
   ```

2. **Newer player module uses different endpoint:**
   [static/js/player/modules/ui.js:122](../../static/js/player/modules/ui.js#L122)
   ```javascript
   const response = await fetch("/api/corpus_stats");
   ```
   **Note:** This endpoint **DOES NOT EXIST** in backend routes (404).

3. **New approach uses static JSON:**
   [static/img/statistics/corpus_stats.json](../../static/img/statistics/corpus_stats.json) exists (generated by `05_publish_corpus_statistics.py`).

**Conclusion:** `player_script.js` is **legacy code** (likely replaced by modular player in `static/js/player/`).

**Status:** ⚠️ **DEAD CODE** — endpoint exists but no active consumers.

---

#### 3.2.2 Atlas Overview Endpoint (stats_all.db)

**Backend:** [src/app/routes/atlas.py:17-20](../../src/app/routes/atlas.py#L17-L20)

```python
@blueprint.get("/overview")
@cache.cached(timeout=3600)
def overview():
    """Get corpus overview statistics (cached for 1 hour)."""
    return jsonify(fetch_overview())
```

**Frontend Usage Search:**

```bash
$ rg "/api/v1/atlas/overview" static/
# Result: NO MATCHES

$ rg "atlas.*overview|fetch.*overview" static/js/
# Result: Only comments, no actual calls
```

**Evidence:** Endpoint exists, but **no frontend code calls it**.

**Status:** ⚠️ **DEAD CODE** — API route exists but unused.

---

### 3.3 Consumer Matrix Summary

| Consumer | Database | Endpoint/Module | Status | Safe to Remove DB? |
|----------|----------|-----------------|--------|--------------------|
| **Atlas Map** | `stats_country.db` | `/api/v1/atlas/countries` | ✅ Active | ❌ NO |
| **Atlas Map** | `stats_files.db` | `/api/v1/atlas/files` | ✅ Active | ❌ NO |
| **Editor File Info** | `stats_files.db` | Internal (`_get_file_info()`) | ✅ Active | ❌ NO |
| **Player Overview** | `stats_files.db` | `/api/v1/atlas/files` | ✅ Active | ❌ NO |
| **Corpus Metadata** | `stats_files.db` | `/api/v1/atlas/files` | ✅ Active | ❌ NO |
| **Legacy Player Footer** | `stats_all.db` | `/get_stats_all_from_db` | ⚠️ Dead | ✅ YES |
| **Atlas Overview** | `stats_all.db` | `/api/v1/atlas/overview` | ⚠️ Dead | ✅ YES |

**Decision:**
- **Keep:** `stats_files.db`, `stats_country.db` (4+ active consumers)
- **Remove:** `stats_all.db` (no active consumers, replaced by static JSON)

---

## Phase 4: stats_all.db — PROVEN OBSOLETE

### 4.1 Final Evidence

**Endpoint exists but unused:**
- `/api/v1/atlas/overview` → returns `stats_all.db` data
- `/get_stats_all_from_db` → legacy endpoint (same data)
- **No frontend code calls either endpoint**

**Replacement exists:**
- [static/img/statistics/corpus_stats.json](../../static/img/statistics/corpus_stats.json)
- Generated by [LOKAL/_0_json/05_publish_corpus_statistics.py](../../LOKAL/_0_json/05_publish_corpus_statistics.py)
- **Format matches** (total_word_count, total_duration, etc.)

**Code that SHOULD use it (but doesn't):**
- [static/js/player/modules/ui.js:122](../../static/js/player/modules/ui.js#L122) fetches `/api/corpus_stats` (404 — endpoint missing)
- **Likely bug:** New player tries to fetch non-existent endpoint

---

### 4.2 Removal Plan

#### Step 1: Remove Backend Code

**Files to Edit:**

1. [src/app/services/atlas.py:7-18](../../src/app/services/atlas.py#L7-L18)
   - Remove `fetch_overview()` function

2. [src/app/routes/atlas.py:17-20](../../src/app/routes/atlas.py#L17-L20)
   - Remove `/overview` endpoint
   - Remove legacy redirect [atlas.py:60](../../src/app/routes/atlas.py#L60)

3. [src/app/routes/public.py:343-351](../../src/app/routes/public.py#L343-L351)
   - Remove `/get_stats_all_from_db` endpoint

4. [src/app/services/database.py:17](../../src/app/services/database.py#L17)
   - Remove `"stats_all": PUBLIC_DB_ROOT / "stats_all.db"` from `DATABASES` dict

**Validation:** Run tests, ensure no import errors.

---

#### Step 2: Remove Database File (Local + Prod)

**Local:**
```bash
rm data/db_public/stats_all.db
```

**Prod (via sync script):**
- Remove from sync list (already not in `sync_data.ps1` — only `stats_files.db` and `stats_country.db` are synced)
- Manual cleanup: `ssh prod "rm /srv/webapps/corapan/data/db_public/stats_all.db"`

---

#### Step 3: Remove from Producer Script

**File:** `scripts/stats_db/build_metadata_stats.py` (after migration from LOKAL/)

**Change:** Remove `build_stats_all()` function and related code.

**Rationale:** No point generating unused DB.

---

#### Step 4: Fix Broken Frontend (Player Footer)

**Problem:** [static/js/player/modules/ui.js:122](../../static/js/player/modules/ui.js#L122) fetches `/api/corpus_stats` (doesn't exist).

**Solution A:** Create endpoint that serves static JSON

**File:** [src/app/routes/corpus.py](../../src/app/routes/corpus.py) (add new endpoint)

```python
@blueprint.get("/api/corpus_stats")
def corpus_stats():
    """Serve pre-generated corpus statistics (static JSON)."""
    stats_file = Path(current_app.static_folder) / "img" / "statistics" / "corpus_stats.json"
    
    if not stats_file.exists():
        return jsonify({"error": "Statistics not available"}), 404
    
    with open(stats_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return jsonify(data)
```

**Solution B:** Update frontend to fetch static file directly

**File:** [static/js/player/modules/ui.js:122](../../static/js/player/modules/ui.js#L122)

```javascript
// OLD:
const response = await fetch("/api/corpus_stats");

// NEW:
const response = await fetch("/static/img/statistics/corpus_stats.json");
```

**Recommendation:** Use **Solution A** (backend serves JSON) — easier to add caching headers, versioning, etc.

---

## Phase 5: Implementation Roadmap

### 5.1 Priority Order

**PR 1: Remove stats_all.db (Low Risk)**
- Remove backend endpoints
- Remove DB from `DATABASES` dict
- Fix player footer (add `/api/corpus_stats` endpoint)
- Delete `stats_all.db` file
- Update producer script (remove `build_stats_all()`)

**Validation:**
- Player footer shows stats (no console errors)
- Atlas page works (map loads)
- No 500 errors in logs

---

**PR 2: Migrate Producer Script (Zero Runtime Risk)**
- Copy `03_build_metadata_stats.py` → `scripts/stats_db/build_metadata_stats.py`
- Add `scripts/stats_db/README.md` + `SCHEMA.md`
- Update docs ([startme.md](../../startme.md), [CONTRIBUTING.md](../../CONTRIBUTING.md))
- Test regeneration: `python scripts/stats_db/build_metadata_stats.py --rebuild`

**Validation:**
- Generated DBs match schema
- Atlas page works (reads new DBs)

---

**PR 3: Dev Postgres Migration (Breaking Change for Devs)**
- Update `.env.example` (Postgres default)
- Remove SQLite fallback in `config/__init__.py`
- Update scripts (`create_initial_admin.py`, `apply_auth_migration.py`)
- Add `auth.db` to `.gitignore`
- Update README (mandatory Postgres setup)

**Validation:**
- Dev start without Postgres → **fails with clear error**
- Dev start with Postgres → auth works
- Tests pass (unit tests use in-memory SQLite)

**Communication:**
- Announce in team chat / PR description
- Link to updated setup docs
- Offer help debugging Postgres issues

---

### 5.2 Post-Migration Cleanup

**After all PRs merged:**
1. Remove deprecated LOKAL/ producer script
2. Archive old audit docs (keep as reference)
3. Update architecture docs (DB layout, pipeline)

---

## Appendix A: Testing Checklist

### stats_all.db Removal
- [ ] `/api/v1/atlas/overview` returns 404 (expected)
- [ ] `/get_stats_all_from_db` returns 404 (expected)
- [ ] `/api/corpus_stats` returns JSON (new endpoint)
- [ ] Player footer displays stats (no errors)
- [ ] Atlas map loads (countries + files)
- [ ] Editor file info works (duration + word count)

### Producer Script Migration
- [ ] `python scripts/stats_db/build_metadata_stats.py --rebuild` succeeds
- [ ] Generated DBs match schema (run `.schema` in sqlite3)
- [ ] Atlas map works after regeneration
- [ ] File metadata correct (check random sample)

### Dev Postgres Migration
- [ ] Dev start without `AUTH_DATABASE_URL` → fails
- [ ] Dev start with Postgres → app boots
- [ ] Login/register works
- [ ] Password reset works
- [ ] Admin user creation works
- [ ] Tests pass (`pytest tests/`)

---

## Appendix B: Rollback Plans

### stats_all.db Removal
**If frontend breaks:**
1. Revert endpoint removal commits
2. Restore `stats_all.db` from backup (rsync prod copy)
3. Debug player footer code

**Likelihood:** Low (frontend doesn't call removed endpoints)

### Producer Migration
**If DBs corrupted:**
1. Use old LOKAL/ script to regenerate
2. Compare schemas: `diff <(sqlite3 old.db .schema) <(sqlite3 new.db .schema)`
3. Fix migration script, re-run

**Likelihood:** Very low (script tested locally before PR)

### Dev Postgres Migration
**If devs blocked:**
1. Restore SQLite fallback temporarily
2. Help debug individual Postgres setup issues
3. Re-remove fallback once all devs migrated

**Likelihood:** Medium (depends on team Docker familiarity)

---

**End of Results Document**

**Next Action:** Implement PR 1 (stats_all.db removal) — lowest risk, immediate value.
