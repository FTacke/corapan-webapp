---
title: "BlackLab Integration - Quick Reference"
status: active
owner: devops
updated: "2025-11-10"
tags: [blacklab, search, indexing, quick-start, operations]
links:
  - blacklab-integration-status.md
  - development-setup.md
  - ../concepts/blacklab-indexing.md
---

# 🚀 BlackLab Integration - Quick Reference

**Status:** ✅ Stage 1 Complete | ⏳ Stage 2-3 Pending  
**Last Updated:** 2025-11-10

---

## ⚡ Quick Start

### Development
```bash
# 1. Export JSON → TSV (already done!)
python -m src.scripts.blacklab_index_creation

# 2. Start Flask app (already running!)
python -m src.app.main  # localhost:8000

# 3. View exported files
ls -la data/blacklab_index/tsv/        # 146 TSV files
head -5 data/blacklab_index/docmeta.jsonl  # Document metadata
```

### Next Steps (After Java installed)
```bash
# 4. Build Lucene index
bash scripts/build_blacklab_index.sh tsv 4

# 5. Start BlackLab Server
bash scripts/run_bls.sh 8081 2g 512m

# 6. Test proxy
curl http://localhost:8000/bls/
curl 'http://localhost:8000/bls/corpus/corapan/1/hits?cql_query=[lemma="ser"]'
```

---

## 📊 Current Status

| Component | Status | Details |
|-----------|--------|---------|
| **Export** | ✅ Done | 146 JSON → 1,487,120 tokens |
| **Metadata** | ✅ Done | 146 entries in docmeta.jsonl |
| **TSV Format** | ✅ Done | 17-column schema |
| **Index Config** | ✅ Done | corapan-tsv.blf.yaml |
| **Proxy Blueprint** | ✅ Done | bls_proxy.py registered |
| **Index Build** | ⏳ Blocked | Needs Java + BlackLab |
| **BLS Server** | ⏳ Blocked | Needs Java + Binary |
| **E2E Testing** | ⏳ Pending | After BLS available |

---

## 📁 Key Files

**Code:**
- `src/scripts/blacklab_index_creation.py` - Exporter (406 lines)
- `scripts/build_blacklab_index.sh` - Index builder
- `src/app/routes/bls_proxy.py` - Flask proxy
- `config/blacklab/corapan-tsv.blf.yaml` - Index schema

**Data:**
- `data/blacklab_index/tsv/` - 146 TSV files (exported)
- `data/blacklab_index/docmeta.jsonl` - Metadata (146 entries)

**Documentation:**
- `docs/operations/blacklab-integration-status.md` - Full status report
- `BLACKLAB_EXECUTION_REPORT.md` - Execution details
- `docs/concepts/blacklab-indexing.md` - Architecture
- `docs/how-to/build-blacklab-index.md` - Step-by-step
- `docs/troubleshooting/blacklab-issues.md` - Common issues

---

## 🔧 Configuration

### Export Script
```bash
python -m src.scripts.blacklab_index_creation \
  --in media/transcripts           # Input JSON dir
  --out data/blacklab_index/tsv    # Output TSV dir
  --docmeta data/blacklab_index/docmeta.jsonl
  --format tsv                     # TSV-only
  --workers 4                      # Thread count
  [--limit N]                      # Testing only
  [--dry-run]                      # Preview
```

### Index Build
```bash
bash scripts/build_blacklab_index.sh [format] [workers]
# format: tsv (default)
# workers: 4 (default)
```

### BlackLab Server
```bash
bash scripts/run_bls.sh [port] [memory] [heap]
# port: 8081 (default)
# memory: 2g (default)
# heap: 512m (default)
```

---

## 📚 Paths (All Relative to Project Root)

