#!/usr/bin/env bash
# =============================================================================
# CO.RA.PAN Production BlackLab Index Build Script
# =============================================================================
#
# Builds a BlackLab index from TSV files synchronized from the dev environment.
# This script is designed to run on the production server.
#
# Prerequisites:
#   - TSV files in /srv/webapps/corapan/data/tsv
#   - Metadata files in /srv/webapps/corapan/data/metadata
#   - BlackLab Docker image: instituutnederlandsetaal/blacklab:latest
#   - BlackLab config: /srv/webapps/corapan/app/config/blacklab/corapan-tsv.blf.yaml
#
# Usage:
#   sudo bash /srv/webapps/corapan/app/scripts/blacklab/build_blacklab_index_prod.sh
#
# After building, run run_bls_prod.sh to restart the BlackLab server.
#
# =============================================================================

set -euo pipefail

# Configuration
DATA_ROOT="/srv/webapps/corapan/data"
APP_ROOT="/srv/webapps/corapan/app"
TSV_DIR="${DATA_ROOT}/tsv"
TSV_FOR_INDEX="${DATA_ROOT}/tsv_for_index"
INDEX_DIR="${DATA_ROOT}/blacklab_index"
INDEX_DIR_NEW="${DATA_ROOT}/blacklab_index.new"
METADATA_DIR="${DATA_ROOT}/metadata"
BLF_CONFIG="${APP_ROOT}/config/blacklab/corapan-tsv.blf.yaml"
TIMESTAMP=$(date +%F_%H%M%S)
LOG_FILE="${DATA_ROOT}/logs/blacklab_build_${TIMESTAMP}.log"
BLACKLAB_IMAGE="instituutnederlandsetaal/blacklab:latest"
TEST_CONTAINER_NAME="corapan-blacklab-test-${TIMESTAMP}"
TEST_PORT=18082

# Java Memory Settings (configurable, defaults for low-RAM hosts)
JAVA_XMX="${JAVA_XMX:-1400m}"
JAVA_XMS="${JAVA_XMS:-512m}"

# Optional Docker Memory Limits (disabled by default)
DOCKER_MEM="${DOCKER_MEM:-}"          # e.g. 2500m or 3g
DOCKER_MEMSWAP="${DOCKER_MEMSWAP:-}"  # e.g. 3g or 0 to disable swap limit
DOCKER_LIMITS=()
[ -n "$DOCKER_MEM" ] && DOCKER_LIMITS+=(--memory "$DOCKER_MEM")
[ -n "$DOCKER_MEMSWAP" ] && DOCKER_LIMITS+=(--memory-swap "$DOCKER_MEMSWAP")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${GREEN}${msg}${NC}"
    echo "${msg}" >> "$LOG_FILE" 2>/dev/null || true
}

error() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1"
    echo -e "${RED}${msg}${NC}" >&2
    echo "${msg}" >> "$LOG_FILE" 2>/dev/null || true
}

warn() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] WARN: $1"
    echo -e "${YELLOW}${msg}${NC}"
    echo "${msg}" >> "$LOG_FILE" 2>/dev/null || true
}

# Ensure log directory exists
mkdir -p "${DATA_ROOT}/logs"

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

echo "=============================================="
echo "CO.RA.PAN Production BlackLab Index Build"
echo "=============================================="
log "=== BlackLab Index Build Started ==="

# Step 1: Verify prerequisites
log "Verifying prerequisites..."

if [ ! -d "$TSV_DIR" ]; then
    error "TSV directory not found: $TSV_DIR"
    exit 1
fi

if [ ! -d "$METADATA_DIR" ]; then
    error "Metadata directory not found: $METADATA_DIR"
    exit 1
fi

if [ ! -f "$BLF_CONFIG" ]; then
    error "BlackLab config not found: $BLF_CONFIG"
    exit 1
fi

TSV_COUNT=$(find "$TSV_DIR" -maxdepth 1 -type f -name '*.tsv' ! -name '*_min.tsv' | wc -l)
if [ "$TSV_COUNT" -eq 0 ]; then
    error "No TSV files found in $TSV_DIR"
    exit 1
fi
log "Found $TSV_COUNT TSV files to index"

METADATA_COUNT=$(find "$METADATA_DIR" -maxdepth 1 -type f -name '*.yaml' | wc -l)
log "Found $METADATA_COUNT metadata files"

# Step 2: Prepare tsv_for_index directory
log "Preparing tsv_for_index directory..."
rm -rf "$TSV_FOR_INDEX"
mkdir -p "$TSV_FOR_INDEX"

