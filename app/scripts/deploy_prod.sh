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
#   - Git repository root cloned to /srv/webapps/corapan/app
#   - Application subtree present under /srv/webapps/corapan/app/app
#   - Runtime roots /srv/webapps/corapan/data, /srv/webapps/corapan/media, and /srv/webapps/corapan/logs populated on the host
#   - passwords.env configured in /srv/webapps/corapan/config/
#
# Usage:
#   cd /srv/webapps/corapan/app
#   bash app/scripts/deploy_prod.sh
#
# =============================================================================

set -euo pipefail

# Configuration
BASE_DIR="/srv/webapps/corapan"
CHECKOUT_DIR="${BASE_DIR}/app"
APP_DIR="${CHECKOUT_DIR}/app"
ENV_FILE="${BASE_DIR}/config/passwords.env"
COMPOSE_FILE="${APP_DIR}/infra/docker-compose.prod.yml"
CONTAINER_NAME="corapan-web-prod"
LEGACY_CONTAINER="corapan-webapp"
HEALTH_URL="http://127.0.0.1:6000/health"
DEFAULT_APP_REPOSITORY_URL="https://github.com/FTacke/corapan-webapp"
LATEST_RELEASE_API_URL="https://api.github.com/repos/FTacke/corapan-webapp/releases/latest"

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

normalize_app_version() {
  local raw="${1:-}"
  raw="${raw#v}"
  printf '%s' "${raw}"
}

fetch_latest_release_metadata() {
  local curl_args=()
  local release_json
  local compact_json

  curl_args+=(-fsSL)
  curl_args+=(-H 'Accept: application/vnd.github+json')
  curl_args+=(-H 'User-Agent: corapan-deploy')

  if [ -n "${GITHUB_TOKEN:-}" ]; then
    curl_args+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
  fi

  if ! release_json="$(curl "${curl_args[@]}" "${LATEST_RELEASE_API_URL}")"; then
    log_warn "Could not fetch latest GitHub release metadata. Footer release line will remain hidden."
    APP_RELEASE_TAG=""
    APP_RELEASE_URL=""
    APP_VERSION=""
    export APP_RELEASE_TAG APP_RELEASE_URL APP_VERSION
    return 0
  fi

  compact_json="$(printf '%s' "${release_json}" | tr -d '\r\n')"
  APP_RELEASE_TAG="$(printf '%s' "${compact_json}" | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
  APP_RELEASE_URL="$(printf '%s' "${compact_json}" | sed -n 's/.*"html_url"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"

  if [ -z "${APP_RELEASE_TAG}" ] || [ -z "${APP_RELEASE_URL}" ]; then
    log_warn "Latest GitHub release metadata was incomplete. Footer release line will remain hidden."
    APP_RELEASE_TAG=""
    APP_RELEASE_URL=""
    APP_VERSION=""
    export APP_RELEASE_TAG APP_RELEASE_URL APP_VERSION
    return 0
  fi

  APP_VERSION="$(normalize_app_version "${APP_RELEASE_TAG}")"
  export APP_RELEASE_TAG APP_RELEASE_URL APP_VERSION
  log_info "Using latest official GitHub release for footer: ${APP_RELEASE_TAG}"
  log_info "Release URL: ${APP_RELEASE_URL}"
}

resolve_compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
    COMPOSE_VARIANT="docker compose"
    COMPOSE_VERSION="$(docker compose version --short 2>/dev/null || docker compose version)"
    return 0
  fi

  if command -v docker-compose >/dev/null 2>&1; then
    local raw_version
    raw_version="$(docker-compose version --short 2>/dev/null || docker-compose version 2>/dev/null | head -n 1)"

    if printf '%s\n' "${raw_version}" | grep -Eiq '(^|[[:space:]]|v)2(\.|[[:space:]]|$)'; then
      COMPOSE_CMD=(docker-compose)
      COMPOSE_VARIANT="docker-compose"
      COMPOSE_VERSION="${raw_version}"
      return 0
    fi

    log_error "Docker Compose V2 plugin is required on the production server, but only docker-compose v1 was found: ${raw_version}"
    log_error "This deploy runs locally on the target server via the self-hosted GitHub Actions runner. Refusing to use docker-compose v1 because it is a known failure source for modern Docker/Compose deploys."
    log_error "Install the Docker Compose V2 plugin on the server so 'docker compose' is available, then rerun the deploy."
    exit 1
  fi

  log_error "No supported Docker Compose command found on the production server. Expected 'docker compose' (preferred) or a docker-compose wrapper backed by Compose V2."
  exit 1
}

echo "=============================================="
echo "CO.RA.PAN Production Deployment"
echo "=============================================="
echo "Started at: $(date)"
echo "Host: $(hostname)"
echo "User: $(whoami)"
echo "PWD: $(pwd)"
echo "Runner: ${RUNNER_NAME:-unknown}"
echo "GitHub Actions: ${GITHUB_ACTIONS:-false}"
echo ""

cd "${CHECKOUT_DIR}"
export APP_REPOSITORY_URL="${APP_REPOSITORY_URL:-${DEFAULT_APP_REPOSITORY_URL}}"
fetch_latest_release_metadata

# Step 0: Resolve Docker Compose implementation on the target host
log_info "Resolving Docker Compose implementation on target host..."
resolve_compose_cmd
log_info "Compose command: ${COMPOSE_VARIANT}"
log_info "Compose version: ${COMPOSE_VERSION}"
log_info "Docker version: $(docker version --format '{{.Client.Version}}|{{.Server.Version}}')"
log_info "Release metadata: APP_RELEASE_TAG=${APP_RELEASE_TAG:-<unset>} APP_RELEASE_URL=${APP_RELEASE_URL:-<unset>}"
echo ""

# Step 1: Update code from Git
log_info "Fetching latest code from origin/main..."
git fetch origin

if [ -n "${GITHUB_SHA:-}" ]; then
  git reset --hard "${GITHUB_SHA}"
  log_info "Code updated to workflow SHA: $(git rev-parse --short HEAD)"
else
  git reset --hard origin/main
  log_info "Code updated to origin/main: $(git rev-parse --short HEAD)"
fi
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

# Step 3: Start via Docker Compose (canonical top-level mounts)
log_info "Starting production stack via ${COMPOSE_VARIANT}..."
"${COMPOSE_CMD[@]}" --env-file "${ENV_FILE}" \
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

# Step 5: Verify canonical mounts (container destinations + write test)
log_info "Verifying canonical mounts..."

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

log_info "Mount destinations present"
log_info "Write check ok"
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
