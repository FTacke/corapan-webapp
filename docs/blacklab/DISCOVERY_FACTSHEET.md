# BlackLab Pipeline Discovery Factsheet
**Repository Inventory & Contract Analysis**  
**Date:** 2026-01-16  
**Status:** Fact-Finding Complete (No Code Changes)

---

## PHASE 1: LOKAL Inventory

### Repository Structure

```
LOKAL/ (Private Operator Folder)
├── README.md
├── requirements-lokal.txt
├── _0_json/              # JSON preprocessing outputs (not BlackLab-related)
├── _0_mp3/               # Audio file staging
├── _1_blacklab/          # ← PRIMARY EXPORT ENTRY POINT
│   └── blacklab_export.py  (shell wrapper for Python module)
├── _1_metadata/
├── _1_zenodo-repos/
└── _3_analysis_on_json/
```

**Git Remote:**  
`origin  https://github.com/FTacke/corapan-webapp (fetch/push)`

**Git Status:**  
No uncommitted changes in LOKAL (checked 2026-01-16)

---

## PHASE 2A: Export Contract

### Export Entry Point

**File:** `LOKAL/_1_blacklab/blacklab_export.py`

**Purpose:**  
Wrapper that invokes the core Python module `src.scripts.blacklab_index_creation` from the corapan-webapp repo root.

#### Export Command

```bash
cd /path/to/corapan-webapp
python -m src.scripts.blacklab_index_creation --format tsv
```

**Module Path:** `src/scripts/blacklab_index_creation.py` (608 lines)

#### Export CLI Arguments (with Defaults)

```
--in        Default: media/transcripts
            Input JSON corpus directory (relative to project root)

--out       Default: data/blacklab_export/tsv
            Output TSV directory (relative to project root)

--format    Default: tsv
            Export format (TSV-only; WPL support removed)

--docmeta   Default: data/blacklab_export/docmeta.jsonl
            Output docmeta JSONL file (one JSON per line, one doc per line)

--workers   Default: 4
            Number of parallel worker threads

--limit     Default: None
            Optional: Limit number of input files (for testing)

--dry-run   Default: False
            Dry-run mode (prints first 3 files, no writes)
```

#### Export Inputs

**Required:**
- `media/transcripts/` — Directory containing `*.json` files (JSON v2 corpus format)
  - Each JSON file is one corpus document
  - Files are sorted alphabetically for consistent output

**Expected JSON Structure (v2 format):**
```json
{
  "file_id": "2023-08-10_ARG_Mitre",
  "country_code": "ARG",
  "country_scope": "...",
  "country_parent_code": "...",
  "country_region_code": "...",
  "city": "Buenos Aires",
  "radio": "Mitre",
  "date": "2023-08-10",
  "filename": "path/to/audio.mp3",
  "segments": [
    {
      "speaker": {
        "code": "lib-pm",
        "speaker_type": "pro",
        "speaker_sex": "m",
        "speaker_mode": "libre",
        "speaker_discourse": "general"
      },
      "words": [
        {
          "token_id": "...",
          "start_ms": 0,
          "end_ms": 100,
          "text": "hello",
          "norm": "hello",
          "lemma": "hello",
          "pos": "NOUN",
          "sentence_id": "s1",
          "utterance_id": "u1",
          "tense": "",
          "mood": "",
          "person": "",
          "number": "",
          "aspect": "",
          "PastType": "",
          "FutureType": "",
          "morph": {}
        }
      ]
    }
  ]
}
```

#### Export Outputs

**Primary Outputs:**

1. **TSV Files:**
   - **Path:** `data/blacklab_export/tsv/*.tsv` (one file per input JSON)
   - **Naming:** `{input_filename_stem}.tsv`
   - **Format:** Tab-separated, 29 columns (word, norm, lemma, pos, tense, mood, person, number, aspect, PastType, FutureType, tokid, start_ms, end_ms, sentence_id, utterance_id, speaker_code, speaker_type, speaker_sex, speaker_mode, speaker_discourse, file_id, country_code, country_scope, country_parent_code, country_region_code, city, radio, date, audio_path)
   - **First Line:** Header (column names)
   - **Data Lines:** One token per line

2. **Docmeta JSONL:**
   - **Path:** `data/blacklab_export/docmeta.jsonl`
   - **Format:** JSONL (one JSON object per line; each line = one document)
   - **Content:** Document metadata (file_id, filename, date, country_code, city, radio, etc.)
   - **One entry per input JSON file** (not per token)

