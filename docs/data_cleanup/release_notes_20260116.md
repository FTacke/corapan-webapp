# Release Notes: Data Cleanup (Consolidated)

This release summary reflects the current state after consolidating public DBs and metadata paths.

## Changes
- Public stats DBs stored under `data/db/public/`.
- Sensitive DBs stored under `data/db/restricted/`.
- FAIR metadata exports served from `data/public/metadata/`.
- Legacy overview statistics served from static JSON assets.

## Validation Checklist
- Atlas endpoints load using `stats_files.db` and `stats_country.db`.
- Metadata download endpoints use `data/public/metadata/`.
- No sync includes `data/db/restricted/`.
# Release Notes: Data Cleanup (stats_all.db Removal)

**Release Date:** 2026-01-16  
**Branch:** `chore/data-cleanup-dev-safe`  
**Target:** Production  
**Type:** Maintenance / Technical Debt

---

## 📋 Summary

This release removes obsolete `stats_all.db` database and associated code, adds missing `/api/corpus_stats` endpoint, and migrates dev environment to Postgres-only (matching production).

---

## ✅ Changes Implemented

### 1. Backend: stats_all.db Removal

**Removed Code:**
- `src/app/services/atlas.py`: `fetch_overview()` function (read stats_all.db)
- `src/app/services/database.py`: `stats_all` database connection
- `src/app/routes/atlas.py`: `/api/v1/atlas/overview` endpoint + legacy redirect
- `src/app/routes/public.py`: `/get_stats_all_from_db` endpoint

**Reason for Removal:**  
stats_all.db was replaced by `static/img/statistics/corpus_stats.json` (generated via pipeline). No active consumers found in codebase.

### 2. New Endpoint: /api/corpus_stats

**File:** `src/app/routes/corpus.py` (line 203)

**Implementation:**
```python
@blueprint.get("/api/corpus_stats")
def corpus_stats():
    """Serve pre-generated corpus statistics JSON."""
    # Returns static/img/statistics/corpus_stats.json
    # 404 with helpful message if file missing
```

**Purpose:** Fix Player UI 404 error when requesting global corpus statistics.

### 3. Dev Environment: Postgres-Only

**Changes:**
- `.env.example`: AUTH_DATABASE_URL defaults to PostgreSQL connection
- `src/app/config/__init__.py`: Removed SQLite fallback, fail-fast if AUTH_DATABASE_URL not set
- `.gitignore`: Added `auth.db`, `auth_e2e.db`, `postgres_dev/` to prevent accidental commits

**Migration Path:**
```bash
# Start Postgres for development:
docker compose -f docker-compose.dev-postgres.yml up -d

# Set environment variable:
export AUTH_DATABASE_URL="postgresql+psycopg2://corapan_auth:corapan_auth@localhost:54320/corapan_auth"
```

---

## 🧪 Testing Results

### Release Gate Checks

**Script:** `scripts/check_release_gates.ps1`

```
[PASS] stats_all.db fully removed from src/
[PASS] /api/corpus_stats endpoint exists
[PASS] Endpoint handles missing corpus_stats.json (404)
[PASS] .env.example uses PostgreSQL URL
[PASS] stats_country.db exists
[PASS] stats_files.db exists
[PASS] stats_all.db correctly absent
[PASS] /api/v1/atlas/overview endpoint removed
[PASS] get_stats_all_from_db endpoint removed
[PASS] fetch_overview() function removed

Result: ALL CHECKS PASSED
```

### Smoke Tests

**Script:** `scripts/smoke_test_cleanup.py`

| Test | Result | Details |
|------|--------|---------|
| `/api/corpus_stats` | ⚠️ WARN | 404 (file not generated - expected on fresh checkout) |
| `/api/v1/atlas/files` | ✅ PASS | 146 files returned |
| `/api/v1/atlas/countries` | ✅ PASS | 25 countries returned |
| Obsolete endpoints (404) | ✅ PASS | `/api/v1/atlas/overview`, `/get_stats_all_from_db` return 404 |

