#!/usr/bin/env bash
# =============================================================================
# Build, verify and publish the CO.RA.PAN BlackLab security overlay image
# =============================================================================
#
# Builds app/infra/blacklab/Dockerfile LOCALLY (never on the production server),
# verifies that only libbrotli1 changed against the pinned upstream image and
# that the BlackLab WAR is byte-identical, prints the immutable image ID
# (config digest) to pin in run_bls_prod.sh, and optionally publishes the image
# to a Docker host over SSH (docker save | docker load) and checks the ID there.
#
# Usage (from the repository root, Git Bash or Linux):
#   bash app/scripts/blacklab/build_blacklab_security_image.sh
#   bash app/scripts/blacklab/build_blacklab_security_image.sh --publish <ssh-host>
#
# The publish step only adds an image to the remote host; it does not stop,
# start or recreate any container.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONTEXT_DIR="${APP_DIR}/infra/blacklab"
BASE_IMAGE="instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7"
TAG="corapan/blacklab:5.0.0-snapshot-20260112-sec1"
PUBLISH_HOST=""

if [ "${1:-}" = "--publish" ]; then
    PUBLISH_HOST="${2:?--publish requires an ssh host}"
fi

echo "[1/4] Building ${TAG} from ${BASE_IMAGE}"
docker pull -q "${BASE_IMAGE}" >/dev/null
docker build --no-cache --platform linux/amd64 --provenance=false --sbom=false \
    -t "${TAG}" -f "${CONTEXT_DIR}/Dockerfile" "${CONTEXT_DIR}"

echo "[2/4] Verifying package and application identity"
pkgs() { docker run --rm --entrypoint dpkg-query "$1" -W -f='${Package} ${Version}\n' | sort; }
# The path stays inside the sh -c string so Git Bash does not rewrite it.
war() { docker run --rm --entrypoint sh "$1" -c 'sha256sum /usr/local/tomcat/webapps/blacklab-server.war' | cut -d' ' -f1; }
changed="$(diff <(pkgs "${BASE_IMAGE}") <(pkgs "${TAG}") | grep '^>' || true)"
echo "${changed}"
if [ "$(printf '%s\n' "${changed}" | grep -c .)" -ne 1 ] || ! printf '%s' "${changed}" | grep -q '^> libbrotli1 '; then
    echo "[ERROR] Expected exactly one changed package (libbrotli1)" >&2
    exit 1
fi
base_war="$(war "${BASE_IMAGE}")"
new_war="$(war "${TAG}")"
if [ -z "${base_war}" ] || [ "${base_war}" != "${new_war}" ]; then
    echo "[ERROR] blacklab-server.war missing or different from the upstream image" >&2
    exit 1
fi
echo "blacklab-server.war sha256 ${new_war} (unchanged)"
if [ "$(docker image inspect "${BASE_IMAGE}" --format '{{json .Config}}')" != \
     "$(docker image inspect "${TAG}" --format '{{json .Config}}')" ]; then
    echo "[ERROR] Image config (user, cmd, env, volumes, ports) differs from the upstream image" >&2
    exit 1
fi

echo "[3/4] Immutable image ID (config digest) to pin in run_bls_prod.sh:"
IMAGE_ID="$(docker save "${TAG}" | tar -xOf - manifest.json | sed -n 's/.*"Config":"\([^"]*\)".*/\1/p' \
    | sed -e 's#^blobs/sha256/#sha256:#' -e 's#\.json$##' -e 's#^\([0-9a-f]\{64\}\)$#sha256:\1#')"
echo "  ${IMAGE_ID}"

if [ -z "${PUBLISH_HOST}" ]; then
    echo "[4/4] Not published (no --publish host given)"
    exit 0
fi

echo "[4/4] Publishing ${TAG} to ${PUBLISH_HOST}"
docker save "${TAG}" | gzip -1 | ssh -o BatchMode=yes "${PUBLISH_HOST}" 'gunzip | docker load'
REMOTE_ID="$(ssh -o BatchMode=yes "${PUBLISH_HOST}" "docker image inspect '${TAG}' --format '{{.Id}}'")"
echo "  remote image ID: ${REMOTE_ID}"
if [ "${REMOTE_ID}" != "${IMAGE_ID}" ]; then
    echo "[ERROR] Remote image ID does not match the local config digest" >&2
    exit 1
fi
echo "Published and verified."