**Secondary Outputs (if errors occur):**

3. **Error Log:**
   - **Path:** `data/blacklab_export/export_errors.jsonl`
   - **Content:** One JSON per line per failed file
   - **Format:** `{"file": "...", "error": "..."}`

#### Export Idempotency & Caching

- **Hash-based Cache:** Computes SHA256 hash over (country_code + date + radio + segments_count + first_tokens)
- **Skip Cache File:** (Computed in-memory, not persisted)
- **Behavior:** If hash matches, file is skipped (logged as "Skipped {file_id} (unchanged)")
- **Effect:** Files with same content are not re-exported

#### Export Error Handling

- **Exit Code 0:** Success (errors count logged, not fatal)
- **Exit Code 1:** Fatal errors (missing input dir, no TSV files written)
- **Malformed Tokens:** Logged per-file summary; tokens with missing mandatory fields are skipped
- **Mandatory Token Fields:** token_id, start_ms, end_ms, lemma, pos, norm, sentence_id, utterance_id

#### Export Termination Criteria ("fertig wenn")

✓ All JSON files in `media/transcripts/` processed  
✓ All TSV files written to `data/blacklab_export/tsv/`  
✓ `docmeta.jsonl` written with one entry per successful file  
✓ Script returns exit code 0  
✓ Log shows: "Export complete: {result_dict}"

---

## PHASE 2B: Build Contract (Local)

### Build Entry Point

**File:** `scripts/blacklab/build_blacklab_index.ps1` (303 lines, PowerShell)

**Purpose:**  
Local (Windows/Dev) index builder using Docker with BlackLab IndexTool.

#### Build Command

```powershell
cd c:\dev\corapan-webapp
.\scripts\blacklab\build_blacklab_index.ps1 [-SkipBackup] [-Force] [-Activate]
```

#### Build Parameters

```
-SkipBackup   Default: $false
              Skip creating a backup of the existing index

-Force        Default: $false
              Don't prompt for confirmation before deleting existing index

-Activate     Default: $true
              Atomically swap built index into place (blacklab_index.new → blacklab_index)
```

#### Build Inputs (Requirements)

**Required Files/Directories:**

1. **TSV Files:**
   - **Path:** `data/blacklab_export/tsv/*.tsv`
   - **Required Count:** > 0 files
   - **Expected:** Output from Export phase (same filenames)

2. **Docmeta:**
   - **Path:** `data/blacklab_export/docmeta.jsonl`
   - **Format:** JSONL (one JSON per line)
   - **Required:** Must exist and have > 0 entries

3. **BlackLab Config:**
   - **Path:** `config/blacklab/corapan-tsv.blf.yaml`
   - **Purpose:** Defines field mappings, indexing rules for TSV columns
   - **Referenced:** Used by IndexTool

4. **Docker Image:**
   - **Image:** `instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7`
   - **Alternative (Prod):** `instituutnederlandsetaal/blacklab:latest`
   - **Requirement:** Must be pulled before build starts (script auto-pulls if missing)

#### Build Process Overview

**Step 1: Preflight Validation**
- Check Docker available
- Verify TSV source has files
- Count docmeta entries
- Verify BLF config exists

**Step 2: Backup Existing Index** (unless -SkipBackup)
- Move `data/blacklab_index` → `data/blacklab_index.backup`
- Requires user confirmation (unless -Force)

**Step 3: Pull Docker Image** (if not present)
- `docker pull instituutnederlandsetaal/blacklab@sha256:...`

**Step 4: Run IndexTool in Docker**

```powershell
# Internal command (not shown to user, but functionally:)
docker run --rm \
  -v "${exportPath}:/data/export:ro" \
  -v "${indexTargetPathNew}:/data/index:rw" \
  -v "${configPath}:/config:ro" \
  "${BLACKLAB_IMAGE}" \
  java -cp "/usr/local/lib/blacklab-tools/*" \
    nl.inl.blacklab.tools.IndexTool create \
    /data/index \
    /data/export/tsv/tsv_for_index \
    /config/corapan-tsv.blf.yaml \
    --linked-file-dir /data/export/metadata \
    --threads 1
```

