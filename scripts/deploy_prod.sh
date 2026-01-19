#!/bin/bash
# =============================================================================
# CO.RA.PAN Production Deployment Script
# =============================================================================
#
# This script is executed by the GitHub self-hosted runner on the server
# after a push to the main branch. It performs the following steps:
#   1. Fetches latest code from origin/main
#   2. Builds the Docker image
#   3. Stops and removes the old container
#   4. Starts a new container with the configured volumes
#   5. Optionally runs the database setup script
#
# Prerequisites:
#   - Docker installed and running
#   - Git repository cloned to /srv/webapps/corapan/app
#   - Data/media directories populated via rsync
#   - passwords.env configured in /srv/webapps/corapan/config/
#
# Usage:
#   cd /srv/webapps/corapan/app
#   bash scripts/deploy_prod.sh
#
# =============================================================================

set -euo pipefail

# DEBUG (temporary): prove which deploy script revision actually runs
echo "[DEBUG] deploy_prod.sh path: $0"
echo "[DEBUG] deploy_prod.sh sha256:"
sha256sum "$0"
echo ""

# Configuration
BASE_DIR="/srv/webapps/corapan"
APP_DIR="${BASE_DIR}/app"
RUNTIME_DIR="${BASE_DIR}/runtime/corapan"
ENV_FILE="${BASE_DIR}/config/passwords.env"
COMPOSE_FILE="${APP_DIR}/infra/docker-compose.prod.yml"
CONTAINER_NAME="corapan-web-prod"
LEGACY_CONTAINER="corapan-webapp"
HEALTH_URL="http://127.0.0.1:6000/health"

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

cd "${APP_DIR}"

# Step 1: Update code from Git
log_info "Fetching latest code from origin/main..."
git fetch origin
git reset --hard origin/main
log_info "Code updated to: $(git rev-parse --short HEAD)"
echo ""

# Step 2: Remove legacy container if present (avoid port conflicts)
log_info "Removing legacy container if present..."
if docker ps --format '{{.Names}}' | grep -qx "${LEGACY_CONTAINER}"; then
    docker rm -f "${LEGACY_CONTAINER}"
    log_info "Removed legacy container: ${LEGACY_CONTAINER}"
else
    log_info "Legacy container not running"
fi
echo ""

# Step 3: Start via docker-compose (runtime-first)
log_info "Starting production stack via docker-compose..."
docker-compose --env-file "${ENV_FILE}" \
  -f "${COMPOSE_FILE}" up -d --force-recreate --build
echo ""

# Step 4: Verify container is running
log_info "Verifying container is running..."
if docker ps --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
    log_info "Container is running: ${CONTAINER_NAME}"
else
    log_error "Container ${CONTAINER_NAME} is not running"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    exit 1
fi
echo ""

# Step 5: Verify runtime-first mounts
# NOTE: Skip in CI environments (GitHub Actions runner / CI), because host bind paths
# like /srv/webapps/... may not exist there and mount verification would false-fail.
log_info "Verifying runtime-first mounts..."

mount_dests="$(docker inspect "${CONTAINER_NAME}" --format '{{range .Mounts}}{{println .Destination}}{{end}}' \
  | tr -d '\r' | sort)"

required_dests=(
  "/app/data"
  "/app/media"
  "/app/logs"
  "/app/config"
)

missing=0
for d in "${required_dests[@]}"; do
  if ! printf '%s\n' "${mount_dests}" | grep -Fqx "${d}"; then
    log_error "Missing mount destination: ${d}"
    missing=1
  fi
done

if [ "${missing}" -ne 0 ]; then
  log_error "Mount destinations mismatch. Actual mount destinations:"
  printf '%s\n' "${mount_dests}"
  exit 1
fi

# Minimal write proof (permissions)
docker exec "${CONTAINER_NAME}" bash -lc 'set -e; touch /app/data/stats_temp/.deploy_write_test && rm -f /app/data/stats_temp/.deploy_write_test'

log_info "Runtime-first mounts verified"
echo ""

# Step 6: Health check (wait/retry)
log_info "Checking health endpoint (with retries)..."

max_tries=60
sleep_s=2

for i in $(seq 1 "${max_tries}"); do
  # If container vanished or restarted, surface it early
  if ! docker ps --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
    log_error "Container ${CONTAINER_NAME} is not running during health wait"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    docker logs --tail 200 "${CONTAINER_NAME}" || true
    exit 1
  fi

  # Prefer docker health status if present
  health_status="$(docker inspect "${CONTAINER_NAME}" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null || echo "unknown")"
  log_info "Health wait ${i}/${max_tries} (docker health=${health_status})"

  # External check
  if curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
    log_info "Health check ok"
    echo ""
    break
  fi

  # If docker health says unhealthy, fail fast with diagnostics
  if [ "${health_status}" = "unhealthy" ]; then
    log_error "Container reported unhealthy"
    docker inspect "${CONTAINER_NAME}" --format '{{json .State.Health}}' | head -c 4000 || true
    docker logs --tail 200 "${CONTAINER_NAME}" || true
    exit 1
  fi

  sleep "${sleep_s}"
done

# If we exhausted retries, fail with diagnostics
if ! curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
  log_error "Health check failed after $((max_tries * sleep_s))s: ${HEALTH_URL}"
  docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
  docker logs --tail 200 "${CONTAINER_NAME}" || true
  exit 1
fi

echo ""

# Summary
echo "=============================================="
log_info "Deployment completed successfully!"
echo "=============================================="
echo "Container: ${CONTAINER_NAME}"
echo "Commit: $(git rev-parse --short HEAD)"
echo "Finished at: $(date)"
echo ""

# Show container status
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
