#!/usr/bin/env bash
# =============================================================================
# CO.RA.PAN Production BlackLab Backup Retention Script
# =============================================================================
#
# Applies backup retention policy on production server.
# Analyzes existing backups, logs KEEP/DELETE decisions, and optionally removes old backups.
#
# Prerequisites:
#   - BlackLab backups already exist in the data directory (created by publish script swap)
#
# Usage:
#   bash /srv/webapps/corapan/app/scripts/blacklab/retain_blacklab_backups_prod.sh
#   BLACKLAB_RETENTION_DELETE=1 BLACKLAB_KEEP_BACKUPS=5 bash ...
#
# Configuration (environment variables):
#   BLACKLAB_KEEP_BACKUPS=3              # How many backups to keep (default: 3)
#   BLACKLAB_RETENTION_DELETE=0          # 0 = report only, 1 = actually delete (default: 0)
#   BLACKLAB_RETENTION_OLDER_THAN_DAYS=  # Optional: only delete if older than N days
#
# Environment (injected by publish script):
#   DATA_ROOT (optional, default: /srv/webapps/corapan/data)
#
# Exit Codes:
#   0 = Success (retention applied/analyzed)
#   1 = Error (missing directory, permission issues)
#
# =============================================================================

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_ROOT="${DATA_ROOT:-/srv/webapps/corapan/data}"

TIMESTAMP=$(date +%F_%H%M%S)
LOG_FILE="${DATA_ROOT}/logs/blacklab_retention_${TIMESTAMP}.log"

# Backup Retention Configuration (opt-in, default: report-only)
# These match the schema produced by publish_blacklab_index.ps1 STEP 6:
#   Primary:   blacklab_index.bak_YYYY-MM-DD_HHMMSS  (current schema from STEP 6)
#   Legacy:    blacklab_index.backup_*               (historical backups)
: "${BLACKLAB_KEEP_BACKUPS:=3}"          # how many backups to retain
: "${BLACKLAB_RETENTION_DELETE:=0}"      # 0 = report only, 1 = actually delete
: "${BLACKLAB_RETENTION_OLDER_THAN_DAYS:=}"  # optional: only delete if older than N days

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# LOGGING
# ============================================================================

mkdir -p "$(dirname "$LOG_FILE")"

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

# ============================================================================
# MAIN EXECUTION
# ============================================================================

echo "=============================================="
echo "CO.RA.PAN BackLab Backup Retention"
echo "=============================================="
log "=== Backup Retention Started ==="

# Verify data directory exists
if [ ! -d "$DATA_ROOT" ]; then
    error "Data root directory does not exist: $DATA_ROOT"
    exit 1
fi

log "Data root: $DATA_ROOT"
log "Keep backups: $BLACKLAB_KEEP_BACKUPS"
log "Delete enabled: $BLACKLAB_RETENTION_DELETE"
if [ -n "$BLACKLAB_RETENTION_OLDER_THAN_DAYS" ]; then
    log "Age filter: $BLACKLAB_RETENTION_OLDER_THAN_DAYS days"
fi

# Find all backup directories matching known patterns
local_backups=()

# Collect all matching backup directories
# Pattern source: scripts/deploy_sync/publish_blacklab_index.ps1 STEP 6
#   Creates: blacklab_index.bak_YYYY-MM-DD_HHMMSS
#   Also matches legacy: blacklab_index.backup_* (if any)
# Never matches: blacklab_index (active) or blacklab_index.new (staging)
if [ -d "$DATA_ROOT" ]; then
    while IFS= read -r -d '' dir; do
        local_backups+=("$dir")
    done < <(find "$DATA_ROOT" -maxdepth 1 -type d \
        \( -name 'blacklab_index.bak_*' -o -name 'blacklab_index.backup_*' \) \
        -print0 2>/dev/null | sort -z)
fi

backup_count=${#local_backups[@]}

# If no backups found, nothing to do
if [ "$backup_count" -eq 0 ]; then
    log "[RETENTION] No backup directories found in $DATA_ROOT"
    echo ""
    echo "=============================================="
    log "Backup retention completed (no backups found)"
    echo "=============================================="
    exit 0
fi

log "[RETENTION] Found $backup_count backup(s)"

# Sort by mtime (newest first)
sorted_backups=()
while IFS= read -r dir; do
    sorted_backups+=("$dir")
done < <(printf '%s\n' "${local_backups[@]}" | while read -r dir; do
    stat -c "%Y %n" "$dir" 2>/dev/null || echo "0 $dir"
done | sort -rn | cut -d' ' -f2-)

# Determine which ones to keep and which to delete
keep_cnt=0
delete_cnt=0

for i in "${!sorted_backups[@]}"; do
    dir="${sorted_backups[$i]}"
    dir_name=$(basename "$dir")
    
    if [ "$i" -lt "$BLACKLAB_KEEP_BACKUPS" ]; then
        keep_cnt=$((keep_cnt + 1))
        log "[RETENTION] KEEP:   $dir_name"
    else
        # Check age filter if configured
        if [ -n "$BLACKLAB_RETENTION_OLDER_THAN_DAYS" ] && [ "$BLACKLAB_RETENTION_OLDER_THAN_DAYS" -gt 0 ]; then
            mtime=$(stat -c %Y "$dir" 2>/dev/null || echo 0)
            now=$(date +%s)
            age_days=$(( (now - mtime) / 86400 ))
            
            if [ "$age_days" -lt "$BLACKLAB_RETENTION_OLDER_THAN_DAYS" ]; then
                log "[RETENTION] SKIP:   $dir_name (age: ${age_days}d < ${BLACKLAB_RETENTION_OLDER_THAN_DAYS}d)"
                keep_cnt=$((keep_cnt + 1))
                continue
            fi
        fi
        
        delete_cnt=$((delete_cnt + 1))
        local delete_marker="(dry-run)"
        if [ "$BLACKLAB_RETENTION_DELETE" = "1" ]; then
            delete_marker=""
            if rm -rf "$dir" 2>/dev/null; then
                log "[RETENTION] DELETE: $dir_name"
            else
                error "[RETENTION] Failed to delete $dir_name"
            fi
        else
            log "[RETENTION] DELETE: $dir_name $delete_marker"
        fi
    fi
done

# Summary
local mode="dry-run"
[ "$BLACKLAB_RETENTION_DELETE" = "1" ] && mode="executed"

log "[RETENTION] Summary: keep=$keep_cnt, delete=$delete_cnt, mode=$mode"
log "[RETENTION] path: $DATA_ROOT"

echo ""
echo "=============================================="
log "Backup retention completed successfully"
echo "=============================================="
echo "Backups kept:  $keep_cnt"
echo "Candidates:    $delete_cnt"
echo "Mode:          $mode"
echo "Log:           $LOG_FILE"
echo ""

exit 0