**Key Details:**
- **Working CWD:** Project root (where `data/blacklab_export` exists)
- **TSV Copy:** Before build, TSV files (excluding `*_min.tsv`) are copied to `data/blacklab_export/tsv/tsv_for_index`
- **Metadata Linkage:** IndexTool receives `--linked-file-dir /data/export/metadata` (per-file JSONs)
- **Threads:** Single-threaded (`--threads 1`) to avoid race conditions on Windows/OneDrive
- **Output:** All index files written to `/data/index` inside container → `data/blacklab_index.new` on host

**Step 5: Verify & Activate**
- Check new index dir has files
- Move `data/blacklab_index.new` → `data/blacklab_index` (atomic)
- Create backup if previous index exists
- Log summary

#### Build Outputs

**Primary Output:**

1. **Index Directory:**
   - **Path:** `data/blacklab_index/` (after -Activate swap)
   - **Staging (Pre-Activation):** `data/blacklab_index.new/`
   - **Content:** Lucene index files (*.blfi.*, *.dat, etc.)
   - **Backup (if -Activate):** `data/blacklab_index.backup` (timestamped or simple)

2. **Build Log:**
   - **Path:** `data/blacklab_index.new/build.log` (during build, then moved with index)
   - **Content:** All docker run stderr/stdout

#### Build Exit Codes

- **0:** Success (index built, validated, and activated)
- **1:** Failure at any stage (preflight, Docker, build, activation)

#### Build Termination Criteria ("fertig wenn")

✓ Step 1-2-3 pass (preflight, backup, image pull)  
✓ Docker IndexTool returns exit code 0  
✓ New index dir has > 0 files (verified)  
✓ Index is activated: `data/blacklab_index` exists with content  
✓ Script returns exit code 0

#### Build "Fertig wenn" Validation

```powershell
# Script verifies:
$indexFiles = @(Get-ChildItem -Path $newIndexPath -File -Recurse)
if ($indexFiles.Count -eq 0) {
    exit 1  # Failed
}
Move-Item -Path $newIndexPath -Destination $indexTargetPath  # Activate
# Now data/blacklab_index/ is ready
```

---

## PHASE 2C: Publish Contract (to Production)

### Publish Entry Point

**File:** `scripts/deploy_sync/publish_blacklab_index.ps1` (579 lines, PowerShell)

**Purpose:**  
Upload built index from local staging to production server, validate, and perform atomic swap with backup.

#### Publish Command

```powershell
cd c:\dev\corapan-webapp
.\scripts\deploy_sync\publish_blacklab_index.ps1 `
  -Host "137.248.186.51" `
  -User "root" `
  -Port 22 `
  -DataDir "/srv/webapps/corapan/data" `
  -ConfigDir "/srv/webapps/corapan/app/config/blacklab" `
  [-DryRun]
```

#### Publish Parameters

```
-Host       Default: "137.248.186.51"
            Production server hostname or IP

-User       Default: "root"
            SSH user for remote login

-Port       Default: 22
            SSH port

-DataDir    Default: "/srv/webapps/corapan/data"
            Remote data directory (where blacklab_index lives)

-ConfigDir  Default: "/srv/webapps/corapan/app/config/blacklab"
            Remote BlackLab config directory

-DryRun     Default: $false
            Print commands without executing
```

#### Publish Configuration (Hardcoded in Script)

```powershell
$BLACKLAB_IMAGE = "instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7"
$VALIDATE_PORT = 18092          # Temp container validation port
$PROD_PORT = 8081               # Production BlackLab server port
$MIN_FILES = 10                 # Minimum file count for successful upload
$MIN_SIZE_MB = 50               # Minimum size in MB
```

#### Publish Inputs

**Required Local:**

1. **Staging Index:**
   - **Path:** `data/blacklab_index.new` (from Build phase)
   - **Required:** Must exist and have > MIN_FILES files and > MIN_SIZE_MB size
   - **Checked:** Before upload starts (STEP 1: LOCAL PREFLIGHT)

**Required Remote (pre-existing):**

1. **Remote Data Directory:**
   - **Path:** `/srv/webapps/corapan/data/` (or custom via -DataDir)
   - **Required Subdirs:** Already exist

2. **Remote BlackLab Config:**
   - **Path:** `/srv/webapps/corapan/app/config/blacklab/` (or custom via -ConfigDir)
   - **Required:** `corapan-tsv.blf.yaml` must exist

