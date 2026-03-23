#!/usr/bin/env bash
# Lightweight helper to run the BlackLab Docker image for local/dev use.
# Usage: ./scripts/blacklab/run_bls.sh <PORT> <HEAP_MAX> <HEAP_INIT>
# Example: ./scripts/blacklab/run_bls.sh 8081 2g 512m

set -euo pipefail
PORT=${1:-8081}
HEAP_MAX=${2:-2g}
HEAP_INIT=${3:-512m}
IMAGE="instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7"
CONTAINER_NAME="corapan-blacklab-${PORT}"

echo "Starting BlackLab container $CONTAINER_NAME on port $PORT (Xmx=$HEAP_MAX, Xms=$HEAP_INIT)"

docker run --rm \
  --name "$CONTAINER_NAME" \
  -p "${PORT}:8080" \
  -e JAVA_TOOL_OPTIONS="-Xmx${HEAP_MAX} -Xms${HEAP_INIT}" \
  "$IMAGE"
