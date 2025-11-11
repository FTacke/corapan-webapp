#!/bin/bash
# Build BlackLab Index from exported TSV/WPL files
# Usage: ./scripts/build_blacklab_index.sh [--format tsv|wpl] [--workers N]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration (all relative paths from project root)
CORAPAN_JSON_DIR="${CORAPAN_JSON_DIR:-media/transcripts}"
EXPORT_DIR="data/blacklab_index/tsv"
INDEX_DIR="data/blacklab_index"
INDEX_DIR_NEW="data/blacklab_index.new"
BLF_CONFIG="config/blacklab/corapan-tsv.blf.yaml"
LOG_FILE="logs/bls/index_build.log"

FORMAT="${1:-tsv}"
WORKERS="${2:-4}"

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log "=== BlackLab Index Build Started ==="
log "Format: $FORMAT, Workers: $WORKERS"
log "Input corpus: $CORAPAN_JSON_DIR"
log "Export dir: $EXPORT_DIR"
log "Index target: $INDEX_DIR"

# Step 1: Verify prerequisites
if [ ! -d "$CORAPAN_JSON_DIR" ]; then
    error "Input directory not found: $CORAPAN_JSON_DIR"
    exit 1
fi

if [ ! -f "$BLF_CONFIG" ]; then
    error "BlackLab config not found: $BLF_CONFIG"
    exit 1
fi

# Step 2: Prepare directories
log "Preparing directories..."
mkdir -p "$INDEX_DIR_NEW"

# Step 3: Check for exported files
if [ ! -d "$EXPORT_DIR" ] || [ -z "$(find "$EXPORT_DIR" -name "*.$FORMAT" -type f)" ]; then
    log "No exported $FORMAT files found. Running export..."
    mkdir -p "$EXPORT_DIR"
    
    python -m src.scripts.blacklab_index_creation \
        --in "$CORAPAN_JSON_DIR" \
        --out "$EXPORT_DIR" \
        --docmeta "$EXPORT_DIR/docmeta.jsonl" \
        --format "$FORMAT" \
        --workers "$WORKERS" \
        2>&1 | tee -a "$LOG_FILE"
else
    log "Using existing exported $FORMAT files"
fi

EXPORT_COUNT=$(find "$EXPORT_DIR" -name "*.$FORMAT" -type f 2>/dev/null | wc -l)
if [ "$EXPORT_COUNT" -eq 0 ]; then
    error "No $FORMAT files found in $EXPORT_DIR"
    exit 1
fi

log "Found $EXPORT_COUNT exported files"

# Step 4: Verify docmeta.jsonl
if [ ! -f "$EXPORT_DIR/docmeta.jsonl" ]; then
    error "docmeta.jsonl not found after export"
    exit 1
fi

DOCMETA_COUNT=$(wc -l < "$EXPORT_DIR/docmeta.jsonl")
log "Document metadata: $DOCMETA_COUNT entries"

# Step 5: Build index
log "Building BlackLab index..."
if ! command -v IndexTool &> /dev/null; then
    error "IndexTool command not found. Is BlackLab installed?"
    error "Install via: apt-get install blacklab-server (Ubuntu/Debian)"
    exit 1
fi

# Build index (format-specific)
if [ "$FORMAT" = "wpl" ]; then
    log "Building index from WPL files..."
    IndexTool create "$INDEX_DIR_NEW" "$EXPORT_DIR"/*.wpl "$BLF_CONFIG" \
        2>&1 | tee -a "$LOG_FILE"
else
    log "Building index from TSV files (with docmeta)..."
    # For TSV, use docmeta.jsonl for metadata
    IndexTool create "$INDEX_DIR_NEW" "$EXPORT_DIR"/*.tsv "$BLF_CONFIG" \
        --docmeta "$EXPORT_DIR/docmeta.jsonl" \
        2>&1 | tee -a "$LOG_FILE"
fi

if [ $? -ne 0 ]; then
    error "Index build failed"
    rm -rf "$INDEX_DIR_NEW"
    exit 1
fi

log "Index build successful"

# Step 6: Atomic index switch
log "Performing atomic index switch..."
if [ -d "$INDEX_DIR" ]; then
    log "Backing up previous index..."
    rm -rf "${INDEX_DIR}.bak" 2>/dev/null || true
    mv "$INDEX_DIR" "${INDEX_DIR}.bak"
else
    log "No previous index to backup"
fi

mv "$INDEX_DIR_NEW" "$INDEX_DIR"
log "Index activated: $INDEX_DIR"

# Step 7: Cleanup (optional)
log "Cleaning up export directory..."
# Note: keep export files for troubleshooting; comment out to auto-clean
# rm -rf "${EXPORT_DIR:?}"/*

# Step 8: Summary
INDEX_SIZE=$(du -sh "$INDEX_DIR" | cut -f1)
TOKEN_COUNT=$(find "$EXPORT_DIR" -name "*.$FORMAT" -exec wc -l {} + | tail -1 | awk '{print $1}')

log "=== Build Complete ==="
log "Index size: $INDEX_SIZE"
log "Estimated tokens: $TOKEN_COUNT"
log "Index directory: $INDEX_DIR"
log "Next: run 'make bls' to start BlackLab Server"

exit 0