3. **Remote Tools:**
   - **Docker:** `command -v docker`
   - **curl:** `command -v curl`
   - **tar:** `command -v tar` (or scp fallback)
   - **SSH:** Required (used by -Invoke-SSH calls)

#### Publish Process Overview

**STEP 1: LOCAL PREFLIGHT**
- Count files in `data/blacklab_index.new`
- Calculate size
- Verify > MIN_FILES and > MIN_SIZE_MB
- Exit if fails

**STEP 2: REMOTE CONNECTIVITY & PREREQUISITES**
- SSH connectivity test (hostname query)
- Remote paths exist (`$DataDir`, `$ConfigDir`)
- Remote tools available (docker, curl, tar)

**STEP 3: UPLOAD INDEX TO STAGING**
- Method 1 (Preferred): `tar` + SSH streaming (binary-safe, no temp files)
  ```bash
  tar -cf - -C "local_index" . | ssh user@host "mkdir -p remote_new; tar -xpf - -C remote_new"
  ```
- Method 2 (Fallback): `scp -r` (slower, no streaming)
  ```bash
  scp -r "local_index" "user@host:/remote/path/"
  ```
- **Remote Staging Path:** `{DataDir}/blacklab_index.new`
- **Duration:** 5-15 minutes (typical index size ~500MB-2GB)

**STEP 4: REMOTE VERIFICATION**
- Count files on remote: `find remote_new -type f | wc -l`
- Calculate remote size: `du -sb remote_new`
- Verify > MIN_FILES and > MIN_SIZE_MB
- Exit if fails

**STEP 5: VALIDATE NEW INDEX (CRITICAL GATE)**

- **Start Temporary Validation Container:**
  ```bash
  docker run -d --rm --name bl-validate-new \
    -p 127.0.0.1:18092:8080 \
    -v "/srv/webapps/corapan/data/blacklab_index.new:/data/index/corapan:ro" \
    -v "/srv/webapps/corapan/app/config/blacklab:/etc/blacklab:ro" \
    "instituutnederlandsetaal/blacklab@sha256:..."
  ```

- **Wait for Ready:** Poll `http://127.0.0.1:18092/blacklab-server/` (retry up to 30s)

- **Test Endpoints:**
  1. **Health:** `GET /blacklab-server/?outputformat=json`
     - Expect: 200 OK, valid JSON response
  
  2. **Corpora List:** `GET /blacklab-server/corpora/?outputformat=json`
     - Expect: 200 OK, JSON with key `"corpora"` containing object
     - Critical Check: Must find corpus named `"corapan"`
  
  3. **Corpus Info:** `GET /blacklab-server/corapan?outputformat=json`
     - Expect: 200 OK, JSON with document and token counts
     - Critical Check: `documentCount > 0` OR `count.documents > 0`

- **Cleanup:** Remove validation container (docker rm)

- **Failure:** Exit code 2 (ABORT before swap)

**STEP 6: ATOMIC INDEX SWAP**

- **Create Timestamped Backup:**
  ```bash
  mv /srv/webapps/corapan/data/blacklab_index \
     /srv/webapps/corapan/data/blacklab_index.bak_2026-01-16_120000
  ```

- **Activate New Index:**
  ```bash
  mv /srv/webapps/corapan/data/blacklab_index.new \
     /srv/webapps/corapan/data/blacklab_index
  ```

- **Atomic:** Both commands in single SSH call: `mv old bak && mv new active`

**STEP 7: PRODUCTION SANITY CHECK**

- **Test Production Endpoint:** `GET http://127.0.0.1:8081/blacklab-server/corpora/?outputformat=json`
  - Expect: corpus `"corapan"` present
  - Expect: documentCount + tokenCount > 0

- **Failure Behavior:**
  - Display rollback command to operator
  - Exit code 4 (CRITICAL)
  - Manual rollback required:
    ```bash
    ssh root@host
    mv /srv/webapps/corapan/data/blacklab_index \
       /srv/webapps/corapan/data/blacklab_index.bad_2026-01-16_120000
    mv /srv/webapps/corapan/data/blacklab_index.bak_2026-01-16_120000 \
       /srv/webapps/corapan/data/blacklab_index
    ```

#### Publish Outputs

**Remote:**

1. **Timestamped Backup:**
   - **Path:** `/srv/webapps/corapan/data/blacklab_index.bak_{timestamp}`
   - **Content:** Previous active index (before swap)
   - **Retention:** Manual cleanup (can be deleted after index proven stable)

