# Path Usage Matrix — Readers & Writers (2026-01-17)

Status: Access pattern baseline on `work/current`

---

## Overview

This matrix documents **who reads and writes what data** in the repository:
- **Path:** Data directory or file
- **Reader(s):** Scripts, services, or application components that consume the data
- **Writer(s):** Scripts or services that produce or modify the data
- **Context:** Development, build, or production use
- **Risks/Notes:** Potential issues, multi-writer conflicts, or deployment concerns

---

## Data Source Paths

### `media/transcripts/` — Core Corpus (Source)

| Aspect | Details |
|--------|---------|
| **Path** | `media/transcripts/` |
| **Content** | JSON v3 transcript files (primary corpus) |
| **Readers** | |
| · Flask App | Search endpoints (`src/app/search/advanced.py`) proxy via BlackLab |
| · BlackLab Export | `src/scripts/blacklab_index_creation.py` reads JSON, generates TSV/metadata |
| · Analysis Scripts | `scripts/check_normalized_transcripts.py`, `inspect_tsvs.py` |
| · Web UI | Audio/transcript display (via Flask proxy) |
| **Writers** | |
| · Data Import Pipeline | `scripts/migrate_json_v3.py`, user import endpoints |
| · Normalization Scripts | `scripts/normalize_transcripts.py`, `scripts/fix_emoji.py` |
| **Context** | `dev | prod` (synced via `deploy_media.ps1`) |
| **Risk** | 🔴 **CRITICAL**: Corruption breaks entire search system; **backup essential** |
| **Deployment** | ✅ Synced to production; canonical source on production server |
| **Notes** | Single source of truth for corpus; changes immediately affect BlackLab rebuild |

---

### `media/mp3-full/` — Full Audio (Source)

| Aspect | Details |
|--------|---------|
| **Path** | `media/mp3-full/` |
| **Content** | Full-length MP3 audio files |
| **Readers** | |
| · Web UI | Audio player (served via Flask static or endpoint) |
| · MP3 Splitting | `scripts/split_audio.py` (or equivalent) generates segment clips |
| · Analysis Scripts | Metadata extraction, duration calculation |
| **Writers** | |
| · Audio Upload Pipeline | `scripts/apply_audio_files.py` or user import endpoint |
| · Audio Normalization | Transcoding, bitrate adjustment scripts |
| **Context** | `dev | prod` (synced via `deploy_media.ps1`) |
| **Risk** | 🟡 Regenerable from original source; large (~50 GB); backup useful but not critical |
| **Deployment** | ✅ Synced to production; served to users |
| **Notes** | 1:1 mapping with transcripts; if transcripts change, audio must stay in sync |

---

### `media/mp3-split/` — Segment Audio (Generated)

| Aspect | Details |
|--------|---------|
| **Path** | `media/mp3-split/` |
| **Content** | Segment-level MP3 clips (one per token or segment) |
| **Readers** | |
| · Web UI | Segment audio playback (player widget) |
| · Analysis/KWIC | Token-level playback in search results |
| **Writers** | |
| · `scripts/split_audio.py` (or similar) | Generates clips from `mp3-full/` |
| **Context** | `dev | prod` (synced via `deploy_media.ps1`) |
| **Risk** | 🟡 **RISK**: Regenerable but time-consuming (hours to days); production copy must be preserved |
| **Deployment** | ✅ Synced to production; served to users |
| **Notes** | Dependent on both `mp3-full/` and `media/transcripts/` segment boundaries; rebuild if either changes |

---

## Build & Export Paths

### `data/blacklab_export/` — Build Intermediates

| Aspect | Details |
|--------|---------|
| **Path** | `data/blacklab_export/` |
| **Sub-paths** | `tsv/`, `json_ready/`, `docmeta.jsonl`, `metadata/` |
| **Content** | TSV corpus rows, JSON for JSON indexing, document metadata |
| **Readers** | |
| · `build_blacklab_index.ps1` | Reads `tsv/` and `docmeta.jsonl` to build Lucene index |
| · Backup/inspection | Manual verification, export audits |
| **Writers** | |
| · `src/scripts/blacklab_index_creation.py` | Reads `media/transcripts/` → writes TSV + docmeta.jsonl |
| · `scripts/blacklab/prepare_json_for_blacklab.py` | Reads `media/transcripts/` → writes `json_ready/` |
| · `scripts/blacklab/docmeta_to_metadata_dir.py` | Reads `docmeta.jsonl` → writes `metadata/` |
| **Context** | `dev | build` (not deployed to production directly; data is synced, not export) |
| **Risk** | 🟢 **OK**: Regenerable in minutes–hours from `media/transcripts/` |
| **Dependency Chain** | `media/transcripts/` → **export** → `data/blacklab_export/` → **build** → `data/blacklab_index/` |
| **Notes** | Part of CI/CD build pipeline; idempotent and reproducible |

