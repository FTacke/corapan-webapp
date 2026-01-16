# BlackLab Pipeline Discovery — Document Index

**Phase:** Fact-Finding & Analysis Complete  
**Date:** 2026-01-16  
**Output:** Three comprehensive documents

---

## 📄 Documents Created

### 1. **DISCOVERY_README.md** (This Overview)
- **Purpose:** Executive summary, 1-page reference
- **Audience:** Everyone (managers, operators, developers)
- **Content:**
  - Pipeline overview (Export → Build → Publish)
  - Key findings summary
  - "Build in Production" audit results
  - Risks & mitigations
  - Recommendations
  - Success criteria

**Start here** if you want a quick understanding.

---

### 2. **DISCOVERY_FACTSHEET.md** (Complete Technical Reference)
- **Purpose:** Complete inventory with all technical details
- **Audience:** Developers, technical leads
- **Content:**
  - LOKAL repository structure
  - **Export Contract** (full specification)
    - Command, parameters, inputs, outputs
    - Idempotency behavior
    - Error handling & exit codes
  - **Build Contract** (full specification)
    - Command, parameters, Docker image
    - Process steps (preflight → backup → build → verify → activate)
    - Outputs & validation criteria
  - **Publish Contract** (full specification)
    - SSH parameters, upload method, validation gates
    - 7-step process (preflight → upload → verify → validate → swap → sanity check → summary)
    - Remote paths & configuration
  - **Production Build Script** (reference, not auto-run)
  - **Contracts Summary Table**
  - **Wrapper Parameter List** (proposed)
  - **Happy Path Sequence** (3-line example)
  - **Top 5 Failure Modes** (troubleshooting)
  - **"Build in Production" Audit** (what we searched for, what we found)
  - **Removal Plan** (why nothing needs removal; auto-building doesn't exist)

**Read this** for complete technical reference before implementing wrapper.

---

### 3. **WRAPPER_DESIGN.md** (Implementation Guide)
- **Purpose:** Design & specification for the upcoming wrapper script
- **Audience:** Developers building the wrapper
- **Content:**
  - **Executive Summary** (what the wrapper will do)
  - **Wrapper Signature & Parameters**
    - Full PowerShell parameter list
    - Detailed descriptions of each parameter
    - Default values
  - **Wrapper Internal Structure**
    - Phase 1: Initialization & Validation
    - Phase 2: Export (with command & error handling)
    - Phase 3: Build (with command & error handling)
    - Phase 4: Publish (with command & error handling)
    - Phase 5: Summary & Cleanup
  - **Usage Examples** (6 real-world scenarios)
    - Full pipeline
    - Dry-run
    - Skip export
    - Build only
    - Custom server
    - Automation/CI
  - **Error Handling & Recovery**
    - Fail-fast behavior
    - Phase-specific recovery
    - Manual rollback commands
  - **Logging Format** (example log output)
  - **Integration with LOKAL Workflow** (folder structure)
  - **Dependencies & Assumptions** (tools required)
  - **Testing Strategy** (4-step validation before full run)
  - **Future Enhancements** (out of scope but mentioned)
  - **Quick Reference** (cheat sheet of common commands)

**Read this** to understand the wrapper design and how to implement it.

---

## 🔍 How to Navigate

### "I'm a Manager/Operator"
→ Read **DISCOVERY_README.md** (this file)  
→ Then look at **WRAPPER_DESIGN.md** usage examples section

### "I'm Implementing the Wrapper"
→ Read **DISCOVERY_FACTSHEET.md** (full reference)  
→ Then **WRAPPER_DESIGN.md** (specification)  
→ Use both as your implementation guide

### "I'm Reviewing the Work"
→ Read **DISCOVERY_README.md** (findings summary)  
→ Scan **DISCOVERY_FACTSHEET.md** (to verify completeness)  
→ Check **WRAPPER_DESIGN.md** (to see if design is sound)

### "I'm Doing a Security Audit"
→ Check "Build in Production" Audit section in all docs  
→ Review SSH parameters in WRAPPER_DESIGN.md  
→ Check error handling sections

---

## 📊 Document Statistics

| Document | Lines | Sections | Tables | Examples |
|----------|-------|----------|--------|----------|
| DISCOVERY_README.md | ~200 | 12 | 3 | 1 |
| DISCOVERY_FACTSHEET.md | ~800 | 15 | 5 | 20+ |
| WRAPPER_DESIGN.md | ~400 | 12 | 2 | 6 |
| **TOTAL** | **~1400** | **39** | **10** | **30+** |

---

## ✅ What Was Done (Scope)

- ✅ Explored LOKAL repository structure
- ✅ Documented `blacklab_export.py` entry point
- ✅ Analyzed Export module fully (`src/scripts/blacklab_index_creation.py`)
- ✅ Found & documented Build script (`scripts/blacklab/build_blacklab_index.ps1`)
- ✅ Found & documented Publish script (`scripts/deploy_sync/publish_blacklab_index.ps1`)
- ✅ Found & documented Prod Build script (`scripts/blacklab/build_blacklab_index_prod.sh`)
- ✅ Extracted all parameters, commands, inputs, outputs
- ✅ Defined "contracts" for Export/Build/Publish
- ✅ Audited for "Build in Production" (found: none auto-triggered)
- ✅ Created comprehensive troubleshooting guide
- ✅ Designed wrapper script signature & behavior

---

## ❌ What Was NOT Done (Out of Scope)

- ❌ No code changes to any scripts
- ❌ No wrapper implementation (design only)
- ❌ No functional modifications to pipeline
- ❌ No production deployment
- ❌ No refactoring
- ❌ No automated build system setup

---

## 🎯 Purpose of Each Document

### DISCOVERY_README.md
**Why:** Executives & operators need to understand findings without technical depth  
**What:** Key insights, risks, success criteria, recommendations

### DISCOVERY_FACTSHEET.md
**Why:** Complete reference needed before building anything  
**What:** Every path, parameter, command, input, output, exit code

### WRAPPER_DESIGN.md
**Why:** Developer needs clear specification before coding  
**What:** Interface design, behavior spec, examples, error handling

---

## 🔗 Cross-References

### In DISCOVERY_FACTSHEET.md
- Links to actual script files: [file](path#L10)
- Code excerpts from real implementation
- Exact command lines that run
- Actual exit codes observed

### In WRAPPER_DESIGN.md
- References to factsheet sections for details
- Examples that use real parameters
- Error handling that matches actual scripts
- Testing sequence that validates the design

### In DISCOVERY_README.md
- Summary of factsheet findings
- Links to all three documents
- High-level overview of wrapper design

---

## 💡 Key Insights

1. **Pipeline is Production-Ready**  
   All three phases (Export, Build, Publish) are well-implemented with proper validation

2. **No Automatic "Build in Production" Exists**  
   This is intentional—builds should be operator-controlled, not automated

3. **Wrapper Will Simplify Workflow**  
   Currently: operator runs 3 separate scripts  
   After: operator runs 1 wrapper script

4. **Export & Build Are Idempotent**  
   Safe to re-run multiple times (caching via hashing)

5. **Publish Has Multiple Validation Gates**  
   3 layers of validation prevent bad indexes reaching production

---

## 🚀 What Happens Next

### Phase 1: Fact-Finding (Done ✅)
Documents: DISCOVERY_README.md, DISCOVERY_FACTSHEET.md, WRAPPER_DESIGN.md

### Phase 2: Wrapper Implementation (Not in scope)
Would create: `LOKAL/_1_blacklab/publish_blacklab.ps1`

### Phase 3: Testing (Not in scope)
Would test wrapper against real data in staging environment

### Phase 4: Operator Documentation (Not in scope)
Would write end-user guide for using the wrapper

---

## 📌 Summary

**Status:** ✅ Fact-finding complete  
**Quality:** Comprehensive (1400+ lines of analysis)  
**Ready for:** Implementation phase  
**Code Changes:** None (analysis only)  
**Risk Level:** Low (read-only exploration)

---

## Quick Command Reference

### To Read Documents in Order
```bash
# Start here
cat DISCOVERY_README.md

# Then technical details
cat DISCOVERY_FACTSHEET.md

# Then implementation details
cat WRAPPER_DESIGN.md
```

### To Search Documents
```bash
# Find all mentions of "Export"
grep -n "Export" DISCOVERY_FACTSHEET.md

# Find all PowerShell examples
grep -n "powershell\|\.ps1" WRAPPER_DESIGN.md

# Find all parameters
grep -n "param\|Default:" WRAPPER_DESIGN.md
```

---

## Document Versions

| Document | Version | Date | Status |
|----------|---------|------|--------|
| DISCOVERY_README.md | 1.0 | 2026-01-16 | ✅ Final |
| DISCOVERY_FACTSHEET.md | 1.0 | 2026-01-16 | ✅ Final |
| WRAPPER_DESIGN.md | 1.0 | 2026-01-16 | ✅ Final |

All documents are ready for review and implementation planning.

---

## Contact & Support

For questions about findings:
→ Check DISCOVERY_FACTSHEET.md (all technical details with proof)

For implementation questions:
→ Check WRAPPER_DESIGN.md (specification & examples)

For high-level overview:
→ You're reading it (DISCOVERY_README.md)

