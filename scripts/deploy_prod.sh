#!/bin/bash
# =============================================================================
# CO.RA.PAN Production Deployment Script
# =============================================================================
#
# This script is executed by the GitHub self-hosted runner on the server
# after a push to the main branch. It performs the following steps:
#   1. Fetches latest code from origin/main
#   2. Loads production secrets for compose variable expansion
#   3. Starts the stack via docker-compose.prod.yml (runtime-first mounts)
#   4. Verifies runtime-first mounts
#   5. Optionally runs the database setup script
#
# Prerequisites:
#   - Docker installed and running
#   - Git repository cloned to /srv/webapps/corapan
#   - Runtime data/media populated via rsync
#   - passwords.env configured in /srv/webapps/corapan/config/
#
# Usage:
#   cd /srv/webapps/corapan
#   bash scripts/deploy_prod.sh
#
# =============================================================================

set -euo pipefail  # Exit on any error

# Configuration
CONTAINER_NAME="corapan-web-prod"

# Paths (on the host)
BASE_DIR="/srv/webapps/corapan"
COMPOSE_FILE="${BASE_DIR}/docker-compose.prod.yml"
ENV_FILE="${BASE_DIR}/config/passwords.env"
RUNTIME_ROOT="${BASE_DIR}/runtime/corapan"
DATA_DIR="${RUNTIME_ROOT}/data"
MEDIA_DIR="${RUNTIME_ROOT}/media"
CONFIG_DIR="${RUNTIME_ROOT}/config"
LOGS_DIR="${RUNTIME_ROOT}/logs"

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

log_info "Changing to deploy root: ${BASE_DIR}"
cd "${BASE_DIR}"

# Step 1: Update code from Git
log_info "Fetching latest code from origin/main..."
git fetch origin
git reset --hard origin/main
log_info "Code updated to: $(git rev-parse --short HEAD)"
echo ""

# Step 2: Load env secrets (for compose variable expansion)
if [ -f "${ENV_FILE}" ]; then
    log_info "Loading environment file: ${ENV_FILE}"
    set -a
    # shellcheck source=/dev/null
    . "${ENV_FILE}"
    set +a
else
    log_warn "Environment file not found at ${ENV_FILE} (compose will use shell env/.env)"
fi
echo ""

# Step 3: Ensure statistics assets are readable by container user
STATS_DIR="${DATA_DIR}/public/statistics"
if [ -d "${STATS_DIR}" ]; then
    log_info "Ensuring statistics permissions in ${STATS_DIR}..."
    chmod 755 "${STATS_DIR}" || log_warn "Failed to chmod stats directory"
    find "${STATS_DIR}" -type f -exec chmod 644 {} \; || log_warn "Failed to chmod stats files"
else
    log_warn "Statistics directory not found at ${STATS_DIR}"
fi

if [ ! -f "${COMPOSE_FILE}" ]; then
    log_error "Compose file not found: ${COMPOSE_FILE}"
    exit 1
fi

# Step 4: Start services via docker-compose (v1)
log_info "Starting production stack via docker-compose..."
COMPOSE_CMD=(docker-compose -f "${COMPOSE_FILE}" up -d --force-recreate)
if [ "${COMPOSE_BUILD:-0}" = "1" ]; then
    COMPOSE_CMD+=(--build)
fi
"${COMPOSE_CMD[@]}"

log_info "Compose stack started successfully"
echo ""

# Step 5: Wait for container to be healthy
log_info "Waiting for container to be ready..."
sleep 5

# Check if container is running
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log_info "Container is running"
else
    log_error "Container failed to start!"
    docker logs "${CONTAINER_NAME}" 2>&1 | tail -20
    exit 1
fi
echo ""

# Step 6: Verify mounts are runtime-first
log_info "Verifying runtime-first mounts..."
MOUNTS=$(docker inspect "${CONTAINER_NAME}" --format '{{range .Mounts}}{{println .Destination " <- " .Source}}{{end}}' | sort)
echo "${MOUNTS}"

EXPECTED_MOUNTS=(
    "/app/data <- ${RUNTIME_ROOT}/data"
    "/app/media <- ${RUNTIME_ROOT}/media"
    "/app/logs <- ${RUNTIME_ROOT}/logs"
    "/app/config <- ${RUNTIME_ROOT}/config"
)

for mount in "${EXPECTED_MOUNTS[@]}"; do
    if ! echo "${MOUNTS}" | grep -Fxq "${mount}"; then
        log_error "Mount mismatch detected: ${mount}"
        exit 1
    fi
done
log_info "Mounts verified"
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
echo "Compose file: ${COMPOSE_FILE}"
echo "Commit: $(git rev-parse --short HEAD)"
echo "Finished at: $(date)"
echo ""

# Show container status
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
