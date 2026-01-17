# BlackLab Dev Container Health & Stability Guide

## Issue: Unhealthy BlackLab Container (Jan 17, 2026)

### Symptom
- `docker ps` showed `blacklab-server-v3` status: **Up X seconds (unhealthy)**
- Health check failures: 50+
- Error: `FieldType` Enum deserialization mismatch in logs

### Root Cause
**Index Format Incompatibility:** The existing BlackLab index at `data/blacklab_index` was built with an **older version** of BlackLab (pre-5.0). The `latest` image tag pulled a newer `5.0.0-SNAPSHOT` version with incompatible metadata format:

```
Old format: FieldType = "untokenized" (lowercase)
New format: FieldType = "UNTOKENIZED" (uppercase enum)
```

When BlackLab 5.0 tried to deserialize the old index metadata, Jackson failed:
```
InvalidFormatException: Cannot deserialize value of type `FieldType` 
from String "untokenized": not one of the values accepted for Enum class: 
[UNTOKENIZED, TOKENIZED, NUMERIC]
```

### Solution

#### Phase 1: Docker Cleanup & Image Pinning

1. **Remove floating tag** in `docker-compose.dev-postgres.yml`:
   ```yaml
   # BEFORE (unstable):
   image: instituutnederlandsetaal/blacklab:latest
   
   # AFTER (pinned, stable):
   image: instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7
   ```

2. **Backup old index** (do not delete):
   ```powershell
   Rename-Item -Path "data/blacklab_index" -NewName "blacklab_index.bad_20260117_000048"
   ```

3. **Restart Docker**:
   ```powershell
   docker compose down
   docker compose -f docker-compose.dev-postgres.yml up -d
   ```

#### Phase 2: Verification

After restart, verify:
```powershell
# Check health status (should be "healthy" within 30s)
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"

# Verify endpoint
curl.exe -fsS "http://127.0.0.1:8081/blacklab-server/"
```

**Expected result:**
```xml
<?xml version="1.0" encoding="utf-8" ?>
<blacklabResponse>
  <apiVersion>5.0</apiVersion>
  <blacklabVersion>5.0.0-SNAPSHOT</blacklabVersion>
  <corpora>
    <entry>
      <key>corapan</key>
      <value><status>available</status>...</value>
    </entry>
  </corpora>
  ...
</blacklabResponse>
```

---

## Why Image Pinning Matters (DEV)

### Problem with `latest` Tag
- Pulls **unpredictable versions** (could be older, newer, different configuration)
- When Docker image is updated upstream, local dev suddenly breaks
- Floating versions make debugging harder

### Solution: Pin to Digest
```
instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7
```

**Benefits:**
- ✓ Deterministic: Same image every time
- ✓ Reproducible: All devs get same version
- ✓ Traceable: SHA identifies exact build
- ✓ Aligned with PROD: Use same digest as production

### How to Find Digest
```powershell
# Check what version is currently running
docker images --digests | grep blacklab

# Or inspect running container
docker inspect blacklab-server-v3 --format "{{.Image}}"
```

---

## Index Management

### Current Dev Index Location
- **Host path:** `C:\dev\corapan-webapp\data\blacklab_index`
- **Container mount:** `/data/index/corapan` (read-only)
- **Size:** ~280 MB

### Index Format

The index in use is **Index Format 4** (compatible with BlackLab 5.0):
```
FieldType enum values (5.0.0):
  - UNTOKENIZED
  - TOKENIZED
  - NUMERIC
```

### Rebuilding Index (If Needed)

If index becomes corrupted or needs refresh:

```powershell
# 1. Backup current
Rename-Item "data/blacklab_index" "blacklab_index.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# 2. Build new index
.\scripts\blacklab\build_blacklab_index.ps1

# 3. Restart BlackLab
docker compose down
docker compose -f docker-compose.dev-postgres.yml up -d
```

---

## Health Check Configuration

BlackLab uses HTTP health check (from `docker-compose.dev-postgres.yml`):

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/blacklab-server/"]
  interval: 10s      # Check every 10 seconds
  timeout: 5s        # Fail if no response in 5s
  retries: 12        # Fail after 12 failed checks (120s total)
  start_period: 30s  # Wait 30s before first check
```

**Healthy = endpoint returns HTTP 200**
**Unhealthy = endpoint returns 5xx or no response**

---

## Troubleshooting

### Still Unhealthy After Fix?

1. **Check logs:**
   ```powershell
   docker logs blacklab-server-v3 --tail 100
   ```

2. **Look for:**
   - `InvalidIndex` / `InvalidFormatException`
   - `FileNotFoundException` (wrong mount path?)
   - Tomcat startup errors

3. **If still broken:**
   - Remove index: `Remove-Item -Recurse -Force data/blacklab_index`
   - Rebuild: `.\scripts\blacklab\build_blacklab_index.ps1`

### Port Already in Use?

If `8081` is taken:
```yaml
# In docker-compose.dev-postgres.yml:
ports:
  - "8081:8080"  # Change first number to unused port
```

---

## Related Documentation

- [BlackLab Setup](../blacklab/index.md)
- [Development Setup](./development-setup.md)
- [Index Building](../blacklab/index-building.md)
- [Docker Troubleshooting](./docker-troubleshooting.md)

---

## Summary (Changes Made)

| File | Change | Reason |
|------|--------|--------|
| `docker-compose.dev-postgres.yml` | Pin image to digest (sha256:3753...) | Prevent floating-tag breakage |
| `data/blacklab_index.bad_*` | Backed up old index | Preserve for recovery, not in git |

**Status:** ✅ Fixed 2026-01-17  
**Next check:** 2026-02-17 (monthly health review)

