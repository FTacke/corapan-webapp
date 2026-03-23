#!/usr/bin/env bash
# =============================================================================
# CO.RA.PAN Production DB Public Setup Script
# =============================================================================
#
# Verifies and sets up the public stats DB directory containing SQLite
# statistics databases. These files are synchronized from the dev environment
# and used read-only by the webapp.
#
# The public DB directory contains:
#   - stats_files.db
#   - stats_country.db
#
# Prerequisites:
#   - data/db/public/ directory synchronized from dev
#   - SQLite database files must be valid
#
# Usage:
#   sudo bash /srv/webapps/corapan/app/scripts/ops/setup_public_db.sh
#
# =============================================================================

set -euo pipefail

# Configuration
DATA_ROOT="/srv/webapps/corapan/data"
PUBLIC_DB_DIR="${DATA_ROOT}/db/public"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo "=============================================="
echo "CO.RA.PAN Production DB Public Setup"
echo "=============================================="
log "Verifying database directories..."

# Step 1: Check public DB directory
if [ ! -d "$PUBLIC_DB_DIR" ]; then
    warn "Creating public DB directory..."
    mkdir -p "$PUBLIC_DB_DIR"
fi

# Step 2: Check for required files
REQUIRED_DBS=("stats_files.db" "stats_country.db")
MISSING_DBS=()

for db in "${REQUIRED_DBS[@]}"; do
    if [ ! -f "${PUBLIC_DB_DIR}/${db}" ]; then
        MISSING_DBS+=("$db")
    fi
done

if [ ${#MISSING_DBS[@]} -gt 0 ]; then
    warn "Missing database files in public DB directory:"
    for db in "${MISSING_DBS[@]}"; do
        warn "  - $db"
    done
    warn "These files need to be synchronized from the dev environment"
    warn "Run: rsync -avz dev:/path/to/data/db/public/ $PUBLIC_DB_DIR/"
else
    log "All required database files present"
fi

# Step 3: Verify file integrity (basic check)
for db in "${REQUIRED_DBS[@]}"; do
    if [ -f "${PUBLIC_DB_DIR}/${db}" ]; then
        # Check if it's a valid SQLite file
        if file "${PUBLIC_DB_DIR}/${db}" | grep -q "SQLite"; then
            SIZE=$(du -h "${PUBLIC_DB_DIR}/${db}" | cut -f1)
            log "  ✓ ${db} ($SIZE) - valid SQLite database"
        else
            error "  ✗ ${db} - not a valid SQLite database"
        fi
    fi
done

# Step 4: Set permissions
log "Setting file permissions..."
chown -R root:root "$PUBLIC_DB_DIR" 2>/dev/null || warn "Could not change ownership (may need sudo)"
chmod -R 644 "$PUBLIC_DB_DIR"/*.db 2>/dev/null || true
chmod 755 "$PUBLIC_DB_DIR"

# Summary
echo ""
echo "=============================================="
log "DB Public setup complete!"
echo "=============================================="
echo "Public DB directory: $PUBLIC_DB_DIR"
echo "Files in public DB directory:"
ls -lah "$PUBLIC_DB_DIR"/ 2>/dev/null || echo "(empty)"
echo ""

if [ ${#MISSING_DBS[@]} -gt 0 ]; then
    warn "Some files are missing - sync from dev environment required"
    exit 1
fi
