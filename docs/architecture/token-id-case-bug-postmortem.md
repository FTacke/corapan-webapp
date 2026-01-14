# Token_ID Case Preservation Bug - Root Cause Analysis

**Date:** 2026-01-15  
**Status:** ✅ FIXED  
**Severity:** Critical (data integrity issue)  

---

## Problem Statement

Token IDs displayed in DataTables were **always lowercase** (e.g., `venb379fcc75`) despite source data containing mixed-case values (e.g., `VENb379fcc75`).

**Evidence:**
- TSV source: `data/blacklab_export/tsv/2022-03-14_VEN_RCR.tsv` line 19 contains `tokid` = `VENb379fcc75`
- BlackLab response: Returns `venb379fcc75` (all lowercase)
- UI display: Shows `venb379fcc75` (matches BlackLab)

---

## Root Cause

**BlackLab-Index configuration was case-insensitive for `tokid` field.**

### Technical Details

BlackLab Format files (`.blf.yaml`) define how fields are indexed. By default, **fields without explicit `sensitivity: sensitive` are indexed case-insensitively**, meaning:
- Input: `VENb379fcc75`
- Indexed: `venb379fcc75` (lowercased)
- Query result: `venb379fcc75` (lowercase only)

**Affected files:**
1. `config/blacklab/corapan-tsv.blf.yaml` - TSV import format
2. `config/blacklab/corapan-json.blf.yaml` - JSON import format

### Configuration Before Fix

```yaml
# corapan-tsv.blf.yaml - Line 130-133
- name: tokid
  displayName: "Token ID"
  description: "Unique token identifier for linking to app"
  valuePath: tokid
  uiType: "text"
  # ❌ NO sensitivity specified = default case-insensitive
```

---

## Investigation Timeline

### Phase 1: Initial Hypothesis (INCORRECT)
**Suspected:** DataTables render function not wrapping `token_id` with `.token-id` CSS class  
**Action:** Added CSS class wrapper in `datatableFactory.js`  
**Result:** Did not fix issue (BlackLab was already returning lowercase)

### Phase 2: Pipeline Trace
1. **TSV Source Check** ✅
   - Confirmed: `tokid` column contains mixed case (`VENb379fcc75`)
   
2. **BlackLab Response Check** ❌ **ROOT CAUSE FOUND**
   - Query: `http://localhost:8081/blacklab-server/corpora/corapan/hits?patt=[word="El"]&listvalues=word,tokid`
   - Response: All `tokid` values returned as lowercase (`arg53b36e4ff`, etc.)
   - **Conclusion:** BlackLab index was lowercasing at indexing time

3. **Backend Python Check** ✅
   - `blacklab_search.py` line 244: `token_id = _safe_first(match.get("tokid", []))` - No transformation
   - **Conclusion:** Python backend preserves case (but receives lowercase from BlackLab)

4. **Frontend JS Check** ✅
   - `datatableFactory.js` line 24: `toLowerCase()` only for `data-token-id-lower` attribute (search/URL)
   - Display column (line 217): Uses original `data` value
   - **Conclusion:** Frontend preserves case (but receives lowercase from API)

5. **CSS Check** ✅
   - No `text-transform: lowercase` found
   - **Conclusion:** CSS not causing transformation

### Phase 3: BlackLab Configuration Analysis
- Checked `config/blacklab/corapan-tsv.blf.yaml`
- **Found:** `tokid` field missing `sensitivity: sensitive` property
- **BlackLab Default:** Fields without explicit sensitivity are **case-insensitive** (lowercased)

---

## Fix Implementation

### Changes Required

#### 1. BlackLab Format Configuration
**File:** `config/blacklab/corapan-tsv.blf.yaml`

```yaml
# Before
- name: tokid
  displayName: "Token ID"
  description: "Unique token identifier for linking to app"
  valuePath: tokid
  uiType: "text"

# After
- name: tokid
  displayName: "Token ID"
  description: "Unique token identifier for linking to app"
  valuePath: tokid
  sensitivity: sensitive  # CRITICAL: Preserve case for VENb379fcc75 etc
  uiType: "text"
```

**File:** `config/blacklab/corapan-json.blf.yaml`

```yaml
# Before
- name: tokid
  valuePath: tokid
  uiType: text

# After
- name: tokid
  valuePath: tokid
  sensitivity: sensitive  # CRITICAL: Preserve case for token_id values
  uiType: text
```

