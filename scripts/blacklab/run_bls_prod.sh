#!/usr/bin/env bash
# =============================================================================
# CO.RA.PAN Production BlackLab Server Start Script
# =============================================================================
#
# Starts the BlackLab server container for production use.
# The container will mount the BlackLab index and configuration.
#
# Prerequisites:
#   - BlackLab index in /srv/webapps/corapan/data/blacklab_index
#   - BlackLab config in /srv/webapps/corapan/app/config/blacklab
#   - Docker network: corapan-network
#
# Usage:
#   sudo bash /srv/webapps/corapan/app/scripts/blacklab/run_bls_prod.sh
#
# Options:
#   HEAP_MAX  - Maximum heap size (default: 2g)
#   HEAP_INIT - Initial heap size (default: 512m)
#
# =============================================================================

set -euo pipefail

# Configuration
CONTAINER_NAME="corapan-blacklab"
IMAGE="instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7"
HOST_PORT=8081
CONTAINER_PORT=8080
NETWORK_NAME="corapan-network"

# Paths
DATA_ROOT="/srv/webapps/corapan/data"
APP_ROOT="/srv/webapps/corapan/app"
INDEX_DIR="${DATA_ROOT}/blacklab_index"
CONFIG_DIR="${APP_ROOT}/config/blacklab"

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

echo "=============================================="
echo "CO.RA.PAN Production BlackLab Server Start"
echo "=============================================="
log "Starting BlackLab server..."

# Step 1: Verify prerequisites
log "Verifying prerequisites..."

if [ ! -d "$INDEX_DIR" ]; then
    error "BlackLab index not found: $INDEX_DIR"
    error "Run build_blacklab_index_prod.sh first"
    exit 1
fi

if [ ! -d "$CONFIG_DIR" ]; then
    error "BlackLab config not found: $CONFIG_DIR"
    exit 1
fi

if [ -z "$(ls -A "$INDEX_DIR")" ]; then
    error "BlackLab index directory is empty: $INDEX_DIR"
    error "Run build_blacklab_index_prod.sh first"
    exit 1
fi

INDEX_SIZE=$(du -sh "$INDEX_DIR" | cut -f1)
log "Index directory: $INDEX_DIR ($INDEX_SIZE)"

# Step 2: Create network if not exists
log "Ensuring Docker network exists..."
docker network create "$NETWORK_NAME" 2>/dev/null && log "Created network: $NETWORK_NAME" || log "Network already exists: $NETWORK_NAME"

# Step 3: Stop and remove old container
log "Stopping old container (if running)..."
docker stop "$CONTAINER_NAME" 2>/dev/null && log "Stopped: $CONTAINER_NAME" || true
docker rm "$CONTAINER_NAME" 2>/dev/null && log "Removed: $CONTAINER_NAME" || true

# Step 4: Pull latest image
log "Pulling latest BlackLab image..."
docker pull "$IMAGE"

# Step 5: Start new container
log "Starting BlackLab container..."
log "  Container: $CONTAINER_NAME"
log "  Port: $HOST_PORT -> $CONTAINER_PORT"
log "  Network: $NETWORK_NAME"
log "  Heap: Xms=$HEAP_INIT, Xmx=$HEAP_MAX"

docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    --network "$NETWORK_NAME" \
    -p "${HOST_PORT}:${CONTAINER_PORT}" \
    -e JAVA_TOOL_OPTIONS="-Xmx${HEAP_MAX} -Xms${HEAP_INIT}" \
    -v "${INDEX_DIR}:/data/index/corapan:ro" \
    -v "${CONFIG_DIR}:/etc/blacklab:ro" \
    "$IMAGE"

# Step 6: Wait for container to be ready
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

# Step 7: Health check
log "Checking BlackLab health..."
MAX_RETRIES=12
RETRY_INTERVAL=5
RETRIES=0

while [ $RETRIES -lt $MAX_RETRIES ]; do
    if curl -s -f "http://localhost:${HOST_PORT}/blacklab-server/" > /dev/null 2>&1; then
        log "BlackLab server is responding"
        break
    fi
    RETRIES=$((RETRIES + 1))
    if [ $RETRIES -lt $MAX_RETRIES ]; then
        warn "BlackLab not ready yet, retrying in ${RETRY_INTERVAL}s... ($RETRIES/$MAX_RETRIES)"
        sleep $RETRY_INTERVAL
    fi
done

if [ $RETRIES -eq $MAX_RETRIES ]; then
    warn "BlackLab did not respond within the timeout"
    warn "Check logs with: docker logs $CONTAINER_NAME"
else
    # Check for corpus
    CORPUS_CHECK=$(curl -s "http://localhost:${HOST_PORT}/blacklab-server/" 2>/dev/null || echo "error")
    if echo "$CORPUS_CHECK" | grep -q "corapan"; then
        log "Corpus 'corapan' is available"
    else
        warn "Corpus 'corapan' may not be indexed correctly"
        warn "Response: $CORPUS_CHECK"
    fi
fi

# Summary
echo ""
echo "=============================================="
log "BlackLab server started successfully!"
echo "=============================================="
echo "Container: $CONTAINER_NAME"
echo "Image: $IMAGE"
echo "Port: http://localhost:$HOST_PORT/blacklab-server/"
echo "Network: $NETWORK_NAME"
echo "Index: $INDEX_DIR ($INDEX_SIZE)"
echo ""
echo "To check logs: docker logs -f $CONTAINER_NAME"
echo "To verify: curl http://localhost:$HOST_PORT/blacklab-server/"
echo ""

# Show container status
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