```
media/transcripts/                     # Input JSON corpus
data/blacklab_index/
  ├── tsv/                            # Exported TSV files (146)
  ├── docmeta.jsonl                   # Metadata (146 entries)
  └── [built after indexing]          # Lucene index
data/blacklab_index.new/              # Index build staging
config/blacklab/
  ├── corapan.blf.yaml                # Original config (old)
  └── corapan-tsv.blf.yaml            # New TSV-only config
scripts/
  ├── build_blacklab_index.sh
  └── run_bls.sh
logs/bls/
  └── index_build.log                 # Index build output
```

---

## 🎯 Data Statistics

- **Input Files:** 146 JSON (from CO.RA.PAN corpus)
- **Output Tokens:** 1,487,120 (~1.5M)
- **Avg Tokens/File:** 10,187
- **Countries:** USA, VEN (2 main contributors)
- **Date Range:** 2022-2025

**TSV Column Mapping:**
```
1. word           → original form
2. norm           → normalized form
3. lemma          → dictionary entry
4. pos            → universal POS
5-8. tense,mood,person,number → morphology
9. aspect         → verbal aspect
10-13. tokid,start_ms,end_ms,sentence_id → alignment
14. utterance_id  → speaker turn
15. speaker_code  → speaker ID
```

---

## ⚠️ Known Issues

| Issue | Severity | Solution |
|-------|----------|----------|
| ~50 tokens missing lemma | LOW | Gracefully skipped, logged |
| Java not installed | HIGH | Install JDK 11+ |
| BlackLab Server not available | HIGH | Download binary |
| No proxy tests yet | MEDIUM | Create after BLS ready |
| Index not built | MEDIUM | Run build script after Java |

---

## 🔍 Debugging

### Check Export
```bash
# View first 3 lines
head -3 data/blacklab_index/tsv/2025-02-28_USA_Univision.tsv

# Check error log
cat data/blacklab_index/export_errors.jsonl

# Count tokens
wc -l data/blacklab_index/tsv/*.tsv | tail -1
```

### Check Metadata
```bash
# View sample entry
head -1 data/blacklab_index/docmeta.jsonl | jq .

# Count entries
wc -l data/blacklab_index/docmeta.jsonl
```

### Check Proxy
```bash
# Is Flask running?
ps aux | grep "flask run"

# Test endpoint
curl -v http://localhost:8000/bls/

# Check logs
tail -100 logs/flask.log
```

---

## 📖 Full Documentation

**Architecture & Concepts:**
- [BlackLab Indexing](docs/concepts/blacklab-indexing.md)
- [System Design](docs/concepts/architecture.md)

**How-To Guides:**
- [Build Index Step-by-Step](docs/how-to/build-blacklab-index.md)
- [Export Options](docs/how-to/build-blacklab-index.md#export-optionen)

**Reference:**
- [Proxy API Endpoints](docs/reference/blacklab-api-proxy.md)
- [Index Schema (YAML)](docs/reference/blf-yaml-schema.md)
- [CQL Query Examples](docs/reference/blacklab-api-proxy.md#cql-beispiele)

**Troubleshooting:**
- [Common Issues](docs/troubleshooting/blacklab-issues.md)
- [Index Build Errors](docs/troubleshooting/blacklab-issues.md#index-build-fehlschlag)
- [Proxy Errors](docs/troubleshooting/blacklab-issues.md#proxy-fehler)

**Reports & Status:**
- [Full Status Report](docs/operations/blacklab-integration-status.md)
- [Execution Report](BLACKLAB_EXECUTION_REPORT.md)

---

## 🎓 Contributing

When making changes:

1. **Discover** what files are affected
2. **Plan** changes with a dry-run table
3. **Lint** before applying (syntax, front-matter)
4. **Apply** changes systematically
5. **Document** in CONTRIBUTING.md case studies

See [Contributing Guidelines](docs/CONTRIBUTING.md) for details.

---

## 📞 Support

- **Questions?** Check docs/ folder first
- **Bug?** Create GitHub issue with details
- **Need help?** Contact backend-team

---

**Last Update:** 2025-11-10 14:40 UTC  
**Next Milestone:** Java + BlackLab Server Installation
