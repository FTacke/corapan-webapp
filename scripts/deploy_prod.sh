#!/bin/bash
# =============================================================================
# CO.RA.PAN Production Deployment Script
# =============================================================================
#
# This script is executed by the GitHub self-hosted runner on the server
# after a push to the main branch. It performs the following steps:
#   1. Fetches latest code from origin/main
#   2. Deploys using docker-compose.prod.yml (runtime-first mounts)
#   3. Verifies container mounts are correct
#   4. Optionally runs the database setup script
#
# Prerequisites:
#   - docker-compose (v1) installed and running
#   - Git repository cloned to /srv/webapps/corapan/app
#   - Runtime directory at /srv/webapps/corapan/runtime/corapan
#   - passwords.env configured in /srv/webapps/corapan/config/
#
# Usage:
#   cd /srv/webapps/corapan/app
#   bash scripts/deploy_prod.sh
#
# IMPORTANT: Production MUST use docker-compose.prod.yml with runtime-first mounts.
# Legacy mounts (/srv/webapps/corapan/{data,media,logs}) are NOT supported.
# =============================================================================

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# Configuration
CONTAINER_NAME="corapan-web-prod"  # Must match container_name in docker-compose.prod.yml
COMPOSE_FILE="docker-compose.prod.yml"

# Paths (on the host)
BASE_DIR="/srv/webapps/corapan"
RUNTIME_DIR="${BASE_DIR}/runtime/corapan"
CONFIG_DIR="${BASE_DIR}/config"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=============================================="
echo "CO.RA.PAN Production Deployment"
echo "=============================================="
echo "Started at: $(date)"
echo ""

# Step 1: Update code from Git
log_info "Fetching latest code from origin/main..."
git fetch origin
git reset --hard origin/main
log_info "Code updated to: $(git rev-parse --short HEAD)"
echo ""

# Step 2: Ensure runtime directories exist (on host)
log_info "Ensuring runtime directories exist at ${RUNTIME_DIR}..."
mkdir -p "${RUNTIME_DIR}/data" "${RUNTIME_DIR}/media" "${RUNTIME_DIR}/logs" "${RUNTIME_DIR}/config"
log_info "Runtime directories ready"
echo ""

# Step 3: Ensure statistics assets are readable by container user
STATS_DIR="${RUNTIME_DIR}/data/public/statistics"
if [ -d "${STATS_DIR}" ]; then
    log_info "Ensuring statistics permissions in ${STATS_DIR}..."
    chmod 755 "${STATS_DIR}" || log_warn "Failed to chmod stats directory"
    find "${STATS_DIR}" -type f -exec chmod 644 {} \; || log_warn "Failed to chmod stats files"
else
    log_warn "Statistics directory not found at ${STATS_DIR}"
fi

# Step 4: Deploy using docker-compose.prod.yml (runtime-first mounts)
# Note: Running from app directory where infra/docker-compose.prod.yml exists
log_info "Deploying via docker-compose -f infra/${COMPOSE_FILE}..."
log_info "Current directory: $(pwd)"

# Try to find docker-compose (v1) or use docker compose (v2 plugin)
if command -v docker-compose &> /dev/null; then
    log_info "Using docker-compose v1 (standalone)"
    docker-compose -f "infra/${COMPOSE_FILE}" up -d --force-recreate --build
elif docker compose version &> /dev/null; then
    log_info "Using docker compose v2 (plugin)"
    docker compose -f "infra/${COMPOSE_FILE}" up -d --force-recreate --build
else
    log_error "Neither docker-compose (v1) nor docker compose (v2) found!"
    exit 1
fi

log_info "Containers started successfully"
echo ""

# Step 5: Wait for container to be ready
log_info "Waiting for container to be ready..."
sleep 10

# Check if container is running
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log_info "Container ${CONTAINER_NAME} is running"
else
    log_error "Container ${CONTAINER_NAME} failed to start!"
    docker logs "${CONTAINER_NAME}" 2>&1 | tail -20
    exit 1
fi
echo ""

# Step 6: Verify runtime-first mounts are correct
log_info "Verifying runtime-first mounts..."
MOUNTS=$(docker inspect "${CONTAINER_NAME}" --format '{{range .Mounts}}{{println .Destination "<-" .Source}}{{end}}' | sort)
echo "${MOUNTS}"

# Check critical mounts
if echo "${MOUNTS}" | grep -q "/app/data <- /srv/webapps/corapan/runtime/corapan/data"; then
    log_info "✓ /app/data mount is correct (runtime-first)"
else
    log_error "✗ /app/data mount is WRONG! Expected: /srv/webapps/corapan/runtime/corapan/data"
    log_error "Actual mounts:"
    echo "${MOUNTS}"
    exit 1
fi

if echo "${MOUNTS}" | grep -q "/app/media <- /srv/webapps/corapan/runtime/corapan/media"; then
    log_info "✓ /app/media mount is correct (runtime-first)"
else
    log_error "✗ /app/media mount is WRONG! Expected: /srv/webapps/corapan/runtime/corapan/media"
    exit 1
fi

if echo "${MOUNTS}" | grep -q "/app/logs <- /srv/webapps/corapan/runtime/corapan/logs"; then
    log_info "✓ /app/logs mount is correct (runtime-first)"
else
    log_error "✗ /app/logs mount is WRONG! Expected: /srv/webapps/corapan/runtime/corapan/logs"
    exit 1
fi

log_info "All mounts verified successfully!"
echo ""

# Step 7: Run database setup (optional - uncomment if needed)
# This creates tables and ensures admin user exists
log_info "Running database setup..."
docker exec "${CONTAINER_NAME}" python scripts/setup_prod_db.py || {
    log_warn "Database setup failed or skipped. Check logs for details."
}
echo ""

# Summary
echo "=============================================="
log_info "Deployment completed successfully!"
echo "=============================================="
echo "Container: ${CONTAINER_NAME}"
echo "Compose File: infra/${COMPOSE_FILE}"
echo "Runtime Root: ${RUNTIME_DIR}"
echo "Commit: $(git rev-parse --short HEAD) (in app/)"
echo "Finished at: $(date)"
echo ""

# Show container status
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

log_info "Verify deployment with: docker inspect ${CONTAINER_NAME} --format '{{range .Mounts}}{{println .Destination \"<-\" .Source}}{{end}}'"
