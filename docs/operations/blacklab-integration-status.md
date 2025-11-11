---
title: "BlackLab Integration Status"
status: active
owner: backend-team
updated: "2025-11-10"
tags: [blacklab, status, integration, infrastructure]
links:
  - docs/operations/blacklab-minimalplan.md
  - docs/operations/blacklab-verification-checklist.md
---

# 🎯 BlackLab Integration - Ready for "Búsqueda avanzada" UI

**Date:** 2025-11-10  
**Status:** ✅ Stage 1 Complete | ⏳ Stage 2-3 Pending Infrastructure  
**Target:** UI Implementation of "Búsqueda avanzada" (Advanced Search)

---

## 📋 Current State

### ✅ Completed (Stage 1: Export)
- **146 JSON files** → **146 TSV files** + **docmeta.jsonl**
- **1,487,120 tokens** ready for indexing
- Export script fully idempotent (can re-run anytime)
- All infrastructure code ready
- Full documentation suite created

### ⏳ Pending (Stage 2-3: Index Build + BLS)
- **Java JDK 11+** installation needed
- **BlackLab Server** binary needed
- **Index build:** `bash scripts/build_blacklab_index.sh tsv 4`
- **BLS startup:** `bash scripts/run_bls.sh 8081 2g 512m`
- **Proxy testing:** curl smoke tests

---

## 🚀 Next Steps (1-2 Hours)

### **Step 1:** Install Java + BlackLab
See: `docs/operations/blacklab-minimalplan.md` → "Installation"

### **Step 2:** Build Index
```bash
bash scripts/build_blacklab_index.sh tsv 4
```
Expected: `data/blacklab_index/` populated with Lucene index

### **Step 3:** Start BlackLab Server  
```bash
bash scripts/run_bls.sh 8081 2g 512m
```

### **Step 4:** Test Proxy (in another terminal)
```bash
curl http://localhost:8000/bls/
curl 'http://localhost:8000/bls/corpus/corapan/1/hits?cql_query=[lemma="ser"]'
```

**When all tests pass:** Environment is ready for UI implementation

---

## 📚 Documentation

**Quick Start:**
- `docs/operations/blacklab-minimalplan.md` ← **START HERE**
- `docs/operations/blacklab-quick-reference.md` (commands reference)

**Full Details:**
- `docs/operations/blacklab-integration-status.md` (comprehensive status)
- `docs/concepts/blacklab-indexing.md` (architecture)
- `docs/how-to/build-blacklab-index.md` (step-by-step)
- `docs/troubleshooting/blacklab-issues.md` (problems & solutions)

**Reference:**
- `docs/reference/blacklab-api-proxy.md` (CQL endpoints)
- `docs/reference/blf-yaml-schema.md` (index configuration)

**Contributing:**
- `docs/CONTRIBUTING.md` + case study: BlackLab workflow example

---

## 🎯 When Ready: UI Implementation

Once Stages 2-3 complete, implement **Búsqueda avanzada** with:

### **Backend Components**
1. **Blueprint:** `src/app/routes/advanced.py`
   - CQL query builder helpers
   - /advanced/search endpoint
   - Result pagination

2. **CQL Query Module:** `src/app/utils/cql.py`
   - CQL syntax validator
   - Query builder (from form fields)
   - Example queries

3. **Proxy Integration:** Already registered in `src/app/routes/bls_proxy.py`
   - No changes needed

### **Frontend Components**
1. **Template:** `templates/pages/search-advanced.html`
   - Form with field selectors (word, lemma, pos, tense, etc.)
   - Query preview
   - Results display (tokens with context)

2. **Styles:** `static/css/search-advanced.css`
   - Material Design 3 form styling
   - Syntax highlighting for CQL
   - Results layout

3. **JS Modules:**
   - `static/js/modules/search/cql-builder.js` (form → CQL)
   - `static/js/modules/search/results-renderer.js` (BLS → UI)

### **Utilities**
- htmx integration for live search preview
- Results export (CSV/JSON)
- Query history / saved searches

---

## 📁 Key Files

**Code:**
- `src/scripts/blacklab_index_creation.py` (exporter)
- `scripts/build_blacklab_index.sh` (index builder)
- `scripts/run_bls.sh` (BLS launcher)
- `src/app/routes/bls_proxy.py` (Flask proxy)

**Config:**
- `config/blacklab/corapan-tsv.blf.yaml` (index schema)

**Data:**
- `data/blacklab_index/tsv/*.tsv` (146 exported files)
- `data/blacklab_index/docmeta.jsonl` (metadata)

**Docs:** (See above)

---

## 🔍 Status Tracking

| Component | Status | Action |
|-----------|--------|--------|
| **Export** | ✅ Done | (no action needed) |
| **Java** | ⏳ TODO | Install JDK 11+ |
| **BlackLab** | ⏳ TODO | Download + extract |
| **Index Build** | ⏳ TODO | Run build script |
| **BLS Server** | ⏳ TODO | Start server |
| **Proxy Test** | ⏳ TODO | Run smoke tests |
| **UI Code** | ⏳ TODO | After Stage 2-3 |

---

## ⚡ Quick Commands

```bash
# Check prerequisites
java -version
ls /opt/blacklab-server/

# Build index
bash scripts/build_blacklab_index.sh tsv 4

# Start BLS (separate terminal)
bash scripts/run_bls.sh 8081 2g 512m

# Test proxy (separate terminal, Flask must run)
curl http://localhost:8000/bls/

# View exports
ls -la data/blacklab_index/tsv/ | wc -l
wc -l data/blacklab_index/docmeta.jsonl
```

---

## 💡 For Questions

1. **"How do I install Java?"**
   → See `docs/operations/blacklab-minimalplan.md` → Step 1

2. **"Index build failed"**
   → Check `logs/bls/index_build.log` + see troubleshooting

3. **"What's CQL?"**
   → See `docs/reference/blacklab-api-proxy.md` → CQL Examples

4. **"How do I implement the UI?"**
   → Prompt engineer will generate components + integration

---

## 📞 Support

- **Docs:** `docs/operations/` (all BlackLab docs)
- **Troubleshooting:** `docs/troubleshooting/blacklab-issues.md`
- **Guidelines:** `docs/CONTRIBUTING.md` (case study included)

---

**Created:** 2025-11-10  
**Target:** Ready for "Búsqueda avanzada" UI implementation  
**Next Review:** After Java + BlackLab installation  
**Milestone:** When proxy smoke tests pass ✅