# Copy TSV files (excluding *_min.tsv test files)
find "$TSV_DIR" -maxdepth 1 -type f -name '*.tsv' ! -name '*_min.tsv' -exec cp {} "$TSV_FOR_INDEX/" \;

TSV_FOR_INDEX_COUNT=$(find "$TSV_FOR_INDEX" -maxdepth 1 -type f -name '*.tsv' | wc -l)
log "Copied $TSV_FOR_INDEX_COUNT TSV files to $TSV_FOR_INDEX"

# Step 3: Prepare new index directory
log "Preparing new index directory..."
rm -rf "$INDEX_DIR_NEW"
mkdir -p "$INDEX_DIR_NEW"

# Step 4: Build index using Docker
log "Building BlackLab index (this may take a while)..."
log "Image: $BLACKLAB_IMAGE"
log "Config: $BLF_CONFIG"
log "Java heap: -Xms${JAVA_XMS} -Xmx${JAVA_XMX}"
if [ -n "$DOCKER_MEM" ]; then
    log "Docker memory limit: ${DOCKER_MEM}"
    [ -n "$DOCKER_MEMSWAP" ] && log "Docker memory+swap limit: ${DOCKER_MEMSWAP}"
fi

# Pull latest image
log "Pulling latest BlackLab image..."
docker pull "$BLACKLAB_IMAGE" 2>&1 | tee -a "$LOG_FILE"

# Run IndexTool
docker run --rm "${DOCKER_LIMITS[@]}" \
    -v "$DATA_ROOT:/data/export:ro" \
    -v "$INDEX_DIR_NEW:/data/index:rw" \
    -v "$APP_ROOT/config/blacklab:/config:ro" \
    "$BLACKLAB_IMAGE" \
    java -Xms"${JAVA_XMS}" -Xmx"${JAVA_XMX}" -cp '/usr/local/lib/blacklab-tools/*' \
        nl.inl.blacklab.tools.IndexTool create \
            /data/index \
            /data/export/tsv_for_index \
            /config/corapan-tsv.blf.yaml \
            --linked-file-dir /data/export/metadata \
            --threads 2 \
    2>&1 | tee -a "$LOG_FILE"

# Capture the exit code of docker run, not tee
RC=${PIPESTATUS[0]}
if [ "$RC" -ne 0 ]; then
    if [ "$RC" -eq 137 ]; then
        error "Index build KILLED (exit code 137) - OUT OF MEMORY!"
        error "The container was killed by Docker/OOM killer."
        error "Try reducing JAVA_XMX (current: ${JAVA_XMX}) or increase system RAM."
        error "Example: JAVA_XMX=1000m bash $0"
    else
        error "Index build failed with exit code $RC"
    fi
    rm -rf "$INDEX_DIR_NEW"
    exit 1
fi

# Step 5: Pre-validation of new index
log "Validating new index structure..."

# Check directory exists and is not empty
if [ ! -d "$INDEX_DIR_NEW" ]; then
    error "New index directory does not exist: $INDEX_DIR_NEW"
    exit 1
fi

if [ -z "$(ls -A "$INDEX_DIR_NEW")" ]; then
    error "New index directory is empty after build"
    exit 1
fi

# Check minimum file count (should have more than 20 files for a proper index)
FILE_COUNT=$(find "$INDEX_DIR_NEW" -type f | wc -l)
if [ "$FILE_COUNT" -lt 20 ]; then
    error "New index has too few files: $FILE_COUNT (expected > 20)"
    rm -rf "$INDEX_DIR_NEW"
    exit 1
fi
log "File count validation passed: $FILE_COUNT files"

# Check minimum size (should be at least 50MB)
SIZE_MB=$(du -sm "$INDEX_DIR_NEW" | cut -f1)
if [ "$SIZE_MB" -lt 50 ]; then
    error "New index is too small: ${SIZE_MB}MB (expected > 50MB)"
    rm -rf "$INDEX_DIR_NEW"
    exit 1
fi
log "Size validation passed: ${SIZE_MB}MB"

# Check for essential BlackLab index files (*.blfi.*)
BLFI_COUNT=$(find "$INDEX_DIR_NEW" -type f -name '*.blfi.*' | wc -l)
if [ "$BLFI_COUNT" -eq 0 ]; then
    error "No BlackLab index files (*.blfi.*) found in new index"
    rm -rf "$INDEX_DIR_NEW"
    exit 1
