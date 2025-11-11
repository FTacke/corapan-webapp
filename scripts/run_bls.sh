#!/bin/bash
# Start BlackLab Server on port 8081
# Usage: ./scripts/run_bls.sh [--port 8081] [--mem 2g]

set -euo pipefail

PORT="${1:-8081}"
MAX_MEM="${2:-2g}"
MIN_MEM="${3:-512m}"

INDEX_DIR="/data/blacklab_index"
BLS_HOME="${BLS_HOME:-.}"
LOG_DIR="logs/bls"
LOG_FILE="$LOG_DIR/server.log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Prerequisites
log "BlackLab Server Startup"

# Check Java
if ! command -v java &> /dev/null; then
    error "Java not found. Install Java 11+:"
    error "  Ubuntu/Debian: apt-get install openjdk-11-jre-headless"
    error "  macOS: brew install openjdk@11"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | grep -oP '(?<=version ")[^"]*' || echo "unknown")
log "Java version: $JAVA_VERSION"

# Check index directory
if [ ! -d "$INDEX_DIR" ]; then
    error "Index directory not found: $INDEX_DIR"
    error "Run 'make index' first"
    exit 1
fi

# Create log directory
mkdir -p "$LOG_DIR"

# Check if already running
if [ -f "$LOG_DIR/bls.pid" ]; then
    OLD_PID=$(cat "$LOG_DIR/bls.pid")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        warn "BlackLab Server already running (PID: $OLD_PID)"
        log "Server log: tail -f $LOG_FILE"
        exit 0
    else
        log "Cleaning up stale PID file"
        rm -f "$LOG_DIR/bls.pid"
    fi
fi

# Find blacklab-server.jar
BLS_JAR=""
if [ -f "$BLS_HOME/blacklab-server.jar" ]; then
    BLS_JAR="$BLS_HOME/blacklab-server.jar"
elif command -v find &> /dev/null; then
    BLS_JAR=$(find /opt /usr -name "blacklab-server.jar" 2>/dev/null | head -1 || echo "")
fi

if [ -z "$BLS_JAR" ] || [ ! -f "$BLS_JAR" ]; then
    error "blacklab-server.jar not found"
    error "Install BlackLab Server:"
    error "  Ubuntu/Debian: apt-get install blacklab-server"
    error "  Or download from: https://github.com/INL/BlackLab/releases"
    exit 1
fi

log "BlackLab JAR: $BLS_JAR"

# Start server
log "Starting BlackLab Server..."
log "  Port: $PORT"
log "  Memory: $MIN_MEM - $MAX_MEM"
log "  Index: $INDEX_DIR"
log "  Log: $LOG_FILE"

java \
    -Xms"$MIN_MEM" \
    -Xmx"$MAX_MEM" \
    -Dbls.port="$PORT" \
    -Dbls.indexDir="$INDEX_DIR" \
    -Dlogback.configurationFile="conf/logback.xml" \
    -jar "$BLS_JAR" \
    > "$LOG_FILE" 2>&1 &

BLS_PID=$!
echo "$BLS_PID" > "$LOG_DIR/bls.pid"

# Wait for startup
sleep 2

if kill -0 "$BLS_PID" 2>/dev/null; then
    log "Server started (PID: $BLS_PID)"
    log "Health check: curl -s http://127.0.0.1:$PORT/blacklab-server/"
    log "Web UI: http://localhost:$PORT/blacklab-server/"
    log "Logs: tail -f $LOG_FILE"
else
    error "Failed to start server"
    tail -20 "$LOG_FILE"
    exit 1
fi

exit 0
