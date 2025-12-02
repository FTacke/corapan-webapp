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
LOG_FILE="${DATA_ROOT}/logs/blacklab_index_build.log"
BLACKLAB_IMAGE="instituutnederlandsetaal/blacklab:latest"

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

# Pull latest image
log "Pulling latest BlackLab image..."
docker pull "$BLACKLAB_IMAGE" 2>&1 | tee -a "$LOG_FILE"

# Run IndexTool
docker run --rm \
    -v "$DATA_ROOT:/data/export:ro" \
    -v "$INDEX_DIR_NEW:/data/index:rw" \
    -v "$APP_ROOT/config/blacklab:/config:ro" \
    "$BLACKLAB_IMAGE" \
    java -Xmx2g -cp '/usr/local/lib/blacklab-tools/*' \
        nl.inl.blacklab.tools.IndexTool create \
            /data/index \
            /data/export/tsv_for_index \
            /config/corapan-tsv.blf.yaml \
            --linked-file-dir /data/export/metadata \
            --threads 2 \
    2>&1 | tee -a "$LOG_FILE"

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    error "Index build failed!"
    rm -rf "$INDEX_DIR_NEW"
    exit 1
fi

# Step 5: Verify new index
if [ ! -d "$INDEX_DIR_NEW" ] || [ -z "$(ls -A "$INDEX_DIR_NEW")" ]; then
    error "New index directory is empty after build"
    exit 1
fi

NEW_INDEX_SIZE=$(du -sh "$INDEX_DIR_NEW" | cut -f1)
log "New index size: $NEW_INDEX_SIZE"

# Step 6: Atomic index switch
log "Performing atomic index switch..."

if [ -d "$INDEX_DIR" ]; then
    log "Backing up previous index..."
    rm -rf "${INDEX_DIR}.bak" 2>/dev/null || true
    mv "$INDEX_DIR" "${INDEX_DIR}.bak"
    log "Previous index backed up to ${INDEX_DIR}.bak"
else
    log "No previous index to backup"
fi

mv "$INDEX_DIR_NEW" "$INDEX_DIR"
log "New index activated: $INDEX_DIR"

# Step 7: Show summary
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