---

### `data/blacklab_index/` — Live Search Index (Runtime)

| Aspect | Details |
|--------|---------|
| **Path** | `data/blacklab_index/` |
| **Content** | Lucene 9 search index (binary, tokenized corpus) |
| **Readers** | |
| · BlackLab Server (Docker) | Index mounted at `/data/index` (read-only during serve) |
| · Flask Search Proxy | Queries BlackLab CQL API (`src/app/search/advanced.py`) |
| **Writers** | |
| · `build_blacklab_index.ps1` | Rebuilds from `data/blacklab_export/tsv/` + `config/blacklab/` |
| **Context** | `dev | prod` (mounted in Docker; mounted in production) |
| **Risk** | 🟢 **OK**: Critical but reproducible; `build_blacklab_index.ps1` automates rebuild with backups |
| **Deployment** | ✅ Mounted in Docker; produced locally, synced/deployed to production |
| **Build Frequency** | On-demand (when corpus changes); typically before deployment |
| **Backup Policy** | Automatic backups in `data/blacklab_index.backup/` (see retention concerns) |
| **Notes** | Large index (5–20 GB); rebuild takes 1–3 hours depending on hardware |

---

## Database Paths

### `data/db/` — SQLite Auth DB (Local Dev)

| Aspect | Details |
|--------|---------|
| **Path** | `data/db/auth.db` |
| **Content** | User credentials, sessions, roles (SQLite) |
| **Readers** | |
| · Flask App | ORM queries via SQLAlchemy (`src/app/extensions/sqlalchemy_ext.py`) |
| · CLI Tools | `scripts/create_initial_admin.py`, `scripts/reset_user_password.py` |
| · Inspection | Manual SQL inspection for debugging |
| **Writers** | |
| · Flask App | User login, registration, password changes |
| · Migration Scripts | `scripts/apply_auth_migration.py` (v1 → v3 schema migration) |
| · Admin Tools | `scripts/create_initial_admin.py`, `scripts/reset_user_password.py` |
| **Context** | `dev` only (local SQLite fallback via `dev-setup.ps1 -UseSQLite`) |
| **Risk** | 🔴 **CRITICAL**: Contains real user credentials; **must never be committed** |
| **Deployment** | ❌ **NOT deployed**; production uses separate Docker PostgreSQL |
| **Status** | `.gitignore`d; regenerated per dev environment |
| **Notes** | Dev-only artifact; each developer has independent auth DB |

---

### PostgreSQL Auth DB (Docker, Dev & Prod)

| Aspect | Details |
|--------|---------|
| **Connection** | `postgresql://corapan_auth:corapan_auth@localhost:54320/corapan_auth` (dev) |
| **Content** | User credentials, sessions, roles, audit logs |
| **Readers** | |
| · Flask App | ORM queries via SQLAlchemy |
| · CLI Tools | Migration & admin scripts |
| **Writers** | |
| · Flask App | Login, registration, password changes |
| · Migration Scripts | Schema migrations |
| **Container** | `corapan_auth_db` (started by `dev-setup.ps1` or `dev-start.ps1`) |
| **Context** | `dev | prod` |
| **Risk** | 🔴 **CRITICAL**: User data; access must be restricted in production |
| **Backup** | Handled by Docker backup strategy (not in this repo) |
| **Init Script** | `migrations/0001_create_auth_schema_postgres.sql` (schema creation) |
| **Notes** | Default mode; SQLite only used as fallback with `-UseSQLite` flag |

---

## Metadata & Config Paths

### `data/blacklab_export/metadata/` — Search Metadata Cache (Generated)

| Aspect | Details |
|--------|---------|
| **Path** | `data/blacklab_export/metadata/` |
| **Content** | Per-document metadata JSONs (facets, fields for search) |
| **Readers** | |
| · BlackLab Server | Linked-file metadata for indexing |
| · Flask Search | Metadata display in search results |
| **Writers** | |
| · `src/scripts/blacklab_index_creation.py` | Generates from `media/transcripts/` document-level fields |
| · `scripts/blacklab/docmeta_to_metadata_dir.py` | Expands `docmeta.jsonl` to per-document JSONs |
| **Context** | `dev | prod` (cached; regenerable) |
| **Risk** | 🟢 **OK**: Regenerable from `data/blacklab_export/docmeta.jsonl` |
| **Dependency** | Generated during `blacklab_export/` creation |
| **Notes** | Performance optimization; indexing fails gracefully without it |

