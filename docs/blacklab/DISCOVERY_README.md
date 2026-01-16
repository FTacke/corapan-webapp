# BlackLab Pipeline Discovery — Executive Summary

**Status:** ✅ Fact-Finding Complete  
**Date:** 2026-01-16  
**Scope:** Export → Build → Publish Pipeline Analysis (No Code Changes)

---

## What We Discovered

### 1. **The Pipeline Already Exists — It's Just Manual**

The complete BlackLab pipeline (Export → Build → Publish) is fully functional and well-designed:

| Phase | Location | Tool | Status |
|-------|----------|------|--------|
| **Export** | `src/scripts/blacklab_index_creation.py` | Python | ✅ Working |
| **Build** | `scripts/blacklab/build_blacklab_index.ps1` | PowerShell + Docker | ✅ Working |
| **Publish** | `scripts/deploy_sync/publish_blacklab_index.ps1` | PowerShell + SSH | ✅ Working |

### 2. **No Automatic "Build in Production" Exists**

Our audit found:
- ❌ No cron jobs for automatic rebuilds
- ❌ No systemd timers
- ❌ No GitHub Actions for index building
- ✅ Manual execution only (operator-triggered)

**This is intentional:** Index builds take 10-30 minutes and should be controlled manually.

### 3. **The Pipeline is Production-Ready**

Each phase has:
- ✅ Comprehensive error handling
- ✅ Validation gates (pre/post checks)
- ✅ Timestamped backups
- ✅ Rollback mechanisms
- ✅ Detailed logging

---

## What's Documented

### Three Deliverables Created

#### **1. DISCOVERY_FACTSHEET.md**
Complete technical inventory with:
- Export contract (inputs, outputs, commands, exit codes)
- Build contract (local Docker-based indexing)
- Publish contract (SSH upload, validation, atomic swap)
- Production build reference (bash script, not auto-run)
- Full parameter lists and troubleshooting guide

**Read this for:** Complete technical reference, all paths/commands/flags

#### **2. WRAPPER_DESIGN.md**
Proposed PowerShell wrapper design for `LOKAL/_1_blacklab/publish_blacklab.ps1`:
- Single entry point for full pipeline
- Phase control flags (`-SkipExport`, `-SkipBuild`, `-SkipPublish`)
- Dry-run mode (`-WhatIf`)
- Custom logging
- Usage examples

**Read this for:** How the wrapper will work, integration design, examples

#### **3. This File**
High-level summary and next steps

---

## Key Findings — One Page Summary

### Export Phase
```
Input:   media/transcripts/*.json (corpus documents)
Output:  data/blacklab_export/tsv/*.tsv + docmeta.jsonl
Command: python -m src.scripts.blacklab_index_creation --format tsv
Time:    5-10 minutes
```

### Build Phase
```
Input:   data/blacklab_export/tsv/*.tsv + docmeta.jsonl
Output:  data/blacklab_index/ (active Lucene index)
Command: .\scripts\blacklab\build_blacklab_index.ps1 -Activate
Time:    10-20 minutes (Docker-based, 1 thread to avoid race conditions)
```

### Publish Phase
```
Input:   data/blacklab_index/ (local) + SSH access + remote paths
Output:  /srv/webapps/corapan/data/blacklab_index/ (active) + timestamped backup
Command: .\scripts\deploy_sync\publish_blacklab_index.ps1 -Host 137.248.186.51
Time:    10-20 minutes (upload + validation + swap)
```

### Total Pipeline Time
**~30-50 minutes** (sequential: Export 5-10 + Build 10-20 + Publish 10-20)

---

## Top 5 Things to Know

### 1. Export Idempotency
- Uses content hashing → skips unchanged files
- Safe to re-run multiple times

### 2. Build Validation
- Checks file counts, sizes, Lucene structure files
- Starts temporary validation container
- Verifies corpus "corapan" present before swap

### 3. Publish Validation (3 Layers)
- **Local:** File count + size checks
- **Remote:** File count + size checks  
- **Container:** Temporary container validates corpus, documents, tokens

### 4. Atomic Swap
```bash
# Both commands run together (no failure window):
mv old_index backup_timestamped && mv new_index active
```

### 5. Rollback is Manual
```bash
# Operator provides this if swap fails:
ssh root@host
mv active bad && mv backup_timestamped active
```

---

## "Build in Production" Audit Results

### Was Looking For
- Cronjobs that automatically run index builds on prod
- Systemd timers that trigger on schedule
- GitHub Actions workflows that auto-deploy indexes
- Any automated rebuild mechanism

### What We Found
- ✅ Production build script exists: `build_blacklab_index_prod.sh`
- ✅ It's well-designed with validation + rollback
- ❌ But it's **never called automatically**
- ❌ No cron jobs, no timers, no GitHub Actions for it
- ✅ Operator must SSH and run manually

### Conclusion
**Current state is clean:** Manual control = Safe, Predictable, Auditable

**If auto-building was desired (future):** Script is ready, just needs cron wrapper

---

## Next Steps (Implementation Phase — Out of Scope Here)

These were NOT done (per requirements):