fi
log "BlackLab index files validation passed: $BLFI_COUNT *.blfi.* files found"

NEW_INDEX_SIZE=$(du -sh "$INDEX_DIR_NEW" | cut -f1)
log "New index size: $NEW_INDEX_SIZE"

# Step 6: Post-validation with test container
log "Running post-validation with temporary BlackLab server..."

# Start temporary test container on different port
# Use the same Tomcat-based setup as production (not the standalone Java command)
log "Starting test container: $TEST_CONTAINER_NAME on port $TEST_PORT"
docker run -d --rm \
    --name "$TEST_CONTAINER_NAME" \
    -p "127.0.0.1:${TEST_PORT}:8080" \
    -e JAVA_TOOL_OPTIONS="-Xmx1g -Xms512m" \
    -v "$INDEX_DIR_NEW:/data/index/corapan:ro" \
    -v "$APP_ROOT/config/blacklab:/etc/blacklab:ro" \
    "$BLACKLAB_IMAGE" \
    > /dev/null 2>&1

# Wait for test container to be ready
log "Waiting for test container to become ready..."
TEST_READY=false
for i in {1..30}; do
    if curl -s -f "http://localhost:${TEST_PORT}/blacklab-server/" > /dev/null 2>&1; then
        TEST_READY=true
        break
    fi
    sleep 2
done

# Query corpus information
VALIDATION_PASSED=false
if [ "$TEST_READY" = true ]; then
    log "Test container is ready, querying corpus information..."
    CORPUS_ID="corapan"
    CORPORA_URL="http://localhost:${TEST_PORT}/blacklab-server/?outputformat=json"
    CORPUS_URL="http://localhost:${TEST_PORT}/blacklab-server/${CORPUS_ID}?outputformat=json"
    log "Validation URL (corpora list): $CORPORA_URL"

    CORPORA_LIST_JSON=$(curl -fsS "$CORPORA_URL" 2>/dev/null || echo "")
    if [ -n "$CORPORA_LIST_JSON" ]; then
        CORPUS_KEYS=$(python3 - <<'PY'
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    print("")
    sys.exit(0)
corpora = data.get("corpora", {})
if isinstance(corpora, dict):
    print(",".join(corpora.keys()))
else:
    print("")
PY
        <<< "$CORPORA_LIST_JSON" 2>/dev/null || true)
        if [ -n "$CORPUS_KEYS" ]; then
            log "Corpora list keys: $CORPUS_KEYS"
            # Detect wrong corpus id early
            if ! printf '%s' "$CORPUS_KEYS" | tr ',' '\n' | grep -qx "$CORPUS_ID"; then
                warn "Requested CORPUS_ID '$CORPUS_ID' not found in corpora list keys"
            fi
        else
            warn "Corpora list keys: (none parsed)"
        fi
    else
        warn "Corpora list response empty"
    fi

    log "Validation URL (corpus info): $CORPUS_URL"
    CORPUS_INFO=$(curl -fsS "$CORPUS_URL" 2>/dev/null || echo "")
    if [ -z "$CORPUS_INFO" ]; then
        warn "Corpus info response empty"
    fi

    # Parse document and token counts (accept count.* or legacy top-level fields)
    PARSE_RESULT=$(python3 - <<'PY'
import json, sys
doc = 0
tok = 0
doc_path = "(not found)"
tok_path = "(not found)"
try:
    data = json.load(sys.stdin)
except Exception:
    print("0|(parse failed)|0|(parse failed)")
    sys.exit(0)

if isinstance(data, dict):
    count = data.get("count") if isinstance(data.get("count"), dict) else None
    if isinstance(count, dict) and "documents" in count:
        try:
            doc = int(count.get("documents", 0))
        except Exception:
            doc = 0
        doc_path = "count.documents"
    elif "documentCount" in data:
        try:
            doc = int(data.get("documentCount", 0))
        except Exception:
            doc = 0
        doc_path = "documentCount"

    if isinstance(count, dict) and "tokens" in count:
        try:
            tok = int(count.get("tokens", 0))
        except Exception:
            tok = 0
        tok_path = "count.tokens"
    elif "tokenCount" in data:
        try:
            tok = int(data.get("tokenCount", 0))
        except Exception:
            tok = 0
        tok_path = "tokenCount"

print(f"{doc}|{doc_path}|{tok}|{tok_path}")
PY
        <<< "$CORPUS_INFO" 2>/dev/null || echo "0|(parse failed)|0|(parse failed)")

    IFS='|' read -r DOC_COUNT DOC_PATH TOKEN_COUNT TOKEN_PATH <<< "$PARSE_RESULT"
    log "Parsed counts: documents=$DOC_COUNT (path: $DOC_PATH), tokens=$TOKEN_COUNT (path: $TOKEN_PATH)"

    if [ "$DOC_COUNT" -gt 0 ] || [ "$TOKEN_COUNT" -gt 0 ]; then
        VALIDATION_PASSED=true
        log "Post-validation passed: Index is queryable and contains data"
        if [ "$DOC_COUNT" -eq 0 ] || [ "$TOKEN_COUNT" -eq 0 ]; then
            warn "Post-validation warning: one of the counts is 0 (documents=$DOC_COUNT, tokens=$TOKEN_COUNT)"
        fi
    else
        error "Post-validation failed: Index has 0 documents and 0 tokens"
    fi