2. **Active Index:**
   - **Path:** `/srv/webapps/corapan/data/blacklab_index/`
   - **Content:** New built index (after successful validation & swap)

#### Publish Exit Codes

- **0:** Success (index uploaded, validated, swapped, production healthy)
- **1:** Preflight failure
- **2:** Validation container failure
- **3:** Swap failure
- **4:** Production sanity check failure

#### Publish Termination Criteria ("fertig wenn")

✓ STEP 1-2 pass (local preflight, remote connectivity)  
✓ STEP 3 completes (upload finished, file counts match)  
✓ STEP 4 validates remote files  
✓ STEP 5 validates new index (corpus found, documents/tokens > 0)  
✓ STEP 6 completes atomic swap  
✓ STEP 7 validates production (corpus found, documents/tokens > 0)  
✓ Script returns exit code 0  
✓ Timestamped backup exists at `/srv/webapps/corapan/data/blacklab_index.bak_*`

---

## PHASE 2D: Production Build Script (Reference)

### Production Build Entry Point

**File:** `scripts/blacklab/build_blacklab_index_prod.sh` (540 lines, Bash)

**Purpose:**  
Build BlackLab index directly on the production server using TSV files synced from dev.

**IMPORTANT:** This script is **NOT part of the main deployment pipeline** currently. It is provided as a reference for how to build indexes in production if needed. The current recommended approach is: **Build locally → Validate locally → Upload → Validate remotely.**

#### Production Build Command

```bash
cd /srv/webapps/corapan/app
sudo bash scripts/blacklab/build_blacklab_index_prod.sh
```

#### Production Build Parameters (Environment Variables)

```bash
JAVA_XMX              Default: 1400m
JAVA_XMS              Default: 512m
DOCKER_MEM            Default: (unset)  e.g., 2500m
DOCKER_MEMSWAP        Default: (unset)  e.g., 3g
CLEAN_INPUTS          Default: 0        (set to 1 to remove tsv_for_index after build)
```

#### Production Build Inputs

**Remote Paths (Pre-existing):**

1. **TSV Files:**
   - **Path:** `/srv/webapps/corapan/data/tsv/`
   - **Required:** *.tsv files (excluding *_min.tsv)
   - **Source:** Synced from dev via rsync or similar (external to this script)

2. **Metadata:**
   - **Path:** `/srv/webapps/corapan/data/metadata/`
   - **Required:** *.yaml files (one per corpus document)
   - **Source:** Synced from dev (external to this script)

3. **BlackLab Config:**
   - **Path:** `/srv/webapps/corapan/app/config/blacklab/corapan-tsv.blf.yaml`

4. **Docker Image:**
   - **Image:** `instituutnederlandsetaal/blacklab:latest`

#### Production Build Process

Similar to local build, but:

1. **Pulls image as `latest`** (not a specific digest)
2. **Uses higher Java heap by default** (1400m vs dev defaults)
3. **Creates test container** on a free port in range 18080-18150
4. **Validates before swap** (same criteria as local)
5. **Atomic swap** with timestamped backup: `blacklab_index.bak_{timestamp}`
6. **Auto-rollback** on swap failure

#### Production Build Termination Criteria

Same as local build:

✓ Pre-validation passed (file count, size, *.blfi.* files)  
✓ Docker IndexTool build completed (exit 0)  
✓ Post-validation passed (test container queries corpus, documents/tokens > 0)  
✓ Atomic swap completed  
✓ Index backed up to timestamped location  
✓ Script returns exit code 0

---

## PHASE 3A: Export → Build → Publish Contracts Summary

| **Phase** | **Entry Point** | **Command** | **Input** | **Output** | **Exit 0 When** |
|-----------|-----------------|-------------|----------|-----------|-----------------|
| **Export** | `LOKAL/_1_blacklab/blacklab_export.py` or `src/scripts/blacklab_index_creation.py` | `python -m src.scripts.blacklab_index_creation --format tsv` | `media/transcripts/*.json` | `data/blacklab_export/tsv/*.tsv`, `data/blacklab_export/docmeta.jsonl` | All JSON files processed, TSV + docmeta written, exit 0 |
| **Build** | `scripts/blacklab/build_blacklab_index.ps1` | `.\build_blacklab_index.ps1 -Activate` | `data/blacklab_export/tsv/*.tsv`, `data/blacklab_export/docmeta.jsonl`, Docker image | `data/blacklab_index/` (active, index files present) | Index built, verified, activated, exit 0 |
| **Publish** | `scripts/deploy_sync/publish_blacklab_index.ps1` | `.\publish_blacklab_index.ps1 -Host 137.248... -User root` | `data/blacklab_index.new`, SSH access, remote paths | `/srv/webapps/corapan/data/blacklab_index/` (active), timestamped backup | Index uploaded, validated (remote), swapped, production OK, exit 0 |