---

### `config/blacklab/` — Index Configuration (Source, Committed)

| Aspect | Details |
|--------|---------|
| **Path** | `config/blacklab/` |
| **Content** | Field definitions, analyzer config, index rules (YAML/XML) |
| **Readers** | |
| · `build_blacklab_index.ps1` | Mounted in Docker as `-v config/blacklab:/config/blacklab` |
| · BlackLab Server (Docker) | Loaded at startup |
| · `scripts/calc_blacklab_config_hash.py` | Computes config hash for validation |
| **Writers** | |
| · Repository Maintainer | Manual edits (version controlled) |
| **Context** | `dev | prod` (mounted in Docker) |
| **Risk** | 🟢 **OK**: Git-tracked; changes are deliberate and auditable |
| **Deployment** | ✅ Copied to production server; config determines index behavior |
| **Notes** | Critical for search behavior; changing this requires index rebuild |

---

## Development Scripts — Data Access Patterns

### BlackLab Export & Indexing Pipeline

```
media/transcripts/
  ↓ read by src/scripts/blacklab_index_creation.py
data/blacklab_export/
  ├── tsv/
  ├── docmeta.jsonl
  └── metadata/
  ↓ read by build_blacklab_index.ps1
data/blacklab_index/ (Lucene index)
  ↓ read by Flask search proxy
Web UI (search results)
```

| Stage | Script | Input | Output | Context |
|-------|--------|-------|--------|---------|
| 1. Export | `src/scripts/blacklab_index_creation.py` | `media/transcripts/` | `data/blacklab_export/tsv/`, `docmeta.jsonl` | build |
| 2. Metadata | `scripts/docmeta_to_metadata_dir.py` | `docmeta.jsonl` | `data/blacklab_export/metadata/` | build |
| 3. Build Index | `scripts/blacklab/build_blacklab_index.ps1` | `data/blacklab_export/tsv/`, `config/blacklab/` | `data/blacklab_index/` | build |
| 4. Serve | BlackLab Server (Docker) + Flask | `data/blacklab_index/` | Search API | runtime |

---

### Transcript Normalization & Migration

| Script | Input | Output | Writers | Risk |
|--------|-------|--------|---------|------|
| `scripts/normalize_transcripts.py` | `media/transcripts/` | `media/transcripts/` (in-place) | Modifies source | 🔴 **RISK**: Modifies canonical source; backup before running |
| `scripts/migrate_json_v3.py` | JSON v2 format | `media/transcripts/` (v3 format) | Writes to source | 🔴 **RISK**: Version conversion; test on copy first |
| `scripts/fix_emoji.py` | `media/transcripts/` | `media/transcripts/` (cleaned) | Modifies source | 🟡 **RISK**: Text normalization; verify results |
| `scripts/check_normalized_transcripts.py` | `media/transcripts/` | stdout (report) | Read-only | 🟢 OK |

---

### Audio Processing

| Script | Input | Output | Risk |
|--------|-------|--------|------|
| `scripts/split_audio.py` (or similar) | `media/mp3-full/` | `media/mp3-split/` | 🟡 **RISK**: Time-consuming; run on staging copy first |
| MP3 import pipeline | User upload | `media/mp3-full/` | 🔴 **RISK**: Depends on transcript sync; verify before import |

---

### Deployment Sync Scripts

| Script | Source | Destination | Context | Risk |
|--------|--------|-------------|---------|------|
| `LOKAL/_2_deploy/deploy_data.ps1` | `data/` on dev | Production server `/data/` | prod deploy | 🟡 **RISK**: Syncs to production; test on staging first |
| `LOKAL/_2_deploy/deploy_media.ps1` | `media/` on dev | Production server `/media/` | prod deploy | 🟡 **RISK**: Large; uses delta updates (rsync); test bandwidth |
| `LOKAL/_2_deploy/publish_blacklab.ps1` | `data/blacklab_index/` | BlackLab Docker registry or production | prod deploy | 🟡 **RISK**: Index distribution; coordinate with deployment window |

---

## Multi-Writer Conflict Zones

### 🔴 CRITICAL: `media/transcripts/` (Multiple Writers)

| Writer | Trigger | Frequency | Notes |
|--------|---------|-----------|-------|
| User Import Pipeline | Manual upload / API call | Occasional | Adds/updates documents |
| `scripts/normalize_transcripts.py` | Manual invocation | Rare | In-place normalization |
| `scripts/migrate_json_v3.py` | Manual invocation | One-time or migrations | Schema conversion |
| `scripts/fix_emoji.py` | Manual invocation | Ad-hoc | Text cleanup |

