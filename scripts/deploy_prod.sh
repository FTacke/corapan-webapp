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
#   - Docker installed and running (docker-compose v1)
#   - Git repository cloned on the server (self-hosted runner workspace)
#   - Runtime data/media already present under /srv/webapps/corapan/runtime/corapan
#   - passwords.env configured in /srv/webapps/corapan/config/
#
# Usage:
#   bash scripts/deploy_prod.sh
#
# NOTE: This is a code-only deploy (no data/media sync). Runtime data is not modified.
#
# =============================================================================

set -euo pipefail  # Exit on any error

# Configuration
CONTAINER_NAME="corapan-web-prod"

# Paths (on the host)
RUNTIME_BASE="/srv/webapps/corapan"
ENV_FILE="${RUNTIME_BASE}/config/passwords.env"
RUNTIME_ROOT="${RUNTIME_BASE}/runtime/corapan"
DATA_DIR="${RUNTIME_ROOT}/data"
MEDIA_DIR="${RUNTIME_ROOT}/media"
CONFIG_DIR="${RUNTIME_ROOT}/config"
LOGS_DIR="${RUNTIME_ROOT}/logs"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_DIR="${REPO_ROOT}/infra"
COMPOSE_FILE="${COMPOSE_DIR}/docker-compose.prod.yml"

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

extract_db_password() {
    local url="$1"
    # Expected: scheme://user:pass@host:port/db
    if [[ "${url}" =~ ^[^:]+://[^:]+:([^@]+)@ ]]; then
        echo "${BASH_REMATCH[1]}"
    fi
}

resolve_compose() {
    if [ -n "${DOCKER_COMPOSE_BIN:-}" ] && [ -x "${DOCKER_COMPOSE_BIN}" ]; then
        echo "${DOCKER_COMPOSE_BIN}"
        return 0
    fi
    if command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose"
        return 0
    fi
    for candidate in \
        "/usr/local/bin/docker-compose" \
        "/usr/bin/docker-compose" \
        "/snap/bin/docker-compose" \
        "/usr/local/bin/docker-compose-v1" \
        "/usr/bin/docker-compose-v1"; do
        if [ -x "${candidate}" ]; then
            echo "${candidate}"
            return 0
        fi
    done
    SEARCH_BIN=$(find /usr /snap -maxdepth 4 -type f -name docker-compose 2>/dev/null | head -n 1)
    if [ -n "${SEARCH_BIN}" ] && [ -x "${SEARCH_BIN}" ]; then
        echo "${SEARCH_BIN}"
        return 0
    fi
    return 1
}

echo "=============================================="
echo "CO.RA.PAN Production Deployment"
echo "=============================================="
echo "Started at: $(date)"
echo ""

log_info "Using repo root: ${REPO_ROOT}"
cd "${REPO_ROOT}"

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

    if [ -z "${POSTGRES_PASSWORD:-}" ]; then
        if [ -n "${AUTH_DATABASE_URL:-}" ]; then
            POSTGRES_PASSWORD="$(extract_db_password "${AUTH_DATABASE_URL}")"
        fi
        if [ -z "${POSTGRES_PASSWORD:-}" ] && [ -n "${DATABASE_URL:-}" ]; then
            POSTGRES_PASSWORD="$(extract_db_password "${DATABASE_URL}")"
        fi
        if [ -n "${POSTGRES_PASSWORD:-}" ]; then
            export POSTGRES_PASSWORD
            log_info "Derived POSTGRES_PASSWORD from database URL"
        fi
    fi
else
    log_warn "Environment file not found at ${ENV_FILE} (compose will use shell env/.env)"
fi
echo ""

if [ ! -f "${COMPOSE_FILE}" ]; then
    log_error "Compose file not found: ${COMPOSE_FILE}"
    exit 1
fi

# Step 4: Start services via docker-compose (v1)
log_info "Starting production stack via docker-compose..."
COMPOSE_BIN=$(resolve_compose) || {
    log_error "docker-compose (v1) not found in PATH. Install or add to PATH."
    exit 1
}
cd "${COMPOSE_DIR}"
COMPOSE_CMD=("${COMPOSE_BIN}")
if [ -f "${ENV_FILE}" ]; then
    COMPOSE_CMD+=(--env-file "${ENV_FILE}")
fi
COMPOSE_CMD+=(-f "${COMPOSE_FILE}" up -d --force-recreate)
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