else
    error "Test container did not become ready within timeout"
fi

# Stop test container
log "Stopping test container..."
docker stop "$TEST_CONTAINER_NAME" > /dev/null 2>&1 || true

# Exit if post-validation failed
if [ "$VALIDATION_PASSED" = false ]; then
    error "Post-validation failed - index is not valid"
    TS=$(date +%F_%H%M%S)
    FAILED="${INDEX_DIR_NEW}.failed_${TS}"
    if [ -d "$INDEX_DIR_NEW" ]; then
        mv "$INDEX_DIR_NEW" "$FAILED"
        error "Preserved failed index at: $FAILED"
    else
        error "Failed index directory missing; nothing to preserve"
    fi
    exit 1
fi

# Step 7: Atomic index switch with timestamped backup
# Step 7: Atomic index switch with timestamped backup
log "Performing atomic index switch..."

BACKUP_DIR="${INDEX_DIR}.bak_${TIMESTAMP}"

if [ -d "$INDEX_DIR" ]; then
    log "Backing up current index to timestamped backup..."
    # Remove old non-timestamped backup if it exists
    rm -rf "${INDEX_DIR}.bak" 2>/dev/null || true
    
    # Create timestamped backup
    mv "$INDEX_DIR" "$BACKUP_DIR"
    log "Current index backed up to $BACKUP_DIR"
else
    log "No previous index to backup"
fi

# Perform the swap
mv "$INDEX_DIR_NEW" "$INDEX_DIR"
log "New index activated: $INDEX_DIR"

# Verify the swap was successful
if [ ! -d "$INDEX_DIR" ] || [ -z "$(ls -A "$INDEX_DIR")" ]; then
    error "CRITICAL: Index swap failed - index directory is missing or empty!"
    
    # Attempt rollback if backup exists
    if [ -d "$BACKUP_DIR" ]; then
        error "Attempting rollback to backup..."
        mv "$BACKUP_DIR" "$INDEX_DIR"
        if [ -d "$INDEX_DIR" ] && [ -n "$(ls -A "$INDEX_DIR")" ]; then
            warn "Rollback successful - previous index restored"
        else
            error "CRITICAL: Rollback failed - manual intervention required!"
        fi
    fi
    exit 1
fi

log "Index swap verified successfully"

# Step 8: Cleanup
log "Cleaning up temporary directories..."

# Optional: Remove tsv_for_index (opt-in via CLEAN_INPUTS=1)
CLEAN_INPUTS="${CLEAN_INPUTS:-0}"
if [ "$CLEAN_INPUTS" = "1" ]; then
    log "Removing tsv_for_index (CLEAN_INPUTS=1)"
    rm -rf "$TSV_FOR_INDEX"
    log "Removed temporary tsv_for_index directory"
else
    log "Keeping tsv_for_index (set CLEAN_INPUTS=1 to remove)"
fi

# Keep the timestamped backup for safety (can be removed manually later)
log "Timestamped backup preserved at: $BACKUP_DIR"
log "You can remove it manually once the new index is confirmed stable"

# Step 9: Show summary
INDEX_SIZE=$(du -sh "$INDEX_DIR" | cut -f1)

echo ""
echo "=============================================="
log "Index build completed successfully!"
echo "=============================================="
echo "Index location: $INDEX_DIR"
echo "Index size: $INDEX_SIZE"
echo "TSV files indexed: $TSV_FOR_INDEX_COUNT"
echo "Log file: $LOG_FILE"
echo ""
log "Next step: Run scripts/blacklab/run_bls_prod.sh to restart BlackLab server"
