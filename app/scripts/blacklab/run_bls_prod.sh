#!/usr/bin/env bash
# =============================================================================
# CO.RA.PAN Production BlackLab Server Start Script
# =============================================================================
#
# Starts the BlackLab server container for production use.
# The container will mount the BlackLab index and configuration.
#
# Prerequisites:
#   - BlackLab index in /srv/webapps/corapan/data/blacklab/index
#   - BlackLab config in /srv/webapps/corapan/app/app/config/blacklab
#   - Docker network: corapan-network
#
# Usage:
#   sudo bash /srv/webapps/corapan/app/app/scripts/blacklab/run_bls_prod.sh
#
# Options:
#   HEAP_MAX  - Maximum heap size (default: 2g)
#   HEAP_INIT - Initial heap size (default: 512m)
#   BLACKLAB_IMAGE_ID - override the pinned image ID (rollback only)
#
# Image:
#   The security overlay of the upstream BlackLab image (same BlackLab build,
#   patched libbrotli1, CVE-2026-111497) is built locally and published to the
#   server by build_blacklab_security_image.sh; it is not in a registry, so the
#   script does not pull. The container is started by the pinned image ID and
#   the old container is only stopped after that ID has been found locally.
#   Previous image: instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7
#
# =============================================================================

set -euo pipefail

# Configuration
CONTAINER_NAME="corapan-blacklab"
IMAGE="corapan/blacklab:5.0.0-snapshot-20260112-sec1"
IMAGE_ID="${BLACKLAB_IMAGE_ID:-sha256:327fe4fb0849ee9c20ed9e63b7d7fab06fa623d97657bcaa7f79114b23b161f5}"
HOST_PORT=8081
CONTAINER_PORT=8080
NETWORK_NAME="corapan-network-prod"

# Paths
DATA_ROOT="/srv/webapps/corapan/data"
CHECKOUT_DIR="/srv/webapps/corapan/app"
APP_DIR="${CHECKOUT_DIR}/app"
INDEX_DIR="${DATA_ROOT}/blacklab/index"
CONFIG_DIR="${APP_DIR}/config/blacklab"

# JVM settings
HEAP_MAX="${HEAP_MAX:-2g}"
HEAP_INIT="${HEAP_INIT:-512m}"

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

quote_path() {
    printf '%q' "$1"
}

fail_path_check() {
    error "$1"
    exit 1
}

validate_exact_index_path() {
    local path="$1"
    local expected_root="$2"
    local expected="${expected_root}/blacklab/index"
    local leaf="${path##*/}"

    if [[ "$path" != "$expected" ]]; then
        fail_path_check "Active index path mismatch. Expected $(quote_path "$expected") but got $(quote_path "$path")"
    fi

    if [[ "$leaf" != "index" ]]; then
        fail_path_check "Active index leaf must be exact index, got $(quote_path "$leaf") from $(quote_path "$path")"
    fi

    if [[ "$path" =~ [[:cntrl:]] ]]; then
        fail_path_check "Active index path contains control characters: $(quote_path "$path")"
    fi

    if [[ "$path" =~ ^[[:space:]] || "$path" =~ [[:space:]]$ ]]; then
        fail_path_check "Active index path contains leading or trailing whitespace: $(quote_path "$path")"
    fi
}

collect_index_conflicts() {
    local parent_dir="$1"
    local found=0

    while IFS= read -r -d '' entry; do
        local base
        local normalized
        base="$(basename "$entry")"
        normalized="$(printf '%s' "$base" | tr -d '[:cntrl:]' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        if [[ "$normalized" == "index" && "$base" != "index" ]]; then
            printf '%s\n' "$(quote_path "$entry")"
            found=1
        fi
    done < <(find "$parent_dir" -mindepth 1 -maxdepth 1 -type d -print0)

    return $found
}

assert_index_ready_for_start() {
    validate_exact_index_path "$INDEX_DIR" "$DATA_ROOT"

    if [[ ! -d "$INDEX_DIR" ]]; then
        fail_path_check "BlackLab index not found: $(quote_path "$INDEX_DIR")"
    fi

    if [[ -z "$(find "$INDEX_DIR" -mindepth 1 -print -quit)" ]]; then
        fail_path_check "BlackLab index directory is empty: $(quote_path "$INDEX_DIR")"
    fi

    local conflict_output
    if conflict_output="$(collect_index_conflicts "${DATA_ROOT}/blacklab")"; then
        :
    else
        fail_path_check "Suspicious BlackLab index sibling path(s) detected under $(quote_path "${DATA_ROOT}/blacklab"): ${conflict_output}"
    fi
}

echo "=============================================="
echo "CO.RA.PAN Production BlackLab Server Start"
echo "=============================================="
log "Starting BlackLab server..."

# Step 1: Verify prerequisites
log "Verifying prerequisites..."

assert_index_ready_for_start