**Risk:** No built-in locking; concurrent writes could cause corruption. **Mitigation:** Require single operator; backup before running scripts.

---

### 🟡 RISK: `data/blacklab_export/` (Dependent on Source)

| Dependency | Status |
|-----------|--------|
| **Source:** `media/transcripts/` | Any write requires **regeneration** of export |
| **Impact:** Changes to transcripts invalidate `data/blacklab_export/` → requires rebuild |
| **Workflow:** Edit transcripts → run export → rebuild index (3-4 hours total) |

**Mitigation:** Automate via CI/CD; provide clear documentation for manual processes.

---

### 🟡 RISK: `data/blacklab_index/` (Backup Accumulation)

| Issue | Current State | Risk |
|-------|---------------|------|
| Backup Creation | `build_blacklab_index.ps1` auto-creates `.backup/` before rebuild | 🟡 Unbounded growth |
| Failed Builds | `.bad_*`, `.testbuild.bak_*` directories accumulate | 🟠 Disk space waste |
| Cleanup Policy | None defined | 🔴 **RISK**: Needs automated retention script |

**Mitigation:** Define retention policy (keep last 3 backups, delete >30 days old).

---

## Deployment Workflow

### Development → Production

```
media/transcripts/ (DEV)
  ↓ manual verification + backup
data/blacklab_export/ (DEV, regenerated)
  ↓
data/blacklab_index/ (DEV, rebuilt, backup created)
  ↓
LOKAL/_2_deploy/deploy_*.ps1
  ↓
Production Server:
  media/transcripts/ (PROD, synced via rsync)
  media/mp3-full/ (PROD, synced via rsync)
  media/mp3-split/ (PROD, synced via rsync)
  data/blacklab_export/ (PROD, synced)
  data/blacklab_index/ (PROD, deployed or rebuilt)
  ↓
Web UI (served to users)
```

**Critical Points:**
1. **No automatic deploy to main branch** (per requirements)
2. **Manual approval needed** for production data sync
3. **Backup before production sync**
4. **Staging validation** before production rollout

---

## Summary: Who Can Write What?

| Path | Safe to Write | Restrictions | Owner |
|------|---------------|--------------|-------|
| `media/transcripts/` | Operators + Scripts | Single operator; backup first | Corpus maintainer |
| `media/mp3-full/` | Import pipeline | Depends on transcript sync | Media engineer |
| `media/mp3-split/` | Audio split script | Regenerable; test on staging | DevOps |
| `data/blacklab_export/` | Build scripts (automated) | Regenerate from transcripts | CI/CD |
| `data/blacklab_index/` | Build scripts (automated) | Backed up automatically | CI/CD |
| `data/db/` | Flask app + migration scripts | Dev-only; local per developer | Framework |
| `config/blacklab/` | Repo maintainer | Git-tracked; reviewed in PR | Architecture |
| `config/keys/` | Ops (external secret mgmt) | Never in repo; secure injected | DevOps/Security |
| `static/` | Frontend developers | Git-tracked; CI/CD builds | Frontend |
| `logs/` | Application (runtime) | Log-rotated; not in repo | Framework/Ops |

---

## Risk Summary by Path

| Path | Risk Level | Action Required |
|------|-----------|-----------------|
| `media/transcripts/` | 🔴 **CRITICAL** | Backup essential; locking mechanism; versioning |
| `media/mp3-full/` | 🟡 | Sync schedule; verify before production |
| `media/mp3-split/` | 🟡 | Production copy is canonical; document rebuild time |
| `data/blacklab_export/` | 🟢 | OK; regenerable; automate |
| `data/blacklab_index/` | 🟢 | OK; but backup accumulation needs cleanup |
| `data/blacklab_index.backup*` | 🟡 | Define retention policy |
| `data/blacklab_index.bad*` | 🔴 | Delete (garbage) |
| `data/blacklab_index.testbuild*` | 🟠 | Delete (debug artifacts) |
| `data/db/` | 🔴 | Never commit; dev-only; backup per-developer |
| `config/blacklab/` | 🟢 | OK; Git-tracked |
| `config/keys/` | 🔴 | Never commit; secure injection only |
| `LOKAL/_2_deploy/` | 🟢 | OK; tracked; test before production |

---

**Generated:** 2026-01-17 | **Branch:** `work/current` | **Status:** Access baseline