---

## PHASE 3B: Wrapper Script Parameter List

**Proposed Signature for `LOKAL/_1_blacklab/publish_blacklab.ps1`:**

```powershell
param(
    # Paths & Environment
    [string]$WebappRepoPath = "C:\dev\corapan-webapp",
    
    # Production Server Config
    [string]$ProdHost = "137.248.186.51",
    [string]$ProdUser = "root",
    [int]$SshPort = 22,
    [string]$ProdDataDir = "/srv/webapps/corapan/data",
    [string]$ProdConfigDir = "/srv/webapps/corapan/app/config/blacklab",
    
    # Pipeline Phases
    [switch]$SkipExport,
    [switch]$SkipBuild,
    [switch]$SkipPublish,
    
    # Options
    [switch]$WhatIf,        # Dry-run (print commands only)
    [switch]$Force,         # Don't prompt for confirmations
    [string]$LogPath = "$env:USERPROFILE\Desktop\corapan-publish.log",
    
    # Advanced
    [switch]$SkipBuildBackup,  # Skip backup during build phase
    [switch]$ValidateOnly      # Only run validation, no actual publish
)
```

---

## PHASE 4A: Happy Path Command Sequence

### Scenario: Full Export → Build → Publish

```powershell
# Terminal 1: Export (from anywhere with Python access)
cd C:\dev\corapan-webapp
python -m src.scripts.blacklab_index_creation --format tsv
# Output: data/blacklab_export/tsv/*.tsv + docmeta.jsonl

# Terminal 2: Build (Windows/Dev machine)
cd C:\dev\corapan-webapp
.\scripts\blacklab\build_blacklab_index.ps1
# Output: data/blacklab_index/

# Terminal 3: Publish to Production (Windows/Dev with SSH)
cd C:\dev\corapan-webapp
.\scripts\deploy_sync\publish_blacklab_index.ps1 -Host 137.248.186.51
# Output: /srv/webapps/corapan/data/blacklab_index/ (active), timestamped backup
```

**Total Duration:** ~30-50 minutes (export 5-10min + build 10-20min + publish 10-20min)

---

## PHASE 4B: Top 5 Failure Modes & Troubleshooting

### 1. **Export: No JSON files found**

**Symptom:**  
```
ERROR: No TSV files found in media/transcripts
```

**Cause:**  
`media/transcripts/` directory empty or doesn't exist.

**Check:**
```bash
cd c:\dev\corapan-webapp
dir media\transcripts\
# Should show *.json files
```

**Fix:**
- Ensure JSON files are copied to `media/transcripts/`
- Check JSON v2 format (has "segments" with "words" array)

---

### 2. **Build: "docker pull" fails or image not available**

**Symptom:**
```
ERROR: Failed to pull image!
```

**Cause:**  
- Network issue
- Docker daemon not running
- Image SHA digest incorrect

**Check:**
```powershell
docker ps
docker images
docker pull instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7
```

**Fix:**
- Start Docker Desktop
- Check network connectivity
- Verify image SHA in script matches registry

---

### 3. **Build: OOM (Out of Memory) or Exit Code 137**

**Symptom:**
```
ERROR: Index build KILLED (exit code 137) - OUT OF MEMORY!
```

**Cause:**  
IndexTool Java process killed by system due to memory pressure.

**Check:**
```powershell
docker stats  # Monitor during build
# Look for memory usage approaching system limit
```

**Fix:**
- Reduce JAVA_XMX in prod script (e.g., 1000m instead of 1400m)
- Or: Run on machine with more RAM
- Or: Reduce number of TSV files (--limit flag in export)

---

### 4. **Publish: SSH connection fails**

**Symptom:**
```
[ERROR] SSH connection failed: The network path was not found
```

**Cause:**  
- SSH not installed on Windows (use OpenSSH via Windows Store or Git Bash)
- Host unreachable (firewall, wrong IP)
- Port wrong or firewall blocking SSH port

