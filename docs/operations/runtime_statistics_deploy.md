# Production Deployment: Runtime-Only Statistics

**Status:** ✅ Runtime-only architecture active (as of 2026-01-17)

## Overview

Corpus statistics (`corpus_stats.json` + `viz_*.png`) are **generated at build/deployment time** and served from the **runtime data directory**, not from Git.

This document covers production deployment requirements and verification.

---

## Environment Configuration

### Required Environment Variables

**Either** set `PUBLIC_STATS_DIR` directly:
```bash
export PUBLIC_STATS_DIR="/path/to/runtime/data/public/statistics"
```

**Or** set `CORAPAN_RUNTIME_ROOT` and let the app derive it:
```bash
export CORAPAN_RUNTIME_ROOT="/path/to/runtime/root"
# App will use: ${CORAPAN_RUNTIME_ROOT}/data/public/statistics
```

### Validation in App Startup

The Flask app will:
- **Fail to start** if neither variable is set → Error on config load
- **Create directory** if it doesn't exist (with appropriate permissions)
- **Warn** if `corpus_stats.json` is missing (but continue; API returns 404 for stats endpoints)

---

## Deployment Checklist

### 1. Pre-Deploy (CI/Build Step)

Generate statistics **before** shipping the container or deployment package:

```bash
python LOKAL/_0_json/05_publish_corpus_statistics.py --out "${PUBLIC_STATS_DIR}"
```

This produces:
- `corpus_stats.json` (metadata + aggregated stats)
- `viz_total_corpus.png` (overall corpus composition)
- `viz_genero_profesionales.png` (gender distribution)
- `viz_modo_genero_profesionales.png` (production mode by gender)
- `viz_${COUNTRY}_resumen.png` (29 country-specific charts)

**Total:** 32 files (~3.6 MB).

### 2. Runtime Setup

Ensure the target deployment environment has:
- `${PUBLIC_STATS_DIR}` (or `${CORAPAN_RUNTIME_ROOT}/data/public/statistics`) writable by the app process
- All 32 generated files copied/synced to this directory

### 3. App Startup

Start the Flask app with environment variables set:

```bash
export PUBLIC_STATS_DIR="/path/to/statistics"  # OR
export CORAPAN_RUNTIME_ROOT="/path/to/runtime"
python -m src.app.main
```

---

## Verification (Post-Deploy)

### Health Check: Endpoints

#### JSON API
```bash
curl -i http://<host>:8000/corpus/api/corpus_stats
```
**Expected:** HTTP 200, Content-Type: `application/json`

#### Static Asset (PNG)
```bash
curl -i http://<host>:8000/corpus/api/statistics/viz_total_corpus.png
```
**Expected:** HTTP 200, Content-Type: `image/png`

#### Missing Stats (should 404, not 500)
```bash
curl -i http://<host>:8000/corpus/api/statistics/nonexistent.png
```
**Expected:** HTTP 404

### Logs to Check

App startup should show:
```
✓ Statistics found (generated: YYYY-MM-DD HH:MM:SS)
```

If missing:
```
⚠️  STATISTICS NOT GENERATED
    corpus_stats.json not found at: /path/to/statistics/corpus_stats.json
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| App fails to start | `PUBLIC_STATS_DIR` not set | Set env var before startup |
| GET `/corpus/api/corpus_stats` → 500 | Directory misconfigured | Verify `PUBLIC_STATS_DIR` in app config |
| GET `/corpus/api/statistics/viz_*.png` → 404 | Files not generated/synced | Run generator script or re-sync files |
| Content-Type wrong | Static file serving misconfigured | Check Flask route for `.png` MIME type handling |

---

## Rollback

If statistics become corrupted or out-of-date:

1. **Re-generate locally** (with latest corpus data):
   ```bash
   python LOKAL/_0_json/04_internal_country_statistics.py
   python LOKAL/_0_json/05_publish_corpus_statistics.py --out "${PUBLIC_STATS_DIR}"
   ```

2. **Replace on server:**
   ```bash
   rsync -av /local/statistics/ user@prod:/path/to/PUBLIC_STATS_DIR/
   ```

3. **Restart app** (cache will be cleared automatically):
   ```bash
   docker restart corapan_app  # or your deployment restart command
   ```

---

## Related Documentation

- [Statistics Generation](./statistics_generation.md)
- [Local Runtime Layout](../local_runtime_layout.md)
- [Production Setup](./production.md)