1. Create `LOKAL/_1_blacklab/publish_blacklab.ps1` wrapper
2. Implement phase orchestration logic
3. Add parameter validation & help system
4. Create unit tests for phase transitions
5. Test on both Windows (local) and Linux (prod validation)

---

## How to Use These Documents

### **For the Operator**
→ Read **WRAPPER_DESIGN.md**  
Shows how to use the upcoming wrapper script with examples

### **For the Developer Implementing Wrapper**
→ Read **DISCOVERY_FACTSHEET.md** (complete reference)  
Then read **WRAPPER_DESIGN.md** (design spec)  
Use both to build the PowerShell wrapper

### **For Code Review / Audit**
→ Read **DISCOVERY_FACTSHEET.md** + this file  
Contains all proof (file paths, code excerpts, command lines)

---

## Factual Proof (Excerpts)

### Export Entry Point
**File:** [LOKAL/_1_blacklab/blacklab_export.py](LOKAL/_1_blacklab/blacklab_export.py#L27)
```python
module_name = "src.scripts.blacklab_index_creation"
cmd = [sys.executable, "-m", module_name, "--format", "tsv"]
```

### Build Entry Point
**File:** [scripts/blacklab/build_blacklab_index.ps1](scripts/blacklab/build_blacklab_index.ps1#L1-L27)
```powershell
.SYNOPSIS
  Docker-based BlackLab index builder (BlackLab 5.x / Lucene 9)
```

### Publish Entry Point
**File:** [scripts/deploy_sync/publish_blacklab_index.ps1](scripts/deploy_sync/publish_blacklab_index.ps1#L1-L24)
```powershell
.SYNOPSIS
    Publish BlackLab index from local staging to production server
```

### No Automatic Building
**Search Result:** Grep for `cron|schedule|timer|auto.*build` found:
- Only references in docs
- No active configuration files
- No cron entries
- No GitHub Actions workflows for index building

---

## Risks & Mitigations

### Risk 1: Export Input JSON Format Changes
- **Impact:** Export fails or produces wrong output
- **Mitigation:** Version control JSON schema; document breaking changes

### Risk 2: Build Out of Memory
- **Impact:** Docker container killed (exit 137)
- **Mitigation:** Script detects exit 137, suggests reducing JAVA_XMX

### Risk 3: Network Interruption During Publish
- **Impact:** Upload incomplete, remote validation fails
- **Mitigation:** Script checks remote file count/size; fails gracefully before swap

### Risk 4: SSH Credential/Auth Issues
- **Impact:** Publish fails at first SSH call
- **Mitigation:** Wrapper can do connectivity check before starting phases

---

## Recommendations

### ✅ Do These
1. Create wrapper script as designed in WRAPPER_DESIGN.md
2. Use parameter defaults shown (they match current prod setup)
3. Implement `-WhatIf` mode for operators to preview
4. Add `-Force` flag for CI/automation contexts
5. Log comprehensively to file (for audit trail)

### ❌ Don't Do These
1. Add automatic "build in production" without operator approval
2. Remove production build script `build_blacklab_index_prod.sh` (keep as reference)
3. Change the atomic swap mechanism (it's working well)
4. Remove the validation gates (they prevent bad indexes)

---

## Questions for Next Phase

Before building the wrapper:

1. **Should `-Force` also skip validation questions?**  
   Recommendation: Yes (for CI automation)

2. **Should wrapper detect and warn about stale `media/transcripts/`?**  
   Recommendation: Check git status, warn if no changes since last export

3. **Should we add progress indicators / time estimates?**  
   Recommendation: Yes, improves UX (user can plan time)

4. **Should we support parallel/staged execution?**  
   Recommendation: No (for now); keep sequential for safety

5. **Should wrapper auto-generate rollback command?**  
   Recommendation: Yes, display it in log + console after successful publish

---

## Success Criteria (When Wrapper is Done)

✅ Operator can run single command: `publish_blacklab.ps1`  
✅ Full pipeline executes (Export → Build → Publish)  
✅ All errors are logged with context  
✅ Rollback commands are clear and easy  
✅ Dry-run mode (`-WhatIf`) works perfectly  
✅ Automation friendly (`-Force` flag skips all prompts)  
✅ Documentation is complete and examples are correct

---

## Files Produced

1. **[DISCOVERY_FACTSHEET.md](DISCOVERY_FACTSHEET.md)** (This repository)  
   Complete technical reference, 350+ lines

2. **[WRAPPER_DESIGN.md](WRAPPER_DESIGN.md)** (This repository)  
   Design document & usage guide, 280+ lines

3. **[DISCOVERY_README.md](DISCOVERY_README.md)** (This file)  
   Executive summary, 1-page overview

---

## Contact & Questions

For questions about this discovery phase:
- Review the factsheet for technical details
- Check the design document for implementation guidance
- All information is fact-based and documented with code references

---

**Phase Status:** ✅ Complete  
**Ready for Implementation:** Yes  
**Code Changes Required:** None (discovery only)  
**Next Phase:** Build `LOKAL/_1_blacklab/publish_blacklab.ps1` wrapper