**Check:**
```powershell
ssh -V
ssh -p 22 root@137.248.186.51 "echo OK"
```

**Fix:**
- Install OpenSSH: `Add-WindowsCapability -Online -Name OpenSSH.Client`
- Verify host/port are correct
- Check firewall rules on production server

---

### 5. **Publish: Validation fails (corpus "corapan" not found)**

**Symptom:**
```
VALIDATION FAILED: Corpus 'corapan' not found in index
```

**Cause:**  
- Index built but corpus ID not set correctly
- BLF config doesn't define "corapan" corpus
- Index files incomplete

**Check:**
```bash
# On prod server:
docker run -it \
  -v /srv/webapps/corapan/data/blacklab_index.new:/data/index:ro \
  -v /srv/webapps/corapan/app/config/blacklab:/config:ro \
  instituutnederlandsetaal/blacklab:latest \
  curl http://localhost:8080/blacklab-server/corpora/

# Check config:
cat /srv/webapps/corapan/app/config/blacklab/corapan-tsv.blf.yaml | grep -A5 "corpusConfig"
```

**Fix:**
- Ensure BLF config has correct corpus ID ("corapan")
- Rebuild index locally with correct config
- Verify docmeta.jsonl was exported and has entries

---

## ADDENDUM: "Build in Production" Audit

### Current State

**Build locations found:**

1. ✅ **Local (Dev Machine):** `scripts/blacklab/build_blacklab_index.ps1`
   - **Status:** Primary recommended approach
   - **Manual:** Operator runs explicitly

2. ⚠️ **Production Server:** `scripts/blacklab/build_blacklab_index_prod.sh`
   - **Status:** Available but NOT automatically triggered
   - **Manual:** Operator must SSH and run explicitly
   - **No Cron/Timer:** No automated schedule found

3. ✅ **App Deployment:** `scripts/deploy_prod.sh`
   - **Status:** GitHub Actions trigger on `push main`
   - **What it does:** Git pull + Docker rebuild + restart
   - **Does NOT rebuild BlackLab index:** Only rebuilds Flask app container

### No Automatic Index Building Found

**Audit Result:**

- ❌ **No Cron Jobs:** No `/etc/cron.d/`, `crontab -l`, or cron references
- ❌ **No Systemd Timers:** No `*.timer` or `*.service` files with scheduled tasks
- ❌ **No GitHub Actions for Index Build:** Deploy workflow only rebuilds Flask app
- ❌ **No Scheduled Index Rebuild:** No trigger on `git push` or time-based schedule

**Conclusion:**  
BlackLab index rebuild is **completely manual** (operator-triggered). This is intentional:
- Index builds are long (10-30 min)
- Requires TSV sync from dev first
- Requires production server resources
- Operator should control when it runs

---

## ADDENDUM: "Build in Production" Removal Plan

### Since automatic "Build in Production" does NOT exist, removal is N/A.

However, if considering future migrations:

1. **What to Keep:**
   - Local build script: `scripts/blacklab/build_blacklab_index.ps1` ✅ (primary)
   - Publish script: `scripts/deploy_sync/publish_blacklab_index.ps1` ✅ (upload + validate)

2. **What to Archive/Remove (if any future auto-build is added):**
   - `scripts/blacklab/build_blacklab_index_prod.sh` (only if we decide "no server-side builds")
   - Any cron/systemd config for auto-rebuild (none currently exist)

3. **Desired Final State:**
   - Operator exports locally (Python module)
   - Operator builds locally (PowerShell)
   - Operator publishes to prod (PowerShell + SSH)
   - Production: Validate + Swap only (no building on prod)

---

## Summary

**All facts collected without code changes.**  
**Ready for local wrapper design in next phase.**

### Key Takeaways

1. **Export Module:** Python `src.scripts.blacklab_index_creation`, outputs TSV + docmeta
2. **Build Tool:** PowerShell `scripts/blacklab/build_blacklab_index.ps1`, Docker-based, local only
3. **Publish Tool:** PowerShell `scripts/deploy_sync/publish_blacklab_index.ps1`, SSH + tar streaming + validation
4. **No Auto-Building:** All steps manual, operator-controlled
5. **Wrapper Opportunity:** Can automate Export → Build → Publish sequence with single PowerShell script in `LOKAL/_1_blacklab/`