if [ ! -d "$CONFIG_DIR" ]; then
    error "BlackLab config not found: $(quote_path "$CONFIG_DIR")"
    exit 1
fi

if ! docker image inspect "$IMAGE_ID" >/dev/null 2>&1; then
    error "Pinned BlackLab image not present on this host: $IMAGE_ID ($IMAGE)"
    error "Publish it with app/scripts/blacklab/build_blacklab_security_image.sh --publish <host>"
    exit 1
fi
log "Pinned image present: $IMAGE_ID"

INDEX_SIZE=$(du -sh "$INDEX_DIR" | cut -f1)
log "Index directory: $(quote_path "$INDEX_DIR") ($INDEX_SIZE)"

# Step 2: Create network if not exists
log "Ensuring Docker network exists..."
docker network create "$NETWORK_NAME" 2>/dev/null && log "Created network: $NETWORK_NAME" || log "Network already exists: $NETWORK_NAME"

# Step 3: Stop and remove old container
log "Stopping old container (if running)..."
docker stop "$CONTAINER_NAME" 2>/dev/null && log "Stopped: $CONTAINER_NAME" || true
docker rm "$CONTAINER_NAME" 2>/dev/null && log "Removed: $CONTAINER_NAME" || true

# Step 4: Start new container (image presence was verified before the stop)
log "Starting BlackLab container..."
log "  Container: $CONTAINER_NAME"
log "  Image: $IMAGE_ID ($IMAGE)"
log "  Port: $HOST_PORT -> $CONTAINER_PORT"
log "  Network: $NETWORK_NAME"
log "  Heap: Xms=$HEAP_INIT, Xmx=$HEAP_MAX"
log "  Index mount: $(quote_path "$INDEX_DIR") -> /data/index/corapan"
log "  Config mount: $(quote_path "$CONFIG_DIR") -> /etc/blacklab"

docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    --network "$NETWORK_NAME" \
    -p "${HOST_PORT}:${CONTAINER_PORT}" \
    -e JAVA_TOOL_OPTIONS="-Xmx${HEAP_MAX} -Xms${HEAP_INIT}" \
    -e BLACKLAB_CONFIG_DIR="/etc/blacklab" \
    -v "${INDEX_DIR}:/data/index/corapan:ro" \
    -v "${CONFIG_DIR}:/etc/blacklab:ro" \
    "$IMAGE_ID"

# Step 5: Wait for container to be ready
log "Waiting for BlackLab to start..."
sleep 5

# Check if container is running
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log "Container is running"
else
    error "Container failed to start!"
    docker logs "$CONTAINER_NAME" 2>&1 | tail -20
    exit 1
fi

# Step 6: Health check
log "Checking BlackLab health..."
MAX_RETRIES=12
RETRY_INTERVAL=5
RETRIES=0
CORPORA_URL="http://localhost:${HOST_PORT}/blacklab-server/corpora/?outputformat=json"
CORPORA_RESPONSE=""

while [ $RETRIES -lt $MAX_RETRIES ]; do
    if CORPORA_RESPONSE="$(curl -s -f "$CORPORA_URL" 2>/dev/null)" && [[ -n "$CORPORA_RESPONSE" ]]; then
        log "BlackLab corpora endpoint is responding"
        break
    fi
    RETRIES=$((RETRIES + 1))
    if [ $RETRIES -lt $MAX_RETRIES ]; then
        warn "BlackLab not ready yet, retrying in ${RETRY_INTERVAL}s... ($RETRIES/$MAX_RETRIES)"
        sleep $RETRY_INTERVAL
    fi
done

if [ $RETRIES -eq $MAX_RETRIES ]; then
    error "BlackLab corpora endpoint did not respond within the timeout: $(quote_path "$CORPORA_URL")"
    docker logs "$CONTAINER_NAME" 2>&1 | tail -20
    exit 1
else
    assert_index_ready_for_start

    if echo "$CORPORA_RESPONSE" | grep -q '"corapan"'; then
        log "Corpus 'corapan' is available"
    else
        error "Corpus 'corapan' not found in corpora response from $(quote_path "$CORPORA_URL")"
        error "Corpora response: $(quote_path "$CORPORA_RESPONSE")"
        exit 1
    fi
fi

# Summary
echo ""
echo "=============================================="
log "BlackLab server started successfully!"
echo "=============================================="
echo "Container: $CONTAINER_NAME"
echo "Image: $IMAGE_ID ($IMAGE)"
echo "Port: http://localhost:$HOST_PORT/blacklab-server/"
echo "Network: $NETWORK_NAME"
echo "Index: $(quote_path "$INDEX_DIR") ($INDEX_SIZE)"
echo ""
echo "To check logs: docker logs -f $CONTAINER_NAME"
echo "To verify: curl http://localhost:$HOST_PORT/blacklab-server/"
echo ""

# Show container status
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