#### 2. Index Rebuild Required ⚠️

**CRITICAL:** Existing BlackLab index must be rebuilt to apply case-sensitive indexing.

```powershell
# Step 1: Backup current index
Copy-Item -Path "data\blacklab_index" -Destination "data\blacklab_index.backup_$(Get-Date -Format 'yyyyMMdd')" -Recurse

# Step 2: Delete old index
Remove-Item -Path "data\blacklab_index" -Recurse -Force

# Step 3: Rebuild with updated config
.\scripts\build_blacklab_index.ps1
```

**Time Estimate:** ~10-30 minutes depending on corpus size

---

## Verification

### Test Plan

1. **Unit Test** ✅
   ```bash
   pytest tests/test_token_id_case_preservation.py -v
   ```
   - Tests: Python backend preserves case
   - Status: PASSING

2. **Integration Test** (After index rebuild)
   ```powershell
   # Query BlackLab directly
   Invoke-WebRequest -Uri "http://localhost:8081/blacklab-server/corpora/corapan/hits?patt=[tokid=%22VENb379fcc75%22]&first=0&number=1&listvalues=tokid" -UseBasicParsing
   ```
   - Expected: `<value>VENb379fcc75</value>` (mixed case preserved)
   - Current (before rebuild): `<value>venb379fcc75</value>` (lowercase only)

3. **E2E Test** (After index rebuild)
   - Navigate to `/search/advanced`
   - Search for: `[word="El"]`
   - Inspect DataTables rows
   - **Expected:** Token ID column shows mixed case (e.g., `VENb379fcc75`)

---

## Impact Assessment

### Data Integrity
- ✅ **Source data intact:** TSV files have correct mixed-case values
- ❌ **Index corrupted:** BlackLab index has lowercased values (must rebuild)
- ✅ **Backend code correct:** No transformation in Python layer
- ✅ **Frontend code correct:** No transformation in JavaScript layer

### User Impact
- **Search by Token ID:** May have been case-insensitive (users could search `venb...` or `VENb...`)
- **Display:** Always showed lowercase (confusing for users expecting mixed case)
- **Downloads/Exports:** May have exported lowercase (depends on source)

### Backward Compatibility
- **Breaking Change:** After rebuild, searches must use exact case
- **Mitigation:** Document case-sensitive search requirement
- **Alternative:** Add case-insensitive search variant if needed

---

## Lessons Learned

### Investigation Methodology
1. ✅ **Always trace from source to display** (TSV → BlackLab → Backend → API → Frontend)
2. ✅ **Test actual responses, not assumptions** (query BlackLab directly, don't assume backend)
3. ✅ **Check configuration files** (`.blf.yaml` files are critical for BlackLab behavior)
4. ❌ **Initial hypothesis was wrong** (CSS/JS wrapper was not the issue)

### BlackLab Gotchas
- **Default is case-insensitive:** Fields need explicit `sensitivity: sensitive`
- **Index rebuild required:** Configuration changes don't apply to existing index
- **No warning:** BlackLab doesn't warn about case transformation during indexing

### Prevention
- **CI Check:** Add validation that all ID fields have `sensitivity: sensitive`
- **Documentation:** Clearly document BlackLab format configuration rules
- **Testing:** Add E2E tests that verify case preservation through full stack

---

## Related Issues

- **Initial Fix Attempt:** Added `.token-id` CSS class (PR #XXX) - Did not solve root cause
- **Font Priority Fix:** Changed Consolas/Courier New order - Unrelated but in same branch

---

## References

- BlackLab Documentation: https://inl.github.io/BlackLab/guide/indexing-with-blacklab.html#annotation-sensitivity
- TSV Source Data: `data/blacklab_export/tsv/2022-03-14_VEN_RCR.tsv`
- BlackLab Format Spec: `config/blacklab/corapan-tsv.blf.yaml`
- Test Coverage: `tests/test_token_id_case_preservation.py`

---

**Status:** Fix committed, index rebuild pending  
**Next Steps:** 
1. Rebuild BlackLab index with updated configuration
2. Verify E2E test passes
3. Update user documentation about case-sensitive token ID search
4. Add CI validation for `sensitivity` on ID fields
