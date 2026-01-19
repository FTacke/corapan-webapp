# BlackLab Index Rebuild - Token_ID Case Fix

**Date:** 2026-01-15  
**Reason:** Fix token_id case preservation (VENb379fcc75 → venb379fcc75 bug)  
**Time Required:** 10-30 minutes  

---

## Problem

BlackLab index was configured with case-insensitive `tokid` field, causing all Token IDs to be lowercased during indexing. The configuration has been fixed, but **the existing index must be rebuilt** to apply the changes.

---

## Prerequisites

✅ Docker Desktop running  
✅ BlackLab server container running (`blacklab-server-v3`)  
✅ TSV export files exist in `data/blacklab_export/tsv/`  

---

## Rebuild Steps

### 1. Backup Current Index

```powershell
# Create timestamped backup
$backupName = "blacklab_index.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item -Path "data\blacklab_index" -Destination "data\$backupName" -Recurse
Write-Host "Backup created: data\$backupName"
```

### 2. Stop BlackLab Server

```powershell
docker compose -f docker-compose.dev-postgres.yml stop blacklab-server-v3
```

### 3. Delete Old Index

```powershell
Remove-Item -Path "data\blacklab_index" -Recurse -Force
Write-Host "Old index deleted"
```

### 4. Restart BlackLab Server

```powershell
docker compose -f docker-compose.dev-postgres.yml start blacklab-server-v3

# Wait for server to be ready (10-15 seconds)
Start-Sleep -Seconds 15
```

### 5. Rebuild Index

```powershell
# Run the index build script
.\scripts\build_blacklab_index.ps1

# This will:
# - Create new empty index with updated config
# - Import all TSV files from data/blacklab_export/tsv/
# - Apply case-sensitive tokid indexing
```

**Expected Output:**
```
Building BlackLab index...
Creating corpus 'corapan'...
Indexing TSV files...
Processed: 2022-03-14_VEN_RCR.tsv
Processed: 2023-10-10_ARG_Mitre.tsv
...
Index build complete!
Total documents: 146
Total tokens: ~5 million
```

---

## Verification

### Test 1: BlackLab Direct Query

```powershell
# Query for specific mixed-case token_id
$response = Invoke-WebRequest -Uri "http://localhost:8081/blacklab-server/corpora/index/hits?patt=[tokid=%22VENb379fcc75%22]&first=0&number=1&listvalues=tokid" -UseBasicParsing
$response.Content
```

**Expected:** `<value>VENb379fcc75</value>` (mixed case preserved)  
**Before Fix:** `<value>venb379fcc75</value>` (lowercase only) OR no matches

### Test 2: Backend Integration

```powershell
# Start dev server
.\scripts\dev-start.ps1

# In another terminal, test API
Invoke-WebRequest -Uri "http://localhost:8000/search/advanced/data?q=El&draw=1&start=0&length=10" -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json | Select-Object -ExpandProperty data | Select-Object token_id -First 3
```

**Expected:** Token IDs with mixed case (if present in data)

### Test 3: Frontend E2E

1. Navigate to `http://localhost:8000/search/advanced`
2. Search for: `El` (word search)
3. Check Token-ID column in results table
4. **Expected:** Mixed case token IDs visible (e.g., `VENb379fcc75`)

### Test 4: Case-Sensitive Search

```powershell
# This should work (exact case)
Invoke-WebRequest -Uri "http://localhost:8081/blacklab-server/corpora/index/hits?patt=[tokid=%22VENb379fcc75%22]&first=0&number=1" -UseBasicParsing

# This should NOT work (wrong case)
Invoke-WebRequest -Uri "http://localhost:8081/blacklab-server/corpora/index/hits?patt=[tokid=%22venb379fcc75%22]&first=0&number=1" -UseBasicParsing
```

**Expected:** Only exact case matches work

---

## Rollback (If Needed)

If rebuild fails or causes issues:

```powershell
# Stop server
docker compose -f docker-compose.dev-postgres.yml stop blacklab-server-v3

# Delete failed index
Remove-Item -Path "data\blacklab_index" -Recurse -Force

# Restore backup (use actual backup name)
Copy-Item -Path "data\blacklab_index.backup_YYYYMMDD_HHmmss" -Destination "data\blacklab_index" -Recurse

# Restart server
docker compose -f docker-compose.dev-postgres.yml start blacklab-server-v3
```

---

## Troubleshooting

### Issue: "Index already exists"

```powershell
# Force delete via Docker
docker exec blacklab-server-v3 rm -rf /data/index/corapan
```

### Issue: Build script fails

```powershell
# Check TSV files exist
Get-ChildItem data\blacklab_export\tsv\*.tsv

# Check BlackLab server logs
docker logs blacklab-server-v3 --tail 50

# Verify config files
Get-Content config\blacklab\corapan-tsv.blf.yaml | Select-String -Pattern "tokid" -Context 3
```

Should show:
```yaml
- name: tokid
  valuePath: tokid
  sensitivity: sensitive  # <-- THIS LINE IS CRITICAL
  uiType: text
```

### Issue: Rebuild takes too long

Normal rebuild times:
- Small corpus (<1M tokens): 2-5 minutes
- Medium corpus (1-5M tokens): 10-20 minutes
- Large corpus (>5M tokens): 30-60 minutes

If stuck for >1 hour, check Docker logs for errors.

---

## Post-Rebuild Checklist

- [ ] Backup created successfully
- [ ] Old index deleted
- [ ] Rebuild completed without errors
- [ ] BlackLab direct query shows mixed case
- [ ] Backend API returns mixed case
- [ ] Frontend displays mixed case
- [ ] Case-sensitive search works
- [ ] All E2E tests pass

---

## References

- **Root Cause Analysis:** [docs/architecture/token-id-case-bug-postmortem.md](./token-id-case-bug-postmortem.md)
- **BlackLab Config:** [config/blacklab/corapan-tsv.blf.yaml](../../config/blacklab/corapan-tsv.blf.yaml)
- **Build Script:** [scripts/build_blacklab_index.ps1](../../scripts/build_blacklab_index.ps1)

---

**Status:** Ready for execution  
**Impact:** Critical - required for token_id case preservation fix