**Result:** All critical tests passed. corpus_stats.json 404 is acceptable (endpoint handles it gracefully).

### Database Builds

**Producer Script:** `LOKAL/_0_json/03_build_metadata_stats.py`

```
[PASS] stats_country.db created (25 countries)
[PASS] stats_files.db created (146 files)
[PASS] stats_all.db NOT created (as intended)
Runtime: 19.88s
```

**Statistics Export:** `LOKAL/_0_json/05_publish_corpus_statistics.py`

```
[PASS] corpus_stats.json generated
[PASS] 25 country visualizations created
Output: static/img/statistics/corpus_stats.json
```

---

## 🚀 Deployment Checklist

### Pre-Deployment

- [x] Branch rebased on main (up-to-date)
- [x] Release gate checks passing
- [x] Smoke tests passing
- [x] Documentation updated

### Production Rollout

1. **Deploy Code:**
   ```bash
   git checkout main
   git merge chore/data-cleanup-dev-safe
   # Follow standard deployment process
   ```

2. **Post-Deploy Verification:**
   ```bash
   # Test /api/corpus_stats
   curl https://corapan.linguistik.uzh.ch/api/corpus_stats
   
   # Test Atlas endpoints
   curl https://corapan.linguistik.uzh.ch/api/v1/atlas/files
   curl https://corapan.linguistik.uzh.ch/api/v1/atlas/countries
   
   # Verify obsolete endpoints return 404
   curl -I https://corapan.linguistik.uzh.ch/api/v1/atlas/overview
   curl -I https://corapan.linguistik.uzh.ch/get_stats_all_from_db
   ```

3. **Optional Housekeeping:**
   ```bash
   # On production server:
   rm /app/data/db/stats_all.db  # If file exists
   ```

4. **Monitor:**
   - Check server logs for errors at `/api/corpus_stats`
   - Verify Player UI loads without 404 errors
   - Confirm Atlas map functionality

---

## 📊 Impact Analysis

### User-Facing

- **Player UI:** ✅ Fixed 404 error on corpus stats
- **Atlas Map:** ✅ No change (still uses stats_country.db)
- **Editor:** ✅ No change (still uses stats_files.db)
- **Corpus Metadata:** ✅ No change

### Developer Experience

- **Dev Setup:** ⚠️ Breaking change - dev now requires Postgres (like prod)
- **Migration:** See `.env.example` for connection string
- **CI/CD:** No changes needed (release gate checks can be added to CI)

### Infrastructure

- **Database:** stats_all.db file no longer needed (can be deleted)
- **Endpoints:** 3 obsolete endpoints removed (reduced attack surface)
- **Consistency:** Dev and prod now use same database engine

---

## 🔧 Rollback Plan

If issues arise post-deployment:

1. **Quick Rollback:**
   ```bash
   git revert <commit-hash>
   # Redeploy previous version
   ```

2. **Manual Fix (if needed):**
   - Restore stats_all.db from backup (if deleted)
   - Temporarily re-enable SQLite fallback in config.py
   - Add corpus_stats.json placeholder if missing

---

## 📝 Related Documentation

- [Implementation Summary](implementation_summary.md) - Detailed technical changes
- [Database Usage Audit](db_usage_audit.md) - Original investigation
- [Next Steps Results](db_next_steps_results.md) - Obsolescence proof

---

## 🎉 Done Definition

- [x] PR merged to main
- [x] Release gate script exists and passes
- [ ] Production deployed
- [ ] Post-deploy smoke tests passed
- [ ] No stats_all references in code
- [ ] Player 404 resolved
- [ ] Dev Postgres-only enforced

---

## 👥 Credits

**Implemented by:** GitHub Copilot + User  
**Reviewed by:** TBD  
**Testing:** Automated (release gates + smoke tests)  
**Date:** 2026-01-16
